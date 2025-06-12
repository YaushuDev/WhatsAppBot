# whatsapp_bot.py
"""
Bot de WhatsApp - Interfaz Principal y Orquestador
Este archivo actúa como la interfaz principal del Bot de WhatsApp, proporcionando una API
limpia y simple para la GUI mientras coordina todos los módulos especializados. Mantiene
compatibilidad completa con la interfaz existente y actúa como punto de entrada único
para todas las operaciones del bot.
"""

import threading
from typing import List, Dict, Any, Optional, Callable
from whatsapp_automation import AutomationController
from whatsapp_driver import ChromeDriverManager
from whatsapp_session import WhatsAppSession
from whatsapp_contacts import ContactManager
from whatsapp_messaging import MessageSender


class WhatsAppBot:
    """
    Clase principal del Bot de WhatsApp que actúa como interfaz pública
    Coordina todos los módulos especializados y proporciona una API simple para la GUI
    """

    def __init__(self, status_callback: Optional[Callable] = None):
        """
        Inicializa el bot de WhatsApp

        Args:
            status_callback: Función callback para actualizar el estado en la GUI
        """
        self.status_callback = status_callback

        # Controlador principal de automatización
        self.automation_controller = AutomationController(status_callback)

        # Componentes para uso individual (cuando no se usa automatización completa)
        self._standalone_driver = None
        self._standalone_session = None
        self._standalone_contacts = None
        self._standalone_messaging = None

        # Threading para automatización
        self._automation_thread = None

    def _update_status(self, message: str):
        """
        Actualiza el estado y notifica a la GUI

        Args:
            message: Mensaje de estado
        """
        print(f"[Bot] {message}")
        if self.status_callback:
            self.status_callback(message)

    def _initialize_standalone_components(self) -> bool:
        """
        Inicializa componentes para uso individual (no automatización)

        Returns:
            True si se inicializaron correctamente
        """
        try:
            if not self._standalone_driver:
                self._standalone_driver = ChromeDriverManager(self.status_callback)
                if not self._standalone_driver.initialize_driver():
                    return False

            if not self._standalone_session:
                self._standalone_session = WhatsAppSession(self._standalone_driver, self.status_callback)
                if not self._standalone_session.open_whatsapp_web():
                    return False

            if not self._standalone_contacts:
                self._standalone_contacts = ContactManager(self._standalone_driver, self.status_callback)

            if not self._standalone_messaging:
                self._standalone_messaging = MessageSender(self._standalone_driver, self.status_callback)

            return True

        except Exception as e:
            self._update_status(f"Error inicializando componentes: {str(e)}")
            return False

    def _cleanup_standalone_components(self):
        """
        Limpia los componentes standalone
        """
        try:
            if self._standalone_contacts:
                self._standalone_contacts.clear_cache()

            if self._standalone_messaging:
                self._standalone_messaging.clear_cache()

            if self._standalone_driver:
                self._standalone_driver.close()

            # Limpiar referencias
            self._standalone_driver = None
            self._standalone_session = None
            self._standalone_contacts = None
            self._standalone_messaging = None

        except Exception as e:
            self._update_status(f"Error en limpieza: {str(e)}")

    def start_automation(self, phone_numbers: List[str], messages: List[Dict[str, Any]],
                         min_interval: int, max_interval: int):
        """
        Inicia la automatización del envío de mensajes

        Args:
            phone_numbers: Lista de números de teléfono
            messages: Lista de mensajes con formato {'texto': str, 'imagen': str, 'envio_conjunto': bool}
            min_interval: Intervalo mínimo entre mensajes (segundos)
            max_interval: Intervalo máximo entre mensajes (segundos)
        """
        if self.is_active():
            self._update_status("⚠️ La automatización ya está en ejecución")
            return

        try:
            # Iniciar automatización en hilo separado
            self._automation_thread = threading.Thread(
                target=self.automation_controller.start_automation,
                args=(phone_numbers, messages, min_interval, max_interval),
                daemon=True
            )
            self._automation_thread.start()

        except Exception as e:
            self._update_status(f"Error al iniciar automatización: {str(e)}")

    def stop_automation(self):
        """
        Detiene la automatización en curso
        """
        self.automation_controller.stop_automation()

    def is_active(self) -> bool:
        """
        Verifica si el bot está activo

        Returns:
            True si está ejecutándose
        """
        return self.automation_controller.is_active()

    def send_message_to_contact(self, phone_number: str, message_data: Dict[str, Any]) -> bool:
        """
        Envía un mensaje a un contacto específico (uso individual, no automatización)

        Args:
            phone_number: Número de teléfono
            message_data: Datos del mensaje

        Returns:
            True si se envió correctamente
        """
        try:
            # Inicializar componentes standalone si no están listos
            if not self._initialize_standalone_components():
                return False

            # Verificar sesión
            if not self._standalone_session.validate_session():
                self._update_status("Sesión perdida, intentando reconectar...")
                if not self._standalone_session.reconnect_if_needed():
                    return False

            # Abrir conversación
            if not self._standalone_contacts.open_contact_conversation(phone_number):
                self._update_status(f"No se pudo abrir conversación con {phone_number}")
                return False

            # Enviar mensaje
            if self._standalone_messaging.send_message(message_data):
                self._update_status(f"Mensaje enviado correctamente a {phone_number}")
                return True
            else:
                self._update_status(f"Error al enviar mensaje a {phone_number}")
                return False

        except Exception as e:
            self._update_status(f"Error enviando mensaje: {str(e)}")
            return False

    def get_session_info(self) -> Dict[str, Any]:
        """
        Obtiene información de la sesión actual

        Returns:
            Diccionario con información de la sesión
        """
        # Si hay automatización activa, usar sus estadísticas
        if self.automation_controller.is_active():
            return self.automation_controller.get_session_info()

        # Si no hay automatización, usar componentes standalone
        info = {
            'is_running': False,
            'driver_active': False,
            'session_valid': False,
            'contacts_count': 0,
            'messages_count': 0,
            'current_message_index': 0
        }

        if self._standalone_driver:
            info['driver_active'] = self._standalone_driver.is_session_alive()

        if self._standalone_session:
            info['session_valid'] = self._standalone_session.is_session_valid()

        return info

    def get_current_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas actuales de automatización

        Returns:
            Diccionario con estadísticas
        """
        return self.automation_controller.get_current_stats()

    def close(self):
        """
        Cierra el bot y limpia todos los recursos
        """
        try:
            # Detener automatización si está activa
            if self.is_active():
                self.stop_automation()

                # Esperar a que termine el hilo de automatización
                if self._automation_thread and self._automation_thread.is_alive():
                    self._automation_thread.join(timeout=5)

            # Limpiar componentes standalone
            self._cleanup_standalone_components()

            self._update_status("Bot cerrado correctamente")

        except Exception as e:
            self._update_status(f"Error al cerrar bot: {str(e)}")

    def refresh_session(self) -> bool:
        """
        Refresca la sesión actual (para uso standalone)

        Returns:
            True si el refresco fue exitoso
        """
        try:
            if self._standalone_session:
                return self._standalone_session.refresh_session()
            return False
        except Exception as e:
            self._update_status(f"Error refrescando sesión: {str(e)}")
            return False

    def validate_session(self) -> bool:
        """
        Valida que la sesión actual sigue activa (para uso standalone)

        Returns:
            True si la sesión es válida
        """
        try:
            if self._standalone_session:
                return self._standalone_session.validate_session()
            return False
        except Exception as e:
            self._update_status(f"Error validando sesión: {str(e)}")
            return False

    def get_contact_cache_stats(self) -> Dict[str, int]:
        """
        Obtiene estadísticas del cache de contactos

        Returns:
            Diccionario con estadísticas del cache
        """
        if self._standalone_contacts:
            return self._standalone_contacts.get_cache_stats()
        return {
            'total_cached': 0,
            'successful_contacts': 0,
            'failed_contacts': 0,
            'validated_numbers': 0,
            'last_contact': None
        }