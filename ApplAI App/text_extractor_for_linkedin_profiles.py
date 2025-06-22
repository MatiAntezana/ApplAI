import requests
from typing import Optional

def format_date(date_obj: dict) -> str:
    """
    Format a date object (dict with day, month, year) into a string.
    
    Parameters
    ----------
    date_obj : dict
        A dictionary containing 'day', 'month', and 'year' keys.

    Returns
    -------
    str
        A formatted date string in the format "DD/MM/YYYY" or "Not available" if the date object is None or does not 
        contain the required keys.
    """
    if date_obj and all(key in date_obj for key in ["day", "month", "year"]):
        return f"{date_obj['day']:02}/{date_obj['month']:02}/{date_obj['year']}"
    return "Not available"


def scrape_linkedin_profile(source: str, output_path: str, api_key: Optional[str] = None) -> None:
    """
    Scrape LinkedIn profile data and save it to a text file.
    
    Parameters
    ----------
    source : str
        LinkedIn profile URL to scrape
    output_path : str
        Path where the output text file will be saved
    api_key : str, optional
        API key for EnrichLayer service. If not provided, uses default key.
    
    Returns
    -------
    None
    """
        # Validate input parameters
    if not isinstance(source, str) or not source.strip():
        raise ValueError("Invalid source URL provided.")
    
    if not isinstance(output_path, str) or not output_path.strip():
        raise ValueError("Invalid output path provided.")
    
    # Default API key
    if api_key is None:
        api_key = "CXsYh7_s4ncwk87NkmX_Qg"
    
    endpoint = "https://enrichlayer.com/api/v2/profile"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"url": source}

    try:
        response = requests.get(endpoint, headers=headers, params=params, timeout=15)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise RuntimeError("The request to EnrichLayer timed out.")
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"An error occurred while making the request: {e}")

    try:
        data = response.json()
    except ValueError:
        raise RuntimeError("Failed to parse response JSON from EnrichLayer.")

    try:
        with open(output_path, "w", encoding="utf-8") as file:
            # Basic Info
            file.write("=== Basic Info ===\n")
            file.write(f"Full name: {data.get('full_name', 'Not available')}\n")
            file.write(f"Occupation: {data.get('occupation', 'Not available')}\n")
            file.write(f"Headline: {data.get('headline', 'Not available')}\n")
            file.write(f"Summary: {data.get('summary', 'Not available')}\n")
            file.write(f"Public identifier: {data.get('public_identifier', 'Not available')}\n")
            file.write(f"Profile picture: {data.get('profile_pic_url', 'Not available')}\n")
            file.write(f"Background cover image: {data.get('background_cover_image_url', 'Not available')}\n")
            file.write(f"City: {data.get('city', 'Not available')}\n")
            file.write(f"State: {data.get('state', 'Not available')}\n")
            file.write(f"Country: {data.get('country_full_name', 'Not available')}\n")
            file.write(f"Pronouns: {data.get('personal_pronoun', 'Not available')}\n")
            file.write(f"Followers: {data.get('follower_count', 'Not available')}\n")
            file.write(f"Connections: {data.get('connections', 'Not available')}\n\n")

            # Work Experience
            file.write("=== Work Experience ===\n")
            experiences = data.get("experiences", [])
            if experiences:
                for exp in experiences:
                    file.write(f"Title: {exp.get('title', 'Not available')}\n")
                    file.write(f"Company: {exp.get('company', 'Not available')}\n")
                    file.write(f"Company URL: {exp.get('company_linkedin_profile_url', 'Not available')}\n")
                    file.write(f"Start date: {format_date(exp.get('starts_at'))}\n")
                    file.write(f"End date: {format_date(exp.get('ends_at'))}\n")
                    file.write(f"Location: {exp.get('location', 'Not available')}\n")
                    file.write(f"Description: {exp.get('description', 'Not available')}\n")
                    file.write("-" * 50 + "\n")
            else:
                file.write("No work experience available.\n")
            file.write("\n")

            # Education
            file.write("=== Education ===\n")
            education = data.get("education", [])
            if education:
                for edu in education:
                    file.write(f"School: {edu.get('school', 'Not available')}\n")
                    file.write(f"Degree: {edu.get('degree_name', 'Not available')}\n")
                    file.write(f"Field of study: {edu.get('field_of_study', 'Not available')}\n")
                    file.write(f"Start date: {format_date(edu.get('starts_at'))}\n")
                    file.write(f"End date: {format_date(edu.get('ends_at'))}\n")
                    file.write(f"Description: {edu.get('description', 'Not available')}\n")
                    file.write("-" * 50 + "\n")
            else:
                file.write("No education available.\n")
            file.write("\n")

            # Skills
            file.write("=== Skills ===\n")
            skills = data.get("skills", [])
            if skills:
                file.write(", ".join(skills) + "\n")
            else:
                file.write("No skills available.\n")
            file.write("\n")

            # Certifications
            file.write("=== Certifications ===\n")
            certifications = data.get("certifications", [])
            if certifications:
                for cert in certifications:
                    file.write(f"Name: {cert.get('name', 'Not available')}\n")
                    file.write(f"Issuer: {cert.get('authority', 'Not available')}\n")
                    file.write(f"Start date: {format_date(cert.get('starts_at'))}\n")
                    file.write(f"End date: {format_date(cert.get('ends_at'))}\n")
                    file.write(f"URL: {cert.get('url', 'Not available')}\n")
                    file.write("-" * 50 + "\n")
            else:
                file.write("No certifications available.\n")
            file.write("\n")

            # Languages
            file.write("=== Languages ===\n")
            languages = data.get("languages", [])
            if languages:
                file.write(", ".join(languages) + "\n")
            else:
                file.write("No languages available.\n")
            file.write("\n")

            # Languages and Proficiencies
            file.write("=== Languages and Proficiencies ===\n")
            for lang in data.get("languages_and_proficiencies", []):
                file.write(f"{lang.get('name', 'Not available')}: {lang.get('proficiency', 'Not available')}\n")
            file.write("\n")

            # Projects
            file.write("=== Projects ===\n")
            projects = data.get("accomplishment_projects", [])
            if projects:
                for proj in projects:
                    file.write(f"Title: {proj.get('title', 'Not available')}\n")
                    file.write(f"Description: {proj.get('description', 'Not available')}\n")
                    file.write(f"URL: {proj.get('url', 'Not available')}\n")
                    file.write("-" * 50 + "\n")
            else:
                file.write("No projects available.\n")
            file.write("\n")

            # Publications
            file.write("=== Publications ===\n")
            publications = data.get("accomplishment_publications", [])
            if publications:
                for pub in publications:
                    file.write(f"Title: {pub.get('name', 'Not available')}\n")
                    file.write(f"Publisher: {pub.get('publisher', 'Not available')}\n")
                    file.write(f"Published on: {format_date(pub.get('published_on'))}\n")
                    file.write(f"URL: {pub.get('url', 'Not available')}\n")
                    file.write("-" * 50 + "\n")
            else:
                file.write("No publications available.\n")
            file.write("\n")

            # Patents
            file.write("=== Patents ===\n")
            patents = data.get("accomplishment_patents", [])
            if patents:
                for patent in patents:
                    file.write(f"Title: {patent.get('title', 'Not available')}\n")
                    file.write(f"Issuer: {patent.get('issuer', 'Not available')}\n")
                    file.write(f"Issued on: {format_date(patent.get('issued_on'))}\n")
                    file.write(f"Patent number: {patent.get('patent_number', 'Not available')}\n")
                    file.write(f"URL: {patent.get('url', 'Not available')}\n")
                    file.write("-" * 50 + "\n")
            else:
                file.write("No patents available.\n")
            file.write("\n")

            # Courses
            file.write("=== Courses ===\n")
            courses = data.get("accomplishment_courses", [])
            if courses:
                for course in courses:
                    file.write(f"Name: {course.get('name', 'Not available')}\n")
                    file.write(f"Number: {course.get('number', 'Not available')}\n")
                    file.write("-" * 50 + "\n")
            else:
                file.write("No courses available.\n")
            file.write("\n")

            # Organizations
            file.write("=== Organizations ===\n")
            organizations = data.get("accomplishment_organisations", [])
            if organizations:
                for org in organizations:
                    file.write(f"Name: {org.get('name', 'Not available')}\n")
                    file.write(f"Position: {org.get('position', 'Not available')}\n")
                    file.write(f"Start date: {format_date(org.get('starts_at'))}\n")
                    file.write(f"End date: {format_date(org.get('ends_at'))}\n")
                    file.write(f"Description: {org.get('description', 'Not available')}\n")
                    file.write("-" * 50 + "\n")
            else:
                file.write("No organizations available.\n")
            file.write("\n")

            # Awards
            file.write("=== Awards ===\n")
            awards = data.get("accomplishment_honors_awards", [])
            if awards:
                for award in awards:
                    file.write(f"Title: {award.get('title', 'Not available')}\n")
                    file.write(f"Issuer: {award.get('issuer', 'Not available')}\n")
                    file.write(f"Issued on: {format_date(award.get('issued_on'))}\n")
                    file.write(f"Description: {award.get('description', 'Not available')}\n")
                    file.write("-" * 50 + "\n")
            else:
                file.write("No awards available.\n")
            file.write("\n")

            # Volunteer Work
            file.write("=== Volunteer Work ===\n")
            volunteer_work = data.get("volunteer_work", [])
            if volunteer_work:
                for vol in volunteer_work:
                    file.write(f"Title: {vol.get('title', 'Not available')}\n")
                    file.write(f"Organization: {vol.get('company', 'Not available')}\n")
                    file.write(f"Cause: {vol.get('cause', 'Not available')}\n")
                    file.write(f"Start date: {format_date(vol.get('starts_at'))}\n")
                    file.write(f"End date: {format_date(vol.get('ends_at'))}\n")
                    file.write(f"Description: {vol.get('description', 'Not available')}\n")
                    file.write("-" * 50 + "\n")
            else:
                file.write("No volunteer work available.\n")
            file.write("\n")

            # Recommendations
            file.write("=== Recommendations ===\n")
            recommendations = data.get("recommendations", [])
            if recommendations:
                for rec in recommendations:
                    file.write(f"Recommender: {rec.get('recommender_name', 'Not available')}\n")
                    file.write(f"Title: {rec.get('recommender_title', 'Not available')}\n")
                    file.write(f"Text: {rec.get('text', 'Not available')}\n")
                    file.write("-" * 50 + "\n")
            else:
                file.write("No recommendations available.\n")
            file.write("\n")

            # Articles
            file.write("=== Articles ===\n")
            articles = data.get("articles", [])
            if articles:
                for art in articles:
                    file.write(f"Title: {art.get('title', 'Not available')}\n")
                    file.write(f"Published on: {format_date(art.get('published_on'))}\n")
                    file.write(f"URL: {art.get('url', 'Not available')}\n")
                    file.write(f"Description: {art.get('description', 'Not available')}\n")
                    file.write("-" * 50 + "\n")
            else:
                file.write("No articles available.\n")
            file.write("\n")

            # Inferred Salary
            file.write("=== Inferred Salary ===\n")
            file.write(f"{data.get('inferred_salary', 'Not available')}\n\n")

            # Gender
            file.write("=== Gender ===\n")
            file.write(f"{data.get('gender', 'Not available')}\n\n")

            # Birth Date
            file.write("=== Birth Date ===\n")
            file.write(f"{data.get('birth_date', 'Not available')}\n\n")

            # Industry
            file.write("=== Industry ===\n")
            file.write(f"{data.get('industry', 'Not available')}\n\n")

            # Interests
            file.write("=== Interests ===\n")
            interests = data.get("interests", [])
            if interests:
                file.write(", ".join(interests) + "\n")
            else:
                file.write("No interests available.\n")
            file.write("\n")

            # Personal Emails
            file.write("=== Personal Emails ===\n")
            emails = data.get("personal_emails", [])
            if emails:
                file.write(", ".join(emails) + "\n")
            else:
                file.write("No personal emails available.\n")
            file.write("\n")

            # Personal Phone Numbers
            file.write("=== Personal Phone Numbers ===\n")
            numbers = data.get("personal_numbers", [])
            if numbers:
                file.write(", ".join(numbers) + "\n")
            else:
                file.write("No personal phone numbers available.\n")
            file.write("\n")

            # Groups
            file.write("=== Groups ===\n")
            groups = data.get("groups", [])
            if groups:
                for group in groups:
                    file.write(f"Name: {group.get('name', 'Not available')}\n")
                    file.write(f"URL: {group.get('group_linkedin_url', 'Not available')}\n")
                    file.write("-" * 50 + "\n")
            else:
                file.write("No groups available.\n")
            file.write("\n")

            # Activities
            file.write("=== Activities ===\n")
            activities = data.get("activities", [])
            if activities:
                for activity in activities:
                    file.write(f"Title: {activity.get('title', 'Not available')}\n")
                    file.write(f"Link: {activity.get('link', 'Not available')}\n")
                    file.write(f"Status: {activity.get('activity_status', 'Not available')}\n")
                    file.write("-" * 50 + "\n")
            else:
                file.write("No activities available.\n")
            file.write("\n")

    except IOError as e:
        raise RuntimeError(f"Failed to write to output file {output_path}: {e}")