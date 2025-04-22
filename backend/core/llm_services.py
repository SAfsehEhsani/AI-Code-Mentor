# backend/core/llm_services.py

import os
import ast
from dotenv import load_dotenv

# Import necessary classes for all potential providers
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser

from backend.core.code_parser import parse_python_code # Assuming this path is correct relative to where you run uvicorn

# --- Load Environment Variables ---
# Ensure this runs before accessing environment variables
load_dotenv()

# --- LLM Configuration & Selection ---
# Read the desired provider from environment variables, default to 'openai' if not set
# Make it lowercase for case-insensitive matching
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()

# Define models for each provider (adjust models as needed)
PROVIDER_CONFIG = {
    "openai": {
        "class": ChatOpenAI,
        "model": "gpt-3.5-turbo",
        "api_key_name": "OPENAI_API_KEY"
    },
    "anthropic": {
        "class": ChatAnthropic,
        # Consider using claude-3-haiku... for potentially lower cost/faster response
        "model": "claude-3-sonnet-20240229",
        "api_key_name": "ANTHROPIC_API_KEY"
    },
    "groq": {
        "class": ChatGroq,
        "model": "llama3-8b-8192", # Or other models like mixtral-8x7b-32768
        "api_key_name": "GROQ_API_KEY"
    },
    "google": {
        "class": ChatGoogleGenerativeAI,
        "model": "gemini-pro",
        "api_key_name": "GOOGLE_API_KEY"
    }
}

print(f"--- Attempting to initialize LLM provider: {LLM_PROVIDER} ---")

llm = None
if LLM_PROVIDER in PROVIDER_CONFIG:
    config = PROVIDER_CONFIG[LLM_PROVIDER]
    api_key = os.getenv(config["api_key_name"])

    if not api_key:
        print(f"Warning: API key '{config['api_key_name']}' not found in environment variables for provider '{LLM_PROVIDER}'.")
        # Decide if you want to raise an error or proceed (LangChain might raise its own error)
        # raise ValueError(f"API key '{config['api_key_name']}' not found for provider '{LLM_PROVIDER}'.")
    else:
        try:
            # Initialize the selected LLM
            llm = config["class"](
                model=config["model"],
                temperature=0.3
                # Langchain classes usually pick up the API key from env vars automatically if named correctly,
                # but you could pass it explicitly if needed: api_key=api_key (check specific class docs)
            )
            print(f"--- Successfully initialized LLM with provider: {LLM_PROVIDER}, model: {config['model']} ---")
        except ImportError:
             print(f"Error: Required package for '{LLM_PROVIDER}' not installed.")
             print(f"Please install the necessary package (e.g., pip install langchain-{LLM_PROVIDER})")
             llm = None # Ensure llm remains None if import fails
        except Exception as e:
            print(f"Error initializing LLM provider {LLM_PROVIDER}: {e}")
            llm = None # Ensure llm remains None if initialization fails

else:
    print(f"Error: Unsupported LLM_PROVIDER '{LLM_PROVIDER}' specified in environment variables.")
    print(f"Available providers: {list(PROVIDER_CONFIG.keys())}")
    # Decide if you want to raise an error or default to one (e.g., OpenAI)
    # raise ValueError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}")

# --- Check if LLM Initialization Succeeded ---
if llm is None:
    # Handle the case where no LLM could be initialized
    # Option 1: Raise an error to stop the application
    raise RuntimeError("Failed to initialize any LLM provider. Please check your .env configuration and installed packages.")
    # Option 2: Set a dummy/fallback mechanism (not recommended for core functionality)
    # print("CRITICAL: LLM could not be initialized. Using fallback (not implemented).")


# --- Prompt Templates (Keep these as they are) ---
explain_template = ChatPromptTemplate.from_messages([
    ("system", """You are an expert Python code mentor. Your goal is to explain Python code step-by-step, focusing on the 'why' behind each part, not just the 'what'.
    Be clear, concise, and act like a patient teacher. Break down complex logic.
    If possible, explain based on the structure provided (e.g., function by function, or block by block).
    Explain the overall purpose first, then go into details."""),
    ("human", "Please explain the following Python code:\n\n```python\n{code}\n```")
])

suggest_template = ChatPromptTemplate.from_messages([
    ("system", "You are an expert Python code reviewer. Analyze the following Python code for potential improvements in terms of performance, readability, Pythonic style, and potential edge cases. Provide clear, actionable suggestions."),
    ("human", "Suggest improvements for this Python code:\n\n```python\n{code}\n```")
])

debug_template = ChatPromptTemplate.from_messages([
     ("system", "You are an expert Python debugger. Analyze the following Python code for potential syntax errors, logical flaws, runtime errors, or common pitfalls. Highlight the potential issues and explain why they might be problematic."),
     ("human", "Find potential bugs or issues in this Python code:\n\n```python\n{code}\n```")
 ])

what_if_template = ChatPromptTemplate.from_messages([
    ("system", """You are an expert Python code mentor. The user has provided Python code and a 'what if' question about it.
    1. Briefly explain the potential impact of the user's hypothetical change.
    2. If feasible, provide a modified version of the code reflecting the change.
    3. If the change is problematic or doesn't make sense, explain why."""),
    ("human", "Consider the following Python code:\n\n```python\n{code}\n```\n\nNow, what if: {user_question}")
])


# --- Chains (These will now use the correctly selected 'llm' variable) ---
explain_chain = explain_template | llm | StrOutputParser()
suggest_chain = suggest_template | llm | StrOutputParser()
debug_chain = debug_template | llm | StrOutputParser()
what_if_chain = what_if_template | llm | StrOutputParser()


# --- Service Functions (Keep these as they are) ---
async def get_code_explanation(code: str) -> dict:
    """Gets explanation using LLM."""
    tree = parse_python_code(code)
    if tree is None:
        return {"error": "Syntax error in code, cannot parse."}
    try:
        explanation = await explain_chain.ainvoke({"code": code})
        return {"overall_summary": explanation}
    except Exception as e:
        # Log the error more informatively on the backend
        print(f"LLM Error during explanation for provider {LLM_PROVIDER}: {e}")
        # Return a generic error message to the frontend
        return {"error": f"Failed to get explanation from LLM: An internal error occurred."}

async def get_code_suggestions(code: str) -> dict:
    """Gets improvement suggestions using LLM."""
    try:
        suggestions_text = await suggest_chain.ainvoke({"code": code})
        suggestions_list = [s.strip() for s in suggestions_text.split('\n') if s.strip()]
        return {"suggestions": suggestions_list}
    except Exception as e:
        print(f"LLM Error during suggestions for provider {LLM_PROVIDER}: {e}")
        return {"error": f"Failed to get suggestions from LLM: An internal error occurred."}

async def get_code_debugging_info(code: str) -> dict:
    """Gets debugging help using LLM."""
    try:
        debug_text = await debug_chain.ainvoke({"code": code})
        potential_bugs = [{"issue": line.strip()} for line in debug_text.split('\n') if line.strip()]
        return {"potential_bugs": potential_bugs}
    except Exception as e:
        print(f"LLM Error during debugging for provider {LLM_PROVIDER}: {e}")
        return {"error": f"Failed to get debugging info from LLM: An internal error occurred."}

async def answer_what_if_question(code: str, user_question: str) -> dict:
    """Answers 'what if' questions using LLM."""
    try:
        response_text = await what_if_chain.ainvoke({"code": code, "user_question": user_question})
        return {"explanation": response_text}
    except Exception as e:
        print(f"LLM Error during 'what if' for provider {LLM_PROVIDER}: {e}")
        return {"error": f"Failed to answer 'what if' question: An internal error occurred."}

'''import os
import ast
from langchain_openai import ChatOpenAI # Or other providers
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from dotenv import load_dotenv

from backend.core.code_parser import parse_python_code

load_dotenv() # Load environment variables from .env

# --- LLM Initialization ---
# Choose your LLM provider
# Make sure the corresponding package (e.g., langchain-openai) is installed
# and the API key is in your .env file
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3)
llm = ChatAnthropic(model="claude-3-sonnet-20240229", temperature=0.3)
llm = ChatGroq(model="llama3-8b-8192", temperature=0.3)
llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3)

# --- Prompt Templates ---
explain_template = ChatPromptTemplate.from_messages([
    ("system", """You are an expert Python code mentor. Your goal is to explain Python code step-by-step, focusing on the 'why' behind each part, not just the 'what'.
    Be clear, concise, and act like a patient teacher. Break down complex logic.
    If possible, explain based on the structure provided (e.g., function by function, or block by block).
    Explain the overall purpose first, then go into details."""),
    ("human", "Please explain the following Python code:\n\n```python\n{code}\n```")
])

suggest_template = ChatPromptTemplate.from_messages([
    ("system", "You are an expert Python code reviewer. Analyze the following Python code for potential improvements in terms of performance, readability, Pythonic style, and potential edge cases. Provide clear, actionable suggestions."),
    ("human", "Suggest improvements for this Python code:\n\n```python\n{code}\n```")
])

debug_template = ChatPromptTemplate.from_messages([
     ("system", "You are an expert Python debugger. Analyze the following Python code for potential syntax errors, logical flaws, runtime errors, or common pitfalls. Highlight the potential issues and explain why they might be problematic."),
     ("human", "Find potential bugs or issues in this Python code:\n\n```python\n{code}\n```")
 ])

what_if_template = ChatPromptTemplate.from_messages([
    ("system", """You are an expert Python code mentor. The user has provided Python code and a 'what if' question about it.
    1. Briefly explain the potential impact of the user's hypothetical change.
    2. If feasible, provide a modified version of the code reflecting the change.
    3. If the change is problematic or doesn't make sense, explain why."""),
    ("human", "Consider the following Python code:\n\n```python\n{code}\n```\n\nNow, what if: {user_question}")
])

# --- Chains ---
explain_chain = explain_template | llm | StrOutputParser()
suggest_chain = suggest_template | llm | StrOutputParser()
debug_chain = debug_template | llm | StrOutputParser()
what_if_chain = what_if_template | llm | StrOutputParser()

# --- Service Functions ---
async def get_code_explanation(code: str) -> dict:
    """Gets explanation using LLM."""
    # Basic AST check (can be expanded)
    tree = parse_python_code(code)
    if tree is None:
        return {"error": "Syntax error in code, cannot parse."}

    # Here you could potentially pass AST info into the prompt or use it
    # to guide a more complex line-by-line explanation strategy later.
    # For now, just send the raw code.

    try:
        explanation = await explain_chain.ainvoke({"code": code})
        # Basic parsing of the response (can be improved)
        # This assumes the LLM follows instructions to give an overall summary.
        # Line-by-line requires more sophisticated prompting and parsing or AST mapping.
        return {"overall_summary": explanation}
    except Exception as e:
        print(f"LLM Error: {e}")
        return {"error": f"Failed to get explanation from LLM: {e}"}

async def get_code_suggestions(code: str) -> dict:
    """Gets improvement suggestions using LLM."""
    try:
        suggestions_text = await suggest_chain.ainvoke({"code": code})
        # Simple parsing: split suggestions by newline, assuming LLM lists them.
        suggestions_list = [s.strip() for s in suggestions_text.split('\n') if s.strip()]
        return {"suggestions": suggestions_list}
    except Exception as e:
        print(f"LLM Error: {e}")
        return {"error": f"Failed to get suggestions from LLM: {e}"}

async def get_code_debugging_info(code: str) -> dict:
    """Gets debugging help using LLM."""
    try:
        debug_text = await debug_chain.ainvoke({"code": code})
        # Very basic parsing, ideally the LLM would structure its output better.
        # E.g., ask LLM to format as "Line X: [Issue Description]"
        potential_bugs = [{"issue": line.strip()} for line in debug_text.split('\n') if line.strip()]
        return {"potential_bugs": potential_bugs}
    except Exception as e:
        print(f"LLM Error: {e}")
        return {"error": f"Failed to get debugging info from LLM: {e}"}

async def answer_what_if_question(code: str, user_question: str) -> dict:
    """Answers 'what if' questions using LLM."""
    try:
        response_text = await what_if_chain.ainvoke({"code": code, "user_question": user_question})
        # Simple response, assumes LLM gives a coherent answer.
        # Parsing modified code would require specific instructions to the LLM.
        return {"explanation": response_text}
    except Exception as e:
        print(f"LLM Error: {e}")
        return {"error": f"Failed to answer 'what if' question: {e}"}'''