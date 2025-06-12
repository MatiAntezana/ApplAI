from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import re
import argparse
from urllib.parse import urlparse

class LinkedInSeleniumScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        self.setup_driver()

    def setup_driver(self):
        """Configura el driver de Chrome con opciones optimizadas"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # Opciones para evitar detección
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User agent realista
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Configuraciones adicionales
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")  # Para cargar más rápido
        chrome_options.add_argument("--disable-javascript")  # LinkedIn funciona sin JS para contenido básico
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.set_page_load_timeout(30)
            print("Driver de Chrome configurado exitosamente")
        except Exception as e:
            print(f"Error al configurar Chrome driver: {e}")
            print("Asegúrate de tener ChromeDriver instalado y en tu PATH")
            raise

    def clean_text(self, text):
        """Limpia y formatea el texto extraído"""
        # Eliminar espacios en blanco excesivos
        text = re.sub(r'\s+', ' ', text)
        # Eliminar caracteres especiales problemáticos
        text = re.sub(r'[^\w\s\-.,;:()\[\]{}¿?¡!@#$%&+=*/\'"áéíóúñüÁÉÍÓÚÑÜ]', '', text)
        return text.strip()

    def extract_linkedin_content(self, url):
        """Extrae contenido usando Selenium"""
        try:
            print(f"Navegando a: {url}")
            self.driver.get(url)
            
            # Esperar a que la página cargue
            time.sleep(3)
            
            # Verificar si estamos en una página de login
            if self.is_login_page():
                print("LinkedIn está mostrando página de login")
                return self.extract_limited_content()
            
            # Scroll para cargar contenido dinámico
            self.scroll_page()
            
            # Extraer contenido
            content = {}
            
            # Título de la página
            try:
                title = self.driver.title
                if title:
                    content['titulo'] = self.clean_text(title)
            except:
                pass
            
            # Extraer todo el texto visible
            try:
                body = self.driver.find_element(By.TAG_NAME, "body")
                full_text = body.text
                
                if full_text:
                    cleaned_text = self.clean_text(full_text)
                    content['contenido'] = cleaned_text
                else:
                    # Intentar con elementos específicos
                    content['contenido'] = self.extract_specific_elements()
                    
            except Exception as e:
                print(f"Error extrayendo contenido del body: {e}")
                content['contenido'] = self.extract_specific_elements()
            
            return content
            
        except TimeoutException:
            print("Timeout cargando la página")
            return None
        except Exception as e:
            print(f"Error extrayendo contenido: {e}")
            return None

    def is_login_page(self):
        """Detecta si estamos en una página de login"""
        try:
            # Buscar elementos típicos de login
            login_indicators = [
                "sign in",
                "join linkedin",
                "email",
                "password"
            ]
            
            page_source = self.driver.page_source.lower()
            return any(indicator in page_source for indicator in login_indicators)
            
        except:
            return False

    def extract_limited_content(self):
        """Extrae contenido limitado cuando hay restricciones"""
        content = {}
        
        try:
            # Título
            content['titulo'] = self.driver.title
            
            # Cualquier texto visible disponible
            body = self.driver.find_element(By.TAG_NAME, "body")
            text = body.text
            
            if text:
                content['contenido'] = self.clean_text(text)
                content['nota'] = "Extracción limitada - LinkedIn requiere autenticación para contenido completo"
            
        except Exception as e:
            print(f"Error en extracción limitada: {e}")
            content['contenido'] = "No se pudo extraer contenido"
            
        return content

    def scroll_page(self):
        """Hace scroll para cargar contenido dinámico"""
        try:
            # Scroll gradual
            for i in range(3):
                self.driver.execute_script(f"window.scrollTo(0, {(i+1) * 1000});")
                time.sleep(1)
            
            # Volver arriba
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
        except Exception as e:
            print(f"Error haciendo scroll: {e}")

    def extract_specific_elements(self):
        """Extrae texto de elementos específicos cuando el método general falla"""
        elements_to_try = [
            "main",
            "div[class*='profile']",
            "div[class*='content']",
            "article",
            "section",
            "p",
            "h1", "h2", "h3"
        ]
        
        all_text = []
        
        for selector in elements_to_try:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    text = element.text.strip()
                    if text and len(text) > 10 and text not in all_text:
                        all_text.append(text)
            except:
                continue
        
        return '\n\n'.join(all_text) if all_text else "No se pudo extraer contenido específico"

    def generate_filename(self, url):
        """Genera un nombre de archivo basado en la URL"""
        parsed_url = urlparse(url)
        path_parts = [part for part in parsed_url.path.split('/') if part]
        
        if 'jobs' in path_parts:
            filename = f"linkedin_job_selenium_{int(time.time())}"
        elif 'in' in path_parts:
            profile_id = path_parts[-1] if path_parts else 'profile'
            filename = f"linkedin_profile_selenium_{profile_id}"
        else:
            filename = f"linkedin_content_selenium_{int(time.time())}"
        
        return f"{filename}.txt"

    def save_to_file(self, content, filename):
        """Guarda el contenido en un archivo de texto"""
        try:
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(f"URL: {content.get('url', 'N/A')}\n")
                file.write(f"Fecha de extracción: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                file.write(f"Método: Selenium WebDriver\n")
                file.write("=" * 50 + "\n\n")
                
                if 'titulo' in content:
                    file.write(f"TÍTULO:\n{content['titulo']}\n\n")
                
                if 'nota' in content:
                    file.write(f"NOTA: {content['nota']}\n\n")
                
                if 'contenido' in content:
                    file.write(f"CONTENIDO:\n{content['contenido']}\n")
                
                # Estadísticas
                char_count = len(content.get('contenido', ''))
                word_count = len(content.get('contenido', '').split())
                file.write(f"\n\n--- ESTADÍSTICAS ---\n")
                file.write(f"Caracteres: {char_count}\n")
                file.write(f"Palabras: {word_count}\n")
            
            print(f"Contenido guardado en: {filename}")
            char_count = len(content.get('contenido', ''))
            word_count = len(content.get('contenido', '').split())
            print(f"Estadísticas: {char_count} caracteres, {word_count} palabras")
            return True
            
        except Exception as e:
            print(f"Error al guardar el archivo: {e}")
            return False

    def scrape_linkedin_url(self, url, output_file=None):
        """Función principal para extraer contenido de LinkedIn"""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        if 'linkedin.com' not in url:
            print("Error: La URL debe ser de LinkedIn")
            return False
        
        print("Iniciando extracción con Selenium...")
        
        try:
            content = self.extract_linkedin_content(url)
            
            if not content:
                print("No se pudo extraer contenido de la URL")
                return False
            
            content['url'] = url
            
            if not output_file:
                output_file = self.generate_filename(url)
            
            success = self.save_to_file(content, output_file)
            
            if success:
                print("Extracción completada exitosamente!")
                
            return success
            
        finally:
            self.close()

    def close(self):
        """Cierra el driver"""
        if self.driver:
            self.driver.quit()
            print("Driver cerrado")

def main():
    parser = argparse.ArgumentParser(description='Extrae texto de LinkedIn usando Selenium')
    parser.add_argument('url', help='URL del perfil o oferta de LinkedIn')
    parser.add_argument('-o', '--output', help='Nombre del archivo de salida')
    parser.add_argument('--show-browser', action='store_true', help='Mostrar el navegador (no headless)')
    
    args = parser.parse_args()
    
    scraper = LinkedInSeleniumScraper(headless=not args.show_browser)
    try:
        scraper.scrape_linkedin_url(args.url, args.output)
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 1:
        print("=== LinkedIn Selenium Scraper ===")
        url = input("Ingresa la URL de LinkedIn: ").strip()
        show_browser = input("¿Mostrar navegador? (s/n): ").lower().startswith('s')
        
        if url:
            scraper = LinkedInSeleniumScraper(headless=not show_browser)
            try:
                scraper.scrape_linkedin_url(url)
            except KeyboardInterrupt:
                print("\nInterrumpido por el usuario")
            finally:
                scraper.close()
        else:
            print("URL no válida")
    else:
        main()