from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Literal, Optional

from ..core import ConfigManager, ClientManager, PromptBuilder, FilterChain
from ..constants import CONFIGS_DIR
from ..utils.logger import setup_task_logger
from rich.progress import Progress

# Default logger (will be replaced by task-specific logger)
logger = logging.getLogger(__name__)


class DataGenService:
    """
    Data generation service.
    High-level service for generating training data.
    """
    
    def __init__(
        self,
        config: ConfigManager,
        client_manager: ClientManager,
        prompt_builder: PromptBuilder,
        filter_chain: FilterChain,
        logger: Optional[logging.Logger] = None,
    ):
        self.config = config
        self.client_manager = client_manager
        self.prompt_builder = prompt_builder
        self.filter_chain = filter_chain
        self.logger = logger or logging.getLogger(__name__)
    
    @classmethod
    def from_config_files(
        cls,
        *config_paths: Path,
        task: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ) -> "DataGenService":
        """
        Create service from configuration files.
        
        Args:
            config_paths: Configuration file paths
            task: Task name for logging (e.g., 'fim', 'l2r')
            logger: Custom logger instance
        """
        config = ConfigManager.from_files(*config_paths)
        client_manager = ClientManager(config)
        prompt_builder = PromptBuilder(config)
        filter_chain = FilterChain.for_funcname(config)
        
        return cls(config, client_manager, prompt_builder, filter_chain, logger)
    
    @classmethod
    def from_config_path(
        cls,
        config_path: Path,
        task: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ) -> "DataGenService":
        """
        Create service from single config file (auto-loads model.yaml).
        
        Args:
            config_path: Main configuration file path
            task: Task name for logging (e.g., 'fim', 'l2r')
            logger: Custom logger instance
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
        filter_chain = FilterChain.for_funcname(config)
        
        return cls(config, client_manager, prompt_builder, filter_chain, logger)
    
    async def generate_function_names(
        self,
        mode: Literal["FIM", "L2R"] = "FIM",
        num_samples: Optional[int] = None,
    ) -> List[Dict]:
        """
        Generate function names using FIM or L2R mode.
        
        Args:
            mode: "FIM" or "L2R"
            num_samples: Total number of samples to generate (overrides config)
        
        Returns:
            List of candidates with function names
        """
        client = self.client_manager.completion_client
        
        # Get parameters
        temperature = float(self.config.get("namegen.temperature", 0.4))
        top_p = float(self.config.get("namegen.top_p", 0.9))
        max_tokens = int(self.config.get("namegen.max_tokens", 512))
        stop = self.config.get("namegen.stop", ["(", " ", "\n"])
        
        # Calculate batching based on num_samples and max_concurrent
        if num_samples is None:
            num_samples = int(self.config.get("namegen.num_samples", 100))
        
        # Prefer the client's actual semaphore setting to avoid drift
        try:
            max_concurrent = int(getattr(self.client_manager.completion_client.semaphore, "_value", 0)) or int(self.config.get("api.concurrency.max_concurrent_requests", 5))
        except Exception:
            max_concurrent = int(self.config.get("api.concurrency.max_concurrent_requests", 5))
        
        # Each request generates 1 sample, batch them based on concurrency
        # We'll make ceil(num_samples / max_concurrent) batches
        import math
        num_batches = math.ceil(num_samples / max_concurrent)
        samples_per_batch = min(max_concurrent, num_samples)
        
        self.logger.info(f"Generating function names: mode={mode}, total_samples={num_samples}")
        self.logger.info(f"Batching: {num_batches} batches, {samples_per_batch} samples per batch, max_concurrent={max_concurrent}")
        self.logger.info(f"Client base_url: {getattr(client, 'base_url', 'N/A')}, model: {getattr(client, 'model', 'N/A')}")
        self.logger.info(f"Generation params: temperature={temperature}, top_p={top_p}, max_tokens={max_tokens}, stop={stop}")
        
        # Get FIM stop token
        fim_suffix_token = self.config.get("api.fim.suffix_token", "<|fim_suffix|>")
        if mode == "FIM" and fim_suffix_token not in stop:
            stop = list(stop) + [fim_suffix_token]
        
        # Prepare requests - generate num_samples total
        if mode == "FIM":
            fim_prompt = self.prompt_builder.build_funcname_fim()
            self.logger.debug(f"FIM prompt: {repr(fim_prompt[:80])}...")
            base_prompt = fim_prompt
        else:  # L2R
            base_prompt = self.prompt_builder.build_funcname_l2r()
            self.logger.debug(f"L2R prompt: {repr(base_prompt[:50])}...")
        
        # Generate all samples in batches with progress
        all_results: List[List[Dict]] = []
        completed = 0
        with Progress() as progress:
            task_id = progress.add_task("Generating", total=num_samples)
            for batch_idx, start_idx in enumerate(range(0, num_samples, max_concurrent)):
                batch_size = min(max_concurrent, num_samples - start_idx)
                batch_prompts = [base_prompt] * batch_size
                self.logger.info(f"[Batch {batch_idx+1}/{num_batches}] Sending {batch_size} requests...")
                
                batch_results = await client.complete_batch_async(
                    prompts=batch_prompts,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    n=1,  # One sample per request
                    stop=stop,
                )
                
                self.logger.info(f"[Batch {batch_idx+1}/{num_batches}] Received {len(batch_results)} responses")
                all_results.extend(batch_results)
                completed += batch_size
                progress.update(task_id, advance=batch_size)
                self.logger.info(f"Progress: {completed}/{num_samples}")
        
        # Flatten results
        flattened = []
        for batch in all_results:
            flattened.extend(batch)
        
        # Extract problem descriptions (no function names for now)
        candidates = []
        for idx, result in enumerate(flattened):
            raw_text = result.get("text", "").strip()
            
            # Log first 3 samples for debugging
            if idx < 3:
                self.logger.info(f"Sample {idx+1} raw output (full): {repr(raw_text)}")
            
            # For now, just store the description (which is the algorithm problem)
            # We'll generate function names in a later stage
            if raw_text:  # Only keep non-empty descriptions
                candidates.append({
                    "problem_description": raw_text,
                    "source": mode,
                    "raw_text": raw_text,
                })
        
        # No filtering needed for descriptions (we'll filter when generating function names later)
        filtered = candidates
        
        self.logger.info(f"Generated {len(filtered)}/{len(candidates)} valid function names")
        self.logger.info(f"Filter stats: {self.filter_chain.get_stats()}")
        
        return filtered
    
    async def generate_function_names_ab_test(
        self,
        num_samples: Optional[int] = None
    ) -> tuple[List[Dict], List[Dict]]:
        """
        Run A/B test: FIM vs L2R function name generation.
        
        Args:
            num_samples: Total samples to generate per mode
        
        Returns:
            (fim_results, l2r_results)
        """
        self.logger.info("=" * 60)
        self.logger.info("A/B Test: FIM vs L2R Function Name Generation")
        self.logger.info("=" * 60)
        
        # Generate FIM
        self.logger.info("Running FIM mode...")
        fim_results = await self.generate_function_names("FIM", num_samples)
        
        # Generate L2R
        self.logger.info("Running L2R mode...")
        l2r_results = await self.generate_function_names("L2R", num_samples)
        
        # Statistics
        fim_unique = len(set(r["func_name"] for r in fim_results))
        l2r_unique = len(set(r["func_name"] for r in l2r_results))
        
        self.logger.info("=" * 60)
        self.logger.info("A/B Test Results:")
        self.logger.info(f"  FIM: {len(fim_results)} total, {fim_unique} unique")
        self.logger.info(f"  L2R: {len(l2r_results)} total, {l2r_unique} unique")
        self.logger.info("=" * 60)
        
        return fim_results, l2r_results

