from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from typing import List, Optional
import time

def scrape_profile_and_company(email: str, password: str, profile_url: str, company_url: Optional[str] = None) -> tuple[str, str, str]:
    """Faz login e coleta dados do perfil manualmente. Retorna o texto formatado, nome da pessoa e empresa (vazio por ora)."""
    
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless=new")  # Deixe como está, se quiser ver a janela, comente esta linha
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=options
    )

    try:
        # Login no LinkedIn
        driver.get("https://www.linkedin.com/login")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(email)
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()

        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "global-nav")))
        except TimeoutException:
            raise Exception("Login inválido. Verifique seu e-mail e senha do LinkedIn.")

        # Acessa o perfil
        driver.get(profile_url)
        time.sleep(3)  # Pequeno delay para carregamento completo

        def safe_get_text(by, value):
            try:
                return driver.find_element(by, value).text.strip()
            except NoSuchElementException:
                return "-"

        nome = safe_get_text(By.CSS_SELECTOR, "h1.text-heading-xlarge")
        localizacao = safe_get_text(By.CSS_SELECTOR, "span.text-body-small.inline.t-black--light.break-words")
        sobre = safe_get_text(By.ID, "about") or safe_get_text(By.CSS_SELECTOR, "section.pv-about-section")

        # Experiências (simplificado)
        experiencias = []
        try:
            exp_sections = driver.find_elements(By.CSS_SELECTOR, "li.pvs-list__paged-list-item")
            for exp in exp_sections[:5]:  # Limita para evitar excesso
                titulo = exp.text.strip().split("\n")[0]
                experiencias.append(f"  • {titulo}")
        except:
            experiencias.append("  • Não foi possível carregar experiências.")

        # Monta texto
        lines: List[str] = [
            f"Nome: {nome}",
            f"Localização: {localizacao}",
            "\nSobre:",
            sobre or "-",
            "\nExperiências:",
        ]
        lines.extend(experiencias)

        nome_pessoa = nome or "Desconhecido"
        nome_empresa = ""  # Empresa não implementado ainda

        texto_formatado = "\n".join(lines)
        return texto_formatado, nome_pessoa, nome_empresa

    finally:
        driver.quit()
