"""
ChatML format converter for training data.

Converts rated function implementations to ChatML format suitable for fine-tuning.
Uses multiprocessing for efficient batch conversion.
"""

import ast
import json
import multiprocessing as mp
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from evoselfcode.core import ConfigManager
from evoselfcode.utils.logger import LoggerManager


def _process_record_worker(args):
    """Worker function for multiprocessing.
    
    Args:
        args: Tuple of (record_json, config_dict)
        
    Returns:
        Tuple of (success, result_or_error)
    """
    record_json, config_dict = args
    
    try:
        record = json.loads(record_json)
    except json.JSONDecodeError:
        return (False, "json_error", None)
    
    # Recreate converter settings
    min_ratings = config_dict["min_ratings"]
    require_all = config_dict["require_all"]
    output_fields = config_dict["output_fields"]
    
    # Check quality
    ratings = record.get("ratings", {})
    if min_ratings:
        if require_all:
            for dimension, min_score in min_ratings.items():
                if ratings.get(dimension, 0) < min_score:
                    return (False, "quality", None)
        else:
            passed = False
            for dimension, min_score in min_ratings.items():
                if ratings.get(dimension, 0) >= min_score:
                    passed = True
                    break
            if not passed:
                return (False, "quality", None)
    
    # Process record
    try:
        result = _convert_single_record(record, output_fields)
        if result:
            return (True, "success", json.dumps(result, ensure_ascii=False))
        else:
            return (False, "parse", None)
    except Exception as e:
        return (False, "error", str(e))


def _convert_single_record(record: Dict[str, Any], output_fields: List[str]) -> Optional[Dict[str, Any]]:
    """Convert a single record (called by worker).
    
    Args:
        record: Input record dict
        output_fields: List of fields to include in output
        
    Returns:
        Converted record or None
    """
    uid = record.get("uid")
    problem_text = record.get("problem_text", "")
    code = record.get("code", "")
    ratings = record.get("ratings", {})
    
    # Remove hint
    problem_no_hint = _remove_hint_static(problem_text)
    
    # Extract signature
    signature = _extract_signature_static(code)
    if not signature:
        return None
    
    # Extract body
    body = _extract_body_static(code)
    if not body:
        return None
    
    # Construct result
    user_content = f"{problem_no_hint}\n\n{signature}"
    assistant_content = body
    
    result = {
        "uid": uid,
        "messages": [
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": assistant_content}
        ]
    }
    
    if "ratings" in output_fields:
        result["ratings"] = ratings
    
    # Filter fields
    filtered = {k: v for k, v in result.items() if k in output_fields}
    return filtered


def _remove_hint_static(problem_text: str) -> str:
    """Static version of hint removal."""
    lines = problem_text.split('\n')
    filtered_lines = []
    skip_rest = False
    
    for line in lines:
        if line.strip().startswith("Hint:"):
            skip_rest = True
            continue
        if not skip_rest:
            filtered_lines.append(line)
    
    return '\n'.join(filtered_lines).strip()


def _extract_signature_static(code: str) -> Optional[str]:
    """Static version of signature extraction."""
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                lines = code.split('\n')
                for i, line in enumerate(lines):
                    if line.strip().startswith('def ') and node.name in line:
                        signature_lines = [line]
                        j = i + 1
                        while j < len(lines) and not signature_lines[-1].rstrip().endswith(':'):
                            signature_lines.append(lines[j])
                            j += 1
                        return '\n'.join(signature_lines).strip()
        return None
    except:
        return None


def _extract_body_static(code: str) -> Optional[str]:
    """Static version of body extraction."""
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                lines = code.split('\n')
                func_start_line = node.lineno - 1
                body_start = func_start_line + 1
                
                while body_start < len(lines) and not lines[body_start].strip():
                    body_start += 1
                
                if (node.body and 
                    isinstance(node.body[0], ast.Expr) and 
                    isinstance(node.body[0].value, ast.Constant) and
                    isinstance(node.body[0].value.value, str)):
                    docstring_end_line = node.body[0].end_lineno
                    body_start = docstring_end_line
                
                body_lines = []
                for i in range(body_start, len(lines)):
                    line = lines[i]
                    if line and not line[0].isspace() and line.strip():
                        break
                    body_lines.append(line)
                
                while body_lines and not body_lines[0].strip():
                    body_lines.pop(0)
                
                if not body_lines:
                    return None
                
                base_indent = len(body_lines[0]) - len(body_lines[0].lstrip())
                normalized_lines = []
                for line in body_lines:
                    if line.strip():
                        if len(line) >= base_indent:
                            normalized_lines.append(line[base_indent:])
                        else:
                            normalized_lines.append(line)
                    else:
                        normalized_lines.append('')
                
                return '\n'.join(normalized_lines).rstrip()
        return None
    except:
        return None


class ChatMLConverter:
    """Convert rated implementations to ChatML format.
    
    Transforms data by:
    - Removing hints from problem descriptions
    - Extracting function signature from code
    - Removing docstrings and keeping only function body
    - Filtering by quality ratings
    """
    
    def __init__(
        self,
        config: ConfigManager,
        logger: Optional[Any] = None
    ):
        """Initialize converter.
        
        Args:
            config: Configuration manager with conversion settings
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger or LoggerManager.get_logger(
            name="chatml_converter",
            module="datagen",
            task="convert"
        )
        
        # Load configuration
        self.filter_cfg = config.get_section("filter")
        self.output_cfg = config.get_section("output")
        self.processing_cfg = config.get_section("processing")
        
        # Quality thresholds
        self.min_ratings = self.filter_cfg.get("min_ratings", {})
        self.require_all = self.filter_cfg.get("require_all_above_threshold", True)
        
        # Output fields
        self.output_fields = self.output_cfg.get("fields", ["uid", "messages"])
        
        # Processing settings
        self.num_workers = self.processing_cfg.get("num_workers", 0)
        if self.num_workers == 0:
            self.num_workers = max(1, mp.cpu_count() - 1)
        self.chunk_size = self.processing_cfg.get("chunk_size", 500)
        
        self.logger.info(f"Initialized ChatML converter")
        self.logger.info(f"Quality filters: {self.min_ratings}")
        self.logger.info(f"Output fields: {self.output_fields}")
        self.logger.info(f"Workers: {self.num_workers}, Chunk size: {self.chunk_size}")
    
    def _remove_hint(self, problem_text: str) -> str:
        """Remove hint section from problem text.
        
        Args:
            problem_text: Original problem description
            
        Returns:
            Problem text without hint
        """
        # Remove lines starting with "Hint:"
        lines = problem_text.split('\n')
        filtered_lines = []
        skip_rest = False
        
        for line in lines:
            if line.strip().startswith("Hint:"):
                skip_rest = True
                continue
            if not skip_rest:
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines).strip()
    
    def _extract_function_signature(self, code: str) -> Optional[str]:
        """Extract function signature (def line) from code.
        
        Args:
            code: Full function implementation
            
        Returns:
            Function signature or None if not found
        """
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Get the line with the function definition
                    lines = code.split('\n')
                    # Find the def line
                    for i, line in enumerate(lines):
                        if line.strip().startswith('def ') and node.name in line:
                            # Handle multi-line signatures
                            signature_lines = [line]
                            j = i + 1
                            # Continue if line doesn't end with ):
                            while j < len(lines) and not signature_lines[-1].rstrip().endswith(':'):
                                signature_lines.append(lines[j])
                                j += 1
                            return '\n'.join(signature_lines).strip()
            return None
        except Exception as e:
            self.logger.debug(f"Failed to extract signature: {e}")
            return None
    
    def _remove_docstring_and_extract_body(self, code: str) -> Optional[str]:
        """Remove docstring and extract function body.
        
        Args:
            code: Full function implementation
            
        Returns:
            Function body without docstring, or None if parsing fails
        """
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Get function body
                    lines = code.split('\n')
                    
                    # Find where the function body starts (after def line and docstring)
                    func_start_line = node.lineno - 1  # 0-indexed
                    
                    # Skip the def line(s)
                    body_start = func_start_line + 1
                    while body_start < len(lines) and not lines[body_start].strip():
                        body_start += 1
                    
                    # Check if first statement is a docstring
                    if (node.body and 
                        isinstance(node.body[0], ast.Expr) and 
                        isinstance(node.body[0].value, ast.Constant) and
                        isinstance(node.body[0].value.value, str)):
                        # Skip docstring
                        docstring_end_line = node.body[0].end_lineno  # 1-indexed
                        body_start = docstring_end_line  # Now 0-indexed due to array indexing
                    
                    # Extract body lines
                    body_lines = []
                    for i in range(body_start, len(lines)):
                        line = lines[i]
                        # Stop at next function or class definition at same level
                        if line and not line[0].isspace() and line.strip():
                            break
                        body_lines.append(line)
                    
                    # Remove leading empty lines and normalize indentation
                    while body_lines and not body_lines[0].strip():
                        body_lines.pop(0)
                    
                    if not body_lines:
                        return None
                    
                    # Get base indentation (from first non-empty line)
                    base_indent = len(body_lines[0]) - len(body_lines[0].lstrip())
                    
                    # Remove base indentation from all lines
                    normalized_lines = []
                    for line in body_lines:
                        if line.strip():  # Non-empty line
                            if len(line) >= base_indent:
                                normalized_lines.append(line[base_indent:])
                            else:
                                normalized_lines.append(line)
                        else:  # Empty line
                            normalized_lines.append('')
                    
                    return '\n'.join(normalized_lines).rstrip()
            
            return None
        except Exception as e:
            self.logger.debug(f"Failed to extract body: {e}")
            return None
    
    def _check_quality(self, ratings: Dict[str, int]) -> bool:
        """Check if ratings meet quality thresholds.
        
        Args:
            ratings: Rating scores dictionary
            
        Returns:
            True if quality requirements are met
        """
        if not self.min_ratings:
            return True
        
        if self.require_all:
            # All specified dimensions must meet threshold
            for dimension, min_score in self.min_ratings.items():
                if ratings.get(dimension, 0) < min_score:
                    return False
            return True
        else:
            # At least one dimension must meet threshold
            for dimension, min_score in self.min_ratings.items():
                if ratings.get(dimension, 0) >= min_score:
                    return True
            return False
    
    def convert_record(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert a single record to ChatML format.
        
        Args:
            record: Input record with ratings
            
        Returns:
            ChatML formatted record or None if conversion fails
        """
        # Check quality first
        ratings = record.get("ratings", {})
        if not self._check_quality(ratings):
            self.logger.debug(f"Record {record.get('uid')} filtered by quality: {ratings}")
            return None
        
        # Extract fields
        uid = record.get("uid")
        problem_text = record.get("problem_text", "")
        code = record.get("code", "")
        
        # Remove hint from problem
        problem_no_hint = self._remove_hint(problem_text)
        
        # Extract function signature
        signature = self._extract_function_signature(code)
        if not signature:
            self.logger.debug(f"Failed to extract signature for {uid}")
            return None
        
        # Extract function body without docstring
        body = self._remove_docstring_and_extract_body(code)
        if not body:
            self.logger.debug(f"Failed to extract body for {uid}")
            return None
        
        # Construct ChatML format
        user_content = f"{problem_no_hint}\n\n{signature}"
        assistant_content = body
        
        chatml_record = {
            "uid": uid,
            "messages": [
                {
                    "role": "user",
                    "content": user_content
                },
                {
                    "role": "assistant",
                    "content": assistant_content
                }
            ]
        }
        
        # Add optional fields based on configuration
        if "ratings" in self.output_fields:
            chatml_record["ratings"] = ratings
        
        # Filter to only include specified fields
        filtered_record = {
            field: chatml_record[field]
            for field in self.output_fields
            if field in chatml_record
        }
        
        return filtered_record
    
    def convert_file(
        self,
        input_path: Path,
        output_path: Path
    ) -> Dict[str, int]:
        """Convert entire JSONL file to ChatML format using multiprocessing.
        
        Args:
            input_path: Input JSONL file path
            output_path: Output JSONL file path
            
        Returns:
            Statistics dictionary
        """
        self.logger.info(f"Converting {input_path} to ChatML format")
        self.logger.info(f"Output: {output_path}")
        self.logger.info(f"Using {self.num_workers} worker processes")
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Read all input lines
        self.logger.info("Reading input file...")
        with open(input_path, 'r', encoding='utf-8') as f:
            input_lines = [line.strip() for line in f if line.strip()]
        
        total_records = len(input_lines)
        self.logger.info(f"Loaded {total_records} records")
        
        # Prepare config dict for workers
        config_dict = {
            "min_ratings": self.min_ratings,
            "require_all": self.require_all,
            "output_fields": self.output_fields
        }
        
        # Prepare args for multiprocessing
        worker_args = [(line, config_dict) for line in input_lines]
        
        # Process in parallel
        stats = {
            "total": total_records,
            "converted": 0,
            "filtered_quality": 0,
            "failed_parse": 0
        }
        
        self.logger.info("Starting parallel conversion...")
        
        with open(output_path, 'w', encoding='utf-8') as outfile:
            with mp.Pool(processes=self.num_workers) as pool:
                # Process in chunks with progress updates
                chunk_results = []
                for i, result in enumerate(pool.imap(_process_record_worker, worker_args, chunksize=self.chunk_size)):
                    success, status, data = result
                    
                    if success:
                        outfile.write(data + '\n')
                        stats["converted"] += 1
                    elif status == "quality":
                        stats["filtered_quality"] += 1
                    else:
                        stats["failed_parse"] += 1
                    
                    # Progress logging
                    if (i + 1) % 1000 == 0:
                        self.logger.info(
                            f"Processed {i + 1}/{total_records} records: "
                            f"{stats['converted']} converted, "
                            f"{stats['filtered_quality']} filtered, "
                            f"{stats['failed_parse']} failed"
                        )
        
        # Final statistics
        self.logger.info(f"\n=== Conversion Complete ===")
        self.logger.info(f"Total records: {stats['total']}")
        self.logger.info(f"Converted: {stats['converted']}")
        self.logger.info(f"Filtered by quality: {stats['filtered_quality']}")
        self.logger.info(f"Parse failures: {stats['failed_parse']}")
        if stats['total'] > 0:
            self.logger.info(f"Success rate: {stats['converted']/stats['total']*100:.1f}%")
        
        return stats
    
    @classmethod
    def from_config_path(
        cls,
        config_path: Path,
        logger: Optional[Any] = None
    ) -> "ChatMLConverter":
        """Create converter from configuration file.
        
        Args:
            config_path: Path to configuration YAML
            logger: Optional logger instance
            
        Returns:
            Initialized converter
        """
        # Load main config
        config = ConfigManager.from_file(config_path)
        
        return cls(config=config, logger=logger)

