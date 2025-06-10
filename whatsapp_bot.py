# whatsapp_bot.py
"""
Bot de automatización para WhatsApp Web
Utiliza Selenium para controlar WhatsApp Web y enviar mensajes automáticamente
a números específicos con mensajes aleatorios de una lista predefinida.
Incluye manejo robusto de perfiles de Chrome y gestión de errores avanzada.
"""

import time
import random
import threading
import os
import tempfile
import shutil
import uuid
from typing import List, Callable, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException


class ChromeProfileManager:
    """
    Gestor de perfiles de Chrome para evitar conflictos
    """

    def __init__(self):
        """
        Inicializa el gestor de perfiles
        """
        self.profile_path = None
        self.temp_profile = False

    def create_profile_path(self) -> str:
        """
        Crea un directorio de perfil único para Chrome

        Returns:
            Ruta del directorio de perfil
        """
        try:
            # Intentar usar el directorio predeterminado
            default_profile = os.path.join(os.getcwd(), "chrome_profile")

            # Si no existe, crearlo
            if not os.path.exists(default_profile):
                os.makedirs(default_profile, exist_ok=True)
                self.profile_path = default_profile
                self.temp_profile = False
                return self.profile_path

            # Si existe pero está en uso, crear uno temporal
            if self._is_profile_in_use(default_profile):
                temp_dir = tempfile.mkdtemp(prefix="whatsapp_bot_")
                self.profile_path = temp_dir
                self.temp_profile = True
                return self.profile_path

            # Si está disponible, usarlo
            self.profile_path = default_profile
            self.temp_profile = False
            return self.profile_path

        except Exception:
            # En caso de error, crear uno temporal
            temp_dir = tempfile.mkdtemp(prefix="whatsapp_bot_")
            self.profile_path = temp_dir
            self.temp_profile = True
            return self.profile_path

    def _is_profile_in_use(self, profile_path: str) -> bool:
        """
        Verifica si un perfil está en uso

        Args:
            profile_path: Ruta del perfil a verificar

        Returns:
            True si está en uso
        """
        lock_file = os.path.join(profile_path, "SingletonLock")
        return os.path.exists(lock_file)

    def cleanup(self):
        """
        Limpia el perfil temporal si fue creado
        """
        if self.temp_profile and self.profile_path and os.path.exists(self.profile_path):
            try:
                shutil.rmtree(self.profile_path)
            except Exception:
                pass  # Ignorar errores de limpieza


class WhatsAppBot:
    """
    Bot para automatizar el envío de mensajes en WhatsApp Web
    """

    def __init__(self, status_callback: Optional[Callable] = None):
        """
        Inicializa el bot de WhatsApp

        Args:
            status_callback: Función callback para reportar el estado
        """
        self.driver = None
        self.is_running = False
        self.should_stop = False
        self.status_callback = status_callback
        self.wait_time = 10
        self.profile_manager = ChromeProfileManager()
        self.automation_thread = None

    def _update_status(self, message: str):
        """
        Actualiza el estado y llama al callback si existe

        Args:
            message: Mensaje de estado
        """
        if self.status_callback:
            self.status_callback(message)
        print(f"[WhatsApp Bot] {message}")

    def _cleanup_existing_processes(self):
        """
        Intenta cerrar procesos de Chrome existentes
        """
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name']):
                if 'chrome' in proc.info['name'].lower():
                    try:
                        proc.terminate()
                        proc.wait(timeout=3)
                    except:
                        pass
        except ImportError:
            # psutil no está disponible, continuar sin limpieza
            pass
        except Exception:
            # Ignorar errores de limpieza
            pass

    def setup_driver(self) -> bool:
        """
        Configura e inicializa el driver de Chrome

        Returns:
            True si se configuró correctamente
        """
        try:
            self._update_status("Configurando navegador...")

            # Limpiar procesos existentes si es necesario
            self._cleanup_existing_processes()

            # Obtener ruta de perfil
            profile_path = self.profile_manager.create_profile_path()

            # Configuración de Chrome
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")
            chrome_options.add_argument("--disable-javascript")
            chrome_options.add_argument("--window-size=1200,800")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # Configurar perfil de usuario
            chrome_options.add_argument(f"--user-data-dir={profile_path}")
            chrome_options.add_argument(f"--profile-directory=Default")

            # Configuración adicional para evitar conflictos
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--no-default-browser-check")

            # Crear el driver
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(self.wait_time)

            # Ejecutar script para ocultar que es un bot
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            self._update_status("Navegador configurado correctamente")
            return True

        except WebDriverException as e:
            error_msg = str(e)
            if "user data directory" in error_msg.lower():
                self._update_status("Error: Directorio de perfil en uso. Creando perfil temporal...")
                try:
                    # Forzar creación de perfil temporal
                    temp_dir = tempfile.mkdtemp(prefix=f"whatsapp_bot_{uuid.uuid4().hex[:8]}_")
                    self.profile_manager.profile_path = temp_dir
                    self.profile_manager.temp_profile = True

                    # Intentar nuevamente
                    return self._retry_setup_driver(temp_dir)
                except Exception as retry_error:
                    self._update_status(f"Error en reintento: {retry_error}")
                    return False
            else:
                self._update_status(f"Error al configurar el navegador: {e}")
                return False
        except Exception as e:
            self._update_status(f"Error inesperado: {e}")
            return False

    def _retry_setup_driver(self, temp_profile_path: str) -> bool:
        """
        Reintenta configurar el driver con un perfil temporal

        Args:
            temp_profile_path: Ruta del perfil temporal

        Returns:
            True si se configuró correctamente
        """
        try:
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1200,800")
            chrome_options.add_argument(f"--user-data-dir={temp_profile_path}")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(self.wait_time)

            self._update_status("Navegador configurado con perfil temporal")
            return True

        except Exception as e:
            self._update_status(f"Error en reintento de configuración: {e}")
            return False

    def open_whatsapp(self) -> bool:
        """
        Abre WhatsApp Web y espera a que esté listo

        Returns:
            True si se abrió correctamente
        """
        try:
            if not self.driver:
                if not self.setup_driver():
                    return False

            self._update_status("Abriendo WhatsApp Web...")
            self.driver.get("https://web.whatsapp.com")

            # Esperar a que aparezca el indicador de que está cargado
            self._update_status("Esperando a que WhatsApp Web esté listo...")

            # Esperar a que aparezca la barra de búsqueda o el código QR
            wait = WebDriverWait(self.driver, 60)

            # Intentar encontrar la barra de búsqueda (indica que está logueado)
            try:
                # Selector más robusto para la barra de búsqueda
                search_selectors = [
                    "//div[@contenteditable='true'][@data-tab='3']",
                    "//div[@title='Buscar o comenzar un chat nuevo']",
                    "//div[contains(@class, 'copyable-text')][@contenteditable='true']"
                ]

                search_found = False
                for selector in search_selectors:
                    try:
                        wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                        search_found = True
                        break
                    except TimeoutException:
                        continue

                if search_found:
                    self._update_status("WhatsApp Web está listo")
                    return True

            except TimeoutException:
                pass

            # Si no encuentra la barra de búsqueda, verificar si hay QR
            try:
                qr_selectors = [
                    "//canvas[@aria-label='Scan me!']",
                    "//canvas[contains(@aria-label, 'Scan')]",
                    "//div[contains(@data-ref, 'qr')]//canvas"
                ]

                qr_found = False
                for selector in qr_selectors:
                    try:
                        self.driver.find_element(By.XPATH, selector)
                        qr_found = True
                        break
                    except NoSuchElementException:
                        continue

                if qr_found:
                    self._update_status("Código QR detectado. Por favor, escanea el código QR en tu teléfono")

                    # Esperar a que desaparezca el QR (timeout más largo)
                    wait_long = WebDriverWait(self.driver, 120)

                    for selector in qr_selectors:
                        try:
                            wait_long.until(EC.invisibility_of_element_located((By.XPATH, selector)))
                            break
                        except TimeoutException:
                            continue

                    # Esperar a que aparezca la barra de búsqueda
                    for selector in search_selectors:
                        try:
                            wait_long.until(EC.presence_of_element_located((By.XPATH, selector)))
                            self._update_status("WhatsApp Web está listo")
                            return True
                        except TimeoutException:
                            continue

                self._update_status("No se pudo detectar el estado de WhatsApp Web")
                return False

            except Exception as e:
                self._update_status(f"Error verificando estado: {e}")
                return False

        except Exception as e:
            self._update_status(f"Error al abrir WhatsApp Web: {e}")
            return False

    def send_message_to_number(self, number: str, message: str) -> bool:
        """
        Envía un mensaje a un número específico

        Args:
            number: Número de teléfono (solo dígitos)
            message: Mensaje a enviar

        Returns:
            True si se envió correctamente
        """
        try:
            if not self.driver:
                self._update_status("Error: Navegador no inicializado")
                return False

            # Crear URL directa al chat
            url = f"https://web.whatsapp.com/send?phone={number}"
            self._update_status(f"Abriendo chat con {number}")

            self.driver.get(url)
            time.sleep(3)  # Esperar a que cargue

            # Esperar a que cargue el chat
            wait = WebDriverWait(self.driver, 20)

            # Selectores para el cuadro de texto
            message_selectors = [
                "//div[@contenteditable='true'][@data-tab='10']",
                "//div[@contenteditable='true'][contains(@class, 'copyable-text')]",
                "//div[@role='textbox'][@contenteditable='true']",
                "//div[contains(@class, '_13NKt')][@contenteditable='true']"
            ]

            message_box = None
            for selector in message_selectors:
                try:
                    message_box = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                    break
                except TimeoutException:
                    continue

            if not message_box:
                self._update_status(f"No se encontró el cuadro de mensaje para {number}")
                return False

            # Escribir el mensaje
            message_box.click()
            time.sleep(1)

            # Limpiar y escribir el mensaje
            message_box.clear()
            message_box.send_keys(message)
            time.sleep(1)

            # Selectores para el botón de enviar
            send_selectors = [
                "//button[@data-tab='11']",
                "//span[@data-icon='send']/../..",
                "//button[contains(@class, '_4sWnG')]",
                "//button[./span[@data-icon='send']]"
            ]

            send_button = None
            for selector in send_selectors:
                try:
                    send_button = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    break
                except TimeoutException:
                    continue

            if not send_button:
                self._update_status(f"No se encontró el botón de enviar para {number}")
                return False

            send_button.click()

            # Esperar un momento para confirmar el envío
            time.sleep(3)

            self._update_status(f"Mensaje enviado a {number}")
            return True

        except TimeoutException:
            self._update_status(f"Timeout al enviar mensaje a {number}")
            return False
        except Exception as e:
            self._update_status(f"Error al enviar mensaje a {number}: {e}")
            return False

    def start_automation(self, numbers: List[str], messages: List[str],
                         interval_min: int = 30, interval_max: int = 60):
        """
        Inicia la automatización de envío de mensajes

        Args:
            numbers: Lista de números de teléfono
            messages: Lista de mensajes
            interval_min: Intervalo mínimo entre mensajes (segundos)
            interval_max: Intervalo máximo entre mensajes (segundos)
        """
        if not numbers or not messages:
            self._update_status("Error: No hay números o mensajes configurados")
            return

        if self.is_running:
            self._update_status("La automatización ya está en ejecución")
            return

        # Iniciar en un hilo separado
        self.automation_thread = threading.Thread(
            target=self._automation_loop,
            args=(numbers, messages, interval_min, interval_max),
            daemon=True
        )
        self.automation_thread.start()

    def _automation_loop(self, numbers: List[str], messages: List[str],
                         interval_min: int, interval_max: int):
        """
        Bucle principal de automatización

        Args:
            numbers: Lista de números
            messages: Lista de mensajes
            interval_min: Intervalo mínimo
            interval_max: Intervalo máximo
        """
        self.is_running = True
        self.should_stop = False

        try:
            # Inicializar WhatsApp Web
            if not self.open_whatsapp():
                self._update_status("Error: No se pudo inicializar WhatsApp Web")
                return

            self._update_status("Automatización iniciada")
            sent_count = 0

            while not self.should_stop and numbers and messages:
                # Seleccionar número y mensaje aleatorio
                number = random.choice(numbers)
                message = random.choice(messages)

                # Enviar mensaje
                if self.send_message_to_number(number, message):
                    sent_count += 1
                    self._update_status(f"Mensajes enviados: {sent_count}")

                    # Calcular tiempo de espera aleatorio
                    wait_time = random.randint(interval_min, interval_max)
                    self._update_status(f"Esperando {wait_time} segundos hasta el próximo mensaje...")

                    # Esperar con posibilidad de interrumpir
                    for _ in range(wait_time):
                        if self.should_stop:
                            break
                        time.sleep(1)
                else:
                    self._update_status("Error al enviar mensaje, esperando 10 segundos...")
                    for _ in range(10):
                        if self.should_stop:
                            break
                        time.sleep(1)

        except Exception as e:
            self._update_status(f"Error en la automatización: {e}")

        finally:
            self.is_running = False
            self._update_status("Automatización detenida")

    def stop_automation(self):
        """
        Detiene la automatización
        """
        if self.is_running:
            self._update_status("Deteniendo automatización...")
            self.should_stop = True

            # Esperar a que termine el hilo
            if self.automation_thread and self.automation_thread.is_alive():
                self.automation_thread.join(timeout=5)
        else:
            self._update_status("La automatización no está en ejecución")

    def close(self):
        """
        Cierra el bot y limpia recursos
        """
        self.stop_automation()

        if self.driver:
            try:
                self.driver.quit()
                self._update_status("Navegador cerrado")
            except Exception as e:
                self._update_status(f"Error al cerrar navegador: {e}")
            finally:
                self.driver = None

        # Limpiar perfil temporal
        self.profile_manager.cleanup()

    def is_active(self) -> bool:
        """
        Verifica si la automatización está activa

        Returns:
            True si está activa
        """
        return self.is_running