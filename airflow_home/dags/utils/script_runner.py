"""
ScriptRunner class for executing external scripts via subprocess.

Provides robust script execution with timeout handling, result parsing, and comprehensive error management.
"""

import dataclasses
import json
import logging
import os
import platform
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Union

logger = logging.getLogger("kharon.runner")


@dataclasses.dataclass
class ScriptExecutionResult:
    """
    Result of script execution containing all execution metadata.
    
    Attributes:
        success: Whether script executed successfully (exit code 0)
        exit_code: Exit code from script execution
        stdout: Complete stdout output
        stderr: Complete stderr output
        duration_seconds: Time taken for execution in seconds
        timed_out: Whether execution timed out
        parsed_result: Parsed JSON result from stdout if present
    """
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool
    parsed_result: Optional[Dict]


class ScriptRunner:
    """
    Robust script execution engine with timeout handling and result parsing.
    
    Supports both Python and bash scripts with automatic detection based on file extension.
    Handles timeouts gracefully and parses structured output from scripts.
    """
    
    def __init__(self, timeout: int = 3600, python: str = "python3"):
        """
        Initialize the script runner.
        
        Args:
            timeout: Maximum execution time in seconds (default: 3600)
            python: Python executable to use (default: "python3")
        """
        self.timeout = timeout
        self.python = python
        
    def run_script(
        self, 
        script_path: str, 
        args: List[str] = None, 
        env_vars: Dict[str, str] = None
    ) -> ScriptExecutionResult:
        """
        Execute a script with the given arguments and environment variables.
        
        Args:
            script_path: Path to the script to execute
            args: List of arguments to pass to the script
            env_vars: Environment variables to set for script execution
            
        Returns:
            ScriptExecutionResult containing execution metadata
            
        Raises:
            FileNotFoundError: If script_path doesn't exist
            PermissionError: If script is not executable
            subprocess.SubprocessError: For execution errors
        """
        script_path_obj = Path(os.path.expanduser(script_path))
        if not script_path_obj.exists():
            raise FileNotFoundError(f"Script not found: {script_path}")
            
        if not script_path_obj.is_file():
            raise ValueError(f"Path is not a file: {script_path}")
            
        executable = self._detect_python(script_path)
        command = [executable, str(script_path)]
        
        if args:
            command.extend(args)
            
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)
        start_time = time.time()
        stdout, stderr = "", ""
        timed_out = False
        exit_code = -1
        
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True
            )
            
            try:
                stdout, stderr = process.communicate(timeout=self.timeout)
                exit_code = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                try:
                    stdout, stderr = process.communicate()
                except Exception:
                    stdout, stderr = "", ""
                stdout = stdout or ""
                stderr = stderr or ""
                timed_out = True
                exit_code = -1
                
        except FileNotFoundError as e:
            logger.error(f"Executable not found: {executable}")
            raise
        except PermissionError as e:
            logger.error(f"Permission denied for script: {script_path}")
            raise
        except subprocess.SubprocessError as e:
            logger.error(f"Subprocess error executing {script_path}: {e}")
            raise
            
        duration = time.time() - start_time
        
        # Parse result from stdout
        parsed_result = self._parse_result(stdout)
        
        success = not timed_out and exit_code == 0
        
        result = ScriptExecutionResult(
            success=success,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_seconds=duration,
            timed_out=timed_out,
            parsed_result=parsed_result
        )
        
        status = "timeout" if timed_out else "success" if success else "failed"
        logger.info(f"Script execution: {status} ({duration:.2f}s, exit_code={exit_code})")
        
        return result
        
    def _detect_python(self, script_path: str) -> str:
        """
        Detect whether script needs python3 or bash based on file extension.
        
        Args:
            script_path: Path to the script file
            
        Returns:
            Command to use for script execution ("python3" or "bash")
        """
        path_obj = Path(script_path)

        if path_obj.suffix.lower() in ['.sh', '.bash']:
            # On Windows, look for bash (Git Bash, WSL, or Cygwin)
            if platform.system() == 'Windows':
                for candidate in ['bash', 'wsl', 'wsl.exe']:
                    if shutil.which(candidate):
                        return candidate
                raise FileNotFoundError(
                    f"No bash interpreter found for {script_path}. "
                    "Install Git for Windows, WSL2, or run Airflow inside Podman."
                )
            return 'bash'
        elif path_obj.suffix.lower() == '.ps1':
            return 'powershell'
        else:
            return self.python
            
    def _parse_result(self, stdout: str) -> Optional[Dict]:
        """
        Parse JSON results from stdout lines matching RESULT:{json} pattern.
        
        Args:
            stdout: Complete stdout output from script
            
        Returns:
            Parsed JSON result as dict, or None if no result found
        """
        lines = stdout.split('\n')
        result_lines = [line.strip() for line in lines if line.strip().startswith('RESULT:')]
        
        if not result_lines:
            return None
            
        try:
            result_json = result_lines[0][7:]
            return json.loads(result_json)
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse RESULT from stdout: {e}")
            return None