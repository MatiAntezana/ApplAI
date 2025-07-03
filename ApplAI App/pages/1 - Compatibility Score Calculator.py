import os
import streamlit as st
import os
from PIL import Image
import base64
from dotenv import load_dotenv

from scripts.text_extraction.text_extractor_for_files import scrape_files
from scripts.text_extraction.text_extractor_for_general_webs import scrape_web
from scripts.text_extraction.text_extractor_for_linkedin_profiles import scrape_linkedin_profile
from scripts.text_extraction.text_extractor_for_linkedin_jobs import scrape_linkedin_job
from scripts.api_call.api_call_for_format_and_fe import get_applicant_information, get_job_description
from scripts.models.model import calculate_score    

# Load environment variables
load_dotenv()

# Configure Streamlit app
st.set_page_config(page_title="ApplAI - Compatibility Score Calculator", page_icon="📊", layout="centered")

st.markdown(
    """
    <h1 style='text-align: center;'>
        Score your Applicant Information based on a Job Description
    </h1>
    """,
    unsafe_allow_html=True
)

st.markdown("<br>", unsafe_allow_html=True)

# Set the title and header
st.markdown(
    """
    <div style='text-align: center;'>
        <img src="data:image/png;base64,{}" width="300">
    </div>
    """.format(
        base64.b64encode(open("imgs/puntuacion_logo.png", "rb").read()).decode()
    ),
    unsafe_allow_html=True
)

st.markdown(""" <br>*Calculate your **compatibility score** between your **experience, skills and achievements** and the description of a **job** 
            you would like to apply for using **AI**. Share your **profile** (LinkedIn, resume, or portfolio) and the **job ad**. We'll instantly analyze **how well you match the role**.*""", unsafe_allow_html=True)

st.markdown("", unsafe_allow_html=True)

st.subheader("Applicant Information Input")
ai_url_linkedin = st.text_input("LinkedIn Profile URL")
ai_url_web = st.text_input("Personal Website URL")
ai_file = st.file_uploader("Upload AI File (CV, Cover Letter, Certificate, etc)", type=["pdf", "docx", "txt", "pptx", "jpg", "png", "csv", "json"], accept_multiple_files=False)

st.markdown("<br>", unsafe_allow_html=True)

st.subheader("Job Description Input")
job_url_linkedin = st.text_input("Job Posting from LinkedIn URL")
job_url_web = st.text_input("Job Posting from a Website URL")
job_file = st.file_uploader("Upload Job Description File", type=["pdf", "docx", "txt", "pptx", "jpg", "png", "csv", "json"], accept_multiple_files=False)

cv_ready = (ai_url_linkedin.strip() != "") or (ai_url_web.strip() != "") or (ai_file is not None)
job_ready = (job_url_linkedin.strip() != "") or (job_url_web.strip() != "") or (job_file is not None)

st.markdown("<br>", unsafe_allow_html=True)

# Estilo del botón
st.markdown("""
    <style>
    div.stButton > button {
        display: block;
        margin: 0 auto;
        background-color: #4CAF50;
        color: white;
        border-radius: 12px;
        padding: 0.75em 2em;
        font-size: 18px;
        font-weight: bold;
        border: none;
    }
    </style>
""", unsafe_allow_html=True)

if st.button("Calculate Score", type="primary"):
    if not (cv_ready and job_ready):
        st.error("Please provide both a CV and a job posting (URL or file).")
    else:
        with st.spinner("Processing..."):
            try:
                os.makedirs("temp_files", exist_ok=True)

                # Process Applicant Information
                if ai_url_linkedin.strip() != "":
                    scrape_linkedin_profile(ai_url_linkedin, "temp_files/ai.txt")
                
                elif ai_url_web.strip() != "":
                    scrape_web(ai_url_web, "temp_files/ai.txt")
                
                elif ai_file: 
                    ai_path = os.path.join("temp_files", ai_file.name)
                    with open(ai_path, "wb") as f:
                        f.write(ai_file.getbuffer())
                    scrape_files(ai_path, "temp_files/ai.txt")
                   
                # Process Job Description
                if job_url_linkedin.strip() != "":
                    scrape_linkedin_job(job_url_linkedin, "temp_files/job.txt")
                
                elif job_url_web.strip() != "":
                    scrape_web(job_url_web, "temp_files/job.txt")
                
                elif job_file:
                    job_path = os.path.join("temp_files", job_file.name)
                    with open(job_path, "wb") as f:
                        f.write(job_file.getbuffer())
                    scrape_files(job_path, "temp_files/job.txt")

                # Call API to process the applicant information and job description
                ai_model_input = get_applicant_information("temp_files/ai.txt")
                job_model_input = get_job_description("temp_files/job.txt")

                # Calculate the compatibility score
                score = calculate_score(ai_model_input, job_model_input).item()
                
                # Display the compatibility score
                st.success(f"Compatibility Score: {(score * 100):.2f}%")

                # Delete all temporary files
                for file in os.listdir("temp_files"):
                    file_path = os.path.join("temp_files", file)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                    except Exception as e:
                        st.error(f"Error deleting file {file}: {str(e)}")

            except Exception as e:
                st.error(str(e))

# Footer
st.markdown("---")
st.markdown("© 2025 ApplAI. All rights reserved.")


