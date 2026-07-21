from langgraph.graph import StateGraph, END
from models import AgentState
from agents import (
    input_analysis_agent,
    task_planning_agent,
    weight_assignment_agent,
    llm_scheduling_agent as realistic_scheduling_agent,  
    schedule_generation_agent,
    database_creation_agent,
    progress_analysis_agent,
    recommendation_agent,
)
def should_analyze_progress(state: AgentState) -> str:
    """Determine if we should run progress analysis"""
    
    if state.get("objective_id") and not state.get("is_initial_creation", True):
        return "progress_analysis"
    else:
        return END

def should_generate_recommendations(state: AgentState) -> str:
    """Determine if we should generate recommendations"""
    
    if state.get("progress_analysis"):
        return "recommendation"
    else:
        return END

def should_use_realistic_scheduling(state: AgentState) -> str:
    """Determine if we should use realistic scheduling or mathematical fallback"""
    if state.get("is_initial_creation", True):
        return "realistic_scheduling"
    else:
        return "schedule_generation"

def create_agent_graph() -> StateGraph:
    """Create the agent workflow graph"""
    
    workflow = StateGraph(AgentState)
    workflow.add_node("input_analysis", input_analysis_agent)
    workflow.add_node("task_planning", task_planning_agent)
    workflow.add_node("weight_assignment", weight_assignment_agent)
    workflow.add_node("realistic_scheduling", realistic_scheduling_agent) 
    workflow.add_node("schedule_generation", schedule_generation_agent)
    workflow.add_node("database_creation", database_creation_agent)
    workflow.add_node("progress_analysis", progress_analysis_agent)
    workflow.add_node("recommendation", recommendation_agent)
    

    workflow.set_entry_point("input_analysis")
    workflow.add_edge("input_analysis", "task_planning")
    workflow.add_edge("task_planning", "weight_assignment")
    

    workflow.add_conditional_edges("weight_assignment", should_use_realistic_scheduling)
    workflow.add_edge("realistic_scheduling", "schedule_generation") 
    workflow.add_edge("schedule_generation", "database_creation")
    
   
    workflow.add_conditional_edges("database_creation", should_analyze_progress)
    workflow.add_conditional_edges("progress_analysis", should_generate_recommendations)
    workflow.add_edge("recommendation", END)
    
    return workflow.compile() 