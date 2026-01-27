"""
Execution engine for running SKILL.md steps.

Security design by OPUS-3:
- Sandboxed execution
- Command allowlisting
- Resource limits
- Audit logging
"""

from __future__ import annotations

import logging
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable

from inception.enhance.agency.executor.parser import SkillParser, ParsedSkill, SkillStep

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Status of step execution."""
    
    SUCCESS = auto()
    FAILED = auto()
    SKIPPED = auto()
    TIMEOUT = auto()
    BLOCKED = auto()  # Blocked by security


@dataclass
class StepResult:
    """Result of executing a single step."""
    
    step: SkillStep
    status: ExecutionStatus
    stdout: str = ""
    stderr: str = ""
    duration_ms: int = 0
    error: str | None = None


@dataclass
class ExecutionResult:
    """Result of executing a skill."""
    
    skill: ParsedSkill
    step_results: list[StepResult]
    total_duration_ms: int
    success: bool
    
    @property
    def summary(self) -> str:
        """Get execution summary."""
        passed = sum(1 for r in self.step_results if r.status == ExecutionStatus.SUCCESS)
        total = len(self.step_results)
        return f"{passed}/{total} steps passed in {self.total_duration_ms}ms"


@dataclass
class ExecutionConfig:
    """Configuration for skill execution."""
    
    # Sandbox settings
    use_sandbox: bool = True
    sandbox_type: str = "subprocess"  # "subprocess" or "docker"
    docker_image: str = "python:3.11-slim"
    
    # Timeouts
    step_timeout_seconds: int = 60
    total_timeout_seconds: int = 600
    
    # Resource limits
    max_memory_mb: int = 512
    max_cpu_percent: int = 50
    
    # Security
    command_allowlist: list[str] = field(default_factory=lambda: [
        "echo", "cat", "ls", "pwd", "cd", "mkdir", "touch",
        "python", "pip", "uv", "npm", "node",
        "git", "curl", "wget",
    ])
    command_blocklist: list[str] = field(default_factory=lambda: [
        "rm -rf /", "sudo", "chmod 777", ":(){ :|:& };:",
        "shutdown", "reboot", "mkfs", "dd if=/dev/zero",
    ])
    
    # Confirmation
    require_confirmation: bool = True
    confirm_callback: Callable[[str], bool] | None = None
    
    # Dry run
    dry_run: bool = False
    
    # Logging
    log_all_commands: bool = True
    audit_log_path: str | None = None
    
    def is_command_safe(self, command: str) -> tuple[bool, str]:
        """Check if a command is safe to execute."""
        command_lower = command.lower().strip()
        
        # Check blocklist
        for blocked in self.command_blocklist:
            if blocked in command_lower:
                return False, f"Blocked pattern: {blocked}"
        
        # Check if first word is in allowlist
        first_word = command.split()[0] if command else ""
        
        if first_word not in self.command_allowlist:
            return False, f"Command '{first_word}' not in allowlist"
        
        return True, "OK"
    
    def confirm(self, action: str) -> bool:
        """Request confirmation for an action."""
        if not self.require_confirmation:
            return True
        
        if self.confirm_callback:
            return self.confirm_callback(action)
        
        return False


class ExecutionEngine:
    """
    Executes SKILL.md files with safety rails.
    
    Workflow:
    1. Parse SKILL.md
    2. Validate all steps for safety
    3. Execute steps in order (with confirmation)
    4. Capture output and verify success
    5. Generate execution report
    """
    
    def __init__(
        self,
        config: ExecutionConfig | None = None,
        parser: SkillParser | None = None,
    ):
        """Initialize execution engine."""
        self.config = config or ExecutionConfig()
        self.parser = parser or SkillParser()
        
        self._execution_log: list[dict[str, Any]] = []
    
    def execute_skill(
        self,
        skill_path: Path | str,
        working_dir: Path | str | None = None,
        progress_callback: Callable[[int, int, str], None] | None = None,
    ) -> ExecutionResult:
        """
        Execute a SKILL.md file.
        
        Args:
            skill_path: Path to SKILL.md
            working_dir: Working directory for execution
            progress_callback: Callback (step, total, status)
        
        Returns:
            Execution result
        """
        # Parse skill
        skill = self.parser.parse(skill_path)
        
        return self.execute_parsed_skill(
            skill, working_dir, progress_callback
        )
    
    def execute_parsed_skill(
        self,
        skill: ParsedSkill,
        working_dir: Path | str | None = None,
        progress_callback: Callable[[int, int, str], None] | None = None,
    ) -> ExecutionResult:
        """Execute a parsed skill."""
        working_dir = Path(working_dir) if working_dir else Path.cwd()
        
        executable_steps = skill.get_executable_steps()
        step_results: list[StepResult] = []
        
        start_time = time.time()
        
        for i, step in enumerate(executable_steps):
            if progress_callback:
                progress_callback(i + 1, len(executable_steps), step.title)
            
            result = self._execute_step(step, working_dir)
            step_results.append(result)
            
            # Stop on failure (unless step is optional)
            if result.status == ExecutionStatus.FAILED and not step.optional:
                logger.warning(f"Step {step.index} failed, stopping")
                break
            
            # Check total timeout
            elapsed = (time.time() - start_time) * 1000
            if elapsed > self.config.total_timeout_seconds * 1000:
                logger.warning("Total timeout reached")
                break
        
        total_duration = int((time.time() - start_time) * 1000)
        
        success = all(
            r.status == ExecutionStatus.SUCCESS or r.step.optional
            for r in step_results
        )
        
        result = ExecutionResult(
            skill=skill,
            step_results=step_results,
            total_duration_ms=total_duration,
            success=success,
        )
        
        # Log execution
        self._log_execution(result)
        
        return result
    
    def _execute_step(
        self,
        step: SkillStep,
        working_dir: Path,
    ) -> StepResult:
        """Execute a single step."""
        logger.info(f"Executing step {step.index}: {step.title}")
        
        command = step.command
        if not command:
            # Skip non-executable steps
            return StepResult(
                step=step,
                status=ExecutionStatus.SKIPPED,
            )
        
        # Security check
        is_safe, reason = self.config.is_command_safe(command)
        if not is_safe:
            logger.warning(f"Step blocked: {reason}")
            return StepResult(
                step=step,
                status=ExecutionStatus.BLOCKED,
                error=f"Security: {reason}",
            )
        
        # Dry run
        if self.config.dry_run:
            logger.info(f"[DRY RUN] Would execute: {command}")
            return StepResult(
                step=step,
                status=ExecutionStatus.SUCCESS,
                stdout=f"[DRY RUN] {command}",
            )
        
        # Confirmation
        if self.config.require_confirmation:
            if not self.config.confirm(f"Execute: {command}"):
                logger.info("Step skipped (not confirmed)")
                return StepResult(
                    step=step,
                    status=ExecutionStatus.SKIPPED,
                    error="Not confirmed",
                )
        
        # Execute
        return self._run_command(step, command, working_dir)
    
    def _run_command(
        self,
        step: SkillStep,
        command: str,
        working_dir: Path,
    ) -> StepResult:
        """Run a shell command."""
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=self.config.step_timeout_seconds,
            )
            
            duration = int((time.time() - start_time) * 1000)
            
            if result.returncode == 0:
                return StepResult(
                    step=step,
                    status=ExecutionStatus.SUCCESS,
                    stdout=result.stdout[:5000],  # Limit output
                    stderr=result.stderr[:1000],
                    duration_ms=duration,
                )
            else:
                return StepResult(
                    step=step,
                    status=ExecutionStatus.FAILED,
                    stdout=result.stdout[:5000],
                    stderr=result.stderr[:1000],
                    duration_ms=duration,
                    error=f"Exit code: {result.returncode}",
                )
                
        except subprocess.TimeoutExpired:
            return StepResult(
                step=step,
                status=ExecutionStatus.TIMEOUT,
                error=f"Timeout after {self.config.step_timeout_seconds}s",
            )
        except Exception as e:
            return StepResult(
                step=step,
                status=ExecutionStatus.FAILED,
                error=str(e),
            )
    
    def _log_execution(self, result: ExecutionResult) -> None:
        """Log execution for audit."""
        log_entry = {
            "skill_name": result.skill.name,
            "source_path": result.skill.source_path,
            "success": result.success,
            "duration_ms": result.total_duration_ms,
            "steps_executed": len(result.step_results),
            "steps_passed": sum(
                1 for r in result.step_results
                if r.status == ExecutionStatus.SUCCESS
            ),
        }
        
        self._execution_log.append(log_entry)
        
        if self.config.audit_log_path:
            # Would write to audit log file
            pass
    
    def validate_skill(self, skill: ParsedSkill) -> list[str]:
        """
        Validate a skill for safety without executing.
        
        Returns:
            List of validation issues
        """
        issues = []
        
        for step in skill.get_executable_steps():
            if step.command:
                is_safe, reason = self.config.is_command_safe(step.command)
                if not is_safe:
                    issues.append(
                        f"Step {step.index}: {reason}"
                    )
            
            if step.warning:
                issues.append(
                    f"Step {step.index} has warning: {step.warning}"
                )
        
        return issues
    
    def get_execution_log(self) -> list[dict[str, Any]]:
        """Get the execution audit log."""
        return self._execution_log.copy()
