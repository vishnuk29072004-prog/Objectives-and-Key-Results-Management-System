from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import db
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta


try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ API Server: Loaded environment variables from .env file")
except ImportError:
    print("⚠️  API Server: python-dotenv not installed. Install with: pip install python-dotenv")
except Exception as e:
    print(f"⚠️  API Server: Could not load .env file: {e}")


from agentic_system_langgraph import langgraph_agentic_tracker


BASE_DIR = os.path.dirname(__file__)
GRAPHS_DIR = os.path.join(BASE_DIR, "graphs")
VENDOR_GRAPHVIZ_BIN = os.path.join(BASE_DIR, "vendor", "graphviz", "bin")

def ensure_graphviz_on_path():
    """Prepend a vendored Graphviz bin path to PATH if present (no admin needed)."""
    try:
        if os.path.isdir(VENDOR_GRAPHVIZ_BIN):
            current_path = os.environ.get("PATH", "")
            if VENDOR_GRAPHVIZ_BIN not in current_path:
                os.environ["PATH"] = VENDOR_GRAPHVIZ_BIN + os.pathsep + current_path
    except Exception:
        
        pass

app = FastAPI()

@asynccontextmanager
async def lifespan(app):
    db.init_db()
    
    # Start the reminder scheduler automatically
    try:
        from reminder_scheduler import start_reminder_scheduler
        print("🚀 Starting reminder scheduler...")
        start_reminder_scheduler()
        print("✅ Reminder scheduler started successfully")
    except Exception as e:
        print(f"⚠️ Failed to start reminder scheduler: {e}")
    
    yield
    
    # Stop the reminder scheduler when the app shuts down
    try:
        from reminder_scheduler import stop_reminder_scheduler
        print("🛑 Stopping reminder scheduler...")
        stop_reminder_scheduler()
        print("✅ Reminder scheduler stopped")
    except Exception as e:
        print(f"⚠️ Failed to stop reminder scheduler: {e}")

app = FastAPI(lifespan=lifespan)

@app.get("/api/health")
def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "message": "Server is running", "timestamp": str(datetime.now())}

@app.get("/api/test")
def test_endpoint():
    """Test endpoint for debugging"""
    return {"message": "Test endpoint working", "cors": "enabled"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)


try:
    os.makedirs(GRAPHS_DIR, exist_ok=True)
    app.mount("/graphs", StaticFiles(directory=GRAPHS_DIR), name="graphs")
except Exception as _e:
    
    pass

# ============================================================================
# Data Models
# ============================================================================

class ObjectiveCreate(BaseModel):
    objective: str
    deadline: str
    category: Optional[str] = None
    owner: Optional[str] = None

class ObjectiveSuggestion(BaseModel):
    objective: str

class RequiredInputs(BaseModel):
    objective: str

class SubtaskUpdate(BaseModel):
    result: str
    comment: Optional[str] = None

class ReviewAction(BaseModel):
    status: str

class EditAction(BaseModel):
    result: str

class AgenticObjectiveCreate(BaseModel):
    objective: str
    deadline: str
    category: Optional[str] = None
    owner: Optional[str] = None

# ============================================================================
# Endpoints
# ============================================================================

@app.get("/")
def root():
    return {"message": "Agentic OKR Goal Management API"}

@app.post("/api/objective-suggestion")
def get_objective_suggestion(data: ObjectiveSuggestion):
    """Get AI suggestion for objective text"""
    try:
        # Delegate to dedicated agent to keep concerns separated
        from agents import objective_suggestion_agent
        suggestion = objective_suggestion_agent(data.objective)
        return {"suggestion": suggestion}
            
    except Exception as e:
        print(f"Error generating objective suggestion: {e}")
        return {"suggestion": data.objective}  

@app.post("/api/required-inputs")
def get_required_inputs(data: RequiredInputs):
    """Get AI-suggested required inputs for an objective"""
    try:
        # Delegate to dedicated agent
        from agents import required_inputs_agent
        inputs = required_inputs_agent(data.objective)
        return {"inputs": inputs}
            
    except Exception as e:
        print(f"Error generating required inputs: {e}")
        return {"inputs": ["target_metric", "stakeholder", "timeline"]}

@app.post("/api/agentic/objectives")
def create_agentic_objective(data: AgenticObjectiveCreate):
    """Create a new objective using the LangGraph agentic AI system"""
    try:
        print(f"Creating agentic objective: {data.objective}")
        print(f"Deadline: {data.deadline}, Category: {data.category}, Owner: {data.owner}")
        
        result = langgraph_agentic_tracker.create_objective_with_agents(
            objective=data.objective,
            deadline=data.deadline,
            category=data.category,
            owner=data.owner
        )
        
        print(f"LangGraph result: {result}")
        
        if result["success"]:
            return {
                "id": result["objective_id"],
                "message": "Objective created successfully using LangGraph agentic AI",
                "task_breakdown": result["task_breakdown"],
                "progress_analysis": result["progress_analysis"],
                "ai_recommendation": result["ai_recommendation"],
                "agent_messages": result["agent_messages"]
            }
        else:
            error_msg = result.get("error", "Unknown error")
            print(f"LangGraph failed: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
            
    except Exception as e:
        print(f"Exception in create_agentic_objective: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"LangGraph agentic objective creation failed: {str(e)}")

@app.get("/api/agentic/objectives/{objective_id}/analysis")
def get_agentic_analysis(objective_id: int):
    """Get AI analysis and recommendations for an objective using LangGraph"""
    try:
        result = langgraph_agentic_tracker.analyze_progress(objective_id)
        
        if result["success"]:
            return {
                "objective_id": objective_id,
                "progress_analysis": result["progress_analysis"],
                "ai_recommendation": result["ai_recommendation"],
                "agent_messages": result["messages"]
            }
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LangGraph agentic analysis failed: {str(e)}")

@app.post("/api/agentic/subtasks/{subtask_id}/execute")
def execute_subtask_agentic(subtask_id: int):
    """Execute a subtask using the LangGraph agentic AI system"""
    try:
        result = langgraph_agentic_tracker.execute_subtask(subtask_id)
        
        if result["success"]:
            return {
                "subtask_id": subtask_id,
                "result": result["result"],
                "message": "Subtask executed successfully by LangGraph AI agent"
            }
        else:
            
            return {
                "subtask_id": subtask_id,
                "result": result.get("error", "Unknown error"),
                "message": "Subtask execution failed",
                "success": False
            }
            
    except Exception as e:
        
        return {
            "subtask_id": subtask_id,
            "result": f"LangGraph agentic execution failed: {str(e)}",
            "message": "Subtask execution failed",
            "success": False
        }

@app.get("/api/agentic/graph/ascii", response_class=PlainTextResponse)
def get_agentic_graph_ascii():
    """Return an ASCII visualization of the compiled graph (optional dependency)."""
    try:
        try:
            graph = langgraph_agentic_tracker.graph
            g = graph.get_graph()
        except Exception as e:
            
            from graph import create_agent_graph
            g = create_agent_graph().get_graph()  # type: ignore
        
        try:
            ascii_art = g.draw_ascii()  
        except Exception:
            ascii_art = str(g)
        return ascii_art
    except Exception as e:
        return PlainTextResponse(f"Graph visualization unavailable: {e}", status_code=500)

@app.get("/api/agentic/graph/png")
def get_agentic_graph_png():
    """Return a PNG visualization of the compiled graph (optional dependency)."""
    try:
        try:
            graph = langgraph_agentic_tracker.graph
            g = graph.get_graph()
        except Exception:
            from graph import create_agent_graph
            g = create_agent_graph().get_graph()  
        try:
            png_bytes = g.draw_mermaid_png()  
            return Response(content=png_bytes, media_type="image/png")
        except Exception as e:
           
            try:
                ensure_graphviz_on_path()
                png_bytes = g.draw_png()  
                return Response(content=png_bytes, media_type="image/png")
            except Exception as e2:
                raise HTTPException(status_code=501, detail=f"PNG rendering not available: {e2}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph visualization failed: {e}")

@app.get("/api/agentic/graph/png/save")
def save_agentic_graph_png(filename: str = "langgraph_workflow.png"):
    """Render graph to PNG and save to backend/graphs/<filename>."""
    try:
        try:
            graph = langgraph_agentic_tracker.graph
            g = graph.get_graph()
        except Exception:
            from graph import create_agent_graph
            g = create_agent_graph().get_graph()  
        try:
            png_bytes = g.draw_mermaid_png()  
        except Exception:
            # Fallback to graphviz path
            try:
                ensure_graphviz_on_path()
                png_bytes = g.draw_png()  
            except Exception as e2:
                raise HTTPException(status_code=501, detail=f"PNG rendering not available: {e2}")

        os.makedirs(GRAPHS_DIR, exist_ok=True)
        if not filename.lower().endswith(".png"):
            filename = f"{filename}.png"
        safe_name = filename.replace("/", "_").replace("\\", "_")
        file_path = os.path.join(GRAPHS_DIR, safe_name)
        with open(file_path, "wb") as f:
            f.write(png_bytes)
        public_url = f"/graphs/{safe_name}"
        return {"saved": True, "path": file_path.replace("\\", "/"), "url": public_url}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph save failed: {e}")

# ============================================================================
# Legacy Endpoints (for backward compatibility)
# ============================================================================

@app.post("/api/objectives")
def create_objective(data: ObjectiveCreate):
    """Legacy endpoint - redirects to LangGraph agentic system"""
    try:
        print(f"Creating objective: {data.objective}")
        print(f"Data received: {data.dict()}")
        
        # Validate required fields
        if not data.objective or not data.deadline:
            raise HTTPException(status_code=400, detail="Objective and deadline are required")
        
        result = create_agentic_objective(AgenticObjectiveCreate(**data.dict()))
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating objective: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create objective: {str(e)}")

@app.get("/api/objectives/{objective_id}/ai-recommendation")
def ai_objective_recommendation(objective_id: int):
    """Legacy endpoint - redirects to LangGraph agentic analysis"""
    try:
        result = langgraph_agentic_tracker.analyze_progress(objective_id)
        
        if result["success"] and result["ai_recommendation"]:
            ai_recommendation = result["ai_recommendation"]
            
            # First try to get the full LLM analysis
            full_analysis = ai_recommendation.get("full_analysis", "")
            if full_analysis:
                # Parse the full analysis to extract actionable items
                lines = full_analysis.split('\n')
                actions = []
                
                for line in lines:
                    line = line.strip()
                    if line and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                        actions.append(line[1:].strip())
                    elif line.startswith('**Action:'):
                        action = line.replace('**Action:**', '').strip()
                        if action:
                            actions.append(action)
                    elif line.startswith('###') and 'Priority' in line:
                        title = line.replace('###', '').strip()
                        if title:
                            actions.append(title)
                
                if actions:
                    return {"recommendation": actions[:5]}  # Return top 5 actions
            
            # Fallback to structured recommendations
            actions = ai_recommendation.get("actions", [])
            if actions:
                return {"recommendation": actions[:5]}
            
            # Final fallback to default recommendations
            default_recs = [
                "Review current progress and identify bottlenecks",
                "Prioritize high-impact tasks",
                "Allocate additional resources if needed",
                "Set up regular progress check-ins"
            ]
            return {"recommendation": default_recs}
        else:
            default_recs = [
                "Review current progress and identify bottlenecks",
                "Prioritize high-impact tasks",
                "Allocate additional resources if needed",
                "Set up regular progress check-ins"
            ]
            return {"recommendation": default_recs}
    except Exception as e:
        print(f"Error in ai_recommendation: {e}")
        return {"recommendation": [
            "Unable to generate recommendations at this time",
            "Please check your objective progress manually"
        ]}

@app.get("/api/objectives/{objective_id}/ai-summary")
def ai_objective_summary(objective_id: int):
    """Legacy endpoint - redirects to LangGraph agentic analysis"""
    try:
        result = langgraph_agentic_tracker.analyze_progress(objective_id)
        
        if result["success"] and result["progress_analysis"]:
            progress_analysis = result["progress_analysis"]
            
            # Extract the LLM analysis content
            llm_analysis = progress_analysis.get("llm_analysis", "")
            if llm_analysis:
                # Return the actual LLM-generated analysis
                return {"summary": llm_analysis}
            
            # Fallback to task details if no LLM analysis
            task_details = progress_analysis.get("task_details", [])
            current_progress = progress_analysis.get("current_progress", 0)
            
            if task_details:
                summary = f"Current Progress: {current_progress}%\n\nTask Status:\n" + "\n".join(task_details)
                return {"summary": summary}
            
            # Final fallback
            return {"summary": f"Progress analysis completed. Current progress: {current_progress}%"}
        else:
            return {"summary": "Progress analysis not available. Please check your objective details manually."}
    except Exception as e:
        print(f"Error in ai_summary: {e}")
        return {"summary": "Unable to generate summary at this time. Please check your objective progress manually."}

@app.post("/api/subtasks/{subtask_id}/ai-generate")
def ai_generate_subtask(subtask_id: int):
    """Generate AI result for a subtask"""
    try:
        print(f"Starting AI generation for subtask {subtask_id}")
        
        # Check if subtask exists first
        subtask = db.get_subtask_by_id(subtask_id)
        if not subtask:
            print(f"Subtask {subtask_id} not found")
            return {"result": f"Subtask {subtask_id} not found in database. Please check the subtask ID."}
        
        subtask_text = subtask[2] if len(subtask) > 2 else "Unknown subtask"
        print(f"Found subtask: {subtask_text}")
        
        # Check if LLM is available
        from llm_config import qwen_llm, gemini_llm
        if not qwen_llm and not gemini_llm:
            # Return a helpful mock result when LLM is not available
            mock_result = f"""# AI Generated Result for: {subtask_text}

## Analysis
This is a placeholder response because LLM API keys are not configured.

## What needs to be done:
1. Set up API keys for either Google Gemini or OpenRouter
2. Configure environment variables:
   - GOOGLE_API_KEY for Gemini
   - OPENROUTER_API_KEY for Qwen

## Next Steps:
- Review the subtask requirements
- Break down into actionable steps
- Set realistic timelines
- Identify required resources

## Note:
This is a mock response. Enable real AI generation by setting up API keys."""
            
            return {"result": mock_result}
        
        # Use real LLM if available
        result = langgraph_agentic_tracker.execute_subtask(subtask_id)
        
        if result.get("success"):
            print(f"AI generation successful for subtask {subtask_id}")
            return {"result": result["result"]}
        else:
            error_msg = result.get('error', 'Unknown error')
            print(f"Subtask execution failed for {subtask_id}: {error_msg}")
            return {"result": f"Unable to generate AI result for subtask {subtask_id}: {error_msg}"}
            
    except Exception as e:
        print(f"Error in ai_generate_subtask for subtask {subtask_id}: {e}")
        import traceback
        traceback.print_exc()
        return {"result": f"Error generating AI result for subtask {subtask_id}: {str(e)}"}

# ============================================================================
# Standard Database Endpoints
# ============================================================================

@app.get("/api/objectives")
def list_objectives():
    """Get all objectives"""
    objs = db.get_all_objectives()
    result = []
    for obj in objs:
        obj_id, objective, deadline, category, owner = obj
        progress = db.get_objective_progress(obj_id)
        result.append({
            "id": obj_id,
            "objective": objective,
            "deadline": deadline,
            "category": category,
            "owner": owner,
            "progress": progress
        })
    return {"objectives": result}

@app.get("/api/objectives/{objective_id}/tasks")
def get_objective_tasks(objective_id: int):
    """Get tasks for an objective"""
    tasks = db.get_tasks(objective_id)
    result = []
    for t in tasks:
        task_id = t[0]
        subtasks = db.get_subtasks(task_id)
        # Calculate progress based on the weight of subtasks
        completed_weight = sum(st[9] for st in subtasks if st[3] and st[9] is not None)
        total_weight = sum(st[9] for st in subtasks if st[9] is not None)
        progress = round((completed_weight / total_weight) * 100, 2) if total_weight > 0 else 0.0
        result.append({
            "id": task_id,
            "name": t[2],
            "deadline": t[6],
            "progress": progress,
            "subtasks": [
                {
                    "id": st[0],
                    "name": st[2],
                    "deadline": st[8],
                    "status": st[11],
                    "weight": st[9],
                    "result": st[4],
                    "comment": st[5],
                    "ai_generated_result": st[10],
                } for st in subtasks
            ]
        })
    return {"tasks": result}

@app.get("/api/objectives/{objective_id}/progress")
def get_objective_progress_api(objective_id: int):
    """Get progress summary for an objective"""
    tasks = db.get_tasks(objective_id)
    total_tasks = len(tasks)
    # Weighted per-task progress (each task progress weighted by task weight)
    total_task_weight = 0.0
    weighted_task_progress_sum = 0.0
    # Weighted subtask completion across the whole objective
    total_subtask_weight_all = 0.0
    completed_subtask_weight_all = 0.0

    for task in tasks:
        task_id = task[0]
        task_weight = task[7] if task[7] is not None else 1.0
        total_task_weight += task_weight

        subtasks = db.get_subtasks(task_id)
        if not subtasks:
            # If no subtasks, treat task completion as binary
            task_completed = bool(task[3])
            task_progress_ratio = 1.0 if task_completed else 0.0
        else:
            sub_completed_weight = sum(st[9] for st in subtasks if st[3] and st[9] is not None)
            sub_total_weight = sum(st[9] for st in subtasks if st[9] is not None)
            task_progress_ratio = (sub_completed_weight / sub_total_weight) if sub_total_weight > 0 else 0.0
            completed_subtask_weight_all += sub_completed_weight
            total_subtask_weight_all += sub_total_weight

        weighted_task_progress_sum += task_progress_ratio * task_weight

    task_completion_weighted = (weighted_task_progress_sum / total_task_weight * 100.0) if total_task_weight > 0 else 0.0
    subtask_completion_weighted = (completed_subtask_weight_all / total_subtask_weight_all * 100.0) if total_subtask_weight_all > 0 else 0.0

    obj_progress = db.get_objective_progress(objective_id)
    # Keep raw counts for UI, but percentages now reflect weights
    completed_tasks_count = sum(1 for task in tasks if task[3])
    total_subtasks_count = sum(len(db.get_subtasks(task[0])) for task in tasks)
    completed_subtasks_count = sum(sum(1 for s in db.get_subtasks(task[0]) if s[3]) for task in tasks)

    return {"summary": {
        "taskCompletion": round(task_completion_weighted, 2),
        "completedTasks": completed_tasks_count,
        "totalTasks": total_tasks,
        "subtaskCompletion": round(subtask_completion_weighted, 2),
        "completedSubtasks": completed_subtasks_count,
        "totalSubtasks": total_subtasks_count,
        "objectiveCompletion": round(obj_progress, 2)
    }}

@app.post("/api/subtasks/{subtask_id}/update")
def update_subtask_api(subtask_id: int, update: SubtaskUpdate):
    """Update a subtask with manual result"""
    db.save_subtask_result(subtask_id, update.result, update.comment)
    db.mark_subtask_complete(subtask_id)
    # Update parent task progress
    subtask = db.get_subtask_by_id(subtask_id)
    if subtask:
        task_id = subtask[1]
        db.update_task_progress_from_subtasks(task_id)
    return {"subtask_id": subtask_id, "message": "Subtask updated successfully."}

@app.post("/api/subtasks/{subtask_id}/review")
def review_subtask(subtask_id: int, action: ReviewAction):
    """Review a subtask"""
    db.update_review_status(subtask_id, action.status)
    db.mark_subtask_complete(subtask_id)
    # Update parent task progress
    subtask = db.get_subtask_by_id(subtask_id)
    if subtask:
        task_id = subtask[1]
        db.update_task_progress_from_subtasks(task_id)
    return {"subtask_id": subtask_id, "message": "Subtask review updated."}

@app.post("/api/subtasks/{subtask_id}/edit")
def edit_subtask(subtask_id: int, action: EditAction):
    """Edit a subtask result"""
    db.save_ai_generated_result(subtask_id, action.result)
    db.update_review_status(subtask_id, "edited")
    # Update parent task progress
    subtask = db.get_subtask_by_id(subtask_id)
    if subtask:
        task_id = subtask[1]
        db.update_task_progress_from_subtasks(task_id)
    return {"subtask_id": subtask_id, "message": "Manual result saved."}

@app.post("/api/subtasks/{subtask_id}/regenerate")
def regenerate_subtask(subtask_id: int):
    """Regenerate AI result for a subtask"""
    return execute_subtask_agentic(subtask_id)

# ============================================================================
# Reminder Endpoints
# ============================================================================

@app.get("/reminders/check/")
def trigger_reminder_check():
    """Check for due reminders - format for frontend"""
    import remainder_agent
    raw_reminders = remainder_agent.get_due_reminders()
    
    
    formatted_reminders = []
    
    for reminder in raw_reminders:
        
        for task in reminder.get('tasks', []):
            try:
                deadline_date = datetime.strptime(task['deadline'], '%Y-%m-%d')
                days_until = (deadline_date - datetime.now()).days
                status = 'overdue' if days_until < 0 else 'due_soon'
                
                formatted_reminders.append({
                    'type': 'task',
                    'name': task['name'],
                    'deadline': task['deadline'],
                    'status': status,
                    'objective': reminder['objective'][:50] + '...' if len(reminder['objective']) > 50 else reminder['objective']
                })
            except:
                continue
        
        
        
        for subtask in reminder.get('subtasks', []):
            try:
                deadline_date = datetime.strptime(subtask['deadline'], '%Y-%m-%d')
                days_until = (deadline_date - datetime.now()).days
                status = 'overdue' if days_until < 0 else 'due_soon'
                
                formatted_reminders.append({
                    'type': 'subtask',
                    'name': subtask['name'],
                    'deadline': subtask['deadline'],
                    'status': status,
                    'objective': reminder['objective'][:50] + '...' if len(reminder['objective']) > 50 else reminder['objective']
                })
            except:
                continue
    
    
    
    formatted_reminders.sort(key=lambda x: x['deadline'])
    
    return {"reminders": formatted_reminders}

@app.post("/api/progress/update-all")
def update_all_progress():
    """Update progress for all objectives and tasks"""
    try:
        import db
        objectives = db.get_all_objectives()
        updated_count = 0
        
        for objective in objectives:
            objective_id = objective[0]
            
            
            tasks = db.get_tasks(objective_id)
            for task in tasks:
                task_id = task[0]
                db.update_task_progress_from_subtasks(task_id)
                updated_count += 1
        
        
        
        import remainder_agent
        remainder_agent.check_and_send_reminders()
        
        return {
            "success": True, 
            "message": f"Updated progress for {updated_count} tasks",
            "objectives_checked": len(objectives)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/reminders/trigger")
def trigger_manual_reminder():
    """Manually trigger reminder check"""
    try:
        from remainder_agent import check_and_send_reminders
        summary = check_and_send_reminders()
        return {"success": True, "message": "Reminder check completed", "summary": summary}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/reminders/test")
def test_reminder_system():
    """Test the reminder system and show what would be sent"""
    try:
        import remainder_agent
        reminders = remainder_agent.get_due_reminders()
        
        reminder_details = []
        for reminder in reminders:
            reminder_details.append({
                "objective": reminder['objective'],
                "deadline": reminder['deadline'],
                "owner": reminder.get('owner', 'Not specified'),
                "tasks": reminder.get('tasks', []),
                "subtasks": reminder.get('subtasks', []),
                "total_tasks": len(reminder.get('tasks', [])),
                "total_subtasks": len(reminder.get('subtasks', []))
            })
        
        return {
            "success": True,
            "reminders_found": len(reminders),
            "reminder_details": reminder_details,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================================================
# Reminder Scheduler Integration
# ============================================================================

@app.post("/api/reminders/scheduler/start")
def start_reminder_scheduler():
    """Start the reminder scheduler"""
    try:
        from reminder_scheduler import start_reminder_scheduler
        start_reminder_scheduler()
        return {
            "success": True,
            "message": "Reminder scheduler started successfully",
            "schedule": {
                "morning_reminder": "9:00 AM daily",
                "business_checks": "10:00 AM, 2:00 PM, 4:00 PM daily",
                "end_of_day": "5:00 PM daily"
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/reminders/scheduler/stop")
def stop_reminder_scheduler():
    """Stop the reminder scheduler"""
    try:
        from reminder_scheduler import stop_reminder_scheduler
        stop_reminder_scheduler()
        return {
            "success": True,
            "message": "Reminder scheduler stopped successfully"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/reminders/scheduler/status")
def get_scheduler_status():
    """Get scheduler status"""
    try:
        from reminder_scheduler import get_scheduler_status
        status = get_scheduler_status()
        return {
            "success": True,
            "status": status
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================================================
# Dashboard API Endpoints
# ============================================================================

@app.get("/api/dashboard/overview")
def get_dashboard_overview():
    """Get comprehensive dashboard overview"""
    try:
        import db
        from datetime import datetime, timedelta
        
        # Get all objectives
        objectives = db.get_all_objectives()
        
        # Calculate overall statistics
        total_objectives = len(objectives)
        active_objectives = 0
        completed_objectives = 0
        total_progress = 0.0
        overdue_count = 0
        due_soon_count = 0
        
        # Get current date
        today = datetime.now().date()
        
        for obj in objectives:
            objective_id = obj[0]
            deadline = datetime.strptime(obj[2], '%Y-%m-%d').date()
            progress = db.get_objective_progress(objective_id)
            
            total_progress += progress
            
            if progress >= 100:
                completed_objectives += 1
            else:
                active_objectives += 1
            
            # Check for overdue or due soon
            days_until_deadline = (deadline - today).days
            if days_until_deadline < 0:
                overdue_count += 1
            elif days_until_deadline <= 2:
                due_soon_count += 1
        
        # Get urgent items for more accurate counts
        urgent_items = get_urgent_items_internal()
        overdue_count = len(urgent_items["overdue_tasks"]) + len(urgent_items["overdue_subtasks"])
        due_soon_count = len(urgent_items["due_soon_tasks"]) + len(urgent_items["due_soon_subtasks"])
        
        # Calculate overall progress
        overall_progress = round(total_progress / total_objectives, 2) if total_objectives > 0 else 0.0
        
        # Get urgent items
        urgent_items = get_urgent_items_internal()
        
        return {
            "success": True,
            "overview": {
                "total_objectives": total_objectives,
                "active_objectives": active_objectives,
                "completed_objectives": completed_objectives,
                "overall_progress": overall_progress,
                "overdue_count": overdue_count,
                "due_soon_count": due_soon_count,
                "urgent_items": urgent_items
            }
        }
        
    except Exception as e:
        print(f"Error getting dashboard overview: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/dashboard/statistics")
def get_dashboard_statistics():
    """Get aggregated statistics across all objectives"""
    try:
        import db
        from collections import defaultdict
        
        objectives = db.get_all_objectives()
        
        # Statistics by category
        category_stats = defaultdict(lambda: {"count": 0, "progress": 0.0, "total_progress": 0.0})
        owner_stats = defaultdict(lambda: {"count": 0, "progress": 0.0, "total_progress": 0.0})
        
        for obj in objectives:
            objective_id = obj[0]
            category = obj[3] or "Uncategorized"
            owner = obj[4] or "Unassigned"
            progress = db.get_objective_progress(objective_id)
            
            # Category statistics
            category_stats[category]["count"] += 1
            category_stats[category]["total_progress"] += progress
            
            # Owner statistics
            owner_stats[owner]["count"] += 1
            owner_stats[owner]["total_progress"] += progress
        
        # Calculate averages
        for category in category_stats:
            count = category_stats[category]["count"]
            category_stats[category]["progress"] = round(category_stats[category]["total_progress"] / count, 2)
            
        for owner in owner_stats:
            count = owner_stats[owner]["count"]
            owner_stats[owner]["progress"] = round(owner_stats[owner]["total_progress"] / count, 2)
        
        # Convert to regular dict for JSON serialization
        category_stats = dict(category_stats)
        owner_stats = dict(owner_stats)
        
        return {
            "success": True,
            "statistics": {
                "by_category": category_stats,
                "by_owner": owner_stats
            }
        }
        
    except Exception as e:
        print(f"Error getting dashboard statistics: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/dashboard/urgent-items")
def get_urgent_items():
    """Get items requiring immediate attention"""
    try:
        urgent_items = get_urgent_items_internal()
        return {
            "success": True,
            "urgent_items": urgent_items
        }
    except Exception as e:
        print(f"Error getting urgent items: {e}")
        return {"success": False, "error": str(e)}

def get_urgent_items_internal():
    """Internal function to get urgent items"""
    import db
    from datetime import datetime, timedelta
    
    urgent_items = {
        "overdue_tasks": [],
        "due_soon_tasks": [],
        "overdue_subtasks": [],
        "due_soon_subtasks": []
    }
    
    today = datetime.now().date()
    
    # Get all objectives and their tasks/subtasks
    objectives = db.get_all_objectives()
    
    for obj in objectives:
        objective_id = obj[0]
        objective_name = obj[1]
        tasks = db.get_tasks(objective_id)
        
        for task in tasks:
            task_id = task[0]
            task_name = task[2]
            task_deadline = task[6]
            
            if task_deadline:
                task_deadline_date = datetime.strptime(task_deadline, '%Y-%m-%d').date()
                days_until = (task_deadline_date - today).days
                
                if days_until < 0:
                    urgent_items["overdue_tasks"].append({
                        "id": task_id,
                        "name": task_name,
                        "objective_id": objective_id,
                        "objective_name": objective_name,
                        "deadline": task_deadline,
                        "days_overdue": abs(days_until)
                    })
                elif days_until <= 2:
                    urgent_items["due_soon_tasks"].append({
                        "id": task_id,
                        "name": task_name,
                        "objective_id": objective_id,
                        "objective_name": objective_name,
                        "deadline": task_deadline,
                        "days_until": days_until
                    })
            
            # Check subtasks
            subtasks = db.get_subtasks(task_id)
            for subtask in subtasks:
                subtask_id = subtask[0]
                subtask_name = subtask[2]
                subtask_deadline = subtask[8]
                
                if subtask_deadline:
                    subtask_deadline_date = datetime.strptime(subtask_deadline, '%Y-%m-%d').date()
                    days_until = (subtask_deadline_date - today).days
                    
                    if days_until < 0:
                        urgent_items["overdue_subtasks"].append({
                            "id": subtask_id,
                            "name": subtask_name,
                            "task_id": task_id,
                            "task_name": task_name,
                            "objective_id": objective_id,
                            "objective_name": objective_name,
                            "deadline": subtask_deadline,
                            "days_overdue": abs(days_until)
                        })
                    elif days_until <= 2:
                        urgent_items["due_soon_subtasks"].append({
                            "id": subtask_id,
                            "name": subtask_name,
                            "task_id": task_id,
                            "task_name": task_name,
                            "objective_id": objective_id,
                            "objective_name": objective_name,
                            "deadline": subtask_deadline,
                            "days_until": days_until
                        })
    
    return urgent_items

@app.get("/reminders/debug")
def debug_reminders():
    """Debug endpoint to see what's in the database"""
    try:
        import db
        from datetime import datetime
        
        # Get all objectives
        objectives = db.get_all_objectives()
        debug_info = {
            "total_objectives": len(objectives),
            "objectives": []
        }
        
        for obj in objectives:
            objective_id = obj[0]
            objective_name = obj[1]
            deadline = obj[2]
            
            # Get tasks for this objective
            tasks = db.get_tasks(objective_id)
            task_info = []
            
            for task in tasks:
                task_id = task[0]
                task_name = task[2]
                task_deadline = task[6]
                task_completed = task[3]
                
                # Get subtasks for this task
                subtasks = db.get_subtasks(task_id)
                subtask_info = []
                
                for subtask in subtasks:
                    subtask_id = subtask[0]
                    subtask_name = subtask[2]
                    subtask_deadline = subtask[8]
                    subtask_completed = subtask[3]
                    
                    subtask_info.append({
                        "id": subtask_id,
                        "name": subtask_name,
                        "deadline": subtask_deadline,
                        "completed": subtask_completed
                    })
                
                task_info.append({
                    "id": task_id,
                    "name": task_name,
                    "deadline": task_deadline,
                    "completed": task_completed,
                    "subtasks": subtask_info
                })
            
            debug_info["objectives"].append({
                "id": objective_id,
                "name": objective_name,
                "deadline": deadline,
                "tasks": task_info
            })
        
        return debug_info
        
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/deadlines/recalculate")
def recalculate_deadlines():
    """Recalculate realistic deadlines for all objectives"""
    try:
        from deadline_calculator import recalculate_all_deadlines
        
        updated_count = recalculate_all_deadlines()
        
        return {
            "success": True,
            "message": f"Successfully recalculated deadlines for {updated_count} objectives",
            "updated_count": updated_count
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/deadlines/recalculate/{objective_id}")
def recalculate_objective_deadlines(objective_id: int):
    """Recalculate realistic deadlines for a specific objective"""
    try:
        from deadline_calculator import DeadlineCalculator
        
        calculator = DeadlineCalculator()
        success = calculator.update_database_deadlines(objective_id)
        
        if success:
            return {
                "success": True,
                "message": f"Successfully recalculated deadlines for objective {objective_id}"
            }
        else:
            return {"success": False, "error": "Failed to update deadlines"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/deadlines/validate-boundaries")
def validate_deadline_boundaries(objective_id: int):
    """Validate that all subtask deadlines are within their parent task boundaries"""
    try:
        from deadline_calculator import DeadlineCalculator
        
        calculator = DeadlineCalculator()
        
        # Get the current deadlines from database
        conn = calculator.get_conn()
        cursor = conn.cursor()
        
        try:
            # Get objective details
            cursor.execute("SELECT objective, deadline FROM objectives WHERE id = ?", (objective_id,))
            objective_data = cursor.fetchone()
            if not objective_data:
                return {"success": False, "error": "Objective not found"}
            
            objective_name, objective_deadline = objective_data
            
            # Get all tasks and their deadlines
            cursor.execute("""
                SELECT id, task, deadline, weight 
                FROM tasks 
                WHERE objective_id = ? 
                ORDER BY id ASC
            """, (objective_id,))
            tasks = cursor.fetchall()
            
            # Get all subtasks and their deadlines
            cursor.execute("""
                SELECT id, subtask, deadline, task_id, weight 
                FROM subtasks 
                WHERE task_id IN (SELECT id FROM tasks WHERE objective_id = ?)
                ORDER BY task_id ASC, id ASC
            """, (objective_id,))
            subtasks = cursor.fetchall()
            
            # Validate boundaries
            validation_results = {
                "objective_id": objective_id,
                "objective_name": objective_name,
                "objective_deadline": objective_deadline,
                "tasks": [],
                "subtasks": [],
                "boundary_violations": [],
                "overall_status": "valid"
            }
            
            # Process tasks
            task_boundaries = {}
            for task in tasks:
                task_id, task_name, task_deadline, task_weight = task
                
                if task_deadline:
                    task_date = datetime.strptime(task_deadline, '%Y-%m-%d').date()
                    task_boundaries[task_id] = task_date
                    
                    validation_results["tasks"].append({
                        "id": task_id,
                        "name": task_name,
                        "deadline": task_deadline,
                        "weight": task_weight,
                        "status": "valid"
                    })
                else:
                    validation_results["tasks"].append({
                        "id": task_id,
                        "name": task_name,
                        "deadline": None,
                        "weight": task_weight,
                        "status": "no_deadline"
                    })
            
            # Process subtasks
            for subtask in subtasks:
                subtask_id, subtask_name, subtask_deadline, task_id, subtask_weight = subtask
                
                if subtask_deadline and task_id in task_boundaries:
                    subtask_date = datetime.strptime(subtask_deadline, '%Y-%m-%d').date()
                    task_deadline = task_boundaries[task_id]
                    
                    if subtask_date > task_deadline:
                        violation = {
                            "subtask_id": subtask_id,
                            "subtask_name": subtask_name,
                            "subtask_deadline": subtask_deadline,
                            "task_deadline": task_deadline.strftime('%Y-%m-%d'),
                            "violation_type": "exceeds_task_boundary",
                            "days_over": (subtask_date - task_deadline).days
                        }
                        validation_results["boundary_violations"].append(violation)
                        validation_results["overall_status"] = "invalid"
                        
                        validation_results["subtasks"].append({
                            "id": subtask_id,
                            "name": subtask_name,
                            "deadline": subtask_deadline,
                            "task_id": task_id,
                            "weight": subtask_weight,
                            "status": "boundary_violation",
                            "violation": violation
                        })
                    else:
                        validation_results["subtasks"].append({
                            "id": subtask_id,
                            "name": subtask_name,
                            "deadline": subtask_deadline,
                            "task_id": task_id,
                            "weight": subtask_weight,
                            "status": "valid"
                        })
                else:
                    validation_results["subtasks"].append({
                        "id": subtask_id,
                        "name": subtask_name,
                        "deadline": subtask_deadline,
                        "task_id": task_id,
                        "weight": subtask_weight,
                        "status": "no_deadline" if not subtask_deadline else "orphaned"
                    })
            
            return validation_results
            
        finally:
            conn.close()
            
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================================================
# Advanced Deadline Shifting and Dynamic Rescheduling Endpoints
# ============================================================================

@app.get("/api/deadlines/progress-drift/{objective_id}")
def get_progress_drift(objective_id: int):
    """Get progress drift analysis for an objective"""
    try:
        from deadline_shifter import DeadlineShifter
        
        shifter = DeadlineShifter()
        drift_analysis = shifter.calculate_progress_drift(objective_id)
        
        return {
            "success": True,
            "objective_id": objective_id,
            "drift_analysis": drift_analysis
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/deadlines/shift/{objective_id}")
def shift_objective_deadlines_endpoint(objective_id: int, shift_days: int, reason: str = "manual"):
    """Shift objective deadlines by a specified number of business days"""
    try:
        from deadline_shifter import shift_objective_deadlines
        
        result = shift_objective_deadlines(objective_id, shift_days, reason)
        
        if result.get("success"):
            return {
                "success": True,
                "message": result["message"],
                "shift_details": result.get("shift_details", {})
            }
        else:
            return result
            
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/deadlines/auto-adjust/{objective_id}")
def auto_adjust_deadlines_endpoint(objective_id: int):
    """Automatically adjust deadlines based on progress analysis"""
    try:
        from deadline_shifter import auto_adjust_deadlines
        
        result = auto_adjust_deadlines(objective_id)
        
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/deadlines/validate-shift/{objective_id}")
def validate_deadline_shift(objective_id: int, shift_days: int):
    """Validate the impact of a proposed deadline shift"""
    try:
        from deadline_shifter import DeadlineShifter
        
        shifter = DeadlineShifter()
        validation = shifter.validate_shift_impact(objective_id, shift_days)
        
        return {
            "success": True,
            "validation": validation
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/deadlines/dependency-adjust/{objective_id}")
def adjust_deadlines_for_dependencies(objective_id: int):
    """Automatically adjust deadlines based on dependency conflicts"""
    try:
        from deadline_shifter import DeadlineShifter
        
        shifter = DeadlineShifter()
        result = shifter.auto_adjust_for_dependencies(objective_id)
        
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/deadlines/shift-history/{objective_id}")
def get_deadline_shift_history(objective_id: int):
    """Get history of deadline shifts for an objective"""
    try:
        from deadline_shifter import DeadlineShifter
        
        shifter = DeadlineShifter()
        history = shifter.get_shift_history(objective_id)
        
        return {
            "success": True,
            "objective_id": objective_id,
            "shift_history": history
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================================================
# Main Application
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting API server...")
    print("📡 Server will be available at: http://localhost:8000")
    print("🔧 CORS enabled for frontend at: http://localhost:3000")
    
    try:
        uvicorn.run("api_server_agentic:app", host="0.0.0.0", port=8000, reload=True)
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        import traceback
        traceback.print_exc() 