# whatsapp_bot.py
"""
Bot de WhatsApp automatizado optimizado con soporte completo para emoticones
Maneja la automatización del envío de mensajes a través de WhatsApp Web usando Selenium.
Incluye soporte robusto para emoticones y caracteres Unicode mediante JavaScript injection,
solucionando las limitaciones de ChromeDriver con caracteres fuera del BMP.
Optimizado para velocidad: envío de texto ~10s, envío con imagen ~20-25s máximo.
"""

import time
import random
import os
import json
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, \
    ElementClickInterceptedException, NoSuchElementException
from typing import List, Dict, Any, Callable, Optional


class WhatsAppBot:
    """
    Bot automatizado para WhatsApp Web con soporte completo para emoticones y caracteres Unicode
    Optimizado para velocidad y eficiencia en el envío de mensajes
    """

    def __init__(self, status_callback: Optional[Callable] = None):
        """
        Inicializa el bot de WhatsApp

        Args:
            status_callback: Función callback para actualizar el estado en la GUI
        """
        self.driver = None
        self.is_running = False
        self.status_callback = status_callback
        self.wait_timeout = 15  # Reducido de 20 a 15
        self.current_session_contacts = []
        self.current_session_messages = []

        # Cache para elementos encontrados (optimización)
        self._element_cache = {}
        self._last_contact = None

        # Configuración de Chrome optimizada
        self.chrome_options = self._configure_chrome_options()

    def _configure_chrome_options(self) -> Options:
        """
        Configura las opciones de Chrome para el bot con soporte mejorado para Unicode

        Returns:
            Opciones configuradas de Chrome
        """
        options = Options()

        # Configuración básica optimizada
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-extensions")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")

        # Optimizaciones de rendimiento
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--disable-ipc-flooding-protection")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-background-networking")

        # Configuración para soporte de Unicode y emoticones
        options.add_argument("--lang=es")
        options.add_argument("--accept-lang=es-ES,es,en")

        # Configuración de usuario para mantener sesión
        user_data_dir = os.path.join(os.getcwd(), "chrome_user_data")
        options.add_argument(f"--user-data-dir={user_data_dir}")

        # Configuración de medios optimizada
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
            # Optimizaciones de carga
            "profile.default_content_setting_values.automatic_downloads": 1,
            "profile.content_settings.exceptions.automatic_downloads.*.setting": 1
        }
        options.add_experimental_option("prefs", prefs)

        return options

    def _has_emoji_or_unicode(self, text: str) -> bool:
        """
        Detecta si el texto contiene emoticones o caracteres Unicode especiales

        Args:
            text: Texto a analizar

        Returns:
            True si contiene emoticones o caracteres especiales
        """
        try:
            # Patrón optimizado para detectar emoticones
            emoji_pattern = re.compile(
                "["
                "\U0001F600-\U0001F64F"  # emoticones faciales
                "\U0001F300-\U0001F5FF"  # símbolos & pictogramas
                "\U0001F680-\U0001F6FF"  # transporte & símbolos de mapa
                "\U0001F1E0-\U0001F1FF"  # banderas (iOS)
                "\U00002500-\U00002BEF"  # símbolos varios
                "\U00002702-\U000027B0"
                "\U000024C2-\U0001F251"
                "\U0001f926-\U0001f937"
                "\U00010000-\U0010ffff"
                "\u2640-\u2642"
                "\u2600-\u2B55"
                "\u200d"
                "\u23cf"
                "\u23e9"
                "\u231a"
                "\ufe0f"  # variaciones de emoji
                "\u3030"
                "]+", flags=re.UNICODE)

            return bool(emoji_pattern.search(text))
        except Exception:
            return True

    def _escape_unicode_for_js(self, text: str) -> str:
        """
        Escapa caracteres Unicode para uso seguro en JavaScript

        Args:
            text: Texto a escapar

        Returns:
            Texto escapado para JavaScript
        """
        try:
            escaped = json.dumps(text, ensure_ascii=False)[1:-1]
            return escaped
        except Exception:
            return text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')

    def _update_status(self, message: str):
        """
        Actualiza el estado y notifica a la GUI

        Args:
            message: Mensaje de estado
        """
        print(f"[Bot] {message}")
        if self.status_callback:
            self.status_callback(message)

    def _initialize_driver(self) -> bool:
        """
        Inicializa el driver de Chrome

        Returns:
            True si se inicializó correctamente
        """
        try:
            self._update_status("Iniciando navegador...")
            self.driver = webdriver.Chrome(options=self.chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.maximize_window()

            # Optimizar timeouts
            self.driver.implicitly_wait(3)  # Reducido de default
            self.driver.set_page_load_timeout(30)

            return True
        except Exception as e:
            self._update_status(f"Error al inicializar navegador: {str(e)}")
            return False

    def _check_session_alive(self) -> bool:
        """
        Verifica si la sesión del navegador sigue activa

        Returns:
            True si la sesión está activa
        """
        try:
            if not self.driver:
                return False
            _ = self.driver.title
            return True
        except Exception:
            return False

    def _wait_for_element_optimized(self, selectors: List[str], timeout: int = 10, clickable: bool = False) -> Optional[
        Any]:
        """
        Espera a que aparezca un elemento usando múltiples selectores (optimizado)

        Args:
            selectors: Lista de selectores XPath/CSS a probar
            timeout: Tiempo máximo de espera
            clickable: Si el elemento debe ser clickeable

        Returns:
            Elemento encontrado o None
        """
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

    def _safe_click_optimized(self, element, max_attempts: int = 2) -> bool:
        """
        Hace click de forma segura evitando interceptaciones (optimizado)

        Args:
            element: Elemento a hacer click
            max_attempts: Máximo número de intentos

        Returns:
            True si el click fue exitoso
        """
        for attempt in range(max_attempts):
            try:
                # Scroll rápido al elemento
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'instant'});",
                                           element)
                time.sleep(0.2)  # Reducido de 0.5

                # Click directo
                element.click()
                return True

            except ElementClickInterceptedException:
                try:
                    # Click con JavaScript (más rápido)
                    self.driver.execute_script("arguments[0].click();", element)
                    return True
                except:
                    if attempt < max_attempts - 1:
                        time.sleep(0.3)  # Reducido de 1
                        continue
                    return False
            except Exception:
                if attempt < max_attempts - 1:
                    time.sleep(0.3)  # Reducido de 1
                    continue
                return False
        return False

    def _open_whatsapp_web(self) -> bool:
        """
        Abre WhatsApp Web y espera a que se cargue (optimizado)

        Returns:
            True si se abrió correctamente
        """
        try:
            self._update_status("Abriendo WhatsApp Web...")
            self.driver.get("https://web.whatsapp.com")

            # Selectores optimizados (CSS cuando sea posible)
            main_selectors = [
                "div[contenteditable='true'][data-tab='3']",
                "div[role='textbox'][title*='Buscar']",
                "div[data-testid='search'] div[contenteditable='true']",
                "//div[@title='Nueva conversación']",
                "//div[@contenteditable='true'][@data-tab='3']"
            ]

            self._update_status("Esperando carga de WhatsApp Web...")

            # Detectar interfaz principal
            main_element = self._wait_for_element_optimized(main_selectors, timeout=25)
            if main_element:
                self._update_status("WhatsApp Web cargado correctamente")
                return True

            # Buscar QR si no encuentra interfaz
            qr_selectors = [
                "canvas[aria-label='Scan me!']",
                "canvas",
                "//div[@data-ref]//canvas"
            ]

            qr_element = self._wait_for_element_optimized(qr_selectors, timeout=5)
            if qr_element:
                self._update_status("Escanea el código QR en WhatsApp Web para continuar")

                # Esperar login
                main_element = self._wait_for_element_optimized(main_selectors, timeout=60)
                if main_element:
                    self._update_status("QR escaneado correctamente, WhatsApp Web listo")
                    return True

            self._update_status("No se pudo cargar WhatsApp Web correctamente")
            return False

        except Exception as e:
            self._update_status(f"Error al abrir WhatsApp Web: {str(e)}")
            return False

    def _search_and_open_contact_optimized(self, phone_number: str) -> bool:
        """
        Busca y abre un contacto específico (optimizado)

        Args:
            phone_number: Número de teléfono del contacto

        Returns:
            True si se abrió el contacto correctamente
        """
        try:
            if not self._check_session_alive():
                self._update_status("Sesión perdida, reintentando...")
                return False

            # Si es el mismo contacto que antes, verificar si ya está abierto
            if self._last_contact == phone_number:
                message_selectors = [
                    "div[contenteditable='true'][data-tab='10']",
                    "div[role='textbox'][title*='mensaje']",
                    "div[data-testid='conversation-compose-box-input']"
                ]

                existing_message_box = self._wait_for_element_optimized(message_selectors, timeout=2)
                if existing_message_box:
                    return True

            # Selectores optimizados para búsqueda
            search_selectors = [
                "div[contenteditable='true'][data-tab='3']",
                "div[role='textbox'][title*='Buscar']",
                "div[data-testid='search'] div[contenteditable='true']"
            ]

            search_box = self._wait_for_element_optimized(search_selectors, timeout=10, clickable=True)
            if not search_box:
                self._update_status("No se encontró el campo de búsqueda")
                return False

            if not self._safe_click_optimized(search_box):
                return False

            # Limpiar y escribir más rápido
            search_box.clear()
            time.sleep(0.3)  # Reducido de 1
            search_box.send_keys(phone_number)
            time.sleep(1.5)  # Reducido de 3
            search_box.send_keys(Keys.ENTER)
            time.sleep(2)  # Reducido de 4

            # Verificar conversación abierta
            message_selectors = [
                "div[contenteditable='true'][data-tab='10']",
                "div[role='textbox'][title*='mensaje']",
                "div[data-testid='conversation-compose-box-input']"
            ]

            message_box = self._wait_for_element_optimized(message_selectors, timeout=8)
            if message_box:
                self._last_contact = phone_number
                return True

            # URL directa como fallback (más rápido)
            self._update_status(f"Abriendo {phone_number} con URL directa...")
            whatsapp_url = f"https://web.whatsapp.com/send?phone={phone_number}"
            self.driver.get(whatsapp_url)
            time.sleep(3)  # Reducido de 6

            message_box = self._wait_for_element_optimized(message_selectors, timeout=10)
            if message_box:
                self._last_contact = phone_number
                return True

            return False

        except Exception as e:
            self._update_status(f"Error al buscar contacto {phone_number}: {str(e)}")
            return False

    def _send_text_message_javascript_optimized(self, message_text: str) -> bool:
        """
        Envía un mensaje de texto usando JavaScript optimizado para soporte completo de emoticones

        Args:
            message_text: Texto del mensaje

        Returns:
            True si se envió correctamente
        """
        try:
            self._update_status("📝 Enviando mensaje con soporte de emoticones...")

            escaped_text = self._escape_unicode_for_js(message_text)

            # Script JavaScript optimizado
            js_script = f"""
            function sendMessageOptimized() {{
                try {{
                    const messageBox = document.querySelector('[contenteditable="true"][data-tab="10"]') ||
                                     document.querySelector('[role="textbox"][title*="mensaje"]') ||
                                     document.querySelector('[data-testid="conversation-compose-box-input"]');

                    if (!messageBox) return false;

                    messageBox.focus();
                    messageBox.innerHTML = '';

                    const textToSend = "{escaped_text}";
                    const textNode = document.createTextNode(textToSend);
                    messageBox.appendChild(textNode);

                    const inputEvent = new InputEvent('input', {{
                        bubbles: true,
                        cancelable: true,
                        data: textToSend
                    }});
                    messageBox.dispatchEvent(inputEvent);

                    // Envío inmediato sin setTimeout
                    const sendButton = document.querySelector('[data-testid="send"]') ||
                                     document.querySelector('[aria-label*="Enviar"]') ||
                                     document.querySelector('span[data-icon="send"]').closest('button');

                    if (sendButton) {{
                        sendButton.click();
                        return true;
                    }}
                    return false;

                }} catch (error) {{
                    console.log("Error:", error);
                    return false;
                }}
            }}
            return sendMessageOptimized();
            """

            result = self.driver.execute_script(js_script)
            time.sleep(1.5)  # Reducido de 3

            if result is not False:
                self._update_status("✅ Mensaje con emoticones enviado correctamente")
                return True
            else:
                return self._send_text_message_fallback_optimized(message_text)

        except Exception as e:
            self._update_status(f"❌ Error en envío JavaScript: {str(e)}")
            return self._send_text_message_fallback_optimized(message_text)

    def _send_text_message_fallback_optimized(self, message_text: str) -> bool:
        """
        Método de fallback optimizado para enviar mensajes

        Args:
            message_text: Texto del mensaje

        Returns:
            True si se envió correctamente
        """
        try:
            self._update_status("📝 Enviando con método tradicional...")

            message_selectors = [
                "div[contenteditable='true'][data-tab='10']",
                "div[role='textbox'][title*='mensaje']",
                "div[data-testid='conversation-compose-box-input']"
            ]

            message_box = self._wait_for_element_optimized(message_selectors, timeout=10, clickable=True)
            if not message_box:
                self._update_status("No se encontró el campo de mensaje")
                return False

            if not self._safe_click_optimized(message_box):
                return False

            message_box.clear()
            time.sleep(0.3)  # Reducido de 1

            safe_text = self._filter_bmp_characters(message_text)

            # Envío optimizado
            lines = safe_text.split('\n')
            for i, line in enumerate(lines):
                message_box.send_keys(line)
                if i < len(lines) - 1:
                    message_box.send_keys(Keys.SHIFT + Keys.ENTER)

            time.sleep(0.5)  # Reducido de 1
            message_box.send_keys(Keys.ENTER)
            time.sleep(1.5)  # Reducido de 3

            return True

        except Exception as e:
            self._update_status(f"Error en método fallback: {str(e)}")
            return False

    def _filter_bmp_characters(self, text: str) -> str:
        """
        Filtra caracteres que no están en el Basic Multilingual Plane

        Args:
            text: Texto original

        Returns:
            Texto filtrado solo con caracteres BMP
        """
        try:
            filtered = ''.join(char for char in text if ord(char) <= 0xFFFF)
            if len(filtered) != len(text):
                self._update_status("⚠️ Algunos emoticones fueron filtrados por compatibilidad")
            return filtered
        except Exception:
            return text

    def _send_text_message_optimized(self, message_text: str) -> bool:
        """
        Envía un mensaje de texto con soporte inteligente para emoticones (optimizado)

        Args:
            message_text: Texto del mensaje

        Returns:
            True si se envió correctamente
        """
        try:
            if not self._check_session_alive():
                return False

            if self._has_emoji_or_unicode(message_text):
                self._update_status("😀 Detectados emoticones, usando método avanzado...")
                return self._send_text_message_javascript_optimized(message_text)
            else:
                self._update_status("📝 Enviando texto simple...")
                return self._send_text_message_fallback_optimized(message_text)

        except Exception as e:
            self._update_status(f"Error al enviar mensaje de texto: {str(e)}")
            return False

    def _validate_image_file_cached(self, image_path: str) -> bool:
        """
        Valida que el archivo de imagen existe y es válido (con cache)

        Args:
            image_path: Ruta de la imagen

        Returns:
            True si la imagen es válida
        """
        # Cache de validaciones para evitar re-validar
        if hasattr(self, '_validated_images') and image_path in self._validated_images:
            return self._validated_images[image_path]

        if not hasattr(self, '_validated_images'):
            self._validated_images = {}

        try:
            if not os.path.exists(image_path):
                self._update_status(f"Archivo no encontrado: {image_path}")
                self._validated_images[image_path] = False
                return False

            # Verificar tamaño del archivo (máximo 64MB)
            file_size = os.path.getsize(image_path)
            if file_size > 64 * 1024 * 1024:
                self._update_status(f"Archivo demasiado grande: {file_size / (1024 * 1024):.1f}MB")
                self._validated_images[image_path] = False
                return False

            # Verificar extensión
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
            ext = os.path.splitext(image_path)[1].lower()
            if ext not in valid_extensions:
                self._update_status(f"Formato de imagen no soportado: {ext}")
                self._validated_images[image_path] = False
                return False

            self._validated_images[image_path] = True
            return True

        except Exception as e:
            self._update_status(f"Error validando imagen: {str(e)}")
            self._validated_images[image_path] = False
            return False

    def _send_image_only_optimized(self, image_path: str) -> bool:
        """
        Envía solo una imagen sin texto (optimizado)

        Args:
            image_path: Ruta de la imagen

        Returns:
            True si se envió correctamente
        """
        try:
            self._update_status(f"🖼️ Enviando imagen: {os.path.basename(image_path)}")

            # Selectores optimizados para botón adjuntar
            attach_selectors = [
                "div[title='Adjuntar']",
                "button[aria-label='Adjuntar']",
                "span[data-icon='plus']",
                "span[data-icon='attach-menu-plus']",
                "[data-testid='clip']"
            ]

            attach_button = self._wait_for_element_optimized(attach_selectors, timeout=8, clickable=True)
            if not attach_button:
                self._update_status("❌ No se encontró el botón adjuntar")
                return False

            if not self._safe_click_optimized(attach_button):
                return False

            time.sleep(1)  # Reducido de 2

            # Selectores optimizados para input de archivo
            file_input_selectors = [
                "input[accept*='image']",
                "input[type='file'][accept*='image']",
                "input[type='file']",
                "li[data-testid='mi-attach-image'] input"
            ]

            # Buscar input directamente primero
            file_input = self._wait_for_element_optimized(file_input_selectors, timeout=5)

            if not file_input:
                # Buscar opción de fotos
                photos_option_selectors = [
                    "li[data-testid='mi-attach-image']",
                    "span:contains('Fotos y videos')",
                    "div[role='button'][title*='foto']"
                ]

                photos_option = self._wait_for_element_optimized(photos_option_selectors, timeout=5, clickable=True)
                if photos_option and self._safe_click_optimized(photos_option):
                    time.sleep(1)  # Reducido de 2
                    file_input = self._wait_for_element_optimized(file_input_selectors, timeout=5)

            if not file_input:
                self._update_status("❌ No se encontró el input de archivo")
                return False

            # Enviar archivo
            absolute_path = os.path.abspath(image_path)
            self._update_status(f"📎 Cargando imagen...")
            file_input.send_keys(absolute_path)
            time.sleep(3)  # Reducido de 6

            # Enviar imagen
            send_selectors = [
                "span[data-icon='send']",
                "button[aria-label='Enviar']",
                "div[role='button'][aria-label='Enviar']",
                "[data-testid='send']"
            ]

            send_button = self._wait_for_element_optimized(send_selectors, timeout=10, clickable=True)
            if not send_button:
                self._update_status("❌ No se encontró el botón de enviar")
                return False

            if not self._safe_click_optimized(send_button):
                self._update_status("❌ No se pudo hacer click en enviar")
                return False

            time.sleep(2.5)  # Reducido de 5

            self._update_status("✅ Imagen enviada correctamente")
            return True

        except Exception as e:
            self._update_status(f"❌ Error al enviar imagen: {str(e)}")
            return False

    def _send_message_optimized(self, message_data: Dict[str, Any]) -> bool:
        """
        Envía un mensaje (texto y/o imagen) con estrategia optimizada

        Args:
            message_data: Datos del mensaje con 'texto' e 'imagen' opcional

        Returns:
            True si se envió correctamente
        """
        try:
            if not self._check_session_alive():
                self._update_status("Sesión perdida, no se puede enviar mensaje")
                return False

            # Compatibilidad con mensajes de texto simple
            if isinstance(message_data, str):
                return self._send_text_message_optimized(message_data)

            text = message_data.get('texto', '').strip()
            image_filename = message_data.get('imagen')

            # Si hay imagen y texto, enviar por separado pero optimizado
            if image_filename and text:
                image_path = os.path.join("imagenes_mensajes", image_filename)

                if not os.path.exists(image_path):
                    self._update_status(f"⚠️ Imagen no encontrada: {image_path}")
                    self._update_status("📝 Enviando solo el texto...")
                    return self._send_text_message_optimized(text)

                if not self._validate_image_file_cached(image_path):
                    self._update_status("📝 Imagen no válida, enviando solo el texto...")
                    return self._send_text_message_optimized(text)

                # Estrategia optimizada: Imagen primero, luego texto
                self._update_status("📤 Enviando imagen y texto por separado...")

                # 1. Enviar imagen
                image_sent = self._send_image_only_optimized(image_path)
                if not image_sent:
                    self._update_status("⚠️ Error enviando imagen, intentando solo con texto...")
                    return self._send_text_message_optimized(text)

                # 2. Esperar menos tiempo
                time.sleep(1)  # Reducido de 2

                # 3. Enviar texto
                text_sent = self._send_text_message_optimized(text)
                if not text_sent:
                    self._update_status("⚠️ Imagen enviada pero falló el texto")
                    return True  # Al menos la imagen se envió

                self._update_status("✅ Imagen y texto enviados correctamente")
                return True

            # Si solo hay imagen
            elif image_filename:
                image_path = os.path.join("imagenes_mensajes", image_filename)

                if not os.path.exists(image_path):
                    self._update_status(f"❌ Imagen no encontrada: {image_path}")
                    return False

                if not self._validate_image_file_cached(image_path):
                    self._update_status("❌ Imagen no válida")
                    return False

                return self._send_image_only_optimized(image_path)

            # Si solo hay texto
            elif text:
                return self._send_text_message_optimized(text)

            else:
                self._update_status("❌ Mensaje vacío")
                return False

        except Exception as e:
            self._update_status(f"❌ Error procesando mensaje: {str(e)}")
            return False

    def send_message_to_contact(self, phone_number: str, message_data: Dict[str, Any]) -> bool:
        """
        Envía un mensaje a un contacto específico (optimizado)

        Args:
            phone_number: Número de teléfono
            message_data: Datos del mensaje

        Returns:
            True si se envió correctamente
        """
        try:
            self._update_status(f"📱 Preparando envío a {phone_number}...")

            if not self._check_session_alive():
                self._update_status("❌ Sesión del navegador perdida")
                return False

            if not self._search_and_open_contact_optimized(phone_number):
                self._update_status(f"❌ No se pudo abrir conversación con {phone_number}")
                return False

            if self._send_message_optimized(message_data):
                self._update_status(f"✅ Mensaje enviado correctamente a {phone_number}")
                return True
            else:
                self._update_status(f"❌ Error al enviar mensaje a {phone_number}")
                return False

        except Exception as e:
            self._update_status(f"❌ Error general enviando a {phone_number}: {str(e)}")
            return False

    def start_automation(self, phone_numbers: List[str], messages: List[Dict[str, Any]],
                         min_interval: int, max_interval: int):
        """
        Inicia la automatización del envío de mensajes (optimizado)

        Args:
            phone_numbers: Lista de números de teléfono
            messages: Lista de mensajes con formato {'texto': str, 'imagen': str}
            min_interval: Intervalo mínimo entre mensajes (segundos)
            max_interval: Intervalo máximo entre mensajes (segundos)
        """
        if self.is_running:
            self._update_status("⚠️ La automatización ya está en ejecución")
            return

        try:
            self.is_running = True
            self.current_session_contacts = phone_numbers.copy()
            self.current_session_messages = messages.copy()

            # Limpiar cache
            self._element_cache = {}
            self._last_contact = None
            if hasattr(self, '_validated_images'):
                delattr(self, '_validated_images')

            self._update_status("🚀 Iniciando automatización...")

            if not self._initialize_driver():
                self.is_running = False
                return

            if not self._open_whatsapp_web():
                self.close()
                self.is_running = False
                return

            if not messages:
                self._update_status("❌ No hay mensajes configurados")
                self.close()
                self.is_running = False
                return

            if not phone_numbers:
                self._update_status("❌ No hay contactos configurados")
                self.close()
                self.is_running = False
                return

            self._update_status(f"📊 Iniciando envío a {len(phone_numbers)} contactos con {len(messages)} mensajes")

            messages_sent = 0
            messages_failed = 0

            for i, phone_number in enumerate(phone_numbers):
                if not self.is_running:
                    self._update_status("⏹ Automatización detenida por el usuario")
                    break

                try:
                    if not self._check_session_alive():
                        self._update_status("❌ Sesión perdida, deteniendo automatización")
                        break

                    selected_message = random.choice(messages)

                    message_text = selected_message.get('texto', '')[:50] + "..." if len(
                        selected_message.get('texto', '')) > 50 else selected_message.get('texto', '')
                    has_image = selected_message.get('imagen') is not None
                    has_emoji = self._has_emoji_or_unicode(selected_message.get('texto', ''))

                    emoji_indicator = " 😀" if has_emoji else ""
                    image_indicator = " 📷" if has_image else ""
                    message_info = f"'{message_text}'{emoji_indicator}{image_indicator}"

                    self._update_status(f"📱 ({i + 1}/{len(phone_numbers)}) Enviando a {phone_number}: {message_info}")

                    if self.send_message_to_contact(phone_number, selected_message):
                        messages_sent += 1
                    else:
                        messages_failed += 1

                    if i < len(phone_numbers) - 1 and self.is_running:
                        wait_time = random.randint(min_interval, max_interval)
                        self._update_status(f"⏱ Esperando {wait_time} segundos antes del siguiente mensaje...")

                        for _ in range(wait_time):
                            if not self.is_running:
                                break
                            time.sleep(1)

                except Exception as e:
                    messages_failed += 1
                    self._update_status(f"❌ Error con contacto {phone_number}: {str(e)}")
                    continue

            if self.is_running:
                self._update_status(
                    f"✅ Automatización completada: {messages_sent} enviados, {messages_failed} fallidos")
            else:
                self._update_status(f"⏹ Automatización detenida: {messages_sent} enviados, {messages_failed} fallidos")

        except Exception as e:
            self._update_status(f"❌ Error en automatización: {str(e)}")
        finally:
            self.is_running = False
            self.close()

    def stop_automation(self):
        """
        Detiene la automatización en curso
        """
        if self.is_running:
            self._update_status("🛑 Deteniendo automatización...")
            self.is_running = False
        else:
            self._update_status("ℹ️ No hay automatización en ejecución")

    def is_active(self) -> bool:
        """
        Verifica si el bot está activo

        Returns:
            True si está ejecutándose
        """
        return self.is_running

    def close(self):
        """
        Cierra el navegador y limpia recursos
        """
        try:
            if self.driver:
                self._update_status("🔄 Cerrando navegador...")
                self.driver.quit()
                self.driver = None
        except Exception as e:
            self._update_status(f"⚠️ Error al cerrar navegador: {str(e)}")
        finally:
            self.is_running = False
            # Limpiar cache
            self._element_cache = {}
            self._last_contact = None

    def get_session_info(self) -> Dict[str, Any]:
        """
        Obtiene información de la sesión actual

        Returns:
            Diccionario con información de la sesión
        """
        return {
            'is_running': self.is_running,
            'contacts_count': len(self.current_session_contacts),
            'messages_count': len(self.current_session_messages),
            'driver_active': self.driver is not None
        }