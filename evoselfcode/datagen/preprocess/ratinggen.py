"""
Rating Generator Module

This module generates quality ratings for function implementations using LLM evaluation.
"""

import asyncio
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Dict, List, Optional

from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeRemainingColumn,
)


class RatingGenerator:
    """Generator for quality ratings of function implementations."""

    def __init__(self, client_manager, config: Dict, logger):
        """Initialize rating generator.

        Args:
            client_manager: Manager for API clients
            config: Rating generation configuration
            logger: Logger instance
        """
        self.client_manager = client_manager
        self.config = config
        self.logger = logger

    def _compute_hash(self, text: str) -> str:
        """Compute SHA256 hash of text.

        Args:
            text: Input text

        Returns:
            First 16 characters of hex digest
        """
        return hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]

    def _load_existing_hashes(self, hash_file: Path) -> set:
        """Load existing hashes from file.

        Args:
            hash_file: Path to hash table file

        Returns:
            Set of existing hashes
        """
        if not hash_file.exists():
            return set()

        with open(hash_file, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f if line.strip())

    def _load_implementations(
        self,
        input_file: Path,
        problem_key: str,
        code_key: str,
        function_name_key: str,
        uid_key: str,
        source_key: str
    ) -> List[Dict]:
        """Load implementations from JSONL file.

        Args:
            input_file: Path to input JSONL file
            problem_key: Key for problem text
            code_key: Key for code
            function_name_key: Key for function name
            uid_key: Key for unique ID
            source_key: Key for source mode

        Returns:
            List of implementation dictionaries
        """
        if not input_file.exists():
            self.logger.error(f"Input file not found: {input_file}")
            return []

        implementations = []
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    implementations.append({
                        'problem_text': data.get(problem_key, ""),
                        'code': data.get(code_key, ""),
                        'function_name': data.get(function_name_key, ""),
                        'uid': data.get(uid_key, ""),
                        'source': data.get(source_key, "UNKNOWN")
                    })

        return implementations

    def _build_prompt(self, problem_text: str, code: str, template: str) -> str:
        """Build rating prompt from template.

        Args:
            problem_text: Problem description
            code: Function implementation
            template: Prompt template with placeholders

        Returns:
            Formatted prompt string
        """
        return template.replace("{{problem_text}}", problem_text).replace("{{code}}", code)

    def _parse_rating(self, raw_text: str) -> Dict:
        """Parse rating output into structured scores.

        Expected format:
        Problem Design Score: 5
        Function Definition Score: 4
        Algorithm Correctness Score: 5
        Algorithm Efficiency Score: 4
        Code Readability Score: 5
        Summary: ...

        Args:
            raw_text: Raw model output

        Returns:
            Dictionary with parsed scores and summary
        """
        patterns = {
            'problem_design': r'Problem\s+Design\s+Score:\s*(\d+)',
            'function_definition': r'Function\s+Definition\s+Score:\s*(\d+)',
            'correctness': r'Algorithm\s+Correctness\s+Score:\s*(\d+)',
            'efficiency': r'Algorithm\s+Efficiency\s+Score:\s*(\d+)',
            'readability': r'Code\s+Readability\s+Score:\s*(\d+)',
            'summary': r'Summary:\s*(.+?)(?:\n\n|---|\Z)'
        }

        result = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, raw_text, re.IGNORECASE | re.DOTALL)
            if match:
                if key == 'summary':
                    result[key] = match.group(1).strip()
                else:
                    try:
                        result[key] = int(match.group(1))
                    except ValueError:
                        result[key] = None
            else:
                result[key] = None

        return result

    def _validate_scores(
        self,
        scores: Dict,
        min_score: int = 1,
        max_score: int = 5
    ) -> bool:
        """Validate that all scores are in valid range.

        Args:
            scores: Dictionary of scores
            min_score: Minimum valid score
            max_score: Maximum valid score

        Returns:
            True if all scores are valid, False otherwise
        """
        required_keys = ['problem_design', 'function_definition', 'correctness', 'efficiency', 'readability']

        for key in required_keys:
            score = scores.get(key)
            if score is None or not isinstance(score, int):
                return False
            if not (min_score <= score <= max_score):
                return False

        # Check summary exists
        if not scores.get('summary'):
            return False

        return True

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
        """Write hash table asynchronously.

        Args:
            file_path: Output file path
            hashes: List of hashes to write
        """
        def _write():
            with open(file_path, 'a', encoding='utf-8') as f:
                for h in hashes:
                    f.write(h + '\n')

        await asyncio.to_thread(_write)

    async def generate(
        self,
        input_file: Path,
        output_dir: Path,
        prompt_template: str,
        num_samples: Optional[int] = None,
        temperature: float = 0.3,
        top_p: float = 0.9,
        max_tokens: int = 1024,
        stop: Optional[List[str]] = None,
        batch_write_size: int = 50,
        problem_key: str = "problem_text",
        code_key: str = "code",
        function_name_key: str = "function_name",
        uid_key: str = "uid",
        source_key: str = "source",
        validate_scores: bool = True,
        min_score: int = 1,
        max_score: int = 5
    ) -> List[Dict]:
        """Generate quality ratings for implementations.

        Args:
            input_file: Input JSONL file with implementations
            output_dir: Output directory for ratings
            prompt_template: Prompt template with {{problem_text}} and {{code}} placeholders
            num_samples: Number of samples to process (None = all)
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            max_tokens: Maximum tokens per generation
            stop: Stop sequences
            batch_write_size: Write to disk every N samples
            problem_key: Key for problem text in input JSON
            code_key: Key for code in input JSON
            function_name_key: Key for function name in input JSON
            uid_key: Key for UID in input JSON
            source_key: Key for source in input JSON
            validate_scores: Whether to validate scores
            min_score: Minimum valid score
            max_score: Maximum valid score

        Returns:
            List of rating dictionaries
        """
        self.logger.info(f"=== Rating Generator ===")
        self.logger.info(f"Input: {input_file}")
        self.logger.info(f"Output: {output_dir}")

        # Setup output paths
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "ratings.jsonl"
        hash_file = output_dir / "hash_table.txt"

        # Load existing hashes (UIDs of already-rated implementations)
        existing_hashes = self._load_existing_hashes(hash_file)
        self.logger.info(f"Loaded {len(existing_hashes)} existing ratings")

        # Load implementations
        implementations = self._load_implementations(
            input_file,
            problem_key,
            code_key,
            function_name_key,
            uid_key,
            source_key
        )
        self.logger.info(f"Loaded {len(implementations)} implementations")

        # Filter out already-rated implementations
        implementations = [impl for impl in implementations if impl['uid'] not in existing_hashes]
        self.logger.info(f"Filtered to {len(implementations)} unrated implementations")

        if num_samples is not None:
            implementations = implementations[:num_samples]

        if not implementations:
            self.logger.warning("No implementations to rate")
            return []

        # Get client
        client = self.client_manager.completion_client
        self.logger.info(f"Client: {client.base_url}, Model: {client.model}")

        # Calculate batching
        max_concurrent = getattr(client.semaphore, '_value', 5)
        num_batches = math.ceil(len(implementations) / max_concurrent)

        self.logger.info(f"Batching: {num_batches} batches, max_concurrent={max_concurrent}")
        self.logger.info(f"Parameters: temp={temperature}, top_p={top_p}, max_tokens={max_tokens}")

        # Generation loop
        all_results = []
        pending_write = []
        pending_hashes = []
        total_processed = 0
        total_parse_failures = 0
        total_invalid_scores = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
        ) as progress:
            task_id = progress.add_task(
                "[cyan]Generating quality ratings...",
                total=len(implementations)
            )

            # Process in batches
            for batch_idx in range(num_batches):
                batch_start = batch_idx * max_concurrent
                batch_end = min(batch_start + max_concurrent, len(implementations))
                batch_implementations = implementations[batch_start:batch_end]

                # Build prompts for batch
                batch_prompts = [
                    self._build_prompt(
                        impl['problem_text'],
                        impl['code'],
                        prompt_template
                    )
                    for impl in batch_implementations
                ]

                self.logger.info(f"[Batch {batch_idx+1}/{num_batches}] Processing {len(batch_prompts)} implementations...")

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
                        impl_data = batch_implementations[idx]
                        function_name = impl_data['function_name']

                        for result in result_list:
                            rating_text = result.get("text", "").strip()

                            self.logger.debug(f"[{function_name}] Raw rating output (first 200 chars): {rating_text[:200]}")

                            if not rating_text:
                                self.logger.debug(f"[{function_name}] Empty response")
                                continue

                            # Parse rating
                            parsed_rating = self._parse_rating(rating_text)

                            # Validate scores
                            if validate_scores and not self._validate_scores(parsed_rating, min_score, max_score):
                                self.logger.debug(f"[{function_name}] Invalid scores, adding to retry queue")
                                self.logger.debug(f"[{function_name}] Parsed: {parsed_rating}")
                                retry_tasks.append({
                                    'impl_data': impl_data,
                                    'function_name': function_name,
                                    'attempts': 0,
                                    'max_attempts': 3
                                })
                                continue

                            # Add to pending write
                            pending_write.append({
                                "uid": impl_data['uid'],
                                "source": impl_data['source'],
                                "problem_text": impl_data['problem_text'],
                                "code": impl_data['code'],
                                "function_name": function_name,
                                "ratings": {
                                    "problem_design": parsed_rating['problem_design'],
                                    "function_definition": parsed_rating['function_definition'],
                                    "correctness": parsed_rating['correctness'],
                                    "efficiency": parsed_rating['efficiency'],
                                    "readability": parsed_rating['readability']
                                },
                                "summary": parsed_rating['summary'],
                                "raw_rating_text": rating_text
                            })
                            pending_hashes.append(impl_data['uid'])

                    # Process retry queue asynchronously
                    if retry_tasks:
                        self.logger.debug(f"Processing {len(retry_tasks)} retry tasks...")
                        retry_prompts = [
                            self._build_prompt(task['impl_data']['problem_text'], task['impl_data']['code'], prompt_template)
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
                                    retry_text = result.get("text", "").strip()
                                    self.logger.debug(f"[{task['function_name']}] Retry {task['attempts']} output: {retry_text[:200]}")

                                    if retry_text:
                                        parsed_retry = self._parse_rating(retry_text)
                                        if not validate_scores or self._validate_scores(parsed_retry, min_score, max_score):
                                            # Success! Add this result
                                            pending_write.append({
                                                "uid": task['impl_data']['uid'],
                                                "source": task['impl_data']['source'],
                                                "problem_text": task['impl_data']['problem_text'],
                                                "code": task['impl_data']['code'],
                                                "function_name": task['function_name'],
                                                "ratings": {
                                                    "problem_design": parsed_retry['problem_design'],
                                                    "function_definition": parsed_retry['function_definition'],
                                                    "correctness": parsed_retry['correctness'],
                                                    "efficiency": parsed_retry['efficiency'],
                                                    "readability": parsed_retry['readability']
                                                },
                                                "summary": parsed_retry['summary'],
                                                "raw_rating_text": retry_text
                                            })
                                            pending_hashes.append(task['impl_data']['uid'])
                                            retry_success_count += 1
                                            self.logger.debug(f"✓ Retry succeeded for {task['function_name']}")
                                            break
                                        else:
                                            total_invalid_scores += 1
                                    else:
                                        total_parse_failures += 1

                            self.logger.debug(f"Retry batch: {retry_success_count}/{len(retry_tasks)} succeeded")

                        except Exception as e:
                            self.logger.error(f"Retry batch failed: {e}")
                            total_parse_failures += len(retry_tasks)

                    total_processed += len(batch_prompts)
                    progress.update(task_id, advance=len(batch_prompts))

                    self.logger.debug(f"[Batch {batch_idx+1}/{num_batches}] Pending write: {len(pending_write)}, batch_write_size: {batch_write_size}")

                    # Incremental write
                    if len(pending_write) >= batch_write_size:
                        await self._write_jsonl(output_file, pending_write)
                        await self._write_hashes(hash_file, pending_hashes)

                        existing_hashes.update(pending_hashes)
                        all_results.extend(pending_write)

                        pending_write = []
                        pending_hashes = []

                        self.logger.info(f"✅ Progress: {len(all_results)} ratings generated")

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
        self.logger.info(f"✅ Rating generation complete!")
        self.logger.info(f"  Total ratings: {len(all_results)}")
        self.logger.info(f"  Parse failures: {total_parse_failures}")
        self.logger.info(f"  Invalid scores: {total_invalid_scores}")
        self.logger.info(f"  Output: {output_file}")
        self.logger.info(f"  Hash table: {hash_file}")

        return all_results

