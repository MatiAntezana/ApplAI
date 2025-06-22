import requests
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime

def format_text(text):
    """Clean and format text content."""
    if not text:
        return "Not available"
    
    # Remove extra whitespace and clean up text
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    cleaned_text = ' '.join(chunk for chunk in chunks if chunk)
    
    return cleaned_text if cleaned_text else "Not available"

def extract_contact_info(soup):
    """Extract potential contact information from the page."""
    contact_info = {
        'emails': [],
        'phones': [],
        'social_links': []
    }
    
    # Extract emails using regex
    text_content = soup.get_text()
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text_content)
    contact_info['emails'] = list(set(emails))
    
    # Extract phone numbers (basic pattern)
    phone_pattern = r'[\+]?[1-9]?[\d\s\-\(\)]{10,15}'
    phones = re.findall(phone_pattern, text_content)
    contact_info['phones'] = [phone.strip() for phone in phones if len(phone.strip()) >= 10]
    
    # Extract social media links
    social_domains = ['linkedin.com', 'twitter.com', 'facebook.com', 'instagram.com', 'github.com']
    for link in soup.find_all('a', href=True):
        href = link['href']
        if any(domain in href for domain in social_domains):
            contact_info['social_links'].append({
                'platform': next((domain.split('.')[0] for domain in social_domains if domain in href), 'unknown'),
                'url': href,
                'text': format_text(link.get_text())
            })
    
    return contact_info

def extract_structured_content(soup):
    """Extract structured content similar to LinkedIn profile sections."""
    content = {
        'basic_info': {},
        'headings': [],
        'paragraphs': [],
        'links': [],
        'images': [],
        'lists': [],
        'contact_info': {},
        'meta_info': {}
    }
    
    # Basic Info
    title_tag = soup.find('title')
    content['basic_info']['title'] = format_text(title_tag.get_text() if title_tag else "")
    
    # Meta description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    content['basic_info']['description'] = format_text(meta_desc.get('content') if meta_desc else "")
    
    # Keywords
    meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
    content['basic_info']['keywords'] = format_text(meta_keywords.get('content') if meta_keywords else "")
    
    # Headings (structured like work experience)
    for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        content['headings'].append({
            'level': heading.name,
            'text': format_text(heading.get_text()),
            'id': heading.get('id', 'Not available')
        })
    
    # Paragraphs
    for p in soup.find_all('p'):
        text = format_text(p.get_text())
        if text != "Not available" and len(text) > 10:  # Filter out very short paragraphs
            content['paragraphs'].append(text)
    
    # Links (structured like company URLs)
    for link in soup.find_all('a', href=True):
        link_text = format_text(link.get_text())
        if link_text != "Not available":
            content['links'].append({
                'text': link_text,
                'url': link['href'],
                'title': format_text(link.get('title', ''))
            })
    
    # Images
    for img in soup.find_all('img', src=True):
        content['images'].append({
            'src': img['src'],
            'alt': format_text(img.get('alt', '')),
            'title': format_text(img.get('title', ''))
        })
    
    # Lists (unordered and ordered)
    for ul in soup.find_all(['ul', 'ol']):
        list_items = []
        for li in ul.find_all('li'):
            item_text = format_text(li.get_text())
            if item_text != "Not available":
                list_items.append(item_text)
        
        if list_items:
            content['lists'].append({
                'type': ul.name,
                'items': list_items
            })
    
    # Contact Information
    content['contact_info'] = extract_contact_info(soup)
    
    # Meta Information
    content['meta_info'] = {
        'scraped_at': datetime.now().isoformat(),
        'total_links': len(content['links']),
        'total_images': len(content['images']),
        'total_paragraphs': len(content['paragraphs']),
        'total_headings': len(content['headings'])
    }
    
    return content

class WebScraper:
    def __init__(self, delay=1):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_page_content(self, url):
        """Fetch page content with error handling."""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error accessing {url}: {e}")
            return None
    
    def scrape_url_detailed(self, url):
        """Scrape URL with detailed extraction similar to LinkedIn profile structure."""
        print(f"Scraping: {url}")
        
        html_content = self.get_page_content(url)
        if not html_content:
            return None
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Extract structured content
        structured_data = extract_structured_content(soup)
        structured_data['url'] = url
        
        # Add full text content
        structured_data['full_text'] = format_text(soup.get_text())
        
        # Pause between requests
        time.sleep(self.delay)
        
        return structured_data
    
    def scrape_multiple_urls(self, urls):
        """Scrape multiple URLs with detailed extraction."""
        results = []
        
        for i, url in enumerate(urls, 1):
            print(f"Processing URL {i}/{len(urls)}: {url}")
            data = self.scrape_url_detailed(url)
            if data:
                results.append(data)
        
        return results
    
    def save_to_detailed_txt(self, data, filename):
        """Save scraped data to text file with LinkedIn-style formatting."""
        with open(filename, "w", encoding="utf-8") as file:
            for item in data:
                file.write("=" * 80 + "\n")
                file.write(f"WEBSITE ANALYSIS REPORT\n")
                file.write("=" * 80 + "\n\n")
                
                # Basic Info
                file.write("=== Basic Information ===\n")
                file.write(f"URL: {item.get('url', 'Not available')}\n")
                file.write(f"Title: {item['basic_info'].get('title', 'Not available')}\n")
                file.write(f"Description: {item['basic_info'].get('description', 'Not available')}\n")
                file.write(f"Keywords: {item['basic_info'].get('keywords', 'Not available')}\n")
                file.write(f"Scraped at: {item['meta_info'].get('scraped_at', 'Not available')}\n\n")
                
                # Contact Information
                file.write("=== Contact Information ===\n")
                contact = item.get('contact_info', {})
                
                emails = contact.get('emails', [])
                if emails:
                    file.write(f"Emails found: {', '.join(emails)}\n")
                else:
                    file.write("Emails found: Not available\n")
                
                phones = contact.get('phones', [])
                if phones:
                    file.write(f"Phone numbers found: {', '.join(phones)}\n")
                else:
                    file.write("Phone numbers found: Not available\n")
                
                social_links = contact.get('social_links', [])
                if social_links:
                    file.write("Social media links:\n")
                    for social in social_links:
                        file.write(f"  - {social['platform'].title()}: {social['url']}\n")
                else:
                    file.write("Social media links: Not available\n")
                file.write("\n")
                
                # Headings Structure
                file.write("=== Page Structure (Headings) ===\n")
                headings = item.get('headings', [])
                if headings:
                    for heading in headings:
                        file.write(f"{heading['level'].upper()}: {heading['text']}\n")
                        if heading['id'] != 'Not available':
                            file.write(f"  ID: {heading['id']}\n")
                        file.write("-" * 50 + "\n")
                else:
                    file.write("No headings found.\n")
                file.write("\n")
                
                # Main Content (Paragraphs)
                file.write("=== Main Content ===\n")
                paragraphs = item.get('paragraphs', [])
                if paragraphs:
                    for i, paragraph in enumerate(paragraphs, 1):
                        file.write(f"Paragraph {i}: {paragraph}\n")
                        file.write("-" * 50 + "\n")
                else:
                    file.write("No main content paragraphs found.\n")
                file.write("\n")
                
                # Links
                file.write("=== Links Found ===\n")
                links = item.get('links', [])
                if links:
                    for link in links:
                        file.write(f"Text: {link['text']}\n")
                        file.write(f"URL: {link['url']}\n")
                        if link['title'] != 'Not available':
                            file.write(f"Title: {link['title']}\n")
                        file.write("-" * 50 + "\n")
                else:
                    file.write("No links found.\n")
                file.write("\n")
                
                # Images
                file.write("=== Images Found ===\n")
                images = item.get('images', [])
                if images:
                    for img in images:
                        file.write(f"Source: {img['src']}\n")
                        file.write(f"Alt text: {img['alt']}\n")
                        file.write(f"Title: {img['title']}\n")
                        file.write("-" * 50 + "\n")
                else:
                    file.write("No images found.\n")
                file.write("\n")
                
                # Lists
                file.write("=== Lists Found ===\n")
                lists = item.get('lists', [])
                if lists:
                    for i, lst in enumerate(lists, 1):
                        file.write(f"List {i} ({lst['type'].upper()}):\n")
                        for item_text in lst['items']:
                            file.write(f"  • {item_text}\n")
                        file.write("-" * 50 + "\n")
                else:
                    file.write("No lists found.\n")
                file.write("\n")
                
                # Statistics
                file.write("=== Content Statistics ===\n")
                meta = item.get('meta_info', {})
                file.write(f"Total headings: {meta.get('total_headings', 0)}\n")
                file.write(f"Total paragraphs: {meta.get('total_paragraphs', 0)}\n")
                file.write(f"Total links: {meta.get('total_links', 0)}\n")
                file.write(f"Total images: {meta.get('total_images', 0)}\n")
                file.write(f"Total word count: {len(item.get('full_text', '').split())}\n\n")
                
                # Full Text Content
                file.write("=== Full Text Content ===\n")
                file.write(f"{item.get('full_text', 'Not available')}\n")
                file.write("\n" + "=" * 80 + "\n\n")
        
        print(f"Detailed analysis saved to {filename}")
    


# Example usage
def main():
    # URLs to scrape
    urls_to_scrape = [
        "https://www.alexbodner.com/",
        # Add more URLs as needed
    ]
    
    # Initialize scraper
    scraper = WebScraper(delay=2)  # 2 second delay between requests
    
    print("Starting web scraping...")
    print(f"URLs to process: {len(urls_to_scrape)}")
    print("-" * 50)
    
    # Scrape URLs
    results = scraper.scrape_multiple_urls(urls_to_scrape)
    
    if results:
        # Save only TXT file
        scraper.save_to_detailed_txt(results, "website_scraped_content.txt")
        
        print(f"\nScraping completed! Processed {len(results)} URLs successfully.")
        print("File generated: website_scraped_content.txt")
    else:
        print("No data was successfully scraped.")

if __name__ == "__main__":
    main()