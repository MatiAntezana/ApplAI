import streamlit as st
import os
from PIL import Image
import base64
from utils import process_ai, process_job
from coso_modified import calculate_score
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de la página
st.set_page_config(page_title="ApplAI", page_icon="💼", layout="centered")

st.markdown(
    """
    <div style='text-align: center;'>
        <img src="data:image/png;base64,{}" width="300">
    </div>
    """.format(
        base64.b64encode(open("ApplAI logo.png", "rb").read()).decode()
    ),
    unsafe_allow_html=True
)


st.markdown(""" <br>*Calculate your **compatibility score** between a CV and a job posting using AI.
                    Provide a LinkedIn profile URL or upload a CV file, and a job posting URL or file.*""", unsafe_allow_html=True)

st.markdown("", unsafe_allow_html=True)

# --- Inputs ---

st.subheader("CV Input")
cv_url_linkedin = st.text_input("LinkedIn Profile URL")
cv_url = st.text_input("CV URL from a Website")
cv_file = st.file_uploader("Upload CV (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"], disabled=bool(cv_url_linkedin.strip()))

st.markdown("<br>", unsafe_allow_html=True)

st.subheader("Job Posting Input")
job_url_linkedin = st.text_input("Job Posting URL from LinkedIn")
job_url = st.text_input("Job Posting URL from a Website")
job_file = st.file_uploader("Upload Job Posting (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"], disabled=bool(job_url_linkedin.strip()))

# --- Botón ---

cv_ready = (cv_url_linkedin.strip() != "") or (cv_file is not None)
job_ready = (job_url_linkedin.strip() != "") or (job_file is not None)

st.markdown("<br>", unsafe_allow_html=True)

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

                # Procesar CV
                cv_text = ""
                if cv_url_linkedin.strip() != "":
                    cv_text = process_ai(cv_url_linkedin, "temp_files/cv.txt")
                elif cv_file:
                    cv_path = os.path.join("temp_files", cv_file.name)
                    with open(cv_path, "wb") as f:
                        f.write(cv_file.read())
                    cv_text = process_ai(cv_path, "temp_files/cv.txt")

                # Procesar oferta de trabajo
                job_text = ""
                if job_url_linkedin.strip() != "":
                    job_text = process_job(job_url_linkedin, "temp_files/job.txt")
                elif job_file:
                    job_path = os.path.join("temp_files", job_file.name)
                    with open(job_path, "wb") as f:
                        f.write(job_file.read())
                    job_text = process_job(job_path, "temp_files/job.txt")

                # Calcular score
                if cv_text and job_text:
                    score = calculate_score(cv_text, job_text)
                    st.success(f"Compatibility Score: {(score * 100):.2f}%")
                else:
                    st.error("Failed to process CV or job posting.")

            except Exception as e:
                st.error(f"Error: {str(e)}")

# Footer
st.markdown("---")
st.markdown("© 2025 ApplAI. All rights reserved.")

