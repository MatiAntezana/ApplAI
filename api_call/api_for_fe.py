import requests
import json
import csv
import io

# Configuration
API_KEY = "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"
MODEL = "deepseek/deepseek-r1:free"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
AI_TXT_PATH = "example/med_cv.txt"
JD_TXT_PATH = "example/jd_med.txt"
OUTPUT_CSV = "cv_jd_output.csv"

# Read input files
with open(AI_TXT_PATH, "r", encoding="utf-8") as f:
    ai_text = f.read()

with open(JD_TXT_PATH, "r", encoding="utf-8") as f:
    jd_text = f.read()

# Improved system prompt
system_prompt = """
You are an AI assistant that extracts specific fields from two types of documents: Job Descriptions and Applicant Information (CVs, LinkedIn profiles, etc.).

Your task is to:
1. Extract the specified fields from both documents
2. Format the output as a CSV row with two columns: "AI" and "JD"
3. Each field should be formatted as "Field Name: Value" or "Field Name: [list of values]"
4. All extracted information should be combined into a single string for each document type

FIELDS TO EXTRACT FROM APPLICANT INFORMATION (AI):
- Career Objective: Brief description of career goals and desired role
- Skills: List of technical and soft skills
- Institution: Educational institutions attended
- Degree: Academic degrees obtained
- Results: Academic results (GPA, grades, honors)
- Result Type: Type of academic result (GPA, Percentage, N/A)
- Field of Study: Areas of study or specialization
- Companies: Companies where the candidate has worked
- Job Skills: Skills used in each job position
- Positions: Job titles/roles held
- Responsibilities: Key responsibilities in each role
- Activity Type: Types of activities/involvement
- Organizations: Organizations involved with
- Roles: Roles in organizations
- Languages: Languages spoken
- Proficiency: Language proficiency levels
- Certifications From: Certification providers
- Certification Skills: Skills from certifications

FIELDS TO EXTRACT FROM JOB DESCRIPTION (JD):
- Job Position: Name of the advertised position
- Education: Minimum educational requirements
- Experience: Work experience requirements
- Age: Preferred age range
- JD Responsibilities: Expected job responsibilities
- Required Skills: Skills required for the position

FORMAT REQUIREMENTS:
- Return ONLY a CSV format response
- First line: AI,JD
- Second line: "extracted_AI_data","extracted_jd_data"
- Use double quotes around each field
- Escape internal quotes by doubling them
- Format lists as ['item1', 'item2', 'item3']
- Use "null" for missing information
- Use "N/A" for explicitly unavailable information
- Separate multiple field entries with ". " (period and space)

EXAMPLE OUTPUT FORMAT:
AI,JD
"Career Objective: Brief career objective text. Skills: ['Skill1', 'Skill2', 'Skill3']. Institution: ['University Name']. Degree: ['Degree Name']. Results: ['Grade/GPA']. Result Type: ['Type']. Field of Study: ['Field']. Companies: ['Company1', 'Company2']. Job Skills: [['Skill1', 'Skill2'], ['Skill3', 'Skill4']]. Positions: ['Position1', 'Position2']. Responsibilities: [Description of responsibilities]. Activity Type: ['Type']. Organizations: ['Org1', 'Org2']. Roles: ['Role1', 'Role2']. Languages: ['Language1']. Proficiency: ['Level']. Certifications From: ['Provider']. Certification Skills: [['Skill1', 'Skill2']]","Job Position: Position name. Education: Educational requirements. Experience: Experience requirements. Age: Age requirements. JD Responsibilities: [Responsibility1, Responsibility2]. Required Skills: [Skill1, Skill2]"

Real World Example:

Career Objective: Big data analytics working and database warehouse manager with robust experience in handling all kinds of data. I have also used multiple cloud infrastructure services and am well acquainted with them. Currently in search of role that offers more of development.. Skills: ['Big Data', 'Hadoop', 'Hive', 'Python', 'Mapreduce', 'Spark', 'Java', 'Machine Learning', 'Cloud', 'Hdfs', 'YARN', 'Core Java', 'Data Science', 'C++', 'Data Structures', 'DBMS', 'RDBMS', 'Informatica', 'Talend', 'Amazon Redshift', 'Microsoft Azure']. Institution: ['The Amity School of Engineering & Technology (ASET), Noida']. Degree: ['B.Tech']. Results: ['N/A']. Result Type: [None]. Field of Study: ['Electronics']. Companies: ['Coca-COla']. Job Skills: [['Big Data']]. Positions: ['Big Data Analyst']. Responsibilities: [Technical Support, Troubleshooting, Collaboration, Documentation, System Monitoring, Software Deployment, Training & Mentorship, Industry Trends, Field Visits]. Activity Type: null. Organizations: null. Roles: null. Languages: null. Proficiency: null. Certifications From: null. Certification Skills: null","Job Position: Senior Software Engineer. Education: B.Sc in Computer Science & Engineering from a reputed university.. Experience: At least 1 year. Age: null. JD Responsibilities: [Technical Support, Troubleshooting, Collaboration, Documentation, System Monitoring, Software Deployment, Training & Mentorship, Industry Trends, Field Visits]. Required Skills: null"

IMPORTANT: 
- Extract information accurately from the provided texts
- Do not invent or hallucinate information
- If information is not present, use "null"
- Maintain the exact field names as specified
- Return ONLY the CSV format, no additional text or explanations
"""

user_prompt = f"""Extract the required fields from the following documents and return them in CSV format:

APPLICANT INFORMATION:
{ai_text}

JOB DESCRIPTION:
{jd_text}
"""

# Request to the API
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "model": MODEL,
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    "temperature": 0.1,  # Lower temperature for more consistent output
    "max_tokens": 4000
}

print("🔄 Sending request to API...")
response = requests.post(API_URL, headers=headers, json=data)

if response.status_code != 200:
    print(f"❌ API Error: {response.status_code}")
    print(response.text)
    exit(1)

try:
    response_data = response.json()
    output_text = response_data["choices"][0]["message"]["content"].strip()
    
    # Clean up the output text
    if output_text.startswith("```csv"):
        output_text = output_text.removeprefix("```csv").removesuffix("```").strip()
    elif output_text.startswith("```"):
        output_text = output_text.removeprefix("```").removesuffix("```").strip()
    
    # Validate CSV format
    csv_reader = csv.reader(io.StringIO(output_text))
    rows = list(csv_reader)
    
    if len(rows) < 2:
        raise ValueError("Invalid CSV format: Expected at least 2 rows")
    
    if rows[0] != ['AI', 'JD']:
        raise ValueError("Invalid CSV format: Expected header 'CV,JD'")
    
    # Save to CSV file
    with open(OUTPUT_CSV, "w", encoding="utf-8", newline='') as f:
        f.write(output_text)
    
    print("✅ CSV file saved successfully to:", OUTPUT_CSV)
    print("\n📊 Preview of extracted data:")
    print("Header:", rows[0])
    print("AI data length:", len(rows[1][0]) if len(rows[1]) > 0 else 0, "characters")
    print("JD data length:", len(rows[1][1]) if len(rows[1]) > 1 else 0, "characters")
    
    # Display first 200 characters of each field for preview
    if len(rows[1]) > 0:
        print("\n🔍 CV Preview:")
        print(rows[1][0][:200] + "..." if len(rows[1][0]) > 200 else rows[1][0])
    
    if len(rows[1]) > 1:
        print("\n🔍 JD Preview:")
        print(rows[1][1][:200] + "..." if len(rows[1][1]) > 200 else rows[1][1])

except json.JSONDecodeError:
    print("❌ Error parsing the API response as JSON.")
    with open("raw_output.txt", "w", encoding="utf-8") as f:
        f.write(output_text)
    print("🔍 Raw output saved to 'raw_output.txt' for inspection.")

except csv.Error as e:
    print(f"❌ CSV format error: {e}")
    print("🔍 Raw output:")
    print(output_text)
    with open("raw_output.txt", "w", encoding="utf-8") as f:
        f.write(output_text)

except ValueError as e:
    print(f"❌ Validation error: {e}")
    print("🔍 Raw output:")
    print(output_text)
    with open("raw_output.txt", "w", encoding="utf-8") as f:
        f.write(output_text)

except Exception as e:
    print(f"❌ Unexpected error: {e}")
    print("🔍 Raw output:")
    print(output_text)
    with open("raw_output.txt", "w", encoding="utf-8") as f:
        f.write(output_text)
