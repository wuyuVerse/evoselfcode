"""
Skeleton Generator (SkeletonGen)

Core module for generating Python function skeletons from algorithm problem descriptions.
Produces well-structured function definitions with type hints and Google-style docstrings.
"""

import asyncio
import ast
import hashlib
import json
import logging
import math
import re
from pathlib import Path
from typing import List, Dict, Optional

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn

from ...core.client_manager import ClientManager


class SkeletonGenerator:
    """
    Generates Python function skeletons from problem descriptions.
    
    Features:
    - Batch async generation for high throughput
    - AST validation of generated code
    - Function name extraction
    - Hash-based deduplication
    - Incremental writing to disk
    """
    
    def __init__(
        self,
        client_manager: ClientManager,
        config: dict,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize the skeleton generator.
        
        Args:
            client_manager: Manager for API clients
            config: Configuration dictionary
            logger: Logger instance
        """
        self.client_manager = client_manager
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
    
    def _compute_hash(self, text: str) -> str:
        """Compute SHA256 hash as UID.
        
        Args:
            text: Text to hash
            
        Returns:
            16-character hash string
        """
        return hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]
    
    def _load_existing_hashes(self, hash_file: Path) -> set:
        """Load existing hashes from file.
        
        Args:
            hash_file: Path to hash table file
            
        Returns:
            Set of existing hash strings
        """
        if not hash_file.exists():
            return set()
        
        with open(hash_file, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f if line.strip())
    
    def _build_prompt(self, problem_text: str, template: str) -> str:
        """Build skeleton generation prompt from template.
        
        Args:
            problem_text: Algorithm problem description
            template: Prompt template with {{problem}} placeholder
            
        Returns:
            Complete prompt string
        """
        return template.replace("{{problem}}", problem_text.strip())
    
    def _extract_function_name(self, skeleton_code: str) -> Optional[str]:
        """Extract function name from skeleton code.
        
        Args:
            skeleton_code: Generated function skeleton
            
        Returns:
            Function name if found, None otherwise
        """
        match = re.search(r'^def\s+([a-z_][a-z0-9_]*)\s*\(', skeleton_code, re.MULTILINE)
        return match.group(1) if match else None
    
    def _validate_skeleton(self, skeleton_code: str) -> bool:
        """Validate skeleton code using AST parsing.
        
        Args:
            skeleton_code: Generated function skeleton
            
        Returns:
            True if valid Python code, False otherwise
        """
        try:
            ast.parse(skeleton_code)
            return True
        except SyntaxError:
            return False
    
    async def _write_jsonl(self, file_path: Path, data: List[Dict]):
        """Write JSONL data asynchronously.
        
        Args:
            file_path: Output file path
            data: List of dictionaries to write
        """
        def _write():
            with open(file_path, 'a', encoding='utf-8') as f:
                for item in data:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        await asyncio.to_thread(_write)
    
    async def _write_hashes(self, file_path: Path, hashes: List[str]):
        """Write hashes asynchronously.
        
        Args:
            file_path: Hash table file path
            hashes: List of hash strings
        """
        def _write():
            with open(file_path, 'a', encoding='utf-8') as f:
                for h in hashes:
                    f.write(h + '\n')
        
        await asyncio.to_thread(_write)
    
    def _load_problems(self, input_file: Path, problem_key: str = "problem_description") -> List[Dict]:
        """Load problem descriptions from JSONL file.
        
        Args:
            input_file: Input JSONL file path
            problem_key: Key for problem text in each JSON object
            
        Returns:
            List of problem dictionaries
        """
        problems = []
        
        if not input_file.exists():
            self.logger.error(f"Input file not found: {input_file}")
            return problems
        
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        item = json.loads(line)
                        if problem_key in item:
                            problems.append(item)
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"Failed to parse JSON line: {e}")
        
        return problems
    
    async def generate(
        self,
        input_file: Path,
        output_dir: Path,
        prompt_template: str,
        num_samples: Optional[int] = None,
        temperature: float = 0.7,
        top_p: float = 0.95,
        max_tokens: int = 512,
        stop: Optional[List[str]] = None,
        batch_write_size: int = 50,
        problem_key: str = "problem_description"
    ) -> List[Dict]:
        """Generate function skeletons from problem descriptions.
        
        Args:
            input_file: Input JSONL file with problem descriptions
            output_dir: Output directory for skeletons
            prompt_template: Prompt template with {{problem}} placeholder
            num_samples: Number of samples to process (None = all)
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            max_tokens: Maximum tokens per generation
            stop: Stop sequences
            batch_write_size: Write to disk every N samples
            problem_key: Key for problem text in input JSON
            
        Returns:
            List of generated skeleton dictionaries
        """
        self.logger.info(f"=== Skeleton Generator ===")
        self.logger.info(f"Input: {input_file}")
        self.logger.info(f"Output: {output_dir}")
        
        # Setup output paths
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "skeletons.jsonl"
        hash_file = output_dir / "hash_table.txt"
        
        # Load existing hashes
        existing_hashes = self._load_existing_hashes(hash_file)
        self.logger.info(f"Loaded {len(existing_hashes)} existing hashes")
        
        # Load problems
        problems = self._load_problems(input_file, problem_key)
        self.logger.info(f"Loaded {len(problems)} problem descriptions")
        
        if num_samples is not None:
            problems = problems[:num_samples]
            self.logger.info(f"Limited to {len(problems)} samples")
        
        if not problems:
            self.logger.warning("No problems to process")
            return []
        
        # Get client
        client = self.client_manager.completion_client
        self.logger.info(f"Client: {client.base_url}, Model: {client.model}")
        
        # Calculate batching
        max_concurrent = getattr(client.semaphore, '_value', 5)
        num_batches = math.ceil(len(problems) / max_concurrent)
        
        self.logger.info(f"Batching: {num_batches} batches, max_concurrent={max_concurrent}")
        self.logger.info(f"Parameters: temp={temperature}, top_p={top_p}, max_tokens={max_tokens}")
        
        # Generation loop
        all_results = []
        pending_write = []
        pending_hashes = []
        total_processed = 0
        total_duplicates = 0
        total_invalid = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
        ) as progress:
            task_id = progress.add_task(
                "[cyan]Generating function skeletons...",
                total=len(problems)
            )
            
            # Process in batches
            for batch_idx in range(num_batches):
                batch_start = batch_idx * max_concurrent
                batch_end = min(batch_start + max_concurrent, len(problems))
                batch_problems = problems[batch_start:batch_end]
                
                # Build prompts for batch
                batch_prompts = [
                    self._build_prompt(p.get(problem_key, ""), prompt_template)
                    for p in batch_problems
                ]
                
                self.logger.info(f"[Batch {batch_idx+1}/{num_batches}] Processing {len(batch_prompts)} problems...")
                
                try:
                    # Call API with batch
                    batch_results = await client.complete_batch_async(
                        prompts=batch_prompts,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        top_p=top_p,
                        n=1,
                        stop=stop
                    )
                    
                    self.logger.info(f"[Batch {batch_idx+1}/{num_batches}] Received {len(batch_results)} responses")
                    
                    # Process results
                    for idx, result_list in enumerate(batch_results):
                        problem_data = batch_problems[idx]
                        problem_text = problem_data.get(problem_key, "")
                        
                        for result in result_list:
                            skeleton_code = result.get("text", "").strip()
                            
                            if not skeleton_code:
                                continue
                            
                            # Compute hash
                            uid = self._compute_hash(skeleton_code)
                            
                            # Check duplicates
                            if uid in existing_hashes or uid in pending_hashes:
                                total_duplicates += 1
                                continue
                            
                            # Validate
                            is_valid = self._validate_skeleton(skeleton_code)
                            if not is_valid:
                                total_invalid += 1
                                self.logger.debug(f"Invalid skeleton: {uid}")
                            
                            # Extract function name
                            function_name = self._extract_function_name(skeleton_code)
                            
                            # Add to pending
                            pending_hashes.append(uid)
                            pending_write.append({
                                "uid": uid,
                                "source": problem_data.get("source", "UNKNOWN"),
                                "problem_text": problem_text,
                                "skeleton_code": skeleton_code,
                                "function_name": function_name,
                                "valid": is_valid
                            })
                    
                    total_processed += len(batch_prompts)
                    progress.update(task_id, advance=len(batch_prompts))
                    
                    # Incremental write
                    if len(pending_write) >= batch_write_size:
                        write_count = len(pending_write)
                        self.logger.info(f"Writing {write_count} skeletons to disk...")
                        
                        await self._write_jsonl(output_file, pending_write)
                        await self._write_hashes(hash_file, pending_hashes)
                        
                        existing_hashes.update(pending_hashes)
                        all_results.extend(pending_write)
                        
                        pending_write = []
                        pending_hashes = []
                        
                        self.logger.info(f"✅ Wrote {write_count} skeletons (total unique: {len(all_results)})")
                
                except Exception as e:
                    self.logger.error(f"Error in batch {batch_idx+1}: {e}", exc_info=True)
        
        # Write remaining
        if pending_write:
            self.logger.info(f"Writing final {len(pending_write)} skeletons...")
            await self._write_jsonl(output_file, pending_write)
            await self._write_hashes(hash_file, pending_hashes)
            all_results.extend(pending_write)
            
            # Wait for writes to complete
            await asyncio.sleep(0.5)
        
        # Summary
        self.logger.info(f"✅ Skeleton generation complete!")
        self.logger.info(f"  Total unique skeletons: {len(all_results)}")
        self.logger.info(f"  Duplicates skipped: {total_duplicates}")
        self.logger.info(f"  Invalid skeletons: {total_invalid}")
        self.logger.info(f"  Output: {output_file}")
        self.logger.info(f"  Hash table: {hash_file}")
        
        return all_results


