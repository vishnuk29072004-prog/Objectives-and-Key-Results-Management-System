
from typing import Dict, List, Optional, TypedDict, Any
from pydantic import BaseModel, Field

# ============================================================================
# Pydantic Models for Structured Output
# ============================================================================

class RequiredInput(BaseModel):
    input_name: str = Field(description="Name of the required input")
    description: str = Field(description="Description of what this input should contain")
    importance: str = Field(description="High/Medium/Low importance level")

class Task(BaseModel):
    task_name: str = Field(description="Name of the task")
    description: str = Field(description="Detailed description of the task")
    priority: str = Field(description="High/Medium/Low priority")
    estimated_duration: str = Field(description="Estimated time to complete")

class Subtask(BaseModel):
    subtask_name: str = Field(description="Name of the subtask")
    description: str = Field(description="Detailed description of the subtask")
    deliverable: str = Field(description="What should be delivered upon completion")
    complexity: str = Field(description="Simple/Medium/Complex complexity level")

class TaskBreakdown(BaseModel):
    tasks: List[Task] = Field(description="List of main tasks")
    subtasks: Dict[str, List[Subtask]] = Field(description="Subtasks for each task")

class WeightAssignment(BaseModel):
    task_weights: Dict[str, float] = Field(description="Weight for each task (0.5-3.0)")
    subtask_weights: Dict[str, float] = Field(description="Weight for each subtask (0.5-3.0)")

class ProgressAnalysis(BaseModel):
    current_status: str = Field(description="Current progress status")
    bottlenecks: List[str] = Field(description="Identified bottlenecks")
    recommendations: List[str] = Field(description="Actionable recommendations")
    risk_factors: List[str] = Field(description="Potential risks")

class AIRecommendation(BaseModel):
    focus_areas: List[str] = Field(description="Areas to focus on next")
    actions: List[str] = Field(description="Specific actions to take")
    timeline: str = Field(description="Suggested timeline")
    priority: str = Field(description="High/Medium/Low priority")

# ============================================================================
# State Management
# ============================================================================

class AgentState(TypedDict, total=False):
    objective: str
    deadline: str
    category: Optional[str]
    owner: Optional[str]
    inputs: Dict[str, str]
    task_breakdown: Optional[Dict]
    weight_assignment: Optional[Dict]
    progress_analysis: Optional[Dict]
    ai_recommendation: Optional[Dict]
    objective_id: Optional[int]
    current_task_id: Optional[int]
    current_subtask_id: Optional[int]
    messages: List[Any]
    error: Optional[str]
    llm_subtask_count_issue: bool
    generated_schedule: Optional[List[Dict[str, Any]]]
    is_initial_creation: Optional[bool]
    baseline_schedule: Optional[List[Dict[str, Any]]]  
    adjusted_schedule: Optional[List[Dict[str, Any]]] 
    schedule_drift: Optional[float] 
    needs_replanning: Optional[bool] 

# ============================================================================
# Reminder Workflow State (LangGraph modular reminder flow)
# ============================================================================

class ReminderState(TypedDict, total=False):
    """State for the LangGraph-based reminder email workflow"""
    reminder: Dict[str, Any]
    email_subject: str
    email_body: str
    used_fallback: bool
    send_success: bool
    error: Optional[str]