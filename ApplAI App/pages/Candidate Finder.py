import streamlit as st
import os
from PIL import Image
import base64
from utils import process_ai, process_job
from coso_modified import calculate_score
from dotenv import load_dotenv
import sys

# Agrega el path del proyecto raíz (donde está la carpeta "rag")
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from rag.select_candidates_and_opinions import get_cvs_and_recomendations

# Cargar variables de entorno
load_dotenv()

# Configuración de la página
st.set_page_config(page_title="ApplAI - Score CV", page_icon="📄", layout="centered")

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

st.header("Find your perfect candidate with ApplAI!")

st.markdown(""" <br>*Find the best candidates from uor database using AI.
                    Provide a job posting URL or upload a job posting file.*""", unsafe_allow_html=True)

st.markdown("", unsafe_allow_html=True)

# --- Inputs ---
st.subheader("Job Posting Input")
job_url_linkedin = st.text_input("Job Posting URL from LinkedIn")
job_url = st.text_input("Job Posting URL from a Website")
job_file = st.file_uploader("Upload Job Posting (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"], disabled=bool(job_url_linkedin.strip()))

st.subheader("Number of candidates to return")
top_k = st.number_input("How many candidates would you like to retrieve?", min_value=1, max_value=15, value=3, step=1)

# --- Botón ---
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

if st.button("Find!", type="primary"):
    if not job_file and job_url_linkedin.strip() == "" and job_url.strip() == "":
        st.error("Please provide a job posting (URL or file).")
    else:
        with st.spinner("Processing job description and retrieving candidates..."):
            try:
                os.makedirs("temp_files", exist_ok=True)

                # Procesar job description
                job_text = ""
                if job_url_linkedin.strip():
                    job_text = process_job(job_url_linkedin, "temp_files/job.txt")
                elif job_url.strip():
                    job_text = process_job(job_url, "temp_files/job.txt")
                elif job_file:
                    job_path = os.path.join("temp_files", job_file.name)
                    with open(job_path, "wb") as f:
                        f.write(job_file.read())
                    job_text = process_job(job_path, "temp_files/job.txt")

                if job_text:
                    # Ejecutar el motor de recomendación
                    get_cvs_and_recomendations(job_text, top_k=top_k)
                    st.success("Candidate analysis completed!")

                    # Ofrecer descarga
                    output_path = "../rag/cv_vector_db/reviews_of_candidates.csv"
                    with open(output_path, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode()
                    href = f'<a href="data:file/csv;base64,{b64}" download="recommended_candidates.csv">Download Results as CSV</a>'
                    st.markdown(href, unsafe_allow_html=True)
                else:
                    st.error("Could not process job description.")

            except Exception as e:
                st.error(f"Error: {str(e)}")

# Footer
st.markdown("---")
st.markdown("© 2025 ApplAI. All rights reserved.")
