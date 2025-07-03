import streamlit as st
import asyncio
import os
from PIL import Image
import base64
from dotenv import load_dotenv

from scripts.text_extraction.text_extractor_for_files import scrape_files
from scripts.text_extraction.text_extractor_for_general_webs import scrape_web
from scripts.text_extraction.text_extractor_for_linkedin_profiles import scrape_linkedin_profile
from scripts.text_extraction.text_extractor_for_linkedin_jobs import scrape_linkedin_job
from scripts.api_call.api_call_for_format_and_fe import (get_applicant_information, get_job_description)
from scripts.models.model import calculate_score

# Load environment variables
load_dotenv()

# Configure Streamlit app
st.set_page_config(page_title="ApplAI - Add a new candidate", page_icon="💾", layout="centered")

st.markdown(
    """
    <h1 style='text-align: center;'>
        Add new Applicant Information to the Database
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
        base64.b64encode(open("imgs/descarga_logo.png", "rb").read()).decode()
    ),
    unsafe_allow_html=True
)

st.markdown("<br>", unsafe_allow_html=True)

st.markdown("", unsafe_allow_html=True)

ai_url_linkedin = st.text_input("LinkedIn Profile URL")
ai_url_web = st.text_input("Personal Website URL")
ai_file = st.file_uploader("Upload AI File (CV, Cover Letter, Certificate, etc)", type=["pdf", "docx", "txt", "pptx", "jpg", "png", "csv", "json"], accept_multiple_files=False)

ai_ready = (ai_url_linkedin.strip() != "") or (ai_url_web.strip() != "") or (ai_file is not None)

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

if st.button("Add", type="primary"):
    if not (ai_ready):
        st.error("Please provide Applicant Information (LinkedIn, Website, or File) to proceed.")
    else:
        with st.spinner("Processing..."):
            try:
                os.makedirs("temp_files", exist_ok=True)

                # # Process Applicant Information
                # if ai_url_linkedin.strip() != "":
                #     scrape_linkedin_profile(ai_url_linkedin, "temp_files/ai.txt")
                
                # elif ai_url_web.strip() != "":
                #     scrape_web(ai_url_web, "temp_files/ai.txt")
                
                # elif ai_file: 
                #     ai_path = os.path.join("temp_files", ai_file.name)
                #     scrape_files(ai_path, "temp_files/ai.txt")

                    # Función que procesa archivo y lo guarda en la base de datos
                   
                # Display the compatibility score
                st.success("The information has been successfully processed!")

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


