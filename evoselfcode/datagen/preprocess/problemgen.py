"""
Problem Description Generator (ProblemGen)

Core module for generating algorithm problem descriptions using LLM.
Supports both FIM (Fill-in-the-Middle) and L2R (Left-to-Right) generation modes.
"""

import asyncio
import hashlib
import json
import logging
import math
from pathlib import Path
from typing import List, Dict, Literal, Optional

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn

from ...core.client_manager import ClientManager
from ...core.prompt_builder import PromptBuilder


class ProblemGenerator:
    """
    Generates algorithm problem descriptions using LLM.
    
    Features:
    - Batch async generation for high throughput
    - Hash-based deduplication
    - Incremental writing to disk
    - Support for FIM and L2R modes
    """
    
    def __init__(
        self,
        client_manager: ClientManager,
        prompt_builder: PromptBuilder,
        config: dict,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize the problem generator.
        
        Args:
            client_manager: Manager for API clients
            prompt_builder: Builder for constructing prompts
            config: Configuration dictionary
            logger: Logger instance
        """
        self.client_manager = client_manager
        self.prompt_builder = prompt_builder
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
    
    async def generate(
        self,
        mode: Literal["FIM", "L2R"],
        num_samples: int,
        output_dir: Path,
        temperature: float = 1.0,
        top_p: float = 0.95,
        max_tokens: int = 2048,
        stop: Optional[List[str]] = None,
        batch_write_size: int = 50
    ) -> List[Dict]:
        """Generate algorithm problem descriptions.
        
        Args:
            mode: Generation mode ("FIM" or "L2R")
            num_samples: Number of problems to generate
            output_dir: Output directory for results
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            max_tokens: Maximum tokens per generation
            stop: Stop sequences
            batch_write_size: Write to disk every N samples
            
        Returns:
            List of generated problem dictionaries
        """
        self.logger.info(f"=== Problem Generator: {mode} Mode ===")
        self.logger.info(f"Target samples: {num_samples}")
        self.logger.info(f"Output directory: {output_dir}")
        
        # Setup output paths
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{mode.lower()}_results.jsonl"
        hash_file = output_dir / "hash_table.txt"
        
        # Load existing hashes for deduplication
        existing_hashes = self._load_existing_hashes(hash_file)
        self.logger.info(f"Loaded {len(existing_hashes)} existing hashes")
        
        # Get client
        client = self.client_manager.completion_client
        self.logger.info(f"Client: {client.base_url}, Model: {client.model}")
        
        # Build base prompt
        if mode == "FIM":
            base_prompt = self.prompt_builder.build_funcname_fim()
        else:  # L2R
            base_prompt = self.prompt_builder.build_funcname_l2r()
        
        self.logger.debug(f"Base prompt preview: {base_prompt[:100]}...")
        
        # Calculate batch size from client's semaphore
        max_concurrent = getattr(client.semaphore, '_value', 5)
        num_batches = math.ceil(num_samples / max_concurrent)
        
        self.logger.info(f"Batching: {num_batches} batches, max_concurrent={max_concurrent}")
        self.logger.info(f"Parameters: temp={temperature}, top_p={top_p}, max_tokens={max_tokens}")
        
        # Generation loop with batching
        all_results = []
        pending_write = []
        pending_hashes = []
        total_generated = 0
        total_duplicates = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
        ) as progress:
            task_id = progress.add_task(
                f"[cyan]Generating {mode} problems...",
                total=num_samples
            )
            
            for batch_idx in range(num_batches):
                # Calculate batch size
                remaining = num_samples - total_generated
                batch_size = min(max_concurrent, remaining)
                
                if batch_size <= 0:
                    break
                
                # Prepare batch prompts
                batch_prompts = [base_prompt] * batch_size
                
                self.logger.info(f"[Batch {batch_idx+1}/{num_batches}] Requesting {batch_size} samples...")
                
                # Call API with batch
                try:
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
                    for result_list in batch_results:
                        for result in result_list:
                            raw_text = result.get("text", "").strip()
                            
                            if not raw_text:
                                continue
                            
                            # Compute hash
                            uid = self._compute_hash(raw_text)
                            
                            # Check duplicates
                            if uid in existing_hashes or uid in pending_hashes:
                                total_duplicates += 1
                                continue
                            
                            # Add to pending
                            pending_hashes.append(uid)
                            pending_write.append({
                                "uid": uid,
                                "problem_description": raw_text,
                                "source": mode,
                                "raw_text": raw_text
                            })
                    
                    total_generated += batch_size
                    progress.update(task_id, advance=batch_size)
                    
                    # Incremental write
                    if len(pending_write) >= batch_write_size:
                        write_count = len(pending_write)
                        self.logger.info(f"Writing {write_count} samples to disk...")
                        
                        await self._write_jsonl(output_file, pending_write)
                        await self._write_hashes(hash_file, pending_hashes)
                        
                        existing_hashes.update(pending_hashes)
                        all_results.extend(pending_write)
                        
                        pending_write = []
                        pending_hashes = []
                        
                        self.logger.info(f"✅ Wrote {write_count} samples (total unique: {len(all_results)})")
                
                except Exception as e:
                    self.logger.error(f"Error in batch {batch_idx+1}: {e}", exc_info=True)
        
        # Write remaining
        if pending_write:
            self.logger.info(f"Writing final {len(pending_write)} samples...")
            await self._write_jsonl(output_file, pending_write)
            await self._write_hashes(hash_file, pending_hashes)
            all_results.extend(pending_write)
            
            # Wait for writes to complete
            await asyncio.sleep(0.5)
        
        # Summary
        self.logger.info(f"✅ Generation complete!")
        self.logger.info(f"  Total unique problems: {len(all_results)}")
        self.logger.info(f"  Duplicates skipped: {total_duplicates}")
        self.logger.info(f"  Output: {output_file}")
        self.logger.info(f"  Hash table: {hash_file}")
        
        return all_results

