"""
Flow Schema Definition for AgentFlow Integration.

This module defines the core data structures for the AgentFlow engine,
mapping the Planner-Executor-Verifier-Generator pattern to Pydantic models.
"""

from typing import Literal, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class FlowRole(str, Enum):
    """The role of a step in the AgentFlow pattern."""
    PLANNER = "planner"
    EXECUTOR = "executor"
    VERIFIER = "verifier"
    GENERATOR = "generator"

class FlowStepSpec(BaseModel):
    """Static definition of a step in a flow."""
    name: str = Field(description="Unique name of this step")
    role: FlowRole = Field(description="The AgentFlow role")
    tool: Optional[str] = Field(default=None, description="Tool to invoke (if executor)")
    description: str = Field(description="Purpose of this step")
    next_steps: list[str] = Field(default_factory=list, description="Possible next steps")
    # GRPO Optimization Targets
    optimizable: bool = Field(default=False, description="Can this step's prompt be optimized?")

class FlowSpec(BaseModel):
    """Definition of an entire Flow."""
    id: str = Field(description="Unique flow ID (e.g., 'ingest_v2')")
    version: str = Field(default="0.1.0")
    steps: list[FlowStepSpec]
    entry_point: str = Field(description="Name of the first step")

class StepResult(BaseModel):
    """Result of a single executed step."""
    step_name: str
    role: FlowRole
    output: Any
    confidence: float = 1.0
    duration_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

class FlowTrajectory(BaseModel):
    """A complete run of a flow, used for GRPO training."""
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    flow_id: str
    steps: list[StepResult] = Field(default_factory=list)
    final_reward: Optional[float] = Field(default=None, description="0.0 to 1.0")
    status: Literal["running", "completed", "failed"] = "running"
    
    def add_step(self, result: StepResult):
        self.steps.append(result)

class FlowState(BaseModel):
    """Runtime state passed between steps."""
    context: dict[str, Any] = Field(default_factory=dict)
    history: list[StepResult] = Field(default_factory=list)
    current_step: str
    trajectory_id: str
