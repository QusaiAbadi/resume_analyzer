import streamlit as st
import fitz  # PyMuPDF
import spacy
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    import subprocess
    import sys
    subprocess.run([sys.executable, "-m", "pip", "install", "en-core-web-sm", "--user"])
    nlp = spacy.load("en_core_web_sm")
import re
from difflib import SequenceMatcher

nlp = spacy.load("en_core_web_sm")

# --- Helper Functions ---
def extract_text_from_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_sections(text):
    sections = {
        "Objective": re.findall(r"(?i)(Objective.*?)Skills", text, re.DOTALL),
        "Skills": re.findall(r"(?i)(Skills.*?)Professional Experience", text, re.DOTALL),
        "Experience": re.findall(r"(?i)(Professional Experience.*?)Education", text, re.DOTALL),
        "Education": re.findall(r"(?i)(Education.*?)Certifications", text, re.DOTALL),
        "Certifications": re.findall(r"(?i)(Certifications.*?)CORE COMPETENCIES", text, re.DOTALL),
        "Competencies": re.findall(r"(?i)(CORE COMPETENCIES.*?)$", text, re.DOTALL)
    }
    return {k: v[0].strip() if v else "Not found" for k, v in sections.items()}

def extract_keywords(text):
    doc = nlp(text)
    keywords = set()
    for chunk in doc.noun_chunks:
        if len(chunk.text) > 2:
            keywords.add(chunk.text.strip().lower())
    return keywords

def match_score(resume_keywords, job_keywords):
    matches = sum(1 for word in job_keywords if any(SequenceMatcher(None, word, rkw).ratio() > 0.8 for rkw in resume_keywords))
    score = int((matches / len(job_keywords)) * 100) if job_keywords else 0
    return score, matches, len(job_keywords)

# --- Streamlit UI ---
st.title("📄 Resume Analyzer")
st.write("Upload your resume and compare it to a job description.")

resume_file = st.file_uploader("Upload Your Resume (PDF)", type=["pdf"])
job_description = st.text_area("Paste the Job Description")

if resume_file and job_description:
    with st.spinner("Analyzing resume..."):
        resume_text = extract_text_from_pdf(resume_file)
        sections = extract_sections(resume_text)
        resume_keywords = extract_keywords(resume_text)
        job_keywords = extract_keywords(job_description)

        score, matched, total = match_score(resume_keywords, job_keywords)

        st.subheader("📊 Match Score")
        st.metric(label="Match Score", value=f"{score}%")
        st.write(f"{matched} of {total} job keywords matched.")

        st.subheader("📌 Missing Keywords")
        missing = [word for word in job_keywords if not any(SequenceMatcher(None, word, rkw).ratio() > 0.8 for rkw in resume_keywords)]
        st.write(", ".join(missing) if missing else "None – great match!")

        st.subheader("🧾 Resume Sections")
        for section, content in sections.items():
            with st.expander(section):
                st.write(content)
	
