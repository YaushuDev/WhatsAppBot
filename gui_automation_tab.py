# gui_automation_tab.py
"""
Pestaña de automatización para el Bot de WhatsApp
Este módulo implementa la funcionalidad de control y configuración de la automatización
del bot, incluyendo configuración de intervalos, estadísticas en tiempo real y controles
de inicio/detención con registro de actividad detallado.
"""

import tkinter as tk
import threading
from gui_styles import StyleManager
from gui_components import (TabHeader, StatsDisplay, ActivityLog,
                            show_error_message, show_success_message)


class AutomationConfigSection:
    """
    Sección de configuración de la automatización
    Maneja los parámetros de intervalos entre mensajes
    """

    def __init__(self, parent, style_manager: StyleManager):
        """
        Inicializa la sección de configuración

        Args:
            parent: Widget padre donde se mostrará la sección
            style_manager: Gestor de estilos para mantener consistencia visual
        """
        self.style_manager = style_manager

        # Crear frame principal de configuración
        self._create_config_frame(parent)
        self._create_interval_controls()

    def _create_config_frame(self, parent):
        """
        Crea el frame principal de configuración

        Args:
            parent: Widget padre
        """
        self.config_frame = self.style_manager.create_styled_labelframe(
            parent,
            "⚙️ Configuración de Automatización"
        )
        self.config_frame.pack(fill=tk.X, padx=25, pady=(0, 20))

        # Contenido interno
        self.content_frame = self.style_manager.create_styled_frame(self.config_frame)
        self.content_frame.pack(fill=tk.X, padx=15, pady=15)

    def _create_interval_controls(self):
        """
        Crea los controles de configuración de intervalos
        """
        # Descripción
        description_label = self.style_manager.create_styled_label(
            self.content_frame,
            "Configura el tiempo de espera entre envío de mensajes para evitar bloqueos:",
            "secondary"
        )
        description_label.pack(anchor="w", pady=(0, 15))

        # Label principal
        interval_label = self.style_manager.create_styled_label(
            self.content_frame,
            "Intervalo entre mensajes (segundos):",
            "normal"
        )
        interval_label.pack(anchor="w", pady=(0, 10))

        # Frame para los inputs
        self._create_interval_inputs()

    def _create_interval_inputs(self):
        """
        Crea los campos de entrada para intervalos mínimo y máximo
        """
        inputs_frame = self.style_manager.create_styled_frame(self.content_frame)
        inputs_frame.pack(fill=tk.X)

        # Input mínimo
        self._create_min_interval_input(inputs_frame)

        # Input máximo
        self._create_max_interval_input(inputs_frame)

    def _create_min_interval_input(self, parent):
        """
        Crea el input para el intervalo mínimo

        Args:
            parent: Widget padre
        """
        min_container = self.style_manager.create_styled_frame(parent)
        min_container.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 20))

        min_label = self.style_manager.create_styled_label(min_container, "Mínimo:", "normal")
        min_label.pack(anchor="w")

        self.min_interval = self.style_manager.create_styled_entry(min_container)
        self.min_interval.pack(fill=tk.X, pady=(5, 0))
        self.min_interval.insert(0, "30")

    def _create_max_interval_input(self, parent):
        """
        Crea el input para el intervalo máximo

        Args:
            parent: Widget padre
        """
        max_container = self.style_manager.create_styled_frame(parent)
        max_container.pack(side=tk.LEFT, fill=tk.X, expand=True)

        max_label = self.style_manager.create_styled_label(max_container, "Máximo:", "normal")
        max_label.pack(anchor="w")

        self.max_interval = self.style_manager.create_styled_entry(max_container)
        self.max_interval.pack(fill=tk.X, pady=(5, 0))
        self.max_interval.insert(0, "60")

    def get_intervals(self):
        """
        Obtiene los intervalos configurados

        Returns:
            tuple: (min_interval, max_interval) o (None, None) si hay error
        """
        try:
            min_val = int(self.min_interval.get())
            max_val = int(self.max_interval.get())
            return min_val, max_val
        except ValueError:
            return None, None

    def validate_intervals(self):
        """
        Valida que los intervalos sean correctos

        Returns:
            tuple: (is_valid, error_message)
        """
        min_val, max_val = self.get_intervals()

        if min_val is None or max_val is None:
            return False, "Los intervalos deben ser números válidos"

        if min_val <= 0 or max_val <= 0:
            return False, "Los intervalos deben ser números positivos"

        if min_val > max_val:
            return False, "El intervalo mínimo debe ser menor al máximo"

        if min_val < 10:
            return False, "El intervalo mínimo recomendado es 10 segundos para evitar bloqueos"

        return True, ""


class AutomationControlSection:
    """
    Sección de controles de automatización
    Maneja los botones de inicio y detención del bot
    """

    def __init__(self, parent, style_manager: StyleManager, start_callback=None, stop_callback=None):
        """
        Inicializa la sección de controles

        Args:
            parent: Widget padre donde se mostrará la sección
            style_manager: Gestor de estilos para mantener consistencia visual
            start_callback: Función a ejecutar al iniciar automatización
            stop_callback: Función a ejecutar al detener automatización
        """
        self.style_manager = style_manager
        self.start_callback = start_callback
        self.stop_callback = stop_callback
        self.automation_active = False

        # Crear controles
        self._create_control_frame(parent)
        self._create_control_buttons()

    def _create_control_frame(self, parent):
        """
        Crea el frame principal de controles

        Args:
            parent: Widget padre
        """
        self.control_frame = self.style_manager.create_styled_frame(parent)
        self.control_frame.pack(fill=tk.X, padx=25, pady=20)

    def _create_control_buttons(self):
        """
        Crea los botones de control de automatización
        """
        # Botón iniciar
        self.start_btn = self.style_manager.create_styled_button(
            self.control_frame,
            "▶️ Iniciar Automatización",
            self._on_start_clicked,
            "success"
        )
        self.start_btn.configure(
            font=self.style_manager.fonts["button_large"],
            pady=15
        )
        self.start_btn.pack(fill=tk.X, pady=(0, 15))

        # Botón detener
        self.stop_btn = self.style_manager.create_styled_button(
            self.control_frame,
            "⏹️ Detener Automatización",
            self._on_stop_clicked,
            "error"
        )
        self.stop_btn.configure(
            font=self.style_manager.fonts["button_large"],
            pady=15,
            state="disabled"
        )
        self.stop_btn.pack(fill=tk.X)

    def _on_start_clicked(self):
        """
        Maneja el clic en el botón de iniciar
        """
        if self.start_callback:
            self.start_callback()

    def _on_stop_clicked(self):
        """
        Maneja el clic en el botón de detener
        """
        if self.stop_callback:
            self.stop_callback()

    def set_automation_state(self, is_active):
        """
        Actualiza el estado visual de los botones según el estado de automatización

        Args:
            is_active: True si la automatización está activa
        """
        self.automation_active = is_active

        if is_active:
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
        else:
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")

    def is_automation_active(self):
        """
        Verifica si la automatización está activa

        Returns:
            bool: True si está activa
        """
        return self.automation_active


class AutomationTab:
    """
    Pestaña principal de automatización
    Coordina la configuración, estadísticas, controles y registro de actividad
    """

    def __init__(self, parent, style_manager: StyleManager, data_manager, whatsapp_bot, update_stats_callback):
        """
        Inicializa la pestaña de automatización

        Args:
            parent: Widget padre donde se mostrará la pestaña
            style_manager: Gestor de estilos para mantener consistencia visual
            data_manager: Gestor de datos para obtener contactos y mensajes
            whatsapp_bot: Instancia del bot de WhatsApp
            update_stats_callback: Callback para actualizar estadísticas globales
        """
        self.style_manager = style_manager
        self.data_manager = data_manager
        self.whatsapp_bot = whatsapp_bot
        self.update_stats_callback = update_stats_callback

        # Frame principal de la pestaña
        self.frame = style_manager.create_styled_frame(parent)

        # Crear componentes de la interfaz
        self._create_header()
        self._create_config_section()
        self._create_stats_section()
        self._create_control_section()
        self._create_activity_log()

        # Actualizar estadísticas iniciales
        self._update_stats()

    def _create_header(self):
        """
        Crea la cabecera de la pestaña con título y descripción
        """
        TabHeader(
            self.frame,
            self.style_manager,
            "Automatización",
            "Controla la automatización del envío de mensajes a tus contactos con soporte completo para emoticones"
        )

    def _create_config_section(self):
        """
        Crea la sección de configuración de automatización
        """
        self.config_section = AutomationConfigSection(
            self.frame,
            self.style_manager
        )

    def _create_stats_section(self):
        """
        Crea la sección de estadísticas
        """
        self.stats_display = StatsDisplay(self.frame, self.style_manager)

    def _create_control_section(self):
        """
        Crea la sección de controles de automatización
        """
        self.control_section = AutomationControlSection(
            self.frame,
            self.style_manager,
            start_callback=self._start_automation,
            stop_callback=self._stop_automation
        )

    def _create_activity_log(self):
        """
        Crea el registro de actividad
        """
        self.activity_log = ActivityLog(
            self.frame,
            self.style_manager,
            "📋 Registro de Actividad"
        )

    def _start_automation(self):
        """
        Inicia la automatización del bot
        Valida la configuración y datos antes de iniciar
        """
        # Validar configuración
        if not self._validate_automation_config():
            return

        # Validar datos disponibles
        if not self._validate_automation_data():
            return

        # Obtener configuración
        min_interval, max_interval = self.config_section.get_intervals()
        numbers = self.data_manager.get_numbers_only()
        messages = self.data_manager.get_messages()

        # Actualizar estado de controles
        self.control_section.set_automation_state(True)

        # Iniciar automatización en hilo separado
        self._start_automation_thread(numbers, messages, min_interval, max_interval)

    def _validate_automation_config(self):
        """
        Valida la configuración de automatización

        Returns:
            bool: True si la configuración es válida
        """
        is_valid, error_message = self.config_section.validate_intervals()
        if not is_valid:
            show_error_message(error_message)
            return False
        return True

    def _validate_automation_data(self):
        """
        Valida que haya contactos y mensajes disponibles

        Returns:
            bool: True si hay datos suficientes para automatización
        """
        numbers = self.data_manager.get_numbers_only()
        messages = self.data_manager.get_messages()

        if not numbers:
            show_error_message("No hay contactos configurados.\nAgrega contactos en la pestaña 'Contactos'.")
            return False

        if not messages:
            show_error_message("No hay mensajes configurados.\nAgrega mensajes en la pestaña 'Mensajes'.")
            return False

        return True

    def _start_automation_thread(self, numbers, messages, min_interval, max_interval):
        """
        Inicia la automatización en un hilo separado

        Args:
            numbers: Lista de números de contactos
            messages: Lista de mensajes
            min_interval: Intervalo mínimo entre mensajes
            max_interval: Intervalo máximo entre mensajes
        """
        automation_thread = threading.Thread(
            target=self.whatsapp_bot.start_automation,
            args=(numbers, messages, min_interval, max_interval),
            daemon=True
        )
        automation_thread.start()

        # Mostrar mensaje de inicio
        self.activity_log.add_message("🚀 Automatización iniciada...")
        self.activity_log.add_message(f"📊 Enviando a {len(numbers)} contactos con {len(messages)} mensajes")
        self.activity_log.add_message(f"⏱️ Intervalo: {min_interval}-{max_interval} segundos")

    def _stop_automation(self):
        """
        Detiene la automatización del bot
        """
        self.whatsapp_bot.stop_automation()
        self._automation_finished()
        self.activity_log.add_message("🛑 Automatización detenida por el usuario")

    def _automation_finished(self):
        """
        Callback ejecutado cuando termina la automatización
        Restaura el estado de los controles
        """
        self.control_section.set_automation_state(False)

    def _update_stats(self):
        """
        Actualiza las estadísticas mostradas en la interfaz
        """
        contacts_count = len(self.data_manager.get_contacts())
        messages_count = len(self.data_manager.get_messages())
        self.stats_display.update_stats(contacts_count, messages_count)

    def update_status(self, message):
        """
        Actualiza el status y registro de actividad

        Args:
            message: Mensaje de estado del bot
        """
        self.activity_log.add_message(message)

        # Detectar fin de automatización por mensajes específicos
        completion_indicators = [
            "completada",
            "detenida",
            "Error en automatización",
            "Sesión perdida"
        ]

        if any(indicator in message for indicator in completion_indicators):
            self._automation_finished()

    def on_show(self):
        """
        Callback ejecutado cuando se muestra la pestaña
        Actualiza las estadísticas y callback global
        """
        self._update_stats()
        if self.update_stats_callback:
            self.update_stats_callback()

    def get_frame(self):
        """
        Retorna el frame principal de la pestaña

        Returns:
            tk.Frame: Frame contenedor de toda la pestaña
        """
        return self.frame

    def is_automation_active(self):
        """
        Verifica si la automatización está actualmente activa

        Returns:
            bool: True si la automatización está corriendo
        """
        return self.control_section.is_automation_active() or self.whatsapp_bot.is_active()

    def get_automation_stats(self):
        """
        Obtiene estadísticas actuales de automatización

        Returns:
            dict: Diccionario con estadísticas de automatización
        """
        return {
            'contacts_count': len(self.data_manager.get_contacts()),
            'messages_count': len(self.data_manager.get_messages()),
            'is_active': self.is_automation_active(),
            'intervals': self.config_section.get_intervals()
        }