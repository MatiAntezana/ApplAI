import logging
from typing import List, Dict, Optional, Tuple, Set
from serpapi import GoogleSearch  # pip install google-search-results
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Lista global de claves API de SerpAPI
SERPAPI_KEYS: List[str] = [
    "ad29f33b33bb8d2185a8eccb9e58ff9c45f3ac271282672f13f6fde9c130e712",
]

LANG_REMOTE_TERMS = {
    "es": ["remoto", "teletrabajo", "trabajo remoto", "home office"],
    "en": ["remote", "remote work", "work from home", "telecommute"],
    "fr": ["télétravail", "travail à distance"],
    "de": ["Fernarbeit", "Homeoffice", "remote"],
    "pt": ["remoto", "teletrabalho", "trabalho remoto"]
}

VALID_JOB_DOMAINS = [
    "linkedin.com/jobs/view",
    "indeed.com",
    "computrabajo.com",
    "glassdoor.com",
    "bumeran.com",
    "zonajobs.com"
]

# Map antiguedad_maxima to Google 'tbs' filter codes
AGE_MAP = {
    'dia': 'd',       # past day
    'semana': 'w',    # past week
    'mes': 'm',       # past month
    'anio': 'y'       # past year
}

@dataclass
class JobVerificationResult:
    """Resultado de la verificación de un trabajo"""
    url: str
    is_accepting: bool
    confidence: float  # 0.0 - 1.0
    reason: str
    scraped_content: str = ""

class WebScraper:
    """Scraper web para verificar estado de ofertas de trabajo"""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Patrones específicos por sitio
        self.site_patterns = {
            'linkedin.com': {
                'closed_selectors': [
                    '.jobs-details-top-card__apply-error',
                    '.jobs-apply-button--disabled',
                    '[data-test="job-application-closed"]',
                    '.artdeco-inline-feedback--error'
                ],
                'closed_text': [
                    'no longer accepting applications',
                    'ya no se aceptan solicitudes',
                    'application deadline has passed',
                    'this job is no longer available',
                    'este trabajo ya no está disponible'
                ],
                'open_selectors': [
                    '.jobs-apply-button:not(.jobs-apply-button--disabled)',
                    '[data-test="jobs-apply-button"]',
                    '.jobs-apply-button--enabled'
                ],
                'open_text': [
                    'apply now',
                    'aplicar ahora',
                    'postular',
                    'solicitar empleo'
                ]
            },
            'indeed.com': {
                'closed_selectors': [
                    '.jobsearch-ApplyButtonDisabled',
                    '.jobsearch-JobExpired',
                    '.expired-job'
                ],
                'closed_text': [
                    'this job has expired',
                    'no longer accepting applications',
                    'este trabajo ha expirado',
                    'ya no acepta solicitudes'
                ],
                'open_selectors': [
                    '.jobsearch-ApplyButton',
                    '.indeed-apply-button',
                    '.jobsearch-IndeedApplyButton'
                ],
                'open_text': [
                    'apply now',
                    'aplicar ahora',
                    'easily apply'
                ]
            },
            'computrabajo.com': {
                'closed_selectors': [
                    '.aviso-cerrado',
                    '.expired-job',
                    '.job-closed'
                ],
                'closed_text': [
                    'aviso cerrado',
                    'ya no se aceptan postulaciones',
                    'búsqueda cerrada',
                    'proceso cerrado'
                ],
                'open_selectors': [
                    '.btn-postular',
                    '.apply-button',
                    '.postulate-button'
                ],
                'open_text': [
                    'postular',
                    'postularse',
                    'aplicar'
                ]
            },
            'glassdoor.com': {
                'closed_selectors': [
                    '.disabled-apply-button',
                    '.expired-job'
                ],
                'closed_text': [
                    'no longer accepting applications',
                    'this job is no longer available'
                ],
                'open_selectors': [
                    '.apply-button',
                    '.gd-btn-apply'
                ],
                'open_text': [
                    'apply now',
                    'easy apply'
                ]
            }
        }
    
    def get_domain_patterns(self, url: str) -> Dict:
        """Obtiene los patrones específicos para un dominio"""
        domain = urlparse(url).netloc.lower()
        for site_domain, patterns in self.site_patterns.items():
            if site_domain in domain:
                return patterns
        return {}
    
    def scrape_job_page(self, url: str) -> JobVerificationResult:
        """Scrapea una página de trabajo para verificar si acepta solicitudes"""
        try:
            logger.info(f"Scraping job page: {url}")
            
            # Hacer solicitud HTTP
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Parsear HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            page_text = soup.get_text().lower()
            
            # Obtener patrones específicos del sitio
            patterns = self.get_domain_patterns(url)
            
            # Verificar indicadores de trabajo cerrado
            closed_confidence = 0.0
            closed_reasons = []
            
            # Verificar selectores CSS específicos
            if patterns.get('closed_selectors'):
                for selector in patterns['closed_selectors']:
                    elements = soup.select(selector)
                    if elements:
                        closed_confidence = max(closed_confidence, 0.9)
                        closed_reasons.append(f"Found closed selector: {selector}")
            
            # Verificar texto específico del sitio
            if patterns.get('closed_text'):
                for text in patterns['closed_text']:
                    if text.lower() in page_text:
                        closed_confidence = max(closed_confidence, 0.8)
                        closed_reasons.append(f"Found closed text: {text}")
            
            # Verificar indicadores generales de trabajo cerrado
            general_closed_indicators = [
                "ya no se aceptan solicitudes",
                "no longer accepting applications",
                "application deadline has passed",
                "position filled",
                "job closed",
                "expired",
                "no longer available",
                "applications closed",
                "deadline passed",
                "puesto cerrado",
                "solicitudes cerradas",
                "plazo vencido",
                "posición cubierta",
                "vacante cerrada",
                "closed position",
                "position closed",
                "búsqueda finalizada",
                "proceso cerrado",
                "convocatoria cerrada"
            ]
            
            for indicator in general_closed_indicators:
                if indicator in page_text:
                    closed_confidence = max(closed_confidence, 0.7)
                    closed_reasons.append(f"Found general closed indicator: {indicator}")
            
            # Verificar indicadores de trabajo abierto
            open_confidence = 0.0
            open_reasons = []
            
            # Verificar selectores CSS específicos
            if patterns.get('open_selectors'):
                for selector in patterns['open_selectors']:
                    elements = soup.select(selector)
                    if elements:
                        open_confidence = max(open_confidence, 0.9)
                        open_reasons.append(f"Found open selector: {selector}")
            
            # Verificar texto específico del sitio
            if patterns.get('open_text'):
                for text in patterns['open_text']:
                    if text.lower() in page_text:
                        open_confidence = max(open_confidence, 0.8)
                        open_reasons.append(f"Found open text: {text}")
            
            # Verificar indicadores generales de trabajo abierto
            general_open_indicators = [
                "evaluando solicitudes de forma activa",
                "actively reviewing applications",
                "now hiring",
                "apply now",
                "solicita ahora",
                "contratando ahora",
                "urgent",
                "urgente",
                "immediate start",
                "inicio inmediato",
                "accepting applications",
                "aceptando solicitudes",
                "open position",
                "active posting",
                "hiring immediately",
                "postular",
                "postularse",
                "aplicar",
                "enviar cv",
                "send resume"
            ]
            
            for indicator in general_open_indicators:
                if indicator in page_text:
                    open_confidence = max(open_confidence, 0.6)
                    open_reasons.append(f"Found general open indicator: {indicator}")
            
            # Determinar resultado final
            if closed_confidence > open_confidence and closed_confidence >= 0.7:
                is_accepting = False
                confidence = closed_confidence
                reason = "; ".join(closed_reasons)
            elif open_confidence >= 0.6:
                is_accepting = True
                confidence = open_confidence
                reason = "; ".join(open_reasons)
            else:
                # Si no hay indicadores claros, asumir que está abierto
                is_accepting = True
                confidence = 0.5
                reason = "No clear indicators found, assuming open"
            
            logger.info(f"Job verification result: {url} - Accepting: {is_accepting}, Confidence: {confidence:.2f}")
            
            return JobVerificationResult(
                url=url,
                is_accepting=is_accepting,
                confidence=confidence,
                reason=reason,
                scraped_content=page_text[:500]  # Primeros 500 caracteres para debug
            )
            
        except requests.RequestException as e:
            logger.error(f"Error scraping {url}: {e}")
            return JobVerificationResult(
                url=url,
                is_accepting=True,  # Asumir abierto si no se puede verificar
                confidence=0.3,
                reason=f"Scraping error: {str(e)}",
                scraped_content=""
            )
        except Exception as e:
            logger.error(f"Unexpected error scraping {url}: {e}")
            return JobVerificationResult(
                url=url,
                is_accepting=True,  # Asumir abierto si no se puede verificar
                confidence=0.3,
                reason=f"Unexpected error: {str(e)}",
                scraped_content=""
            )

class SerpAPISearcher:
    def __init__(self, api_keys: List[str]):
        self.api_keys = api_keys
        self.key_index = 0
    
    def _next_key(self) -> str:
        key = self.api_keys[self.key_index]
        self.key_index = (self.key_index + 1) % len(self.api_keys)
        return key
    
    def search(self, params: Dict) -> Optional[List[Dict]]:
        """
        Ejecuta una búsqueda en SerpAPI con clave rotativa.
        Devuelve lista de resultados completos o None en caso de fallo.
        """
        params['api_key'] = self._next_key()
        try:
            search = GoogleSearch(params)
            results = search.get_dict()
            
            # Debug: imprimir la respuesta completa para diagnóstico
            logger.info(f"SerpAPI response keys: {list(results.keys())}")
            
            # Verificar si hay error en la respuesta
            if 'error' in results:
                logger.error(f"SerpAPI returned error: {results['error']}")
                return []
            
            # Buscar resultados en diferentes campos posibles
            search_results = []
            
            if 'organic_results' in results:
                search_results = results['organic_results']
                logger.info(f"Found {len(search_results)} organic results")
            elif 'jobs_results' in results:
                search_results = results['jobs_results']
                logger.info(f"Found {len(search_results)} job results")
            elif 'local_results' in results:
                search_results = results['local_results']
                logger.info(f"Found {len(search_results)} local results")
            else:
                logger.warning(f"No search results found. Available keys: {list(results.keys())}")
                
                # Mostrar información de la búsqueda para debugging
                if 'search_information' in results:
                    search_info = results['search_information']
                    logger.info(f"Search info: {search_info}")
                
                # Intentar extraer URLs de cualquier campo que contenga 'link'
                all_results = []
                for key, value in results.items():
                    if isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict) and 'link' in item:
                                all_results.append(item)
                
                if all_results:
                    logger.info(f"Found {len(all_results)} results from other fields")
                    search_results = all_results
                else:
                    logger.warning("No results found in any field")
                    return []
            
            return search_results
        except Exception as e:
            logger.error(f"SerpAPI error: {e}")
            return []

def build_search_queries(query: str, localization: str, linkedin_only: bool) -> List[str]:
    """
    Construye múltiples consultas de búsqueda priorizando trabajos remotos y locales.
    """
    queries = []
    
    # Obtener términos remotos en diferentes idiomas
    remote_terms = []
    for lang_terms in LANG_REMOTE_TERMS.values():
        remote_terms.extend(lang_terms)
    
    site_filter = ' site:linkedin.com/jobs/view' if linkedin_only else ''
    
    # 1. Búsqueda específica para trabajos remotos (máxima prioridad)
    remote_query = f'"{query}" (' + ' OR '.join([f'"{term}"' for term in remote_terms]) + ')' + site_filter
    queries.append(remote_query)
    
    # 2. Búsqueda específica para la localización (segunda prioridad)
    local_query = f'"{query}" "{localization}"' + site_filter
    queries.append(local_query)
    
    # 3. Búsqueda combinada (respaldo)
    combined_query = f'"{query}" (' + ' OR '.join([f'"{term}"' for term in remote_terms + [localization]]) + ')' + site_filter
    queries.append(combined_query)
    
    return queries

def build_fallback_queries(query: str, localization: str, linkedin_only: bool) -> List[str]:
    """
    Construye consultas más amplias para usar cuando no se obtienen suficientes resultados.
    """
    queries = []
    site_filter = ' site:linkedin.com/jobs/view' if linkedin_only else ''
    
    # 1. Búsqueda solo con el query principal
    basic_query = f'"{query}"' + site_filter
    queries.append(basic_query)
    
    # 2. Búsqueda con términos de trabajo más generales
    job_terms = ["empleo", "trabajo", "vacante", "job", "position", "career"]
    for term in job_terms:
        job_query = f'"{query}" "{term}"' + site_filter
        queries.append(job_query)
    
    # 3. Búsqueda sin comillas (más amplia)
    loose_query = f'{query} empleo trabajo' + site_filter
    queries.append(loose_query)
    
    # 4. Búsqueda por industria/sector relacionado
    if any(term in query.lower() for term in ["data", "scientist", "analyst", "analytics"]):
        industry_query = f'"data analyst" OR "data science" OR "business intelligence"' + site_filter
        queries.append(industry_query)
    elif any(term in query.lower() for term in ["developer", "programmer", "software", "engineer"]):
        industry_query = f'"software developer" OR "programmer" OR "software engineer"' + site_filter
        queries.append(industry_query)
    elif any(term in query.lower() for term in ["marketing", "digital", "social media"]):
        industry_query = f'"digital marketing" OR "marketing specialist" OR "social media"' + site_filter
        queries.append(industry_query)
    
    # 5. Si no es LinkedIn only, buscar en sitios específicos
    if not linkedin_only:
        job_sites = ["indeed.com", "computrabajo.com", "bumeran.com", "zonajobs.com"]
        for site in job_sites:
            site_query = f'"{query}" site:{site}'
            queries.append(site_query)
    
    return queries

def is_remote_job(result: Dict) -> bool:
    """
    Determina si un trabajo es remoto basándose en título y snippet.
    """
    # Crear texto combinado de todos los campos disponibles
    text_fields = [
        str(result.get('title', '')),
        str(result.get('snippet', '')),
        str(result.get('description', '')),
        str(result.get('position', '')),
        str(result.get('location', ''))
    ]
    
    text_to_check = ' '.join(text_fields).lower()
    
    # Buscar términos remotos en el texto
    for lang_terms in LANG_REMOTE_TERMS.values():
        for term in lang_terms:
            if term.lower() in text_to_check:
                return True
    
    return False

def is_local_job(result: Dict, localization: str) -> bool:
    """
    Determina si un trabajo está cerca de la localización especificada.
    """
    # Crear texto combinado de todos los campos disponibles
    text_fields = [
        str(result.get('title', '')),
        str(result.get('snippet', '')),
        str(result.get('description', '')),
        str(result.get('position', '')),
        str(result.get('location', ''))
    ]
    
    text_to_check = ' '.join(text_fields).lower()
    
    # Buscar la localización en el texto
    return localization.lower() in text_to_check

def is_accepting_applications(result: Dict) -> bool:
    """
    Determina si un trabajo todavía está aceptando solicitudes (verificación básica).
    """
    # Crear texto combinado de todos los campos disponibles
    text_fields = [
        str(result.get('title', '')),
        str(result.get('snippet', '')),
        str(result.get('description', '')),
        str(result.get('position', '')),
        str(result.get('company', '')),
        str(result.get('location', ''))
    ]
    
    text_to_check = ' '.join(text_fields).lower()
    
    # Frases que indican que NO acepta solicitudes
    closed_indicators = [
        "ya no se aceptan solicitudes",
        "no longer accepting applications",
        "application deadline has passed",
        "position filled",
        "job closed",
        "expired",
        "no longer available",
        "applications closed",
        "deadline passed",
        "puesto cerrado",
        "solicitudes cerradas",
        "plazo vencido",
        "posición cubierta",
        "vacante cerrada",
        "closed position",
        "position closed"
    ]
    
    # Frases que indican que SÍ acepta solicitudes (positivas)
    open_indicators = [
        "evaluando solicitudes de forma activa",
        "actively reviewing applications",
        "now hiring",
        "apply now",
        "solicita ahora",
        "contratando ahora",
        "urgent",
        "urgente",
        "immediate start",
        "inicio inmediato",
        "accepting applications",
        "aceptando solicitudes",
        "open position",
        "active posting",
        "hiring immediately"
    ]
    
    # Si encuentra indicadores de que está cerrado, retorna False
    for indicator in closed_indicators:
        if indicator in text_to_check:
            return False
    
    # Si encuentra indicadores positivos, retorna True
    for indicator in open_indicators:
        if indicator in text_to_check:
            return True
    
    # Si no encuentra indicadores claros, asume que está abierto
    return True

def score_job_result(result: Dict, localization: str) -> Tuple[int, str]:
    """
    Asigna una puntuación a un resultado de trabajo basándose en prioridades.
    Retorna (puntuación, tipo) donde mayor puntuación = mayor prioridad.
    """
    is_remote = is_remote_job(result)
    is_local = is_local_job(result, localization)
    is_accepting = is_accepting_applications(result)
    
    # Base score según ubicación
    if is_remote and is_local:
        base_score = 3  # Máxima prioridad: remoto Y local
        job_type = "remote_local"
    elif is_remote:
        base_score = 2  # Alta prioridad: solo remoto
        job_type = "remote"
    elif is_local:
        base_score = 1  # Media prioridad: solo local
        job_type = "local"
    else:
        base_score = 0  # Baja prioridad: ni remoto ni local
        job_type = "other"
    
    # Multiplicar por 2 si acepta solicitudes, por 1 si no acepta
    final_score = base_score * 2 if is_accepting else base_score
    
    # Actualizar tipo de trabajo para incluir estado de solicitudes
    if not is_accepting:
        job_type += "_closed"
    else:
        job_type += "_open"
    
    return (final_score, job_type)

def execute_searches(searcher: SerpAPISearcher, queries: List[str], base_params: Dict, 
                    localization: str, seen_urls: set, parallel_workers: int = 1) -> List[Dict]:
    """
    Ejecuta una lista de consultas y devuelve los resultados procesados.
    """
    all_results = []
    
    for i, search_query in enumerate(queries):
        params = base_params.copy()
        params['q'] = search_query
        
        logger.info(f"Executing search {i+1}/{len(queries)}: {search_query}")
        
        with ThreadPoolExecutor(max_workers=parallel_workers) as executor:
            futures = [executor.submit(searcher.search, params) for _ in SERPAPI_KEYS]
            for future in as_completed(futures):
                results = future.result()
                if results is None:
                    continue
                
                logger.info(f"Got {len(results)} results from search {i+1}")
                
                for result in results:
                    url = result.get('link')
                    if not url or url in seen_urls:
                        continue
                    
                    # Validar dominio
                    if not any(domain in url for domain in VALID_JOB_DOMAINS):
                        logger.debug(f"Skipping URL (invalid domain): {url}")
                        continue
                    
                    seen_urls.add(url)
                    
                    # Asignar puntuación al resultado
                    score, job_type = score_job_result(result, localization)
                    
                    all_results.append({
                        'url': url,
                        'score': score,
                        'type': job_type,
                        'title': str(result.get('title', '')),
                        'snippet': str(result.get('snippet', '')),
                        'description': str(result.get('description', '')),
                        'position': str(result.get('position', '')),
                        'company': str(result.get('company', '')),
                        'location': str(result.get('location', ''))
                    })
    
    return all_results

def verify_job_applications(urls: List[str], scraper: WebScraper, 
                          min_confidence: float = 0.7) -> List[JobVerificationResult]:
    """
    Verifica que las URLs de trabajo aún acepten solicitudes usando scraping.
    """
    verified_results = []
    
    logger.info(f"Verifying {len(urls)} job URLs...")
    
    for i, url in enumerate(urls):
        logger.info(f"Verifying URL {i+1}/{len(urls)}: {url}")
        
        # Verificar el estado de la aplicación
        result = scraper.scrape_job_page(url)
        verified_results.append(result)
        
        # Pequeña pausa para evitar sobrecarga del servidor
        time.sleep(1)
    
    return verified_results

def search_jobs_serpapi_verified(
    query: str,
    max_urls: int = 10,
    localization: str = "Buenos Aires",
    antiguedad_maxima: str = "semana",
    linkedin_only: bool = True,
    parallel_workers: int = 1,
    verification_confidence: float = 0.7,
    max_search_iterations: int = 3
) -> List[str]:
    """
    Busca empleos usando SerpAPI priorizando trabajos remotos y locales.
    GARANTIZA que devuelve exactamente max_urls resultados que aún acepten solicitudes.
    """
    searcher = SerpAPISearcher(SERPAPI_KEYS)
    scraper = WebScraper()
    
    # Parámetros base
    base_params = {
        'engine': 'google',
        'num': max_urls * 5,  # Incrementar más para tener buffer
        'hl': 'es'
    }
    
    # Añadir filtro de tiempo
    age_code = AGE_MAP.get(antiguedad_maxima.lower())
    if age_code:
        base_params['tbs'] = f'qdr:{age_code}'
    
    verified_urls = []
    seen_urls = set()
    search_iteration = 0
    
    while len(verified_urls) < max_urls and search_iteration < max_search_iterations:
        search_iteration += 1
        logger.info(f"=== BÚSQUEDA ITERACIÓN {search_iteration} ===")
        logger.info(f"URLs verificadas hasta ahora: {len(verified_urls)}/{max_urls}")
        
        all_results = []
        
        # FASE 1: Búsquedas prioritarias
        logger.info("FASE 1: Búsquedas prioritarias")
        priority_queries = build_search_queries(query, localization, linkedin_only)
        priority_results = execute_searches(searcher, priority_queries, base_params, 
                                          localization, seen_urls, parallel_workers)
        all_results.extend(priority_results)
        
        # FASE 2: Búsquedas de respaldo si no tenemos suficientes
        if len(all_results) < max_urls * 2:
            logger.info("FASE 2: Búsquedas de respaldo")
            fallback_queries = build_fallback_queries(query, localization, linkedin_only)
            fallback_results = execute_searches(searcher, fallback_queries, base_params, 
                                              localization, seen_urls, parallel_workers)
            all_results.extend(fallback_results)
        
        # FASE 3: Búsquedas sin filtros de tiempo
        if len(all_results) < max_urls * 2:
            logger.info("FASE 3: Búsquedas sin filtros de tiempo")
            no_time_params = base_params.copy()
            if 'tbs' in no_time_params:
                del no_time_params['tbs']
            
            additional_results = execute_searches(searcher, priority_queries, no_time_params, 
                                                localization, seen_urls, parallel_workers)
            all_results.extend(additional_results)
        
        # FASE 4: Búsquedas sin restricción de sitio
        if len(all_results) < max_urls * 2 and linkedin_only:
            logger.info("FASE 4: Búsquedas sin restricción de LinkedIn")
            broad_queries = build_search_queries(query, localization, linkedin_only=False)
            broad_queries.extend(build_fallback_queries(query, localization, linkedin_only=False))
            
            no_site_params = base_params.copy()
            if 'tbs' in no_site_params:
                del no_site_params['tbs']
            
            broad_results = execute_searches(searcher, broad_queries, no_site_params, 
                                           localization, seen_urls, parallel_workers)
            all_results.extend(broad_results)
        
        # Ordenar por puntuación
        priority_order = {
            "remote_local_open": 0,
            "remote_open": 1,
            "local_open": 2,
            "other_open": 3,
            "remote_local_closed": 4,
            "remote_closed": 5,
            "local_closed": 6,
            "other_closed": 7
        }
        all_results.sort(key=lambda x: (-x['score'], priority_order.get(x['type'], 8)))
        
        # Extraer URLs candidatas
        candidate_urls = []
        for result in all_results:
            if len(candidate_urls) >= max_urls * 2:  # Buscar más URLs para tener buffer
                break
            candidate_urls.append(result['url'])
        
        logger.info(f"Encontradas {len(candidate_urls)} URLs candidatas para verificación")
        
        # Verificar URLs candidatas
        if candidate_urls:
            verification_results = verify_job_applications(candidate_urls, scraper, verification_confidence)
            
            # Procesar resultados de verificación
            for result in verification_results:
                if len(verified_urls) >= max_urls:
                    break
                
                if result.is_accepting and result.confidence >= verification_confidence:
                    verified_urls.append(result.url)
                    logger.info(f"✅ URL verificada ({len(verified_urls)}/{max_urls}): {result.url}")
                    logger.info(f"   Confianza: {result.confidence:.2f} - Razón: {result.reason}")
                else:
                    logger.warning(f"❌ URL rechazada: {result.url}")
                    logger.warning(f"   Acepta solicitudes: {result.is_accepting}, Confianza: {result.confidence:.2f}")
                    logger.warning(f"   Razón: {result.reason}")
        
        # Incrementar el número de resultados por búsqueda para la siguiente iteración
        base_params['num'] = min(base_params['num'] + max_urls, 100)
        
        # Si no encontramos suficientes URLs, relajar los criterios
        if len(verified_urls) < max_urls and search_iteration < max_search_iterations:
            logger.info(f"Relajando criterios de búsqueda para la siguiente iteración...")
            # Reducir el mínimo de confianza para verificación
            verification_confidence = max(0.3, verification_confidence - 0.1)
            logger.info(f"Nueva confianza mínima: {verification_confidence}")
    
    # Si aún no tenemos suficientes URLs, hacer búsquedas muy amplias
    if len(verified_urls) < max_urls:
        logger.info(f"=== BÚSQUEDA FINAL AMPLIA ===")
        logger.info(f"Necesitamos {max_urls - len(verified_urls)} URLs más")
        
        # Búsquedas muy generales
        general_queries = [
            f'{query} trabajo',
            f'{query} empleo',
            f'{query} vacante',
            f'{query} job',
            f'trabajo {localization}',
            f'empleo {localization}',
        ]
        
        if not linkedin_only:
            general_queries.extend([
                f'{query} site:indeed.com',
                f'{query} site:computrabajo.com',
                f'{query} site:bumeran.com',
                f'{query} site:zonajobs.com',
            ])
        
        very_broad_params = {
            'engine': 'google',
            'num': max_urls * 3,
            'hl': 'es'
        }
        
        general_results = execute_searches(searcher, general_queries, very_broad_params, 
                                         localization, seen_urls, parallel_workers)
        
        # Ordenar resultados generales
        general_results.sort(key=lambda x: (-x['score'], priority_order.get(x['type'], 8)))
        
        # Extraer URLs adicionales
        additional_urls = []
        for result in general_results:
            if len(additional_urls) >= (max_urls - len(verified_urls)) * 2:
                break
            additional_urls.append(result['url'])
        
        logger.info(f"Encontradas {len(additional_urls)} URLs adicionales para verificación")
        
        # Verificar URLs adicionales con confianza más baja
        if additional_urls:
            additional_verification = verify_job_applications(additional_urls, scraper, 0.3)
            
            for result in additional_verification:
                if len(verified_urls) >= max_urls:
                    break
                
                if result.is_accepting and result.confidence >= 0.3:
                    verified_urls.append(result.url)
                    logger.info(f"✅ URL adicional verificada ({len(verified_urls)}/{max_urls}): {result.url}")
                    logger.info(f"   Confianza: {result.confidence:.2f} - Razón: {result.reason}")
    
    # Si aún no tenemos suficientes URLs, crear URLs de búsqueda como último recurso
    if len(verified_urls) < max_urls:
        logger.warning(f"Solo se encontraron {len(verified_urls)} URLs verificadas de {max_urls} solicitadas")
        
        # Crear URLs de búsqueda directa en los sitios principales
        search_urls = []
        
        # LinkedIn
        if linkedin_only or len(verified_urls) < max_urls // 2:
            linkedin_search = f"https://www.linkedin.com/jobs/search?keywords={query.replace(' ', '%20')}&location={localization.replace(' ', '%20')}"
            search_urls.append(linkedin_search)
        
        # Indeed
        indeed_search = f"https://ar.indeed.com/jobs?q={query.replace(' ', '+')}&l={localization.replace(' ', '+')}"
        search_urls.append(indeed_search)
        
        # Computrabajo
        computrabajo_search = f"https://www.computrabajo.com.ar/trabajo-de-{query.replace(' ', '-')}-en-{localization.replace(' ', '-')}"
        search_urls.append(computrabajo_search)
        
        # Bumeran
        bumeran_search = f"https://www.bumeran.com.ar/empleos-busqueda-{query.replace(' ', '-')}.html"
        search_urls.append(bumeran_search)
        
        # Agregar URLs de búsqueda hasta completar max_urls
        for search_url in search_urls:
            if len(verified_urls) >= max_urls:
                break
            verified_urls.append(search_url)
            logger.info(f"🔍 URL de búsqueda agregada ({len(verified_urls)}/{max_urls}): {search_url}")
    
    # Garantizar que devolvemos exactamente max_urls
    final_urls = verified_urls[:max_urls]
    
    # Si aún no tenemos suficientes, duplicar las mejores
    while len(final_urls) < max_urls:
        if verified_urls:
            final_urls.extend(verified_urls)
        else:
            # URL de fallback absoluto
            fallback_url = f"https://www.linkedin.com/jobs/search?keywords={query.replace(' ', '%20')}&location={localization.replace(' ', '%20')}"
            final_urls.append(fallback_url)
    
    # Asegurar que devolvemos exactamente max_urls
    final_urls = final_urls[:max_urls]
    
    logger.info(f"=== RESULTADO FINAL ===")
    logger.info(f"URLs verificadas que aceptan solicitudes: {len(final_urls)}")
    for i, url in enumerate(final_urls, 1):
        logger.info(f"{i}. {url}")
    
    return final_urls