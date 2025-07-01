# whatsapp_utils.py
"""
Utilidades y funciones compartidas para el Bot de WhatsApp con selectores configurables
Este módulo centraliza todas las funciones de utilidad comunes utilizadas por los diferentes
componentes del bot, incluyendo detección de Unicode, validaciones de archivos, manejo de
JavaScript y configuraciones dinámicas de selectores CSS/XPath que pueden ser actualizados
desde la interfaz gráfica para adaptarse a los cambios de WhatsApp Web.
"""

import re
import os
import json
from typing import Dict, Any, Optional, List


class SelectorsConfig:
    """
    Gestor de configuración dinámica de selectores CSS/XPath
    Permite cargar selectores personalizados desde configuración
    """

    def __init__(self, config_file: str = "selectores_config.json"):
        """
        Inicializa el gestor de selectores configurables

        Args:
            config_file: Archivo donde se guardan los selectores personalizados
        """
        self.config_file = config_file
        self._custom_selectors = {}
        self._load_custom_selectors()

    def _load_custom_selectors(self):
        """
        Carga los selectores personalizados desde el archivo de configuración
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as file:
                    self._custom_selectors = json.load(file)
                print(f"[SelectorsConfig] Selectores personalizados cargados: {len(self._custom_selectors)} elementos")
            else:
                print(f"[SelectorsConfig] No existe configuración personalizada, usando selectores por defecto")
        except Exception as e:
            print(f"[SelectorsConfig] Error cargando selectores personalizados: {e}")
            self._custom_selectors = {}

    def save_custom_selectors(self, selectors: Dict[str, List[str]]) -> bool:
        """
        Guarda selectores personalizados en el archivo de configuración

        Args:
            selectors: Diccionario con selectores a guardar

        Returns:
            True si se guardó correctamente
        """
        try:
            # Validar que los selectores tengan el formato correcto
            for key, selector_list in selectors.items():
                if not isinstance(selector_list, list) or not all(isinstance(s, str) for s in selector_list):
                    raise ValueError(f"Selector '{key}' debe ser una lista de strings")

            self._custom_selectors.update(selectors)

            with open(self.config_file, 'w', encoding='utf-8') as file:
                json.dump(self._custom_selectors, file, indent=2, ensure_ascii=False)

            print(f"[SelectorsConfig] Selectores guardados correctamente")
            return True

        except Exception as e:
            print(f"[SelectorsConfig] Error guardando selectores: {e}")
            return False

    def get_selectors(self, selector_key: str, default_selectors: List[str]) -> List[str]:
        """
        Obtiene selectores para una clave específica (personalizados o por defecto)

        Args:
            selector_key: Clave del selector (ej: 'message_box')
            default_selectors: Selectores por defecto si no hay personalizados

        Returns:
            Lista de selectores a usar
        """
        if selector_key in self._custom_selectors:
            custom = self._custom_selectors[selector_key]
            if custom and len(custom) > 0:
                return custom

        return default_selectors

    def reset_selector(self, selector_key: str) -> bool:
        """
        Resetea un selector específico a los valores por defecto

        Args:
            selector_key: Clave del selector a resetear

        Returns:
            True si se reseteo correctamente
        """
        try:
            if selector_key in self._custom_selectors:
                del self._custom_selectors[selector_key]

                with open(self.config_file, 'w', encoding='utf-8') as file:
                    json.dump(self._custom_selectors, file, indent=2, ensure_ascii=False)

                print(f"[SelectorsConfig] Selector '{selector_key}' reseteado a valores por defecto")
                return True
            return True

        except Exception as e:
            print(f"[SelectorsConfig] Error reseteando selector: {e}")
            return False

    def get_all_custom_selectors(self) -> Dict[str, List[str]]:
        """
        Obtiene todos los selectores personalizados actuales

        Returns:
            Diccionario con todos los selectores personalizados
        """
        return self._custom_selectors.copy()


class WhatsAppConstants:
    """
    Constantes y configuraciones compartidas del bot de WhatsApp con selectores configurables
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

    # Selectores por defecto (pueden ser sobrescritos por configuración)
    DEFAULT_SELECTORS = {
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

    # Instancia del gestor de selectores configurables
    _selectors_config = None

    @classmethod
    def get_selectors_config(cls) -> SelectorsConfig:
        """
        Obtiene la instancia del gestor de selectores (singleton)

        Returns:
            Instancia del SelectorsConfig
        """
        if cls._selectors_config is None:
            cls._selectors_config = SelectorsConfig()
        return cls._selectors_config

    @classmethod
    def get_selectors(cls, selector_key: str) -> List[str]:
        """
        Obtiene selectores dinámicos para una clave específica

        Args:
            selector_key: Clave del selector (ej: 'message_box', 'attach_button')

        Returns:
            Lista de selectores a usar (personalizados o por defecto)
        """
        if selector_key not in cls.DEFAULT_SELECTORS:
            raise ValueError(f"Selector '{selector_key}' no existe en la configuración por defecto")

        config = cls.get_selectors_config()
        default_selectors = cls.DEFAULT_SELECTORS[selector_key]

        return config.get_selectors(selector_key, default_selectors)

    @classmethod
    def update_selectors(cls, selectors: Dict[str, List[str]]) -> bool:
        """
        Actualiza selectores personalizados

        Args:
            selectors: Diccionario con selectores a actualizar

        Returns:
            True si se actualizó correctamente
        """
        config = cls.get_selectors_config()
        return config.save_custom_selectors(selectors)

    @classmethod
    def reset_selectors(cls, selector_keys: List[str] = None) -> bool:
        """
        Resetea selectores a valores por defecto

        Args:
            selector_keys: Lista de claves a resetear (None para resetear todos)

        Returns:
            True si se reseteó correctamente
        """
        config = cls.get_selectors_config()

        if selector_keys is None:
            # Resetear todos los selectores
            try:
                if os.path.exists(config.config_file):
                    os.remove(config.config_file)
                config._custom_selectors = {}
                print("[WhatsAppConstants] Todos los selectores reseteados a valores por defecto")
                return True
            except Exception as e:
                print(f"[WhatsAppConstants] Error reseteando todos los selectores: {e}")
                return False
        else:
            # Resetear selectores específicos
            success = True
            for key in selector_keys:
                if not config.reset_selector(key):
                    success = False
            return success

    @classmethod
    def get_available_selector_keys(cls) -> List[str]:
        """
        Obtiene todas las claves de selectores disponibles

        Returns:
            Lista de claves de selectores
        """
        return list(cls.DEFAULT_SELECTORS.keys())

    # Propiedad para mantener compatibilidad con código existente
    @property
    def SELECTORS(self):
        """
        Propiedad de compatibilidad que devuelve selectores dinámicos
        DEPRECATED: Usar get_selectors() en su lugar
        """
        return {
            key: self.get_selectors(key)
            for key in self.DEFAULT_SELECTORS.keys()
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
    Generador de scripts JavaScript para el bot con selectores dinámicos
    """

    @staticmethod
    def create_message_sender_script(message_text: str) -> str:
        """
        Crea script JavaScript mejorado para enviar mensajes con selectores dinámicos

        Args:
            message_text: Texto del mensaje a enviar

        Returns:
            Script JavaScript listo para ejecutar
        """
        escaped_text = UnicodeHandler.escape_unicode_for_js(message_text)

        # Obtener selectores dinámicos para message_box
        message_selectors = WhatsAppConstants.get_selectors('message_box')

        # Convertir selectores a JavaScript
        js_selectors = ', '.join([f"'{sel}'" for sel in message_selectors])

        return f"""
        function sendMessageOptimized() {{
            try {{
                // PASO 1: Buscar el campo de mensaje con selectores configurables
                const selectors = [{js_selectors}];
                let messageBox = null;

                for (const selector of selectors) {{
                    messageBox = document.querySelector(selector);
                    if (messageBox) break;
                }}

                if (!messageBox) {{
                    console.log("MessageBox no encontrado con selectores configurados");
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
                        // Buscar botón de envío con selectores dinámicos
                        const sendSelectors = {JavaScriptInjector._get_send_button_selectors_js()};
                        let sendButton = null;

                        for (const selector of sendSelectors) {{
                            sendButton = document.querySelector(selector);
                            if (sendButton && !sendButton.disabled) break;
                        }}

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
    def _get_send_button_selectors_js() -> str:
        """
        Obtiene selectores del botón send en formato JavaScript
        """
        send_selectors = WhatsAppConstants.get_selectors('send_button')
        return '[' + ', '.join([f"'{sel}'" for sel in send_selectors]) + ']'

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