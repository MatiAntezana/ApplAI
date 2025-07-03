from openai import AsyncAzureOpenAI
from pydantic import BaseModel, Field
import json
import os
import csv
import faiss 
import pickle
from typing import Optional
import json

API_KEY = "4u9eeKTcKNBvzIqH8PdwKGPcFt0oOIrVg03KDrRdshQBthudt701JQQJ99BEACHYHv6XJ3w3AAAAACOGdOzM"
ENDPOINT = "https://tizia-maebl6ih-eastus2.cognitiveservices.azure.com/"
DEPLOYMENT = "gpt-4o-mini-tiziano"
azure_client = AsyncAzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint=ENDPOINT,
    api_key=API_KEY
)

# Pydantic model para parsear luego
class CleanedCV(BaseModel):
    name: Optional[str] = Field(default="Not provided", description="Candidate's name")
    email: Optional[str] = Field(default="Not provided", description="Email address")
    phone_number: Optional[str] = Field(default="Not provided", description="Phone number")
    cv_information: str = Field(default="Not provided", description="Cleaned and structured CV information without personal identifiers")

# Función que llama al LLM y parsea el resultado
async def extract_cv_info(texto_crudo: str):
    system_prompt = "You are an assistant that extracts structured information from CVs."

    # Prompt
    user_prompt = f"""
You will receive a resume in raw text format. Your task is to extract:

1. The name of the candidate.
2. The email address.
3. The phone number.
4. A cleaned and structured version of the resume that removes any personal contact information (name, email, phone, address, LinkedIn, etc.).

For the fourth part:
- Do NOT summarize or omit key content.
- Instead, preserve as much of the original job-related information as possible.
- Reorganize and rephrase disconnected items into full sentences with proper structure and connectors (e.g., “The candidate worked at...”, “They were responsible for...”, “Their skills include...”).
- You may rewrite bullet points and lists as prose, but keep all relevant details intact.
- Do NOT include any personal identifiers or contact information.
- Imagine you are preparing the resume for analysis by an AI model – you want to keep the full context but make it more readable.

You may use the following fields **only if present** in the text:
- Career Objective
- Skills
- Institution
- Degree
- Results
- Result Type
- Field of Study
- Companies
- Job Skills
- Positions
- Responsibilities
- Activity Type
- Organizations
- Roles
- Languages
- Proficiency
- Certifications From
- Certification Skills

Return your answer strictly in JSON format as follows:

{{
    "name": "...",
    "email": "...",
    "phone_number": "...",
    "cv_information": "..."
}}

CV TEXT:
{texto_crudo}
"""
    try:
        response = await azure_client.chat.completions.create(
            model=DEPLOYMENT,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            max_tokens=1000
        )

        content = response.choices[0].message.content.strip()

        # Eliminar formato tipo markdown de código ```json ... ```
        if content.startswith("```json"):
            content = content.removeprefix("```json").removesuffix("```").strip()
        elif content.startswith("```"):
            content = content.removeprefix("```").removesuffix("```").strip()

        # Intentar cargar JSON
        data = json.loads(content)

        # Rellenar claves faltantes manualmente
        data = {
                "name": data.get("name", "Not provided"),
                "email": data.get("email", "Not provided"),
                "phone_number": data.get("phone_number", "Not provided"),
                "cv_information": data.get("cv_information", "Not provided")
            }
        return CleanedCV(**data)

    except Exception as e:
        print("⚠️ Error al procesar la respuesta del modelo:", e)
        print("🔎 Respuesta recibida:")
        print(content)
        return CleanedCV()

# === FUNCIÓN: Agregar a CSV ===
def append_to_csv(result, csv_path):
    file_exists = os.path.exists(csv_path)
    headers = ["id", "name", "email", "phone_number", "cv_information"]

    # Determinar nuevo ID
    new_id = 1
    if file_exists:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            if rows:
                new_id = max(int(row["id"]) for row in rows) + 1

    # Escribir fila
    with open(csv_path, "a", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "id": new_id,
            "name": result.name or "N/A",
            "email": result.email or "N/A",
            "phone_number": result.phone_number or "N/A",
            "cv_information":result.cv_information or "N/A",
        })

    return new_id  # Devolvemos el ID para asociarlo al embedding

# === FUNCIÓN: Agregar embedding a FAISS ===
def append_to_faiss(cv_id, info_cv_text, model, faiss_path, meta_path):
    embedding = model.encode([info_cv_text], normalize_embeddings=True)

    # Cargar o crear FAISS index
    if os.path.exists(faiss_path):
        index = faiss.read_index(faiss_path)
    else:
        dim = embedding.shape[1]
        index = faiss.IndexFlatIP(dim)  # producto interno (dot product) porque están normalizados

    # Agregar embedding
    index.add(embedding)
    faiss.write_index(index, faiss_path)

    # Cargar o crear metadatos
    if os.path.exists(meta_path):
        with open(meta_path, "rb") as f:
            metadata = pickle.load(f)
    else:
        metadata = {"ids": [], "texts": []}

    metadata["ids"].append(cv_id)
    metadata["texts"].append(info_cv_text)

    with open(meta_path, "wb") as f:
        pickle.dump(metadata, f)