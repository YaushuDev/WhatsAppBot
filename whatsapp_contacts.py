# whatsapp_contacts.py
"""
Gestor de contactos y navegación para el Bot de WhatsApp
Este módulo se encarga exclusivamente de la búsqueda, navegación y gestión de contactos
en WhatsApp Web, incluyendo optimizaciones de cache, múltiples estrategias de búsqueda,
apertura de conversaciones y validación de números de teléfono.
"""

import time
import re
from typing import Optional, Callable, Dict, Set
from selenium.webdriver.common.keys import Keys
from whatsapp_utils import WhatsAppConstants
from whatsapp_driver import ChromeDriverManager


class ContactManager:
    """
    Gestor especializado para navegación y manejo de contactos en WhatsApp Web
    """

    def __init__(self, driver_manager: ChromeDriverManager, status_callback: Optional[Callable] = None):
        """
        Inicializa el gestor de contactos

        Args:
            driver_manager: Instancia del gestor de Chrome
            status_callback: Función callback para reportar estado
        """
        self.driver_manager = driver_manager
        self.status_callback = status_callback

        # Cache para optimización
        self._contact_cache: Dict[str, bool] = {}  # phone -> conversation_opened
        self._last_opened_contact: Optional[str] = None
        self._validated_numbers: Set[str] = set()

    def _update_status(self, message: str):
        """
        Actualiza el estado y notifica mediante callback

        Args:
            message: Mensaje de estado
        """
        print(f"[Contacts] {message}")
        if self.status_callback:
            self.status_callback(message)

    def _clean_phone_number(self, phone_number: str) -> str:
        """
        Limpia y normaliza un número de teléfono

        Args:
            phone_number: Número de teléfono sin limpiar

        Returns:
            Número limpio solo con dígitos
        """
        # Remover todos los caracteres no numéricos
        cleaned = re.sub(r'[^0-9]', '', phone_number)

        # Agregar código de país si no tiene (asumiendo que números sin código son locales)
        if len(cleaned) == 10 and not cleaned.startswith('1'):
            # Para números de 10 dígitos sin código, agregar código común
            pass  # Mantener como está, cada país puede tener su lógica

        return cleaned

    def _validate_phone_number(self, phone_number: str) -> bool:
        """
        Valida que el número de teléfono tenga formato correcto

        Args:
            phone_number: Número a validar

        Returns:
            True si el número es válido
        """
        cleaned = self._clean_phone_number(phone_number)

        # Usar cache para evitar re-validar
        if cleaned in self._validated_numbers:
            return True

        # Validaciones básicas
        if len(cleaned) < 7 or len(cleaned) > 15:
            return False

        # Solo dígitos
        if not cleaned.isdigit():
            return False

        # Agregar a cache si es válido
        self._validated_numbers.add(cleaned)
        return True

    def _is_conversation_already_open(self, phone_number: str) -> bool:
        """
        Verifica si la conversación con un contacto ya está abierta

        Args:
            phone_number: Número del contacto

        Returns:
            True si la conversación ya está abierta
        """
        try:
            cleaned_number = self._clean_phone_number(phone_number)

            # Si es el mismo contacto que antes, verificar rápidamente
            if self._last_opened_contact == cleaned_number:
                message_box = self.driver_manager.wait_for_element(
                    WhatsAppConstants.SELECTORS['message_box'],
                    timeout=2
                )
                return message_box is not None

            return False

        except Exception:
            return False

    def _search_contact_by_input(self, phone_number: str) -> bool:
        """
        Busca un contacto usando el campo de búsqueda

        Args:
            phone_number: Número del contacto

        Returns:
            True si se encontró y abrió el contacto
        """
        try:
            cleaned_number = self._clean_phone_number(phone_number)

            # Buscar campo de búsqueda
            search_box = self.driver_manager.wait_for_element(
                WhatsAppConstants.SELECTORS['search_box'],
                timeout=WhatsAppConstants.ELEMENT_WAIT_TIMEOUT,
                clickable=True
            )

            if not search_box:
                self._update_status("No se encontró el campo de búsqueda")
                return False

            # Click en el campo de búsqueda
            if not self.driver_manager.safe_click(search_box):
                return False

            # Limpiar campo y escribir número
            search_box.clear()
            time.sleep(WhatsAppConstants.SHORT_DELAY)

            search_box.send_keys(cleaned_number)
            time.sleep(1.5)  # Tiempo para que aparezcan resultados

            # Presionar Enter para seleccionar
            search_box.send_keys(Keys.ENTER)
            time.sleep(WhatsAppConstants.LONG_DELAY)

            # Verificar si se abrió la conversación
            return self._verify_conversation_opened()

        except Exception as e:
            self._update_status(f"Error en búsqueda por input: {str(e)}")
            return False

    def _search_contact_by_url(self, phone_number: str) -> bool:
        """
        Abre un contacto usando URL directa de WhatsApp

        Args:
            phone_number: Número del contacto

        Returns:
            True si se abrió correctamente
        """
        try:
            cleaned_number = self._clean_phone_number(phone_number)
            whatsapp_url = WhatsAppConstants.WHATSAPP_SEND_URL.format(cleaned_number)

            self._update_status(f"Abriendo {cleaned_number} con URL directa...")

            if not self.driver_manager.navigate_to(whatsapp_url):
                return False

            time.sleep(3)  # Tiempo para carga de la página

            # Verificar si se abrió la conversación
            return self._verify_conversation_opened()

        except Exception as e:
            self._update_status(f"Error en búsqueda por URL: {str(e)}")
            return False

    def _verify_conversation_opened(self) -> bool:
        """
        Verifica si una conversación se abrió correctamente

        Returns:
            True si hay una conversación abierta
        """
        try:
            # Buscar campo de mensaje para confirmar conversación abierta
            message_box = self.driver_manager.wait_for_element(
                WhatsAppConstants.SELECTORS['message_box'],
                timeout=8
            )

            if message_box:
                return True

            # Buscar indicadores alternativos de conversación abierta
            alternative_selectors = [
                "div[data-testid='conversation-header']",
                "header[data-testid='chatlist-header']",
                "div[aria-label*='Conversación']",
                "div[role='application'][tabindex='-1']"
            ]

            alternative_element = self.driver_manager.wait_for_element(
                alternative_selectors,
                timeout=5
            )

            return alternative_element is not None

        except Exception:
            return False

    def open_contact_conversation(self, phone_number: str) -> bool:
        """
        Abre la conversación con un contacto específico usando múltiples estrategias

        Args:
            phone_number: Número de teléfono del contacto

        Returns:
            True si se abrió la conversación correctamente
        """
        try:
            # Validar número de teléfono
            if not self._validate_phone_number(phone_number):
                self._update_status(f"Número de teléfono inválido: {phone_number}")
                return False

            cleaned_number = self._clean_phone_number(phone_number)

            # Verificar si el driver está activo
            if not self.driver_manager.is_session_alive():
                self._update_status("Sesión perdida, no se puede abrir contacto")
                return False

            # Verificar si la conversación ya está abierta
            if self._is_conversation_already_open(cleaned_number):
                self._update_status(f"Conversación con {cleaned_number} ya está abierta")
                return True

            self._update_status(f"📱 Abriendo conversación con {cleaned_number}...")

            # Estrategia 1: Búsqueda por campo de input
            if self._search_contact_by_input(cleaned_number):
                self._last_opened_contact = cleaned_number
                self._contact_cache[cleaned_number] = True
                self._update_status(f"✅ Conversación abierta con {cleaned_number} (búsqueda)")
                return True

            # Estrategia 2: URL directa como fallback
            self._update_status("Intentando con URL directa...")
            if self._search_contact_by_url(cleaned_number):
                self._last_opened_contact = cleaned_number
                self._contact_cache[cleaned_number] = True
                self._update_status(f"✅ Conversación abierta con {cleaned_number} (URL)")
                return True

            # Si ninguna estrategia funcionó
            self._update_status(f"❌ No se pudo abrir conversación con {cleaned_number}")
            self._contact_cache[cleaned_number] = False
            return False

        except Exception as e:
            self._update_status(f"❌ Error al abrir contacto {phone_number}: {str(e)}")
            return False

    def close_current_conversation(self) -> bool:
        """
        Cierra la conversación actual y regresa a la lista de chats

        Returns:
            True si se cerró correctamente
        """
        try:
            # Buscar botón de retroceso o X para cerrar conversación
            close_selectors = [
                "button[aria-label='Atrás']",
                "button[title='Atrás']",
                "span[data-icon='back']",
                "div[role='button'][aria-label='Atrás']"
            ]

            close_button = self.driver_manager.wait_for_element(
                close_selectors,
                timeout=5,
                clickable=True
            )

            if close_button and self.driver_manager.safe_click(close_button):
                self._last_opened_contact = None
                time.sleep(WhatsAppConstants.SHORT_DELAY)
                return True

            # Método alternativo: presionar Escape
            try:
                body = self.driver_manager.wait_for_element(["body"], timeout=2)
                if body:
                    body.send_keys(Keys.ESCAPE)
                    self._last_opened_contact = None
                    time.sleep(WhatsAppConstants.SHORT_DELAY)
                    return True
            except:
                pass

            return False

        except Exception as e:
            self._update_status(f"Error cerrando conversación: {str(e)}")
            return False

    def get_current_contact_info(self) -> Optional[Dict[str, str]]:
        """
        Obtiene información del contacto actual

        Returns:
            Diccionario con información del contacto o None
        """
        try:
            if not self.driver_manager.is_session_alive():
                return None

            # Buscar elementos del header de la conversación
            header_selectors = [
                "div[data-testid='conversation-header']",
                "header[data-testid='chatlist-header']",
                "div[role='button'][title]"
            ]

            header = self.driver_manager.wait_for_element(header_selectors, timeout=3)

            if header:
                # Intentar extraer nombre del contacto
                try:
                    contact_name = header.get_attribute('title') or header.text
                    return {
                        'name': contact_name,
                        'number': self._last_opened_contact or 'unknown'
                    }
                except:
                    pass

            return {
                'name': 'unknown',
                'number': self._last_opened_contact or 'unknown'
            }

        except Exception:
            return None

    def clear_cache(self):
        """
        Limpia el cache de contactos
        """
        self._contact_cache.clear()
        self._last_opened_contact = None
        self._validated_numbers.clear()
        self._update_status("Cache de contactos limpiado")

    def get_cache_stats(self) -> Dict[str, int]:
        """
        Obtiene estadísticas del cache

        Returns:
            Diccionario con estadísticas del cache
        """
        successful_contacts = sum(1 for success in self._contact_cache.values() if success)
        failed_contacts = len(self._contact_cache) - successful_contacts

        return {
            'total_cached': len(self._contact_cache),
            'successful_contacts': successful_contacts,
            'failed_contacts': failed_contacts,
            'validated_numbers': len(self._validated_numbers),
            'last_contact': self._last_opened_contact
        }

    def is_contact_cached(self, phone_number: str) -> Optional[bool]:
        """
        Verifica si un contacto está en cache

        Args:
            phone_number: Número del contacto

        Returns:
            True si exitoso, False si falló, None si no está en cache
        """
        cleaned_number = self._clean_phone_number(phone_number)
        return self._contact_cache.get(cleaned_number)