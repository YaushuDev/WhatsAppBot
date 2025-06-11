# whatsapp_bot.py
"""
Bot de WhatsApp automatizado con soporte completo para emoticones
Maneja la automatización del envío de mensajes a través de WhatsApp Web usando Selenium.
Incluye soporte robusto para emoticones y caracteres Unicode mediante JavaScript injection,
solucionando las limitaciones de ChromeDriver con caracteres fuera del BMP.
Soporta envío de mensajes con texto e imágenes por separado para mayor confiabilidad.
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
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, \
    ElementClickInterceptedException
from typing import List, Dict, Any, Callable, Optional


class WhatsAppBot:
    """
    Bot automatizado para WhatsApp Web con soporte completo para emoticones y caracteres Unicode
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
        self.wait_timeout = 20
        self.current_session_contacts = []
        self.current_session_messages = []

        # Configuración de Chrome
        self.chrome_options = self._configure_chrome_options()

    def _configure_chrome_options(self) -> Options:
        """
        Configura las opciones de Chrome para el bot con soporte mejorado para Unicode

        Returns:
            Opciones configuradas de Chrome
        """
        options = Options()

        # Configuración básica
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-extensions")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")

        # Configuración para soporte de Unicode y emoticones
        options.add_argument("--lang=es")
        options.add_argument("--accept-lang=es-ES,es,en")

        # Configuración de usuario para mantener sesión
        user_data_dir = os.path.join(os.getcwd(), "chrome_user_data")
        options.add_argument(f"--user-data-dir={user_data_dir}")

        # Configuración de medios para imágenes y Unicode
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
            "intl.charset_default": "UTF-8"
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
            # Patrón para detectar emoticones y caracteres Unicode fuera del BMP
            emoji_pattern = re.compile(
                "["
                "\U0001F600-\U0001F64F"  # emoticones faciales
                "\U0001F300-\U0001F5FF"  # símbolos & pictogramas
                "\U0001F680-\U0001F6FF"  # transporte & símbolos de mapa
                "\U0001F1E0-\U0001F1FF"  # banderas (iOS)
                "\U00002500-\U00002BEF"  # símbolos varios
                "\U00002702-\U000027B0"
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
            # Si hay algún error en la detección, asumir que tiene caracteres especiales
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
            # Convertir a JSON para escape automático y luego quitar las comillas
            escaped = json.dumps(text, ensure_ascii=False)[1:-1]
            return escaped
        except Exception:
            # Fallback: escape manual básico
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
            # Intentar acceder al título de la página
            _ = self.driver.title
            return True
        except Exception:
            return False

    def _wait_for_element(self, selectors: List[str], timeout: int = 15, clickable: bool = False) -> Optional[Any]:
        """
        Espera a que aparezca un elemento usando múltiples selectores

        Args:
            selectors: Lista de selectores XPath a probar
            timeout: Tiempo máximo de espera
            clickable: Si el elemento debe ser clickeable

        Returns:
            Elemento encontrado o None
        """
        for selector in selectors:
            try:
                wait = WebDriverWait(self.driver, timeout)
                if clickable:
                    element = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                else:
                    element = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                return element
            except TimeoutException:
                continue
        return None

    def _safe_click(self, element, max_attempts: int = 3) -> bool:
        """
        Hace click de forma segura evitando interceptaciones

        Args:
            element: Elemento a hacer click
            max_attempts: Máximo número de intentos

        Returns:
            True si el click fue exitoso
        """
        for attempt in range(max_attempts):
            try:
                # Scroll al elemento si es necesario
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(0.5)

                # Intentar click normal
                element.click()
                return True

            except ElementClickInterceptedException:
                try:
                    # Intentar click con JavaScript
                    self.driver.execute_script("arguments[0].click();", element)
                    return True
                except:
                    # Intentar con ActionChains
                    try:
                        ActionChains(self.driver).move_to_element(element).click().perform()
                        return True
                    except:
                        if attempt < max_attempts - 1:
                            time.sleep(1)
                            continue
                        return False
            except Exception as e:
                if attempt < max_attempts - 1:
                    time.sleep(1)
                    continue
                return False
        return False

    def _open_whatsapp_web(self) -> bool:
        """
        Abre WhatsApp Web y espera a que se cargue

        Returns:
            True si se abrió correctamente
        """
        try:
            self._update_status("Abriendo WhatsApp Web...")
            self.driver.get("https://web.whatsapp.com")

            # Selectores actualizados para detectar carga
            main_selectors = [
                "//div[@contenteditable='true'][@data-tab='3']",
                "//div[contains(@class, 'two')]//div[@contenteditable='true']",
                "//div[@title='Nueva conversación']",
                "//div[@role='textbox'][@title='Buscar o crear un chat nuevo']",
                "//div[@data-testid='search']//div[@contenteditable='true']"
            ]

            self._update_status("Esperando carga de WhatsApp Web...")

            # Intentar detectar interfaz principal
            main_element = self._wait_for_element(main_selectors, timeout=30)
            if main_element:
                self._update_status("WhatsApp Web cargado correctamente")
                return True

            # Si no encuentra la interfaz, buscar QR
            qr_selectors = [
                "//canvas[@aria-label='Scan me!']",
                "//div[@data-ref]//canvas",
                "//canvas",
                "//div[contains(@class, 'qr-code')]//canvas"
            ]

            qr_element = self._wait_for_element(qr_selectors, timeout=10)
            if qr_element:
                self._update_status("Escanea el código QR en WhatsApp Web para continuar")

                # Esperar a que se complete el login
                main_element = self._wait_for_element(main_selectors, timeout=120)
                if main_element:
                    self._update_status("QR escaneado correctamente, WhatsApp Web listo")
                    return True

            self._update_status("No se pudo cargar WhatsApp Web correctamente")
            return False

        except Exception as e:
            self._update_status(f"Error al abrir WhatsApp Web: {str(e)}")
            return False

    def _search_and_open_contact(self, phone_number: str) -> bool:
        """
        Busca y abre un contacto específico

        Args:
            phone_number: Número de teléfono del contacto

        Returns:
            True si se abrió el contacto correctamente
        """
        try:
            if not self._check_session_alive():
                self._update_status("Sesión perdida, reintentando...")
                return False

            # Selectores actualizados para búsqueda
            search_selectors = [
                "//div[@contenteditable='true'][@data-tab='3']",
                "//div[@role='textbox'][@title='Buscar o crear un chat nuevo']",
                "//div[@data-testid='search']//div[@contenteditable='true']",
                "//div[contains(@class, 'two')]//div[@contenteditable='true']"
            ]

            search_box = self._wait_for_element(search_selectors, timeout=15, clickable=True)
            if not search_box:
                self._update_status("No se encontró el campo de búsqueda")
                return False

            # Limpiar y escribir el número
            if not self._safe_click(search_box):
                return False

            search_box.clear()
            time.sleep(1)
            search_box.send_keys(phone_number)
            time.sleep(3)
            search_box.send_keys(Keys.ENTER)
            time.sleep(4)

            # Verificar si se abrió la conversación
            message_selectors = [
                "//div[@contenteditable='true'][@data-tab='10']",
                "//div[@role='textbox'][@title='Escribe un mensaje']",
                "//div[@data-testid='conversation-compose-box-input']",
                "//div[contains(@class, 'copyable-text')][@data-tab='10']"
            ]

            message_box = self._wait_for_element(message_selectors, timeout=10)
            if message_box:
                return True

            # Intentar con URL directa
            self._update_status(f"Intentando abrir {phone_number} con URL directa...")
            whatsapp_url = f"https://web.whatsapp.com/send?phone={phone_number}"
            self.driver.get(whatsapp_url)
            time.sleep(6)

            message_box = self._wait_for_element(message_selectors, timeout=15)
            return message_box is not None

        except Exception as e:
            self._update_status(f"Error al buscar contacto {phone_number}: {str(e)}")
            return False

    def _send_text_message_javascript(self, message_text: str) -> bool:
        """
        Envía un mensaje de texto usando JavaScript para soporte completo de emoticones

        Args:
            message_text: Texto del mensaje

        Returns:
            True si se envió correctamente
        """
        try:
            self._update_status("📝 Enviando mensaje con soporte de emoticones...")

            # Escapar el texto para JavaScript
            escaped_text = self._escape_unicode_for_js(message_text)

            # Script JavaScript mejorado para envío con emoticones
            js_script = f"""
            function sendMessageWithEmojis() {{
                try {{
                    // Buscar el campo de mensaje
                    const messageBox = document.querySelector('[contenteditable="true"][data-tab="10"]') ||
                                     document.querySelector('[role="textbox"][title*="mensaje"]') ||
                                     document.querySelector('[data-testid="conversation-compose-box-input"]') ||
                                     document.querySelector('[contenteditable="true"]:not([data-tab="3"])');

                    if (!messageBox) {{
                        console.log("No se encontró el campo de mensaje");
                        return false;
                    }}

                    // Hacer foco en el campo
                    messageBox.focus();

                    // Limpiar contenido existente
                    messageBox.innerHTML = '';

                    // Insertar el texto con emoticones
                    const textToSend = "{escaped_text}";

                    // Método 1: Insertar como texto plano (preserva emoticones)
                    const textNode = document.createTextNode(textToSend);
                    messageBox.appendChild(textNode);

                    // Disparar eventos para que WhatsApp reconozca el cambio
                    const inputEvent = new InputEvent('input', {{
                        bubbles: true,
                        cancelable: true,
                        data: textToSend
                    }});
                    messageBox.dispatchEvent(inputEvent);

                    // Esperar un poco y enviar
                    setTimeout(() => {{
                        // Buscar y hacer click en el botón de enviar
                        const sendButton = document.querySelector('[data-testid="send"]') ||
                                         document.querySelector('[aria-label*="Enviar"]') ||
                                         document.querySelector('[title*="Enviar"]') ||
                                         document.querySelector('span[data-icon="send"]').closest('button');

                        if (sendButton) {{
                            sendButton.click();
                            console.log("Mensaje enviado correctamente");
                            return true;
                        }} else {{
                            console.log("No se encontró el botón enviar");
                            return false;
                        }}
                    }}, 500);

                    return true;

                }} catch (error) {{
                    console.log("Error en sendMessageWithEmojis:", error);
                    return false;
                }}
            }}

            return sendMessageWithEmojis();
            """

            # Ejecutar el script JavaScript
            result = self.driver.execute_script(js_script)

            # Esperar a que se complete el envío
            time.sleep(3)

            if result is not False:
                self._update_status("✅ Mensaje con emoticones enviado correctamente")
                return True
            else:
                # Fallback al método tradicional si JavaScript falla
                self._update_status("⚠️ Fallback al método tradicional...")
                return self._send_text_message_fallback(message_text)

        except Exception as e:
            self._update_status(f"❌ Error en envío JavaScript: {str(e)}")
            # Fallback al método tradicional
            return self._send_text_message_fallback(message_text)

    def _send_text_message_fallback(self, message_text: str) -> bool:
        """
        Método de fallback para enviar mensajes sin emoticones

        Args:
            message_text: Texto del mensaje

        Returns:
            True si se envió correctamente
        """
        try:
            self._update_status("📝 Enviando con método tradicional...")

            # Selectores actualizados para el campo de mensaje
            message_selectors = [
                "//div[@contenteditable='true'][@data-tab='10']",
                "//div[@role='textbox'][@title='Escribe un mensaje']",
                "//div[@data-testid='conversation-compose-box-input']",
                "//div[contains(@class, 'copyable-text')][@data-tab='10']"
            ]

            message_box = self._wait_for_element(message_selectors, timeout=15, clickable=True)
            if not message_box:
                self._update_status("No se encontró el campo de mensaje")
                return False

            if not self._safe_click(message_box):
                return False

            message_box.clear()
            time.sleep(1)

            # Filtrar caracteres problemáticos para fallback
            safe_text = self._filter_bmp_characters(message_text)

            # Enviar mensaje línea por línea
            lines = safe_text.split('\n')
            for i, line in enumerate(lines):
                message_box.send_keys(line)
                if i < len(lines) - 1:
                    message_box.send_keys(Keys.SHIFT + Keys.ENTER)

            time.sleep(1)
            message_box.send_keys(Keys.ENTER)
            time.sleep(3)

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
            # Mantener solo caracteres dentro del BMP (U+0000 a U+FFFF)
            filtered = ''.join(char for char in text if ord(char) <= 0xFFFF)

            # Si se filtraron caracteres, informar
            if len(filtered) != len(text):
                self._update_status("⚠️ Algunos emoticones fueron filtrados por compatibilidad")

            return filtered
        except Exception:
            # Si hay error, devolver texto original
            return text

    def _send_text_message(self, message_text: str) -> bool:
        """
        Envía un mensaje de texto con soporte inteligente para emoticones

        Args:
            message_text: Texto del mensaje

        Returns:
            True si se envió correctamente
        """
        try:
            if not self._check_session_alive():
                return False

            # Detectar si el mensaje contiene emoticones
            if self._has_emoji_or_unicode(message_text):
                self._update_status("😀 Detectados emoticones, usando método avanzado...")
                return self._send_text_message_javascript(message_text)
            else:
                self._update_status("📝 Enviando texto simple...")
                return self._send_text_message_fallback(message_text)

        except Exception as e:
            self._update_status(f"Error al enviar mensaje de texto: {str(e)}")
            return False

    def _validate_image_file(self, image_path: str) -> bool:
        """
        Valida que el archivo de imagen existe y es válido

        Args:
            image_path: Ruta de la imagen

        Returns:
            True si la imagen es válida
        """
        try:
            if not os.path.exists(image_path):
                self._update_status(f"Archivo no encontrado: {image_path}")
                return False

            # Verificar tamaño del archivo (máximo 64MB)
            file_size = os.path.getsize(image_path)
            if file_size > 64 * 1024 * 1024:
                self._update_status(f"Archivo demasiado grande: {file_size / (1024 * 1024):.1f}MB")
                return False

            # Verificar extensión
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
            ext = os.path.splitext(image_path)[1].lower()
            if ext not in valid_extensions:
                self._update_status(f"Formato de imagen no soportado: {ext}")
                return False

            return True

        except Exception as e:
            self._update_status(f"Error validando imagen: {str(e)}")
            return False

    def _send_image_only(self, image_path: str) -> bool:
        """
        Envía solo una imagen sin texto

        Args:
            image_path: Ruta de la imagen

        Returns:
            True si se envió correctamente
        """
        try:
            self._update_status(f"🖼️ Enviando imagen: {os.path.basename(image_path)}")

            # Selectores actualizados para el botón adjuntar
            attach_selectors = [
                "//div[@title='Adjuntar']",
                "//button[@aria-label='Adjuntar']",
                "//span[@data-icon='plus']/../..",
                "//span[@data-icon='attach-menu-plus']/../..",
                "//div[@role='button'][@aria-label='Adjuntar']"
            ]

            attach_button = self._wait_for_element(attach_selectors, timeout=10, clickable=True)
            if not attach_button:
                self._update_status("❌ No se encontró el botón adjuntar")
                return False

            if not self._safe_click(attach_button):
                return False

            time.sleep(2)

            # Selectores para la opción de fotos
            photos_selectors = [
                "//input[@accept='image/*,video/mp4,video/3gpp,video/quicktime']",
                "//input[@type='file'][contains(@accept, 'image')]",
                "//input[@accept][@type='file']",
                "//li[@data-testid='mi-attach-image']//input",
                "//input[contains(@accept, 'image')]"
            ]

            # Buscar directamente el input de archivo
            file_input = self._wait_for_element(photos_selectors, timeout=10)

            if not file_input:
                # Intentar hacer clic en la opción de fotos primero
                photos_option_selectors = [
                    "//span[contains(text(), 'Fotos y videos')]",
                    "//div[contains(text(), 'Fotos y videos')]",
                    "//li[@data-testid='mi-attach-image']",
                    "//div[@role='button'][contains(., 'Foto')]"
                ]

                photos_option = self._wait_for_element(photos_option_selectors, timeout=8, clickable=True)
                if photos_option:
                    if self._safe_click(photos_option):
                        time.sleep(2)
                        file_input = self._wait_for_element(photos_selectors, timeout=10)

            if not file_input:
                self._update_status("❌ No se encontró el input de archivo")
                return False

            # Enviar archivo
            absolute_path = os.path.abspath(image_path)
            self._update_status(f"📎 Cargando imagen...")
            file_input.send_keys(absolute_path)
            time.sleep(6)  # Tiempo para cargar la imagen

            # Enviar imagen directamente sin caption
            send_selectors = [
                "//span[@data-icon='send']/..",
                "//button[@aria-label='Enviar']",
                "//div[@role='button'][@aria-label='Enviar']",
                "//span[@data-testid='send']/..",
                "//button[contains(@class, 'send')]",
                "//div[@data-testid='compose-btn-send']"
            ]

            send_button = self._wait_for_element(send_selectors, timeout=15, clickable=True)
            if not send_button:
                self._update_status("❌ No se encontró el botón de enviar")
                return False

            if not self._safe_click(send_button):
                self._update_status("❌ No se pudo hacer click en enviar")
                return False

            time.sleep(5)  # Tiempo para que se envíe

            self._update_status("✅ Imagen enviada correctamente")
            return True

        except Exception as e:
            self._update_status(f"❌ Error al enviar imagen: {str(e)}")
            return False

    def _send_message(self, message_data: Dict[str, Any]) -> bool:
        """
        Envía un mensaje (texto y/o imagen) con estrategia mejorada

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
                return self._send_text_message(message_data)

            text = message_data.get('texto', '').strip()
            image_filename = message_data.get('imagen')

            # Si hay imagen y texto, enviar por separado
            if image_filename and text:
                image_path = os.path.join("imagenes_mensajes", image_filename)

                if not os.path.exists(image_path):
                    self._update_status(f"⚠️ Imagen no encontrada: {image_path}")
                    # Si no se encuentra la imagen, enviar solo el texto
                    self._update_status("📝 Enviando solo el texto...")
                    return self._send_text_message(text)

                if not self._validate_image_file(image_path):
                    # Si la imagen no es válida, enviar solo el texto
                    self._update_status("📝 Imagen no válida, enviando solo el texto...")
                    return self._send_text_message(text)

                # Estrategia: Primero imagen, luego texto
                self._update_status("📤 Enviando imagen y texto por separado...")

                # 1. Enviar imagen
                image_sent = self._send_image_only(image_path)
                if not image_sent:
                    self._update_status("⚠️ Error enviando imagen, intentando solo con texto...")
                    return self._send_text_message(text)

                # 2. Esperar un poco
                time.sleep(2)

                # 3. Enviar texto
                text_sent = self._send_text_message(text)
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

                if not self._validate_image_file(image_path):
                    self._update_status("❌ Imagen no válida")
                    return False

                return self._send_image_only(image_path)

            # Si solo hay texto
            elif text:
                return self._send_text_message(text)

            else:
                self._update_status("❌ Mensaje vacío")
                return False

        except Exception as e:
            self._update_status(f"❌ Error procesando mensaje: {str(e)}")
            return False

    def send_message_to_contact(self, phone_number: str, message_data: Dict[str, Any]) -> bool:
        """
        Envía un mensaje a un contacto específico

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

            if not self._search_and_open_contact(phone_number):
                self._update_status(f"❌ No se pudo abrir conversación con {phone_number}")
                return False

            if self._send_message(message_data):
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
        Inicia la automatización del envío de mensajes

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