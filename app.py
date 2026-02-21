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

def extract_text_from_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

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

        search_query = f"{company} {role if role else ''} jobs {location if location else ''} careers site:{company.lower()}.com"

        search_result = tavily_client.search(
            query=search_query,
            search_depth="advanced",
            max_results=5
        )

        if not search_result["results"]:
            st.error("Could not find job postings.")
            st.stop()

        job_links = [result["url"] for result in search_result["results"]]

        st.success("🧠 Matching jobs with your resume...")

        ai_prompt = f"""
You are an expert job matching AI.

Company: {company}
Target Role: {role if role else "Not specified"}
Preferred Location: {location if location else "Not specified"}

Candidate Resume:
{resume_text}

Job Links:
{job_links}

Your Tasks:

1. Analyze resume skills.
2. Analyze likely job roles from links.
3. Rank top 5 best matches.
4. For each job:
   - Job Title
   - Why it's a match
   - Location (if inferable)
   - Match Score (1-10)
   - Direct Apply Link (use exact link from list)

Be structured and concise.
"""

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": ai_prompt}],
            temperature=0.3,
        )

        st.markdown(response.choices[0].message.content)

    except Exception as e:
        st.error(f"Error: {str(e)}")