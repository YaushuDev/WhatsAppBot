# gui_tabs.py
"""
Pestañas del Bot de WhatsApp
Implementa la lógica específica de cada pestaña (contactos, mensajes, automatización)
utilizando los componentes reutilizables para mantener el código organizado y conciso.
Incluye un sistema de sub-pestañas para la gestión de contactos con funcionalidad manual
y carga masiva desde archivos Excel.
"""

import tkinter as tk
from tkinter import scrolledtext
import threading
from gui_styles import StyleManager
from gui_components import (TabHeader, ListManager, InputSection, StatsDisplay,
                            ActivityLog, SubTabNavigator, ContactListManager,
                            ContactInputSection, ExcelUploadComponent, ContactEditDialog,
                            show_validation_error, show_success_message,
                            show_error_message, show_confirmation_dialog)


class ManualManagementSubTab:
    """
    Sub-pestaña de gestión manual de contactos
    """

    def __init__(self, parent, style_manager: StyleManager, data_manager):
        """
        Inicializa la sub-pestaña de gestión manual

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
            data_manager: Gestor de datos
        """
        self.style_manager = style_manager
        self.data_manager = data_manager

        # Frame principal de la sub-pestaña
        self.frame = style_manager.create_styled_frame(parent)

        # Sección de entrada de contactos
        self.input_section = ContactInputSection(
            self.frame,
            style_manager,
            "Nuevo contacto:",
            self._add_contact
        )

        # Lista de contactos
        self.list_manager = ContactListManager(
            self.frame,
            style_manager,
            "Contactos guardados:",
            edit_callback=self._edit_contact,
            delete_callback=self._delete_contact,
            clear_all_callback=self._clear_all_contacts
        )

        # Cargar contactos existentes
        self._refresh_contacts()

    def _add_contact(self):
        """
        Agrega un nuevo contacto
        """
        name, number = self.input_section.get_values()

        if not name:
            show_validation_error("Por favor ingresa el nombre del contacto")
            self.input_section.focus_name()
            return

        if not number:
            show_validation_error("Por favor ingresa el número de teléfono")
            return

        if self.data_manager.add_contact(name, number):
            self.input_section.clear_values()
            self.input_section.focus_name()
            self._refresh_contacts()
            show_success_message(f"Contacto '{name}' agregado correctamente")
        else:
            show_error_message("El número ya existe o es inválido")

    def _edit_contact(self):
        """
        Edita el contacto seleccionado
        """
        index, display_text = self.list_manager.get_selection()

        if index is None:
            show_validation_error("Por favor selecciona un contacto para editar")
            return

        # Obtener datos del contacto
        contact_data = self.data_manager.get_contact_by_index(index)
        if not contact_data:
            show_error_message("Contacto no encontrado")
            return

        # Crear y mostrar diálogo de edición
        def on_edit_complete(new_data):
            if new_data and self.data_manager.update_contact(index, new_data['nombre'], new_data['numero']):
                self._refresh_contacts()
                show_success_message(f"Contacto '{new_data['nombre']}' actualizado correctamente")
            elif new_data:
                show_error_message("Error al actualizar contacto. El número podría ya existir.")

        ContactEditDialog(
            self.frame.winfo_toplevel(),
            self.style_manager,
            contact_data,
            on_edit_complete
        )

    def _delete_contact(self):
        """
        Elimina el contacto seleccionado
        """
        index, display_text = self.list_manager.get_selection()

        if index is None:
            show_validation_error("Por favor selecciona un contacto para eliminar")
            return

        # Extraer nombre del display text
        contact_name = display_text.split(" - ")[0] if " - " in display_text else "este contacto"

        if show_confirmation_dialog(f"¿Eliminar {contact_name}?"):
            if self.data_manager.remove_contact(index):
                self._refresh_contacts()
                show_success_message("Contacto eliminado correctamente")
            else:
                show_error_message("Error al eliminar contacto")

    def _clear_all_contacts(self):
        """
        Elimina todos los contactos
        """
        contacts = self.data_manager.get_contacts()

        if not contacts:
            show_validation_error("No hay contactos para eliminar")
            return

        count = len(contacts)
        if show_confirmation_dialog(f"¿Eliminar TODOS los {count} contactos?\n\nEsta acción no se puede deshacer."):
            if self.data_manager.clear_all_contacts():
                self._refresh_contacts()
                show_success_message(f"Se eliminaron {count} contactos correctamente")
            else:
                show_error_message("Error al eliminar contactos")

    def _refresh_contacts(self):
        """
        Actualiza la lista de contactos
        """
        contacts = self.data_manager.get_contacts()
        self.list_manager.clear_and_populate(contacts)

    def get_frame(self):
        """
        Retorna el frame de la sub-pestaña
        """
        return self.frame

    def on_show(self):
        """
        Callback cuando se muestra la sub-pestaña
        """
        self._refresh_contacts()


class BulkLoadSubTab:
    """
    Sub-pestaña de carga masiva desde Excel
    """

    def __init__(self, parent, style_manager: StyleManager, data_manager):
        """
        Inicializa la sub-pestaña de carga masiva

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
            data_manager: Gestor de datos
        """
        self.style_manager = style_manager
        self.data_manager = data_manager

        # Frame principal de la sub-pestaña
        self.frame = style_manager.create_styled_frame(parent)

        # Componente de carga Excel
        self.excel_component = ExcelUploadComponent(
            self.frame,
            style_manager,
            self._import_contacts
        )

        # Estadísticas de importación
        self._create_import_stats()

    def _create_import_stats(self):
        """
        Crea la sección de estadísticas de importación
        """
        stats_frame = self.style_manager.create_styled_labelframe(
            self.frame,
            "📊 Estadísticas de Importación"
        )
        stats_frame.pack(fill=tk.X, padx=25, pady=(20, 0))

        content = self.style_manager.create_styled_frame(stats_frame)
        content.pack(fill=tk.X, padx=15, pady=15)

        # Stats container
        stats_container = self.style_manager.create_styled_frame(content)
        stats_container.pack(fill=tk.X)

        # Columnas de estadísticas
        left_col = self.style_manager.create_styled_frame(stats_container)
        left_col.pack(side=tk.LEFT, fill=tk.X, expand=True)

        right_col = self.style_manager.create_styled_frame(stats_container)
        right_col.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        # Labels de estadísticas
        self.current_contacts_label = self.style_manager.create_styled_label(
            left_col,
            "📱 Contactos actuales: 0",
            "normal"
        )
        self.current_contacts_label.pack(anchor="w")

        self.last_import_label = self.style_manager.create_styled_label(
            right_col,
            "📥 Última importación: -",
            "normal"
        )
        self.last_import_label.pack(anchor="e")

        # Actualizar estadísticas iniciales
        self._update_stats()

    def _import_contacts(self, contacts_data):
        """
        Importa los contactos desde Excel

        Args:
            contacts_data: Lista de contactos desde Excel
        """
        if not contacts_data:
            show_validation_error("No hay datos para importar")
            return

        try:
            # Importar contactos usando el método bulk del data manager
            added_count, total_count = self.data_manager.add_contacts_bulk(contacts_data)

            # Actualizar estadísticas
            self._update_stats()

            # Mostrar resultado
            if added_count == total_count:
                show_success_message(f"¡Importación exitosa!\n\nSe importaron {added_count} contactos correctamente")
            elif added_count > 0:
                duplicates = total_count - added_count
                show_success_message(
                    f"Importación parcial completada:\n\n"
                    f"✅ Importados: {added_count} contactos\n"
                    f"⚠️ Omitidos: {duplicates} (duplicados o inválidos)"
                )
            else:
                show_error_message(
                    f"No se pudo importar ningún contacto.\n"
                    f"Todos los {total_count} contactos ya existen o son inválidos."
                )

            # Actualizar label de última importación
            self.last_import_label.configure(
                text=f"📥 Última importación: {added_count}/{total_count}"
            )

        except Exception as e:
            show_error_message(f"Error durante la importación: {str(e)}")

    def _update_stats(self):
        """
        Actualiza las estadísticas mostradas
        """
        contacts_count = len(self.data_manager.get_contacts())
        self.current_contacts_label.configure(text=f"📱 Contactos actuales: {contacts_count}")

    def get_frame(self):
        """
        Retorna el frame de la sub-pestaña
        """
        return self.frame

    def on_show(self):
        """
        Callback cuando se muestra la sub-pestaña
        """
        self._update_stats()


class NumbersTab:
    """
    Pestaña principal de gestión de contactos con sub-pestañas
    """

    def __init__(self, parent, style_manager: StyleManager, data_manager):
        """
        Inicializa la pestaña de contactos

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
            data_manager: Gestor de datos
        """
        self.style_manager = style_manager
        self.data_manager = data_manager
        self.current_subtab = "manual"

        # Frame principal de la pestaña
        self.frame = style_manager.create_styled_frame(parent)

        # Cabecera
        TabHeader(
            self.frame,
            style_manager,
            "Gestión de Contactos",
            "Administra los contactos a los que se enviarán mensajes, usando gestión manual o carga masiva"
        )

        # Navegador de sub-pestañas
        subtabs_info = [
            ("manual", "Gestión Manual", "✏️"),
            ("bulk", "Carga Masiva", "📁")
        ]

        self.subtab_navigator = SubTabNavigator(
            self.frame,
            style_manager,
            subtabs_info,
            self._on_subtab_change
        )

        # Área de contenido para sub-pestañas
        self.subtab_content = style_manager.create_styled_frame(self.frame)
        self.subtab_content.pack(fill=tk.BOTH, expand=True)

        # Crear sub-pestañas
        self.subtabs = {
            "manual": ManualManagementSubTab(self.subtab_content, style_manager, data_manager),
            "bulk": BulkLoadSubTab(self.subtab_content, style_manager, data_manager)
        }

        # Mostrar sub-pestaña inicial
        self._show_subtab("manual")

    def _on_subtab_change(self, subtab_id):
        """
        Maneja el cambio de sub-pestaña

        Args:
            subtab_id: ID de la sub-pestaña seleccionada
        """
        self._show_subtab(subtab_id)

    def _show_subtab(self, subtab_id):
        """
        Muestra la sub-pestaña especificada

        Args:
            subtab_id: ID de la sub-pestaña a mostrar
        """
        # Ocultar todas las sub-pestañas
        for subtab in self.subtabs.values():
            subtab.get_frame().pack_forget()

        # Mostrar la sub-pestaña seleccionada
        if subtab_id in self.subtabs:
            self.subtabs[subtab_id].get_frame().pack(fill=tk.BOTH, expand=True)
            self.current_subtab = subtab_id

            # Callback cuando se muestra
            if hasattr(self.subtabs[subtab_id], 'on_show'):
                self.subtabs[subtab_id].on_show()

            # Actualizar navegador visual
            self.subtab_navigator.set_active_tab(subtab_id)

    def get_frame(self):
        """
        Retorna el frame de la pestaña
        """
        return self.frame

    def on_show(self):
        """
        Callback cuando se muestra la pestaña principal
        """
        # Notificar a la sub-pestaña actual
        if self.current_subtab in self.subtabs:
            if hasattr(self.subtabs[self.current_subtab], 'on_show'):
                self.subtabs[self.current_subtab].on_show()


class MessagesTab:
    """
    Pestaña de gestión de mensajes (sin cambios significativos)
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
    Pestaña de automatización (actualizada para usar contactos)
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
            "Controla la automatización del envío de mensajes a tus contactos"
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
        # Usar el método de compatibilidad que obtiene solo números
        numbers = self.data_manager.get_numbers_only()
        messages = self.data_manager.get_messages()

        if not numbers:
            show_error_message("No hay contactos configurados")
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
        # Usar contactos para mostrar estadísticas más precisas
        contacts_count = len(self.data_manager.get_contacts())
        messages_count = len(self.data_manager.get_messages())
        self.stats_display.update_stats(contacts_count, messages_count)

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

            # Callback especial para pestañas que lo necesiten
            if hasattr(self.tabs[tab_name], 'on_show'):
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