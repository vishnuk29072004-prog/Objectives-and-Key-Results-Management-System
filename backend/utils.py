#!/usr/bin/env python3
"""
Utility Functions
Helper functions for the agentic system
"""

from datetime import datetime, timedelta, date
from math import ceil
from typing import List, Dict, Any, Optional
import json
from llm_config import safe_llm_call, gemini_llm, qwen_llm
from langchain_core.prompts import ChatPromptTemplate


def _is_business_day(d: date) -> bool:
    return d.weekday() < 5  # Mon-Fri


def _roll_forward_to_business_day(d: date) -> date:
    while not _is_business_day(d):
        d = d + timedelta(days=1)
    return d


def _roll_backward_to_business_day(d: date) -> date:
    while not _is_business_day(d):
        d = d - timedelta(days=1)
    return d


def _business_day_shift(d: date, delta_days: int) -> date:
    """Shift a date by delta business days (skip weekends)."""
    if delta_days == 0:
        return d if _is_business_day(d) else _roll_forward_to_business_day(d)
    step = 1 if delta_days > 0 else -1
    remaining = abs(delta_days)
    cur = d
    while remaining > 0:
        cur = cur + timedelta(days=step)
        if _is_business_day(cur):
            remaining -= 1
    return cur


def _business_days_between(start: date, end: date) -> int:
    if end < start:
        return 0
    days = 0
    cur = start
    while cur <= end:
        if _is_business_day(cur):
            days += 1
        cur = cur + timedelta(days=1)
    return max(0, days)


def generate_llm_baseline_schedule(
    objective: str,
    deadline: str,
    tasks: List[Dict[str, Any]],
    weights: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Generate a realistic baseline schedule using LLM (Gemini-2.0-Flash).
    
    Args:
        objective: The main objective
        deadline: Final deadline (YYYY-MM-DD)
        tasks: List of tasks with subtasks
        weights: Task and subtask weights
    
    Returns:
        List of tasks with realistic durations, dependencies, and deadlines
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert project manager and scheduling specialist. 
        Create a realistic project schedule based on the given objective, tasks, and final deadline.
        
        Guidelines:
        - Estimate realistic durations for each task based on complexity and scope
        - Identify dependencies between tasks (which tasks must complete before others)
        - Consider resource constraints and team capacity
        - Include buffer time for unexpected issues
        - Ensure the schedule fits within the final deadline
        - Use business days only (Monday-Friday)
        - Subtasks within a task should have sequential deadlines (not all the same)
        - Each subtask should have a realistic duration based on its complexity
        - Subtask deadlines should progress sequentially within the task duration
        
        CRITICAL: You MUST return ONLY valid JSON. Do not include any explanatory text, markdown formatting, or code blocks.
        
        Return a JSON structure with:
        - task_name: Name of the task
        - duration_days: Estimated duration in business days
        - dependencies: List of task names this task depends on (empty if none)
        - complexity: High/Medium/Low
        - subtasks: List of subtasks with their durations and dependencies
        
        Example format:
        {{
            "tasks": [
                {{
                    "task_name": "Market Research",
                    "duration_days": 5,
                    "dependencies": [],
                    "complexity": "Medium",
                    "subtasks": [
                        {{
                            "subtask_name": "Competitor Analysis",
                            "duration_days": 3,
                            "dependencies": []
                        }},
                        {{
                            "subtask_name": "Customer Survey",
                            "duration_days": 2,
                            "dependencies": ["Competitor Analysis"]
                        }}
                    ]
                }}
            ]
        }}
        
        IMPORTANT: Ensure subtask durations add up to approximately the task duration, and subtasks have realistic sequential dependencies."""),
        ("human", """Create a realistic schedule for this project:
        
        Objective: {objective}
        Final Deadline: {deadline}
        Tasks: {tasks}
        Weights: {weights}
        
        Generate a JSON schedule that is realistic and achievable with proper sequential subtask deadlines.""")
    ])
    
    try:
        # Format tasks for LLM
        tasks_for_llm = []
        for task in tasks:
            task_name = task["task_name"]
            task_weight = weights["task_weights"].get(task_name, 1.0)
            subtasks = []
            for subtask in task.get("subtasks", []):
                subtask_name = subtask["subtask_name"]
                subtask_weight = weights["subtask_weights"].get(subtask_name, 1.0)
                subtasks.append({
                    "subtask_name": subtask_name,
                    "weight": subtask_weight
                })
            tasks_for_llm.append({
                "task_name": task_name,
                "weight": task_weight,
                "subtasks": subtasks
            })
        
        print(f"Formatted {len(tasks_for_llm)} tasks for LLM")
        
        # Call LLM for baseline schedule
        try:
            response = safe_llm_call(
                prompt.format_messages(
                    objective=objective,
                    deadline=deadline,
                    tasks=json.dumps(tasks_for_llm, indent=2),
                    weights=json.dumps(weights, indent=2)
                ),
                gemini_llm,  # Use Gemini for fast, structured output
                max_retries=2,
                agent_name="generate_llm_baseline_schedule"
            )
        except Exception as e:
            print(f"Error in safe_llm_call: {e}")
            raise e
        
        print(f"LLM Response Length: {len(response) if response else 0}")
        print(f"LLM Response Preview: {response[:500] if response else 'None'}...")
        
        # Check if response is too long and truncate if necessary
        if response and len(response) > 8000:
            print(f"Warning: LLM response is very long ({len(response)} chars), truncating for processing")
            response = response[:8000] + "..."
        
        if not response or len(response.strip()) < 10:
            print("LLM response too short or empty")
            return []
        
        # Parse JSON response
        try:
            # Clean the response to extract JSON
            response_clean = response.strip()
            
            # Try to find JSON in the response
            if response_clean.startswith('{'):
                # Response is already JSON
                schedule_data = json.loads(response_clean)
            elif '```json' in response_clean:
                # Extract JSON from code block
                start_idx = response_clean.find('```json') + 7
                end_idx = response_clean.find('```', start_idx)
                if end_idx == -1:
                    end_idx = response_clean.find('```', start_idx)
                json_str = response_clean[start_idx:end_idx].strip()
                schedule_data = json.loads(json_str)
            elif '{' in response_clean and '}' in response_clean:
                # Extract JSON from response
                start_idx = response_clean.find('{')
                end_idx = response_clean.rfind('}') + 1
                json_str = response_clean[start_idx:end_idx].strip()
                schedule_data = json.loads(json_str)
            else:
                print(f"Could not parse JSON from response: {response_clean[:200]}...")
                return []
            
            tasks = schedule_data.get("tasks", [])
            if tasks:
                print(f"Successfully parsed {len(tasks)} tasks from LLM response")
                return tasks
            else:
                print("No tasks found in LLM response")
                return []
                
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Response preview: {response[:500]}...")
            return []
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            return []
            
    except Exception as e:
        print(f"Error generating LLM baseline schedule: {e}")
        return []


def calculate_schedule_drift(baseline_schedule: List[Dict], adjusted_schedule: List[Dict]) -> float:
    """
    Calculate the percentage drift between baseline and adjusted schedules.
    
    Args:
        baseline_schedule: Original LLM-generated schedule
        adjusted_schedule: Current adjusted schedule
    
    Returns:
        Drift percentage (0.0 to 1.0)
    """
    if not baseline_schedule or not adjusted_schedule:
        return 0.0
    
    total_drift = 0.0
    total_baseline_duration = 0.0
    
    baseline_by_task = {task["task_name"]: task for task in baseline_schedule}
    
    for adjusted_task in adjusted_schedule:
        task_name = adjusted_task["task_name"]
        baseline_task = baseline_by_task.get(task_name)
        
        if baseline_task:
            baseline_duration = baseline_task.get("duration_days", 1)
            adjusted_deadline = datetime.strptime(adjusted_task["task_deadline"], "%Y-%m-%d").date()
            baseline_deadline = datetime.strptime(baseline_task.get("deadline", adjusted_task["task_deadline"]), "%Y-%m-%d").date()
            drift_days = abs((adjusted_deadline - baseline_deadline).days)
            drift_ratio = drift_days / max(baseline_duration, 1)
            total_drift += drift_ratio
            total_baseline_duration += baseline_duration
    
    if total_baseline_duration == 0:
        return 0.0
    
    return total_drift / len(adjusted_schedule) if adjusted_schedule else 0.0


def should_replan_schedule(baseline_schedule: List[Dict], adjusted_schedule: List[Dict], threshold: float = 0.2) -> bool:
    """
    Determine if the schedule needs replanning based on drift threshold.
    Args:
        baseline_schedule: Original LLM-generated schedule
        adjusted_schedule: Current adjusted schedule
        threshold: Drift threshold (default 20%)

    Returns:
        True if replanning is needed
    """
    drift = calculate_schedule_drift(baseline_schedule, adjusted_schedule)
    return drift > threshold


def adjust_schedule_for_progress(
    baseline_schedule: List[Dict],
    current_progress: Dict[str, Any],
    objective_deadline: str
) -> List[Dict[str, Any]]:
    """
    Adjust the baseline schedule based on current progress using local logic. 
    Args:
        baseline_schedule: Original LLM-generated schedule
        current_progress: Current progress data
        objective_deadline: Final deadline
 0
    Returns:
        Adjusted schedule
    """
    if not baseline_schedule:
        return []
    
    # Convert baseline to the format expected by auto_generate_deadlines_advanced
    tasks_payload = []
    for task in baseline_schedule:
        task_name = task["task_name"]
        duration = task.get("duration_days", 5)
        
        subtasks = []
        for subtask in task.get("subtasks", []):
            subtasks.append({
                "subtask_name": subtask["subtask_name"],
                "weight": subtask.get("duration_days", 1)
            })
        
        tasks_payload.append({
            "task_name": task_name,
            "weight": duration,
            "subtasks": subtasks
        })
    
    # Use existing utility for local adjustments
    return auto_generate_deadlines_advanced(
        objective_deadline,
        tasks_payload,
        base_task_units=1.0,  # Use 1:1 mapping with LLM durations
        base_subtask_units=1.0,
        project_buffer_ratio=0.1,
        enforce_business_days=True
    )


def replan_schedule_with_llm(
    objective: str,
    deadline: str,
    tasks: List[Dict[str, Any]],
    weights: Dict[str, Any],
    current_progress: Dict[str, Any],
    drift_analysis: str
) -> List[Dict[str, Any]]:
    """
    Replan the schedule using Qwen3-235B for complex reasoning when drift is significant.
    
    Args:
        objective: The main objective
        deadline: Final deadline
        tasks: List of tasks
        weights: Task weights
        current_progress: Current progress data
        drift_analysis: Analysis of why the schedule drifted
    
    Returns:
        New replanned schedule
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert project manager facing a significant schedule drift. 
        The current project schedule has deviated significantly from the original plan.
        
        Your task is to create a new realistic schedule that:
        1. Accounts for the current progress and delays
        2. Identifies the root causes of the drift
        3. Proposes realistic solutions and adjustments
        4. Maintains project quality while meeting the deadline
        5. Includes risk mitigation strategies
        
        Consider:
        - What caused the original schedule to fail?
        - How can we prevent similar issues?
        - What resources or approaches need to change?
        - Are there any scope adjustments needed?
        
        Return a comprehensive JSON schedule with detailed reasoning.""")
    ])
    
    try:
        response = safe_llm_call(
            prompt.format_messages(
                objective=objective,
                deadline=deadline,
                tasks=json.dumps(tasks, indent=2),
                weights=json.dumps(weights, indent=2),
                current_progress=json.dumps(current_progress, indent=2),
                drift_analysis=drift_analysis
            ),
            qwen_llm,  # Use Qwen3 for complex reasoning
            max_retries=2,
            agent_name="replan_schedule_with_llm"
        )
        
        try:
            schedule_data = json.loads(response)
            return schedule_data.get("tasks", [])
        except json.JSONDecodeError:
            print("LLM replanning failed, returning empty schedule")
            return []
            
    except Exception as e:
        print(f"Error in LLM replanning: {e}")
        return []


def auto_generate_deadlines_advanced(
    objective_deadline_str: str,
    tasks: List[Dict[str, Any]],
    *,
    base_task_units: float = 5.0,
    base_subtask_units: float = 1.0,
    project_buffer_ratio: float = 0.1,
    min_task_days: int = 1,
    min_subtask_days: int = 1,
    enforce_business_days: bool = True,
    now_dt: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """
    Compute a realistic schedule using weighted effort allocation and sequential subtask scheduling.

    Inputs:
      - objective_deadline_str: YYYY-MM-DD
      - tasks: [{
            "task_name": str,
            "weight": float,
            "subtasks": [{"subtask_name": str, "weight": float}, ...]
        }, ...]

    Returns list aligned with input order:
      [{
         "task_name": str,
         "task_deadline": YYYY-MM-DD,
         "subtask_deadlines": [{"subtask_name": str, "deadline": YYYY-MM-DD}, ...]
      }, ...]
    """
    deadline_obj = datetime.strptime(objective_deadline_str, "%Y-%m-%d").date()
    today = (now_dt or datetime.now()).date()

    if enforce_business_days:
        today = _roll_forward_to_business_day(today)

    # Compute available business days with project buffer
    total_bd = _business_days_between(today, deadline_obj)
    if total_bd <= 0:
        # Degenerate: everything due today
        return [
            {
                "task_name": t.get("task_name"),
                "task_deadline": deadline_obj.strftime("%Y-%m-%d"),
                "subtask_deadlines": [
                    {"subtask_name": s.get("subtask_name"), "deadline": deadline_obj.strftime("%Y-%m-%d")}
                    for s in t.get("subtasks", [])
                ],
            }
            for t in tasks
        ]

    project_buffer_days = max(1, int(total_bd * project_buffer_ratio))
    working_bd = max(1, total_bd - project_buffer_days)
    
    # Latest allowed date for schedule considering buffer
    if enforce_business_days:
        window_end = _business_day_shift(deadline_obj, -project_buffer_days)
        window_end = _roll_backward_to_business_day(window_end)
    else:
        window_end = deadline_obj - timedelta(days=project_buffer_days)

    # Compute total effort units
    total_units = 0.0
    for t in tasks:
        t_w = float(t.get("weight", 1.0) or 1.0)
        total_units += t_w * base_task_units
        for s in t.get("subtasks", []):
            s_w = float(s.get("weight", 1.0) or 1.0)
            total_units += s_w * base_subtask_units

    if total_units <= 0:
        total_units = len(tasks) * base_task_units or 1.0

    # Scale units to available working days
    s = working_bd / total_units

    # Build schedule sequentially
    cur_start = today
    schedule: List[Dict[str, Any]] = []

    for t in tasks:
        task_name = t.get("task_name")
        t_w = float(t.get("weight", 1.0) or 1.0)
        subtasks_list = t.get("subtasks", [])

        # Task duration from weight
        task_days = max(min_task_days, ceil(t_w * base_task_units * s))

        # Task start respecting business days
        if enforce_business_days:
            cur_start = _roll_forward_to_business_day(cur_start)
        
        task_start = cur_start
        task_end = cur_start  # Will be updated as subtasks are scheduled

        # Calculate subtask deadlines sequentially within the task duration
        sub_deadlines: List[Dict[str, Any]] = []
        
        if subtasks_list:
            # Calculate proportional durations for subtasks
            total_sub_w = sum(float(sv.get("weight", 1.0) or 1.0) for sv in subtasks_list) or 1.0
            sub_acc_days = 0
            current_sub_start = task_start

            for idx, sdef in enumerate(subtasks_list):
                s_w = float(sdef.get("weight", 1.0) or 1.0)
                proportional = (s_w / total_sub_w) * task_days
                s_days = max(min_subtask_days, ceil(proportional))
                sub_acc_days += s_days

                if idx == len(subtasks_list) - 1:
                    s_days = max(min_subtask_days, task_days - (sub_acc_days - s_days))
                    sub_acc_days = task_days
                sub_end = current_sub_start
                days_added = 0
                while days_added < s_days:
                    if not enforce_business_days or _is_business_day(sub_end):
                        days_added += 1
                    if days_added < s_days:
                        sub_end = sub_end + timedelta(days=1)
                if sub_end > window_end:
                    sub_end = window_end
                if enforce_business_days and not _is_business_day(sub_end):
                    sub_end = _roll_backward_to_business_day(sub_end)

                sub_deadlines.append({
                    "subtask_name": sdef.get("subtask_name"),
                    "deadline": sub_end.strftime("%Y-%m-%d"),
                })
                task_end = max(task_end, sub_end)
                current_sub_start = sub_end + timedelta(days=1)
                if enforce_business_days:
                    current_sub_start = _roll_forward_to_business_day(current_sub_start)
        else:
            task_end = task_start
            days_added = 0
            while days_added < task_days:
                if not enforce_business_days or _is_business_day(task_end):
                    days_added += 1
                if days_added < task_days:
                    task_end = task_end + timedelta(days=1)
            
            if task_end > window_end:
                task_end = window_end
            if enforce_business_days and not _is_business_day(task_end):
                task_end = _roll_backward_to_business_day(task_end)

        schedule.append({
            "task_name": task_name,
            "task_deadline": task_end.strftime("%Y-%m-%d"),
            "subtask_deadlines": sub_deadlines,
        })
        cur_start = task_end + timedelta(days=1)
        if enforce_business_days:
            cur_start = _roll_forward_to_business_day(cur_start)

    return schedule