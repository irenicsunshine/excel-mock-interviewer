"""
Streamlit frontend for Excel Mock Interviewer
"""
import streamlit as st
import requests
import json
import time
from typing import Dict, Any
import os

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

def init_session_state():
    """Initialize session state variables"""
    if "interview_id" not in st.session_state:
        st.session_state.interview_id = None
    if "current_question" not in st.session_state:
        st.session_state.current_question = None
    if "interview_status" not in st.session_state:
        st.session_state.interview_status = "not_started"
    if "progress" not in st.session_state:
        st.session_state.progress = {"current": 0, "total": 6}

def create_interview(candidate_name: str, role: str, difficulty: str) -> Dict[str, Any]:
    """Create a new interview session"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/interviews",
            json={
                "candidate_name": candidate_name,
                "role": role,
                "difficulty": difficulty
            },
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to create interview: {response.text}")
            return {}
            
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        return {}

def get_next_question(interview_id: str) -> Dict[str, Any]:
    """Get the next question or completion status"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/interviews/{interview_id}/next",
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to get next question: {response.text}")
            return {}
            
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        return {}

def submit_answer(interview_id: str, answer_text: str, uploaded_file=None) -> Dict[str, Any]:
    """Submit an answer with optional file"""
    try:
        files = {}
        if uploaded_file is not None:
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        
        data = {"answer_text": answer_text}
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/interviews/{interview_id}/answer",
            data=data,
            files=files,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to submit answer: {response.text}")
            return {}
            
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        return {}

def get_report(interview_id: str, format_type: str = "html") -> str:
    """Get the final report"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/interviews/{interview_id}/report",
            params={"format": format_type},
            timeout=30
        )
        
        if response.status_code == 200:
            if format_type == "html":
                return response.text
            else:
                return response.content
        else:
            st.error(f"Failed to get report: {response.text}")
            return ""
            
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        return ""

def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="Excel Mock Interviewer",
        page_icon="📊",
        layout="wide"
    )
    
    init_session_state()
    
    st.title("📊 Excel Mock Interviewer")
    st.markdown("---")
    
    # Sidebar with progress
    with st.sidebar:
        st.header("Interview Progress")
        if st.session_state.interview_status != "not_started":
            progress = st.session_state.progress
            st.progress(progress["current"] / progress["total"])
            st.write(f"Question {progress['current']} of {progress['total']}")
        
        st.markdown("---")
        st.markdown("### Instructions")
        st.markdown("""
        1. **Answer each question** clearly and completely
        2. **Upload Excel files** when requested
        3. **Take your time** - quality over speed
        4. **Be specific** in your explanations
        """)
    
    # Main content area
    if st.session_state.interview_status == "not_started":
        show_welcome_screen()
    elif st.session_state.interview_status == "active":
        show_interview_screen()
    elif st.session_state.interview_status == "completed":
        show_report_screen()

def show_welcome_screen():
    """Display welcome and setup screen"""
    st.header("Welcome to Your Excel Interview! 🎯")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        This AI-powered interview will assess your Excel skills through:
        - **Practical exercises** with real Excel files
        - **Formula and function** questions
        - **Data analysis** scenarios
        - **Best practices** discussions
        
        The interview adapts to your responses and provides detailed feedback.
        """)
        
        with st.form("interview_setup"):
            st.subheader("Interview Setup")
            
            candidate_name = st.text_input("Your Name", placeholder="Enter your full name")
            
            role = st.selectbox(
                "Role Focus",
                ["finance", "data", "ops"],
                format_func=lambda x: {
                    "finance": "Finance & Accounting",
                    "data": "Data Analysis",
                    "ops": "Operations & Business"
                }[x]
            )
            
            difficulty = st.selectbox(
                "Difficulty Level",
                ["medium", "basic", "advanced"],
                format_func=lambda x: x.title()
            )
            
            submitted = st.form_submit_button("Start Interview", use_container_width=True)
            
            if submitted:
                if not candidate_name.strip():
                    st.error("Please enter your name")
                else:
                    with st.spinner("Setting up your interview..."):
                        result = create_interview(candidate_name, role, difficulty)
                        
                        if result:
                            st.session_state.interview_id = result["interview_id"]
                            st.session_state.current_question = result["first_question"]
                            st.session_state.interview_status = "active"
                            st.session_state.progress = {"current": 1, "total": 6}
                            st.rerun()
    
    with col2:
        st.info("""
        **💡 Tips for Success:**
        
        - Read questions carefully
        - Explain your reasoning
        - Use proper Excel terminology
        - Upload clean, organized files
        - Ask for clarification if needed
        """)

def show_interview_screen():
    """Display current question and answer interface"""
    if not st.session_state.current_question:
        # Try to get next question
        next_data = get_next_question(st.session_state.interview_id)
        if next_data.get("status") == "completed":
            st.session_state.interview_status = "completed"
            st.rerun()
        elif "question" in next_data:
            st.session_state.current_question = next_data["question"]
            if "progress" in next_data:
                st.session_state.progress = next_data["progress"]
        else:
            st.error("Failed to load question. Please refresh the page.")
            return
    
    question = st.session_state.current_question
    
    # Question display
    st.header(f"Question {st.session_state.progress['current']}")
    
    # Question type badge
    question_type = question.get("type", "unknown").title()
    if question_type == "Formula":
        st.markdown("🧮 **Formula Question**")
    elif question_type == "Practical":
        st.markdown("📊 **Practical Exercise**")
    elif question_type == "Mcq":
        st.markdown("❓ **Multiple Choice**")
    else:
        st.markdown("💬 **Explanation Question**")
    
    # Timer display
    time_limit = question.get("time_limit", 300)
    st.info(f"⏰ Recommended time: {time_limit // 60} minutes")
    
    # Question text
    st.markdown("### Question:")
    st.markdown(question["text"])
    
    st.markdown("---")
    
    # Answer form
    with st.form("answer_form"):
        st.subheader("Your Answer")
        
        answer_text = st.text_area(
            "Enter your answer:",
            height=200,
            placeholder="Provide a detailed answer explaining your approach..."
        )
        
        uploaded_file = None
        if question["type"] in ["practical", "formula"]:
            uploaded_file = st.file_uploader(
                "Upload Excel file (optional):",
                type=["xlsx", "xlsm", "xls"],
                help="Upload your Excel workbook if the question requires it"
            )
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            submit_button = st.form_submit_button("Submit Answer", use_container_width=True)
        
        with col2:
            if st.form_submit_button("Need Clarification", use_container_width=True):
                st.info("💡 **Need help?** Re-read the question carefully. If still unclear, provide your best answer and mention what you're unsure about.")
        
        if submit_button:
            if not answer_text.strip():
                st.error("Please provide an answer before submitting")
            else:
                with st.spinner("Submitting your answer..."):
                    result = submit_answer(
                        st.session_state.interview_id,
                        answer_text,
                        uploaded_file
                    )
                    
                    if result.get("evaluation_pending"):
                        st.success("Answer submitted! Processing evaluation...")
                        time.sleep(2)  # Brief pause for user feedback
                        
                        # Clear current question to trigger next question load
                        st.session_state.current_question = None
                        st.rerun()

def show_report_screen():
    """Display final interview report"""
    st.header("📋 Interview Complete!")
    st.success("Congratulations! You've completed all questions.")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("View Report", use_container_width=True):
            with st.spinner("Generating your detailed report..."):
                report_html = get_report(st.session_state.interview_id, "html")
                
                if report_html:
                    st.markdown("---")
                    st.components.v1.html(report_html, height=800, scrolling=True)
    
    with col2:
        if st.button("Download PDF Report", use_container_width=True):
            with st.spinner("Generating PDF..."):
                pdf_content = get_report(st.session_state.interview_id, "pdf")
                
                if pdf_content:
                    st.download_button(
                        label="📄 Download PDF",
                        data=pdf_content,
                        file_name=f"interview_report_{st.session_state.interview_id}.pdf",
                        mime="application/pdf"
                    )
    
    st.markdown("---")
    if st.button("Start New Interview", use_container_width=True):
        # Reset session state
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

if __name__ == "__main__":
    main()
