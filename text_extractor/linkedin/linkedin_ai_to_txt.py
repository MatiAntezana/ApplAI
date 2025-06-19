import requests
import json
from datetime import datetime

def format_date(date_obj):
    """Formatea una fecha de la API (dict con day, month, year) a string."""
    if date_obj and all(key in date_obj for key in ["day", "month", "year"]):
        return f"{date_obj['day']}/{date_obj['month']}/{date_obj['year']}"
    return "No disponible"

# Configuración de la API
api_key = "EqzQFENPfsgA08-4_aMjfQ"  # Reemplaza con tu clave de API de Proxycurl
profile_url = "https://www.linkedin.com/in/tiziano-levi-martin-bernal/"  # Reemplaza con la URL del perfil de LinkedIn
endpoint = "https://nubela.co/proxycurl/api/v2/linkedin"
headers = {"Authorization": f"Bearer {api_key}"}
params = {"url": profile_url}

# Realizar la solicitud a la API
response = requests.get(endpoint, headers=headers, params=params)

# Verificar si la solicitud fue exitosa
if response.status_code == 200:
    data = response.json()
    
    # Abrir archivo para escribir
    with open("perfil_linkedin_completo.txt", "w", encoding="utf-8") as file:
        # Información básica
        file.write("=== Información Básica ===\n")
        file.write(f"Nombre completo: {data.get('full_name', 'No disponible')}\n")
        file.write(f"Titular: {data.get('headline', 'No disponible')}\n")
        file.write(f"URL del perfil: {data.get('public_identifier', 'No disponible')}\n")
        file.write(f"Imagen de perfil: {data.get('profile_picture', 'No disponible')}\n")
        file.write(f"Ciudad: {data.get('city', 'No disponible')}\n")
        file.write(f"Estado: {data.get('state', 'No disponible')}\n")
        file.write(f"País: {data.get('country_full_name', 'No disponible')}\n")
        file.write(f"Resumen: {data.get('summary', 'No disponible')}\n")
        file.write(f"Pronombres: {data.get('personal_pronoun', 'No disponible')}\n")
        file.write(f"Conexiones: {data.get('follower_count', 'No disponible')}\n")
        file.write("\n")

        # Experiencia laboral
        file.write("=== Experiencia Laboral ===\n")
        experiences = data.get("experiences", [])
        if experiences:
            for exp in experiences:
                file.write(f"Cargo: {exp.get('title', 'No disponible')}\n")
                file.write(f"Empresa: {exp.get('company', 'No disponible')}\n")
                file.write(f"URL Empresa: {exp.get('company_linkedin_profile_url', 'No disponible')}\n")
                file.write(f"Desde: {format_date(exp.get('starts_at'))}\n")
                file.write(f"Hasta: {format_date(exp.get('ends_at', {'year': 'Actual'}))}\n")
                file.write(f"Descripción: {exp.get('description', 'No disponible')}\n")
                file.write(f"Ubicación: {exp.get('location', 'No disponible')}\n")
                file.write("-" * 50 + "\n")
        else:
            file.write("No hay experiencia laboral disponible.\n")
        file.write("\n")

        # Educación
        file.write("=== Educación ===\n")
        education = data.get("education", [])
        if education:
            for edu in education:
                file.write(f"Institución: {edu.get('school', 'No disponible')}\n")
                file.write(f"URL Institución: {edu.get('school_linkedin_profile_url', 'No disponible')}\n")
                file.write(f"Grado: {edu.get('degree_name', 'No disponible')}\n")
                file.write(f"Campo de estudio: {edu.get('field_of_study', 'No disponible')}\n")
                file.write(f"Desde: {format_date(edu.get('starts_at'))}\n")
                file.write(f"Hasta: {format_date(edu.get('ends_at'))}\n")
                file.write(f"Descripción: {edu.get('description', 'No disponible')}\n")
                file.write("-" * 50 + "\n")
        else:
            file.write("No hay educación disponible.\n")
        file.write("\n")

        # Habilidades
        file.write("=== Habilidades ===\n")
        skills = data.get("skills", [])
        if skills:
            file.write(", ".join(skills) + "\n")
        else:
            file.write("No hay habilidades disponibles.\n")
        file.write("\n")

        # Certificaciones
        file.write("=== Certificaciones ===\n")
        certifications = data.get("certifications", [])
        if certifications:
            for cert in certifications:
                file.write(f"Nombre: {cert.get('name', 'No disponible')}\n")
                file.write(f"Autoridad: {cert.get('authority', 'No disponible')}\n")
                file.write(f"Desde: {format_date(cert.get('starts_at'))}\n")
                file.write(f"Hasta: {format_date(cert.get('ends_at'))}\n")
                file.write(f"URL: {cert.get('url', 'No disponible')}\n")
                file.write(f"Número de licencia: {cert.get('license_number', 'No disponible')}\n")
                file.write("-" * 50 + "\n")
        else:
            file.write("No hay certificaciones disponibles.\n")
        file.write("\n")

        # Idiomas
        file.write("=== Idiomas ===\n")
        languages = data.get("languages", [])
        if languages:
            file.write(", ".join(languages) + "\n")
        else:
            file.write("No hay idiomas disponibles.\n")
        file.write("\n")

        # Proyectos
        file.write("=== Proyectos ===\n")
        projects = data.get("accomplishment_projects", [])
        if projects:
            for proj in projects:
                file.write(f"Título: {proj.get('title', 'No disponible')}\n")
                file.write(f"Descripción: {proj.get('description', 'No disponible')}\n")
                file.write(f"URL: {proj.get('url', 'No disponible')}\n")
                file.write("-" * 50 + "\n")
        else:
            file.write("No hay proyectos disponibles.\n")
        file.write("\n")

        # Publicaciones
        file.write("=== Publicaciones ===\n")
        publications = data.get("accomplishment_publications", [])
        if publications:
            for pub in publications:
                file.write(f"Título: {pub.get('name', 'No disponible')}\n")
                file.write(f"Editorial: {pub.get('publisher', 'No disponible')}\n")
                file.write(f"Fecha: {format_date(pub.get('published_on'))}\n")
                file.write(f"URL: {pub.get('url', 'No disponible')}\n")
                file.write("-" * 50 + "\n")
        else:
            file.write("No hay publicaciones disponibles.\n")
        file.write("\n")

        # Patentes
        file.write("=== Patentes ===\n")
        patents = data.get("accomplishment_patents", [])
        if patents:
            for patent in patents:
                file.write(f"Título: {patent.get('title', 'No disponible')}\n")
                file.write(f"Autoridad: {patent.get('issuer', 'No disponible')}\n")
                file.write(f"Fecha: {format_date(patent.get('issued_on'))}\n")
                file.write(f"Número: {patent.get('patent_number', 'No disponible')}\n")
                file.write(f"URL: {patent.get('url', 'No disponible')}\n")
                file.write("-" * 50 + "\n")
        else:
            file.write("No hay patentes disponibles.\n")
        file.write("\n")

        # Cursos
        file.write("=== Cursos ===\n")
        courses = data.get("accomplishment_courses", [])
        if courses:
            for course in courses:
                file.write(f"Nombre: {course.get('name', 'No disponible')}\n")
                file.write(f"Número: {course.get('number', 'No disponible')}\n")
                file.write("-" * 50 + "\n")
        else:
            file.write("No hay cursos disponibles.\n")
        file.write("\n")

        # Organizaciones
        file.write("=== Organizaciones ===\n")
        organizations = data.get("accomplishment_organizations", [])
        if organizations:
            for org in organizations:
                file.write(f"Nombre: {org.get('name', 'No disponible')}\n")
                file.write(f"Cargo: {org.get('position', 'No disponible')}\n")
                file.write(f"Desde: {format_date(org.get('starts_at'))}\n")
                file.write(f"Hasta: {format_date(org.get('ends_at'))}\n")
                file.write(f"Descripción: {org.get('description', 'No disponible')}\n")
                file.write("-" * 50 + "\n")
        else:
            file.write("No hay organizaciones disponibles.\n")
        file.write("\n")

        # Premios
        file.write("=== Premios y Reconocimientos ===\n")
        awards = data.get("accomplishment_honors_awards", [])
        if awards:
            for award in awards:
                file.write(f"Título: {award.get('title', 'No disponible')}\n")
                file.write(f"Emisor: {award.get('issuer', 'No disponible')}\n")
                file.write(f"Fecha: {format_date(award.get('issued_on'))}\n")
                file.write(f"Descripción: {award.get('description', 'No disponible')}\n")
                file.write("-" * 50 + "\n")
        else:
            file.write("No hay premios disponibles.\n")
        file.write("\n")

        # Actividades
        file.write("=== Actividades Recientes ===\n")
        activities = data.get("activities", [])
        if activities:
            for activity in activities:
                file.write(f"Título: {activity.get('title', 'No disponible')}\n")
                file.write(f"Enlace: {activity.get('link', 'No disponible')}\n")
                file.write(f"Estado: {activity.get('activity_status', 'No disponible')}\n")
                file.write("-" * 50 + "\n")
        else:
            file.write("No hay actividades disponibles.\n")
        file.write("\n")

        # Grupos
        file.write("=== Grupos ===\n")
        groups = data.get("groups", [])
        if groups:
            for group in groups:
                file.write(f"Nombre: {group.get('name', 'No disponible')}\n")
                file.write(f"URL: {group.get('group_linkedin_url', 'No disponible')}\n")
                file.write("-" * 50 + "\n")
        else:
            file.write("No hay grupos disponibles.\n")
    
    print("Datos guardados en perfil_linkedin_completo.txt")
else:
    print(f"Error: {response.status_code} - {response.text}")