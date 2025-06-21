import requests
from bs4 import BeautifulSoup
import time
import csv
import json
from urllib.parse import urljoin, urlparse
import re

class WebScraper:
    def __init__(self, delay=1):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
    
    def get_page_content(self, url):
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error accessing {url}: {e}")
            return None
    
    def extract_text_basic(self, html_content):
        if not html_content:
            return ""
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text()
        
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def extract_text_structured(self, html_content):
        if not html_content:
            return {}
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        for script in soup(["script", "style"]):
            script.decompose()
        
        result = {
            'title': '',
            'headings': [],
            'paragraphs': [],
            'links': [],
            'all_text': ''
        }
        
        title_tag = soup.find('title')
        if title_tag:
            result['title'] = title_tag.get_text().strip()
        
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            result['headings'].append({
                'level': heading.name,
                'text': heading.get_text().strip()
            })
        
        for p in soup.find_all('p'):
            text = p.get_text().strip()
            if text:
                result['paragraphs'].append(text)
        
        for link in soup.find_all('a', href=True):
            result['links'].append({
                'text': link.get_text().strip(),
                'url': link['href']
            })
        
        result['all_text'] = soup.get_text()
        lines = (line.strip() for line in result['all_text'].splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        result['all_text'] = ' '.join(chunk for chunk in chunks if chunk)
        
        return result
    
    def scrape_single_url(self, url, structured=False):
        html_content = self.get_page_content(url)
        if not html_content:
            return None
        
        if structured:
            data = self.extract_text_structured(html_content)
        else:
            data = {
                'url': url,
                'text': self.extract_text_basic(html_content)
            }
        
        data['url'] = url
        
        # Pausa entre requests
        time.sleep(self.delay)
        
        return data
    
    def scrape_multiple_urls(self, urls, structured=False):
        results = []
        
        for url in urls:
            data = self.scrape_single_url(url, structured)
            if data:
                results.append(data)
        
        return results
    
    def save_to_txt(self, data, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            for item in data:
                if 'text' in item:
                    f.write(item['text'])
                else:
                    f.write(item['all_text'])
    
    def save_to_json(self, data, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def save_to_csv(self, data, filename):
        if not data:
            return
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            for item in data:
                row = {}
                for key, value in item.items():
                    if isinstance(value, (list, dict)):
                        row[key] = str(value)
                    else:
                        row[key] = value
                writer.writerow(row)

def main():
    scraper = WebScraper(delay=1) 
    print("\n--- Scraping individual URL ---")
    single_result = scraper.scrape_single_url('https://www.alexbodner.com/', structured=True)
    if single_result:
        scraper.save_to_txt([single_result], 'single_scraped_result.txt')
        print(f"Scraped data saved for single URL: {single_result['url']}")

if __name__ == "__main__":
    main()