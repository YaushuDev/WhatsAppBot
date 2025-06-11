# gui_contacts_tab.py
"""
Pestaña de gestión de contactos para el Bot de WhatsApp
Este módulo implementa toda la funcionalidad relacionada con la administración de contactos,
incluyendo gestión manual individual y carga masiva desde archivos Excel. Proporciona
una interfaz intuitiva con sub-pestañas para diferentes métodos de gestión de contactos.
"""

import tkinter as tk
from gui_styles import StyleManager
from gui_components import (TabHeader, SubTabNavigator, ContactListManager,
                            ContactInputSection, ExcelUploadComponent, ContactEditDialog,
                            show_validation_error, show_success_message,
                            show_error_message, show_confirmation_dialog)


class ManualManagementSubTab:
    """
    Sub-pestaña para gestión manual de contactos individuales
    Permite agregar, editar y eliminar contactos uno por uno de forma intuitiva
    """

    def __init__(self, parent, style_manager: StyleManager, data_manager):
        """
        Inicializa la sub-pestaña de gestión manual

        Args:
            parent: Widget padre donde se mostrará la sub-pestaña
            style_manager: Gestor de estilos para mantener consistencia visual
            data_manager: Gestor de datos para operaciones CRUD de contactos
        """
        self.style_manager = style_manager
        self.data_manager = data_manager

        # Frame principal de la sub-pestaña
        self.frame = style_manager.create_styled_frame(parent)

        # Crear componentes de la interfaz
        self._create_input_section()
        self._create_list_section()

        # Cargar contactos existentes
        self._refresh_contacts()

    def _create_input_section(self):
        """
        Crea la sección de entrada para nuevos contactos
        Incluye campos para nombre y número con validación
        """
        self.input_section = ContactInputSection(
            self.frame,
            self.style_manager,
            "Nuevo contacto:",
            self._add_contact
        )

    def _create_list_section(self):
        """
        Crea la sección de lista de contactos con botones de acción
        Permite visualizar, editar y eliminar contactos existentes
        """
        self.list_manager = ContactListManager(
            self.frame,
            self.style_manager,
            "Contactos guardados:",
            edit_callback=self._edit_contact,
            delete_callback=self._delete_contact,
            clear_all_callback=self._clear_all_contacts
        )

    def _add_contact(self):
        """
        Agrega un nuevo contacto al sistema
        Valida los datos ingresados y proporciona feedback al usuario
        """
        name, number = self.input_section.get_values()

        # Validar nombre
        if not name:
            show_validation_error("Por favor ingresa el nombre del contacto")
            self.input_section.focus_name()
            return

        # Validar número
        if not number:
            show_validation_error("Por favor ingresa el número de teléfono")
            return

        # Intentar agregar el contacto
        if self.data_manager.add_contact(name, number):
            self._on_contact_added_successfully(name)
        else:
            self._on_contact_add_failed()

    def _on_contact_added_successfully(self, name):
        """
        Maneja el flujo cuando un contacto se agrega exitosamente

        Args:
            name: Nombre del contacto agregado
        """
        self.input_section.clear_values()
        self.input_section.focus_name()
        self._refresh_contacts()
        show_success_message(f"Contacto '{name}' agregado correctamente")

    def _on_contact_add_failed(self):
        """
        Maneja el flujo cuando falla la adición de un contacto
        """
        show_error_message("El número ya existe o es inválido")

    def _edit_contact(self):
        """
        Edita el contacto seleccionado en la lista
        Abre un diálogo modal para modificar los datos del contacto
        """
        index, display_text = self.list_manager.get_selection()

        if index is None:
            show_validation_error("Por favor selecciona un contacto para editar")
            return

        # Obtener datos actuales del contacto
        contact_data = self.data_manager.get_contact_by_index(index)
        if not contact_data:
            show_error_message("Contacto no encontrado")
            return

        # Crear diálogo de edición
        self._show_edit_dialog(contact_data, index)

    def _show_edit_dialog(self, contact_data, index):
        """
        Muestra el diálogo de edición de contacto

        Args:
            contact_data: Datos actuales del contacto
            index: Índice del contacto en la lista
        """
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
        Elimina el contacto seleccionado después de confirmación
        """
        index, display_text = self.list_manager.get_selection()

        if index is None:
            show_validation_error("Por favor selecciona un contacto para eliminar")
            return

        # Extraer nombre del display text para mostrar en confirmación
        contact_name = self._extract_contact_name(display_text)

        if show_confirmation_dialog(f"¿Eliminar {contact_name}?"):
            self._perform_contact_deletion(index)

    def _extract_contact_name(self, display_text):
        """
        Extrae el nombre del contacto del texto mostrado en la lista

        Args:
            display_text: Texto completo mostrado en la lista

        Returns:
            str: Nombre del contacto o texto genérico
        """
        return display_text.split(" - ")[0] if " - " in display_text else "este contacto"

    def _perform_contact_deletion(self, index):
        """
        Ejecuta la eliminación del contacto

        Args:
            index: Índice del contacto a eliminar
        """
        if self.data_manager.remove_contact(index):
            self._refresh_contacts()
            show_success_message("Contacto eliminado correctamente")
        else:
            show_error_message("Error al eliminar contacto")

    def _clear_all_contacts(self):
        """
        Elimina todos los contactos después de confirmación
        Operación irreversible que requiere doble confirmación
        """
        contacts = self.data_manager.get_contacts()

        if not contacts:
            show_validation_error("No hay contactos para eliminar")
            return

        count = len(contacts)
        if show_confirmation_dialog(f"¿Eliminar TODOS los {count} contactos?\n\nEsta acción no se puede deshacer."):
            self._perform_bulk_deletion(count)

    def _perform_bulk_deletion(self, count):
        """
        Ejecuta la eliminación masiva de contactos

        Args:
            count: Número de contactos a eliminar (para mostrar en mensaje)
        """
        if self.data_manager.clear_all_contacts():
            self._refresh_contacts()
            show_success_message(f"Se eliminaron {count} contactos correctamente")
        else:
            show_error_message("Error al eliminar contactos")

    def _refresh_contacts(self):
        """
        Actualiza la lista visual de contactos
        Sincroniza la interfaz con los datos almacenados
        """
        contacts = self.data_manager.get_contacts()
        self.list_manager.clear_and_populate(contacts)

    def get_frame(self):
        """
        Retorna el frame principal de la sub-pestaña

        Returns:
            tk.Frame: Frame contenedor de todos los widgets
        """
        return self.frame

    def on_show(self):
        """
        Callback ejecutado cuando se muestra la sub-pestaña
        Actualiza la información mostrada
        """
        self._refresh_contacts()


class BulkLoadSubTab:
    """
    Sub-pestaña para carga masiva de contactos desde archivos Excel
    Permite importar grandes cantidades de contactos de forma eficiente
    """

    def __init__(self, parent, style_manager: StyleManager, data_manager):
        """
        Inicializa la sub-pestaña de carga masiva

        Args:
            parent: Widget padre donde se mostrará la sub-pestaña
            style_manager: Gestor de estilos para mantener consistencia visual
            data_manager: Gestor de datos para operaciones de importación
        """
        self.style_manager = style_manager
        self.data_manager = data_manager

        # Frame principal de la sub-pestaña
        self.frame = style_manager.create_styled_frame(parent)

        # Crear componentes de la interfaz
        self._create_excel_component()
        self._create_import_stats()

    def _create_excel_component(self):
        """
        Crea el componente principal de carga de Excel
        Incluye selección de archivo, configuración y vista previa
        """
        self.excel_component = ExcelUploadComponent(
            self.frame,
            self.style_manager,
            self._import_contacts
        )

    def _create_import_stats(self):
        """
        Crea la sección de estadísticas de importación
        Muestra información sobre contactos actuales y últimas importaciones
        """
        stats_frame = self.style_manager.create_styled_labelframe(
            self.frame,
            "📊 Estadísticas de Importación"
        )
        stats_frame.pack(fill=tk.X, padx=25, pady=(15, 0))

        content = self.style_manager.create_styled_frame(stats_frame)
        content.pack(fill=tk.X, padx=15, pady=12)

        # Contenedor para estadísticas en columnas
        self._create_stats_layout(content)

        # Actualizar estadísticas iniciales
        self._update_stats()

    def _create_stats_layout(self, parent):
        """
        Crea el layout de las estadísticas en columnas

        Args:
            parent: Widget padre para el layout de estadísticas
        """
        stats_container = self.style_manager.create_styled_frame(parent)
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

    def _import_contacts(self, contacts_data):
        """
        Importa los contactos desde los datos procesados del Excel

        Args:
            contacts_data: Lista de diccionarios con datos de contactos
        """
        if not contacts_data:
            show_validation_error("No hay datos para importar")
            return

        try:
            # Realizar importación masiva
            added_count, total_count = self.data_manager.add_contacts_bulk(contacts_data)

            # Actualizar estadísticas
            self._update_stats()

            # Mostrar resultado de la importación
            self._show_import_result(added_count, total_count)

            # Actualizar label de última importación
            self._update_last_import_label(added_count, total_count)

        except Exception as e:
            show_error_message(f"Error durante la importación: {str(e)}")

    def _show_import_result(self, added_count, total_count):
        """
        Muestra el resultado de la importación al usuario

        Args:
            added_count: Número de contactos importados exitosamente
            total_count: Número total de contactos procesados
        """
        if added_count == total_count:
            self._show_complete_success(added_count)
        elif added_count > 0:
            self._show_partial_success(added_count, total_count)
        else:
            self._show_import_failure(total_count)

    def _show_complete_success(self, added_count):
        """
        Muestra mensaje de éxito completo

        Args:
            added_count: Número de contactos importados
        """
        show_success_message(f"¡Importación exitosa!\n\nSe importaron {added_count} contactos correctamente")

    def _show_partial_success(self, added_count, total_count):
        """
        Muestra mensaje de éxito parcial

        Args:
            added_count: Número de contactos importados
            total_count: Número total de contactos procesados
        """
        duplicates = total_count - added_count
        show_success_message(
            f"Importación parcial completada:\n\n"
            f"✅ Importados: {added_count} contactos\n"
            f"⚠️ Omitidos: {duplicates} (duplicados o inválidos)"
        )

    def _show_import_failure(self, total_count):
        """
        Muestra mensaje de fallo en importación

        Args:
            total_count: Número total de contactos que se intentó procesar
        """
        show_error_message(
            f"No se pudo importar ningún contacto.\n"
            f"Todos los {total_count} contactos ya existen o son inválidos."
        )

    def _update_last_import_label(self, added_count, total_count):
        """
        Actualiza el label de última importación

        Args:
            added_count: Contactos importados exitosamente
            total_count: Total de contactos procesados
        """
        self.last_import_label.configure(
            text=f"📥 Última importación: {added_count}/{total_count}"
        )

    def _update_stats(self):
        """
        Actualiza las estadísticas mostradas en la interfaz
        """
        contacts_count = len(self.data_manager.get_contacts())
        self.current_contacts_label.configure(text=f"📱 Contactos actuales: {contacts_count}")

    def get_frame(self):
        """
        Retorna el frame principal de la sub-pestaña

        Returns:
            tk.Frame: Frame contenedor de todos los widgets
        """
        return self.frame

    def on_show(self):
        """
        Callback ejecutado cuando se muestra la sub-pestaña
        Actualiza las estadísticas mostradas
        """
        self._update_stats()


class NumbersTab:
    """
    Pestaña principal de gestión de contactos
    Coordina las sub-pestañas de gestión manual y carga masiva
    """

    def __init__(self, parent, style_manager: StyleManager, data_manager):
        """
        Inicializa la pestaña principal de contactos

        Args:
            parent: Widget padre donde se mostrará la pestaña
            style_manager: Gestor de estilos para mantener consistencia visual
            data_manager: Gestor de datos compartido con las sub-pestañas
        """
        self.style_manager = style_manager
        self.data_manager = data_manager
        self.current_subtab = "manual"

        # Frame principal de la pestaña
        self.frame = style_manager.create_styled_frame(parent)

        # Crear componentes de la interfaz
        self._create_header()
        self._create_subtab_navigation()
        self._create_subtab_content_area()
        self._create_subtabs()

        # Mostrar sub-pestaña inicial
        self._show_subtab("manual")

    def _create_header(self):
        """
        Crea la cabecera de la pestaña con título y descripción
        """
        TabHeader(
            self.frame,
            self.style_manager,
            "Gestión de Contactos",
            "Administra los contactos a los que se enviarán mensajes, usando gestión manual o carga masiva"
        )

    def _create_subtab_navigation(self):
        """
        Crea el navegador de sub-pestañas
        """
        subtabs_info = [
            ("manual", "Gestión Manual", "✏️"),
            ("bulk", "Carga Masiva", "📁")
        ]

        self.subtab_navigator = SubTabNavigator(
            self.frame,
            self.style_manager,
            subtabs_info,
            self._on_subtab_change
        )

    def _create_subtab_content_area(self):
        """
        Crea el área de contenido donde se mostrarán las sub-pestañas
        """
        self.subtab_content = self.style_manager.create_styled_frame(self.frame)
        self.subtab_content.pack(fill=tk.BOTH, expand=True)

    def _create_subtabs(self):
        """
        Crea las instancias de las sub-pestañas
        """
        self.subtabs = {
            "manual": ManualManagementSubTab(
                self.subtab_content,
                self.style_manager,
                self.data_manager
            ),
            "bulk": BulkLoadSubTab(
                self.subtab_content,
                self.style_manager,
                self.data_manager
            )
        }

    def _on_subtab_change(self, subtab_id):
        """
        Maneja el cambio de sub-pestaña

        Args:
            subtab_id: ID de la sub-pestaña seleccionada
        """
        self._show_subtab(subtab_id)

    def _show_subtab(self, subtab_id):
        """
        Muestra la sub-pestaña especificada y oculta las demás

        Args:
            subtab_id: ID de la sub-pestaña a mostrar
        """
        # Validar que la sub-pestaña existe
        if subtab_id not in self.subtabs:
            return

        # Ocultar todas las sub-pestañas
        self._hide_all_subtabs()

        # Mostrar la sub-pestaña seleccionada
        self._show_specific_subtab(subtab_id)

        # Actualizar estado
        self.current_subtab = subtab_id

        # Actualizar navegador visual
        self.subtab_navigator.set_active_tab(subtab_id)

    def _hide_all_subtabs(self):
        """
        Oculta todas las sub-pestañas
        """
        for subtab in self.subtabs.values():
            subtab.get_frame().pack_forget()

    def _show_specific_subtab(self, subtab_id):
        """
        Muestra una sub-pestaña específica

        Args:
            subtab_id: ID de la sub-pestaña a mostrar
        """
        target_subtab = self.subtabs[subtab_id]
        target_subtab.get_frame().pack(fill=tk.BOTH, expand=True)

        # Ejecutar callback de la sub-pestaña si existe
        if hasattr(target_subtab, 'on_show'):
            target_subtab.on_show()

    def get_frame(self):
        """
        Retorna el frame principal de la pestaña

        Returns:
            tk.Frame: Frame contenedor de toda la pestaña
        """
        return self.frame

    def on_show(self):
        """
        Callback ejecutado cuando se muestra la pestaña principal
        Notifica a la sub-pestaña actual para que actualice su contenido
        """
        if self.current_subtab in self.subtabs:
            current_subtab = self.subtabs[self.current_subtab]
            if hasattr(current_subtab, 'on_show'):
                current_subtab.on_show()