import os
import gradio as gr
from openai import OpenAI
from fpdf import FPDF
import tempfile
from datetime import datetime

# Initialize OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Roles
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

# PDF generator
def clean_text(text):
    return text.encode("latin-1", errors="replace").decode("latin-1")

def create_pdf(text, goal_summary, goal):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "WorkFlows Project Plan", ln=True, align='C')
    pdf.ln(10)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"Goal: {clean_text(goal_summary)}", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", size=12)
    for line in clean_text(text).split("\n"):
        pdf.multi_cell(0, 10, line)

    # Use the original goal for the filename, cleaned up
    import re
    safe_goal = re.sub(r'[^a-zA-Z0-9_]', '_', goal.lower()).strip('_')
    safe_goal = '_'.join(safe_goal.split())[:30]
    filename = f"workflow_{safe_goal}.pdf"

    temp_path = os.path.join(tempfile.gettempdir(), filename)
    pdf.output(temp_path)
    return temp_path

# Summarize the goal using OpenAI
def summarize_goal(goal):
    summary_prompt = f"Summarize this goal in one concise sentence: {goal}"
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": summary_prompt}
        ]
    )
    return response.choices[0].message.content.strip()

# Workflow generator
def generate_workflow(goal, role):
    prompt = f"""
    {roles_prompt[role]}
    Help a user who wants to: {goal}
    Break it down into a clear, actionable workflow.
    Include tools, time estimates, and one alternative method per step.
    Format it in a numbered list.
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
    pdf_file = create_pdf(workflow, goal_summary, goal)
    return workflow, pdf_file

# Gradio UI
with gr.Blocks() as demo:
    gr.Markdown("## 🛠️ WorkFlows: Turn Ideas into Action")

    goal_input = gr.Textbox(label="What's your goal?", placeholder="e.g., Launch an Etsy store")
    role_dropdown = gr.Dropdown(choices=list(roles_prompt.keys()), label="Select Role", value="Generalist")
    generate_btn = gr.Button("🚀 Generate Workflow")

    output_text = gr.Textbox(label="📋 Preview Workflow", lines=20)
    download_link = gr.File(label="📄 Download PDF")

    generate_btn.click(
        fn=generate_workflow,
        inputs=[goal_input, role_dropdown],
        outputs=[output_text, download_link]
    )

demo.launch()