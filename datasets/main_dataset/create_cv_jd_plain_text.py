import numpy as np
import pandas as pd
import re
import os

def main():
    # Load the data
    df = pd.read_csv('cv_jd_score_dataset/resume_data.csv')

    # Define the columns for Applicant Information (AI) and Job Description (JD)
    cv_columns = [
        "career_objective", "skills", "educational_institution_name", "degree_names",
        "educational_results", "result_types", "major_field_of_studies",
        "professional_company_names", "related_skils_in_job", "positions",
        "responsibilities", "extra_curricular_activity_types", "extra_curricular_organization_names",
        "role_positions", "languages", "proficiency_levels", "certification_providers", "certification_skills"
    ]

    jd_columns = [
        "job_position_name", "educationaL_requirements", "experiencere_requirement",
        "age_requirement", "responsibilities.1", "skills_required"
    ]

    # 🔁 Preprocesar campos con \n y ponerlos en listas
    multiline_fields = ['responsibilities', 'responsibilities.1', 'skills_required']
    for col in multiline_fields:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: f"[{', '.join(x.strip().splitlines())}]" if isinstance(x, str) else x
            )

    # Función para convertir a texto un bloque del CV o JD
    def concatenate_fields(row, columns, field_prefixes):
        return ". ".join([
            f"{prefix}: {row[col] if pd.notnull(row[col]) else 'null'}" 
            for col, prefix in zip(columns, field_prefixes)
        ])

    # Prefijos descriptivos (en el mismo orden que las columnas)
    cv_prefixes = [
        "Career Objective", "Skills", "Institution", "Degree",
        "Results", "Result Type", "Field of Study",
        "Companies", "Job Skills", "Positions",
        "Responsibilities", "Activity Type", "Organizations",
        "Roles", "Languages", "Proficiency", "Certifications From", "Certification Skills"
    ]

    jd_prefixes = [
        "Job Position", "Education", "Experience",
        "Age", "JD Responsibilities", "Required Skills"
    ]

    # Crear las nuevas columnas
    df['CV'] = df.apply(lambda row: concatenate_fields(row, cv_columns, cv_prefixes), axis=1)
    df['JD'] = df.apply(lambda row: concatenate_fields(row, jd_columns, jd_prefixes), axis=1)

    # Conservar solo lo que te interesa
    final_df = df[['CV', 'JD', 'matched_score']].rename(columns={'matched_score': 'score'})

    # Guardar a CSV
    final_df.to_csv("cv_jd_score_dataset/plain_text_resume_data.csv", index=False)

if __name__ == "__main__":
    main()
