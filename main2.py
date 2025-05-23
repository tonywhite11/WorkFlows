import os
import streamlit as st
from openai import OpenAI
import tempfile
import re
import markdown2
import pdfkit

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

def create_pdf(text, goal_summary, goal):
    html_content = f"""
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ text-align: center; color: #1976d2; }}
        h2 {{ color: #1976d2; }}
        ul, ol {{ margin-left: 20px; }}
        a {{ color: #1976d2; text-decoration: underline; }}
        strong {{ color: #333; }}
        .goal-summary {{ font-size: 1.1em; margin-bottom: 20px; }}
    </style>
    </head>
    <body>
    <h1>WorkFlows Project Plan</h1>
    <div class="goal-summary"><strong>Goal:</strong> {goal_summary}</div>
    {markdown2.markdown(text)}
    </body>
    </html>
    """
    safe_goal = re.sub(r'[^a-zA-Z0-9_]', '_', goal.lower()).strip('_')
    safe_goal = '_'.join(safe_goal.split())[:30]
    filename = f"workflow_{safe_goal}.pdf"
    temp_path = os.path.join(tempfile.gettempdir(), filename)
    # You may need to specify configuration if wkhtmltopdf is not in PATH
    pdfkit.from_string(html_content, temp_path)
    return temp_path

def summarize_goal(goal):
    summary_prompt = f"Summarize this goal in one concise sentence: {goal}"
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
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
        st.rerun()  # <-- Must be inside the if block!