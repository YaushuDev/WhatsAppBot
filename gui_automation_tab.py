# gui_automation_tab.py
"""
Pestaña de automatización para el Bot de WhatsApp
Este módulo implementa la funcionalidad de control y configuración de la automatización
del bot con layout horizontal compacto, donde los controles están a la izquierda y el
registro de actividad a la derecha. Incluye configuración de intervalos, estadísticas
en tiempo real, controles de inicio/detención, descarga de logs y configuración del
navegador optimizado para pantallas de 1000x600px.
ACTUALIZADO: Persistencia de configuración, descarga de logs, y opción de mantener navegador abierto.
"""

import tkinter as tk
import threading
import datetime
from tkinter import filedialog, messagebox
from gui_styles import StyleManager
from gui_components import (ActivityLog, show_error_message, show_success_message)


class AutomationConfigSection:
    """
    Sección de configuración de la automatización compacta con persistencia y configuración del navegador
    Maneja los parámetros de intervalos entre mensajes y opciones del navegador optimizada para layout horizontal
    con capacidad de guardar y cargar configuración automáticamente
    """

    def __init__(self, parent, style_manager: StyleManager, data_manager):
        """
        Inicializa la sección de configuración compacta con persistencia y opciones del navegador

        Args:
            parent: Widget padre donde se mostrará la sección
            style_manager: Gestor de estilos para mantener consistencia visual
            data_manager: Gestor de datos para cargar/guardar configuración
        """
        self.style_manager = style_manager
        self.data_manager = data_manager

        # Variables para la nueva configuración
        self.keep_browser_open = tk.BooleanVar()

        # Crear frame principal de configuración más compacto
        self._create_compact_config_frame(parent)
        self._create_compact_interval_controls()
        self._create_browser_config_section()  # NUEVO
        self._create_save_button()

        # Cargar configuración guardada al inicializar
        self._load_saved_config()

    def _create_compact_config_frame(self, parent):
        """
        Crea el frame principal de configuración compacto

        Args:
            parent: Widget padre
        """
        self.config_frame = self.style_manager.create_styled_labelframe(
            parent,
            "⚙️ Configuración"
        )
        self.config_frame.pack(fill=tk.X, padx=0, pady=(0, 8))

        # Contenido interno más compacto
        self.content_frame = self.style_manager.create_styled_frame(self.config_frame)
        self.content_frame.pack(fill=tk.X, padx=8, pady=8)

    def _create_compact_interval_controls(self):
        """
        Crea los controles de configuración de intervalos más compactos
        """
        # Descripción más concisa
        description_label = self.style_manager.create_styled_label(
            self.content_frame,
            "Tiempo entre mensajes (seg):",
            "small"
        )
        description_label.pack(anchor="w", pady=(0, 6))

        # Frame para los inputs más compacto
        self._create_compact_interval_inputs()

    def _create_compact_interval_inputs(self):
        """
        Crea los campos de entrada para intervalos en layout compacto
        """
        inputs_frame = self.style_manager.create_styled_frame(self.content_frame)
        inputs_frame.pack(fill=tk.X, pady=(0, 8))

        # Input mínimo
        self._create_min_interval_input(inputs_frame)

        # Input máximo
        self._create_max_interval_input(inputs_frame)

    def _create_min_interval_input(self, parent):
        """
        Crea el input para el intervalo mínimo más compacto

        Args:
            parent: Widget padre
        """
        min_container = self.style_manager.create_styled_frame(parent)
        min_container.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        min_label = self.style_manager.create_styled_label(min_container, "Mín:", "small")
        min_label.pack(anchor="w")

        self.min_interval = self.style_manager.create_styled_entry(min_container)
        self.min_interval.pack(fill=tk.X, pady=(2, 0))
        self.min_interval.insert(0, "30")

    def _create_max_interval_input(self, parent):
        """
        Crea el input para el intervalo máximo más compacto

        Args:
            parent: Widget padre
        """
        max_container = self.style_manager.create_styled_frame(parent)
        max_container.pack(side=tk.LEFT, fill=tk.X, expand=True)

        max_label = self.style_manager.create_styled_label(max_container, "Máx:", "small")
        max_label.pack(anchor="w")

        self.max_interval = self.style_manager.create_styled_entry(max_container)
        self.max_interval.pack(fill=tk.X, pady=(2, 0))
        self.max_interval.insert(0, "60")

    def _create_browser_config_section(self):
        """
        NUEVO: Crea la sección de configuración del navegador
        """
        # Separador visual
        separator = self.style_manager.create_styled_frame(self.content_frame, "border")
        separator.configure(height=1)
        separator.pack(fill=tk.X, pady=(8, 6))

        # Título de la sección
        browser_label = self.style_manager.create_styled_label(
            self.content_frame,
            "Navegador:",
            "small"
        )
        browser_label.pack(anchor="w", pady=(0, 4))

        # Checkbox para mantener navegador abierto
        browser_frame = self.style_manager.create_styled_frame(self.content_frame)
        browser_frame.pack(fill=tk.X, pady=(0, 8))

        self.browser_checkbox = tk.Checkbutton(
            browser_frame,
            text="🌐 Mantener navegador abierto al finalizar",
            variable=self.keep_browser_open,
            font=self.style_manager.fonts["small"],
            bg=self.style_manager.colors["bg_primary"],
            fg=self.style_manager.colors["text_primary"],
            selectcolor=self.style_manager.colors["bg_accent"],
            activebackground=self.style_manager.colors["bg_primary"],
            activeforeground=self.style_manager.colors["text_primary"],
            border=0,
            highlightthickness=0
        )
        self.browser_checkbox.pack(anchor="w")

    def _create_save_button(self):
        """
        Crea el botón para guardar la configuración
        """
        save_btn = self.style_manager.create_styled_button(
            self.content_frame,
            "💾 Guardar",
            self._save_config,
            "accent"
        )
        save_btn.configure(pady=6)
        save_btn.pack(pady=(4, 0))

    def _load_saved_config(self):
        """
        Carga la configuración guardada desde el data manager
        """
        try:
            config = self.data_manager.get_config()

            # Cargar intervalos
            min_interval = config.get("intervalo_min", 30)
            max_interval = config.get("intervalo_max", 60)

            self.min_interval.delete(0, tk.END)
            self.min_interval.insert(0, str(min_interval))

            self.max_interval.delete(0, tk.END)
            self.max_interval.insert(0, str(max_interval))

            # NUEVO: Cargar configuración del navegador
            keep_browser_open = config.get("mantener_navegador_abierto", False)
            self.keep_browser_open.set(keep_browser_open)

        except Exception as e:
            print(f"Error cargando configuración: {e}")

    def _save_config(self):
        """
        Guarda la configuración actual usando el data manager
        """
        try:
            # Validar antes de guardar
            is_valid, error_message = self.validate_intervals()
            if not is_valid:
                show_error_message(f"No se puede guardar: {error_message}")
                return

            # Obtener valores actuales
            min_val, max_val = self.get_intervals()

            # Obtener configuración actual y actualizar
            current_config = self.data_manager.get_config()
            current_config["intervalo_min"] = min_val
            current_config["intervalo_max"] = max_val

            # NUEVO: Guardar configuración del navegador
            current_config["mantener_navegador_abierto"] = self.keep_browser_open.get()

            # Guardar configuración
            self.data_manager.save_config(current_config)

            show_success_message("Configuración guardada correctamente")

        except Exception as e:
            show_error_message(f"Error al guardar configuración: {str(e)}")

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

    def get_browser_keep_open(self) -> bool:
        """
        NUEVO: Obtiene la configuración de mantener navegador abierto

        Returns:
            True si debe mantener el navegador abierto
        """
        return self.keep_browser_open.get()

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
    Sección de controles de automatización compacta con descarga de logs
    Maneja los botones de inicio, detención del bot y descarga de logs optimizada para layout horizontal
    """

    def __init__(self, parent, style_manager: StyleManager, activity_log_ref=None,
                 start_callback=None, stop_callback=None):
        """
        Inicializa la sección de controles compacta con referencia al log

        Args:
            parent: Widget padre donde se mostrará la sección
            style_manager: Gestor de estilos para mantener consistencia visual
            activity_log_ref: Referencia al componente ActivityLog para descarga
            start_callback: Función a ejecutar al iniciar automatización
            stop_callback: Función a ejecutar al detener automatización
        """
        self.style_manager = style_manager
        self.activity_log_ref = activity_log_ref
        self.start_callback = start_callback
        self.stop_callback = stop_callback
        self.automation_active = False

        # Crear controles compactos
        self._create_compact_control_frame(parent)
        self._create_compact_control_buttons()

    def _create_compact_control_frame(self, parent):
        """
        Crea el frame principal de controles compacto

        Args:
            parent: Widget padre
        """
        self.control_frame = self.style_manager.create_styled_frame(parent)
        self.control_frame.pack(fill=tk.X, padx=0, pady=8)

    def _create_compact_control_buttons(self):
        """
        Crea los botones de control de automatización más compactos con descarga de log
        """
        # Botón iniciar más compacto
        self.start_btn = self.style_manager.create_styled_button(
            self.control_frame,
            "▶️ Iniciar",
            self._on_start_clicked,
            "success"
        )
        self.start_btn.configure(pady=8)
        self.start_btn.pack(fill=tk.X, pady=(0, 6))

        # Botón detener más compacto
        self.stop_btn = self.style_manager.create_styled_button(
            self.control_frame,
            "⏹️ Detener",
            self._on_stop_clicked,
            "error"
        )
        self.stop_btn.configure(
            pady=8,
            state="disabled"
        )
        self.stop_btn.pack(fill=tk.X, pady=(0, 6))

        # NUEVO: Botón descargar log
        self.download_btn = self.style_manager.create_styled_button(
            self.control_frame,
            "💾 Descargar Log",
            self._on_download_log_clicked,
            "normal"
        )
        self.download_btn.configure(pady=8)
        self.download_btn.pack(fill=tk.X)

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

    def _on_download_log_clicked(self):
        """
        NUEVO: Maneja el clic en el botón de descargar log
        """
        try:
            if not self.activity_log_ref:
                show_error_message("No hay registro de actividad disponible para descargar")
                return

            # Obtener contenido del log
            log_content = self._get_log_content()

            if not log_content.strip():
                show_error_message("El registro de actividad está vacío")
                return

            # Abrir diálogo para guardar archivo
            current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"whatsapp_bot_log_{current_time}.txt"

            file_path = filedialog.asksaveasfilename(
                title="Guardar registro de actividad",
                defaultextension=".txt",
                filetypes=[
                    ("Archivos de texto", "*.txt"),
                    ("Todos los archivos", "*.*")
                ],
                initialfile=default_filename
            )

            if file_path:
                self._save_log_to_file(log_content, file_path)

        except Exception as e:
            show_error_message(f"Error al descargar log: {str(e)}")

    def _get_log_content(self) -> str:
        """
        NUEVO: Obtiene el contenido completo del log

        Returns:
            String con todo el contenido del log
        """
        try:
            if hasattr(self.activity_log_ref, 'log_text'):
                # Obtener todo el contenido del widget de texto
                log_widget = self.activity_log_ref.log_text
                return log_widget.get(1.0, tk.END)
            else:
                return "Error: No se pudo acceder al contenido del log"
        except Exception as e:
            return f"Error al obtener contenido del log: {str(e)}"

    def _save_log_to_file(self, content: str, file_path: str):
        """
        NUEVO: Guarda el contenido del log en un archivo

        Args:
            content: Contenido del log
            file_path: Ruta donde guardar el archivo
        """
        try:
            # Crear header informativo
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            header = f"""# WhatsApp Bot - Registro de Actividad
# Generado: {current_time}
# ==========================================

"""

            # Combinar header con contenido
            full_content = header + content

            # Guardar archivo
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(full_content)

            # Mostrar confirmación con información del archivo
            import os
            file_size = os.path.getsize(file_path)
            show_success_message(
                f"Log guardado exitosamente:\n\n"
                f"📁 Archivo: {os.path.basename(file_path)}\n"
                f"📊 Tamaño: {file_size:,} bytes\n"
                f"📍 Ubicación: {file_path}"
            )

        except Exception as e:
            show_error_message(f"Error al guardar archivo: {str(e)}")

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
            # El botón de descarga se mantiene habilitado siempre
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


class CompactStatsDisplay:
    """
    Componente compacto para mostrar estadísticas optimizado para layout horizontal
    """

    def __init__(self, parent, style_manager: StyleManager):
        """
        Inicializa el display de estadísticas compacto

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
        """
        self.style_manager = style_manager

        # Frame más compacto
        self.stats_frame = style_manager.create_styled_labelframe(parent, "📊 Estadísticas")
        self.stats_frame.pack(fill=tk.X, padx=0, pady=(0, 8))

        # Contenido compacto
        content_frame = style_manager.create_styled_frame(self.stats_frame)
        content_frame.pack(fill=tk.X, padx=8, pady=6)

        # Estadísticas en columna simple para ahorrar espacio
        self.stats_numbers = style_manager.create_styled_label(content_frame, "📱 Contactos: 0", "small")
        self.stats_numbers.pack(anchor="w")

        self.stats_messages = style_manager.create_styled_label(content_frame, "💬 Mensajes: 0", "small")
        self.stats_messages.pack(anchor="w", pady=(2, 0))

    def update_stats(self, numbers_count, messages_count):
        """
        Actualiza las estadísticas mostradas

        Args:
            numbers_count: Cantidad de contactos
            messages_count: Cantidad de mensajes
        """
        self.stats_numbers.configure(text=f"📱 Contactos: {numbers_count}")
        self.stats_messages.configure(text=f"💬 Mensajes: {messages_count}")


class AutomationTab:
    """
    Pestaña principal de automatización con layout horizontal compacto
    Coordina la configuración, estadísticas, controles, descarga de logs y registro de actividad
    optimizado para 1000x600px con configuración persistente de intervalos, navegador y soporte
    completo para personalización de mensajes
    """

    def __init__(self, parent, style_manager: StyleManager, data_manager, whatsapp_bot, update_stats_callback):
        """
        Inicializa la pestaña de automatización con layout horizontal y nuevas funcionalidades

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

        # Crear layout horizontal
        self._create_horizontal_layout()

        # Actualizar estadísticas iniciales
        self._update_stats()

    def _create_horizontal_layout(self):
        """
        Crea el layout horizontal principal: controles | log
        """
        # Header compacto
        self._create_compact_header()

        # Container principal con layout horizontal
        main_container = self.style_manager.create_styled_frame(self.frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        # Columna izquierda: Controles y configuración (40%)
        self.left_column = self.style_manager.create_styled_frame(main_container)
        self.left_column.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 8))
        self.left_column.configure(width=400)
        self.left_column.pack_propagate(False)

        # Columna derecha: Activity log (60%)
        self.right_column = self.style_manager.create_styled_frame(main_container)
        self.right_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))

        # Crear componentes en cada columna
        self._create_left_column_components()
        self._create_right_column_components()

    def _create_compact_header(self):
        """
        Crea la cabecera compacta de la pestaña
        """
        # Container del header con padding reducido
        header_container = self.style_manager.create_styled_frame(self.frame)
        header_container.pack(fill=tk.X, padx=12, pady=(12, 8))

        # Título
        title_label = self.style_manager.create_styled_label(header_container, "Automatización", "title")
        title_label.pack(anchor="w")

        # Descripción más concisa
        desc_label = self.style_manager.create_styled_label(
            header_container,
            "Controla la automatización del envío de mensajes con personalización automática",
            "secondary"
        )
        desc_label.pack(anchor="w", pady=(4, 0))

        # Línea separadora más sutil
        separator = self.style_manager.create_styled_frame(header_container, "accent")
        separator.configure(height=1)
        separator.pack(fill=tk.X, pady=(8, 0))

    def _create_left_column_components(self):
        """
        Crea los componentes de la columna izquierda (controles) con configuración persistente y nuevas opciones
        """
        # Configuración de automatización con persistencia y navegador
        self.config_section = AutomationConfigSection(
            self.left_column,
            self.style_manager,
            self.data_manager
        )

        # Estadísticas compactas
        self.stats_display = CompactStatsDisplay(self.left_column, self.style_manager)

        # Controles de automatización (se creará después del activity log)
        self.control_section = None

    def _create_right_column_components(self):
        """
        Crea los componentes de la columna derecha (activity log)
        """
        # Crear activity log en la columna derecha
        self.activity_log = ActivityLog(
            self.right_column,
            self.style_manager,
            "📋 Registro de Actividad"
        )

        # Ajustar padding para layout compacto
        self.activity_log.log_text.master.master.pack_configure(padx=0, pady=(0, 8))

        # Ahora crear los controles con referencia al log
        self.control_section = AutomationControlSection(
            self.left_column,
            self.style_manager,
            activity_log_ref=self.activity_log,  # Pasar referencia al log
            start_callback=self._start_automation,
            stop_callback=self._stop_automation
        )

    def _start_automation(self):
        """
        Inicia la automatización del bot con configuración del navegador
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
        keep_browser_open = self.config_section.get_browser_keep_open()  # NUEVO

        # Usar contactos completos en lugar de solo números
        contacts = self.data_manager.get_contacts()
        messages = self.data_manager.get_messages()

        # Actualizar estado de controles
        self.control_section.set_automation_state(True)

        # Detectar y reportar personalización
        personalization_info = self.whatsapp_bot.check_message_personalization(messages)
        if personalization_info.get('has_personalization'):
            placeholders = ', '.join(personalization_info.get('placeholders_found', []))
            self.activity_log.add_message(f"👤 Personalización detectada: {placeholders}")
            self.activity_log.add_message(
                f"📊 {personalization_info['personalizable_messages']} de {personalization_info['total_messages']} mensajes serán personalizados")

        # NUEVO: Reportar configuración del navegador
        if keep_browser_open:
            self.activity_log.add_message("🌐 Navegador se mantendrá abierto al finalizar")
        else:
            self.activity_log.add_message("🔒 Navegador se cerrará al finalizar")

        # Iniciar automatización en hilo separado con contactos completos y configuración del navegador
        self._start_automation_thread(contacts, messages, min_interval, max_interval, keep_browser_open)

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
        contacts = self.data_manager.get_contacts()
        messages = self.data_manager.get_messages()

        if not contacts:
            show_error_message("No hay contactos configurados.\nAgrega contactos en la pestaña 'Contactos'.")
            return False

        if not messages:
            show_error_message("No hay mensajes configurados.\nAgrega mensajes en la pestaña 'Mensajes'.")
            return False

        return True

    def _start_automation_thread(self, contacts, messages, min_interval, max_interval, keep_browser_open):
        """
        ACTUALIZADO: Inicia la automatización en un hilo separado con configuración del navegador

        Args:
            contacts: Lista de contactos completos (con nombre y número)
            messages: Lista de mensajes
            min_interval: Intervalo mínimo entre mensajes
            max_interval: Intervalo máximo entre mensajes
            keep_browser_open: Si mantener el navegador abierto al finalizar
        """
        # ACTUALIZADO: Usar método modificado del bot que acepta configuración del navegador
        automation_thread = threading.Thread(
            target=self._run_automation_with_browser_config,
            args=(contacts, messages, min_interval, max_interval, keep_browser_open),
            daemon=True
        )
        automation_thread.start()

        # Mostrar mensaje de inicio
        self.activity_log.add_message("🚀 Automatización iniciada...")
        self.activity_log.add_message(f"📊 Enviando a {len(contacts)} contactos con {len(messages)} mensajes")
        self.activity_log.add_message(f"⏱️ Intervalo: {min_interval}-{max_interval} segundos")

    def _run_automation_with_browser_config(self, contacts, messages, min_interval, max_interval, keep_browser_open):
        """
        NUEVO: Ejecuta la automatización con configuración del navegador
        """
        try:
            # Intentar usar el método nuevo con configuración del navegador
            if hasattr(self.whatsapp_bot, 'start_automation_with_browser_config'):
                self.whatsapp_bot.start_automation_with_browser_config(
                    contacts, messages, min_interval, max_interval, keep_browser_open
                )
            else:
                # Fallback al método original - el AutomationController ya maneja la configuración
                self.whatsapp_bot.start_automation(contacts, messages, min_interval, max_interval)
                # Nota: La configuración del navegador se pasará a través del AutomationController modificado
        except Exception as e:
            self.activity_log.add_message(f"❌ Error en automatización: {str(e)}")
            self._automation_finished()

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
            'intervals': self.config_section.get_intervals(),
            'keep_browser_open': self.config_section.get_browser_keep_open()  # NUEVO
        }