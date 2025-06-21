import requests
import json
import time
import csv
from datetime import datetime
import re
from typing import Dict, List, Optional
from urllib.parse import urlparse
import os

def validar_nombre_archivo(filename: str) -> str:
    # Reemplaza caracteres no válidos con guiones bajos
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Elimina espacios al inicio y final
    cleaned = cleaned.strip()
    return cleaned

class LinkedInJobScraperByURL:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://nubela.co/proxycurl/api"
        self.headers = {'Authorization': f'Bearer {api_key}'}
        self.request_delay = 1  # Delay entre requests en segundos
    
    def validar_url_linkedin_job(self, url: str) -> bool:
        """
        Valida si la URL es de un trabajo de LinkedIn
        """
        parsed_url = urlparse(url)
        return (
            parsed_url.netloc in ['linkedin.com', 'www.linkedin.com'] and
            '/jobs/view/' in parsed_url.path
        )
    
    def obtener_detalle_trabajo_completo(self, job_url: str) -> Dict:
        """
        Obtiene TODOS los detalles posibles de un trabajo específico por URL
        """
        if not self.validar_url_linkedin_job(job_url):
            raise ValueError("La URL no es válida. Debe ser una URL de trabajo de LinkedIn (ej: https://linkedin.com/jobs/view/12345)")
        
        url = f"{self.base_url}/linkedin/job"
        
        params = {'url': job_url}
        
        try:
            print(f"🔍 Obteniendo detalles del trabajo: {job_url}")
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            time.sleep(self.request_delay)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error obteniendo detalles del trabajo: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Código de respuesta: {e.response.status_code}")
                print(f"Contenido de respuesta: {e.response.text}")
            return {}
    
    def obtener_info_empresa(self, company_url: str) -> Dict:
        """
        Obtiene información detallada de la empresa
        """
        if not company_url:
            return {}
            
        url = f"{self.base_url}/linkedin/company"
        params = {'url': company_url}
        
        try:
            print(f"🏢 Obteniendo información de la empresa...")
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            time.sleep(self.request_delay)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Error obteniendo info de empresa: {e}")
            return {}
    
    def obtener_perfil_reclutador(self, recruiter_url: str) -> Dict:
        """
        Obtiene información del reclutador/hiring manager
        """
        if not recruiter_url:
            return {}
            
        url = f"{self.base_url}/linkedin/person"
        params = {'url': recruiter_url}
        
        try:
            print(f"👤 Obteniendo información del reclutador...")
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            time.sleep(self.request_delay)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Error obteniendo perfil reclutador: {e}")
            return {}
    
    def extraer_skills_de_descripcion(self, descripcion: str) -> List[str]:
        """
        Extrae skills técnicas de la descripción usando regex
        """
        if not descripcion:
            return []
            
        skills_patterns = [
            # Lenguajes de programación
            r'\b(Python|Java|JavaScript|TypeScript|C\+\+|C#|PHP|Ruby|Go|Rust|Swift|Kotlin|Scala|R|MATLAB|Perl|Haskell|Clojure|Dart|Elixir|F#|Groovy|Julia|Lua|Objective-C|Pascal|Prolog|Shell|VBA|Visual Basic)\b',
            
            # Frameworks y librerías
            r'\b(React|Angular|Vue\.js|Node\.js|Django|Flask|Spring|Laravel|Rails|Express|FastAPI|Symfony|CodeIgniter|Zend|CakePHP|Yii|Meteor|Ember|Backbone|jQuery|Bootstrap|Tailwind|Material-UI|Ant Design|Semantic UI|Foundation)\b',
            
            # Bases de datos
            r'\b(MySQL|PostgreSQL|MongoDB|Redis|SQLite|Oracle|SQL Server|MariaDB|Cassandra|CouchDB|Neo4j|InfluxDB|DynamoDB|Firestore|BigQuery|Snowflake|Redshift|Elasticsearch|Solr)\b',
            
            # Cloud y DevOps
            r'\b(AWS|Azure|GCP|Google Cloud|Docker|Kubernetes|Jenkins|GitLab CI|GitHub Actions|Terraform|Ansible|Chef|Puppet|Vagrant|Nginx|Apache|IIS|Load Balancer|CDN|VPC|EC2|S3|Lambda|CloudFormation)\b',
            
            # Herramientas de desarrollo
            r'\b(Git|GitHub|GitLab|Bitbucket|SVN|Visual Studio Code|IntelliJ|Eclipse|Xcode|Android Studio|Postman|Insomnia|Swagger|Jira|Confluence|Trello|Asana|Slack|Teams|Zoom|Figma|Sketch|Adobe XD|Photoshop|Illustrator)\b',
            
            # Metodologías y conceptos
            r'\b(Agile|Scrum|Kanban|DevOps|CI/CD|TDD|BDD|DDD|SOLID|REST|GraphQL|API|Microservices|Serverless|Machine Learning|Deep Learning|AI|Artificial Intelligence|Data Science|Big Data|Analytics|Statistics|ETL|Data Pipeline|Data Warehouse|Business Intelligence|Cybersecurity|Blockchain|IoT|AR|VR|Mobile Development|Web Development|Full Stack|Frontend|Backend|QA|Testing|Automation|Performance Testing|Load Testing|Security Testing|Unit Testing|Integration Testing|E2E Testing)\b',
            
            # Sistemas operativos
            r'\b(Linux|Ubuntu|CentOS|RedHat|Debian|Windows|macOS|Unix|FreeBSD)\b',
            
            # Análisis y visualización
            r'\b(Tableau|Power BI|Excel|Google Sheets|Looker|QlikView|D3\.js|Chart\.js|Matplotlib|Seaborn|Plotly|ggplot2|Pandas|NumPy|SciPy|TensorFlow|PyTorch|Keras|Scikit-learn|OpenCV|NLTK|SpaCy)\b'
        ]
        
        skills = set()
        for pattern in skills_patterns:
            matches = re.findall(pattern, descripcion, re.IGNORECASE)
            skills.update(matches)
        
        return sorted(list(skills))
    
    def extraer_requisitos_experiencia(self, descripcion: str) -> str:
        """
        Extrae información sobre años de experiencia requeridos
        """
        if not descripcion:
            return ""
            
        experiencia_patterns = [
            r'(\d+)\+?\s*(?:years?|años?)\s*(?:of\s*)?(?:experience|experiencia)',
            r'(?:minimum|mínimo|at least|al menos)\s*(\d+)\s*(?:years?|años?)',
            r'(\d+)-(\d+)\s*(?:years?|años?)\s*(?:experience|experiencia)',
            r'(?:senior|jr|junior|mid|middle|lead|principal)\s*(?:level|nivel)?'
        ]
        
        experiencias = []
        for pattern in experiencia_patterns:
            matches = re.findall(pattern, descripcion, re.IGNORECASE)
            experiencias.extend([str(match) if isinstance(match, str) else ' '.join(match) for match in matches])
        
        return '; '.join(set(experiencias)) if experiencias else ""
    
    def extraer_educacion_requerida(self, descripcion: str) -> str:
        """
        Extrae información sobre educación requerida
        """
        if not descripcion:
            return ""
            
        educacion_patterns = [
            r'\b(Bachelor|Licenciatura|Ingeniería|Master|Maestría|PhD|Doctorado|Diploma|Certificación|Título)\b.*?\b(degree|título|career|carrera)',
            r'\b(Computer Science|Sistemas|Informática|Engineering|Software|Mathematics|Matemáticas|Statistics|Estadística)\b',
            r'\b(University|Universidad|College|Instituto|Técnico)\b'
        ]
        
        educacion = []
        for pattern in educacion_patterns:
            matches = re.findall(pattern, descripcion, re.IGNORECASE)
            educacion.extend([' '.join(match) if isinstance(match, tuple) else match for match in matches])
        
        return '; '.join(set(educacion)) if educacion else ""
    
    def extraer_beneficios(self, descripcion: str) -> List[str]:
        """
        Extrae beneficios mencionados en la descripción
        """
        if not descripcion:
            return []
            
        beneficios_patterns = [
            r'\b(health insurance|seguro médico|dental|vision|life insurance|401k|retirement|jubilación|vacation|vacaciones|PTO|sick leave|parental leave|flexible schedule|remote work|trabajo remoto|home office|stock options|equity|bonus|bono|training|capacitación|education|educación|gym|fitness|lunch|almuerzo|snacks|coffee|café|parking|estacionamiento|transportation|transporte|relocation|reubicación)\b'
        ]
        
        beneficios = set()
        for pattern in beneficios_patterns:
            matches = re.findall(pattern, descripcion, re.IGNORECASE)
            beneficios.update(matches)
        
        return sorted(list(beneficios))
    
    def procesar_trabajo_completo(self, job_data: Dict) -> Dict:
        """
        Procesa y estructura toda la información posible de un trabajo
        """
        descripcion = job_data.get('job_description', '')
        
        # Información básica del trabajo
        trabajo_completo = {
            # === INFORMACIÓN BÁSICA ===
            'job_id': job_data.get('job_id', ''),
            'job_title': job_data.get('job_title', ''),
            'job_url': job_data.get('job_url', ''),
            'apply_url': job_data.get('apply_url', ''),
            
            # === DESCRIPCIÓN Y CONTENIDO ===
            'job_description': descripcion,
            'job_description_html': job_data.get('job_description_html', ''),
            'job_criteria': job_data.get('job_criteria', {}),
            
            # === INFORMACIÓN TEMPORAL ===
            'listed_at': job_data.get('listed_at', ''),
            'expiry_date': job_data.get('expiry_date', ''),
            'posted_date': job_data.get('posted_date', ''),
            'original_listed_time': job_data.get('original_listed_time', ''),
            'scraped_at': datetime.now().isoformat(),
            
            # === UBICACIÓN DETALLADA ===
            'location': job_data.get('location', {}),
            'location_name': job_data.get('location', {}).get('name', ''),
            'location_country': job_data.get('location', {}).get('country', ''),
            'location_city': job_data.get('location', {}).get('city', ''),
            'location_state': job_data.get('location', {}).get('state', ''),
            'location_postal_code': job_data.get('location', {}).get('postal_code', ''),
            'remote_allowed': job_data.get('remote_allowed', False),
            
            # === DETALLES DEL EMPLEO ===
            'employment_type': job_data.get('employment_type', ''),
            'job_function': job_data.get('job_function', []),
            'industries': job_data.get('industries', []),
            'seniority_level': job_data.get('seniority_level', ''),
            'total_applicants': job_data.get('total_applicants', 0),
            'job_state': job_data.get('job_state', ''),
            'job_posting_language': job_data.get('job_posting_language', ''),
            
            # === SALARIO Y BENEFICIOS ===
            'salary': job_data.get('salary', {}),
            'salary_min': job_data.get('salary', {}).get('min', 0) if job_data.get('salary') else 0,
            'salary_max': job_data.get('salary', {}).get('max', 0) if job_data.get('salary') else 0,
            'salary_currency': job_data.get('salary', {}).get('currency', '') if job_data.get('salary') else '',
            'salary_period': job_data.get('salary', {}).get('period', '') if job_data.get('salary') else '',
            'benefits': job_data.get('benefits', []),
            'extracted_benefits': self.extraer_beneficios(descripcion),
            
            # === INFORMACIÓN DE LA EMPRESA ===
            'company': job_data.get('company', {}),
            'company_name': job_data.get('company', {}).get('name', ''),
            'company_url': job_data.get('company', {}).get('url', ''),
            'company_logo': job_data.get('company', {}).get('logo', ''),
            'company_industry': job_data.get('company', {}).get('industry', ''),
            'company_size': job_data.get('company', {}).get('company_size', ''),
            'company_headquarters': job_data.get('company', {}).get('headquarters', ''),
            'company_founded': job_data.get('company', {}).get('founded', ''),
            'company_specialties': job_data.get('company', {}).get('specialties', []),
            'company_follower_count': job_data.get('company', {}).get('follower_count', 0),
            
            # === RECLUTADOR/HIRING MANAGER ===
            'hiring_team': job_data.get('hiring_team', []),
            'poster': job_data.get('poster', {}),
            'poster_name': job_data.get('poster', {}).get('name', ''),
            'poster_title': job_data.get('poster', {}).get('title', ''),
            'poster_url': job_data.get('poster', {}).get('url', ''),
            
            # === SKILLS Y REQUISITOS EXTRAÍDOS ===
            'extracted_skills': self.extraer_skills_de_descripcion(descripcion),
            'required_experience': self.extraer_requisitos_experiencia(descripcion),
            'education_requirements': self.extraer_educacion_requerida(descripcion),
            
            # === MÉTRICAS Y ANÁLISIS ===
            'job_description_length': len(descripcion),
            'word_count': len(descripcion.split()) if descripcion else 0,
            'application_deadline': job_data.get('application_deadline', ''),
            'easy_apply': job_data.get('easy_apply', False),
            'application_url': job_data.get('application_url', ''),
        }
        
        return trabajo_completo
    
    def scraper_por_url(self, 
                       job_url: str,
                       incluir_info_empresa: bool = True,
                       incluir_info_reclutador: bool = False) -> Dict:
        """
        Scraper completo que obtiene toda la información de un trabajo por su URL
        """
        print(f"🔍 Iniciando scraping de: {job_url}")
        
        # Obtener detalles completos del trabajo
        job_details = self.obtener_detalle_trabajo_completo(job_url)
        
        if not job_details:
            print("❌ No se pudieron obtener los detalles del trabajo")
            return {}
        
        # Procesar información completa
        print("⚙️ Procesando información del trabajo...")
        trabajo_completo = self.procesar_trabajo_completo(job_details)
        
        # Obtener información adicional de la empresa si se solicita
        if incluir_info_empresa and trabajo_completo['company_url']:
            empresa_info = self.obtener_info_empresa(trabajo_completo['company_url'])
            if empresa_info:
                trabajo_completo.update({
                    'company_description': empresa_info.get('description', ''),
                    'company_website': empresa_info.get('website', ''),
                    'company_phone': empresa_info.get('phone', ''),
                    'company_employees': empresa_info.get('company_size_on_linkedin', 0),
                    'company_employees_range': empresa_info.get('company_size', ''),
                    'company_type': empresa_info.get('company_type', ''),
                    'company_updates': empresa_info.get('updates', []),
                    'company_acquisitions': empresa_info.get('acquisitions', []),
                    'company_funding': empresa_info.get('funding_data', {}),
                    'company_similar_companies': empresa_info.get('similar_companies', []),
                    'company_locations': empresa_info.get('locations', []),
                    'company_technologies': empresa_info.get('technologies', [])
                })
        
        # Obtener información del reclutador si se solicita
        if incluir_info_reclutador and trabajo_completo['poster_url']:
            reclutador_info = self.obtener_perfil_reclutador(trabajo_completo['poster_url'])
            if reclutador_info:
                trabajo_completo.update({
                    'recruiter_headline': reclutador_info.get('headline', ''),
                    'recruiter_summary': reclutador_info.get('summary', ''),
                    'recruiter_location': reclutador_info.get('location', ''),
                    'recruiter_experience': reclutador_info.get('experiences', []),
                    'recruiter_education': reclutador_info.get('education', []),
                    'recruiter_skills': reclutador_info.get('skills', []),
                    'recruiter_languages': reclutador_info.get('languages', []),
                    'recruiter_connections': reclutador_info.get('connections', 0),
                    'recruiter_follower_count': reclutador_info.get('follower_count', 0)
                })
        
        print("✅ Scraping completado exitosamente!")
        return trabajo_completo
    
    def mostrar_resumen(self, trabajo: Dict):
        """
        Muestra un resumen del trabajo scrapeado
        """
        if not trabajo:
            print("❌ No hay información para mostrar")
            return
        
        print("\n" + "="*60)
        print("📋 RESUMEN DEL TRABAJO SCRAPEADO")
        print("="*60)
        
        print(f"🎯 Título: {trabajo.get('job_title', 'N/A')}")
        print(f"🏢 Empresa: {trabajo.get('company_name', 'N/A')}")
        print(f"📍 Ubicación: {trabajo.get('location_name', 'N/A')}")
        print(f"💼 Tipo: {trabajo.get('employment_type', 'N/A')}")
        print(f"📊 Nivel: {trabajo.get('seniority_level', 'N/A')}")
        print(f"👥 Aplicantes: {trabajo.get('total_applicants', 'N/A')}")
        
        if trabajo.get('salary_min') and trabajo.get('salary_max'):
            print(f"💰 Salario: ${trabajo['salary_min']:,} - ${trabajo['salary_max']:,} {trabajo.get('salary_currency', '')} ({trabajo.get('salary_period', '')})")
        
        print(f"📅 Publicado: {trabajo.get('listed_at', 'N/A')}")
        print(f"🔗 URL: {trabajo.get('job_url', 'N/A')}")
        
        # Skills extraídas
        skills = trabajo.get('extracted_skills', [])
        if skills:
            print(f"\n🛠️ Skills identificadas ({len(skills)}):")
            print(", ".join(skills[:15]))  # Mostrar primeras 15
            if len(skills) > 15:
                print(f"... y {len(skills) - 15} más")
        
        # Beneficios extraídos
        beneficios = trabajo.get('extracted_benefits', [])
        if beneficios:
            print(f"\n🎁 Beneficios identificados ({len(beneficios)}):")
            print(", ".join(beneficios))
        
        # Experiencia requerida
        if trabajo.get('required_experience'):
            print(f"\n📈 Experiencia: {trabajo['required_experience']}")
        
        # Educación requerida
        if trabajo.get('education_requirements'):
            print(f"🎓 Educación: {trabajo['education_requirements']}")
        
        print(f"\n📊 Longitud descripción: {trabajo.get('job_description_length', 0)} caracteres")
        print(f"📝 Palabras: {trabajo.get('word_count', 0)}")
        
        print("="*60)


    def guardar_txt(self, trabajo: Dict, filename: str = None):
        """
        Guarda la información del trabajo en un archivo de texto con formato organizado.
        """
        if not trabajo:
            print("❌ No hay trabajo para guardar")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        job_title_clean = re.sub(r'[^\w\s-]', '', trabajo.get('job_title', 'job')).strip()
        job_title_clean = re.sub(r'[-\s]+', '_', job_title_clean)[:30]

        if not filename:
            filename = f"linkedin_job_{job_title_clean}_{timestamp}.txt"
        else:
            # Asegura que el archivo termine en .txt
            if not filename.endswith('.txt'):
                filename += '.txt'
        
        # Valida el nombre del archivo
        filename = validar_nombre_archivo(filename)

        try:
            # Verifica permisos de escritura
            directory = os.path.dirname(filename) or '.'
            if not os.access(directory, os.W_OK):
                raise PermissionError(f"No se tienen permisos de escritura en el directorio: {directory}")

            with open(filename, 'w', encoding='utf-8') as file:
                # === INFORMACIÓN BÁSICA ===
                file.write("=== Información Básica ===\n")
                file.write(f"Título del trabajo: {trabajo.get('job_title', 'No disponible')}\n")
                file.write(f"ID del trabajo: {trabajo.get('job_id', 'No disponible')}\n")
                file.write(f"URL del trabajo: {trabajo.get('job_url', 'No disponible')}\n")
                file.write(f"URL de solicitud: {trabajo.get('apply_url', 'No disponible')}\n")
                file.write(f"Tipo de empleo: {trabajo.get('employment_type', 'No disponible')}\n")
                file.write(f"Nivel de experiencia: {trabajo.get('seniority_level', 'No disponible')}\n")
                file.write(f"Total de aplicantes: {trabajo.get('total_applicants', 'No disponible')}\n")
                file.write(f"Publicado: {trabajo.get('listed_at', 'No disponible')}\n")
                file.write(f"Fecha de expiración: {trabajo.get('expiry_date', 'No disponible')}\n")
                file.write(f"Permite trabajo remoto: {trabajo.get('remote_allowed', 'No disponible')}\n")
                file.write(f"Idioma de la publicación: {trabajo.get('job_posting_language', 'No disponible')}\n")
                file.write("\n")

                # === UBICACIÓN ===
                file.write("=== Ubicación ===\n")
                file.write(f"Ubicación: {trabajo.get('location_name', 'No disponible')}\n")
                file.write(f"Ciudad: {trabajo.get('location_city', 'No disponible')}\n")
                file.write(f"Estado: {trabajo.get('location_state', 'No disponible')}\n")
                file.write(f"País: {trabajo.get('location_country', 'No disponible')}\n")
                file.write(f"Código postal: {trabajo.get('location_postal_code', 'No disponible')}\n")
                file.write("\n")

                # === INFORMACIÓN DE LA EMPRESA ===
                file.write("=== Información de la Empresa ===\n")
                file.write(f"Nombre: {trabajo.get('company_name', 'No disponible')}\n")
                file.write(f"URL: {trabajo.get('company_url', 'No disponible')}\n")
                file.write(f"Logo: {trabajo.get('company_logo', 'No disponible')}\n")
                file.write(f"Industria: {trabajo.get('company_industry', 'No disponible')}\n")
                file.write(f"Tamaño: {trabajo.get('company_size', 'No disponible')}\n")
                file.write(f"Sede: {trabajo.get('company_headquarters', 'No disponible')}\n")
                file.write(f"Fundada: {trabajo.get('company_founded', 'No disponible')}\n")
                file.write(f"Descripción: {trabajo.get('company_description', 'No disponible')}\n")
                file.write(f"Website: {trabajo.get('company_website', 'No disponible')}\n")
                file.write(f"Teléfono: {trabajo.get('company_phone', 'No disponible')}\n")
                file.write(f"Empleados en LinkedIn: {trabajo.get('company_employees', 'No disponible')}\n")
                file.write(f"Rango de empleados: {trabajo.get('company_employees_range', 'No disponible')}\n")
                file.write(f"Tipo de empresa: {trabajo.get('company_type', 'No disponible')}\n")
                file.write(f"Especialidades: {', '.join(trabajo.get('company_specialties', [])) or 'No disponible'}\n")
                file.write(f"Seguidores: {trabajo.get('company_follower_count', 'No disponible')}\n")
                file.write("\n")

                # === SALARIO ===
                file.write("=== Salario ===\n")
                file.write(f"Mínimo: {trabajo.get('salary_min', 'No disponible')} {trabajo.get('salary_currency', '')}\n")
                file.write(f"Máximo: {trabajo.get('salary_max', 'No disponible')} {trabajo.get('salary_currency', '')}\n")
                file.write(f"Período: {trabajo.get('salary_period', 'No disponible')}\n")
                file.write("\n")

                # === DESCRIPCIÓN ===
                file.write("=== Descripción del Trabajo ===\n")
                file.write(f"{trabajo.get('job_description', 'No disponible')}\n")
                file.write(f"Longitud de descripción: {trabajo.get('job_description_length', 'No disponible')} caracteres\n")
                file.write(f"Conteo de palabras: {trabajo.get('word_count', 'No disponible')}\n")
                file.write("\n")

                # === SKILLS ===
                file.write("=== Habilidades Requeridas ===\n")
                skills = trabajo.get('extracted_skills', [])
                file.write(f"{', '.join(skills) if skills else 'No disponible'}\n")
                file.write(f"Total de habilidades: {len(skills)}\n")
                file.write("\n")

                # === EXPERIENCIA REQUERIDA ===
                file.write("=== Experiencia Requerida ===\n")
                file.write(f"{trabajo.get('required_experience', 'No disponible')}\n")
                file.write("\n")

                # === EDUCACIÓN REQUERIDA ===
                file.write("=== Educación Requerida ===\n")
                file.write(f"{trabajo.get('education_requirements', 'No disponible')}\n")
                file.write("\n")

                # === BENEFICIOS ===
                file.write("=== Beneficios ===\n")
                beneficios = trabajo.get('extracted_benefits', [])
                file.write(f"{', '.join(beneficios) if beneficios else 'No disponible'}\n")
                file.write(f"Total de beneficios: {len(beneficios)}\n")
                file.write("\n")

                # === RECLUTADOR ===
                file.write("=== Información del Reclutador ===\n")
                file.write(f"Nombre: {trabajo.get('poster_name', 'No disponible')}\n")
                file.write(f"Título: {trabajo.get('poster_title', 'No disponible')}\n")
                file.write(f"URL: {trabajo.get('poster_url', 'No disponible')}\n")
                file.write(f"Resumen: {trabajo.get('recruiter_summary', 'No disponible')}\n")
                file.write(f"Ubicación: {trabajo.get('recruiter_location', 'No disponible')}\n")
                file.write(f"Conexiones: {trabajo.get('recruiter_connections', 'No disponible')}\n")
                file.write(f"Seguidores: {trabajo.get('recruiter_follower_count', 'No disponible')}\n")
                file.write("\n")

                # === EXPERIENCIA DEL RECLUTADOR ===
                file.write("=== Experiencia del Reclutador ===\n")
                experiencias = trabajo.get('recruiter_experience', [])
                if experiencias:
                    for exp in experiencias:
                        file.write(f"Cargo: {exp.get('title', 'No disponible')}\n")
                        file.write(f"Empresa: {exp.get('company', 'No disponible')}\n")
                        file.write(f"URL Empresa: {exp.get('company_linkedin_profile_url', 'No disponible')}\n")
                        file.write(f"Desde: {exp.get('starts_at', 'No disponible')}\n")
                        file.write(f"Hasta: {exp.get('ends_at', 'No disponible')}\n")
                        file.write(f"Descripción: {exp.get('description', 'No disponible')}\n")
                        file.write(f"Ubicación: {exp.get('location', 'No disponible')}\n")
                        file.write("-" * 50 + "\n")
                else:
                    file.write("No hay experiencia disponible.\n")
                file.write("\n")

                # === EDUCACIÓN DEL RECLUTADOR ===
                file.write("=== Educación del Reclutador ===\n")
                educacion = trabajo.get('recruiter_education', [])
                if educacion:
                    for edu in educacion:
                        file.write(f"Institución: {edu.get('school', 'No disponible')}\n")
                        file.write(f"Grado: {edu.get('degree_name', 'No disponible')}\n")
                        file.write(f"Campo de estudio: {edu.get('field_of_study', 'No disponible')}\n")
                        file.write(f"Desde: {edu.get('starts_at', 'No disponible')}\n")
                        file.write(f"Hasta: {edu.get('ends_at', 'No disponible')}\n")
                        file.write(f"Descripción: {edu.get('description', 'No disponible')}\n")
                        file.write("-" * 50 + "\n")
                else:
                    file.write("No hay educación disponible.\n")
                file.write("\n")

                # === HABILIDADES DEL RECLUTADOR ===
                file.write("=== Habilidades del Reclutador ===\n")
                habilidades = trabajo.get('recruiter_skills', [])
                file.write(f"{', '.join(habilidades) if habilidades else 'No disponible'}\n")
                file.write("\n")

                # === IDIOMAS DEL RECLUTADOR ===
                file.write("=== Idiomas del Reclutador ===\n")
                idiomas = trabajo.get('recruiter_languages', [])
                file.write(f"{', '.join(idiomas) if idiomas else 'No disponible'}\n")
                file.write("\n")

            print(f"💾 Trabajo guardado en TXT: {filename}")
        except PermissionError as e:
            print(f"❌ Error de permisos: {e}")
        except Exception as e:
            print(f"❌ Error al guardar el archivo TXT: {str(e)}")
            import traceback
            print("Detalles del error:")
            traceback.print_exc()

    def guardar_trabajo(self, trabajo: Dict, formato: str = 'json', filename: str = None):
        """
        Guarda el trabajo en el formato especificado (json, csv o txt).
        """
        if not trabajo:
            print("❌ No hay trabajo para guardar")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        job_title_clean = re.sub(r'[^\w\s-]', '', trabajo.get('job_title', 'job')).strip()
        job_title_clean = re.sub(r'[-\s]+', '_', job_title_clean)[:30]

        if not filename:
            filename = f"linkedin_job_{job_title_clean}_{timestamp}"

        formato = formato.lower()
        try:
            if formato == 'json':
                filename = validar_nombre_archivo(filename + '.json')
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(trabajo, f, indent=2, ensure_ascii=False, default=str)
                print(f"💾 Trabajo guardado en JSON: {filename}")

            elif formato == 'csv':
                filename = validar_nombre_archivo(filename + '.csv')
                trabajo_flat = {}
                for key, value in trabajo.items():
                    if isinstance(value, (list, dict)):
                        trabajo_flat[key] = json.dumps(value, ensure_ascii=False)
                    else:
                        trabajo_flat[key] = value
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=trabajo_flat.keys())
                    writer.writeheader()
                    writer.writerow(trabajo_flat)
                print(f"💾 Trabajo guardado en CSV: {filename}")

            elif formato == 'txt':
                self.guardar_txt(trabajo, filename)

            else:
                print("❌ Formato no soportado. Use 'json', 'csv' o 'txt'")
        except Exception as e:
            print(f"❌ Error al guardar el trabajo: {str(e)}")
            import traceback
            print("Detalles del error:")
            traceback.print_exc()

# ============= EJEMPLO DE USO =============
if __name__ == "__main__":
    # Configurar tu API key
    API_KEY = "TM4VWAaCsKVJJarO4YsT0Q"
    
    # URL del trabajo de LinkedIn (ejemplo)
    JOB_URL = "https://www.linkedin.com/jobs/view/4201840839"
    
# Crear el scraper
    scraper = LinkedInJobScraperByURL(API_KEY)
    
    try:
        # Hacer scraping del trabajo
        trabajo = scraper.scraper_por_url(
            job_url=JOB_URL,
            incluir_info_empresa=True,
            incluir_info_reclutador=True
        )
        
        # Mostrar resumen
        scraper.mostrar_resumen(trabajo)
        
        # Guardar solo en TXT para probar
        scraper.guardar_trabajo(trabajo, 'txt')
        
    except ValueError as e:
        print(f"❌ Error de validación: {e}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()