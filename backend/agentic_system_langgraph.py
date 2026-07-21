import sys
import os
from typing import Dict

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import AgentState
from database_tools import generate_ai_result_tool
from graph import create_agent_graph
import db


# ============================================================================
# Main Interface
# ============================================================================

class LangGraphAgenticProgressTracker:
    """LangGraph-based agentic progress tracking system"""

    def __init__(self):
        self.graph = create_agent_graph()
        db.init_db()

    def create_objective_with_agents(
        self, objective: str, deadline: str, category: str = None, owner: str = None
    ) -> Dict:
        """Create a new objective using the LangGraph agentic system"""

        initial_state = AgentState(
            objective=objective,
            deadline=deadline,
            category=category,
            owner=owner,
            inputs={},
            task_breakdown=None,
            weight_assignment=None,
            progress_analysis=None,
            ai_recommendation=None,
            objective_id=None,
            current_task_id=None,
            current_subtask_id=None,
            messages=[],
            error=None,
            llm_subtask_count_issue=False,
            generated_schedule=None,
            is_initial_creation=True,
        )

        try:
            result = self.graph.invoke(initial_state)
            print("LangGraph execution completed successfully")

            # Try saving graph visualization
            try:
                graph_obj = self.graph.get_graph()

                out_dir = os.path.join(os.path.dirname(__file__), "graphs")
                os.makedirs(out_dir, exist_ok=True)
                out_file = os.path.join(out_dir, "agent_flow")

                if hasattr(graph_obj, "render"):
                    graph_obj.render(out_file, format="png", cleanup=True)
                elif hasattr(graph_obj, "write_png"):
                    graph_obj.write_png(out_file + ".png")
                elif hasattr(graph_obj, "draw_png"):
                    png_bytes = graph_obj.draw_png()
                    with open(out_file + ".png", "wb") as f:
                        f.write(png_bytes)
                print(f"Saved graph to {out_file}.png")
            except Exception as ge:
                print(f"Graph save failed: {ge}")

            return {
                "success": True,
                "objective_id": result["objective_id"],
                "task_breakdown": result["task_breakdown"],
                "weight_assignment": result["weight_assignment"],
                "progress_analysis": result.get("progress_analysis", None),
                "ai_recommendation": result.get("ai_recommendation", None),
                "agent_messages": result["messages"],
            }
        except Exception as e:
            print(f"LangGraph execution error: {e}")
            return {
                "success": False,
                "error": str(e),
                "messages": getattr(initial_state, "messages", []),
            }

    def analyze_progress(self, objective_id: int) -> Dict:
        """Analyze progress for an existing objective using LangGraph"""

        objectives = db.get_all_objectives()
        objective_data = next((obj for obj in objectives if obj[0] == objective_id), None)

        if not objective_data:
            return {"success": False, "error": "Objective not found"}

        initial_state = AgentState(
            objective=objective_data[1],
            deadline=objective_data[2],
            category=objective_data[3],
            owner=objective_data[4],
            inputs={},
            task_breakdown=None,
            weight_assignment=None,
            progress_analysis=None,
            ai_recommendation=None,
            objective_id=objective_id,
            current_task_id=None,
            current_subtask_id=None,
            messages=[],
            error=None,
            llm_subtask_count_issue=False,
            is_initial_creation=False,
        )

        try:
            from langgraph.graph import StateGraph, END
            from agents import progress_analysis_agent, recommendation_agent

            analysis_graph = StateGraph(AgentState)
            analysis_graph.add_node("progress_analysis", progress_analysis_agent)
            analysis_graph.add_node("recommendation", recommendation_agent)
            analysis_graph.set_entry_point("progress_analysis")
            analysis_graph.add_edge("progress_analysis", "recommendation")
            analysis_graph.add_edge("recommendation", END)

            compiled_graph = analysis_graph.compile()
            result = compiled_graph.invoke(initial_state)

            return {
                "success": True,
                "progress_analysis": result["progress_analysis"],
                "ai_recommendation": result["ai_recommendation"],
                "messages": result["messages"],
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "messages": getattr(initial_state, "messages", []),
            }

    def execute_subtask(self, subtask_id: int) -> Dict:
        """Execute a specific subtask using AI with LLM only"""

        try:
            subtask = db.get_subtask_by_id(subtask_id)
            if not subtask:
                return {"success": False, "error": "Subtask not found"}

            subtask_text = subtask[2] if len(subtask) > 2 else "Unknown subtask"

            print(f"[Agent] execute_subtask: Executing subtask {subtask_id} with Qwen3 235B...")
            print(f"[Agent] Subtask text: {subtask_text}")

            from llm_config import qwen_llm
            if qwen_llm is None:
                return {"success": False, "error": "LLM not initialized - check API keys"}

            # Use the LangChain tool properly
            if hasattr(generate_ai_result_tool, "invoke"):
                result = generate_ai_result_tool.invoke({
                    "subtask_id": subtask_id,
                    "subtask_text": subtask_text,
                })
            else:
                result = generate_ai_result_tool({
                    "subtask_id": subtask_id,
                    "subtask_text": subtask_text,
                })

            if result and len(str(result).strip()) > 50:
                return {
                    "success": True,
                    "result": result,
                    "subtask_id": subtask_id,
                }
            else:
                raise Exception("Generated content too short or empty")

        except Exception as e:
            print(f"Error executing subtask {subtask_id}: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Subtask execution failed: {str(e)}",
                "subtask_id": subtask_id,
            }


langgraph_agentic_tracker = LangGraphAgenticProgressTracker()

if __name__ == "__main__":
    # Example usage
    response = langgraph_agentic_tracker.create_objective_with_agents(
        objective="Develop a new feature for the product",
        deadline="2024-12-31",
        category="Product Development",
        owner="Alice",
    )
    print(response)
