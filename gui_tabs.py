# gui_tabs.py
"""
Pestañas del Bot de WhatsApp
Implementa la lógica específica de cada pestaña (números, mensajes, automatización)
utilizando los componentes reutilizables para mantener el código organizado y conciso
"""

import tkinter as tk
from tkinter import scrolledtext
import threading
from gui_styles import StyleManager
from gui_components import (TabHeader, ListManager, InputSection, StatsDisplay,
                            ActivityLog, show_validation_error, show_success_message,
                            show_error_message, show_confirmation_dialog)


class NumbersTab:
    """
    Pestaña de gestión de números de teléfono
    """

    def __init__(self, parent, style_manager: StyleManager, data_manager):
        """
        Inicializa la pestaña de números

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
            data_manager: Gestor de datos
        """
        self.style_manager = style_manager
        self.data_manager = data_manager

        # Frame principal de la pestaña
        self.frame = style_manager.create_styled_frame(parent)

        # Cabecera
        TabHeader(
            self.frame,
            style_manager,
            "Gestión de Números",
            "Agrega y gestiona los números de teléfono a los que se enviarán mensajes"
        )

        # Sección de entrada
        self.input_section = InputSection(
            self.frame,
            style_manager,
            "Número de teléfono:",
            "entry",
            "Agregar",
            self._add_number
        )

        # Lista de números
        self.list_manager = ListManager(
            self.frame,
            style_manager,
            "Números guardados:",
            delete_callback=self._delete_number
        )

        # Cargar números existentes
        self._refresh_numbers()

    def _add_number(self):
        """
        Agrega un número de teléfono
        """
        number = self.input_section.get_value()

        if not number:
            show_validation_error("Por favor ingresa un número de teléfono")
            return

        if self.data_manager.add_number(number):
            self.input_section.clear_value()
            self._refresh_numbers()
            show_success_message("Número agregado correctamente")
        else:
            show_error_message("El número ya existe o es inválido")

    def _delete_number(self):
        """
        Elimina el número seleccionado
        """
        index, number = self.list_manager.get_selection()

        if index is None:
            show_validation_error("Por favor selecciona un número para eliminar")
            return

        if show_confirmation_dialog(f"¿Eliminar el número {number}?"):
            if self.data_manager.remove_number(number):
                self._refresh_numbers()
                show_success_message("Número eliminado correctamente")

    def _refresh_numbers(self):
        """
        Actualiza la lista de números
        """
        numbers = self.data_manager.get_numbers()
        self.list_manager.clear_and_populate(numbers)

    def get_frame(self):
        """
        Retorna el frame de la pestaña
        """
        return self.frame


class MessagesTab:
    """
    Pestaña de gestión de mensajes
    """

    def __init__(self, parent, style_manager: StyleManager, data_manager):
        """
        Inicializa la pestaña de mensajes

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
            data_manager: Gestor de datos
        """
        self.style_manager = style_manager
        self.data_manager = data_manager

        # Frame principal de la pestaña
        self.frame = style_manager.create_styled_frame(parent)

        # Cabecera
        TabHeader(
            self.frame,
            style_manager,
            "Gestión de Mensajes",
            "Crea y gestiona los mensajes que el bot enviará aleatoriamente"
        )

        # Sección de entrada para mensajes
        self.input_section = InputSection(
            self.frame,
            style_manager,
            "Nuevo mensaje:",
            "text",
            "Agregar Mensaje",
            self._add_message
        )

        # Lista de mensajes
        self.list_manager = ListManager(
            self.frame,
            style_manager,
            "Mensajes guardados:",
            delete_callback=self._delete_message,
            edit_callback=self._edit_message
        )

        # Cargar mensajes existentes
        self._refresh_messages()

    def _add_message(self):
        """
        Agrega un mensaje
        """
        message = self.input_section.get_value()

        if not message:
            show_validation_error("Por favor ingresa un mensaje")
            return

        if self.data_manager.add_message(message):
            self.input_section.clear_value()
            self._refresh_messages()
            show_success_message("Mensaje agregado correctamente")
        else:
            show_error_message("Error al agregar el mensaje")

    def _edit_message(self):
        """
        Edita el mensaje seleccionado
        """
        index, display_text = self.list_manager.get_selection()

        if index is None:
            show_validation_error("Por favor selecciona un mensaje para editar")
            return

        # Obtener el mensaje completo
        messages = self.data_manager.get_messages()
        if index >= len(messages):
            show_error_message("Mensaje no encontrado")
            return

        current_message = messages[index]

        # Crear ventana de edición
        self._create_edit_window(index, current_message)

    def _create_edit_window(self, index, current_message):
        """
        Crea la ventana de edición de mensaje

        Args:
            index: Índice del mensaje
            current_message: Mensaje actual
        """
        edit_window = tk.Toplevel()
        self.style_manager.configure_window(
            edit_window,
            "Editar Mensaje",
            "400x300"
        )
        edit_window.grab_set()

        # Etiqueta
        label = self.style_manager.create_styled_label(
            edit_window,
            "Editar mensaje:",
            "normal"
        )
        label.pack(pady=10)

        # Área de texto
        edit_text = scrolledtext.ScrolledText(
            edit_window,
            height=10,
            font=self.style_manager.fonts["normal"],
            bg=self.style_manager.colors["bg_secondary"],
            fg=self.style_manager.colors["text_primary"],
            wrap=tk.WORD
        )
        edit_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        edit_text.insert(1.0, current_message)

        # Botón guardar
        def save_edit():
            new_message = edit_text.get(1.0, tk.END).strip()
            if new_message and self.data_manager.update_message(index, new_message):
                self._refresh_messages()
                edit_window.destroy()
                show_success_message("Mensaje actualizado correctamente")
            else:
                show_error_message("Error al actualizar el mensaje")

        save_btn = self.style_manager.create_styled_button(
            edit_window,
            "Guardar",
            save_edit,
            "accent"
        )
        save_btn.pack(pady=10)

    def _delete_message(self):
        """
        Elimina el mensaje seleccionado
        """
        index, display_text = self.list_manager.get_selection()

        if index is None:
            show_validation_error("Por favor selecciona un mensaje para eliminar")
            return

        if show_confirmation_dialog("¿Eliminar el mensaje seleccionado?"):
            if self.data_manager.remove_message(index):
                self._refresh_messages()
                show_success_message("Mensaje eliminado correctamente")

    def _refresh_messages(self):
        """
        Actualiza la lista de mensajes
        """
        messages = self.data_manager.get_messages()
        # Mostrar solo las primeras 50 caracteres para la lista
        display_messages = []
        for i, message in enumerate(messages):
            display_text = message[:50] + "..." if len(message) > 50 else message
            display_messages.append(f"{i + 1}. {display_text}")

        self.list_manager.clear_and_populate(display_messages)

    def get_frame(self):
        """
        Retorna el frame de la pestaña
        """
        return self.frame


class AutomationTab:
    """
    Pestaña de automatización
    """

    def __init__(self, parent, style_manager: StyleManager, data_manager, whatsapp_bot, update_stats_callback):
        """
        Inicializa la pestaña de automatización

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
            data_manager: Gestor de datos
            whatsapp_bot: Instancia del bot
            update_stats_callback: Callback para actualizar estadísticas
        """
        self.style_manager = style_manager
        self.data_manager = data_manager
        self.whatsapp_bot = whatsapp_bot
        self.update_stats_callback = update_stats_callback
        self.automation_active = False

        # Frame principal de la pestaña
        self.frame = style_manager.create_styled_frame(parent)

        # Cabecera
        TabHeader(
            self.frame,
            style_manager,
            "Automatización",
            "Controla la automatización del envío de mensajes"
        )

        # Configuración de intervalos
        self._create_config_section()

        # Estadísticas
        self.stats_display = StatsDisplay(self.frame, style_manager)

        # Controles de automatización
        self._create_automation_controls()

        # Log de actividad
        self.activity_log = ActivityLog(self.frame, style_manager)

        # Actualizar estadísticas iniciales
        self._update_stats()

    def _create_config_section(self):
        """
        Crea la sección de configuración de intervalos
        """
        config_frame = self.style_manager.create_styled_labelframe(
            self.frame,
            "Configuración"
        )
        config_frame.pack(fill=tk.X, padx=20, pady=10)

        # Frame para intervalos
        intervals_frame = self.style_manager.create_styled_frame(config_frame)
        intervals_frame.pack(fill=tk.X, padx=10, pady=10)

        # Etiqueta
        label = self.style_manager.create_styled_label(
            intervals_frame,
            "Intervalo entre mensajes (segundos):",
            "normal"
        )
        label.pack(anchor="w")

        # Frame para inputs
        inputs_frame = self.style_manager.create_styled_frame(intervals_frame)
        inputs_frame.pack(fill=tk.X, pady=(5, 0))

        # Mínimo
        min_label = self.style_manager.create_styled_label(inputs_frame, "Mínimo:", "normal")
        min_label.pack(side=tk.LEFT)

        self.min_interval = self.style_manager.create_styled_entry(inputs_frame)
        self.min_interval.configure(width=10)
        self.min_interval.pack(side=tk.LEFT, padx=(5, 15))
        self.min_interval.insert(0, "30")

        # Máximo
        max_label = self.style_manager.create_styled_label(inputs_frame, "Máximo:", "normal")
        max_label.pack(side=tk.LEFT)

        self.max_interval = self.style_manager.create_styled_entry(inputs_frame)
        self.max_interval.configure(width=10)
        self.max_interval.pack(side=tk.LEFT, padx=(5, 0))
        self.max_interval.insert(0, "60")

    def _create_automation_controls(self):
        """
        Crea los controles de automatización
        """
        control_frame = self.style_manager.create_styled_frame(self.frame)
        control_frame.pack(fill=tk.X, padx=20, pady=20)

        # Botón iniciar
        self.start_btn = self.style_manager.create_styled_button(
            control_frame,
            "▶ Iniciar Automatización",
            self._start_automation,
            "success"
        )
        self.start_btn.configure(
            font=self.style_manager.fonts["button_large"],
            pady=15
        )
        self.start_btn.pack(fill=tk.X, pady=(0, 10))

        # Botón detener
        self.stop_btn = self.style_manager.create_styled_button(
            control_frame,
            "⏹ Detener Automatización",
            self._stop_automation,
            "error"
        )
        self.stop_btn.configure(
            font=self.style_manager.fonts["button_large"],
            pady=15,
            state="disabled"
        )
        self.stop_btn.pack(fill=tk.X)

    def _start_automation(self):
        """
        Inicia la automatización
        """
        numbers = self.data_manager.get_numbers()
        messages = self.data_manager.get_messages()

        if not numbers:
            show_error_message("No hay números configurados")
            return

        if not messages:
            show_error_message("No hay mensajes configurados")
            return

        try:
            min_interval = int(self.min_interval.get())
            max_interval = int(self.max_interval.get())

            if min_interval <= 0 or max_interval <= 0 or min_interval > max_interval:
                show_error_message(
                    "Los intervalos deben ser números positivos y el mínimo debe ser menor al máximo"
                )
                return
        except ValueError:
            show_error_message("Los intervalos deben ser números válidos")
            return

        # Cambiar estado de botones
        self.automation_active = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

        # Iniciar automatización en hilo separado
        threading.Thread(
            target=self.whatsapp_bot.start_automation,
            args=(numbers, messages, min_interval, max_interval),
            daemon=True
        ).start()

    def _stop_automation(self):
        """
        Detiene la automatización
        """
        self.whatsapp_bot.stop_automation()
        self._automation_finished()

    def _automation_finished(self):
        """
        Callback cuando termina la automatización
        """
        self.automation_active = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")

    def _update_stats(self):
        """
        Actualiza las estadísticas
        """
        numbers_count = len(self.data_manager.get_numbers())
        messages_count = len(self.data_manager.get_messages())
        self.stats_display.update_stats(numbers_count, messages_count)

    def update_status(self, message):
        """
        Actualiza el status y log de actividad

        Args:
            message: Mensaje de estado
        """
        self.activity_log.add_message(message)

    def on_show(self):
        """
        Callback cuando se muestra la pestaña
        """
        self._update_stats()
        if self.update_stats_callback:
            self.update_stats_callback()

    def get_frame(self):
        """
        Retorna el frame de la pestaña
        """
        return self.frame


class TabManager:
    """
    Gestor de pestañas que coordina la navegación
    """

    def __init__(self, parent, style_manager: StyleManager, data_manager, whatsapp_bot, update_stats_callback):
        """
        Inicializa el gestor de pestañas

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
            data_manager: Gestor de datos
            whatsapp_bot: Instancia del bot
            update_stats_callback: Callback para actualizar estadísticas globales
        """
        self.style_manager = style_manager
        self.current_tab = "numeros"

        # Crear pestañas
        self.tabs = {
            "numeros": NumbersTab(parent, style_manager, data_manager),
            "mensajes": MessagesTab(parent, style_manager, data_manager),
            "automatizacion": AutomationTab(parent, style_manager, data_manager, whatsapp_bot, update_stats_callback)
        }

        # Mostrar pestaña inicial
        self.show_tab("numeros")

    def show_tab(self, tab_name):
        """
        Muestra la pestaña especificada

        Args:
            tab_name: Nombre de la pestaña a mostrar
        """
        # Ocultar todas las pestañas
        for tab in self.tabs.values():
            tab.get_frame().pack_forget()

        # Mostrar la pestaña seleccionada
        if tab_name in self.tabs:
            self.tabs[tab_name].get_frame().pack(fill=tk.BOTH, expand=True)
            self.current_tab = tab_name

            # Callback especial para automatización
            if tab_name == "automatizacion" and hasattr(self.tabs[tab_name], 'on_show'):
                self.tabs[tab_name].on_show()

    def get_current_tab(self):
        """
        Retorna el nombre de la pestaña actual
        """
        return self.current_tab

    def update_automation_status(self, message):
        """
        Actualiza el estado en la pestaña de automatización

        Args:
            message: Mensaje de estado
        """
        if "automatizacion" in self.tabs:
            self.tabs["automatizacion"].update_status(message)