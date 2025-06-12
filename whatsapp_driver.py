# whatsapp_driver.py
"""
Gestor del navegador Chrome para el Bot de WhatsApp
Este módulo se encarga exclusivamente de la configuración, inicialización, gestión y cierre
del navegador Chrome con todas las optimizaciones necesarias para WhatsApp Web, incluyendo
soporte para Unicode, configuraciones de rendimiento y manejo robusto de sesiones.
"""

import os
import time
from typing import Optional, Callable
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from whatsapp_utils import WhatsAppConstants


class ChromeDriverManager:
    """
    Gestor especializado para el navegador Chrome optimizado para WhatsApp Web
    """

    def __init__(self, status_callback: Optional[Callable] = None):
        """
        Inicializa el gestor del driver Chrome

        Args:
            status_callback: Función callback para reportar estado
        """
        self.driver = None
        self.status_callback = status_callback
        self._chrome_options = None

    def _update_status(self, message: str):
        """
        Actualiza el estado y notifica mediante callback

        Args:
            message: Mensaje de estado
        """
        print(f"[Driver] {message}")
        if self.status_callback:
            self.status_callback(message)

    def _configure_chrome_options(self) -> Options:
        """
        Configura las opciones optimizadas de Chrome para WhatsApp Web

        Returns:
            Opciones configuradas de Chrome con soporte completo para Unicode
        """
        options = Options()

        # Configuración básica anti-detección
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # Optimizaciones de rendimiento
        options.add_argument("--disable-extensions")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--disable-ipc-flooding-protection")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-background-networking")

        # Configuración de idioma para soporte Unicode
        options.add_argument("--lang=es")
        options.add_argument("--accept-lang=es-ES,es,en")

        # Directorio de datos de usuario para mantener sesión
        user_data_dir = os.path.join(os.getcwd(), "chrome_user_data")
        options.add_argument(f"--user-data-dir={user_data_dir}")

        # Configuración de preferencias avanzadas
        prefs = {
            "profile.default_content_setting_values": {
                "media_stream": 1,
                "media_stream_camera": 1,
                "media_stream_mic": 1,
                "notifications": 1
            },
            "profile.default_content_settings.popups": 0,
            "profile.managed_default_content_settings.images": 1,
            "intl.accept_languages": "es-ES,es,en",
            "intl.charset_default": "UTF-8",
            "profile.default_content_setting_values.automatic_downloads": 1,
            "profile.content_settings.exceptions.automatic_downloads.*.setting": 1
        }
        options.add_experimental_option("prefs", prefs)

        return options

    def initialize_driver(self) -> bool:
        """
        Inicializa el driver de Chrome con configuración optimizada

        Returns:
            True si se inicializó correctamente
        """
        try:
            self._update_status("Iniciando navegador Chrome...")

            # Configurar opciones si no están configuradas
            if not self._chrome_options:
                self._chrome_options = self._configure_chrome_options()

            # Crear driver
            self.driver = webdriver.Chrome(options=self._chrome_options)

            # Script anti-detección
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            # Configuración de ventana y timeouts
            self.driver.maximize_window()
            self.driver.implicitly_wait(3)
            self.driver.set_page_load_timeout(WhatsAppConstants.PAGE_LOAD_TIMEOUT)

            self._update_status("Navegador iniciado correctamente")
            return True

        except Exception as e:
            self._update_status(f"Error al inicializar navegador: {str(e)}")
            return False

    def is_session_alive(self) -> bool:
        """
        Verifica si la sesión del navegador sigue activa

        Returns:
            True si la sesión está activa
        """
        try:
            if not self.driver:
                return False
            # Intenta acceder al título para verificar que el driver responde
            _ = self.driver.title
            return True
        except Exception:
            return False

    def navigate_to(self, url: str) -> bool:
        """
        Navega a una URL específica

        Args:
            url: URL de destino

        Returns:
            True si la navegación fue exitosa
        """
        try:
            if not self.is_session_alive():
                self._update_status("Sesión no activa, no se puede navegar")
                return False

            self._update_status(f"Navegando a: {url}")
            self.driver.get(url)
            return True

        except Exception as e:
            self._update_status(f"Error al navegar a {url}: {str(e)}")
            return False

    def execute_script(self, script: str):
        """
        Ejecuta un script JavaScript en el navegador

        Args:
            script: Código JavaScript a ejecutar

        Returns:
            Resultado de la ejecución del script
        """
        try:
            if not self.is_session_alive():
                return None
            return self.driver.execute_script(script)
        except Exception as e:
            self._update_status(f"Error ejecutando script: {str(e)}")
            return None

    def wait_for_element(self, selectors: list, timeout: int = None, clickable: bool = False):
        """
        Espera a que aparezca un elemento usando múltiples selectores

        Args:
            selectors: Lista de selectores CSS/XPath a probar
            timeout: Tiempo máximo de espera (usa default si None)
            clickable: Si el elemento debe ser clickeable

        Returns:
            Elemento encontrado o None
        """
        if not self.is_session_alive():
            return None

        if timeout is None:
            timeout = WhatsAppConstants.ELEMENT_WAIT_TIMEOUT

        # Usar timeout más corto para cada selector individual
        individual_timeout = max(1, timeout // len(selectors))

        for selector in selectors:
            try:
                wait = WebDriverWait(self.driver, individual_timeout)

                # Determinar si es XPath o CSS
                if selector.startswith('//') or selector.startswith('('):
                    by_method = By.XPATH
                else:
                    by_method = By.CSS_SELECTOR

                if clickable:
                    element = wait.until(EC.element_to_be_clickable((by_method, selector)))
                else:
                    element = wait.until(EC.presence_of_element_located((by_method, selector)))

                return element

            except TimeoutException:
                continue

        return None

    def safe_click(self, element, max_attempts: int = 2) -> bool:
        """
        Hace click de forma segura evitando interceptaciones

        Args:
            element: Elemento a hacer click
            max_attempts: Máximo número de intentos

        Returns:
            True si el click fue exitoso
        """
        if not self.is_session_alive():
            return False

        for attempt in range(max_attempts):
            try:
                # Scroll al elemento
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center', behavior: 'instant'});",
                    element
                )
                time.sleep(WhatsAppConstants.SHORT_DELAY)

                # Click directo
                element.click()
                return True

            except Exception:
                try:
                    # Click con JavaScript como fallback
                    self.driver.execute_script("arguments[0].click();", element)
                    return True
                except Exception:
                    if attempt < max_attempts - 1:
                        time.sleep(WhatsAppConstants.SHORT_DELAY)
                        continue
                    return False

        return False

    def get_driver(self):
        """
        Obtiene la instancia del driver

        Returns:
            Instancia del WebDriver de Selenium
        """
        return self.driver

    def close(self):
        """
        Cierra el navegador y limpia recursos
        """
        try:
            if self.driver:
                self._update_status("Cerrando navegador...")
                self.driver.quit()
                self.driver = None
                self._update_status("Navegador cerrado correctamente")
        except Exception as e:
            self._update_status(f"Error al cerrar navegador: {str(e)}")
        finally:
            self.driver = None

    def get_current_url(self) -> Optional[str]:
        """
        Obtiene la URL actual del navegador

        Returns:
            URL actual o None si hay error
        """
        try:
            if self.is_session_alive():
                return self.driver.current_url
        except Exception:
            pass
        return None

    def get_page_title(self) -> Optional[str]:
        """
        Obtiene el título de la página actual

        Returns:
            Título de la página o None si hay error
        """
        try:
            if self.is_session_alive():
                return self.driver.title
        except Exception:
            pass
        return None