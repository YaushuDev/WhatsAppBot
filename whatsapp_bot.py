# whatsapp_bot.py
"""
Bot de automatización para WhatsApp Web mejorado
Utiliza Selenium para controlar WhatsApp Web y enviar mensajes automáticamente.
El bot envía UN mensaje aleatorio a cada número de la lista, una sola vez por sesión.
Incluye detección robusta de cierre de Chrome y mejor control de automatización.
Maneja correctamente múltiples ejecuciones y reconexiones de Chrome.
"""

import time
import random
import threading
import os
import tempfile
import shutil
import uuid
from typing import List, Callable, Optional, Set
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, \
    InvalidSessionIdException


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
    Envía un mensaje único a cada número de la lista
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

        # Control de números enviados
        self.sent_numbers: Set[str] = set()
        self.total_numbers = 0
        self.messages_sent = 0

        # Control de estado del navegador
        self.browser_closed = False
        self.session_active = False

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

    def _is_browser_alive(self) -> bool:
        """
        Verifica si el navegador sigue activo

        Returns:
            True si el navegador está activo
        """
        try:
            if not self.driver:
                return False

            # Intentar ejecutar un comando simple
            self.driver.current_url
            return True
        except (WebDriverException, InvalidSessionIdException):
            self.browser_closed = True
            self.session_active = False
            return False
        except Exception:
            return False

    def _force_close_driver(self):
        """
        Fuerza el cierre del driver y limpia la sesión
        """
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            finally:
                self.driver = None
                self.session_active = False
                self.browser_closed = False

    def _create_new_driver(self) -> bool:
        """
        Crea un nuevo driver de Chrome

        Returns:
            True si se creó correctamente
        """
        try:
            # Cerrar driver existente si hay uno
            self._force_close_driver()

            # Limpiar procesos previos
            self._cleanup_existing_processes()

            # Esperar un momento para que se liberen los recursos
            time.sleep(2)

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

            self.browser_closed = False
            self.session_active = True
            return True

        except Exception as e:
            self._update_status(f"Error al crear nuevo driver: {e}")
            return False

    def setup_driver(self) -> bool:
        """
        Configura e inicializa el driver de Chrome

        Returns:
            True si se configuró correctamente
        """
        try:
            self._update_status("Configurando navegador...")

            # Si ya hay un driver pero la sesión no está activa, crear uno nuevo
            if self.driver and not self.session_active:
                self._update_status("Sesión anterior cerrada, creando nueva...")
                return self._create_new_driver()

            # Si no hay driver, crear uno nuevo
            if not self.driver:
                return self._create_new_driver()

            # Si el driver existe y parece activo, verificarlo
            if self._is_browser_alive():
                self._update_status("Reutilizando navegador existente")
                return True
            else:
                self._update_status("Navegador existente no responde, creando nuevo...")
                return self._create_new_driver()

        except Exception as e:
            self._update_status(f"Error al configurar navegador: {e}")
            return self._create_new_driver()

    def open_whatsapp(self) -> bool:
        """
        Abre WhatsApp Web y espera a que esté listo

        Returns:
            True si se abrió correctamente
        """
        try:
            # Asegurar que tenemos un driver activo
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

        except InvalidSessionIdException:
            self._update_status("Sesión inválida, creando nueva...")
            self.session_active = False
            return self.setup_driver() and self.open_whatsapp()
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
            # Verificar si el navegador sigue activo
            if not self._is_browser_alive():
                self._update_status("Error: El navegador se ha cerrado")
                return False

            # Crear URL directa al chat
            url = f"https://web.whatsapp.com/send?phone={number}"
            self._update_status(f"Enviando mensaje a {number}")

            self.driver.get(url)
            time.sleep(3)  # Esperar a que cargue

            # Verificar nuevamente si el navegador sigue activo
            if not self._is_browser_alive():
                self._update_status("Error: El navegador se cerró durante el envío")
                return False

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

            # Verificar una vez más si el navegador sigue activo
            if not self._is_browser_alive():
                self._update_status("Advertencia: El navegador se cerró después del envío")
                return False

            self._update_status(f"✓ Mensaje enviado a {number}")
            return True

        except TimeoutException:
            self._update_status(f"Timeout al enviar mensaje a {number}")
            return False
        except (WebDriverException, InvalidSessionIdException):
            self._update_status(f"Error: El navegador se cerró durante el envío a {number}")
            self.browser_closed = True
            self.session_active = False
            return False
        except Exception as e:
            self._update_status(f"Error al enviar mensaje a {number}: {e}")
            return False

    def start_automation(self, numbers: List[str], messages: List[str],
                         interval_min: int = 30, interval_max: int = 60):
        """
        Inicia la automatización de envío de mensajes
        Envía UN mensaje a cada número de la lista

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

        # Reiniciar control de envíos
        self.sent_numbers.clear()
        self.total_numbers = len(numbers)
        self.messages_sent = 0
        self.browser_closed = False

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
        Envía un mensaje único a cada número

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

            self._update_status(f"Automatización iniciada - Enviando a {self.total_numbers} números")

            # Crear una copia de la lista para iterar
            numbers_to_send = numbers.copy()
            random.shuffle(numbers_to_send)  # Mezclar orden para mayor naturalidad

            for number in numbers_to_send:
                # Verificar si se debe detener
                if self.should_stop:
                    self._update_status("Automatización detenida por el usuario")
                    break

                # Verificar si el navegador sigue activo
                if self.browser_closed or not self._is_browser_alive():
                    self._update_status("Automatización detenida: El navegador se ha cerrado")
                    break

                # Verificar si ya se envió a este número
                if number in self.sent_numbers:
                    continue

                # Seleccionar mensaje aleatorio
                message = random.choice(messages)

                # Enviar mensaje
                if self.send_message_to_number(number, message):
                    self.sent_numbers.add(number)
                    self.messages_sent += 1

                    progress = f"Progreso: {self.messages_sent}/{self.total_numbers}"
                    self._update_status(progress)

                    # Si ya se enviaron todos los mensajes, terminar
                    if self.messages_sent >= self.total_numbers:
                        self._update_status("✓ Todos los mensajes han sido enviados")
                        break

                    # Calcular tiempo de espera aleatorio
                    wait_time = random.randint(interval_min, interval_max)
                    self._update_status(f"Esperando {wait_time} segundos hasta el próximo mensaje...")

                    # Esperar con posibilidad de interrumpir
                    for second in range(wait_time):
                        if self.should_stop or self.browser_closed or not self._is_browser_alive():
                            break
                        time.sleep(1)

                        # Mostrar countdown cada 10 segundos
                        remaining = wait_time - second - 1
                        if remaining > 0 and remaining % 10 == 0:
                            self._update_status(f"Esperando... {remaining} segundos restantes")

                else:
                    self._update_status(f"Error al enviar mensaje a {number}, continuando con el siguiente...")

                    # Esperar menos tiempo en caso de error
                    for _ in range(5):
                        if self.should_stop or self.browser_closed:
                            break
                        time.sleep(1)

        except Exception as e:
            self._update_status(f"Error en la automatización: {e}")

        finally:
            self.is_running = False
            completion_msg = f"Automatización finalizada - Mensajes enviados: {self.messages_sent}/{self.total_numbers}"
            self._update_status(completion_msg)

    def stop_automation(self):
        """
        Detiene la automatización de forma robusta
        """
        if self.is_running:
            self._update_status("Deteniendo automatización...")
            self.should_stop = True

            # Esperar a que termine el hilo con timeout
            if self.automation_thread and self.automation_thread.is_alive():
                # Dar tiempo para que termine naturalmente
                self.automation_thread.join(timeout=10)

                # Si sigue vivo después del timeout, forzar parada
                if self.automation_thread.is_alive():
                    self._update_status("Forzando detención de automatización...")
                    self.is_running = False
        else:
            self._update_status("La automatización no está en ejecución")

    def reset_session(self):
        """
        Reinicia la sesión del navegador completamente
        """
        self._update_status("Reiniciando sesión del navegador...")
        self.stop_automation()
        self._force_close_driver()
        time.sleep(2)
        self.sent_numbers.clear()
        self.messages_sent = 0
        self.total_numbers = 0

    def get_automation_stats(self) -> dict:
        """
        Obtiene estadísticas de la automatización actual

        Returns:
            Diccionario con estadísticas
        """
        return {
            'total_numbers': self.total_numbers,
            'messages_sent': self.messages_sent,
            'remaining': self.total_numbers - self.messages_sent,
            'is_running': self.is_running,
            'browser_active': self._is_browser_alive(),
            'session_active': self.session_active
        }

    def close(self):
        """
        Cierra el bot y limpia recursos de forma robusta
        """
        self._update_status("Cerrando bot...")

        # Detener automatización si está activa
        self.stop_automation()

        # Cerrar navegador
        self._force_close_driver()

        # Limpiar perfil temporal
        self.profile_manager.cleanup()

        # Reiniciar estado
        self.browser_closed = False
        self.session_active = False
        self.sent_numbers.clear()
        self.total_numbers = 0
        self.messages_sent = 0

    def is_active(self) -> bool:
        """
        Verifica si la automatización está activa

        Returns:
            True si está activa
        """
        return self.is_running and self._is_browser_alive()