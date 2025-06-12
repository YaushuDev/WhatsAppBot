# whatsapp_automation.py
"""
Sistema de automatización para el Bot de WhatsApp
Este módulo controla el flujo completo de automatización del envío de mensajes,
incluyendo el sistema secuencial de mensajes, manejo de intervalos, control de
inicio/parada, estadísticas en tiempo real y coordinación entre todos los componentes.
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
    Gestor de estadísticas de automatización
    """

    def __init__(self):
        self.reset()

    def reset(self):
        """Reinicia todas las estadísticas"""
        self.messages_sent = 0
        self.messages_failed = 0
        self.contacts_processed = 0
        self.contacts_failed = 0
        self.start_time = None
        self.end_time = None
        self.current_contact = None
        self.current_message_index = 0
        self.total_contacts = 0
        self.total_messages = 0

    def start_session(self, total_contacts: int, total_messages: int):
        """Inicia una nueva sesión de estadísticas"""
        self.reset()
        self.start_time = time.time()
        self.total_contacts = total_contacts
        self.total_messages = total_messages

    def end_session(self):
        """Finaliza la sesión actual"""
        self.end_time = time.time()

    def record_message_sent(self):
        """Registra un mensaje enviado exitosamente"""
        self.messages_sent += 1

    def record_message_failed(self):
        """Registra un mensaje que falló"""
        self.messages_failed += 1

    def record_contact_processed(self, phone_number: str):
        """Registra un contacto procesado"""
        self.contacts_processed += 1
        self.current_contact = phone_number

    def record_contact_failed(self):
        """Registra un contacto que falló"""
        self.contacts_failed += 1

    def update_message_index(self, index: int):
        """Actualiza el índice de mensaje actual"""
        self.current_message_index = index

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
            'total_contacts': self.total_contacts,
            'total_messages': self.total_messages,
            'duration_seconds': duration,
            'success_rate': (self.messages_sent / max(1, self.messages_sent + self.messages_failed)) * 100,
            'current_contact': self.current_contact,
            'current_message_index': self.current_message_index
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


class AutomationController:
    """
    Controlador principal de automatización
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

        # Componentes principales
        self.driver_manager = None
        self.session_manager = None
        self.contact_manager = None
        self.message_sender = None

        # Gestores especializados
        self.stats = AutomationStats()
        self.message_manager = None

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
        Inicializa todos los componentes necesarios

        Returns:
            True si se inicializaron correctamente
        """
        try:
            # Driver manager
            self.driver_manager = ChromeDriverManager(self.status_callback)
            if not self.driver_manager.initialize_driver():
                return False

            # Session manager
            self.session_manager = WhatsAppSession(self.driver_manager, self.status_callback)
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

    def _cleanup_components(self):
        """
        Limpia y cierra todos los componentes
        """
        try:
            if self.contact_manager:
                self.contact_manager.clear_cache()

            if self.message_sender:
                self.message_sender.clear_cache()

            if self.driver_manager:
                self.driver_manager.close()

            # Limpiar referencias
            self.driver_manager = None
            self.session_manager = None
            self.contact_manager = None
            self.message_sender = None

        except Exception as e:
            self._update_status(f"⚠️ Error en limpieza: {str(e)}")

    def _validate_automation_data(self, phone_numbers: List[str], messages: List[Dict[str, Any]]) -> bool:
        """
        Valida los datos de automatización

        Args:
            phone_numbers: Lista de números
            messages: Lista de mensajes

        Returns:
            True si los datos son válidos
        """
        if not phone_numbers:
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
                                     total_messages: int) -> str:
        """
        Crea información de visualización para un mensaje

        Args:
            message_data: Datos del mensaje
            cycle_position: Posición en el ciclo
            total_messages: Total de mensajes

        Returns:
            String con información formateada del mensaje
        """
        text = message_data.get('texto', '')
        has_image = message_data.get('imagen') is not None
        envio_conjunto = message_data.get('envio_conjunto', False)

        # Texto truncado
        display_text = text[:50] + "..." if len(text) > 50 else text
        display_text = f"'{display_text}'" if display_text else "'[sin texto]'"

        # Indicadores visuales
        indicators = ""

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

    def _send_to_single_contact(self, phone_number: str, message_data: Dict[str, Any]) -> bool:
        """
        Envía un mensaje a un contacto específico

        Args:
            phone_number: Número del contacto
            message_data: Datos del mensaje

        Returns:
            True si se envió correctamente
        """
        try:
            # Verificar sesión activa
            if not self.session_manager.validate_session():
                self._update_status("❌ Sesión perdida, intentando reconectar...")
                if not self.session_manager.reconnect_if_needed():
                    return False

            # Abrir conversación
            if not self.contact_manager.open_contact_conversation(phone_number):
                self._update_status(f"❌ No se pudo abrir conversación con {phone_number}")
                return False

            # Enviar mensaje
            if self.message_sender.send_message(message_data):
                self._update_status(f"✅ Mensaje enviado correctamente a {phone_number}")
                return True
            else:
                self._update_status(f"❌ Error al enviar mensaje a {phone_number}")
                return False

        except Exception as e:
            self._update_status(f"❌ Error procesando contacto {phone_number}: {str(e)}")
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

    def start_automation(self, phone_numbers: List[str], messages: List[Dict[str, Any]],
                         min_interval: int, max_interval: int):
        """
        Inicia la automatización completa

        Args:
            phone_numbers: Lista de números de teléfono
            messages: Lista de mensajes
            min_interval: Intervalo mínimo entre mensajes
            max_interval: Intervalo máximo entre mensajes
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
            if not self._validate_automation_data(phone_numbers, messages):
                self.is_running = False
                return

            # Inicializar estadísticas
            self.stats.start_session(len(phone_numbers), len(messages))

            # Crear gestor de mensajes secuencial
            self.message_manager = SequentialMessageManager(messages)

            self._update_status("🚀 Iniciando automatización con envío secuencial...")
            self._update_status(f"📊 {len(phone_numbers)} contactos, {len(messages)} mensajes")
            self._update_status(f"🔄 Patrón: Mensaje 1→2→3...→{len(messages)}→1→2... (cíclico)")

            # Inicializar componentes
            if not self._initialize_components():
                self.is_running = False
                return

            # Procesar cada contacto
            for i, phone_number in enumerate(phone_numbers):
                if not self.is_running or self._stop_requested:
                    self._update_status("⏹ Automatización detenida por el usuario")
                    break

                try:
                    # Obtener siguiente mensaje en secuencia
                    current_message = self.message_manager.get_next_message()
                    cycle_position, total_msgs = self.message_manager.get_current_position()

                    # Actualizar estadísticas
                    self.stats.record_contact_processed(phone_number)
                    self.stats.update_message_index(cycle_position)

                    # Crear información de display
                    message_info = self._create_message_display_info(current_message, cycle_position, total_msgs)

                    self._update_status(f"📱 ({i + 1}/{len(phone_numbers)}) {message_info} → {phone_number}")

                    # Enviar mensaje
                    if self._send_to_single_contact(phone_number, current_message):
                        self.stats.record_message_sent()
                    else:
                        self.stats.record_message_failed()
                        self.stats.record_contact_failed()

                    # Esperar entre mensajes
                    self._wait_between_messages(i, len(phone_numbers))

                except Exception as e:
                    self.stats.record_message_failed()
                    self.stats.record_contact_failed()
                    self._update_status(f"❌ Error con contacto {phone_number}: {str(e)}")
                    continue

            # Finalizar automatización
            self.stats.end_session()
            summary = self.stats.get_summary()

            if self.is_running:
                self._update_status(
                    f"✅ Automatización completada: {summary['messages_sent']} enviados, "
                    f"{summary['messages_failed']} fallidos ({summary['success_rate']:.1f}% éxito)"
                )
            else:
                self._update_status(
                    f"⏹ Automatización detenida: {summary['messages_sent']} enviados, "
                    f"{summary['messages_failed']} fallidos"
                )

        except Exception as e:
            self._update_status(f"❌ Error crítico en automatización: {str(e)}")
        finally:
            self.is_running = False
            self._stop_requested = False
            self._cleanup_components()

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