# whatsapp_bot.py
"""
Bot de WhatsApp - Interfaz Principal y Orquestador
Este archivo actúa como la interfaz principal del Bot de WhatsApp, proporcionando una API
limpia y simple para la GUI mientras coordina todos los módulos especializados. Mantiene
compatibilidad completa con la interfaz existente, actúa como punto de entrada único
para todas las operaciones del bot e incluye soporte automático para personalización
de mensajes con placeholders como [nombre] que se reemplazan dinámicamente, configuración
del navegador y gestión inteligente de instancias para evitar conflictos.
"""

import threading
from typing import List, Dict, Any, Optional, Callable, Union
from whatsapp_automation import AutomationController
from whatsapp_driver import ChromeDriverManager
from whatsapp_session import WhatsAppSession
from whatsapp_contacts import ContactManager
from whatsapp_messaging import MessageSender


class WhatsAppBot:
    """
    Clase principal del Bot de WhatsApp que actúa como interfaz pública
    Coordina todos los módulos especializados y proporciona una API simple para la GUI
    con soporte automático para personalización de mensajes, configuración del navegador
    y gestión inteligente de instancias de navegador para evitar conflictos
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

        # NUEVO: Control de estado para evitar conflictos
        self._is_standalone_mode = False

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
        MEJORADO: Inicializa componentes para uso individual con gestión de conflictos

        Returns:
            True si se inicializaron correctamente
        """
        try:
            # Verificar si hay automatización activa
            if self.automation_controller.is_active():
                self._update_status("⚠️ No se puede usar modo standalone mientras hay automatización activa")
                return False

            # Marcar modo standalone
            self._is_standalone_mode = True

            if not self._standalone_driver:
                self._standalone_driver = ChromeDriverManager(self.status_callback)
                if not self._standalone_driver.initialize_driver():
                    self._is_standalone_mode = False
                    return False

            if not self._standalone_session:
                self._standalone_session = WhatsAppSession(self._standalone_driver, self.status_callback)

                # Verificar si WhatsApp Web ya está abierto
                current_url = self._standalone_driver.get_current_url()
                if current_url and "web.whatsapp.com" in current_url:
                    self._update_status("🌐 WhatsApp Web ya está abierto, validando sesión...")
                    if not self._standalone_session.validate_session():
                        if not self._standalone_session.open_whatsapp_web():
                            self._is_standalone_mode = False
                            return False
                else:
                    if not self._standalone_session.open_whatsapp_web():
                        self._is_standalone_mode = False
                        return False

            if not self._standalone_contacts:
                self._standalone_contacts = ContactManager(self._standalone_driver, self.status_callback)

            if not self._standalone_messaging:
                self._standalone_messaging = MessageSender(self._standalone_driver, self.status_callback)

            return True

        except Exception as e:
            self._update_status(f"Error inicializando componentes: {str(e)}")
            self._is_standalone_mode = False
            return False

    def _cleanup_standalone_components(self):
        """
        MEJORADO: Limpia los componentes standalone con gestión inteligente

        """
        try:
            self._is_standalone_mode = False

            if self._standalone_contacts:
                self._standalone_contacts.clear_cache()

            if self._standalone_messaging:
                self._standalone_messaging.clear_cache()

            if self._standalone_driver:
                # Solo cerrar si no hay automatización que pueda estar usando el navegador
                if not self.automation_controller.is_active():
                    self._standalone_driver.close()
                else:
                    self._update_status("🌐 Manteniendo navegador para automatización activa")

            # Limpiar referencias solo si no hay automatización activa
            if not self.automation_controller.is_active():
                self._standalone_driver = None
                self._standalone_session = None
                self._standalone_contacts = None
                self._standalone_messaging = None

        except Exception as e:
            self._update_status(f"Error en limpieza: {str(e)}")

    def _prepare_contacts_data(self, contacts_input: Union[List[str], List[Dict[str, str]]]) -> List[Any]:
        """
        Prepara los datos de contactos para automatización con soporte de personalización

        Args:
            contacts_input: Lista de números (strings) o lista de contactos completos (dicts)

        Returns:
            Lista de contactos preparada para automatización
        """
        try:
            prepared_contacts = []

            for contact in contacts_input:
                # Si es un string (solo número)
                if isinstance(contact, str):
                    prepared_contacts.append(contact)

                # Si es un diccionario (contacto completo con nombre)
                elif isinstance(contact, dict):
                    # Asegurar que tenga las claves necesarias
                    if 'numero' in contact or 'number' in contact:
                        prepared_contacts.append(contact)
                    else:
                        # Fallback: tratarlo como número si no tiene estructura correcta
                        contact_str = str(contact)
                        if contact_str:
                            prepared_contacts.append(contact_str)

                # Otros tipos: convertir a string
                else:
                    contact_str = str(contact)
                    if contact_str:
                        prepared_contacts.append(contact_str)

            return prepared_contacts

        except Exception as e:
            self._update_status(f"Error preparando contactos: {str(e)}")
            return contacts_input  # Devolver original en caso de error

    def start_automation(self, phone_numbers: List[str], messages: List[Dict[str, Any]],
                         min_interval: int, max_interval: int):
        """
        Inicia la automatización del envío de mensajes con personalización automática (método original)

        Args:
            phone_numbers: Lista de números de teléfono o contactos completos
            messages: Lista de mensajes con formato {'texto': str, 'imagen': str, 'envio_conjunto': bool}
            min_interval: Intervalo mínimo entre mensajes (segundos)
            max_interval: Intervalo máximo entre mensajes (segundos)
        """
        self._start_automation_internal(phone_numbers, messages, min_interval, max_interval, False)

    def start_automation_with_browser_config(self, phone_numbers: List[str], messages: List[Dict[str, Any]],
                                             min_interval: int, max_interval: int, keep_browser_open: bool = False):
        """
        NUEVO: Inicia la automatización con configuración del navegador

        Args:
            phone_numbers: Lista de números de teléfono o contactos completos
            messages: Lista de mensajes con formato {'texto': str, 'imagen': str, 'envio_conjunto': bool}
            min_interval: Intervalo mínimo entre mensajes (segundos)
            max_interval: Intervalo máximo entre mensajes (segundos)
            keep_browser_open: Si mantener el navegador abierto al finalizar
        """
        self._start_automation_internal(phone_numbers, messages, min_interval, max_interval, keep_browser_open)

    def _start_automation_internal(self, phone_numbers: List[str], messages: List[Dict[str, Any]],
                                   min_interval: int, max_interval: int, keep_browser_open: bool = False):
        """
        MEJORADO: Método interno para iniciar automatización con gestión de conflictos

        Args:
            phone_numbers: Lista de números de teléfono o contactos completos
            messages: Lista de mensajes
            min_interval: Intervalo mínimo entre mensajes
            max_interval: Intervalo máximo entre mensajes
            keep_browser_open: Si mantener el navegador abierto al finalizar
        """
        if self.is_active():
            self._update_status("⚠️ La automatización ya está en ejecución")
            return

        # NUEVO: Limpiar componentes standalone si están activos
        if self._is_standalone_mode:
            self._update_status("🔄 Cerrando modo standalone para automatización...")
            self._cleanup_standalone_components()

        try:
            # Preparar datos de contactos para soporte de personalización
            prepared_contacts = self._prepare_contacts_data(phone_numbers)

            # Detectar si hay mensajes con personalización
            personalization_detected = False
            if messages:
                for message in messages:
                    text = message.get('texto', '')
                    if '[nombre]' in text.lower() or '[numero]' in text.lower():
                        personalization_detected = True
                        break

            if personalization_detected:
                self._update_status("👤 Personalización detectada en mensajes - se aplicará automáticamente")

            # NUEVO: Mostrar configuración del navegador
            if keep_browser_open:
                self._update_status("🌐 El navegador se mantendrá abierto al finalizar")

            # Iniciar automatización en hilo separado
            self._automation_thread = threading.Thread(
                target=self.automation_controller.start_automation,
                args=(prepared_contacts, messages, min_interval, max_interval, keep_browser_open),
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

    def send_message_to_contact(self, phone_number: str, message_data: Dict[str, Any],
                                contact_data: Optional[Dict[str, str]] = None) -> bool:
        """
        MEJORADO: Envía un mensaje a un contacto específico con gestión de conflictos

        Args:
            phone_number: Número de teléfono
            message_data: Datos del mensaje
            contact_data: Datos del contacto para personalización (opcional)

        Returns:
            True si se envió correctamente
        """
        try:
            # Verificar conflictos con automatización
            if self.automation_controller.is_active():
                self._update_status("⚠️ No se puede enviar mensaje individual durante automatización")
                return False

            # Inicializar componentes standalone si no están listos
            if not self._initialize_standalone_components():
                return False

            # Si no se proporcionan datos de contacto, crear datos básicos
            if not contact_data:
                contact_data = {
                    'nombre': 'Usuario',  # Nombre genérico
                    'numero': phone_number
                }

            # Detectar si el mensaje será personalizado
            will_be_personalized = False
            if self._standalone_messaging and message_data.get('texto'):
                personalizer = self._standalone_messaging.get_personalizer()
                will_be_personalized = personalizer.has_placeholders(message_data.get('texto', ''))

            if will_be_personalized:
                self._update_status(f"👤 Personalizando mensaje para {contact_data.get('nombre', phone_number)}")

            # Verificar sesión
            if not self._standalone_session.validate_session():
                self._update_status("Sesión perdida, intentando reconectar...")
                if not self._standalone_session.reconnect_if_needed():
                    return False

            # Abrir conversación
            if not self._standalone_contacts.open_contact_conversation(phone_number):
                self._update_status(f"No se pudo abrir conversación con {phone_number}")
                return False

            # Enviar mensaje con datos de contacto para personalización
            if self._standalone_messaging.send_message(message_data, contact_data):
                if will_be_personalized:
                    self._update_status(
                        f"Mensaje personalizado enviado correctamente a {contact_data.get('nombre', phone_number)}")
                else:
                    self._update_status(f"Mensaje enviado correctamente a {phone_number}")
                return True
            else:
                self._update_status(f"Error al enviar mensaje a {phone_number}")
                return False

        except Exception as e:
            self._update_status(f"Error enviando mensaje: {str(e)}")
            return False

    def send_message_to_contact_with_name(self, contact_info: Dict[str, str], message_data: Dict[str, Any]) -> bool:
        """
        Envía un mensaje a un contacto usando información completa (nombre + número)

        Args:
            contact_info: Diccionario con 'nombre' y 'numero' del contacto
            message_data: Datos del mensaje

        Returns:
            True si se envió correctamente
        """
        try:
            phone_number = contact_info.get('numero', contact_info.get('number', ''))
            if not phone_number:
                self._update_status("❌ Número de teléfono no válido en contacto")
                return False

            # Usar el método existente con datos de contacto
            return self.send_message_to_contact(phone_number, message_data, contact_info)

        except Exception as e:
            self._update_status(f"Error enviando mensaje a contacto: {str(e)}")
            return False

    def get_session_info(self) -> Dict[str, Any]:
        """
        MEJORADO: Obtiene información de la sesión actual con gestión de estados

        Returns:
            Diccionario con información de la sesión
        """
        # Si hay automatización activa, usar sus estadísticas
        if self.automation_controller.is_active():
            session_info = self.automation_controller.get_session_info()

            # Agregar información de personalización si está disponible
            stats = session_info.get('stats', {})
            if 'personalized_messages' in stats:
                session_info['personalization_active'] = stats['personalized_messages'] > 0
                session_info['personalization_rate'] = stats.get('personalization_rate', 0)

            return session_info

        # Si no hay automatización, usar componentes standalone
        info = {
            'is_running': False,
            'driver_active': False,
            'session_valid': False,
            'contacts_count': 0,
            'messages_count': 0,
            'current_message_index': 0,
            'personalization_active': False,
            'personalization_rate': 0,
            'standalone_mode': self._is_standalone_mode
        }

        if self._standalone_driver:
            info['driver_active'] = self._standalone_driver.is_session_alive()

        if self._standalone_session:
            info['session_valid'] = self._standalone_session.is_session_valid()

        return info

    def get_current_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas actuales de automatización con datos de personalización

        Returns:
            Diccionario con estadísticas
        """
        stats = self.automation_controller.get_current_stats()

        # Asegurar que las estadísticas de personalización estén incluidas
        if 'personalized_messages' not in stats:
            stats['personalized_messages'] = 0
        if 'personalization_rate' not in stats:
            stats['personalization_rate'] = 0

        return stats

    def test_message_personalization(self, message_text: str, contact_data: Dict[str, str]) -> str:
        """
        Método de prueba para verificar cómo se personalizará un mensaje

        Args:
            message_text: Texto del mensaje con placeholders
            contact_data: Datos del contacto

        Returns:
            Texto personalizado (para pruebas)
        """
        try:
            # Crear instancia temporal del personalizador
            from whatsapp_messaging import MessagePersonalizer
            personalizer = MessagePersonalizer()

            return personalizer.personalize_message(message_text, contact_data)

        except Exception as e:
            self._update_status(f"Error en prueba de personalización: {str(e)}")
            return message_text

    def get_available_placeholders(self) -> List[str]:
        """
        Obtiene lista de placeholders disponibles para personalización

        Returns:
            Lista de placeholders soportados
        """
        try:
            # Si hay componente de messaging activo, usar su personalizador
            if self._standalone_messaging:
                return self._standalone_messaging.get_personalizer().get_available_placeholders()

            # Si no, crear instancia temporal
            from whatsapp_messaging import MessagePersonalizer
            personalizer = MessagePersonalizer()
            return personalizer.get_available_placeholders()

        except Exception as e:
            self._update_status(f"Error obteniendo placeholders: {str(e)}")
            return ['[nombre]', '[numero]']  # Fallback

    def force_cleanup_all(self):
        """
        NUEVO: Fuerza la limpieza de todas las instancias (para casos de emergencia)
        """
        try:
            self._update_status("🧹 Iniciando limpieza forzada de todas las instancias...")

            # Detener automatización si está activa
            if self.is_active():
                self.stop_automation()

            # Forzar limpieza del controlador de automatización
            self.automation_controller.force_cleanup_all()

            # Limpiar componentes standalone
            self._cleanup_standalone_components()

            self._update_status("✅ Limpieza forzada completada")

        except Exception as e:
            self._update_status(f"⚠️ Error en limpieza forzada: {str(e)}")

    def close(self):
        """
        MEJORADO: Cierra el bot y limpia todos los recursos con gestión inteligente

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

            # NUEVO: Limpieza adicional de instancias compartidas si es necesario
            if not self.automation_controller.is_active():
                self.automation_controller.force_cleanup_all()

            self._update_status("✅ Bot cerrado correctamente")

        except Exception as e:
            self._update_status(f"⚠️ Error al cerrar bot: {str(e)}")

    def refresh_session(self) -> bool:
        """
        MEJORADO: Refresca la sesión actual con gestión de conflictos

        Returns:
            True si el refresco fue exitoso
        """
        try:
            # No permitir refresh durante automatización
            if self.automation_controller.is_active():
                self._update_status("⚠️ No se puede refrescar sesión durante automatización")
                return False

            if self._standalone_session:
                return self._standalone_session.refresh_session()
            return False
        except Exception as e:
            self._update_status(f"Error refrescando sesión: {str(e)}")
            return False

    def validate_session(self) -> bool:
        """
        MEJORADO: Valida que la sesión actual sigue activa con gestión de estados

        Returns:
            True si la sesión es válida
        """
        try:
            # Si hay automatización activa, usar su sesión
            if self.automation_controller.is_active():
                session_info = self.automation_controller.get_session_info()
                return session_info.get('session_valid', False)

            # Si no, usar standalone
            if self._standalone_session:
                return self._standalone_session.validate_session()
            return False
        except Exception as e:
            self._update_status(f"Error validando sesión: {str(e)}")
            return False

    def get_contact_cache_stats(self) -> Dict[str, int]:
        """
        MEJORADO: Obtiene estadísticas del cache de contactos según el estado actual

        Returns:
            Diccionario con estadísticas del cache
        """
        # Intentar obtener estadísticas de automatización si está activa
        if self.automation_controller.is_active() and hasattr(self.automation_controller, 'contact_manager'):
            if self.automation_controller.contact_manager:
                return self.automation_controller.contact_manager.get_cache_stats()

        # Usar standalone si está disponible
        if self._standalone_contacts:
            return self._standalone_contacts.get_cache_stats()

        return {
            'total_cached': 0,
            'successful_contacts': 0,
            'failed_contacts': 0,
            'validated_numbers': 0,
            'last_contact': None
        }

    def check_message_personalization(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analiza una lista de mensajes para detectar personalización

        Args:
            messages: Lista de mensajes a analizar

        Returns:
            Diccionario con información sobre personalización
        """
        try:
            from whatsapp_messaging import MessagePersonalizer
            personalizer = MessagePersonalizer()

            total_messages = len(messages)
            personalizable_messages = 0
            placeholders_found = set()

            for message in messages:
                text = message.get('texto', '')
                if personalizer.has_placeholders(text):
                    personalizable_messages += 1
                    # Encontrar placeholders específicos
                    import re
                    found = re.findall(r'\[(\w+)\]', text, re.IGNORECASE)
                    placeholders_found.update(found)

            return {
                'total_messages': total_messages,
                'personalizable_messages': personalizable_messages,
                'personalization_rate': (personalizable_messages / max(1, total_messages)) * 100,
                'placeholders_found': list(placeholders_found),
                'has_personalization': personalizable_messages > 0
            }

        except Exception as e:
            self._update_status(f"Error analizando personalización: {str(e)}")
            return {
                'total_messages': len(messages),
                'personalizable_messages': 0,
                'personalization_rate': 0,
                'placeholders_found': [],
                'has_personalization': False
            }

    def get_browser_status(self) -> Dict[str, Any]:
        """
        NUEVO: Obtiene información detallada del estado del navegador

        Returns:
            Información del estado del navegador
        """
        status = {
            'automation_active': self.automation_controller.is_active(),
            'standalone_active': self._is_standalone_mode,
            'browser_instances': 0,
            'user_data_info': None
        }

        # Información de automatización
        if self.automation_controller.is_active() and hasattr(self.automation_controller, 'driver_manager'):
            if self.automation_controller.driver_manager:
                status['browser_instances'] += 1
                status['user_data_info'] = self.automation_controller.driver_manager.get_user_data_info()

        # Información standalone
        if self._standalone_driver:
            status['browser_instances'] += 1
            if not status['user_data_info']:
                status['user_data_info'] = self._standalone_driver.get_user_data_info()

        return status