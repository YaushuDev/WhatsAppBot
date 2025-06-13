# whatsapp_automation.py
"""
Sistema de automatización para el Bot de WhatsApp
Este módulo controla el flujo completo de automatización del envío de mensajes,
incluyendo el sistema secuencial de mensajes, manejo de intervalos, control de
inicio/parada, estadísticas en tiempo real, tracking de números fallidos,
personalización automática de mensajes con placeholders como [nombre] para cada contacto
y gestión inteligente de instancias de navegador para evitar conflictos.
"""

import time
import random
import threading
from typing import List, Dict, Any, Optional, Callable
from whatsapp_utils import WhatsAppConstants, UnicodeHandler
from whatsapp_driver import ChromeDriverManager
from whatsapp_session import WhatsAppSession
from whatsapp_contacts import ContactManager
from whatsapp_messaging import MessageSender


class AutomationStats:
    """
    Gestor de estadísticas de automatización con tracking de números fallidos
    """

    def __init__(self):
        self.reset()

    def reset(self):
        """Reinicia todas las estadísticas"""
        self.messages_sent = 0
        self.messages_failed = 0
        self.contacts_processed = 0
        self.contacts_failed = 0
        self.personalized_messages = 0
        self.start_time = None
        self.end_time = None
        self.current_contact = None
        self.current_message_index = 0
        self.total_contacts = 0
        self.total_messages = 0

        # NUEVO: Tracking de números fallidos
        self.failed_contacts_list = []  # Lista de contactos que fallaron
        self.failed_numbers_set = set()  # Set para evitar duplicados

    def start_session(self, total_contacts: int, total_messages: int):
        """Inicia una nueva sesión de estadísticas"""
        self.reset()
        self.start_time = time.time()
        self.total_contacts = total_contacts
        self.total_messages = total_messages

    def end_session(self):
        """Finaliza la sesión actual"""
        self.end_time = time.time()

    def record_message_sent(self, was_personalized: bool = False):
        """
        Registra un mensaje enviado exitosamente

        Args:
            was_personalized: Si el mensaje fue personalizado
        """
        self.messages_sent += 1
        if was_personalized:
            self.personalized_messages += 1

    def record_message_failed(self):
        """Registra un mensaje que falló"""
        self.messages_failed += 1

    def record_contact_processed(self, contact_info: Any):
        """
        Registra un contacto procesado

        Args:
            contact_info: Información del contacto (dict o string)
        """
        self.contacts_processed += 1

        # Extraer datos del contacto para tracking
        if isinstance(contact_info, dict):
            phone_number = contact_info.get('numero', '')
            contact_name = contact_info.get('nombre', '')
            self.current_contact = f"{contact_name} ({phone_number})" if contact_name else phone_number
        else:
            phone_number = str(contact_info)
            self.current_contact = phone_number

    def record_contact_failed(self, contact_info: Any):
        """
        NUEVO: Registra un contacto que falló

        Args:
            contact_info: Información del contacto que falló
        """
        self.contacts_failed += 1

        # Extraer información del contacto fallido
        if isinstance(contact_info, dict):
            phone_number = contact_info.get('numero', '')
            contact_name = contact_info.get('nombre', 'Sin nombre')

            # Solo agregar si no está ya en la lista
            if phone_number and phone_number not in self.failed_numbers_set:
                self.failed_contacts_list.append({
                    'numero': phone_number,
                    'nombre': contact_name,
                    'display': f"{contact_name} ({phone_number})" if contact_name != 'Sin nombre' else phone_number
                })
                self.failed_numbers_set.add(phone_number)
        else:
            phone_number = str(contact_info)

            # Solo agregar si no está ya en la lista
            if phone_number and phone_number not in self.failed_numbers_set:
                self.failed_contacts_list.append({
                    'numero': phone_number,
                    'nombre': 'Sin nombre',
                    'display': phone_number
                })
                self.failed_numbers_set.add(phone_number)

    def update_message_index(self, index: int):
        """Actualiza el índice de mensaje actual"""
        self.current_message_index = index

    def get_failed_contacts_summary(self) -> List[str]:
        """
        NUEVO: Obtiene un resumen formateado de los contactos fallidos

        Returns:
            Lista de strings con los contactos fallidos formateados
        """
        if not self.failed_contacts_list:
            return []

        summary = []
        for i, contact in enumerate(self.failed_contacts_list, 1):
            summary.append(f"   • {contact['display']}")

        return summary

    def get_summary(self) -> Dict[str, Any]:
        """Obtiene resumen de estadísticas"""
        duration = 0
        if self.start_time:
            end_time = self.end_time or time.time()
            duration = end_time - self.start_time

        return {
            'messages_sent': self.messages_sent,
            'messages_failed': self.messages_failed,
            'contacts_processed': self.contacts_processed,
            'contacts_failed': self.contacts_failed,
            'personalized_messages': self.personalized_messages,
            'total_contacts': self.total_contacts,
            'total_messages': self.total_messages,
            'duration_seconds': duration,
            'success_rate': (self.messages_sent / max(1, self.messages_sent + self.messages_failed)) * 100,
            'personalization_rate': (self.personalized_messages / max(1, self.messages_sent)) * 100,
            'current_contact': self.current_contact,
            'current_message_index': self.current_message_index,
            'failed_contacts_list': self.failed_contacts_list.copy(),  # NUEVO
            'failed_contacts_summary': self.get_failed_contacts_summary()  # NUEVO
        }


class SequentialMessageManager:
    """
    Gestor del sistema secuencial de mensajes
    """

    def __init__(self, messages: List[Dict[str, Any]]):
        self.messages = messages.copy()
        self.current_index = 0
        self.total_messages = len(messages)

    def get_next_message(self) -> Dict[str, Any]:
        """
        Obtiene el siguiente mensaje en orden secuencial/cíclico

        Returns:
            Mensaje seleccionado según el índice secuencial
        """
        if not self.messages:
            return {}

        # Seleccionar mensaje usando índice secuencial con módulo para hacer ciclo
        selected_message = self.messages[self.current_index % self.total_messages]

        # Incrementar índice para el siguiente mensaje
        self.current_index += 1

        return selected_message

    def reset_index(self):
        """Reinicia el índice secuencial"""
        self.current_index = 0

    def get_current_position(self) -> tuple:
        """
        Obtiene la posición actual en el ciclo

        Returns:
            Tupla (índice_actual, total_mensajes)
        """
        if not self.messages:
            return (0, 0)
        return (self.current_index % self.total_messages, self.total_messages)


class ContactDataExtractor:
    """
    Clase para extraer y formatear datos de contactos para personalización
    """

    @staticmethod
    def extract_contact_data(contact_info: Any) -> Dict[str, str]:
        """
        Extrae datos del contacto en formato estándar para personalización

        Args:
            contact_info: Información del contacto (puede ser dict, string o número)

        Returns:
            Diccionario con datos del contacto {'nombre': str, 'numero': str}
        """
        try:
            # Si es un diccionario (contacto completo)
            if isinstance(contact_info, dict):
                return {
                    'nombre': contact_info.get('nombre', 'Usuario'),
                    'numero': contact_info.get('numero', '')
                }

            # Si es solo un número (string)
            elif isinstance(contact_info, str):
                return {
                    'nombre': 'Usuario',  # Nombre genérico para números sin nombre
                    'numero': contact_info
                }

            # Fallback
            else:
                return {
                    'nombre': 'Usuario',
                    'numero': str(contact_info) if contact_info else ''
                }

        except Exception:
            return {
                'nombre': 'Usuario',
                'numero': ''
            }


class BrowserInstanceManager:
    """
    NUEVO: Gestor de instancias de navegador para reutilización y resolución de conflictos
    """

    def __init__(self):
        self._shared_driver_manager = None
        self._browser_should_stay_open = False
        self._instance_lock = threading.Lock()

    def get_or_create_driver_manager(self, status_callback: Optional[Callable] = None) -> ChromeDriverManager:
        """
        Obtiene una instancia existente o crea una nueva del driver manager

        Args:
            status_callback: Callback para reportar estado

        Returns:
            Instancia del ChromeDriverManager
        """
        with self._instance_lock:
            # Si hay una instancia compartida activa, reutilizarla
            if self._shared_driver_manager and self._shared_driver_manager.is_session_alive():
                if status_callback:
                    status_callback("🔄 Reutilizando navegador existente...")
                return self._shared_driver_manager

            # Si la instancia anterior no está activa, crear nueva
            if status_callback:
                status_callback("🚀 Creando nueva instancia de navegador...")

            self._shared_driver_manager = ChromeDriverManager(status_callback)
            return self._shared_driver_manager

    def should_keep_browser_open(self, keep_open: bool):
        """
        Establece si el navegador debe mantenerse abierto

        Args:
            keep_open: Si debe mantener el navegador abierto
        """
        self._browser_should_stay_open = keep_open

    def cleanup_driver_manager(self, driver_manager: ChromeDriverManager, force_close: bool = False):
        """
        Limpia el driver manager según la configuración

        Args:
            driver_manager: Instancia a limpiar
            force_close: Si debe forzar el cierre
        """
        with self._instance_lock:
            if force_close or not self._browser_should_stay_open:
                if driver_manager:
                    driver_manager.close(cleanup_user_data=not self._browser_should_stay_open)

                # Si es la instancia compartida y se está cerrando, limpiar referencia
                if driver_manager == self._shared_driver_manager and not self._browser_should_stay_open:
                    self._shared_driver_manager = None

    def force_cleanup_all(self):
        """
        Fuerza la limpieza de todas las instancias
        """
        with self._instance_lock:
            if self._shared_driver_manager:
                self._shared_driver_manager.force_cleanup()
                self._shared_driver_manager = None


# Instancia global del gestor de navegador
_browser_instance_manager = BrowserInstanceManager()


class AutomationController:
    """
    Controlador principal de automatización con gestión inteligente de instancias de navegador
    """

    def __init__(self, status_callback: Optional[Callable] = None):
        """
        Inicializa el controlador de automatización

        Args:
            status_callback: Función callback para reportar estado
        """
        self.status_callback = status_callback
        self.is_running = False
        self._stop_requested = False

        # Componentes principales (MEJORADO: usar gestor de instancias)
        self.driver_manager = None
        self.session_manager = None
        self.contact_manager = None
        self.message_sender = None

        # Gestores especializados
        self.stats = AutomationStats()
        self.message_manager = None
        self.contact_extractor = ContactDataExtractor()

        # Configuración de automatización
        self.min_interval = 30
        self.max_interval = 60

    def _update_status(self, message: str):
        """
        Actualiza el estado y notifica mediante callback

        Args:
            message: Mensaje de estado
        """
        print(f"[Automation] {message}")
        if self.status_callback:
            self.status_callback(message)

    def _initialize_components(self) -> bool:
        """
        MEJORADO: Inicializa todos los componentes necesarios con gestión de instancias

        Returns:
            True si se inicializaron correctamente
        """
        try:
            # MEJORADO: Usar gestor de instancias de navegador
            self.driver_manager = _browser_instance_manager.get_or_create_driver_manager(self.status_callback)

            # Solo inicializar el driver si no está ya inicializado
            if not self.driver_manager.is_session_alive():
                if not self.driver_manager.initialize_driver():
                    return False
            else:
                self._update_status("✅ Navegador ya inicializado, reutilizando...")

            # Session manager
            self.session_manager = WhatsAppSession(self.driver_manager, self.status_callback)

            # Verificar si WhatsApp Web ya está abierto
            current_url = self.driver_manager.get_current_url()
            if current_url and "web.whatsapp.com" in current_url:
                self._update_status("🌐 WhatsApp Web ya está abierto, validando sesión...")
                if not self.session_manager.validate_session():
                    if not self.session_manager.open_whatsapp_web():
                        return False
            else:
                if not self.session_manager.open_whatsapp_web():
                    return False

            # Contact manager
            self.contact_manager = ContactManager(self.driver_manager, self.status_callback)

            # Message sender
            self.message_sender = MessageSender(self.driver_manager, self.status_callback)

            return True

        except Exception as e:
            self._update_status(f"❌ Error inicializando componentes: {str(e)}")
            return False

    def _cleanup_components(self, keep_browser_open: bool = False):
        """
        MEJORADO: Limpia y cierra todos los componentes con gestión inteligente de instancias

        Args:
            keep_browser_open: Si True, mantiene el navegador abierto
        """
        try:
            # Configurar el gestor sobre si mantener el navegador abierto
            _browser_instance_manager.should_keep_browser_open(keep_browser_open)

            if self.contact_manager:
                self.contact_manager.clear_cache()

            if self.message_sender:
                self.message_sender.clear_cache()

            # MEJORADO: Usar gestor de instancias para la limpieza
            if self.driver_manager:
                if keep_browser_open:
                    self._update_status("🌐 Manteniendo navegador abierto como se configuró")
                else:
                    self._update_status("🔒 Cerrando navegador...")

                _browser_instance_manager.cleanup_driver_manager(self.driver_manager)

            # Limpiar referencias (excepto driver si se mantiene abierto)
            if not keep_browser_open:
                self.driver_manager = None
            self.session_manager = None
            self.contact_manager = None
            self.message_sender = None

        except Exception as e:
            self._update_status(f"⚠️ Error en limpieza: {str(e)}")

    def _validate_automation_data(self, contacts_data: List[Any], messages: List[Dict[str, Any]]) -> bool:
        """
        Valida los datos de automatización

        Args:
            contacts_data: Lista de contactos (puede ser números o contactos completos)
            messages: Lista de mensajes

        Returns:
            True si los datos son válidos
        """
        if not contacts_data:
            self._update_status("❌ No hay contactos configurados")
            return False

        if not messages:
            self._update_status("❌ No hay mensajes configurados")
            return False

        if self.min_interval <= 0 or self.max_interval <= 0:
            self._update_status("❌ Intervalos inválidos")
            return False

        if self.min_interval > self.max_interval:
            self._update_status("❌ Intervalo mínimo mayor al máximo")
            return False

        return True

    def _create_message_display_info(self, message_data: Dict[str, Any], cycle_position: int,
                                     total_messages: int, contact_data: Dict[str, str]) -> str:
        """
        Crea información de visualización para un mensaje con indicadores de personalización

        Args:
            message_data: Datos del mensaje
            cycle_position: Posición en el ciclo
            total_messages: Total de mensajes
            contact_data: Datos del contacto

        Returns:
            String con información formateada del mensaje
        """
        text = message_data.get('texto', '')
        has_image = message_data.get('imagen') is not None
        envio_conjunto = message_data.get('envio_conjunto', False)

        # Verificar si el mensaje será personalizado
        will_be_personalized = False
        if self.message_sender and text:
            personalizer = self.message_sender.get_personalizer()
            will_be_personalized = personalizer.has_placeholders(text)

        # Texto truncado
        display_text = text[:50] + "..." if len(text) > 50 else text
        display_text = f"'{display_text}'" if display_text else "'[sin texto]'"

        # Indicadores visuales
        indicators = ""

        # Indicador de personalización
        if will_be_personalized:
            indicators += " 👤"

        # Emoticones
        if UnicodeHandler.has_emoji_or_unicode(text):
            indicators += " 😀"

        # Tipo de envío
        if has_image and text:
            if envio_conjunto:
                indicators += " 🖼️📝"  # Imagen con caption
            else:
                indicators += " 📷+📝"  # Imagen y texto separados
        elif has_image:
            indicators += " 📷"  # Solo imagen

        return f"[Mensaje {cycle_position}/{total_messages}] {display_text}{indicators}"

    def _send_to_single_contact(self, contact_info: Any, message_data: Dict[str, Any]) -> bool:
        """
        Envía un mensaje a un contacto específico con personalización automática

        Args:
            contact_info: Información del contacto (número o contacto completo)
            message_data: Datos del mensaje

        Returns:
            True si se envió correctamente
        """
        try:
            # Extraer datos del contacto para personalización
            contact_data = self.contact_extractor.extract_contact_data(contact_info)

            # Obtener número de teléfono para operaciones
            phone_number = contact_data.get('numero', '')
            if isinstance(contact_info, str):
                phone_number = contact_info
            elif isinstance(contact_info, dict):
                phone_number = contact_info.get('numero', contact_info.get('number', ''))

            # Verificar sesión activa
            if not self.session_manager.validate_session():
                self._update_status("❌ Sesión perdida, intentando reconectar...")
                if not self.session_manager.reconnect_if_needed():
                    return False

            # Abrir conversación
            if not self.contact_manager.open_contact_conversation(phone_number):
                self._update_status(f"❌ No se pudo abrir conversación con {phone_number}")
                return False

            # Enviar mensaje con datos de contacto para personalización
            if self.message_sender.send_message(message_data, contact_data):
                # Verificar si se personalizó el mensaje
                was_personalized = False
                if self.message_sender and message_data.get('texto'):
                    personalizer = self.message_sender.get_personalizer()
                    was_personalized = personalizer.has_placeholders(message_data.get('texto', ''))

                if was_personalized:
                    self._update_status(f"✅ Mensaje personalizado enviado a {contact_data.get('nombre', phone_number)}")
                else:
                    self._update_status(f"✅ Mensaje enviado correctamente a {phone_number}")

                return True
            else:
                self._update_status(f"❌ Error al enviar mensaje a {phone_number}")
                return False

        except Exception as e:
            self._update_status(f"❌ Error procesando contacto: {str(e)}")
            return False

    def _wait_between_messages(self, current_index: int, total_contacts: int):
        """
        Espera el intervalo configurado entre mensajes

        Args:
            current_index: Índice actual
            total_contacts: Total de contactos
        """
        if current_index < total_contacts - 1 and self.is_running:
            wait_time = random.randint(self.min_interval, self.max_interval)
            self._update_status(f"⏱ Esperando {wait_time} segundos antes del siguiente mensaje...")

            for _ in range(wait_time):
                if not self.is_running:
                    break
                time.sleep(1)

    def _show_failed_contacts_summary(self):
        """
        NUEVO: Muestra un resumen de los contactos que fallaron al final de la automatización
        """
        failed_summary = self.stats.get_failed_contacts_summary()

        if failed_summary:
            self._update_status(f"❌ Números que fallaron ({len(failed_summary)}):")
            for failed_contact in failed_summary:
                self._update_status(failed_contact)
        else:
            self._update_status("✅ No hubo números fallidos")

    def start_automation(self, contacts_data: List[Any], messages: List[Dict[str, Any]],
                         min_interval: int, max_interval: int, keep_browser_open: bool = False):
        """
        MEJORADO: Inicia la automatización completa con gestión inteligente de navegador

        Args:
            contacts_data: Lista de contactos (números o contactos completos)
            messages: Lista de mensajes
            min_interval: Intervalo mínimo entre mensajes
            max_interval: Intervalo máximo entre mensajes
            keep_browser_open: Si mantener el navegador abierto al finalizar
        """
        if self.is_running:
            self._update_status("⚠️ La automatización ya está en ejecución")
            return

        try:
            # Configurar parámetros
            self.min_interval = min_interval
            self.max_interval = max_interval
            self.is_running = True
            self._stop_requested = False

            # Validar datos
            if not self._validate_automation_data(contacts_data, messages):
                self.is_running = False
                return

            # Inicializar estadísticas
            self.stats.start_session(len(contacts_data), len(messages))

            # Crear gestor de mensajes secuencial
            self.message_manager = SequentialMessageManager(messages)

            # Detectar si hay mensajes con personalización
            personalizable_messages = 0
            if self.message_sender:
                personalizer = self.message_sender.get_personalizer()
                for msg in messages:
                    if personalizer.has_placeholders(msg.get('texto', '')):
                        personalizable_messages += 1

            self._update_status("🚀 Iniciando automatización con envío secuencial...")
            self._update_status(f"📊 {len(contacts_data)} contactos, {len(messages)} mensajes")

            # Mostrar información sobre personalización
            if personalizable_messages > 0:
                self._update_status(f"👤 {personalizable_messages} mensajes serán personalizados automáticamente")

            self._update_status(f"🔄 Patrón: Mensaje 1→2→3...→{len(messages)}→1→2... (cíclico)")

            # MEJORADO: Inicializar componentes con gestión de instancias
            if not self._initialize_components():
                self.is_running = False
                return

            # Procesar cada contacto
            for i, contact_info in enumerate(contacts_data):
                if not self.is_running or self._stop_requested:
                    self._update_status("⏹ Automatización detenida por el usuario")
                    break

                try:
                    # Obtener siguiente mensaje en secuencia
                    current_message = self.message_manager.get_next_message()
                    cycle_position, total_msgs = self.message_manager.get_current_position()

                    # Extraer datos del contacto
                    contact_data = self.contact_extractor.extract_contact_data(contact_info)

                    # Actualizar estadísticas
                    self.stats.record_contact_processed(contact_info)
                    self.stats.update_message_index(cycle_position)

                    # Crear información de display
                    message_info = self._create_message_display_info(
                        current_message, cycle_position, total_msgs, contact_data
                    )

                    contact_display = contact_data.get('nombre', contact_data.get('numero', str(contact_info)))
                    self._update_status(f"📱 ({i + 1}/{len(contacts_data)}) {message_info} → {contact_display}")

                    # Enviar mensaje con personalización
                    success = self._send_to_single_contact(contact_info, current_message)

                    if success:
                        # Verificar si se personalizó
                        was_personalized = False
                        if current_message.get('texto') and self.message_sender:
                            personalizer = self.message_sender.get_personalizer()
                            was_personalized = personalizer.has_placeholders(current_message.get('texto', ''))

                        self.stats.record_message_sent(was_personalized)
                    else:
                        self.stats.record_message_failed()
                        self.stats.record_contact_failed(contact_info)  # NUEVO: Registrar contacto fallido

                    # Esperar entre mensajes
                    self._wait_between_messages(i, len(contacts_data))

                except Exception as e:
                    self.stats.record_message_failed()
                    self.stats.record_contact_failed(contact_info)  # NUEVO: Registrar contacto fallido
                    self._update_status(f"❌ Error con contacto: {str(e)}")
                    continue

            # Finalizar automatización
            self.stats.end_session()
            summary = self.stats.get_summary()

            if self.is_running:
                self._update_status(
                    f"✅ Automatización completada: {summary['messages_sent']} enviados, "
                    f"{summary['messages_failed']} fallidos ({summary['success_rate']:.1f}% éxito)"
                )
                # Mostrar estadísticas de personalización
                if summary['personalized_messages'] > 0:
                    self._update_status(
                        f"👤 {summary['personalized_messages']} mensajes personalizados "
                        f"({summary['personalization_rate']:.1f}% del total)"
                    )

                # NUEVO: Mostrar resumen de números fallidos
                self._show_failed_contacts_summary()

            else:
                self._update_status(
                    f"⏹ Automatización detenida: {summary['messages_sent']} enviados, "
                    f"{summary['messages_failed']} fallidos"
                )
                # Mostrar números fallidos incluso si se detuvo
                self._show_failed_contacts_summary()

        except Exception as e:
            self._update_status(f"❌ Error crítico en automatización: {str(e)}")
        finally:
            self.is_running = False
            self._stop_requested = False
            self._cleanup_components(keep_browser_open)  # MEJORADO: Gestión inteligente de navegador

    def stop_automation(self):
        """
        Detiene la automatización en curso
        """
        if self.is_running:
            self._update_status("🛑 Solicitando detención de automatización...")
            self.is_running = False
            self._stop_requested = True
        else:
            self._update_status("ℹ️ No hay automatización en ejecución")

    def is_active(self) -> bool:
        """
        Verifica si la automatización está activa

        Returns:
            True si está ejecutándose
        """
        return self.is_running

    def get_current_stats(self) -> Dict[str, Any]:
        """
        Obtiene las estadísticas actuales

        Returns:
            Diccionario con estadísticas actuales
        """
        return self.stats.get_summary()

    def get_session_info(self) -> Dict[str, Any]:
        """
        Obtiene información completa de la sesión

        Returns:
            Diccionario con información de la sesión
        """
        stats = self.stats.get_summary()

        return {
            'is_running': self.is_running,
            'stop_requested': self._stop_requested,
            'driver_active': self.driver_manager.is_session_alive() if self.driver_manager else False,
            'session_valid': self.session_manager.is_session_valid() if self.session_manager else False,
            'stats': stats,
            'intervals': {
                'min': self.min_interval,
                'max': self.max_interval
            }
        }

    def force_cleanup_all(self):
        """
        NUEVO: Fuerza la limpieza de todas las instancias (para casos de emergencia)
        """
        try:
            self.is_running = False
            self._stop_requested = True
            _browser_instance_manager.force_cleanup_all()
            self._update_status("🧹 Limpieza forzada completada")
        except Exception as e:
            self._update_status(f"⚠️ Error en limpieza forzada: {str(e)}")