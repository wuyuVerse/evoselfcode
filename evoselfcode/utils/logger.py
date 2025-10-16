"""
Unified logging system with structured output to files and console.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler


class LoggerManager:
    """
    Centralized logger management.
    Creates loggers with file and console handlers.
    """
    
    _loggers = {}
    _base_log_dir = Path("logs")
    
    @classmethod
    def setup_base_dir(cls, base_dir: Path):
        """Set base log directory"""
        cls._base_log_dir = base_dir
        cls._base_log_dir.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_logger(
        cls,
        name: str,
        module: Optional[str] = None,
        task: Optional[str] = None,
        level: int = logging.INFO,
    ) -> logging.Logger:
        """
        Get or create a logger with file and console handlers.
        
        Args:
            name: Logger name
            module: Module name (e.g., 'datagen', 'training', 'eval')
            task: Task name (e.g., 'fim', 'l2r', 'd2c')
            level: Logging level
        
        Returns:
            Configured logger
        
        Examples:
            logger = LoggerManager.get_logger('generation', module='datagen', task='fim')
            # Logs to: logs/datagen/fim/YYYYMMDD_HHMMSS.log
        """
        cache_key = f"{module}.{task}.{name}" if module and task else name
        
        if cache_key in cls._loggers:
            return cls._loggers[cache_key]
        
        # Create logger
        logger = logging.getLogger(cache_key)
        logger.setLevel(level)
        logger.propagate = False  # Don't propagate to root
        
        # Remove existing handlers
        logger.handlers.clear()
        
        # Console handler with Rich
        console = Console(stderr=True)
        console_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=False,
            markup=True,
            rich_tracebacks=True,
        )
        console_handler.setLevel(level)
        console_formatter = logging.Formatter("%(message)s")
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler
        if module:
            log_dir = cls._base_log_dir / module
            if task:
                log_dir = log_dir / task
            log_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"{timestamp}.log"
            
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(level)
            file_formatter = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
            logger.info(f"Logging to: {log_file}")
        
        cls._loggers[cache_key] = logger
        return logger
    
    @classmethod
    def close_all(cls):
        """Close all loggers and handlers"""
        for logger in cls._loggers.values():
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
        cls._loggers.clear()


def setup_task_logger(
    module: str,
    task: str,
    level: int = logging.INFO,
    log_dir: Optional[Path] = None,
) -> logging.Logger:
    """
    Convenience function to set up a task logger.
    
    Args:
        module: Module name (e.g., 'datagen', 'training')
        task: Task name (e.g., 'fim', 'l2r')
        level: Logging level
        log_dir: Custom log directory
    
    Returns:
        Configured logger
    
    Example:
        logger = setup_task_logger('datagen', 'fim')
        logger.info("Starting FIM generation...")
    """
    if log_dir:
        LoggerManager.setup_base_dir(log_dir)
    
    return LoggerManager.get_logger(
        name=f"{module}.{task}",
        module=module,
        task=task,
        level=level,
    )

