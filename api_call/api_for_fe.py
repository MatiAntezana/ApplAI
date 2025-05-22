import requests
import json

# === CONFIGURACIÓN ===
API_KEY = "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"
MODEL = "deepseek/deepseek-r1:free"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
CV_TXT_PATH = "example/cv_med.txt"
JD_TXT_PATH = "example/jd_med.txt"
OUTPUT_CV = "cv_med.json"
OUTPUT_JD = "jd_med.json"

# === LEER CV Y JD ===
with open(CV_TXT_PATH, "r", encoding="utf-8") as f:
    cv_text = f.read()

with open(JD_TXT_PATH, "r", encoding="utf-8") as f:
    jd_text = f.read()

# === PROMPTS ===
system_prompt = """
Sos un asistente de IA cuyo trabajo es la extracción de campos especiales de 2 tipos de archivo: Descripciones de
trabajo y CVs de aplicantes. Los campos a extraer del CV son: career_objective, skills, educational_institution_name, 
degree_names, educational_results, result_types, major_field_of_studies, professional_company_names, 
related_skils_in_job, positions, responsibilities, extra_curricular_activity_types, 
extra_curricular_organization_names, role_positions, languages, proficiency_levels, certification_providers, 
certification_skills.

Los campos a extraer de la Descripción de Trabajo son: job_position_name, educational_requirements, 
experience_requirement, age_requirement, responsibilities, skills_required.

Devolvé un único JSON con esta estructura:
{
  "cv": { ... },
  "jd": { ... }
}
"""

user_prompt = f"""Texto del CV:
\"\"\"
{cv_text}
\"\"\"

Texto de la Descripción de Trabajo:
\"\"\"
{jd_text}
\"\"\"
"""

# === REQUEST ===
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "model": MODEL,
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
}

response = requests.post(API_URL, headers=headers, json=data)
output_text = response.json()["choices"][0]["message"]["content"]

# === LIMPIEZA DEL BLOQUE MARKDOWN ===
if output_text.strip().startswith("```json"):
    output_text = output_text.strip().removeprefix("```json").removesuffix("```").strip()
elif output_text.strip().startswith("```"):
    output_text = output_text.strip().removeprefix("```").removesuffix("```").strip()

# === PARSEAR EL JSON Y GUARDAR ===
try:
    resultado = json.loads(output_text)
    with open(OUTPUT_CV, "w", encoding="utf-8") as f:
        json.dump(resultado["cv"], f, ensure_ascii=False, indent=4)
    with open(OUTPUT_JD, "w", encoding="utf-8") as f:
        json.dump(resultado["jd"], f, ensure_ascii=False, indent=4)
    print("✅ Archivos JSON guardados correctamente.")
except json.JSONDecodeError:
    print("❌ Error al parsear la respuesta como JSON.")
    with open("raw_output.txt", "w", encoding="utf-8") as f:
        f.write(output_text)
    print("🔍 Se guardó la salida cruda en 'raw_output.txt' para inspección.")
except KeyError:
    print("❌ El JSON no contiene las claves esperadas ('cv' y 'jd').")
    print("📤 Respuesta completa:")
    print(output_text)

