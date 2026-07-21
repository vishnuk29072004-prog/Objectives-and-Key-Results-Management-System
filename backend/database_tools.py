from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_core.callbacks import CallbackManager
from langchain_core.callbacks.base import BaseCallbackHandler
import db
from llm_config import safe_llm_call, qwen_llm, gemini_llm
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Custom Callback Handler for LangChain Tools
# ============================================================================

class ToolCallbackHandler(BaseCallbackHandler):
    """Custom callback handler for LangChain tools to prevent callback errors"""
    
    def __init__(self):
        super().__init__()
        self.parent_run_id = None
    
    def on_tool_start(self, serialized, input_str, **kwargs):
        """Handle tool start events"""
        logger.info(f"Tool started: {serialized.get('name', 'unknown')}")
        return super().on_tool_start(serialized, input_str, **kwargs)
    
    def on_tool_end(self, output, **kwargs):
        """Handle tool end events"""
        logger.info(f"Tool completed with output length: {len(str(output))}")
        return super().on_tool_end(output, **kwargs)
    
    def on_tool_error(self, error, **kwargs):
        """Handle tool error events"""
        logger.error(f"Tool error: {error}")
        return super().on_tool_error(error, **kwargs)

# ============================================================================
# Database Tools with Proper LangChain Integration
# ============================================================================

@tool
def create_objective_tool(objective: str, deadline: str, category: str = None, owner: str = None) -> int:
    """Create a new objective in the database"""
    try:
        result = db.insert_objective(objective, deadline, category, owner)
        logger.info(f"Created objective with ID: {result}")
        return result
    except Exception as e:
        logger.error(f"Error creating objective: {e}")
        raise Exception(f"Failed to create objective: {e}")

@tool
def create_task_tool(objective_id: int, task_name: str, deadline: str, weight: float = 1.0) -> int:
    """Create a new task in the database"""
    try:
        result = db.insert_task(objective_id, task_name, deadline, weight)
        logger.info(f"Created task with ID: {result}")
        return result
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise Exception(f"Failed to create task: {e}")

@tool
def create_subtask_tool(task_id: int, subtask_name: str, deadline: str, weight: float = 1.0) -> int:
    """Create a new subtask in the database"""
    try:
        result = db.insert_subtask(task_id, subtask_name, deadline, weight)
        logger.info(f"Created subtask with ID: {result}")
        return result
    except Exception as e:
        logger.error(f"Error creating subtask: {e}")
        raise Exception(f"Failed to create subtask: {e}")

@tool
def get_objective_progress_tool(objective_id: int) -> float:
    """Get the current progress percentage for an objective"""
    try:
        progress = db.get_objective_progress(objective_id)
        logger.info(f"Retrieved progress for objective {objective_id}: {progress}%")
        return progress
    except Exception as e:
        logger.error(f"Error getting objective progress: {e}")
        raise Exception(f"Failed to get objective progress: {e}")

@tool
def generate_ai_result_tool(subtask_id: int, subtask_text: str) -> str:
    """Generate AI result for a subtask using Qwen3 235B for creative content"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert task executor and project manager. Your job is to generate detailed, actionable results for specific subtasks.

For the given subtask, provide:
1. A clear breakdown of what needs to be done
2. Specific actionable steps to complete the task
3. Key deliverables or outcomes
4. Important considerations or requirements
5. Timeline estimates if relevant

Write in a clear, professional tone. Be specific and actionable. Focus on practical implementation steps."""),
        ("human", """Generate a detailed, actionable result for this subtask:

Subtask: {subtask_text}

Please provide a comprehensive response that includes specific steps, deliverables, and actionable guidance.""")
    ])
    try:
        logger.info(f"Generating AI result for subtask {subtask_id}")    
        callback_handler = ToolCallbackHandler()
        callback_manager = CallbackManager([callback_handler])
        formatted_prompt = prompt.format_messages(subtask_text=subtask_text)
        llm_content = safe_llm_call(
            formatted_prompt, 
            qwen_llm, 
            max_retries=2, 
            agent_name="generate_ai_result_tool",
            callbacks=[callback_handler]
        )
        if llm_content and len(llm_content.strip()) > 50:
            logger.info(f"Successfully generated AI result for subtask {subtask_id}")
            db.save_ai_generated_result(subtask_id, llm_content)
            return llm_content
        else:
            raise Exception("LLM returned insufficient content for subtask execution")       
    except Exception as e:
        logger.error(f"Error generating AI result for subtask {subtask_id}: {e}")
        # Fallback: Return a mock result if LLM fails
        mock_result = f"""# AI Generated Result for: {subtask_text}

## Analysis
This is a placeholder response because LLM API keys are not valid or credits are exhausted.

## What needs to be done:
1. Set up valid API keys for Google Gemini or OpenRouter
2. Configure environment variables:
   - GOOGLE_API_KEY for Gemini
   - OPENROUTER_API_KEY for Qwen

## Next Steps:
- Review the subtask requirements
- Break down into actionable steps
- Set realistic timelines
- Identify required resources

## Note:
This is a mock response. Enable real AI generation by setting up valid API keys."""
        db.save_ai_generated_result(subtask_id, mock_result)
        return mock_result

@tool
def get_reminders_tool() -> list:
    """Get all upcoming and overdue reminders"""
    try:
        reminders = db.get_all_reminders()
        logger.info(f"Retrieved {len(reminders)} reminders")
        return reminders
    except Exception as e:
        logger.error(f"Error getting reminders: {e}")
        raise Exception(f"Failed to get reminders: {e}")

# ============================================================================
# Tool Registry for Easy Access
# ============================================================================

AVAILABLE_TOOLS = [
    create_objective_tool,
    create_task_tool,
    create_subtask_tool,
    get_objective_progress_tool,
    generate_ai_result_tool,
    get_reminders_tool
]

def get_all_tools():
    """Get all available tools for LangChain agents"""
    return AVAILABLE_TOOLS

def get_tool_by_name(tool_name: str):
    """Get a specific tool by name"""
    for tool in AVAILABLE_TOOLS:
        if tool.name == tool_name:
            return tool
    return None