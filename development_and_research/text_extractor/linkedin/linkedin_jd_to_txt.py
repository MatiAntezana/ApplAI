import requests
import re
from datetime import datetime

def format_date(date_obj: dict | str | None) -> str:
    """
    Format a date object (dict with day, month, year) into a string.
    
    Parameters
    ----------
    date_obj : dict | str | None
        A dictionary with keys 'day', 'month', 'year' or a string representing the date.

    Returns
    -------
    str
        Formatted date string in the format 'DD/MM/YYYY' or 'Not available' if the input is None or invalid.
    """
    if date_obj and isinstance(date_obj, dict) and all(key in date_obj for key in ["day", "month", "year"]):
        return f"{date_obj['day']:02}/{date_obj['month']:02}/{date_obj['year']}"
    elif isinstance(date_obj, str):
        return date_obj
    return "Not available"


def format_salary(salary_data: dict) -> str:
    """
    Format salary information into a readable string.
    
    Parameters
    ----------
    salary_data : dict
        A dictionary containing salary information with keys 'min', 'max', 'currency', and 'period'.

    Returns
    -------
    str
        Formatted salary string or "Not available" if no salary data is provided.
    """
    if not salary_data:
        return "Not available"
    
    min_salary = salary_data.get('min', 0)
    max_salary = salary_data.get('max', 0)
    currency = salary_data.get('currency', '')
    period = salary_data.get('period', '')
    
    if min_salary and max_salary:
        return f"{currency} {min_salary:,} - {max_salary:,} per {period}"
    elif min_salary:
        return f"{currency} {min_salary:,}+ per {period}"
    elif max_salary:
        return f"Up to {currency} {max_salary:,} per {period}"
    else:
        return "Not available"


def extract_skills_from_description(description: str | None) -> list[str]:
    """
    Extract technical skills from job description using regex patterns."
    
    Parameters
    ----------
    description : str | None
        The job description text from which to extract skills.
    
    Returns
    -------
    list[str]
        A sorted list of unique skills extracted from the description. If no skills are found, returns an empty list.
    """ 
    if not description:
        return []
    
    skills_patterns = [
        # Programming languages
        r'\b(Python|Java|JavaScript|TypeScript|C\+\+|C#|PHP|Ruby|Go|Rust|Swift|Kotlin|Scala|R|MATLAB|Perl|Haskell|SQL|HTML|CSS|React|Angular|Vue|Node\.js|Django|Flask|Spring|Laravel|Rails|Express|FastAPI)\b',
        
        # Databases
        r'\b(MySQL|PostgreSQL|MongoDB|Redis|SQLite|Oracle|SQL Server|MariaDB|Cassandra|CouchDB|Neo4j|InfluxDB|DynamoDB|Firestore|BigQuery|Snowflake|Redshift|Elasticsearch)\b',
        
        # Cloud and DevOps
        r'\b(AWS|Azure|GCP|Google Cloud|Docker|Kubernetes|Jenkins|GitLab CI|GitHub Actions|Terraform|Ansible|Chef|Puppet|Nginx|Apache|EC2|S3|Lambda)\b',
        
        # Development tools
        r'\b(Git|GitHub|GitLab|Bitbucket|Visual Studio Code|IntelliJ|Eclipse|Postman|Swagger|Jira|Confluence|Trello|Slack|Teams|Figma|Sketch)\b',
        
        # Methodologies
        r'\b(Agile|Scrum|Kanban|DevOps|CI/CD|TDD|BDD|REST|GraphQL|API|Microservices|Machine Learning|AI|Data Science|Analytics|Testing|Automation)\b'
    ]
    
    skills = set()
    for pattern in skills_patterns:
        matches = re.findall(pattern, description, re.IGNORECASE)
        skills.update(matches)
    
    return sorted(list(skills))


def extract_experience_requirements(description: str | None) -> str:
    """
    Extract experience requirements from job description.
    
    Parameters
    ----------
    description : str | None
        The job description text from which to extract experience requirements.

    Returns
    -------
    str
        A string summarizing the experience requirements. If no requirements are found, returns "Not available".
    """
    if not description:
        return "Not available"
    
    experience_patterns = [
        r'(\d+)\+?\s*(?:years?|años?)\s*(?:of\s*)?(?:experience|experiencia)',
        r'(?:minimum|mínimo|at least|al menos)\s*(\d+)\s*(?:years?|años?)',
        r'(\d+)-(\d+)\s*(?:years?|años?)\s*(?:experience|experiencia)',
        r'(?:entry|junior|mid|senior|lead|principal|director)\s*(?:level|position)?'
    ]
    
    requirements = []
    for pattern in experience_patterns:
        matches = re.findall(pattern, description, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                requirements.append(' '.join(str(m) for m in match))
            else:
                requirements.append(str(match))
    
    return '; '.join(set(requirements)) if requirements else "Not available"


def extract_education_requirements(description: str | None) -> str:
    """
    Extract education requirements from job description.
    
    Parameters
    ----------
    description : str | None
        The job description text from which to extract education requirements.

    Returns
    -------
    str
        A string summarizing the education requirements. If no requirements are found, returns "Not available".
    """
    if not description:
        return "Not available"
    
    education_patterns = [
        r'\b(Bachelor|Master|PhD|Doctorate|Degree|Diploma|Certificate)\b.*?(?:in\s+)?([A-Za-z\s]+)',
        r'\b(Computer Science|Engineering|Mathematics|Statistics|Business|Marketing|Finance|Economics)\b',
        r'\b(University|College|Institute|School)\b\s+(?:degree|education|background)'
    ]
    
    education = []
    for pattern in education_patterns:
        matches = re.findall(pattern, description, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                education.append(' '.join(str(m).strip() for m in match if m.strip()))
            else:
                education.append(str(match).strip())
    
    return '; '.join(set(education)) if education else "Not available"


def extract_benefits(description: str | None) -> list[str]:
    """
    Extract benefits mentioned in job description.
    
    Parameters
    ----------
    description : str | None
        The job description text from which to extract benefits.

    Returns
    -------
    list[str]
        A sorted list of unique benefits mentioned in the description. If no benefits are found, returns an empty list.
    """
    if not description:
        return []
    
    benefits_patterns = [
        r'\b(health insurance|dental|vision|401k|retirement|vacation|PTO|sick leave|parental leave|flexible schedule|remote work|work from home|stock options|equity|bonus|training|education|gym|fitness|free lunch|snacks|parking|transportation|relocation assistance)\b'
    ]
    
    benefits = set()
    for pattern in benefits_patterns:
        matches = re.findall(pattern, description, re.IGNORECASE)
        benefits.update(matches)
    
    return sorted(list(benefits))


def extract_remote_work_info(description: str | None, remote_allowed: bool = False) -> str:
    """
    Extract remote work information.
    
    Parameters
    ----------
    description : str | None
        The job description text from which to extract remote work information.

    remote_allowed : bool
        A boolean indicating if remote work is explicitly allowed.

    Returns
    -------
    str
        A string summarizing the remote work policy. If remote work is allowed, returns "Remote work allowed".
        If no remote work information is found, returns "Not specified".
    """
    if remote_allowed:
        return "Remote work allowed"
    
    if not description:
        return "Not specified"
    
    remote_patterns = [
        r'\b(remote|work from home|telecommute|distributed|hybrid)\b',
        r'\b(on-site|office|in-person)\s+(?:only|required)',
        r'\b(flexible|hybrid)\s+(?:work|schedule)'
    ]
    
    for pattern in remote_patterns:
        if re.search(pattern, description, re.IGNORECASE):
            match = re.search(pattern, description, re.IGNORECASE)
            return match.group(0) if match else "Mentioned in description"
    
    return "Not specified"


# API Configuration
api_key = "CXsYh7_s4ncwk87NkmX_Qg"  
job_url = "https://www.linkedin.com/jobs/view/4201840839"  
endpoint = "https://enrichlayer.com/api/v2/job"
headers = {"Authorization": f"Bearer {api_key}"}
params = {"url": job_url}

# API Request
response = requests.get(endpoint, headers=headers, params=params)

# Process the response
if response.status_code == 200:
    data = response.json()
    job_description = data.get('job_description', '')

    with open("linkedin_job_content.txt", "w", encoding="utf-8") as file:

        # Basic Job Info
        file.write("=== Basic Job Information ===\n")
        file.write(f"Job title: {data.get('job_title', 'Not available')}\n")
        file.write(f"Job ID: {data.get('job_id', 'Not available')}\n")
        file.write(f"Job URL: {data.get('job_url', 'Not available')}\n")
        file.write(f"Apply URL: {data.get('apply_url', 'Not available')}\n")
        file.write(f"Employment type: {data.get('employment_type', 'Not available')}\n")
        file.write(f"Seniority level: {data.get('seniority_level', 'Not available')}\n")
        file.write(f"Job function: {', '.join(data.get('job_function', [])) or 'Not available'}\n")
        file.write(f"Industries: {', '.join(data.get('industries', [])) or 'Not available'}\n")
        file.write(f"Job state: {data.get('job_state', 'Not available')}\n")
        file.write(f"Total applicants: {data.get('total_applicants', 'Not available')}\n")
        file.write(f"Easy apply: {'Yes' if data.get('easy_apply') else 'No'}\n")
        file.write(f"Job posting language: {data.get('job_posting_language', 'Not available')}\n\n")

        # Timing Information
        file.write("=== Timing Information ===\n")
        file.write(f"Listed at: {data.get('listed_at', 'Not available')}\n")
        file.write(f"Posted date: {data.get('posted_date', 'Not available')}\n")
        file.write(f"Original listed time: {data.get('original_listed_time', 'Not available')}\n")
        file.write(f"Expiry date: {data.get('expiry_date', 'Not available')}\n")
        file.write(f"Application deadline: {data.get('application_deadline', 'Not available')}\n")
        file.write(f"Scraped at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Location Information
        file.write("=== Location Information ===\n")
        location = data.get('location', {})
        file.write(f"Location name: {location.get('name', 'Not available')}\n")
        file.write(f"City: {location.get('city', 'Not available')}\n")
        file.write(f"State: {location.get('state', 'Not available')}\n")
        file.write(f"Country: {location.get('country', 'Not available')}\n")
        file.write(f"Postal code: {location.get('postal_code', 'Not available')}\n")
        file.write(f"Remote work: {extract_remote_work_info(job_description, data.get('remote_allowed', False))}\n\n")

        # Company Information
        file.write("=== Company Information ===\n")
        company = data.get('company', {})
        file.write(f"Company name: {company.get('name', 'Not available')}\n")
        file.write(f"Company URL: {company.get('url', 'Not available')}\n")
        file.write(f"Company logo: {company.get('logo', 'Not available')}\n")
        file.write(f"Industry: {company.get('industry', 'Not available')}\n")
        file.write(f"Company size: {company.get('company_size', 'Not available')}\n")
        file.write(f"Headquarters: {company.get('headquarters', 'Not available')}\n")
        file.write(f"Founded: {company.get('founded', 'Not available')}\n")
        file.write(f"Follower count: {company.get('follower_count', 'Not available')}\n")
        file.write(f"Specialties: {', '.join(company.get('specialties', [])) or 'Not available'}\n\n")

        # Salary Information
        file.write("=== Salary Information ===\n")
        salary = data.get('salary', {})
        file.write(f"Salary range: {format_salary(salary)}\n")
        file.write(f"Minimum salary: {salary.get('min', 'Not available') if salary else 'Not available'}\n")
        file.write(f"Maximum salary: {salary.get('max', 'Not available') if salary else 'Not available'}\n")
        file.write(f"Currency: {salary.get('currency', 'Not available') if salary else 'Not available'}\n")
        file.write(f"Period: {salary.get('period', 'Not available') if salary else 'Not available'}\n\n")

        # Job Description
        file.write("=== Job Description ===\n")
        file.write(f"{job_description or 'Not available'}\n")
        file.write(f"Description length: {len(job_description)} characters\n")
        file.write(f"Word count: {len(job_description.split()) if job_description else 0} words\n\n")

        # Job Criteria
        file.write("=== Job Criteria ===\n")
        job_criteria = data.get('job_criteria', {})
        if job_criteria:
            for key, value in job_criteria.items():
                file.write(f"{key.replace('_', ' ').title()}: {value}\n")
        else:
            file.write("Not available\n")
        file.write("\n")

        # Extracted Skills
        file.write("=== Required Skills (Extracted) ===\n")
        skills = extract_skills_from_description(job_description)
        if skills:
            for skill in skills:
                file.write(f"• {skill}\n")
            file.write(f"Total skills identified: {len(skills)}\n")
        else:
            file.write("No specific technical skills identified\n")
        file.write("\n")

        # Experience Requirements
        file.write("=== Experience Requirements ===\n")
        experience_req = extract_experience_requirements(job_description)
        file.write(f"{experience_req}\n\n")

        # Education Requirements
        file.write("=== Education Requirements ===\n")
        education_req = extract_education_requirements(job_description)
        file.write(f"{education_req}\n\n")

        # Benefits
        file.write("=== Benefits (Extracted) ===\n")
        benefits = extract_benefits(job_description)
        if benefits:
            for benefit in benefits:
                file.write(f"• {benefit}\n")
            file.write(f"Total benefits mentioned: {len(benefits)}\n")
        else:
            file.write("No specific benefits mentioned\n")
        file.write("\n")

        # Hiring Team / Poster Information
        file.write("=== Hiring Team Information ===\n")
        poster = data.get('poster', {})
        file.write(f"Poster name: {poster.get('name', 'Not available')}\n")
        file.write(f"Poster title: {poster.get('title', 'Not available')}\n")
        file.write(f"Poster URL: {poster.get('url', 'Not available')}\n")
        
        hiring_team = data.get('hiring_team', [])
        if hiring_team:
            file.write("Hiring team members:\n")
            for member in hiring_team:
                file.write(f"• {member.get('name', 'Not available')} - {member.get('title', 'Not available')}\n")
        else:
            file.write("Hiring team: Not available\n")
        file.write("\n")

        # Application Information
        file.write("=== Application Information ===\n")
        file.write(f"Application URL: {data.get('application_url', 'Not available')}\n")
        file.write(f"Application type: {'Easy Apply' if data.get('easy_apply') else 'External Application'}\n")
        file.write(f"Application instructions: {data.get('application_instructions', 'Not available')}\n\n")

        # Additional Metadata
        file.write("=== Additional Metadata ===\n")
        file.write(f"Job posting HTML available: {'Yes' if data.get('job_description_html') else 'No'}\n")
        file.write(f"Company updates: {len(data.get('company_updates', [])) if data.get('company_updates') else 0}\n")
        file.write(f"Similar jobs: {len(data.get('similar_jobs', [])) if data.get('similar_jobs') else 0}\n")
        file.write(f"Job tags: {', '.join(data.get('job_tags', [])) or 'Not available'}\n")
        file.write(f"Job level: {data.get('job_level', 'Not available')}\n")
        file.write(f"Department: {data.get('department', 'Not available')}\n")
        file.write(f"Work arrangement: {data.get('work_arrangement', 'Not available')}\n")
        file.write(f"Visa sponsorship: {data.get('visa_sponsorship', 'Not available')}\n\n")

        # Quality Score and Analysis
        file.write("=== Job Posting Quality Analysis ===\n")
        quality_score = 0
        quality_factors = []
        
        if job_description and len(job_description) > 500:
            quality_score += 20
            quality_factors.append("Detailed job description")
        
        if salary:
            quality_score += 25
            quality_factors.append("Salary information provided")
        
        if len(skills) > 5:
            quality_score += 20
            quality_factors.append("Multiple technical skills mentioned")
        
        if benefits:
            quality_score += 15
            quality_factors.append("Benefits mentioned")
        
        if company.get('company_size'):
            quality_score += 10
            quality_factors.append("Company size information")
        
        if data.get('easy_apply'):
            quality_score += 10
            quality_factors.append("Easy application process")
        
        file.write(f"Quality score: {quality_score}/100\n")
        file.write("Quality factors:\n")
        for factor in quality_factors:
            file.write(f"• {factor}\n")
        if not quality_factors:
            file.write("• Basic job posting information only\n")
        file.write("\n")

        # Search Keywords
        file.write("=== Suggested Search Keywords ===\n")
        keywords = set()
        if data.get('job_title'):
            keywords.update(data['job_title'].split())
        keywords.update(skills)
        if data.get('seniority_level'):
            keywords.add(data['seniority_level'])
        if company.get('industry'):
            keywords.update(company['industry'].split())
        
        # Clean and filter keywords
        filtered_keywords = [kw for kw in keywords if len(kw) > 2 and kw.isalpha()]
        file.write(f"{', '.join(sorted(filtered_keywords)[:20])}\n\n")

    print("Job information saved to linkedin_job_content.txt")

else:
    print(f"Error: {response.status_code} - {response.text}")