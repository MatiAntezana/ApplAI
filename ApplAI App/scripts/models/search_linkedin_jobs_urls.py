import logging
from typing import List, Dict, Optional, Tuple, Set
from serpapi import GoogleSearch  # pip install google-search-results
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass

# SerpAPI keys for Google Search
SERPAPI_KEYS: List[str] = ["92fc302224c584b72afc5748a5d6c023f99c33ff9bed324f2d584dc2f8d74702"]

LANG_REMOTE_TERMS = {
    "es": ["remoto", "teletrabajo", "trabajo remoto", "home office", "100% remoto", "desde casa"],
    "en": ["remote", "remote work", "work from home", "telecommute", "fully remote", "100% remote"],
    "fr": ["télétravail", "travail à distance", "100% télétravail"],
    "de": ["Fernarbeit", "Homeoffice", "remote", "100% remote"],
    "pt": ["remoto", "teletrabalho", "trabalho remoto", "100% remoto"]
}

VALID_JOB_DOMAINS = ["linkedin.com/jobs/view",]

AGE_MAP = {
    'dia': 'd',      
    'semana': 'w',   
    'mes': 'm',      
    'anio': 'y'       
}

@dataclass
class JobVerificationResult:
    """
    Class to hold the result of job verification after scraping a job page.

    Attributes
    ----------
    url : str
        The URL of the job posting.
    is_accepting : bool
        Indicates if the job posting is currently accepting applications.
    confidence : float
        Confidence score of the verification, ranging from 0.0 to 1.0.
    reason : str
        Reason for the verification result, explaining why the job is considered open or closed.
    scraped_content : str
        The text content scraped from the job page, limited to the first 500 characters.
    location_matches : Optional[bool]
        Indicates if the job location matches the specified localization.
    is_fully_remote : Optional[bool]
        Indicates if the job is fully remote based on the scraped content.
    """
    url: str
    is_accepting: bool
    confidence: float  
    reason: str
    scraped_content: str = ""
    location_matches: Optional[bool] = None
    is_fully_remote: Optional[bool] = None


class WebScraper:
    """
    Class to scrape job pages and verify if they are accepting applications. It uses specific patterns for different job sites to 
    determine if a job is closed or open. 

    Attributes
    ----------
    timeout : int
        Timeout for HTTP requests.
    session : requests.Session
        Session object to handle HTTP requests.
    site_patterns : Dict[str, Dict]
        Dictionary containing specific patterns for different job sites to identify closed and open job postings.
    """    
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
        """
        Gets the specific patterns for a given job site based on the URL.

        Parameters
        ----------
        url : str
            The URL of the job posting.

        Returns
        -------
        Dict
            A dictionary containing the patterns for closed and open job postings for the specific site.
        """
        domain = urlparse(url).netloc.lower()
        for site_domain, patterns in self.site_patterns.items():
            if site_domain in domain:
                return patterns
        return {}


    def _verify_location_and_remoteness(self, page_text: str, localization: str) -> Tuple[bool, bool]:
        """
        Verifies if the job page text contains the specified localization and if it is fully remote.

        Parameters
        ----------
        page_text : str
            The text content of the job page.
        localization : str
            The localization string to check against the page text.

        Returns
        -------
        Tuple[bool, bool]
            A tuple containing:
            - A boolean indicating if the localization matches. 
            - A boolean indicating if the job is fully remote.
        """
        text = page_text.lower()
        
        all_remote_terms = [term for terms in LANG_REMOTE_TERMS.values() for term in terms]
        is_fully_remote = any(term in text for term in all_remote_terms)
        
        simple_localization = localization.split(',')[0].lower()
        location_matches = simple_localization in text
        
        return location_matches, is_fully_remote


    def scrape_job_page(self, url: str, localization: str) -> JobVerificationResult:
        """
        Scrapes a job page to verify if it is accepting applications and checks the localization.

        Parameters
        ----------
        url : str
            The URL of the job posting to scrape.
        localization : str
            The localization string to check against the job page text.
        
        Returns
        -------
        JobVerificationResult
            An object containing the verification result, including whether the job is accepting applications,
            confidence score, reason for the result, and scraped content.
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            page_text = soup.get_text().lower()
            
            location_matches, is_fully_remote = self._verify_location_and_remoteness(page_text, localization)
            
            patterns = self.get_domain_patterns(url)
            
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
            return JobVerificationResult(url=url, is_accepting=True, confidence=0.3, reason=f"Scraping error: {str(e)}", scraped_content="", location_matches=None, is_fully_remote=None)
        
        except Exception as e:
            return JobVerificationResult(url=url, is_accepting=True, confidence=0.3, reason=f"Unexpected error: {str(e)}", scraped_content="", location_matches=None, is_fully_remote=None)

class SerpAPISearcher:
    """
    Class to perform job searches using the SerpAPI Google Search service with multiple API keys for rate limiting.

    Attributes
    ----------
    api_keys : List[str]
        List of SerpAPI keys to use for making requests.
    key_index : int
        Index to track the current API key being used for requests.
    """
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
                return []
            
            search_results = results.get('organic_results', []) or results.get('jobs_results', []) or results.get('local_results', [])
    
            return search_results
        
        except Exception as e:
            return []


def build_search_queries(query: str, localization: str, linkedin_only: bool) -> List[str]:
    """
    Builds search queries for job postings based on the provided query and localization.

    Parameters
    ----------
    query : str
        The job title or keywords to search for.
    localization : str
        The localization string to filter results by.
    linkedin_only : bool
        If True, restricts the search to LinkedIn job postings only.

    Returns
    -------
    List[str]
        A list of search queries to be used for job searches.
    """
    queries = []
    remote_terms = [term for terms in LANG_REMOTE_TERMS.values() for term in terms]
    site_filter = ' site:linkedin.com/jobs/view' if linkedin_only else ''
    
    queries.append(f'"{query}" (' + ' OR '.join([f'"{term}"' for term in remote_terms]) + ')' + site_filter)
    queries.append(f'"{query}" "{localization}"' + site_filter)
    queries.append(f'"{query}" (' + ' OR '.join([f'"{term}"' for term in remote_terms + [localization]]) + ')' + site_filter)
    
    return queries


def build_fallback_queries(query: str, localization: str, linkedin_only: bool) -> List[str]:
    """
    Builds fallback search queries for job postings, including variations and additional job sites.

    Parameters
    ----------
    query : str
        The job title or keywords to search for.
    localization : str
        The localization string to filter results by.
    linkedin_only : bool
        If True, restricts the search to LinkedIn job postings only.
    
    Returns
    -------
    List[str]
        A list of fallback search queries to be used for job searches.
    """
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
    """
    Checks if a job result is remote based on the title, snippet, description, and location.

    Parameters
    ----------
    result : Dict
        A dictionary containing job result data, including 'title', 'snippet', 'description', and 'location'.

    Returns
    -------
    bool
        True if the job is remote, False otherwise.
    """
    text_to_check = ' '.join(str(result.get(k, '')) for k in ['title', 'snippet', 'description', 'location']).lower()
    for lang_terms in LANG_REMOTE_TERMS.values():
        for term in lang_terms:
            if term.lower() in text_to_check:
                return True
    return False


def is_local_job(result: Dict, localization: str) -> bool:
    """
    Checks if a job result matches the specified localization.

    Parameters
    ----------
    result : Dict
        A dictionary containing job result data, including 'title', 'snippet', 'description', and
        'location'.
    localization : str
        The localization string to check against the job result.
    
    Returns
    -------
    bool
        True if the job matches the localization, False otherwise.
    """
    text_to_check = ' '.join(str(result.get(k, '')) for k in ['title', 'snippet', 'description', 'location']).lower()
    return localization.lower() in text_to_check


def is_accepting_applications(result: Dict) -> bool:
    """
    Checks if a job result is currently accepting applications based on the title, snippet, and description.
    
    Parameters
    ----------
    result : Dict
        A dictionary containing job result data, including 'title', 'snippet', and 'description'.
            
    Returns
    -------
    bool
        True if the job is accepting applications, False otherwise.
    """
    text_to_check = ' '.join(str(result.get(k, '')) for k in ['title', 'snippet', 'description']).lower()
    closed_indicators = [
        "ya no se aceptan solicitudes", "no longer accepting applications", "application deadline has passed",
        "position filled", "job closed", "expired", "no longer available"
    ]
    return not any(indicator in text_to_check for indicator in closed_indicators)


def score_job_result(result: Dict, localization: str) -> Tuple[int, str]:
    """
    Scores a job result based on its remote status, localization, and whether it is accepting applications.

    Parameters
    ----------
    result : Dict
        A dictionary containing job result data, including 'title', 'snippet', 'description', and
        'location'.
    localization : str
        The localization string to check against the job result.
    
    Returns
    -------
    Tuple[int, str]
        A tuple containing the score of the job result and its type as a string.
    """
    is_remote = is_remote_job(result)
    is_local = is_local_job(result, localization)
    is_accepting = is_accepting_applications(result)
    
    if is_remote and is_local: base_score = 3
    elif is_remote: base_score = 2
    elif is_local: base_score = 1
    else: base_score = 0
    
    return (base_score * 2 if is_accepting else base_score, "scored_job")


def execute_searches(searcher: SerpAPISearcher, queries: List[str], base_params: Dict, localization: str, 
                     seen_urls: set, parallel_workers: int = 1) -> List[Dict]:
    """
    Executes multiple search queries using the SerpAPISearcher and returns a list of job results.

    Parameters
    ----------
    searcher : SerpAPISearcher
        An instance of SerpAPISearcher to perform the searches.
    queries : List[str]
        A list of search queries to execute.
    base_params : Dict
        Base parameters for the search API.
    localization : str
        The localization string to filter results by.
    seen_urls : set
        A set of URLs that have already been processed to avoid duplicates.
    parallel_workers : int
        Number of parallel workers to use for executing searches.

    Returns
    -------
    List[Dict]
        A list of dictionaries containing job results, each with keys like 'title', 'snippet',
        'description', 'company', 'location', 'url', 'score', and 'type
    """
    all_results = []
    for i, search_query in enumerate(queries):
        params = base_params.copy()
        params['q'] = search_query
        
        results = searcher.search(params)
        if not results:
            continue
        
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
    Verifies job applications by scraping the provided URLs and checking if they are accepting applications.

    Parameters
    ----------
    urls : List[str]
        A list of URLs to scrape for job postings.
    scraper : WebScraper
        An instance of WebScraper to perform the scraping.
    localization : str
        The localization string to check against the job postings.

    Returns
    -------
    List[JobVerificationResult]
        A list of JobVerificationResult objects containing the verification results for each job posting.
    """
    verified_results = []
    
    with ThreadPoolExecutor(max_workers=5) as executor: 
        future_to_url = {executor.submit(scraper.scrape_job_page, url, localization): url for url in urls}
        for i, future in enumerate(as_completed(future_to_url)):
            url = future_to_url[future]
            result = future.result()
            verified_results.append(result)

    return verified_results


def search_jobs_serpapi_verified(query: str,
                                max_urls: int = 10,
                                localization: str = "Buenos Aires",
                                maximum_seniority: str = "semana",
                                linkedin_only: bool = True,
                                parallel_workers: int = 1,
                                verification_confidence: float = 0.7,
                                max_search_iterations: int = 3
                            ) -> List[str]:
    """
    Searches for job postings using SerpAPI and verifies them to ensure they are accepting applications.
    This function performs multiple searches, verifies the results, and returns a list of URLs of job postings that are currently accepting applications.
    
    Parameters
    ----------
    query : str
        The job title or keywords to search for.
    max_urls : int
        The maximum number of job URLs to return.
    localization : str
        The localization string to filter results by (e.g., "Buenos Aires").
    maximum_seniority : str
        The maximum seniority level to filter results by (e.g., "semana" for
        past week). Options are 'dia', 'semana', 'mes', 'anio'.
    linkedin_only : bool
        If True, restricts the search to LinkedIn job postings only.
    parallel_workers : int
        Number of parallel workers to use for executing searches and scraping job pages.
    verification_confidence : float
        The initial confidence threshold for verifying job postings. It will decrease if not enough results are found
        during the search iterations.
    max_search_iterations : int
        The maximum number of search iterations to perform if not enough valid job URLs are found.
    
    Returns
    -------
    List[str]
        A list of URLs of job postings that are currently accepting applications.
    """
    searcher = SerpAPISearcher(SERPAPI_KEYS)
    scraper = WebScraper()
    
    base_params = {'engine': 'google', 'num': 100, 'hl': 'es'}
    if age_code := AGE_MAP.get(maximum_seniority.lower()):
        base_params['tbs'] = f'qdr:{age_code}'
    
    high_quality_urls = []
    fallback_candidates = []
    
    seen_urls = set()
    search_iteration = 0
    
    while len(high_quality_urls) < max_urls and search_iteration < max_search_iterations:
        search_iteration += 1
        
        all_results = []
        
        priority_queries = build_search_queries(query, localization, linkedin_only)
        all_results.extend(execute_searches(searcher, priority_queries, base_params, localization, seen_urls, parallel_workers))
        
        if len(seen_urls) < max_urls * 3:
            fallback_queries = build_fallback_queries(query, localization, linkedin_only)
            all_results.extend(execute_searches(searcher, fallback_queries, base_params, localization, seen_urls, parallel_workers))

        all_results.sort(key=lambda x: -x['score'])
        
        current_urls_in_lists = set(high_quality_urls) | {c.url for c in fallback_candidates}
        candidate_urls = [result['url'] for result in all_results if result['url'] not in current_urls_in_lists]
        
        if candidate_urls:
            verification_results = verify_job_applications(candidate_urls, scraper, localization)
            
            for result in verification_results:
                if len(high_quality_urls) >= max_urls:
                    break
                
                is_valid_location = result.location_matches or result.is_fully_remote
                
                if result.is_accepting and result.confidence >= verification_confidence and is_valid_location:
                    high_quality_urls.append(result.url)
                    loc_reason = "Coincide localización" if result.location_matches else "Es remoto"
                
                else:
                    fallback_candidates.append(result)
                    rejection_reason = f"Acepta: {result.is_accepting}, Conf: {result.confidence:.2f}"
                    if not is_valid_location:
                        rejection_reason += f", LocMatch: {result.location_matches}, Remote: {result.is_fully_remote}"
        
        if len(high_quality_urls) < max_urls and search_iteration < max_search_iterations:
            verification_confidence = max(0.4, verification_confidence - 0.1)

    if len(high_quality_urls) < max_urls:
        urls_in_high_quality = set(high_quality_urls)
        unique_fallbacks = [res for res in fallback_candidates if res.url not in urls_in_high_quality]
        
        unique_fallbacks.sort(key=lambda r: (
            r.is_accepting, 
            r.is_fully_remote or r.location_matches, 
            r.confidence
        ), reverse=True)
        
        needed = max_urls - len(high_quality_urls)
        
        for fallback in unique_fallbacks[:needed]:
            high_quality_urls.append(fallback.url)

    final_results = high_quality_urls[:max_urls]
    
    return final_results