import os
import requests
from dotenv import load_dotenv

load_dotenv()

def process_linkedin_profile(url, output_path):
    """Procesa un perfil de LinkedIn y guarda el texto en output_path."""
    api_key = "TM4VWAaCsKVJJarO4YsT0Q"
    if not api_key:
        raise ValueError("Missing PROXYCURL_API_KEY")
    
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        # Simula llamada a Proxycurl (ajusta la URL según la API real)
        response = requests.get(
            "https://nubela.co/proxycurl/api/v2/linkedin",
            params={"url": url},
            headers=headers
        )
        response.raise_for_status()
        data = response.json()
        
        # Extrae información relevante (simplificado)
        text = f"""
Name: {data.get('full_name', '')}
Headline: {data.get('headline', '')}
Summary: {data.get('summary', '')}
Experiences: {', '.join([exp.get('title', '') for exp in data.get('experiences', [])])}
Skills: {', '.join(data.get('skills', []))}
        """.strip()
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        return text
    except Exception as e:
        raise Exception(f"Failed to process LinkedIn profile: {str(e)}")