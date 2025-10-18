"""
Code Generator (CodeGen)

Core module for generating Python function implementations from skeletons.
Reads problem descriptions and function skeletons, then generates complete implementations.
"""

import asyncio
import ast
import hashlib
import json
import logging
import math
import re
from pathlib import Path
from typing import List, Dict, Optional, Set

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn

from ...core.client_manager import ClientManager


class CodeGenerator:
    """
    Generates complete Python function implementations from skeletons.

    Features:
    - Batch async generation for high throughput
    - AST validation of generated code
    - Import extraction and validation
    - Hash-based deduplication
    - Incremental writing to disk
    """

    def __init__(
        self,
        client_manager: ClientManager,
        config: dict,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize the code generator.

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

    def _build_prompt(self, problem_text: str, skeleton_code: str, template: str) -> str:
        """Build code generation prompt from template.

        Args:
            problem_text: Algorithm problem description
            skeleton_code: Function skeleton with docstring
            template: Prompt template with {{problem}} and {{skeleton}} placeholders

        Returns:
            Complete prompt string
        """
        prompt = template.replace("{{problem}}", problem_text.strip())
        prompt = prompt.replace("{{skeleton}}", skeleton_code.strip())
        return prompt

    def _extract_imports(self, code: str) -> List[str]:
        """Extract import statements from code.

        Args:
            code: Python code string

        Returns:
            List of import statements
        """
        imports = []
        for line in code.split('\n'):
            stripped = line.strip()
            if stripped.startswith('import ') or stripped.startswith('from '):
                imports.append(stripped)
        return imports

    def _validate_syntax(self, code: str) -> bool:
        """Validate Python syntax using AST parsing.

        Args:
            code: Python code string

        Returns:
            True if valid Python code, False otherwise
        """
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    def _check_body_format(self, body: str) -> bool:
        """Check if body is actually function body (not full function definition).

        Args:
            body: Generated text

        Returns:
            True if it looks like function body, False if it's a full function definition
        """
        # If starts with 'def ', it's a full function (wrong format)
        if body.lstrip().startswith('def '):
            return False
        return True
    
    def _check_body_has_code(self, body: str) -> bool:
        """Check if body contains actual code (not just empty lines or comments).
        
        Args:
            body: Generated function body
            
        Returns:
            True if body has actual code statements, False otherwise
        """
        if not body or not body.strip():
            return False
        
        # Check if there's any non-empty, non-comment line
        for line in body.split('\n'):
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                # Has actual code
                return True
        
        return False

    def _combine_skeleton_and_body(self, skeleton: str, body: str) -> str:
        """Combine function skeleton with generated body.

        Args:
            skeleton: Function definition with docstring
            body: Generated function body

        Returns:
            Complete function implementation
        """
        # Remove trailing whitespace from skeleton
        skeleton = skeleton.rstrip()
        
        # Ensure body has proper indentation
        body_lines = body.split('\n')
        indented_body = []
        for line in body_lines:
            if line.strip():  # Non-empty line
                # Ensure at least 4 spaces indentation
                if not line.startswith('    '):
                    indented_body.append('    ' + line.lstrip())
                else:
                    indented_body.append(line)
            else:
                indented_body.append(line)
        
        # Combine
        return skeleton + '\n' + '\n'.join(indented_body)

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

    def _load_skeletons(
        self,
        input_file: Path,
        problem_key: str = "problem_text",
        skeleton_key: str = "skeleton_code",
        function_name_key: str = "function_name",
        valid_key: str = "valid",
        skip_invalid: bool = True
    ) -> List[Dict]:
        """Load function skeletons from JSONL file.

        Args:
            input_file: Input JSONL file path
            problem_key: Key for problem text
            skeleton_key: Key for skeleton code
            function_name_key: Key for function name
            valid_key: Key for validity flag
            skip_invalid: Whether to skip invalid skeletons

        Returns:
            List of skeleton dictionaries
        """
        skeletons = []

        if not input_file.exists():
            self.logger.error(f"Input file not found: {input_file}")
            return skeletons

        with open(input_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if line.strip():
                    try:
                        item = json.loads(line)
                        
                        # Check if skeleton is valid
                        if skip_invalid and not item.get(valid_key, True):
                            continue
                        
                        # Check required keys
                        if problem_key in item and skeleton_key in item:
                            skeletons.append(item)
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"Failed to parse JSON line {line_num}: {e}")

        return skeletons

    async def generate(
        self,
        input_file: Path,
        output_dir: Path,
        prompt_template: str,
        num_samples: Optional[int] = None,
        temperature: float = 0.7,
        top_p: float = 0.95,
        max_tokens: int = 1024,
        stop: Optional[List[str]] = None,
        batch_write_size: int = 50,
        problem_key: str = "problem_text",
        skeleton_key: str = "skeleton_code",
        function_name_key: str = "function_name",
        skip_invalid: bool = True,
        validate_syntax: bool = True,
        validate_imports: bool = True
    ) -> List[Dict]:
        """Generate function implementations from skeletons.

        Args:
            input_file: Input JSONL file with skeletons
            output_dir: Output directory for implementations
            prompt_template: Prompt template with {{problem}} and {{skeleton}} placeholders
            num_samples: Number of samples to process (None = all)
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            max_tokens: Maximum tokens per generation
            stop: Stop sequences
            batch_write_size: Write to disk every N samples
            problem_key: Key for problem text in input JSON
            skeleton_key: Key for skeleton code in input JSON
            function_name_key: Key for function name in input JSON
            skip_invalid: Whether to skip invalid skeletons
            validate_syntax: Whether to validate generated code syntax
            validate_imports: Whether to extract and validate imports

        Returns:
            List of generated implementation dictionaries
        """
        self.logger.info(f"=== Code Generator ===")
        self.logger.info(f"Input: {input_file}")
        self.logger.info(f"Output: {output_dir}")

        # Setup output paths
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "implementations.jsonl"
        hash_file = output_dir / "hash_table.txt"

        # Load existing hashes
        existing_hashes = self._load_existing_hashes(hash_file)
        self.logger.info(f"Loaded {len(existing_hashes)} existing hashes")

        # Load skeletons
        skeletons = self._load_skeletons(
            input_file,
            problem_key,
            skeleton_key,
            function_name_key,
            "valid",
            skip_invalid
        )
        self.logger.info(f"Loaded {len(skeletons)} valid function skeletons")

        if num_samples is not None:
            skeletons = skeletons[:num_samples]

        if not skeletons:
            self.logger.warning("No skeletons to process")
            return []

        # Get client
        client = self.client_manager.completion_client
        self.logger.info(f"Client: {client.base_url}, Model: {client.model}")

        # Calculate batching
        max_concurrent = getattr(client.semaphore, '_value', 5)
        num_batches = math.ceil(len(skeletons) / max_concurrent)

        self.logger.info(f"Batching: {num_batches} batches, max_concurrent={max_concurrent}")
        self.logger.info(f"Parameters: temp={temperature}, top_p={top_p}, max_tokens={max_tokens}")

        # Generation loop
        all_results = []
        pending_write = []
        pending_hashes = []
        total_processed = 0
        total_duplicates = 0
        total_invalid_syntax = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
        ) as progress:
            task_id = progress.add_task(
                "[cyan]Generating function implementations...",
                total=len(skeletons)
            )

            # Process in batches
            for batch_idx in range(num_batches):
                batch_start = batch_idx * max_concurrent
                batch_end = min(batch_start + max_concurrent, len(skeletons))
                batch_skeletons = skeletons[batch_start:batch_end]

                # Build prompts for batch
                batch_prompts = [
                    self._build_prompt(
                        s.get(problem_key, ""),
                        s.get(skeleton_key, ""),
                        prompt_template
                    )
                    for s in batch_skeletons
                ]

                self.logger.info(f"[Batch {batch_idx+1}/{num_batches}] Processing {len(batch_prompts)} skeletons...")

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

                    # Collect tasks that need retry
                    retry_tasks = []
                    
                    # Process results
                    self.logger.debug(f"[Batch {batch_idx+1}/{num_batches}] Processing {len(batch_results)} results")
                    for idx, result_list in enumerate(batch_results):
                        skeleton_data = batch_skeletons[idx]
                        problem_text = skeleton_data.get(problem_key, "")
                        skeleton_code = skeleton_data.get(skeleton_key, "")
                        function_name = skeleton_data.get(function_name_key, "")

                        for result in result_list:
                            body_code = result.get("text", "").strip()
                            
                            # Log raw model output
                            self.logger.debug(f"[{function_name}] Raw output (first 200 chars): {body_code[:200]}")

                            if not body_code:
                                self.logger.debug(f"[{function_name}] Empty response")
                                continue

                            # Check if format is correct (should be function body, not full function)
                            if not self._check_body_format(body_code):
                                self.logger.debug(f"[{function_name}] Wrong format, adding to retry queue")
                                self.logger.debug(f"[{function_name}] Wrong format output: {body_code[:300]}")
                                # Add to retry queue (up to 3 attempts)
                                retry_tasks.append({
                                    'skeleton_data': skeleton_data,
                                    'problem_text': problem_text,
                                    'skeleton_code': skeleton_code,
                                    'function_name': function_name,
                                    'attempts': 0,
                                    'max_attempts': 3
                                })
                                continue
                            
                            # Check if body contains actual code
                            if not self._check_body_has_code(body_code):
                                self.logger.debug(f"[{function_name}] Empty body (no actual code), adding to retry queue")
                                retry_tasks.append({
                                    'skeleton_data': skeleton_data,
                                    'problem_text': problem_text,
                                    'skeleton_code': skeleton_code,
                                    'function_name': function_name,
                                    'attempts': 0,
                                    'max_attempts': 3
                                })
                                continue

                            # Combine skeleton and body
                            full_implementation = self._combine_skeleton_and_body(
                                skeleton_code,
                                body_code
                            )

                            # Compute hash
                            uid = self._compute_hash(full_implementation)

                            # Check duplicates
                            if uid in existing_hashes or uid in pending_hashes:
                                total_duplicates += 1
                                continue

                            # Validate syntax
                            if validate_syntax:
                                is_valid = self._validate_syntax(full_implementation)
                                if not is_valid:
                                    total_invalid_syntax += 1
                                    self.logger.debug(f"Invalid syntax (skipping): {uid}")
                                    continue  # Skip invalid implementations

                            # Add to pending (only valid code reaches here)
                            pending_hashes.append(uid)
                            pending_write.append({
                                "uid": uid,
                                "source": skeleton_data.get("source", "UNKNOWN"),
                                "problem_text": problem_text,
                                "code": full_implementation,
                                "function_name": function_name
                            })
                    
                    # Process retry queue asynchronously
                    if retry_tasks:
                        self.logger.debug(f"Processing {len(retry_tasks)} retry tasks...")
                        retry_prompts = [
                            self._build_prompt(task['problem_text'], task['skeleton_code'], prompt_template)
                            for task in retry_tasks
                        ]
                        
                        try:
                            retry_results = await client.complete_batch_async(
                                prompts=retry_prompts,
                                max_tokens=max_tokens,
                                temperature=temperature,
                                top_p=top_p,
                                n=1,
                                stop=stop
                            )
                            
                            retry_success_count = 0
                            for task_idx, result_list in enumerate(retry_results):
                                task = retry_tasks[task_idx]
                                task['attempts'] += 1
                                
                                for result in result_list:
                                    retry_body = result.get("text", "").strip()
                                    self.logger.debug(f"[{task['function_name']}] Retry {task['attempts']} output: {retry_body[:200]}")
                                    
                                    if retry_body and self._check_body_format(retry_body) and self._check_body_has_code(retry_body):
                                        # Success! Process this result
                                        full_implementation = self._combine_skeleton_and_body(
                                            task['skeleton_code'],
                                            retry_body
                                        )
                                        uid = self._compute_hash(full_implementation)
                                        
                                        if uid not in existing_hashes and uid not in pending_hashes:
                                            if validate_syntax and not self._validate_syntax(full_implementation):
                                                total_invalid_syntax += 1
                                                continue
                                            
                                            pending_hashes.append(uid)
                                            pending_write.append({
                                                "uid": uid,
                                                "source": task['skeleton_data'].get("source", "UNKNOWN"),
                                                "problem_text": task['problem_text'],
                                                "code": full_implementation,
                                                "function_name": task['function_name']
                                            })
                                            retry_success_count += 1
                                            self.logger.debug(f"✓ Retry succeeded for {task['function_name']}")
                                        break
                            
                            self.logger.debug(f"Retry batch: {retry_success_count}/{len(retry_tasks)} succeeded")
                            
                        except Exception as e:
                            self.logger.error(f"Retry batch failed: {e}")

                    total_processed += len(batch_prompts)
                    progress.update(task_id, advance=len(batch_prompts))
                    
                    self.logger.debug(f"[Batch {batch_idx+1}/{num_batches}] Pending write: {len(pending_write)}, batch_write_size: {batch_write_size}")

                    # Incremental write
                    if len(pending_write) >= batch_write_size:
                        write_count = len(pending_write)

                        await self._write_jsonl(output_file, pending_write)
                        await self._write_hashes(hash_file, pending_hashes)

                        existing_hashes.update(pending_hashes)
                        all_results.extend(pending_write)

                        pending_write = []
                        pending_hashes = []

                        self.logger.info(f"✅ Progress: {len(all_results)} implementations generated")

                except Exception as e:
                    self.logger.error(f"Error in batch {batch_idx+1}: {e}", exc_info=True)

        # Write remaining
        if pending_write:
            await self._write_jsonl(output_file, pending_write)
            await self._write_hashes(hash_file, pending_hashes)
            all_results.extend(pending_write)

            # Wait for writes to complete
            await asyncio.sleep(0.5)

        # Summary
        self.logger.info(f"✅ Code generation complete!")
        self.logger.info(f"  Total unique implementations: {len(all_results)}")
        self.logger.info(f"  Duplicates skipped: {total_duplicates}")
        self.logger.info(f"  Invalid syntax: {total_invalid_syntax}")
        self.logger.info(f"  Output: {output_file}")
        self.logger.info(f"  Hash table: {hash_file}")

        return all_results

