import streamlit as st
import os
import base64
import pandas as pd
from dotenv import load_dotenv
from scripts.text_extraction.text_extractor_for_files import scrape_files
from scripts.text_extraction.text_extractor_for_general_webs import scrape_web
from scripts.text_extraction.text_extractor_for_linkedin_jobs import scrape_linkedin_job
from scripts.models.gen_ai_finder_output import get_candidates_and_recomendations

# Load environment variables
load_dotenv()

# Configure Streamlit app
st.set_page_config(page_title="ApplAI - Smart Applicant Information Finder", page_icon="🗃️", layout="centered")

st.markdown(
    """
    <h1 style='text-align: center;'>
        Find the Best Candidates for a Job in your Database
    </h1>
    """,
    unsafe_allow_html=True
)

st.markdown("<br>", unsafe_allow_html=True)

st.markdown(
    """
    <div style='text-align: center;'>
        <img src="data:image/png;base64,{}" width="300">
    </div>
    """.format(
        base64.b64encode(open("imgs/base_logo.png", "rb").read()).decode()
    ),
    unsafe_allow_html=True
)

st.markdown("""<br>*This feature uses a **RAG** (Retrieval-Augmented Generation)-based system to **identify the most suitable candidates** in your **database** for a **specific job position**. Simply **upload the job description** in any format and receive a list ordered by **score** of the **best-matched profiles**. Additionally, you can always **add new applicants to your database** whether by uploading a file or entering a LinkedIn or website link.*""", unsafe_allow_html=True)

st.markdown("", unsafe_allow_html=True)

st.subheader("Number of Candidates to Return")
top_k_candidates = st.number_input("How many candidates would you like to retrieve?", min_value=1, max_value=15, value=3, step=1)

st.markdown("", unsafe_allow_html=True)

st.subheader("Job Description Input")
job_url_linkedin = st.text_input("Job Posting from LinkedIn URL")
job_url_web = st.text_input("Job Posting from a Website URL")
job_file = st.file_uploader("Upload Job Description File", type=["pdf", "docx", "txt", "pptx", "jpg", "png", "csv", "json"], accept_multiple_files=False)

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

if st.button("Find Candidates", type="primary"):
    if not job_ready:
        st.error("Please provide a Job Posting (URL or file).")
    else:
        with st.spinner("Processing..."):
            try:
                os.makedirs("temp_files", exist_ok=True)

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

                # Find candidates
                get_candidates_and_recomendations(
                    "temp_files/job.txt",
                    "database/ai_personal_info.csv",
                    "database/ai_index.faiss",
                    "database/ai_metadata.pkl",
                    "temp_files/candidates.csv",
                    top_k=top_k_candidates
                )

                # Load and display candidates
                candidates_df = pd.read_csv("temp_files/candidates.csv")

                st.markdown("<br>", unsafe_allow_html=True)

                st.markdown("<h3 style='text-align: center;'>🧠 Top Candidates Found</h3>", unsafe_allow_html=True)

                for idx, row in candidates_df.iterrows():
                    candidate_text = row['candidate_text'].replace('\n', '<br>')
                    st.markdown(f"""
                    <div style="border: 1px solid #DDD; padding: 15px; margin-bottom: 10px; border-radius: 10px;">
                        <h4 style="margin-bottom: 5px;">👤 {row['candidate_name']}</h4>
                        <p style="font-size: 14px; line-height: 1.4; margin: 0;">{candidate_text}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Download button
                csv_download = candidates_df.to_csv(index=False).encode('utf-8')
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.download_button(
                        label="📥 Download Candidates CSV",
                        data=csv_download,
                        file_name='top_candidates.csv',
                        mime='text/csv'
                    )

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
