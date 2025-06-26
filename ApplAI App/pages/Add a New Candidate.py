import streamlit as st
import os
import base64
from dotenv import load_dotenv
import pandas as pd
from utils import process_ai
import sys
# Agrega el path del proyecto raíz (donde está la carpeta "rag")
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import rag.extract_contact_info as extract_contact_info


# Cargar variables de entorno
load_dotenv()

# Configurar página
st.set_page_config(page_title="ApplAI - Add Candidate", page_icon="➕", layout="centered")

# Logo
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

st.header("Add a New Candidate to ApplAI")

st.markdown("""<br>*Upload or paste a CV to add it to the database of candidates.*""", unsafe_allow_html=True)
st.markdown("")

# Input
st.subheader("CV Input")
cv_url = st.text_input("LinkedIn Profile URL (optional)")
cv_file = st.file_uploader("Upload CV (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])

# Optional: Name for the new candidate
candidate_name = st.text_input("Candidate Name")

# Botón
st.markdown("<br>", unsafe_allow_html=True)

st.markdown("""
    <style>
    div.stButton > button {
        display: block;
        margin: 0 auto;
        background-color: #2196F3;
        color: white;
        border-radius: 12px;
        padding: 0.75em 2em;
        font-size: 18px;
        font-weight: bold;
        border: none;
    }
    </style>
""", unsafe_allow_html=True)

if st.button("Add Candidate", type="primary"):
    if not (cv_url.strip() or cv_file):
        st.error("Please provide a CV file or a LinkedIn profile URL.")
    else:
        with st.spinner("Processing candidate CV..."):
            try:
                # Procesar CV
                cv_text = ""
                path_to_save_txt = "../rag/pruebas" 

                if cv_url.strip():
                    cv_path = path_to_save_txt + "/cv_from_linkedin.txt"
                    cv_text = process_ai(cv_url, cv_path)
                    st.success("CV from LinkedIn processed successfully!")
                elif cv_file:
                    # Crear el archivo txt path_to_save_txt si no existe y guardar el cv_file
                    cv_path = os.path.join(path_to_save_txt, cv_file.name)
                    with open(cv_path, "wb") as f:
                        f.write(cv_file.getbuffer())
                    st.success("CV contact info uploaded successfully!")
                else:
                    st.error("No CV provided. Please upload a file or provide a URL.")

                extract_contact_info.main(cv_file_path=cv_path)     
                st.success("Candidate added successfully!") 


            except Exception as e:
                st.error(f"Error: {str(e)}")

# Footer
st.markdown("---")
st.markdown("© 2025 ApplAI. All rights reserved.")
