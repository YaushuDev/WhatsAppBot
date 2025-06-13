# whatsapp_driver.py
"""
Gestor del navegador Chrome para el Bot de WhatsApp
Este módulo se encarga exclusivamente de la configuración, inicialización, gestión y cierre
del navegador Chrome con todas las optimizaciones necesarias para WhatsApp Web, incluyendo
soporte para Unicode, configuraciones de rendimiento, manejo robusto de sesiones y
resolución automática de conflictos de directorio de datos de usuario.
"""

import os
import time
import shutil
import psutil
import tempfile
from typing import Optional, Callable
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
from whatsapp_utils import WhatsAppConstants


class ChromeUserDataManager:
    """
    Gestor especializado para manejar directorios de datos de usuario de Chrome
    """

    def __init__(self):
        self.base_user_data_dir = os.path.join(os.getcwd(), "chrome_user_data")
        self.current_user_data_dir = None

    def get_available_user_data_dir(self) -> str:
        """
        Obtiene un directorio de datos de usuario disponible

        Returns:
            Ruta del directorio disponible
        """
        # Intentar usar el directorio base primero
        if self._is_directory_available(self.base_user_data_dir):
            self.current_user_data_dir = self.base_user_data_dir
            return self.base_user_data_dir

        # Si no está disponible, intentar limpiarlo
        if self._try_cleanup_directory(self.base_user_data_dir):
            self.current_user_data_dir = self.base_user_data_dir
            return self.base_user_data_dir

        # Como último recurso, crear directorio único
        unique_dir = self._create_unique_directory()
        self.current_user_data_dir = unique_dir
        return unique_dir

    def _is_directory_available(self, directory_path: str) -> bool:
        """
        Verifica si un directorio está disponible para uso

        Args:
            directory_path: Ruta del directorio

        Returns:
            True si está disponible
        """
        try:
            # Si no existe, está disponible
            if not os.path.exists(directory_path):
                return True

            # Verificar si hay procesos de Chrome usando este directorio
            return not self._is_chrome_using_directory(directory_path)

        except Exception:
            return False

    def _is_chrome_using_directory(self, directory_path: str) -> bool:
        """
        Verifica si hay procesos de Chrome usando el directorio

        Args:
            directory_path: Ruta del directorio

        Returns:
            True si Chrome está usando el directorio
        """
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                        cmdline = proc.info.get('cmdline', [])
                        if cmdline:
                            cmdline_str = ' '.join(cmdline)
                            if directory_path in cmdline_str:
                                return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            return False

        except Exception:
            return True  # En caso de duda, asumir que está en uso

    def _try_cleanup_directory(self, directory_path: str) -> bool:
        """
        Intenta limpiar un directorio de datos de usuario

        Args:
            directory_path: Ruta del directorio

        Returns:
            True si se limpió correctamente
        """
        try:
            if not os.path.exists(directory_path):
                return True

            # Verificar nuevamente si está en uso
            if self._is_chrome_using_directory(directory_path):
                return False

            # Intentar eliminar el directorio
            shutil.rmtree(directory_path, ignore_errors=True)

            # Verificar que se eliminó
            return not os.path.exists(directory_path)

        except Exception:
            return False

    def _create_unique_directory(self) -> str:
        """
        Crea un directorio único para datos de usuario

        Returns:
            Ruta del directorio único creado
        """
        try:
            # Usar timestamp para crear nombre único
            timestamp = str(int(time.time()))
            unique_dir = f"{self.base_user_data_dir}_{timestamp}"

            # Si por alguna razón ya existe, usar tempfile
            if os.path.exists(unique_dir):
                unique_dir = tempfile.mkdtemp(prefix="chrome_user_data_")

            return unique_dir

        except Exception:
            # Fallback: usar directorio temporal del sistema
            return tempfile.mkdtemp(prefix="chrome_user_data_")

    def cleanup_current_directory(self, force: bool = False):
        """
        Limpia el directorio actual si no está en uso

        Args:
            force: Si debe forzar la limpieza
        """
        if not self.current_user_data_dir:
            return

        try:
            if force or not self._is_chrome_using_directory(self.current_user_data_dir):
                if os.path.exists(self.current_user_data_dir):
                    shutil.rmtree(self.current_user_data_dir, ignore_errors=True)

        except Exception:
            pass


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
        self.user_data_manager = ChromeUserDataManager()
        self._initialization_attempts = 0
        self._max_initialization_attempts = 3

    def _update_status(self, message: str):
        """
        Actualiza el estado y notifica mediante callback

        Args:
            message: Mensaje de estado
        """
        print(f"[Driver] {message}")
        if self.status_callback:
            self.status_callback(message)

    def _configure_chrome_options(self, user_data_dir: str) -> Options:
        """
        Configura las opciones optimizadas de Chrome para WhatsApp Web

        Args:
            user_data_dir: Directorio de datos de usuario a usar

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

        # MEJORADO: Directorio de datos de usuario dinámico
        options.add_argument(f"--user-data-dir={user_data_dir}")

        # NUEVO: Argumentos adicionales para manejar múltiples instancias
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")

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

    def _attempt_driver_initialization(self, user_data_dir: str) -> bool:
        """
        Intenta inicializar el driver con un directorio específico

        Args:
            user_data_dir: Directorio de datos de usuario

        Returns:
            True si se inicializó correctamente
        """
        try:
            # Configurar opciones con el directorio específico
            options = self._configure_chrome_options(user_data_dir)

            self._update_status(f"Intentando inicializar Chrome con: {os.path.basename(user_data_dir)}")

            # Crear driver
            self.driver = webdriver.Chrome(options=options)

            # Script anti-detección
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            # Configuración de ventana y timeouts
            self.driver.maximize_window()
            self.driver.implicitly_wait(3)
            self.driver.set_page_load_timeout(WhatsAppConstants.PAGE_LOAD_TIMEOUT)

            return True

        except WebDriverException as e:
            error_message = str(e)
            if "user data directory is already in use" in error_message:
                self._update_status(f"Directorio en uso: {os.path.basename(user_data_dir)}")
                return False
            else:
                self._update_status(f"Error de WebDriver: {error_message}")
                return False
        except Exception as e:
            self._update_status(f"Error inesperado: {str(e)}")
            return False

    def initialize_driver(self) -> bool:
        """
        Inicializa el driver de Chrome con manejo inteligente de directorios

        Returns:
            True si se inicializó correctamente
        """
        self._initialization_attempts += 1

        if self._initialization_attempts > self._max_initialization_attempts:
            self._update_status("❌ Máximo de intentos de inicialización alcanzado")
            return False

        try:
            self._update_status("🚀 Iniciando navegador Chrome...")

            # Obtener directorio de datos de usuario disponible
            user_data_dir = self.user_data_manager.get_available_user_data_dir()

            # Intentar inicializar con el directorio obtenido
            if self._attempt_driver_initialization(user_data_dir):
                self._update_status("✅ Navegador iniciado correctamente")
                self._initialization_attempts = 0  # Resetear contador en éxito
                return True

            # Si falló, intentar con directorio alternativo
            self._update_status("⚠️ Reintentando con directorio alternativo...")

            # Obtener nuevo directorio (forzará uno único)
            alternative_dir = self.user_data_manager._create_unique_directory()

            if self._attempt_driver_initialization(alternative_dir):
                self._update_status("✅ Navegador iniciado con directorio alternativo")
                self._initialization_attempts = 0
                return True

            # Si ambos fallan, reportar error
            self._update_status("❌ No se pudo inicializar el navegador")
            return False

        except Exception as e:
            self._update_status(f"❌ Error al inicializar navegador: {str(e)}")
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

    def close(self, cleanup_user_data: bool = True):
        """
        Cierra el navegador y limpia recursos

        Args:
            cleanup_user_data: Si debe limpiar el directorio de datos de usuario
        """
        try:
            if self.driver:
                self._update_status("🔒 Cerrando navegador...")
                self.driver.quit()
                self.driver = None
                self._update_status("✅ Navegador cerrado correctamente")

            # Limpiar directorio de datos de usuario si se solicita
            if cleanup_user_data:
                self.user_data_manager.cleanup_current_directory()

        except Exception as e:
            self._update_status(f"⚠️ Error al cerrar navegador: {str(e)}")
        finally:
            self.driver = None

    def force_cleanup(self):
        """
        Fuerza la limpieza de todos los recursos
        """
        try:
            if self.driver:
                self.driver.quit()
        except:
            pass
        finally:
            self.driver = None

        # Forzar limpieza del directorio
        self.user_data_manager.cleanup_current_directory(force=True)

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

    def get_user_data_info(self) -> dict:
        """
        NUEVO: Obtiene información sobre el directorio de datos de usuario

        Returns:
            Información del directorio de datos de usuario
        """
        return {
            'current_directory': self.user_data_manager.current_user_data_dir,
            'base_directory': self.user_data_manager.base_user_data_dir,
            'initialization_attempts': self._initialization_attempts,
            'max_attempts': self._max_initialization_attempts
        }