import streamlit as st
import requests
import json

# --- Configuration ---
st.set_page_config(layout="wide", page_title="AI Code Mentor")
BACKEND_URL = "http://localhost:8000" # Make sure this matches your FastAPI backend address

# --- Helper Function to Call Backend ---
def call_api(endpoint: str, code: str, question: str = None):
    """Calls the backend API."""
    url = f"{BACKEND_URL}/{endpoint}"
    payload = {"code": code}
    if question:
        payload["user_question"] = question

    try:
        response = requests.post(url, json=payload, timeout=60) # Increased timeout for LLM calls
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {e}")
        try:
            # Try to parse error details from response if available
            error_detail = response.json().get("detail", "No details available.")
            st.error(f"Backend Error: {error_detail}")
        except Exception:
            st.error("Could not retrieve error details from the backend.")
        return None
    except json.JSONDecodeError:
        st.error("Failed to decode API response. Received:")
        st.text(response.text)
        return None

# --- Streamlit UI ---
st.title("🤖 AI-Powered Code Mentor")
st.write("Get Help Understanding, Improving, and Debugging And Converting your Code.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Enter Your Code")
    code_input = st.text_area("Paste your Python code here:", height=400, key="code_input", placeholder="def example(n):\n    # ...")

    st.subheader("Ask 'What If'")
    what_if_question = st.text_input("Ask a hypothetical question about the code:", key="what_if_question", placeholder="What if I changed the loop condition?")

    action = st.selectbox(
        "Choose an action:",
        ("Explain Code", "Suggest Improvements", "Debug Code", "Answer 'What Is Ask'"),
        key="action_select"
    )

    submit_button = st.button("Analyze Code", type="primary")

with col2:
    st.subheader("Analysis Result")
    result_placeholder = st.empty() # Use a placeholder for dynamic content

    if submit_button and code_input:
        with st.spinner("Analyzing code... Please wait."):
            result = None
            if action == "Explain Code":
                result = call_api("explain", code_input)
                if result:
                    result_placeholder.markdown("### Explanation:")
                    if result.get("overall_summary"):
                         result_placeholder.markdown(result["overall_summary"])
                    # TODO: Add display for line-by-line if implemented
                    else:
                        result_placeholder.warning("No explanation received.")

            elif action == "Suggest Improvements":
                result = call_api("suggest", code_input)
                if result and result.get("suggestions"):
                    result_placeholder.markdown("### Suggestions:")
                    for suggestion in result["suggestions"]:
                        result_placeholder.markdown(f"- {suggestion}")
                elif result:
                    result_placeholder.warning("No suggestions received or an error occurred.")


            elif action == "Debug Code":
                result = call_api("debug", code_input)
                if result and result.get("potential_bugs"):
                    result_placeholder.markdown("### Potential Bugs / Issues:")
                    for bug in result["potential_bugs"]:
                         # Adjust based on actual debug response structure
                        issue = bug.get('issue', 'Unknown issue')
                        line = bug.get('line', 'N/A')
                        result_placeholder.markdown(f"- **Line {line}:** {issue}")
                elif result:
                   result_placeholder.warning("No debugging info received or an error occurred.")


            elif action == "Answer 'What If'":
                if what_if_question:
                    result = call_api("whatif", code_input, question=what_if_question)
                    if result:
                         result_placeholder.markdown("### 'What If' Analysis:")
                         if result.get("explanation"):
                             result_placeholder.markdown(result["explanation"])
                         if result.get("modified_code"):
                             result_placeholder.markdown("\n**Modified Code:**")
                             result_placeholder.code(result["modified_code"], language="python")
                         elif not result.get("explanation"):
                            result_placeholder.warning("No response received for 'What If' scenario.")

                else:
                    st.warning("Please enter a 'What If' question.")

            if result and result.get("error"):
                # Error was already displayed by call_api, but we can add context
                result_placeholder.error(f"Error during '{action}': {result.get('error')}")
            elif not result and not (action == "Answer 'What If'" and not what_if_question):
                 # Handles cases where call_api returned None due to request errors
                result_placeholder.error("Failed to get analysis from the backend.")


    elif submit_button and not code_input:
        st.warning("Please enter some code to analyze.")
    else:
        result_placeholder.info("Enter code and select an action to see the analysis here.")