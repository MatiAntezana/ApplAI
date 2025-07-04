
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
    # "ad29f33b33bb8d2185a8eccb9e58ff9c45f3ac271282672f13f6fde9c130e712",
    "debe90a698560d154bda75a96b129f2a6297e7fa7d952f60afca30b30cc9e9ff",
    "92fc302224c584b72afc5748a5d6c023f99c33ff9bed324f2d584dc2f8d74702"
]

LANG_REMOTE_TERMS = {
    "es": ["remoto", "teletrabajo", "trabajo remoto", "home office", "100% remoto", "desde casa"],
    "en": ["remote", "remote work", "work from home", "telecommute", "fully remote", "100% remote"],
    "fr": ["télétravail", "travail à distance", "100% télétravail"],
    "de": ["Fernarbeit", "Homeoffice", "remote", "100% remote"],
    "pt": ["remoto", "teletrabalho", "trabalho remoto", "100% remoto"]
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
    location_matches: Optional[bool] = None
    is_fully_remote: Optional[bool] = None

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

    def _verify_location_and_remoteness(self, page_text: str, localization: str) -> Tuple[bool, bool]:
        """
        Verifica si la localización coincide o si el trabajo es completamente remoto.
        """
        text = page_text.lower()
        
        # 1. Verificar si es completamente remoto
        all_remote_terms = [term for terms in LANG_REMOTE_TERMS.values() for term in terms]
        is_fully_remote = any(term in text for term in all_remote_terms)
        
        # 2. Verificar si la localización coincide
        # Simplificamos la localización, ej. "Buenos Aires, Argentina" -> "buenos aires"
        simple_localization = localization.split(',')[0].lower()
        location_matches = simple_localization in text
        
        logger.info(f"Location check: Match='{location_matches}' (Searching for '{simple_localization}'). Remote='{is_fully_remote}'")
        
        return location_matches, is_fully_remote

    def scrape_job_page(self, url: str, localization: str) -> JobVerificationResult:
        """Scrapea una página de trabajo para verificar si acepta solicitudes y la localización"""
        try:
            logger.info(f"Scraping job page: {url}")
            
            # Hacer solicitud HTTP
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Parsear HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            page_text = soup.get_text().lower()
            
            # Verificar localización y si es remoto
            location_matches, is_fully_remote = self._verify_location_and_remoteness(page_text, localization)
            
            # Obtener patrones específicos del sitio
            patterns = self.get_domain_patterns(url)
            
            # Verificar indicadores de trabajo cerrado
            closed_confidence = 0.0
            closed_reasons = []
            
            if patterns.get('closed_selectors'):
                for selector in patterns['closed_selectors']:
                    if soup.select(selector):
                        closed_confidence = max(closed_confidence, 0.9)
                        closed_reasons.append(f"Found closed selector: {selector}")
            
            if patterns.get('closed_text'):
                for text in patterns['closed_text']:
                    if text.lower() in page_text:
                        closed_confidence = max(closed_confidence, 0.8)
                        closed_reasons.append(f"Found closed text: {text}")

            general_closed_indicators = [
                "ya no se aceptan solicitudes", "no longer accepting applications", "application deadline has passed",
                "position filled", "job closed", "expired", "no longer available", "applications closed",
                "deadline passed", "puesto cerrado", "solicitudes cerradas", "plazo vencido",
                "posición cubierta", "vacante cerrada", "closed position", "position closed",
                "búsqueda finalizada", "proceso cerrado", "convocatoria cerrada"
            ]
            for indicator in general_closed_indicators:
                if indicator in page_text:
                    closed_confidence = max(closed_confidence, 0.7)
                    closed_reasons.append(f"Found general closed indicator: {indicator}")
            
            # Verificar indicadores de trabajo abierto
            open_confidence = 0.0
            open_reasons = []

            if patterns.get('open_selectors'):
                for selector in patterns['open_selectors']:
                    if soup.select(selector):
                        open_confidence = max(open_confidence, 0.9)
                        open_reasons.append(f"Found open selector: {selector}")
            
            if patterns.get('open_text'):
                for text in patterns['open_text']:
                    if text.lower() in page_text:
                        open_confidence = max(open_confidence, 0.8)
                        open_reasons.append(f"Found open text: {text}")

            general_open_indicators = [
                "evaluando solicitudes de forma activa", "actively reviewing applications", "now hiring",
                "apply now", "solicita ahora", "contratando ahora", "urgent", "urgente",
                "immediate start", "inicio inmediato", "accepting applications", "aceptando solicitudes",
                "open position", "active posting", "hiring immediately", "postular", "postularse",
                "aplicar", "enviar cv", "send resume"
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
                is_accepting = True
                confidence = 0.5
                reason = "No clear indicators found, assuming open"
            
            logger.info(f"Job verification result: {url} - Accepting: {is_accepting}, Confidence: {confidence:.2f}")
            
            return JobVerificationResult(
                url=url,
                is_accepting=is_accepting,
                confidence=confidence,
                reason=reason,
                scraped_content=page_text[:500],
                location_matches=location_matches,
                is_fully_remote=is_fully_remote
            )
            
        except requests.RequestException as e:
            logger.error(f"Error scraping {url}: {e}")
            return JobVerificationResult(url=url, is_accepting=True, confidence=0.3, reason=f"Scraping error: {str(e)}", scraped_content="", location_matches=None, is_fully_remote=None)
        except Exception as e:
            logger.error(f"Unexpected error scraping {url}: {e}")
            return JobVerificationResult(url=url, is_accepting=True, confidence=0.3, reason=f"Unexpected error: {str(e)}", scraped_content="", location_matches=None, is_fully_remote=None)

class SerpAPISearcher:
    def __init__(self, api_keys: List[str]):
        self.api_keys = api_keys
        self.key_index = 0
    
    def _next_key(self) -> str:
        key = self.api_keys[self.key_index]
        self.key_index = (self.key_index + 1) % len(self.api_keys)
        return key
    
    def search(self, params: Dict) -> Optional[List[Dict]]:
        params['api_key'] = self._next_key()
        try:
            search = GoogleSearch(params)
            results = search.get_dict()
            
            if 'error' in results:
                logger.error(f"SerpAPI returned error: {results['error']}")
                return []
            
            search_results = results.get('organic_results', []) or results.get('jobs_results', []) or results.get('local_results', [])
            if not search_results:
                logger.warning(f"No standard search results found. Available keys: {list(results.keys())}")
            
            return search_results
        except Exception as e:
            logger.error(f"SerpAPI error: {e}")
            return []

def build_search_queries(query: str, localization: str, linkedin_only: bool) -> List[str]:
    queries = []
    remote_terms = [term for terms in LANG_REMOTE_TERMS.values() for term in terms]
    site_filter = ' site:linkedin.com/jobs/view' if linkedin_only else ''
    
    queries.append(f'"{query}" (' + ' OR '.join([f'"{term}"' for term in remote_terms]) + ')' + site_filter)
    queries.append(f'"{query}" "{localization}"' + site_filter)
    queries.append(f'"{query}" (' + ' OR '.join([f'"{term}"' for term in remote_terms + [localization]]) + ')' + site_filter)
    
    return queries

def build_fallback_queries(query: str, localization: str, linkedin_only: bool) -> List[str]:
    queries = []
    site_filter = ' site:linkedin.com/jobs/view' if linkedin_only else ''
    
    queries.append(f'"{query}"' + site_filter)
    job_terms = ["empleo", "trabajo", "vacante", "job", "position", "career"]
    for term in job_terms:
        queries.append(f'"{query}" "{term}"' + site_filter)
    queries.append(f'{query} empleo trabajo' + site_filter)
    
    if not linkedin_only:
        job_sites = ["indeed.com", "computrabajo.com", "bumeran.com", "zonajobs.com"]
        for site in job_sites:
            queries.append(f'"{query}" site:{site}')
    
    return queries

def is_remote_job(result: Dict) -> bool:
    text_to_check = ' '.join(str(result.get(k, '')) for k in ['title', 'snippet', 'description', 'location']).lower()
    for lang_terms in LANG_REMOTE_TERMS.values():
        for term in lang_terms:
            if term.lower() in text_to_check:
                return True
    return False

def is_local_job(result: Dict, localization: str) -> bool:
    text_to_check = ' '.join(str(result.get(k, '')) for k in ['title', 'snippet', 'description', 'location']).lower()
    return localization.lower() in text_to_check

def is_accepting_applications(result: Dict) -> bool:
    text_to_check = ' '.join(str(result.get(k, '')) for k in ['title', 'snippet', 'description']).lower()
    closed_indicators = [
        "ya no se aceptan solicitudes", "no longer accepting applications", "application deadline has passed",
        "position filled", "job closed", "expired", "no longer available"
    ]
    return not any(indicator in text_to_check for indicator in closed_indicators)

def score_job_result(result: Dict, localization: str) -> Tuple[int, str]:
    is_remote = is_remote_job(result)
    is_local = is_local_job(result, localization)
    is_accepting = is_accepting_applications(result)
    
    if is_remote and is_local: base_score = 3
    elif is_remote: base_score = 2
    elif is_local: base_score = 1
    else: base_score = 0
    
    return (base_score * 2 if is_accepting else base_score, "scored_job")

def execute_searches(searcher: SerpAPISearcher, queries: List[str], base_params: Dict, 
                    localization: str, seen_urls: set, parallel_workers: int = 1) -> List[Dict]:
    all_results = []
    for i, search_query in enumerate(queries):
        params = base_params.copy()
        params['q'] = search_query
        logger.info(f"Executing search {i+1}/{len(queries)}: {search_query}")
        
        results = searcher.search(params)
        if not results:
            continue
        
        logger.info(f"Got {len(results)} results from search {i+1}")
        for result in results:
            url = result.get('link')
            if not url or url in seen_urls or not any(domain in url for domain in VALID_JOB_DOMAINS):
                continue
            
            seen_urls.add(url)
            score, job_type = score_job_result(result, localization)
            result_data = {k: str(result.get(k, '')) for k in ['title', 'snippet', 'description', 'company', 'location']}
            result_data.update({'url': url, 'score': score, 'type': job_type})
            all_results.append(result_data)
            
    return all_results

def verify_job_applications(urls: List[str], scraper: WebScraper, localization: str) -> List[JobVerificationResult]:
    """
    Verifica que las URLs de trabajo aún acepten solicitudes y la localización.
    """
    verified_results = []
    logger.info(f"Verifying {len(urls)} job URLs...")
    
    with ThreadPoolExecutor(max_workers=5) as executor: # Usar hilos para scraping concurrente
        future_to_url = {executor.submit(scraper.scrape_job_page, url, localization): url for url in urls}
        for i, future in enumerate(as_completed(future_to_url)):
            url = future_to_url[future]
            try:
                result = future.result()
                logger.info(f"Verifying URL {i+1}/{len(urls)} completed for: {url}")
                verified_results.append(result)
            except Exception as exc:
                logger.error(f'{url} generated an exception during verification: {exc}')

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
    searcher = SerpAPISearcher(SERPAPI_KEYS)
    scraper = WebScraper()
    
    base_params = {'engine': 'google', 'num': 100, 'hl': 'es'}
    if age_code := AGE_MAP.get(antiguedad_maxima.lower()):
        base_params['tbs'] = f'qdr:{age_code}'
    
    # MODIFICACIÓN: Listas para separar resultados de alta calidad y de respaldo
    high_quality_urls = []
    fallback_candidates = []
    
    seen_urls = set()
    search_iteration = 0
    
    while len(high_quality_urls) < max_urls and search_iteration < max_search_iterations:
        search_iteration += 1
        logger.info(f"=== BÚSQUEDA ITERACIÓN {search_iteration} | URLs de alta calidad: {len(high_quality_urls)}/{max_urls} ===")
        
        all_results = []
        
        # FASES DE BÚSQUEDA
        priority_queries = build_search_queries(query, localization, linkedin_only)
        all_results.extend(execute_searches(searcher, priority_queries, base_params, localization, seen_urls, parallel_workers))
        
        if len(seen_urls) < max_urls * 3: # Aumentar el factor para tener más candidatos
            fallback_queries = build_fallback_queries(query, localization, linkedin_only)
            all_results.extend(execute_searches(searcher, fallback_queries, base_params, localization, seen_urls, parallel_workers))

        all_results.sort(key=lambda x: -x['score'])
        
        # Evitar verificar URLs ya procesadas
        current_urls_in_lists = set(high_quality_urls) | {c.url for c in fallback_candidates}
        candidate_urls = [result['url'] for result in all_results if result['url'] not in current_urls_in_lists]
        
        logger.info(f"Encontradas {len(candidate_urls)} nuevas URLs candidatas para verificación")
        
        if candidate_urls:
            verification_results = verify_job_applications(candidate_urls, scraper, localization)
            
            for result in verification_results:
                if len(high_quality_urls) >= max_urls:
                    break
                
                is_valid_location = result.location_matches or result.is_fully_remote
                
                # Criterio estricto para URLs de alta calidad
                if result.is_accepting and result.confidence >= verification_confidence and is_valid_location:
                    high_quality_urls.append(result.url)
                    loc_reason = "Coincide localización" if result.location_matches else "Es remoto"
                    logger.info(f"✅ URL de alta calidad ({len(high_quality_urls)}/{max_urls}): {result.url} | Razón: {loc_reason}")
                else:
                    # MODIFICACIÓN: Guardar el resto como candidatos de respaldo
                    fallback_candidates.append(result)
                    rejection_reason = f"Acepta: {result.is_accepting}, Conf: {result.confidence:.2f}"
                    if not is_valid_location:
                        rejection_reason += f", LocMatch: {result.location_matches}, Remote: {result.is_fully_remote}"
                    logger.warning(f"⚠️ URL movida a fallbacks: {result.url} | {rejection_reason}")
        
        if len(high_quality_urls) < max_urls and search_iteration < max_search_iterations:
            logger.info("Relajando criterios de búsqueda para la siguiente iteración...")
            verification_confidence = max(0.4, verification_confidence - 0.1)
            logger.info(f"Nueva confianza mínima: {verification_confidence}")

    # --- MODIFICACIÓN: Lógica de relleno para garantizar max_urls ---
    if len(high_quality_urls) < max_urls:
        logger.info(f"No se alcanzaron las {max_urls} URLs de alta calidad. Buscando en {len(fallback_candidates)} candidatos de respaldo...")
        
        # Evitar duplicados
        urls_in_high_quality = set(high_quality_urls)
        unique_fallbacks = [res for res in fallback_candidates if res.url not in urls_in_high_quality]
        
        # Ordenar candidatos de respaldo por la mejor combinación de factores
        unique_fallbacks.sort(key=lambda r: (
            r.is_accepting, 
            r.is_fully_remote or r.location_matches, 
            r.confidence
        ), reverse=True)
        
        needed = max_urls - len(high_quality_urls)
        
        for fallback in unique_fallbacks[:needed]:
            logger.info(f"Añadiendo URL de respaldo: {fallback.url} (Acepta: {fallback.is_accepting}, Remoto/Local: {fallback.is_fully_remote or fallback.location_matches}, Conf: {fallback.confidence:.2f})")
            high_quality_urls.append(fallback.url)

    final_results = high_quality_urls[:max_urls]
    
    logger.info("=== RESULTADO FINAL ===")
    if not final_results:
        logger.warning("No se encontró ninguna URL que cumpla con los criterios.")
    else:
        logger.info(f"Se devolverán {len(final_results)} URLs ({len(high_quality_urls)} encontradas en total).")
        for i, url in enumerate(final_results, 1):
            logger.info(f"{i}. {url}")
    
    return final_results