import os
from linkedin_ai_to_txt import process_linkedin_profile
from linkedin_jd_to_txt import process_job_posting
from text_extractor_for_files import file_to_text
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from docx import Document

load_dotenv()


def process_ai_or_jd_file(source: str, output_path: str) -> str: # Sirve para los 2
    """
    Process applicant information from a URL or file.
    """
    if os.path.exists(source):
        text = file_to_text(source)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        return text
    return ""

def process_ai_or_jd_url(source: str, output_path: str) -> str:
    """
    Process applicant information from a URL.
    """
    if source.startswith("http"):
        text = process_linkedin_profile(source, output_path)
        return text
    return ""

def process_ai_linkedin(source: str, output_path: str) -> str:
    """Procesa un perfil de LinkedIn desde una URL o archivo."""
    if source.startswith("http"):
        # Procesar URL (e.g., LinkedIn profile)
        text = process_linkedin_profile(source, output_path)
        return text
    elif os.path.exists(source):
        # Procesar archivo
        text = extract_text(source)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        return text
    return ""

def process_jd_file(source: str, output_path: str) -> str:
    """Procesa una oferta de trabajo desde un archivo."""
    if os.path.exists(source):
        text = file_to_text(source)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        return text
    return ""


def process_job(source, output_path):
    """Procesa una oferta de trabajo desde una URL o archivo."""
    if source.startswith("http"):
        # Procesar URL (e.g., LinkedIn job posting)
        text = process_job_posting(source, output_path)
        return text
    elif os.path.exists(source):
        # Procesar archivo
        text = extract_text(source)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        return text
    return ""


def process_ai(source, output_path):
    return ""