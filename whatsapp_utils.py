# whatsapp_utils.py
"""
Utilidades y funciones compartidas para el Bot de WhatsApp
Este módulo centraliza todas las funciones de utilidad comunes utilizadas por los diferentes
componentes del bot, incluyendo detección de Unicode, validaciones de archivos, manejo de
JavaScript y configuraciones compartidas para optimizar el rendimiento y mantener consistencia.
"""

import re
import os
import json
from typing import Dict, Any, Optional


class WhatsAppConstants:
    """
    Constantes y configuraciones compartidas del bot de WhatsApp
    """

    # Timeouts optimizados
    DEFAULT_WAIT_TIMEOUT = 15
    ELEMENT_WAIT_TIMEOUT = 10
    PAGE_LOAD_TIMEOUT = 30

    # Intervalos de tiempo (en segundos)
    SHORT_DELAY = 0.3
    MEDIUM_DELAY = 1.0
    LONG_DELAY = 2.5

    # Límites de archivos
    MAX_FILE_SIZE_MB = 64
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

    # Extensiones de imagen válidas
    VALID_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']

    # URLs de WhatsApp
    WHATSAPP_WEB_URL = "https://web.whatsapp.com"
    WHATSAPP_SEND_URL = "https://web.whatsapp.com/send?phone={}"

    # Selectores CSS/XPath más utilizados
    SELECTORS = {
        'search_box': [
            "div[contenteditable='true'][data-tab='3']",
            "div[role='textbox'][title*='Buscar']",
            "div[data-testid='search'] div[contenteditable='true']"
        ],
        'message_box': [
            "div[contenteditable='true'][data-tab='10']",
            "div[role='textbox'][title*='mensaje']",
            "div[data-testid='conversation-compose-box-input']"
        ],
        'attach_button': [
            "div[title='Adjuntar']",
            "button[aria-label='Adjuntar']",
            "span[data-icon='plus']",
            "span[data-icon='attach-menu-plus']",
            "[data-testid='clip']"
        ],
        'send_button': [
            "span[data-icon='send']",
            "button[aria-label='Enviar']",
            "div[role='button'][aria-label='Enviar']",
            "[data-testid='send']"
        ],
        'file_input': [
            "input[accept*='image']",
            "input[type='file'][accept*='image']",
            "input[type='file']",
            "li[data-testid='mi-attach-image'] input"
        ]
    }


class UnicodeHandler:
    """
    Manejador especializado para caracteres Unicode y emoticones
    """

    @staticmethod
    def has_emoji_or_unicode(text: str) -> bool:
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
            return True  # En caso de duda, asumir que tiene Unicode

    @staticmethod
    def escape_unicode_for_js(text: str) -> str:
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

    @staticmethod
    def filter_bmp_characters(text: str) -> str:
        """
        Filtra caracteres que no están en el Basic Multilingual Plane

        Args:
            text: Texto original

        Returns:
            Texto filtrado solo con caracteres BMP
        """
        try:
            filtered = ''.join(char for char in text if ord(char) <= 0xFFFF)
            return filtered
        except Exception:
            return text


class FileValidator:
    """
    Validador de archivos para el bot de WhatsApp
    """

    def __init__(self):
        self._validation_cache = {}

    def validate_image_file(self, image_path: str) -> bool:
        """
        Valida que el archivo de imagen existe y es válido (con cache)

        Args:
            image_path: Ruta de la imagen

        Returns:
            True si la imagen es válida
        """
        # Cache de validaciones para evitar re-validar
        if image_path in self._validation_cache:
            return self._validation_cache[image_path]

        try:
            if not os.path.exists(image_path):
                self._validation_cache[image_path] = False
                return False

            # Verificar tamaño del archivo
            file_size = os.path.getsize(image_path)
            if file_size > WhatsAppConstants.MAX_FILE_SIZE_BYTES:
                self._validation_cache[image_path] = False
                return False

            # Verificar extensión
            ext = os.path.splitext(image_path)[1].lower()
            if ext not in WhatsAppConstants.VALID_IMAGE_EXTENSIONS:
                self._validation_cache[image_path] = False
                return False

            self._validation_cache[image_path] = True
            return True

        except Exception:
            self._validation_cache[image_path] = False
            return False

    def clear_cache(self):
        """
        Limpia el cache de validaciones
        """
        self._validation_cache.clear()


class JavaScriptInjector:
    """
    Generador de scripts JavaScript para el bot
    """

    @staticmethod
    def create_message_sender_script(message_text: str) -> str:
        """
        Crea script JavaScript mejorado para enviar mensajes con soporte Unicode
        SOLUCION: Mejorada para evitar doble envío de mensajes con emoticones

        Args:
            message_text: Texto del mensaje a enviar

        Returns:
            Script JavaScript listo para ejecutar
        """
        escaped_text = UnicodeHandler.escape_unicode_for_js(message_text)

        return f"""
        function sendMessageOptimized() {{
            try {{
                // PASO 1: Buscar el campo de mensaje con selectores mejorados
                const messageBox = document.querySelector('[contenteditable="true"][data-tab="10"]') ||
                                 document.querySelector('[role="textbox"][title*="mensaje"]') ||
                                 document.querySelector('[data-testid="conversation-compose-box-input"]') ||
                                 document.querySelector('div[contenteditable="true"][dir="ltr"]');

                if (!messageBox) {{
                    console.log("MessageBox no encontrado");
                    return false;
                }}

                // PASO 2: Limpiar y preparar el campo
                messageBox.focus();
                messageBox.innerHTML = '';

                // PASO 3: Insertar el texto con método mejorado
                const textToSend = "{escaped_text}";

                // Usar execCommand como método primario para emoticones
                document.execCommand('insertText', false, textToSend);

                // Fallback: método de nodo de texto
                if (messageBox.textContent !== textToSend) {{
                    messageBox.innerHTML = '';
                    const textNode = document.createTextNode(textToSend);
                    messageBox.appendChild(textNode);
                }}

                // PASO 4: Disparar eventos necesarios
                const events = ['input', 'change', 'keyup'];
                events.forEach(eventType => {{
                    const event = new Event(eventType, {{
                        bubbles: true,
                        cancelable: true
                    }});
                    messageBox.dispatchEvent(event);
                }});

                // PASO 5: Esperar breve momento para que aparezca el botón de envío
                return new Promise(resolve => {{
                    setTimeout(() => {{
                        // Buscar botón de envío con selectores mejorados
                        const sendButton = document.querySelector('[data-testid="send"]') ||
                                         document.querySelector('button[aria-label*="Enviar"]') ||
                                         document.querySelector('span[data-icon="send"]')?.closest('button') ||
                                         document.querySelector('div[role="button"][aria-label*="Enviar"]') ||
                                         document.querySelector('button[aria-label*="Send"]');

                        if (sendButton && !sendButton.disabled) {{
                            console.log("Enviando mensaje con botón encontrado");
                            sendButton.click();

                            // PASO 6: Verificar que el mensaje se envió
                            setTimeout(() => {{
                                const currentText = messageBox.textContent || messageBox.innerText || '';
                                const wasCleared = currentText.trim() === '' || currentText !== textToSend;
                                console.log("Mensaje enviado:", wasCleared);
                                resolve(wasCleared);
                            }}, 500);
                        }} else {{
                            console.log("Botón de envío no encontrado o deshabilitado");
                            resolve(false);
                        }}
                    }}, 300);
                }});

            }} catch (error) {{
                console.log("Error en sendMessageOptimized:", error);
                return false;
            }}
        }}

        // Ejecutar la función y retornar el resultado
        return sendMessageOptimized();
        """

    @staticmethod
    def create_caption_writer_script(caption_text: str) -> str:
        """
        Crea script JavaScript para escribir captions con emoticones

        Args:
            caption_text: Texto del caption

        Returns:
            Script JavaScript para escribir caption
        """
        escaped_caption = UnicodeHandler.escape_unicode_for_js(caption_text)

        return f"""
        try {{
            const captionBox = document.evaluate(
                "//*[@id='app']/div/div[3]/div/div[2]/div[2]/span/div/div/div/div[2]/div/div[1]/div[3]/div/div/div[2]/div[1]/div[1]/p",
                document,
                null,
                XPathResult.FIRST_ORDERED_NODE_TYPE,
                null
            ).singleNodeValue ||
            document.evaluate(
                "//*[@id='app']/div/div[3]/div/div[2]/div[2]/span/div/div/div/div[2]/div/div[1]/div[3]/div/div/div[2]",
                document,
                null,
                XPathResult.FIRST_ORDERED_NODE_TYPE,
                null
            ).singleNodeValue ||
            document.querySelector('[contenteditable="true"][data-tab="10"]');

            if (captionBox) {{
                captionBox.focus();
                captionBox.innerHTML = '';

                const textToSend = "{escaped_caption}";
                const textNode = document.createTextNode(textToSend);
                captionBox.appendChild(textNode);

                const inputEvent = new InputEvent('input', {{
                    bubbles: true,
                    cancelable: true,
                    data: textToSend
                }});
                captionBox.dispatchEvent(inputEvent);
                return true;
            }}
            return false;
        }} catch (error) {{
            console.log("Error caption:", error);
            return false;
        }}
        """


def get_image_folder_path() -> str:
    """
    Obtiene la ruta de la carpeta de imágenes

    Returns:
        Ruta de la carpeta imagenes_mensajes
    """
    return "imagenes_mensajes"


def get_absolute_image_path(image_filename: str) -> Optional[str]:
    """
    Obtiene la ruta absoluta de una imagen

    Args:
        image_filename: Nombre del archivo de imagen

    Returns:
        Ruta absoluta o None si no existe
    """
    if not image_filename:
        return None

    image_path = os.path.join(get_image_folder_path(), image_filename)
    return os.path.abspath(image_path) if os.path.exists(image_path) else None