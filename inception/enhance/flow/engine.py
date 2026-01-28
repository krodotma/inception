"""
AgentFlow Execution Engine.

This module implements the runtime logic for executing flows defined by FlowSpec.
It handles state management, node execution, and GRPO trajectory recording.
"""

import asyncio
import logging
from typing import Any, Callable, Dict
from datetime import datetime

from inception.enhance.flow.schema import (
    FlowSpec, FlowState, FlowStepSpec, StepResult, 
    FlowTrajectory, FlowRole
)

logger = logging.getLogger(__name__)

class FlowRunner:
    """Executes a FlowSpec with optimization hooks."""
    
    def __init__(self, spec: FlowSpec, grpo_callback: Callable[[FlowTrajectory], None] | None = None):
        self.spec = spec
        self.steps_map = {s.name: s for s in spec.steps}
        self.grpo_callback = grpo_callback
        
    async def run(self, input_context: Dict[str, Any]) -> FlowTrajectory:
        """Execute the flow from entry point to completion."""
        trajectory = FlowTrajectory(flow_id=self.spec.id)
        
        # Initialize state
        state = FlowState(
            context=input_context,
            current_step=self.spec.entry_point,
            trajectory_id=trajectory.trace_id
        )
        
        logger.info(f"Starting Flow: {self.spec.id} (Trace: {trajectory.trace_id})")
        
        try:
            while state.current_step:
                step_spec = self.steps_map.get(state.current_step)
                if not step_spec:
                    logger.error(f"Step not found: {state.current_step}")
                    break
                
                # Execute Step
                start_time = datetime.utcnow()
                try:
                    output = await self._execute_step(step_spec, state)
                    success = True
                except Exception as e:
                    logger.error(f"Error in step {step_spec.name}: {e}")
                    output = str(e)
                    success = False
                
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                # Record Result
                result = StepResult(
                    step_name=step_spec.name,
                    role=step_spec.role,
                    output=output,
                    duration_ms=duration,
                    metadata={"success": success}
                )
                trajectory.add_step(result)
                state.history.append(result)
                
                # Update Context with Output (Simplified)
                # In a real system, we'd use JSONPath or similar to map outputs
                state.context[step_spec.name] = output
                
                # Determine Next Step
                if success and step_spec.next_steps:
                    # Simple linear logic for now; real logic would evaluate conditions
                    state.current_step = step_spec.next_steps[0]
                else:
                    state.current_step = None # End of flow
            
            trajectory.status = "completed"
            
        except Exception as e:
            logger.error(f"Flow execution failed: {e}")
            trajectory.status = "failed"
            
        # Trigger GRPO Hook if reward is available (usually calculated externally or by Verifier)
        if self.grpo_callback:
            self.grpo_callback(trajectory)
            
        return trajectory

    async def _execute_step(self, step: FlowStepSpec, state: FlowState) -> Any:
        """Execute a single step based on its role."""
        logger.debug(f"Executing {step.role}: {step.name}")
        
        if step.role == FlowRole.PLANNER:
            # TODO: Invoke LLM to plan/refine
            return {"plan": "execute_default"}
            
        elif step.role == FlowRole.EXECUTOR:
            # TODO: Invoke Tool
            if step.tool == "downloader":
                return f"Downloaded {state.context.get('uri')}"
            return "Executed"
            
        elif step.role == FlowRole.VERIFIER:
            # TODO: Check quality
            return {"valid": True, "score": 0.9}
            
        elif step.role == FlowRole.GENERATOR:
            # TODO: Synthesize final output
            return "Final Output"
            
        return None
