from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
from langgraph.graph.message import add_messages
from llm_config import safe_llm_call, gemini_llm, qwen_llm
from models import AgentState, ReminderState
from langgraph.graph import StateGraph, END
from typing import Dict, Any, List

# ============================================================================
# Agent Nodes
# ============================================================================

def objective_suggestion_agent(objective_text: str) -> str:
    """Generate an improved, actionable objective suggestion via LLM.

    Keeps wording aligned with existing endpoint behavior.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert at writing clear, actionable objectives and goals. 
        Given a user's input, suggest an improved, more specific, and actionable version.
        
        Guidelines:
        - Make it specific and measurable
        - Use action verbs
        - Keep it concise but clear
        - Ensure it's achievable within a reasonable timeframe
        - If the input is already good, suggest minor improvements only
        - Don't change the core intent of the user's objective"""),
        ("human", """Please suggest an improved version of this objective:
        
        Original: {objective}
        
        Provide only the improved objective text, no explanations."""),
    ])

    try:
        suggestion = safe_llm_call(
            prompt.format_messages(objective=objective_text),
            gemini_llm,
            max_retries=2,
            agent_name="objective_suggestion_agent",
        )
        if suggestion and suggestion.strip():
            return suggestion.strip()
    except Exception as _e:
        pass
    return objective_text


def required_inputs_agent(objective_text: str) -> list:
    """Suggest a short list of required inputs for an objective via LLM.

    Returns a list of up to 5 input names.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert at analyzing objectives and determining what additional information would be helpful to make them more complete and actionable.
        
        Given an objective, suggest 2-3 additional inputs that would be useful to collect. These could be:
        - Specific metrics or KPIs
        - Stakeholder information
        - Resource requirements
        - Timeline details
        - Success criteria
        - Dependencies
        - Budget information
        - Team members needed
        
        Return only a simple comma-separated list of input names, no explanations. Example: target_metric, stakeholder, budget"""),
        ("human", """Analyze this objective and suggest required inputs:
        
        Objective: {objective}
        
        Return only a comma-separated list of input names."""),
    ])

    try:
        response = safe_llm_call(
            prompt.format_messages(objective=objective_text),
            gemini_llm,
            max_retries=2,
            agent_name="required_inputs_agent",
        )
        if response and response.strip():
            response_text = response.strip()
            inputs = [name.strip() for name in response_text.split(',') if name.strip()]
            if inputs:
                return inputs[:5]
    except Exception as _e:
        pass
    return ["target_metric", "stakeholder", "timeline"]


def input_analysis_agent(state: AgentState) -> AgentState:
    """Agent that analyzes the objective and determines required inputs using LLM"""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert project planner. Analyze the given objective and determine what inputs are needed to create a comprehensive plan.
        
        Consider:
        - What information is needed to break down this objective?
        - What constraints or requirements should be identified?
        - What resources or context would be helpful?
        
        Return a structured list of required inputs with descriptions and importance levels."""),
        ("human", "Objective: {objective}\nDeadline: {deadline}\nCategory: {category}\nOwner: {owner}")
    ])
    
    try:
        
        print("[Agent] input_analysis_agent: Analyzing objective for required inputs...")
        llm_content = safe_llm_call(prompt.format_messages(
            objective=state["objective"],
            deadline=state["deadline"],
            category=state["category"] or "General",
            owner=state["owner"] or "User"
        ), gemini_llm, max_retries=2, agent_name="input_analysis_agent")
        
        if llm_content:
            
            input_dict = {
                "Requirements": "Detailed requirements and specifications",
                "Resources": "Available resources and constraints", 
                "Timeline": "Specific timeline and milestones",
                "LLM_Insights": llm_content[:200] + "..." if len(llm_content) > 200 else llm_content
            }
        else:
            raise Exception("LLM failed to generate input analysis")
        
        state["inputs"] = input_dict
        state["messages"] = add_messages(state["messages"], AIMessage(content=f"Input analysis completed: {llm_content[:100]}..."))
        
    except Exception as e:
        state["error"] = f"Input analysis failed: {str(e)}"
        raise Exception(f"Input analysis failed: {e}")
    
    return state


def _build_subject_for_reminder(reminder: Dict[str, Any]) -> str:
    from datetime import datetime
    if reminder.get('subtasks'):
        urgent_subtasks = [s for s in reminder['subtasks'] if s['deadline'] == datetime.now().strftime('%Y-%m-%d')]
        if urgent_subtasks:
            return f"🚨 URGENT: {len(urgent_subtasks)} Subtask(s) Due TODAY - {reminder['objective'][:50]}..."
        return f"⚠️ REMINDER: {len(reminder['subtasks'])} Subtask(s) Due Soon - {reminder['objective'][:50]}..."
    return f"Reminder: {reminder['objective'][:50]}... - Deadline Approaching"

def reminder_llm_agent(state: ReminderState) -> ReminderState:
    """Generate email content using LLM or fallback if rate-limited via upstream wrapper."""
    try:
        from remainder_agent import generate_llm_reminder 
        reminder = state["reminder"]
        body = generate_llm_reminder(reminder)
        state["email_body"] = body or ""
        state["email_subject"] = _build_subject_for_reminder(reminder)
    except Exception as e:
        state["email_body"] = ""
        state["error"] = f"LLM generation failed: {e}"
    return state

def reminder_fallback_handler(state: ReminderState) -> ReminderState:
    if not state.get("email_body"):
        from remainder_agent import generate_fallback_email
        state["email_body"] = generate_fallback_email(state["reminder"])
        state["used_fallback"] = True
    else:
        state["used_fallback"] = False
    return state

def reminder_email_dispatcher(state: ReminderState) -> ReminderState:
    from remainder_agent import send_email_reminder
    reminder = state["reminder"]
    subject = state.get("email_subject") or _build_subject_for_reminder(reminder)
    body = state.get("email_body", "")
    success = send_email_reminder(reminder, prebuilt_body=body, prebuilt_subject=subject)
    state["send_success"] = success
    if not success and not state.get("error"):
        state["error"] = "Email dispatch failed"
    return state

def reminder_logger(state: ReminderState) -> ReminderState:
    reminder = state["reminder"]
    status = "SUCCESS" if state.get("send_success") else "FAILURE"
    used_fallback = state.get("used_fallback")
    print(f"[ReminderLogger] {status} sending email for objective: {reminder['objective'][:60]}...")
    if used_fallback is not None:
        print(f"[ReminderLogger] used_fallback={used_fallback}")
    if state.get("error"):
        print(f"[ReminderLogger] error={state['error']}")
    return state

def create_reminder_graph():
    workflow = StateGraph(ReminderState)
    workflow.add_node("llm_agent", reminder_llm_agent)
    workflow.add_node("fallback_handler", reminder_fallback_handler)
    workflow.add_node("email_dispatcher", reminder_email_dispatcher)
    workflow.add_node("logger", reminder_logger)
    workflow.set_entry_point("llm_agent")

    def decide_after_llm(state: ReminderState) -> str:
        return "fallback_handler" if not state.get("email_body") else "email_dispatcher"

    workflow.add_conditional_edges("llm_agent", decide_after_llm)
    workflow.add_edge("fallback_handler", "email_dispatcher")
    workflow.add_edge("email_dispatcher", "logger")
    workflow.add_edge("logger", END)
    return workflow.compile()

def task_planning_agent(state: AgentState) -> AgentState:
    """Agent that creates detailed task and subtask breakdown using LLM, with fallback and input echo on error."""

    input_str = "\n".join([f"{k}: {v}" for k, v in state["inputs"].items() if k != "LLM_Insights"])

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert project manager. Create a focused task breakdown for the given objective.
        
        CRITICAL GUIDELINES:
        - Create EXACTLY 3-4 main tasks (no more, no less)
        - For each task, create EXACTLY 2-3 subtasks (no more, no less)
        - DO NOT create generic tasks like "Breakdown" or "Objective"
        - DO NOT include "Objective" as a subtask
        - Each task should be a specific, actionable phase of the project
        - Each subtask should be a concrete, measurable action
        - Tasks should be logically sequenced and realistic for the deadline
        - Make everything SPECIFIC to the objective, not generic templates
        - DO NOT include validation checklist items like "Deadline alignment" or "Specificity" as subtasks
        - DO NOT include "MANDATORY CHECKS" or similar validation sections in your output
        
        REQUIRED FORMAT - Follow this EXACTLY:
        
        # [Objective Name] Task Breakdown
        
        ## Task 1: [Specific Task Name]
        **Description:** [Brief description of what this task accomplishes]
        
        ### Subtasks:
        - **1.1** [Specific Subtask Name]
        - **1.2** [Specific Subtask Name]
        - **1.3** [Specific Subtask Name]
        
        ## Task 2: [Specific Task Name]
        **Description:** [Brief description of what this task accomplishes]
        
        ### Subtasks:
        - **2.1** [Specific Subtask Name]
        - **2.2** [Specific Subtask Name]
        - **2.3** [Specific Subtask Name]
        
        ## Task 3: [Specific Task Name]
        **Description:** [Brief description of what this task accomplishes]
        
        ### Subtasks:
        - **3.1** [Specific Subtask Name]
        - **3.2** [Specific Subtask Name]
        - **3.3** [Specific Subtask Name]
        
        ## Task 4: [Specific Task Name] (if needed)
        **Description:** [Brief description of what this task accomplishes]
        
        ### Subtasks:
        - **4.1** [Specific Subtask Name]
        - **4.2** [Specific Subtask Name]
        - **4.3** [Specific Subtask Name]
        
        MANDATORY REQUIREMENTS:
        1. You MUST create 3-4 tasks
        2. Each task MUST have 2-3 subtasks
        3. Use the exact format above with "## Task" and "### Subtasks:"
        4. Each subtask must start with "- **X.Y**" where X is task number and Y is subtask number
        5. Do not include any generic tasks like "Breakdown" or "Objective"
        6. Make all tasks and subtasks specific to the given objective
        7. **MANDATORY: If you do not follow the subtask count, your output will be rejected and the process will fail.**
        8. **STOP after the last task's subtasks - DO NOT include any validation checklist, mandatory checks, or summary sections**
        9. **DO NOT include "MANDATORY CHECKS" or similar validation sections in your output**
        """),
        ("human", """Objective: {objective}
        Deadline: {deadline}
        Inputs:
        {inputs}

        Create a detailed task breakdown following the format above. Make sure tasks and subtasks are specific to this objective, not generic templates.""")
    ])

    llm_content = None
    error_msg = None

    try:
        print("[Agent] task_planning_agent: Generating task and subtask breakdown (Qwen first, fallback to Gemini)...")
        # Try Qwen first
        try:
            llm_content = safe_llm_call(prompt.format_messages(
                objective=state["objective"],
                deadline=state["deadline"],
                inputs=input_str
            ), qwen_llm, max_retries=2, agent_name="task_planning_agent")
        except Exception as e_qwen:
            print(f"[Agent] Qwen LLM failed: {e_qwen}")
            error_msg = f"Qwen LLM failed: {e_qwen}"
            # Fallback to Gemini
            try:
                llm_content = safe_llm_call(prompt.format_messages(
                    objective=state["objective"],
                    deadline=state["deadline"],
                    inputs=input_str
                ), gemini_llm, max_retries=2, agent_name="task_planning_agent")
            except Exception as e_gemini:
                print(f"[Agent] Gemini LLM also failed: {e_gemini}")
                error_msg += f" | Gemini LLM failed: {e_gemini}"

        if not llm_content or len(llm_content.strip()) < 50:
            raise Exception(error_msg or "LLM response too short or empty")
        
        
        tasks = []
        subtasks = {}
        
        lines = llm_content.split('\n')
        current_task = None
        current_subtasks = []
        task_counter = 0
        
        
        unwanted_tasks = {'breakdown', 'objective', 'overview', 'introduction', 'summary'}
        unwanted_subtasks = {
            'objective', 'overview', 'introduction', 'summary', 'breakdown', 'description',
            'deadline alignment', 'specificity', 'mandatory checks', 'tasks', 'subtask counts',
            'deadline alignment:', 'specificity:', 'mandatory checks:', 'tasks:', 'subtask counts:',
            'mandatory requirements', 'mandatory requirements:', 'format', 'format:',
            'guidelines', 'guidelines:', 'requirements', 'requirements:'
        }
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            
            if (line.startswith('## Task') or 
                line.startswith('**Task') or 
                line.startswith('Task') or
                (line.startswith('##') and 'Task' in line) or
                (line.startswith('**') and 'Task' in line) or
                (line.startswith('#') and 'Task' in line) or
                line.startswith('## ')):  
                
                
                if current_task and current_subtasks:
                    
                    seen = set()
                    unique_subtasks = []
                    for s in current_subtasks:
                        key = s.get("subtask_name", "")
                        if key and key not in seen:
                            seen.add(key)
                            unique_subtasks.append(s)
                    subtasks[current_task] = unique_subtasks
                    current_subtasks = []
                
                
                task_name = line
                
                
                if task_name.startswith('## '):
                    task_name = task_name[3:]  # Remove "## "
                elif task_name.startswith('**'):
                    task_name = task_name.replace('**', '')
                
                
                if 'Task' in task_name:
                    task_parts = task_name.split('Task', 1)
                    if len(task_parts) > 1:
                        task_name = task_parts[1]
                        
                        if ':' in task_name:
                            task_name = task_name.split(':', 1)[1]
                        task_name = task_name.strip()
                
                
                if task_name and (task_name.startswith('1.') or task_name.startswith('2.') or task_name.startswith('3.') or task_name.startswith('4.') or task_name.startswith('5.')):
                    task_name = task_name.split('.', 1)[1].strip()
                
                
                task_name_lower = task_name.lower().strip()
                if (task_name and len(task_name) < 100 and len(task_name) > 3 and 
                    task_name_lower not in unwanted_tasks and
                    not any(unwanted in task_name_lower for unwanted in unwanted_tasks)):
                    
                    current_task = task_name
                    task_counter += 1
                    tasks.append({
                        "task_name": current_task,
                        "description": f"Complete {current_task}",
                        "priority": "High",
                        "estimated_duration": "2-3 weeks"
                    })
                    print(f"Found task {task_counter}: {current_task}")
                else:
                    print(f"Filtered out unwanted task: {task_name}")
                    current_task = None
            
            
            elif (line.startswith('- **') or 
                  line.startswith('• **') or 
                  line.startswith('* **') or
                  line.startswith('- ') or
                  line.startswith('• ') or
                  line.startswith('* ') or
                  line.startswith('**') or
                  (line.startswith('1.') or line.startswith('2.') or line.startswith('3.') or line.startswith('4.')) or
                  line.startswith('-')):  # Any line starting with - could be a subtask
                
                if current_task:
                    
                    if line.lower().strip() in ['subtasks:', 'subtask:', 'tasks:', 'task:']:
                        continue
                    
                    # Skip validation checklist sections
                    if any(checklist_item in line.lower() for checklist_item in [
                        'mandatory checks:', 'mandatory requirements:', 'format:', 'guidelines:',
                        'deadline alignment:', 'specificity:', 'tasks:', 'subtask counts:'
                    ]):
                        continue
                    
                    subtask_name = line.replace('-', '').replace('•', '').replace('*', '').replace('**', '').strip()
                    
                    # Preserve spaces and formatting while cleaning up
                    subtask_name = ' '.join(subtask_name.split())  # Normalize multiple spaces to single spaces
                    
                    if subtask_name.startswith('1.') or subtask_name.startswith('2.') or subtask_name.startswith('3.') or subtask_name.startswith('4.'):
                        subtask_name = subtask_name.split('.', 1)[1].strip()
                    
                    if ':' in subtask_name:
                        subtask_name = subtask_name.split(':', 1)[0].strip()
                    elif ' - ' in subtask_name:
                        subtask_name = subtask_name.split(' - ', 1)[0].strip()
                    
                    subtask_name_lower = subtask_name.lower().strip()
                    if (subtask_name and len(subtask_name) < 200 and len(subtask_name) > 2 and
                        subtask_name_lower not in unwanted_subtasks and
                        not subtask_name_lower.startswith('subtask') and
                        not subtask_name_lower.startswith('task') and
                        not subtask_name_lower.startswith('description') and
                        not subtask_name_lower.startswith('mandatory') and
                        not subtask_name_lower.startswith('format') and
                        not subtask_name_lower.startswith('guidelines') and
                        not subtask_name_lower.startswith('requirements') and
                        not subtask_name_lower.startswith('deadline alignment') and
                        not subtask_name_lower.startswith('specificity')):
                        
                        current_subtasks.append({
                            "subtask_name": subtask_name,
                            "description": f"Complete {subtask_name}",
                            "deliverable": f"{subtask_name} completed",
                            "complexity": "Medium"
                        })
                        print(f"  Found subtask: {subtask_name}")
                    else:
                        print(f"  Filtered out unwanted subtask: {subtask_name}")
        
        
        if current_task and current_subtasks:
            
            seen = set()
            unique_subtasks = []
            for s in current_subtasks:
                key = s.get("subtask_name", "")
                if key and key not in seen:
                    seen.add(key)
                    unique_subtasks.append(s)
            subtasks[current_task] = unique_subtasks
        
        
        subtask_counts = [len(subtasks.get(t['task_name'], [])) for t in tasks]
        subtask_issue = any((c < 2 or c > 3) for c in subtask_counts)
        if subtask_issue:
            print(f"❌ Some tasks have unexpected number of subtasks: {subtask_counts}")
            state['llm_subtask_count_issue'] = True
        else:
            state['llm_subtask_count_issue'] = False
        
        if tasks:
            total_subtasks = sum(len(subs) for subs in subtasks.values())
            print(f"Successfully extracted {len(tasks)} tasks and {total_subtasks} subtasks from LLM response")
            
            for i, task in enumerate(tasks, 1):
                print(f"Task {i}: {task['task_name']}")
                task_subs = subtasks.get(task['task_name'], [])
                for j, subtask in enumerate(task_subs, 1):
                    print(f"  Subtask {i}.{j}: {subtask['subtask_name']}")
            
            state["task_breakdown"] = {
                "tasks": tasks,
                "subtasks": subtasks,
                "LLM_Insights": llm_content[:300] + "..." if len(llm_content) > 300 else llm_content
            }
            state["messages"] = add_messages(state["messages"], AIMessage(content=f"Task planning completed: {len(tasks)} tasks and {total_subtasks} subtasks generated"))
        else:
            raise Exception("Failed to extract any tasks from LLM response")
        
    except Exception as e:
        # Log the input and error for debugging
        print(f"[Agent] task_planning_agent ERROR: {e}")
        print(f"Input was: {state['objective']}, deadline: {state['deadline']}, inputs: {input_str}")
        import traceback
        traceback.print_exc()
        # Echo the input and error in the state for API/UI
        state['error'] = f"Task planning failed: {e}"
        state['llm_input'] = {
            "objective": state.get("objective"),
            "deadline": state.get("deadline"),
            "inputs": input_str
        }
        return state

    return state

def weight_assignment_agent(state: AgentState) -> AgentState:
    """Agent that assigns importance weights to tasks and subtasks using LLM"""
    
    if not state["task_breakdown"]:
        state["error"] = "No task breakdown available for weight assignment"
        raise Exception("No task breakdown available for weight assignment")
    
    try:
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert project manager. Assign importance weights to tasks and subtasks based on their complexity, dependencies, and impact on project success.
            
            Guidelines:
            - Weights should be between 0.5 and 3.0
            - Higher weights for more complex or critical tasks
            - Consider dependencies and impact on overall project
            - Ensure weights are realistic and balanced"""),
            ("human", """Task Breakdown:
            {task_breakdown}
            
            Assign appropriate weights to each task and subtask.""")
        ])
        
        print("[Agent] weight_assignment_agent: Assigning weights to tasks and subtasks...")
        llm_content = safe_llm_call(prompt.format_messages(
            task_breakdown=str(state["task_breakdown"])
        ), gemini_llm, max_retries=2, agent_name="weight_assignment_agent")
        
        if llm_content:
           
            task_weights = {}
            subtask_weights = {}
            
            
            for i, task in enumerate(state["task_breakdown"]["tasks"]):
                task_name = task["task_name"]
                
                base_weight = 2.0 - (i * 0.3)  
                task_weights[task_name] = max(0.8, base_weight)
                
                
                task_subtasks = state["task_breakdown"]["subtasks"].get(task_name, [])
                for j, subtask in enumerate(task_subtasks):
                    subtask_name = subtask["subtask_name"]
                    
                    subtask_weight = 1.5 - (j * 0.2)  
                    subtask_weights[subtask_name] = max(0.5, subtask_weight)
            
            weight_assignment = {
                "task_weights": task_weights,
                "subtask_weights": subtask_weights,
                "LLM_Insights": llm_content[:200] + "..." if len(llm_content) > 200 else llm_content
            }
        else:
            raise Exception("LLM failed to generate weight assignment")
        
        state["weight_assignment"] = weight_assignment
        state["messages"] = add_messages(state["messages"], AIMessage(content="Weight assignment completed"))
        
    except Exception as e:
        state["error"] = f"Weight assignment failed: {str(e)}"
        raise Exception(f"Weight assignment failed: {e}")
    
    return state

def llm_scheduling_agent(state: AgentState) -> AgentState:
    """Agent that generates realistic baseline schedule using DeadlineCalculator (no LLM required)"""
    
    if not state["task_breakdown"] or not state["weight_assignment"]:
        state["error"] = "Missing task breakdown or weight assignment for realistic scheduling"
        raise Exception("Missing task breakdown or weight assignment for realistic scheduling")

    try:
        from deadline_calculator import DeadlineCalculator
        from datetime import datetime, timedelta
        
        print("[Agent] llm_scheduling_agent: Generating realistic schedule using DeadlineCalculator...")
        
        # Create deadline calculator instance
        calculator = DeadlineCalculator()
        
        # Generate realistic deadlines based on task complexity and dependencies
        objective_deadline = datetime.strptime(state["deadline"], '%Y-%m-%d').date()
        current_date = datetime.now().date()
        
        # Ensure we start on a business day
        if not calculator.is_business_day(current_date):
            current_date = calculator.next_business_day(current_date)
        
        # Calculate task deadlines with business day awareness
        task_schedules = []
        subtask_schedules = []
        current_start_date = current_date
        
        for task in state["task_breakdown"]["tasks"]:
            task_name = task["task_name"]
            task_weight = state["weight_assignment"]["task_weights"].get(task_name, 1.0)
            
            # Calculate complexity and duration
            complexity = calculator.calculate_task_complexity(task_name)
            duration_business_days = calculator.estimate_duration(complexity, 'task')
            
            # Calculate end date using business days
            end_date = calculator.add_business_days(current_start_date, duration_business_days - 1)
            
            # Ensure deadline doesn't exceed objective deadline
            if end_date > objective_deadline:
                end_date = objective_deadline
                # Recalculate start date to fit within objective deadline
                required_business_days = duration_business_days
                temp_end = end_date
                temp_start = temp_end
                for _ in range(required_business_days - 1):
                    temp_start = temp_start - timedelta(days=1)
                    while not calculator.is_business_day(temp_start):
                        temp_start = temp_start - timedelta(days=1)
                current_start_date = temp_start
                end_date = calculator.add_business_days(current_start_date, duration_business_days - 1)
            
            task_schedule = {
                "task_name": task_name,
                "start_date": current_start_date.strftime('%Y-%m-%d'),
                "deadline": end_date.strftime('%Y-%m-%d'),
                "complexity": complexity,
                "duration": duration_business_days,
                "weight": task_weight
            }
            task_schedules.append(task_schedule)
            
            # Calculate subtask deadlines within this task with strict boundary enforcement
            subtasks = state["task_breakdown"]["subtasks"].get(task_name, [])
            if subtasks:
                task_start = current_start_date
                task_end = end_date
                
                if len(subtasks) == 1:
                    # Single subtask gets full task duration
                    subtask_schedules.append({
                        "subtask_name": subtasks[0]["subtask_name"],
                        "task_name": task_name,
                        "start_date": task_start.strftime('%Y-%m-%d'),
                        "deadline": task_end.strftime('%Y-%m-%d'),
                        "complexity": calculator.calculate_subtask_complexity(subtasks[0]["subtask_name"]),
                        "duration": calculator.business_days_between(task_start, task_end) + 1,
                        "weight": state["weight_assignment"]["subtask_weights"].get(subtasks[0]["subtask_name"], 1.0)
                    })
                else:
                    # Multiple subtasks - distribute time proportionally with strict boundary enforcement
                    # Calculate total complexity for proportional distribution
                    total_complexity = sum(calculator.calculate_subtask_complexity(st["subtask_name"]) for st in subtasks)
                    
                    # Calculate available business days for subtasks
                    available_business_days = calculator.business_days_between(task_start, task_end) + 1
                    
                    # Reserve some buffer time between subtasks (1 business day)
                    buffer_days = len(subtasks) - 1
                    working_days = max(1, available_business_days - buffer_days)
                    
                    current_subtask_start = task_start
                    remaining_working_days = working_days
                    
                    for i, subtask in enumerate(subtasks):
                        subtask_name = subtask["subtask_name"]
                        subtask_weight = state["weight_assignment"]["subtask_weights"].get(subtask_name, 1.0)
                        
                        # Calculate proportional duration based on complexity
                        if i == len(subtasks) - 1:
                            # Last subtask gets remaining time
                            subtask_duration = remaining_working_days
                        else:
                            # Proportional duration based on complexity
                            complexity = calculator.calculate_subtask_complexity(subtask_name)
                            proportional_days = max(1, int(working_days * (complexity / total_complexity)))
                            subtask_duration = min(proportional_days, remaining_working_days)
                            remaining_working_days -= subtask_duration
                        
                        # Calculate subtask end date using business days
                        subtask_end = calculator.add_business_days(current_subtask_start, subtask_duration - 1)
                        
                        # CRITICAL: Ensure subtask doesn't exceed task boundary
                        if subtask_end > task_end:
                            subtask_end = task_end
                            # Recalculate duration to fit within task boundary
                            subtask_duration = calculator.business_days_between(current_subtask_start, subtask_end) + 1
                        
                        # CRITICAL: Ensure subtask doesn't start before task
                        if current_subtask_start < task_start:
                            current_subtask_start = task_start
                            # Recalculate duration to fit within task boundary
                            subtask_duration = calculator.business_days_between(current_subtask_start, subtask_end) + 1
                        
                        subtask_schedules.append({
                            "subtask_name": subtask_name,
                            "task_name": task_name,
                            "start_date": current_subtask_start.strftime('%Y-%m-%d'),
                            "deadline": subtask_end.strftime('%Y-%m-%d'),
                            "complexity": calculator.calculate_subtask_complexity(subtask_name),
                            "duration": subtask_duration,
                            "weight": subtask_weight
                        })
                        
                        # Move to next subtask start (next business day after this subtask ends)
                        current_subtask_start = calculator.next_business_day(subtask_end)
            
            # Move to next task start (next business day after this task ends)
            current_start_date = calculator.next_business_day(end_date)
        
        # Create the final schedule structure
        generated_schedule = {
            "generation_method": "realistic_calculator",
            "tasks": task_schedules,
            "subtasks": subtask_schedules
        }
        
        state["generated_schedule"] = generated_schedule
        state["adjusted_schedule"] = generated_schedule
        state["schedule_drift"] = 0.0  # No baseline to compare against
        state["needs_replanning"] = False
        
        state["messages"] = add_messages(state["messages"], AIMessage(content="Realistic schedule generated using DeadlineCalculator with business day awareness and strict boundary enforcement"))
        
        print(f"[Agent] llm_scheduling_agent: Generated schedule with {len(task_schedules)} tasks and {len(subtask_schedules)} subtasks")
        
    except Exception as e:
        state["error"] = f"Realistic scheduling failed: {str(e)}"
        raise Exception(f"Realistic scheduling failed: {e}")
    
    return state

def _validate_schedule_alignment(task_schedules: List[Dict], subtask_schedules: List[Dict]) -> None:
    """
    Validate that all subtask deadlines are within their parent task boundaries
    """
    from datetime import datetime
    
    task_boundaries = {task['task_name']: {
        'start': datetime.strptime(task['start_date'], '%Y-%m-%d').date(),
        'end': datetime.strptime(task['deadline'], '%Y-%m-%d').date()
    } for task in task_schedules}
    
    validation_errors = []
    
    for subtask in subtask_schedules:
        task_name = subtask['task_name']
        if task_name not in task_boundaries:
            validation_errors.append(f"Subtask {subtask['subtask_name']} references non-existent task {task_name}")
            continue
        
        task_start = task_boundaries[task_name]['start']
        task_end = task_boundaries[task_name]['end']
        subtask_start = datetime.strptime(subtask['start_date'], '%Y-%m-%d').date()
        subtask_end = datetime.strptime(subtask['deadline'], '%Y-%m-%d').date()
        
        # Check boundaries
        if subtask_start < task_start:
            validation_errors.append(f"Subtask {subtask['subtask_name']} starts before task {task_name}")
        if subtask_end > task_end:
            validation_errors.append(f"Subtask {subtask['subtask_name']} ends after task {task_name}")
        if subtask_start > subtask_end:
            validation_errors.append(f"Subtask {subtask['subtask_name']} has invalid start/end dates")
    
    if validation_errors:
        error_msg = "Schedule validation failed:\n" + "\n".join(validation_errors)
        print(f"⚠️ {error_msg}")
        raise ValueError(error_msg)
    else:
        print("✅ All schedule alignments validated successfully")


def schedule_generation_agent(state: AgentState) -> AgentState:
    """Agent that generates task and subtask deadlines using advanced weighted scheduling.

    This agent now serves as a fallback when LLM scheduling fails or for mathematical adjustments.
    """
    if not state["task_breakdown"] or not state["weight_assignment"]:
        state["error"] = "Missing task breakdown or weight assignment for scheduling"
        raise Exception("Missing task breakdown or weight assignment for scheduling")

    try:
        from utils import auto_generate_deadlines_advanced, calculate_schedule_drift, should_replan_schedule
        
        # Check if we already have a baseline schedule from LLM
        if state.get("baseline_schedule") and state.get("adjusted_schedule"):
            print("[Agent] schedule_generation_agent: Using existing LLM-generated schedule")
            
            # Calculate drift
            drift = calculate_schedule_drift(state["baseline_schedule"], state["adjusted_schedule"])
            state["schedule_drift"] = drift
            
            # Check if replanning is needed
            needs_replan = should_replan_schedule(state["baseline_schedule"], state["adjusted_schedule"])
            state["needs_replanning"] = needs_replan
            
            if needs_replan:
                print(f"[Agent] schedule_generation_agent: Schedule drift detected ({drift:.2%}), replanning recommended")
                state["messages"] = add_messages(state["messages"], AIMessage(content=f"Schedule drift detected ({drift:.2%}), replanning recommended"))
            else:
                print(f"[Agent] schedule_generation_agent: Schedule drift acceptable ({drift:.2%})")
                state["messages"] = add_messages(state["messages"], AIMessage(content=f"Schedule drift acceptable ({drift:.2%})"))
            
            return state
        
        # Fallback: generate mathematical schedule
        print("[Agent] schedule_generation_agent: Generating mathematical fallback schedule")
        
        tasks_payload = []
        for task in state["task_breakdown"]["tasks"]:
            task_name = task["task_name"]
            t_weight = float(state["weight_assignment"]["task_weights"].get(task_name, 1.0) or 1.0)
            subtasks_defs = state["task_breakdown"]["subtasks"].get(task_name, [])
            sub_items = []
            for s in subtasks_defs:
                s_name = s["subtask_name"]
                s_weight = float(state["weight_assignment"]["subtask_weights"].get(s_name, 1.0) or 1.0)
                sub_items.append({"subtask_name": s_name, "weight": s_weight})
            tasks_payload.append({
                "task_name": task_name,
                "weight": t_weight,
                "subtasks": sub_items,
            })

        schedule = auto_generate_deadlines_advanced(
            state["deadline"],
            tasks_payload,
            base_task_units=5.0,
            base_subtask_units=1.0,
            project_buffer_ratio=0.1,
            enforce_business_days=True,
        )

        state["generated_schedule"] = schedule
        state["adjusted_schedule"] = schedule  # For consistency
        state["schedule_drift"] = 0.0  # No baseline to compare against
        state["needs_replanning"] = False
        
        state["messages"] = add_messages(state["messages"], AIMessage(content="Mathematical fallback schedule generated"))
        
    except Exception as e:
        state["error"] = f"Schedule generation failed: {str(e)}"
        raise Exception(f"Schedule generation failed: {e}")

    return state

def database_creation_agent(state: AgentState) -> AgentState:
    """Agent that creates the objective, tasks, and subtasks in the database"""
    
    if not state["task_breakdown"]:
        state["error"] = "Missing task breakdown"
        raise Exception("Missing task breakdown")
    # Fallback: if schedule missing/empty, generate it now to avoid hard failure
    if not state.get("generated_schedule"):
        try:
            from utils import auto_generate_deadlines_advanced
            if not state.get("weight_assignment"):
                state["error"] = "Missing weight assignment for scheduling"
                raise Exception("Missing weight assignment for scheduling")
            tasks_payload = []
            for task in state["task_breakdown"]["tasks"]:
                task_name = task["task_name"]
                t_weight = float(state["weight_assignment"]["task_weights"].get(task_name, 1.0) or 1.0)
                subtasks_defs = state["task_breakdown"]["subtasks"].get(task_name, [])
                sub_items = []
                for s in subtasks_defs:
                    s_name = s["subtask_name"]
                    s_weight = float(state["weight_assignment"]["subtask_weights"].get(s_name, 1.0) or 1.0)
                    sub_items.append({"subtask_name": s_name, "weight": s_weight})
                tasks_payload.append({
                    "task_name": task_name,
                    "weight": t_weight,
                    "subtasks": sub_items,
                })
            state["generated_schedule"] = auto_generate_deadlines_advanced(
                state["deadline"],
                tasks_payload,
                base_task_units=5.0,
                base_subtask_units=1.0,
                project_buffer_ratio=0.1,
                enforce_business_days=True,
            )
        except Exception as e:
            state["error"] = f"Failed to generate schedule in database_creation_agent: {e}"
            raise Exception(state["error"])
    
    try:
        from database_tools import create_objective_tool, create_task_tool, create_subtask_tool
        
        # Debug logging
        print(f"[Agent] database_creation_agent: Schedule type: {type(state['generated_schedule'])}")
        if isinstance(state['generated_schedule'], dict):
            print(f"[Agent] database_creation_agent: Schedule keys: {list(state['generated_schedule'].keys())}")
        elif isinstance(state['generated_schedule'], list):
            print(f"[Agent] database_creation_agent: Schedule length: {len(state['generated_schedule'])}")
        else:
            print(f"[Agent] database_creation_agent: Unknown schedule format: {state['generated_schedule']}")
        
        
        objective_id = create_objective_tool.invoke({
            "objective": state["objective"],
            "deadline": state["deadline"],
            "category": state["category"],
            "owner": state["owner"]
        })
        
        # Persist tasks and subtasks using the generated schedule
        # Handle both old format and new realistic schedule format
        if isinstance(state["generated_schedule"], dict) and state["generated_schedule"].get("generation_method") == "realistic_calculator":
            # New realistic schedule format
            task_schedules = {task["task_name"]: task for task in state["generated_schedule"]["tasks"]}
            subtask_schedules = {subtask["subtask_name"]: subtask for subtask in state["generated_schedule"]["subtasks"]}
            
            for task in state["task_breakdown"]["tasks"]:
                task_name = task["task_name"]
                task_sched = task_schedules.get(task_name, {})
                task_deadline_str = task_sched.get("deadline") or state["deadline"]
                task_weight = state["weight_assignment"]["task_weights"].get(task_name, 1.0)

                task_id = create_task_tool.invoke({
                    "objective_id": objective_id,
                    "task_name": task_name,
                    "deadline": task_deadline_str,
                    "weight": task_weight,
                })

                # Create subtasks with realistic deadlines
                for subtask in state["task_breakdown"]["subtasks"].get(task_name, []):
                    s_name = subtask["subtask_name"]
                    subtask_sched = subtask_schedules.get(s_name, {})
                    sub_deadline = subtask_sched.get("deadline") or task_deadline_str
                    subtask_weight = state["weight_assignment"]["subtask_weights"].get(s_name, 1.0)

                    create_subtask_tool.invoke({
                        "task_id": task_id,
                        "subtask_name": s_name,
                        "deadline": sub_deadline,
                        "weight": subtask_weight,
                    })
        elif isinstance(state["generated_schedule"], list):
            # Old schedule format (fallback)
            schedule_by_task = {item["task_name"]: item for item in state["generated_schedule"]}
            for task in state["task_breakdown"]["tasks"]:
                task_name = task["task_name"]
                sched = schedule_by_task.get(task_name, {})
                task_deadline_str = sched.get("task_deadline") or state["deadline"]
                task_weight = state["weight_assignment"]["task_weights"].get(task_name, 1.0)

                task_id = create_task_tool.invoke({
                    "objective_id": objective_id,
                    "task_name": task_name,
                    "deadline": task_deadline_str,
                    "weight": task_weight,
                })

                # Subtasks
                sub_sched = {s["subtask_name"]: s["deadline"] for s in sched.get("subtask_deadlines", [])}
                for subtask in state["task_breakdown"]["subtasks"].get(task_name, []):
                    s_name = subtask["subtask_name"]
                    sub_deadline = sub_sched.get(s_name, task_deadline_str)
                    subtask_weight = state["weight_assignment"]["subtask_weights"].get(s_name, 1.0)

                    create_subtask_tool.invoke({
                        "task_id": task_id,
                        "subtask_name": s_name,
                        "deadline": sub_deadline,
                        "weight": subtask_weight,
                    })
        else:
            # Fallback: use objective deadline for all tasks and subtasks
            for task in state["task_breakdown"]["tasks"]:
                task_name = task["task_name"]
                task_weight = state["weight_assignment"]["task_weights"].get(task_name, 1.0)

                task_id = create_task_tool.invoke({
                    "objective_id": objective_id,
                    "task_name": task_name,
                    "deadline": state["deadline"],
                    "weight": task_weight,
                })

                # Create subtasks with objective deadline
                for subtask in state["task_breakdown"]["subtasks"].get(task_name, []):
                    s_name = subtask["subtask_name"]
                    subtask_weight = state["weight_assignment"]["subtask_weights"].get(s_name, 1.0)

                    create_subtask_tool.invoke({
                        "task_id": task_id,
                        "subtask_name": s_name,
                        "deadline": state["deadline"],
                        "weight": subtask_weight,
                    })
        
        state["objective_id"] = objective_id
        state["is_initial_creation"] = True  # Flag to indicate this is initial creation
        state["messages"] = add_messages(state["messages"], AIMessage(content=f"Database entries created for objective {objective_id}"))
        
    except Exception as e:
        state["error"] = f"Database creation failed: {str(e)}"
        raise Exception(f"Database creation failed: {e}")
    
    return state

def progress_analysis_agent(state: AgentState) -> AgentState:
    """Agent that analyzes current progress and identifies issues using LLM"""
    
    if not state["objective_id"]:
        state["error"] = "No objective ID available for progress analysis"
        raise Exception("No objective ID available for progress analysis")
    
    try:
        from database_tools import get_objective_progress_tool
        from utils import adjust_schedule_for_progress, calculate_schedule_drift, should_replan_schedule
        import db
        
        print("[Agent] progress_analysis_agent: Analyzing progress and schedule drift...")
        
        # Get current progress
        progress = get_objective_progress_tool.invoke({"objective_id": state["objective_id"]})
        tasks = db.get_tasks(state["objective_id"])
        
        # Build current progress data
        current_progress = {
            "objective_progress": progress,
            "tasks": []
        }
        
        progress_details = []
        for task in tasks:
            task_id = task[0]
            task_name = task[2]
            subtasks = db.get_subtasks(task_id)
            completed_subtasks = sum(1 for st in subtasks if st[3])  # st[3] is completed flag
            total_subtasks = len(subtasks)
            
            task_progress = {
                "task_name": task_name,
                "completed_subtasks": completed_subtasks,
                "total_subtasks": total_subtasks,
                "progress_percentage": (completed_subtasks / total_subtasks * 100) if total_subtasks > 0 else 0
            }
            current_progress["tasks"].append(task_progress)
            
            progress_details.append(f"Task: {task_name} - {completed_subtasks}/{total_subtasks} subtasks completed ({task_progress['progress_percentage']:.1f}%)")
        
        progress_text = "\n".join(progress_details)
        
        # Analyze schedule drift if we have baseline schedule
        drift_analysis = ""
        if state.get("baseline_schedule"):
            # Adjust schedule based on current progress
            adjusted_schedule = adjust_schedule_for_progress(
                baseline_schedule=state["baseline_schedule"],
                current_progress=current_progress,
                objective_deadline=state["deadline"]
            )
            
            # Calculate drift
            drift = calculate_schedule_drift(state["baseline_schedule"], adjusted_schedule)
            needs_replan = should_replan_schedule(state["baseline_schedule"], adjusted_schedule)
            
            state["adjusted_schedule"] = adjusted_schedule
            state["schedule_drift"] = drift
            state["needs_replanning"] = needs_replan
            
            drift_analysis = f"""
Schedule Drift Analysis:
- Baseline Schedule: {len(state['baseline_schedule'])} tasks
- Current Drift: {drift:.2%}
- Replanning Needed: {'Yes' if needs_replan else 'No'}
- Threshold: 20%

Drift Details:
"""
            
            if drift > 0.2:
                drift_analysis += f"- ⚠️  Significant drift detected ({drift:.2%}) - replanning recommended\n"
            elif drift > 0.1:
                drift_analysis += f"- ⚡ Moderate drift detected ({drift:.2%}) - monitor closely\n"
            else:
                drift_analysis += f"- ✅ Minimal drift ({drift:.2%}) - schedule on track\n"
        
        # Generate progress analysis using LLM
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert project manager analyzing project progress. 
            Provide insights on current status, identify bottlenecks, and suggest improvements.
            
            Focus on:
            1. Overall progress assessment
            2. Identified bottlenecks or delays
            3. Risk factors
            4. Actionable recommendations
            5. Schedule implications"""),
            ("human", """Analyze this project progress:
            
            Objective: {objective}
            Current Progress: {progress}%
            Task Details:
            {progress_details}
            
            {drift_analysis}
            
            Provide a comprehensive analysis with specific recommendations.""")
        ])
        
        analysis_response = safe_llm_call(
            prompt.format_messages(
                objective=state["objective"],
                progress=progress,
                progress_details=progress_text,
                drift_analysis=drift_analysis
            ),
            gemini_llm,
            max_retries=2,
            agent_name="progress_analysis_agent"
        )
        
        # Extract bottlenecks and risk factors from LLM analysis
        bottlenecks = []
        risk_factors = []
        
        if analysis_response:
            lines = analysis_response.split('\n')
            for line in lines:
                line = line.strip().lower()
                if any(keyword in line for keyword in ['bottleneck', 'delay', 'blocker', 'issue']):
                    bottlenecks.append(line)
                elif any(keyword in line for keyword in ['risk', 'threat', 'challenge', 'concern']):
                    risk_factors.append(line)
        
        # Ensure we have at least some default values
        if not bottlenecks:
            bottlenecks = ["No specific bottlenecks identified yet"]
        if not risk_factors:
            risk_factors = ["No major risks identified at this stage"]
        
        state["progress_analysis"] = {
            "current_progress": progress,
            "task_details": progress_details,
            "drift_analysis": drift_analysis,
            "llm_analysis": analysis_response,
            "needs_replanning": state.get("needs_replanning", False),
            "schedule_drift": state.get("schedule_drift", 0.0),
            "bottlenecks": bottlenecks,
            "risk_factors": risk_factors
        }
        
        print(f"[Agent] progress_analysis_agent: Progress analysis completed - {progress}% complete, drift: {state.get('schedule_drift', 0.0):.2%}")
        state["messages"] = add_messages(state["messages"], AIMessage(content=f"Progress analysis completed: {progress}% complete, drift: {state.get('schedule_drift', 0.0):.2%}"))
        
    except Exception as e:
        state["error"] = f"Progress analysis failed: {str(e)}"
        raise Exception(f"Progress analysis failed: {e}")
    
    return state

def recommendation_agent(state: AgentState) -> AgentState:
    """Agent that provides AI recommendations based on current progress using LLM"""
    
    if not state["progress_analysis"]:
        state["error"] = "No progress analysis available for recommendations"
        raise Exception("No progress analysis available for recommendations")
    
    try:
        analysis = state["progress_analysis"]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert project advisor. Provide comprehensive, actionable recommendations.
            
            Your response should include:
            1. A clear summary of the current situation
            2. Specific, actionable recommendations (3-5 items)
            3. Priority levels for each recommendation
            4. Expected timeline for implementation
            5. Potential impact of each recommendation
            
            Format your response as follows:
            
            ## Current Situation Summary
            [Brief overview of the project status and key challenges]
            
            ## Key Recommendations
            
            ### 1. [High Priority] [Recommendation Title]
            **Action:** [Specific action to take]
            **Timeline:** [When to implement]
            **Impact:** [Expected outcome]
            
            ### 2. [Medium Priority] [Recommendation Title]
            **Action:** [Specific action to take]
            **Timeline:** [When to implement]
            **Impact:** [Expected outcome]
            
            ### 3. [Priority] [Recommendation Title]
            **Action:** [Specific action to take]
            **Timeline:** [When to implement]
            **Impact:** [Expected outcome]
            
            ## Next Steps
            [Immediate actions to take in the next 1-2 weeks]
            
            Be specific, actionable, and provide clear guidance for project success."""),
            ("human", """Objective: {objective}
            Current Status: {current_status}
            Bottlenecks: {bottlenecks}
            Risks: {risk_factors}
            
            Provide comprehensive recommendations to improve project progress and success.""")
        ])
        
        print("[Agent] recommendation_agent: Generating AI recommendations...")
       
        llm_content = safe_llm_call(prompt.format_messages(
            objective=state["objective"],
            current_status=analysis["current_progress"],
            bottlenecks=", ".join(analysis["bottlenecks"]),
            risk_factors=", ".join(analysis["risk_factors"])
        ), gemini_llm, max_retries=2, agent_name="recommendation_agent")
        
        if llm_content:
            
            lines = llm_content.split('\n')
            actions = []
            focus_areas = []
            
            
            for line in lines:
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                    actions.append(line[1:].strip())
                elif line.startswith('###') and 'Priority' in line:
                    # Extract recommendation titles
                    title = line.replace('###', '').strip()
                    if title:
                        focus_areas.append(title)
                elif line.startswith('**Action:**'):
                    action = line.replace('**Action:**', '').strip()
                    if action:
                        actions.append(action)
                elif line.startswith('**Impact:**'):
                    impact = line.replace('**Impact:**', '').strip()
                    if impact:
                        actions.append(f"Expected impact: {impact}")
                elif line and any(keyword in line.lower() for keyword in ['action', 'recommend', 'suggest', 'focus', 'implement']):
                    if line not in actions:
                        actions.append(line)
            
            
            if not actions:
                actions = ["Prioritize high-impact items", "Allocate additional resources", "Review project timeline"]
            if not focus_areas:
                focus_areas = ["Complete pending tasks", "Address bottlenecks", "Resource optimization"]
            
            recommendation = {
                "focus_areas": focus_areas[:5],  
                "actions": actions[:8],  
                "timeline": "2-3 weeks for completion",
                "priority": "High",
                "llm_recommendations": llm_content,
                "ai_recommendations": actions[:5], 
                "full_analysis": llm_content 
            }
        else:
            raise Exception("LLM failed to generate recommendations")
        
        state["ai_recommendation"] = recommendation
        state["messages"] = add_messages(state["messages"], AIMessage(content="AI recommendations generated"))
        
    except Exception as e:
        state["error"] = f"Recommendation generation failed: {str(e)}"
        raise Exception(f"Recommendation generation failed: {e}")
    
    return state