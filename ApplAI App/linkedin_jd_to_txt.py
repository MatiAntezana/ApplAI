import os
import requests
from dotenv import load_dotenv

load_dotenv()

def process_job_posting(url, output_path):
    """Procesa una oferta de trabajo desde una URL y guarda el texto en output_path."""
    api_key = "TM4VWAaCsKVJJarO4YsT0Q"
    if not api_key:
        raise ValueError("Missing PROXYCURL_API_KEY")
    
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        # Simula llamada a Proxycurl (ajusta la URL según la API real)
        response = requests.get(
            "https://nubela.co/proxycurl/api/linkedin/job",
            params={"url": url},
            headers=headers
        )
        response.raise_for_status()
        data = response.json()
        
        # Extrae información relevante (simplificado)
        text = f"""
Title: {data.get('job_title', '')}
Company: {data.get('company', '')}
Description: {data.get('description', '')}
Requirements: {data.get('requirements', '')}
        """.strip()
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        return text
    except Exception as e:
        raise Exception(f"Failed to process job posting: {str(e)}")