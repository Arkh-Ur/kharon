"""
Structured logging module for Kharōn.

Provides logging utilities with consistent formatting and structured execution tracking.
"""

import logging
import time
from contextlib import contextmanager
from typing import Optional, Any


def get_task_logger(task_name: str) -> logging.Logger:
    """
    Creates a logger with namespace kharon.{task_name}.
    
    Args:
        task_name: Name of the task or component
        
    Returns:
        Logger instance configured with kharon namespace
    """
    logger = logging.getLogger(f"kharon.{task_name}")
    return logger


def log_execution(
    logger: logging.Logger,
    script_path: str,
    status: str,
    duration: float,
    exit_code: Optional[int] = None,
    error: Optional[str] = None,
    **kwargs
) -> None:
    """
    Logs structured execution information for a script run.
    
    Args:
        logger: Logger instance to use for logging
        script_path: Path to the script that was executed
        status: Execution status (success, failed, timeout, etc.)
        duration: Duration of execution in seconds
        exit_code: Exit code from script execution (if applicable)
        error: Error message if execution failed
        **kwargs: Additional execution metadata to include in log
    """
    log_data = {
        'script_path': script_path,
        'status': status,
        'duration_seconds': duration,
        'exit_code': exit_code,
        **kwargs
    }
    
    if error:
        log_data['error'] = error
        
    log_message = f"Script execution: {status} in {duration:.2f}s"
    if exit_code is not None:
        log_message += f" (exit_code={exit_code})"
    
    if status == 'success':
        logger.info(log_message, extra={'structured_data': log_data})
    elif status in ['failed', 'timeout']:
        logger.error(log_message, extra={'structured_data': log_data})
    else:
        logger.warning(log_message, extra={'structured_data': log_data})


class TaskLogContext:
    """
    Context manager that logs start/end of a task with timing.
    
    Automatically logs when the task starts and finishes, including duration.
    Can be used with any logger and includes optional success/failure tracking.
    """
    
    def __init__(self, logger: logging.Logger, task_name: str):
        """
        Initialize the task logging context.
        
        Args:
            logger: Logger instance to use for logging
            task_name: Name of the task being executed
        """
        self.logger = logger
        self.task_name = task_name
        self.start_time: Optional[float] = None
        self.success: Optional[bool] = None
        
    def __enter__(self) -> 'TaskLogContext':
        """
        Enter the context manager - logs task start time.
        
        Returns:
            Self for context manager usage
        """
        self.start_time = time.time()
        self.logger.info(f"Starting task: {self.task_name}")
        self.success = None
        return self
        
    def __exit__(self, exc_type: Optional[type], exc_val: Optional[Exception], exc_tb: Optional[Any]) -> None:
        """
        Exit the context manager - logs task completion with timing.
        
        Args:
            exc_type: Exception type if task failed
            exc_val: Exception value if task failed  
            exc_tb: Exception traceback if task failed
        """
        if self.start_time is None:
            return
            
        duration = time.time() - self.start_time
        self.success = exc_type is None
        
        if self.success:
            self.logger.info(f"Completed task: {self.task_name} in {duration:.2f}s")
        else:
            error_msg = str(exc_val) if exc_val else "Unknown error"
            self.logger.error(f"Failed task: {self.task_name} in {duration:.2f}s - {error_msg}")
            
        return


def configure_kharon_logging(level: str = "INFO") -> None:
    """
    Configure default logging format for all kharon loggers.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
    )
    
    # Configure root logger if not already configured
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
        root_logger.setLevel(getattr(logging, level.upper()))
    
    # Configure kharon namespace loggers
    kharon_logger = logging.getLogger('kharon')
    kharon_logger.setLevel(getattr(logging, level.upper()))