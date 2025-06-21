import os
from linkedin_ai_to_txt import process_linkedin_profile
from linkedin_jd_to_txt import process_job_posting
from text_extractor_for_files import file_to_text
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from docx import Document

load_dotenv()

def extract_pdf_text(file_path):
    """Extrae texto de un archivo PDF."""
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        raise Exception(f"Error extracting PDF text: {str(e)}")

def extract_docx_text(file_path):
    """Extrae texto de un archivo DOCX."""
    try:
        doc = Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs if para.text])
        return text.strip()
    except Exception as e:
        raise Exception(f"Error extracting DOCX text: {str(e)}")

def extract_text(file_path):
    """Extrae texto según el tipo de archivo."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_pdf_text(file_path)
    elif ext == ".docx":
        return extract_docx_text(file_path)
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    else:
        raise ValueError(f"Unsupported file format: {ext}")

def process_ai(source: str, output_path: str) -> str:
    """
    Process applicant information from a URL or file. If the source is a URL, it processes the LinkedIn profile. If the 
    source is a file, it extracts text from the file.

    Parameters
    ----------
    source : str
        URL or file path of the applicant's information.
    output_path : str
        Path to save the extracted text.

    Returns
    -------
    text : str
        Extracted text from the applicant's information.
    """
    if source.startswith("http"):
        # Procesar URL (e.g., LinkedIn)
        text = process_linkedin_profile(source, output_path)
        return text
    elif os.path.exists(source):
        # Procesar archivo
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