import requests
from bs4 import BeautifulSoup

# ----------------------------------------
# CONFIGURACIÓN: reemplazá por tu cookie li_at real
COOKIE_LI_AT = "AQEDAVCprHYCUvisAAABlxzHZVkAAAGXiVHM704AFI42hkmzzhGZLoRIJsNnJTUkDoKag96qKcCXxSGu22TdWIwnn9uskuaPkGptzaWx9pE6HXLh7w1w2gr4RoEOScQWJuHrrBHrSA6fbCtm9h-Az8ej"
# ----------------------------------------
def descargar_perfil_linkedin(url_perfil):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/114.0.0.0 Safari/537.36",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Cookie": f"li_at={COOKIE_LI_AT}"
    }

    response = requests.get(url_perfil, headers=headers)

    if response.status_code == 200:
        return response.text
    else:
        print(f"Error al descargar el perfil: Código HTTP {response.status_code}")
        return None

def extraer_info(html):
    soup = BeautifulSoup(html, "html.parser")

    info = {}

    # Nombre (usualmente h1)
    nombre_tag = soup.find("h1")
    info['Nombre'] = nombre_tag.get_text(strip=True) if nombre_tag else "No disponible"

    # Título profesional (clase que suele contener el título)
    titulo_tag = soup.find("div", class_="text-body-medium break-words")
    info['Título'] = titulo_tag.get_text(strip=True) if titulo_tag else "No disponible"

    # Ubicación (clase que suele contener la ubicación)
    ubicacion_tag = soup.find("span", class_="text-body-small inline t-black--light break-words")
    info['Ubicación'] = ubicacion_tag.get_text(strip=True) if ubicacion_tag else "No disponible"

    # Extracto / resumen (About) (buscamos sección con id 'about' o similar)
    about_section = soup.find("section", id="about")
    if about_section:
        about_text = about_section.get_text(separator="\n", strip=True)
        info['Extracto'] = about_text
    else:
        info['Extracto'] = "No disponible"

    # Experiencia (section con id experience o con etiquetas similares)
    exp_section = soup.find("section", id="experience")
    experiencias = []
    if exp_section:
        positions = exp_section.find_all("li")
        for pos in positions:
            titulo_pos = pos.find("h3")
            empresa = pos.find("p", class_="pv-entity__secondary-title")
            fechas = pos.find("h4", class_="pv-entity__date-range")
            desc = pos.find("p", class_="pv-entity__description")
            exp_text = ""
            if titulo_pos:
                exp_text += f"{titulo_pos.get_text(strip=True)}"
            if empresa:
                exp_text += f" en {empresa.get_text(strip=True)}"
            if fechas:
                exp_text += f" ({fechas.get_text(strip=True)})"
            if desc:
                exp_text += f"\n{desc.get_text(strip=True)}"
            if exp_text:
                experiencias.append(exp_text)
    info['Experiencia'] = "\n\n".join(experiencias) if experiencias else "No disponible"

    # Educación (section con id education)
    edu_section = soup.find("section", id="education")
    educaciones = []
    if edu_section:
        edu_items = edu_section.find_all("li")
        for edu in edu_items:
            institucion = edu.find("h3")
            titulo = edu.find("p", class_="pv-entity__secondary-title")
            fechas = edu.find("p", class_="pv-entity__dates")
            edu_text = ""
            if institucion:
                edu_text += f"{institucion.get_text(strip=True)}"
            if titulo:
                edu_text += f" - {titulo.get_text(strip=True)}"
            if fechas:
                edu_text += f" ({fechas.get_text(strip=True)})"
            if edu_text:
                educaciones.append(edu_text)
    info['Educación'] = "\n\n".join(educaciones) if educaciones else "No disponible"

    return info

def imprimir_info(info):
    print("\n----- INFORMACIÓN EXTRAÍDA -----\n")
    for clave, valor in info.items():
        print(f"{clave}:\n{valor}\n")

if __name__ == "__main__":
    url = input("📎 Ingresá la URL del perfil de LinkedIn: ").strip()
    html = descargar_perfil_linkedin(url)

    if html:
        info = extraer_info(html)
        imprimir_info(info)


