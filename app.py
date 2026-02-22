import streamlit as st
import os
from openai import OpenAI
from tavily import TavilyClient
from dotenv import load_dotenv
import PyPDF2

# Load environment variables
load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

st.set_page_config(page_title="AI Career Intelligence Agent")
st.title("🚀 AI Career Intelligence Agent")

st.write("Upload your resume and discover best matching jobs at any company.")

# Inputs
company = st.text_input("Company Name (Required)")
role = st.text_input("Target Role (Optional)")
location = st.text_input("Preferred Location (Optional)")
resume_file = st.file_uploader("Upload Resume (PDF only)", type=["pdf"])


# -----------------------------
# PDF Extraction
# -----------------------------
def extract_text_from_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text
    return text


# -----------------------------
# Fetch Real Job Links
# -----------------------------
def fetch_job_postings(company, role=None, location=None):

    query = f"{company} careers job opening apply"

    if role:
        query += f" {role}"
    if location:
        query += f" {location}"

    response = tavily_client.search(
        query=query,
        search_depth="advanced",
        max_results=10
    )

    jobs = []

    for result in response.get("results", []):
        url = result.get("url", "")
        title = result.get("title", "")
        content = result.get("content", "")

        url_lower = url.lower()

        # Filter: must contain job-like keywords
        if any(keyword in url_lower for keyword in [
            "job", "position", "opening", "apply", "requisition"
        ]):

            # Avoid generic careers homepage
            if not url_lower.rstrip("/").endswith("careers"):

                jobs.append({
                    "title": title,
                    "url": url,
                    "description": content[:500]
                })

        if len(jobs) >= 5:
            break

    return jobs


# -----------------------------
# Main Button Logic
# -----------------------------
if st.button("Find Jobs"):

    if not company:
        st.warning("Please enter a company name.")
        st.stop()

    if not resume_file:
        st.warning("Please upload your resume.")
        st.stop()

    try:
        st.write("📄 Extracting resume...")
        resume_text = extract_text_from_pdf(resume_file)

        st.write("🔎 Searching for real job postings...")
        jobs = fetch_job_postings(company, role, location)

        if not jobs:
            st.error("Could not find specific job postings.")
            st.stop()

        st.success("🧠 Matching jobs with your resume...")

        job_data_for_ai = "\n\n".join(
            [
                f"Title: {job['title']}\nLink: {job['url']}\nDescription: {job['description']}"
                for job in jobs
            ]
        )

        ai_prompt = f"""
You are an expert career intelligence AI.

Company: {company}
Target Role: {role if role else "Not specified"}
Preferred Location: {location if location else "Not specified"}

========================
CANDIDATE RESUME
========================
{resume_text}

========================
JOB POSTINGS
========================
{job_data_for_ai}

Your Tasks:

STEP 1 — Resume Analysis
- Provide a short professional summary of the candidate.
- Extract key technical skills.
- Identify strengths.
- Identify possible skill gaps relative to target role (if specified).

STEP 2 — Job Matching
- Compare resume skills against each job posting.
- Rank the top 5 best matches.

For each matched job provide:
- Job Title
- Why it matches the candidate
- Location (if mentioned)
- Match Score (1-10)
- Direct Apply Link (use EXACT link provided above)

Structure your response clearly using headings.
Be professional and concise.
"""

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": ai_prompt}],
            temperature=0.3,
        )

        st.markdown(response.choices[0].message.content)

    except Exception as e:
        st.error(f"Error: {str(e)}")