"""
Data Generation Service (Orchestration Layer)

High-level service that orchestrates the data generation pipeline:
1. Problem Description Generation (ProblemGen)
2. Function Skeleton Generation (SkeletonGen)
3. Code Implementation Generation (CodeGen) - Future

This layer provides a unified API and handles multi-stage workflows.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Literal, Optional

from ..core import ConfigManager, ClientManager, PromptBuilder, FilterChain
from ..constants import CONFIGS_DIR, PROJECT_ROOT
from ..datagen.preprocess import ProblemGenerator, SkeletonGenerator, CodeGenerator
from ..utils.logger import setup_task_logger


class DataGenService:
    """
    Orchestration service for data generation pipeline.
    
    Coordinates:
    - ProblemGenerator: Generates algorithm problem descriptions
    - SkeletonGenerator: Generates function skeletons from problems
    - CodeGenerator: Generates full implementations (future)
    """
    
    def __init__(
        self,
        config: ConfigManager,
        client_manager: ClientManager,
        prompt_builder: PromptBuilder,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize the data generation service.
        
        Args:
            config: Configuration manager
            client_manager: Client manager for API access
            prompt_builder: Prompt builder
            logger: Logger instance
        """
        self.config = config
        self.client_manager = client_manager
        self.prompt_builder = prompt_builder
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize generators
        self.problem_gen = ProblemGenerator(
            client_manager=client_manager,
            prompt_builder=prompt_builder,
            config=config.to_dict(),
            logger=logger
        )
        
        self.skeleton_gen = SkeletonGenerator(
            client_manager=client_manager,
            config=config.to_dict(),
            logger=logger
        )
    
    @classmethod
    def from_config_path(
        cls,
        config_path: Path,
        task: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ) -> "DataGenService":
        """Create service from configuration file.
        
        Args:
            config_path: Main configuration file path
            task: Task name for logging (e.g., 'fim', 'l2r')
            logger: Custom logger instance
            
        Returns:
            Configured DataGenService instance
        """
        # Load main config
        main_config = ConfigManager.from_file(config_path)
        
        # Load and merge model config
        model_config_path = Path(main_config.get("model_config", "configs/model.yaml"))
        if not model_config_path.is_absolute():
            model_config_path = CONFIGS_DIR / model_config_path
        
        if model_config_path.exists():
            model_config = ConfigManager.from_file(model_config_path)
            config = model_config.merge(main_config)  # main_config overrides model_config
        else:
            config = main_config
        
        client_manager = ClientManager(config)
        prompt_builder = PromptBuilder(config)
        
        return cls(config, client_manager, prompt_builder, logger)
    
    async def generate_problems(
        self,
        mode: Literal["FIM", "L2R"],
        num_samples: Optional[int] = None,
    ) -> List[Dict]:
        """Generate algorithm problem descriptions.
        
        Args:
            mode: Generation mode ("FIM" or "L2R")
            num_samples: Number of problems to generate (overrides config)
            
        Returns:
            List of generated problem dictionaries
        """
        # Get parameters from config
        if num_samples is None:
            num_samples = int(self.config.get("namegen.num_samples", 100))
        
        temperature = float(self.config.get("namegen.temperature", 1.0))
        top_p = float(self.config.get("namegen.top_p", 0.95))
        max_tokens = int(self.config.get("namegen.max_tokens", 2048))
        stop = self.config.get("namegen.stop", ["---"])
        batch_write_size = int(self.config.get("namegen.batch_write_size", 50))
        
        # Get output directory
        out_dir = Path(self.config.get("io.out_names_dir", f"data/generated/problems_desc/{mode.lower()}"))
        if not out_dir.is_absolute():
            out_dir = PROJECT_ROOT / out_dir
        
        self.logger.info(f"=== Orchestrating Problem Generation: {mode} ===")
        
        # Call ProblemGenerator
        results = await self.problem_gen.generate(
            mode=mode,
            num_samples=num_samples,
            output_dir=out_dir,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            stop=stop,
            batch_write_size=batch_write_size
        )
        
        return results
    
    async def generate_skeletons(
        self,
        source_mode: Literal["fim", "l2r"],
        num_samples: Optional[int] = None,
    ) -> List[Dict]:
        """Generate function skeletons from problem descriptions.
        
        Args:
            source_mode: Source of problems ("fim" or "l2r")
            num_samples: Number of samples to process (None = all)
            
        Returns:
            List of generated skeleton dictionaries
        """
        # Get parameters from config
        temperature = float(self.config.get("skeleton.temperature", 0.7))
        top_p = float(self.config.get("skeleton.top_p", 0.95))
        max_tokens = int(self.config.get("skeleton.max_tokens", 512))
        stop = self.config.get("skeleton.stop", [])
        batch_write_size = int(self.config.get("skeleton.batch_write_size", 50))
        
        # Get prompt template
        prompt_template = self.config.get("prompts.skeleton.template", "")
        
        # Get input/output paths
        source_cfg = self.config.get("io.source", {})
        dir_map = source_cfg.get("dir_map", {})
        file_name_map = source_cfg.get("file_name_map", {})
        
        input_dir = PROJECT_ROOT / dir_map.get(source_mode, f"data/generated/problems_desc/{source_mode}")
        input_file = input_dir / file_name_map.get(source_mode, f"{source_mode}_results.jsonl")
        
        out_dir_map = self.config.get("io.out_dir_map", {})
        output_dir = PROJECT_ROOT / out_dir_map.get(source_mode, f"data/generated/func_skeletons/{source_mode}")
        
        self.logger.info(f"=== Orchestrating Skeleton Generation: {source_mode.upper()} ===")
        
        # Call SkeletonGenerator
        results = await self.skeleton_gen.generate(
            input_file=input_file,
            output_dir=output_dir,
            prompt_template=prompt_template,
            num_samples=num_samples,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            stop=stop,
            batch_write_size=batch_write_size
        )
        
        return results
    
    async def generate_code(
        self,
        source_mode: str,
        num_samples: Optional[int] = None,
    ) -> List[Dict]:
        """Orchestrates the generation of function implementations from skeletons.
        
        Args:
            source_mode: Source mode ('fim' or 'l2r')
            num_samples: Number of samples to process (None = all)
            
        Returns:
            List of generated implementation dictionaries
        """
        self.logger.info(f"=== Orchestrating Code Generation: {source_mode.upper()} ===")
        
        # Get config for code generation
        codegen_cfg = self.config.get_section("codegen")
        io_cfg = self.config.get_section("io")
        
        # Get input file path
        source_cfg = io_cfg.get("source", {})
        dir_map = source_cfg.get("dir_map", {})
        input_dir = Path(dir_map.get(source_mode, f"data/generated/func_skeletons/{source_mode}"))
        input_file = input_dir / source_cfg.get("file_name", "skeletons.jsonl")
        
        # Get output directory
        output_dir_map = io_cfg.get("out_dir_map", {})
        output_dir = Path(output_dir_map.get(source_mode, f"data/generated/func_implementations/{source_mode}"))
        
        # Get prompt template
        prompts_cfg = self.config.get_section("prompts")
        prompt_template = prompts_cfg.get("codegen.template", "")
        
        if not prompt_template:
            raise ValueError("Code generation prompt template not found in config")
        
        # Create CodeGenerator instance
        code_generator = CodeGenerator(
            client_manager=self.client_manager,
            config=codegen_cfg,
            logger=self.logger
        )
        
        # Generate implementations
        results = await code_generator.generate(
            input_file=input_file,
            output_dir=output_dir,
            prompt_template=prompt_template,
            num_samples=num_samples,
            temperature=codegen_cfg.get("temperature", 0.7),
            top_p=codegen_cfg.get("top_p", 0.95),
            max_tokens=codegen_cfg.get("max_tokens", 1024),
            stop=codegen_cfg.get("stop", ["\n\ndef ", "\n\nclass "]),
            batch_write_size=codegen_cfg.get("batch_write_size", 50),
            problem_key=source_cfg.get("problem_text_key", "problem_text"),
            skeleton_key=source_cfg.get("skeleton_code_key", "skeleton_code"),
            function_name_key=source_cfg.get("function_name_key", "function_name"),
            skip_invalid=False,  # Skeletons no longer contain invalid entries
            validate_syntax=codegen_cfg.get("validate_syntax", True),
            validate_imports=codegen_cfg.get("validate_imports", True)
        )
        
        self.logger.info(f"✅ Generated {len(results)} unique function implementations")
        return results
    
    async def generate_full_pipeline(
        self,
        mode: Literal["FIM", "L2R"],
        num_problems: Optional[int] = None,
        num_skeletons: Optional[int] = None,
        num_implementations: Optional[int] = None,
    ) -> Dict[str, List[Dict]]:
        """Run the full generation pipeline: problems → skeletons → implementations.
        
        Args:
            mode: Generation mode for problems
            num_problems: Number of problems to generate
            num_skeletons: Number of skeletons to generate from problems
            num_implementations: Number of implementations to generate
            
        Returns:
            Dictionary with 'problems', 'skeletons', and 'implementations' lists
        """
        self.logger.info("=" * 80)
        self.logger.info(f"FULL PIPELINE: {mode} Mode")
        self.logger.info("=" * 80)
        
        # Stage 1: Generate problems
        self.logger.info("Stage 1: Generating problem descriptions...")
        problems = await self.generate_problems(mode=mode, num_samples=num_problems)
        
        # Stage 2: Generate skeletons
        source_mode = mode.lower()
        self.logger.info(f"Stage 2: Generating function skeletons from {source_mode} problems...")
        skeletons = await self.generate_skeletons(
            source_mode=source_mode,
            num_samples=num_skeletons
        )
        
        # Stage 3: Generate implementations
        self.logger.info(f"Stage 3: Generating function implementations from {source_mode} skeletons...")
        implementations = await self.generate_code(
            source_mode=source_mode,
            num_samples=num_implementations
        )
        
        self.logger.info("=" * 80)
        self.logger.info("PIPELINE COMPLETE")
        self.logger.info(f"  Problems generated: {len(problems)}")
        self.logger.info(f"  Skeletons generated: {len(skeletons)}")
        self.logger.info(f"  Implementations generated: {len(implementations)}")
        self.logger.info("=" * 80)
        
        return {
            "problems": problems,
            "skeletons": skeletons,
            "implementations": implementations
        }
