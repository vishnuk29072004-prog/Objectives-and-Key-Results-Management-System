import os
import time
import random
from collections import defaultdict
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env file")
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
except Exception as e:
    print(f"⚠️  Could not load .env file: {e}")

# ============================================================================
# Multi-Model LLM Configuration
# ============================================================================


gemini_llm = None
qwen_llm = None

rate_limit_tracker = defaultdict(int)
model_blacklist = set()
last_blacklist_reset = time.time()

def reset_rate_limit_blacklist():
    """Reset the rate limit blacklist every hour"""
    global last_blacklist_reset, model_blacklist, rate_limit_tracker
    current_time = time.time()
    if current_time - last_blacklist_reset > 3600: 
        model_blacklist.clear()
        rate_limit_tracker.clear()
        last_blacklist_reset = current_time
        print("Rate limit blacklist reset")

def initialize_llms():
    """Initialize LLM models based on available API keys"""
    global gemini_llm, qwen_llm
    
   
    google_api_key = os.getenv("GOOGLE_API_KEY")
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    print(f"API Keys Status - Google: {'✅' if google_api_key else '❌'}, OpenRouter: {'✅' if openrouter_api_key else '❌'}") 
    if google_api_key:
        try:
            gemini_llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-001",
                google_api_key=google_api_key,
                temperature=0.7,
                max_retries=3,
                timeout=30
            )
            print("✅ Gemini LLM initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Gemini LLM: {e}")
            gemini_llm = None
    else:
        print("⚠️ GOOGLE_API_KEY not found - Gemini LLM not initialized")
        gemini_llm = None

    if openrouter_api_key:
        try:
            qwen_llm = ChatOpenAI(
                model="qwen/qwen3-235b-a22b",
                base_url="https://openrouter.ai/api/v1",
                api_key=openrouter_api_key,
                temperature=0.7,
                max_retries=3,
                timeout=30
            )
            print("✅ Qwen LLM initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Qwen LLM: {e}")
            qwen_llm = None
    else:
        print("⚠️ OPENROUTER_API_KEY not found - Qwen LLM not initialized")
        qwen_llm = None
    if gemini_llm or qwen_llm:
        print("✅ At least one LLM is available")
    else:
        print("❌ No LLMs are available - API keys required")

def safe_llm_call(prompt, llm_model, max_retries=2, base_delay=1, agent_name=None, callbacks=None):
    """Safely call LLM with retry logic and rate limit handling - NO FALLBACK"""
    if agent_name:
        print(f"[LLM CALL] Agent: {agent_name}")
    if llm_model is None:
        raise Exception("LLM model is not initialized - check API keys")
    
    reset_rate_limit_blacklist()
    
    model_name = llm_model.__class__.__name__
    if model_name in model_blacklist:
        raise Exception(f"Model {model_name} is blacklisted due to rate limits")
    if callbacks is None:
        callbacks = []
    
    for attempt in range(max_retries):
        try:
            print(f"LLM call attempt {attempt + 1}/{max_retries} using {llm_model.__class__.__name__}")
            response = llm_model.invoke(prompt, config={"callbacks": callbacks})
            content = response.content if hasattr(response, 'content') else str(response)
            if content and len(content.strip()) > 5: 
                print(f"LLM call successful on attempt {attempt + 1}")
                rate_limit_tracker[model_name] = 0
                return content
            else:
                print(f"LLM returned minimal content, retrying...")
                if attempt < max_retries - 1:
                    time.sleep(base_delay * (1 + attempt))
                    continue
                else:
                    raise Exception("LLM returned insufficient content after all retries")
                    
        except Exception as e:
            error_str = str(e).lower()
            if "rate" in error_str or "429" in error_str or "quota" in error_str:
                print(f"Rate limited/quota exceeded on {llm_model.__class__.__name__}: {e}")
                rate_limit_tracker[model_name] += 1
                if rate_limit_tracker[model_name] >= 3:
                    model_blacklist.add(model_name)
                    print(f"Model {model_name} blacklisted due to repeated rate limits")
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                print(f"Rate limited, waiting {delay:.2f}s before retry {attempt + 1}/{max_retries}")
                time.sleep(delay)
            elif "timeout" in error_str or "time" in error_str:
                
                delay = base_delay * (1 + attempt)
                print(f"Timeout error, retrying in {delay}s: {e}")
                time.sleep(delay)
            elif attempt < max_retries - 1:
                
                delay = base_delay * (1 + attempt)
                print(f"LLM call failed, retrying in {delay}s: {e}")
                time.sleep(delay)
            else:
               
                raise Exception(f"LLM call failed after {max_retries} attempts: {e}")
    
    raise Exception("LLM call failed after all retries")
initialize_llms() 