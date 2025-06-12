# whatsapp_messaging.py
"""
Sistema de envío de mensajes para el Bot de WhatsApp
Este módulo se encarga exclusivamente del envío de todos los tipos de mensajes en WhatsApp Web,
incluyendo texto simple, texto con emoticones, imágenes, y envío conjunto de imagen con caption.
Incluye soporte completo para Unicode, múltiples estrategias de envío y validaciones robustas.
"""

import os
import time
from typing import Optional, Callable, Dict, Any
from selenium.webdriver.common.keys import Keys
from whatsapp_utils import (WhatsAppConstants, UnicodeHandler, JavaScriptInjector,
                            FileValidator, get_absolute_image_path)
from whatsapp_driver import ChromeDriverManager


class MessageSender:
    """
    Gestor especializado para envío de mensajes en WhatsApp Web
    """

    def __init__(self, driver_manager: ChromeDriverManager, status_callback: Optional[Callable] = None):
        """
        Inicializa el gestor de envío de mensajes

        Args:
            driver_manager: Instancia del gestor de Chrome
            status_callback: Función callback para reportar estado
        """
        self.driver_manager = driver_manager
        self.status_callback = status_callback
        self.file_validator = FileValidator()

    def _update_status(self, message: str):
        """
        Actualiza el estado y notifica mediante callback

        Args:
            message: Mensaje de estado
        """
        print(f"[Messaging] {message}")
        if self.status_callback:
            self.status_callback(message)

    def _get_message_box(self):
        """
        Obtiene el campo de entrada de mensajes

        Returns:
            Elemento del campo de mensaje o None
        """
        return self.driver_manager.wait_for_element(
            WhatsAppConstants.SELECTORS['message_box'],
            timeout=WhatsAppConstants.ELEMENT_WAIT_TIMEOUT,
            clickable=True
        )

    def _send_text_with_javascript(self, message_text: str) -> bool:
        """
        Envía texto usando JavaScript con soporte completo para emoticones

        Args:
            message_text: Texto del mensaje

        Returns:
            True si se envió correctamente
        """
        try:
            self._update_status("📝 Enviando mensaje con soporte de emoticones...")

            # Crear script JavaScript usando la utilidad
            js_script = JavaScriptInjector.create_message_sender_script(message_text)

            # Ejecutar script
            result = self.driver_manager.execute_script(js_script)
            time.sleep(1.5)

            if result is not False:
                self._update_status("✅ Mensaje con emoticones enviado correctamente")
                return True
            else:
                return self._send_text_fallback(message_text)

        except Exception as e:
            self._update_status(f"❌ Error en envío JavaScript: {str(e)}")
            return self._send_text_fallback(message_text)

    def _send_text_fallback(self, message_text: str) -> bool:
        """
        Método de fallback para enviar texto usando Selenium tradicional

        Args:
            message_text: Texto del mensaje

        Returns:
            True si se envió correctamente
        """
        try:
            self._update_status("📝 Enviando con método tradicional...")

            message_box = self._get_message_box()
            if not message_box:
                self._update_status("No se encontró el campo de mensaje")
                return False

            if not self.driver_manager.safe_click(message_box):
                return False

            message_box.clear()
            time.sleep(WhatsAppConstants.SHORT_DELAY)

            # Filtrar caracteres problemáticos para fallback
            safe_text = UnicodeHandler.filter_bmp_characters(message_text)

            # Enviar línea por línea para manejar saltos de línea
            lines = safe_text.split('\n')
            for i, line in enumerate(lines):
                message_box.send_keys(line)
                if i < len(lines) - 1:
                    message_box.send_keys(Keys.SHIFT + Keys.ENTER)

            time.sleep(0.5)
            message_box.send_keys(Keys.ENTER)
            time.sleep(1.5)

            return True

        except Exception as e:
            self._update_status(f"Error en método fallback: {str(e)}")
            return False

    def send_text_message(self, message_text: str) -> bool:
        """
        Envía un mensaje de texto con detección inteligente de emoticones

        Args:
            message_text: Texto del mensaje a enviar

        Returns:
            True si se envió correctamente
        """
        try:
            if not message_text or not message_text.strip():
                self._update_status("❌ Mensaje de texto vacío")
                return False

            if not self.driver_manager.is_session_alive():
                self._update_status("❌ Sesión no activa")
                return False

            # Detección inteligente de emoticones
            if UnicodeHandler.has_emoji_or_unicode(message_text):
                self._update_status("😀 Detectados emoticones, usando método avanzado...")
                return self._send_text_with_javascript(message_text)
            else:
                self._update_status("📝 Enviando texto simple...")
                return self._send_text_fallback(message_text)

        except Exception as e:
            self._update_status(f"❌ Error al enviar mensaje de texto: {str(e)}")
            return False

    def _get_attach_button(self):
        """
        Obtiene el botón de adjuntar archivos

        Returns:
            Elemento del botón adjuntar o None
        """
        return self.driver_manager.wait_for_element(
            WhatsAppConstants.SELECTORS['attach_button'],
            timeout=8,
            clickable=True
        )

    def _get_file_input(self):
        """
        Obtiene el input de archivo para imágenes

        Returns:
            Elemento input de archivo o None
        """
        return self.driver_manager.wait_for_element(
            WhatsAppConstants.SELECTORS['file_input'],
            timeout=5
        )

    def _open_file_picker(self) -> bool:
        """
        Abre el selector de archivos

        Returns:
            True si se abrió correctamente
        """
        try:
            # Buscar botón adjuntar
            attach_button = self._get_attach_button()
            if not attach_button:
                self._update_status("❌ No se encontró el botón adjuntar")
                return False

            if not self.driver_manager.safe_click(attach_button):
                return False

            time.sleep(WhatsAppConstants.MEDIUM_DELAY)

            # Buscar input directo primero
            file_input = self._get_file_input()
            if file_input:
                return True

            # Si no hay input directo, buscar opción de fotos
            photos_option_selectors = [
                "li[data-testid='mi-attach-image']",
                "span:contains('Fotos y videos')",
                "div[role='button'][title*='foto']"
            ]

            photos_option = self.driver_manager.wait_for_element(
                photos_option_selectors,
                timeout=5,
                clickable=True
            )

            if photos_option and self.driver_manager.safe_click(photos_option):
                time.sleep(WhatsAppConstants.MEDIUM_DELAY)
                return self._get_file_input() is not None

            return False

        except Exception as e:
            self._update_status(f"Error abriendo selector de archivos: {str(e)}")
            return False

    def _upload_image_file(self, image_path: str) -> bool:
        """
        Sube un archivo de imagen

        Args:
            image_path: Ruta de la imagen

        Returns:
            True si se subió correctamente
        """
        try:
            file_input = self._get_file_input()
            if not file_input:
                self._update_status("❌ No se encontró el input de archivo")
                return False

            absolute_path = os.path.abspath(image_path)
            self._update_status(f"📎 Cargando imagen: {os.path.basename(image_path)}")

            file_input.send_keys(absolute_path)
            time.sleep(3)  # Tiempo para carga de imagen

            return True

        except Exception as e:
            self._update_status(f"Error subiendo imagen: {str(e)}")
            return False

    def _write_caption(self, caption_text: str) -> bool:
        """
        Escribe un caption para la imagen

        Args:
            caption_text: Texto del caption

        Returns:
            True si se escribió correctamente
        """
        try:
            self._update_status("📝 Escribiendo caption...")

            # Selectores para el área de caption (XPaths específicos + fallbacks)
            caption_selectors = [
                "//*[@id='app']/div/div[3]/div/div[2]/div[2]/span/div/div/div/div[2]/div/div[1]/div[3]/div/div/div[2]/div[1]/div[1]/p",
                "//*[@id='app']/div/div[3]/div/div[2]/div[2]/span/div/div/div/div[2]/div/div[1]/div[3]/div/div/div[2]",
                "div[contenteditable='true'][data-tab='10']",
                "div[role='textbox'][title*='mensaje']"
            ]

            caption_box = self.driver_manager.wait_for_element(caption_selectors, timeout=8, clickable=True)

            if caption_box:
                if not self.driver_manager.safe_click(caption_box):
                    self._update_status("⚠️ No se pudo hacer click en caption, continuando...")
                else:
                    time.sleep(0.5)

                # Usar JavaScript para caption con emoticones
                if UnicodeHandler.has_emoji_or_unicode(caption_text):
                    self._update_status("😀 Caption con emoticones detectado...")
                    js_script = JavaScriptInjector.create_caption_writer_script(caption_text)

                    caption_result = self.driver_manager.execute_script(js_script)
                    if not caption_result:
                        # Fallback: escribir directamente
                        caption_box.clear()
                        caption_box.send_keys(UnicodeHandler.filter_bmp_characters(caption_text))
                else:
                    # Texto simple
                    caption_box.clear()
                    caption_box.send_keys(caption_text)

                time.sleep(WhatsAppConstants.MEDIUM_DELAY)
                return True
            else:
                self._update_status("⚠️ No se encontró área de caption")
                return False

        except Exception as e:
            self._update_status(f"Error escribiendo caption: {str(e)}")
            return False

    def _send_media(self) -> bool:
        """
        Envía el archivo multimedia cargado

        Returns:
            True si se envió correctamente
        """
        try:
            send_button = self.driver_manager.wait_for_element(
                WhatsAppConstants.SELECTORS['send_button'],
                timeout=10,
                clickable=True
            )

            if not send_button:
                self._update_status("❌ No se encontró el botón de enviar")
                return False

            if not self.driver_manager.safe_click(send_button):
                self._update_status("❌ No se pudo hacer click en enviar")
                return False

            time.sleep(WhatsAppConstants.LONG_DELAY)
            return True

        except Exception as e:
            self._update_status(f"Error enviando archivo: {str(e)}")
            return False

    def send_image_only(self, image_filename: str) -> bool:
        """
        Envía solo una imagen sin texto

        Args:
            image_filename: Nombre del archivo de imagen

        Returns:
            True si se envió correctamente
        """
        try:
            image_path = get_absolute_image_path(image_filename)
            if not image_path:
                self._update_status(f"❌ Imagen no encontrada: {image_filename}")
                return False

            if not self.file_validator.validate_image_file(image_path):
                self._update_status("❌ Imagen no válida")
                return False

            self._update_status(f"🖼️ Enviando imagen: {os.path.basename(image_path)}")

            # Abrir selector de archivos
            if not self._open_file_picker():
                return False

            # Subir imagen
            if not self._upload_image_file(image_path):
                return False

            # Enviar
            if self._send_media():
                self._update_status("✅ Imagen enviada correctamente")
                return True

            return False

        except Exception as e:
            self._update_status(f"❌ Error al enviar imagen: {str(e)}")
            return False

    def send_image_with_caption(self, image_filename: str, caption_text: str) -> bool:
        """
        Envía una imagen con texto como caption en un solo mensaje

        Args:
            image_filename: Nombre del archivo de imagen
            caption_text: Texto del caption

        Returns:
            True si se envió correctamente
        """
        try:
            image_path = get_absolute_image_path(image_filename)
            if not image_path:
                self._update_status(f"❌ Imagen no encontrada: {image_filename}")
                return False

            if not self.file_validator.validate_image_file(image_path):
                self._update_status("❌ Imagen no válida")
                return False

            self._update_status(f"🖼️📝 Enviando imagen con caption: {os.path.basename(image_path)}")

            # Abrir selector de archivos
            if not self._open_file_picker():
                return False

            # Subir imagen
            if not self._upload_image_file(image_path):
                return False

            # Escribir caption
            if not self._write_caption(caption_text):
                self._update_status("⚠️ Error con caption, enviando solo imagen...")

            # Enviar
            if self._send_media():
                self._update_status("✅ Imagen con caption enviada correctamente")
                return True

            return False

        except Exception as e:
            self._update_status(f"❌ Error al enviar imagen con caption: {str(e)}")
            return False

    def send_message(self, message_data: Dict[str, Any]) -> bool:
        """
        Envía un mensaje completo (texto y/o imagen) según configuración

        Args:
            message_data: Diccionario con 'texto', 'imagen' y 'envio_conjunto'

        Returns:
            True si se envió correctamente
        """
        try:
            if not self.driver_manager.is_session_alive():
                self._update_status("❌ Sesión perdida, no se puede enviar mensaje")
                return False

            # Compatibilidad con mensajes de texto simple
            if isinstance(message_data, str):
                return self.send_text_message(message_data)

            text = message_data.get('texto', '').strip()
            image_filename = message_data.get('imagen')
            envio_conjunto = message_data.get('envio_conjunto', False)

            # Envío conjunto: imagen con caption
            if image_filename and text and envio_conjunto:
                self._update_status("📤 Enviando imagen con caption (modo conjunto)...")
                return self.send_image_with_caption(image_filename, text)

            # Envío separado: imagen primero, luego texto
            elif image_filename and text and not envio_conjunto:
                self._update_status("📤 Enviando imagen y texto por separado...")

                # 1. Enviar imagen
                if not self.send_image_only(image_filename):
                    self._update_status("⚠️ Error enviando imagen, intentando solo con texto...")
                    return self.send_text_message(text)

                # 2. Esperar brevemente
                time.sleep(WhatsAppConstants.MEDIUM_DELAY)

                # 3. Enviar texto
                if not self.send_text_message(text):
                    self._update_status("⚠️ Imagen enviada pero falló el texto")
                    return True  # Al menos la imagen se envió

                self._update_status("✅ Imagen y texto enviados correctamente (separados)")
                return True

            # Solo imagen
            elif image_filename:
                return self.send_image_only(image_filename)

            # Solo texto
            elif text:
                return self.send_text_message(text)

            else:
                self._update_status("❌ Mensaje vacío")
                return False

        except Exception as e:
            self._update_status(f"❌ Error procesando mensaje: {str(e)}")
            return False

    def clear_cache(self):
        """
        Limpia el cache del validador de archivos
        """
        self.file_validator.clear_cache()