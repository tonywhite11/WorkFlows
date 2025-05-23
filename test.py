import os
import streamlit as st
from openai import OpenAI
from fpdf import FPDF
import tempfile
from datetime import datetime
import re

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

roles_prompt = {
    "Generalist": "",
    "Developer": "You are a senior software engineer.",
    "Designer": "You are a UI/UX designer.",
    "Marketer": "You are a digital marketing strategist.",
    "Coach": "You are a productivity coach.",
    "Entrepreneur": "You are a startup founder and business strategist.",
    "Student": "You are an academic advisor helping students succeed.",
    "Researcher": "You are a scientific researcher and project planner.",
    "Content Creator": "You are a professional content creator and social media strategist.",
    "Event Planner": "You are an experienced event planner.",
    "HR Specialist": "You are a human resources specialist.",
    "Teacher": "You are an experienced teacher and curriculum designer.",
    "Consultant": "You are a business consultant.",
    "Healthcare Professional": "You are a healthcare project manager.",
    "Engineer": "You are a project engineer.",
    "Writer": "You are a professional writer and editor.",
    "Salesperson": "You are a sales strategist.",
    "Financial Advisor": "You are a financial advisor and planner."
}

def clean_text(text):
    return text.encode("latin-1", errors="replace").decode("latin-1")

def create_pdf(text, goal_summary, goal):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)

    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "WorkFlows Project Plan", ln=True, align='C')
    pdf.ln(10)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"Goal: {clean_text(goal_summary)}", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", size=12)
    for line in clean_text(text).split("\n"):
        if line.strip() == "":
            pdf.ln(3)
        else:
            pdf.multi_cell(0, 8, line, align='L')  # Use full width, left-aligned

    safe_goal = re.sub(r'[^a-zA-Z0-9_]', '_', goal.lower()).strip('_')
    safe_goal = '_'.join(safe_goal.split())[:30]
    filename = f"workflow_{safe_goal}.pdf"
    temp_path = os.path.join(tempfile.gettempdir(), filename)
    pdf.output(temp_path)
    return temp_path

def summarize_goal(goal):
    summary_prompt = f"Summarize this goal in one concise sentence: {goal}"
    response = client.chat.completions.create(
        model="gpt-4.1-2025-04-14",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": summary_prompt}
        ]
    )
    return response.choices[0].message.content.strip()

def generate_workflow(goal, role, region=None):
    region_str = f" The user is located in {region}." if region else ""
    prompt = f"""
    {roles_prompt[role]}
    Help a user who wants to: {goal}
    {region_str}
    Break it down into a clear, actionable workflow.
    For each step, include:
    - **Action**: Describe the main action/task for this step.
    - **Tools**: List the recommended tools as Markdown hyperlinks to their official websites (e.g., [Trello](https://trello.com/)).
    - **Time Estimate**
    - **Estimated Cost** (in USD, based on typical prices and, if possible, the user's region)
    - **Alternative**: One alternative method per step.
    Format it in a numbered list, and use bold section headers (Action, Tools, etc.) for each step.
    At the end, provide a total estimated cost for the entire project.
    Only use official, safe, and running websites for tool links.
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an expert project planner."},
            {"role": "user", "content": prompt}
        ]
    )
    workflow = response.choices[0].message.content
    goal_summary = summarize_goal(goal)
    return workflow, goal_summary

st.set_page_config(page_title="WorkFlows", layout="wide")
st.title("🛠️ WorkFlows: Turn Ideas Into Action")

if "workflow" not in st.session_state:
    st.session_state.workflow = None
    st.session_state.goal_summary = None
    st.session_state.goal = ""
    st.session_state.role = ""
    st.session_state.region = ""

goal = st.text_area("What's your goal?", value=st.session_state.goal, placeholder="e.g., Launch an Etsy store")
role = st.selectbox("Select Role", list(roles_prompt.keys()), index=0)
region = st.text_input("Your location or region (optional)", value=st.session_state.region, placeholder="e.g., United States, UK, India")

if st.button("🚀 Generate Workflow") and goal:
    with st.spinner("Generating workflow..."):
        workflow, goal_summary = generate_workflow(goal, role, region)
        st.session_state.workflow = workflow
        st.session_state.goal_summary = goal_summary
        st.session_state.goal = goal
        st.session_state.role = role
        st.session_state.region = region

def add_double_space_before_headers(text):
    headers = ["Action:", "Tools:", "Time Estimate:", "Estimated Cost:", "Alternative:"]
    for header in headers:
        text = re.sub(rf"([^\n])\n{header}", rf"\1\n\n{header}", text)
        text = re.sub(rf"([^\n])({header})", rf"\1\n\n\2", text)
    return text and open

if st.session_state.workflow:
    st.markdown("### 🖥️ Preview")
    st.markdown(st.session_state.workflow, unsafe_allow_html=True)
    pdf_file = create_pdf(st.session_state.workflow, st.session_state.goal_summary, st.session_state.goal)
    with open(pdf_file, "rb") as f:
        st.download_button("📄 Download PDF", f, file_name=os.path.basename(pdf_file), mime="application/pdf")
    if st.button("Reset"):
        for key in ["workflow", "goal_summary", "goal", "role", "region"]:
            st.session_state[key] = ""
        st.rerun()