# gui_contacts_tab.py
"""
Pestaña de gestión de contactos para el Bot de WhatsApp
Este módulo implementa toda la funcionalidad relacionada con la administración de contactos
con layout horizontal compacto, donde la entrada de datos está a la izquierda y la lista de
contactos a la derecha. Incluye gestión manual individual y carga masiva desde archivos Excel
optimizada para pantallas de 1000x600px.
"""

import tkinter as tk
from gui_styles import StyleManager
from gui_components import (SubTabNavigator, ContactListManager,
                            ContactInputSection, ExcelUploadComponent, ContactEditDialog,
                            show_validation_error, show_success_message,
                            show_error_message, show_confirmation_dialog)


class ManualManagementSubTab:
    """
    Sub-pestaña para gestión manual de contactos individuales
    Implementa layout horizontal: entrada a la izquierda, lista a la derecha
    """

    def __init__(self, parent, style_manager: StyleManager, data_manager):
        """
        Inicializa la sub-pestaña de gestión manual con layout horizontal

        Args:
            parent: Widget padre donde se mostrará la sub-pestaña
            style_manager: Gestor de estilos para mantener consistencia visual
            data_manager: Gestor de datos para operaciones CRUD de contactos
        """
        self.style_manager = style_manager
        self.data_manager = data_manager

        # Frame principal de la sub-pestaña
        self.frame = style_manager.create_styled_frame(parent)

        # Crear layout horizontal
        self._create_horizontal_layout()

        # Cargar contactos existentes
        self._refresh_contacts()

    def _create_horizontal_layout(self):
        """
        Crea el layout horizontal principal: entrada | lista
        """
        # Frame principal horizontal con padding compacto
        main_container = self.style_manager.create_styled_frame(self.frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        # Columna izquierda: Entrada de contactos (40% del ancho)
        self.left_column = self.style_manager.create_styled_frame(main_container)
        self.left_column.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 8))
        self.left_column.configure(width=400)
        self.left_column.pack_propagate(False)

        # Columna derecha: Lista de contactos (60% del ancho)
        self.right_column = self.style_manager.create_styled_frame(main_container)
        self.right_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))

        # Crear componentes en cada columna
        self._create_input_section()
        self._create_list_section()

    def _create_input_section(self):
        """
        Crea la sección de entrada en la columna izquierda
        """
        self.input_section = ContactInputSection(
            self.left_column,
            self.style_manager,
            "Nuevo contacto:",
            self._add_contact
        )
        self.input_section.input_frame.pack_configure(padx=0, pady=(0, 12))

    def _create_list_section(self):
        """
        Crea la sección de lista en la columna derecha
        """
        self.list_manager = ContactListManager(
            self.right_column,
            self.style_manager,
            "Contactos guardados:",
            edit_callback=self._edit_contact,
            delete_callback=self._delete_contact,
            clear_all_callback=self._clear_all_contacts
        )
        self.list_manager.list_frame.pack_configure(padx=0, pady=(0, 12))

    def _add_contact(self):
        """
        Agrega un nuevo contacto al sistema
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
        Edita el contacto seleccionado en la lista
        """
        index, display_text = self.list_manager.get_selection()

        if index is None:
            show_validation_error("Por favor selecciona un contacto para editar")
            return

        contact_data = self.data_manager.get_contact_by_index(index)
        if not contact_data:
            show_error_message("Contacto no encontrado")
            return

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

        contact_name = display_text.split(" - ")[0] if " - " in display_text else "este contacto"

        if show_confirmation_dialog(f"¿Eliminar {contact_name}?"):
            if self.data_manager.remove_contact(index):
                self._refresh_contacts()
                show_success_message("Contacto eliminado correctamente")
            else:
                show_error_message("Error al eliminar contacto")

    def _clear_all_contacts(self):
        """
        Elimina todos los contactos después de confirmación
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
        Actualiza la lista visual de contactos
        """
        contacts = self.data_manager.get_contacts()
        self.list_manager.clear_and_populate(contacts)

    def get_frame(self):
        """
        Retorna el frame principal de la sub-pestaña
        """
        return self.frame

    def on_show(self):
        """
        Callback ejecutado cuando se muestra la sub-pestaña
        """
        self._refresh_contacts()


class BulkLoadSubTab:
    """
    Sub-pestaña para carga masiva de contactos desde archivos Excel
    Optimizada para layout horizontal compacto
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

        # Crear layout optimizado
        self._create_optimized_layout()

    def _create_optimized_layout(self):
        """
        Crea el layout optimizado para la carga masiva
        """
        # Container principal con padding reducido
        main_container = self.style_manager.create_styled_frame(self.frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        # Crear componente Excel optimizado
        self._create_excel_section(main_container)

    def _create_excel_section(self, parent):
        """
        Crea la sección de Excel optimizada

        Args:
            parent: Widget padre
        """
        # Usar el componente original pero sin duplicar botones
        self.excel_component = ExcelUploadComponent(
            parent,
            self.style_manager,
            self._import_contacts
        )

        # Modificar el mensaje de configuración de columnas
        self._update_column_instruction()

    def _update_column_instruction(self):
        """
        Actualiza las instrucciones de configuración de columnas para ser más concisas
        """
        try:
            # Buscar y actualizar el label de instrucciones
            for widget in self.excel_component.main_frame.winfo_children():
                for subwidget in widget.winfo_children():
                    if hasattr(subwidget, 'cget') and hasattr(subwidget, 'configure'):
                        try:
                            text = subwidget.cget('text')
                            if 'Especifica los nombres' in text:
                                subwidget.configure(text="Nombres de columnas (no importa mayúsculas):")
                                break
                        except:
                            continue
        except:
            pass

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

            # Mostrar resultado
            self._show_import_result(added_count, total_count)

        except Exception as e:
            show_error_message(f"Error durante la importación: {str(e)}")

    def _show_import_result(self, added_count, total_count):
        """
        Muestra el resultado de la importación

        Args:
            added_count: Número de contactos importados exitosamente
            total_count: Número total de contactos procesados
        """
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

    def get_frame(self):
        """
        Retorna el frame principal de la sub-pestaña
        """
        return self.frame

    def on_show(self):
        """
        Callback ejecutado cuando se muestra la sub-pestaña
        """
        pass


class NumbersTab:
    """
    Pestaña principal de gestión de contactos con layout horizontal compacto
    Coordina las sub-pestañas de gestión manual y carga masiva optimizadas para 1000x600px
    """

    def __init__(self, parent, style_manager: StyleManager, data_manager):
        """
        Inicializa la pestaña principal de contactos con layout compacto

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

        # Crear interfaz compacta
        self._create_compact_interface()

        # Mostrar sub-pestaña inicial
        self._show_subtab("manual")

    def _create_compact_interface(self):
        """
        Crea la interfaz compacta con header y navegación optimizada
        """
        # Header más compacto
        self._create_compact_header()

        # Navegación de sub-pestañas
        self._create_subtab_navigation()

        # Área de contenido
        self._create_subtab_content_area()

        # Sub-pestañas
        self._create_subtabs()

    def _create_compact_header(self):
        """
        Crea la cabecera compacta de la pestaña
        """
        # Container del header con padding reducido
        header_container = self.style_manager.create_styled_frame(self.frame)
        header_container.pack(fill=tk.X, padx=12, pady=(12, 8))

        # Título
        title_label = self.style_manager.create_styled_label(header_container, "Gestión de Contactos", "title")
        title_label.pack(anchor="w")

        # Descripción más concisa
        desc_label = self.style_manager.create_styled_label(
            header_container,
            "Administra contactos usando gestión manual o carga masiva",
            "secondary"
        )
        desc_label.pack(anchor="w", pady=(4, 0))

        # Línea separadora más sutil
        separator = self.style_manager.create_styled_frame(header_container, "accent")
        separator.configure(height=1)
        separator.pack(fill=tk.X, pady=(8, 0))

    def _create_subtab_navigation(self):
        """
        Crea el navegador de sub-pestañas compacto
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

        # Ajustar padding del navegador
        self.subtab_navigator.nav_frame.pack_configure(padx=12, pady=(0, 8))

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
        if subtab_id not in self.subtabs:
            return

        # Ocultar todas las sub-pestañas
        for subtab in self.subtabs.values():
            subtab.get_frame().pack_forget()

        # Mostrar la sub-pestaña seleccionada
        target_subtab = self.subtabs[subtab_id]
        target_subtab.get_frame().pack(fill=tk.BOTH, expand=True)

        # Actualizar estado
        self.current_subtab = subtab_id

        # Actualizar navegador visual
        self.subtab_navigator.set_active_tab(subtab_id)

        # Ejecutar callback si existe
        if hasattr(target_subtab, 'on_show'):
            target_subtab.on_show()

    def get_frame(self):
        """
        Retorna el frame principal de la pestaña
        """
        return self.frame

    def on_show(self):
        """
        Callback ejecutado cuando se muestra la pestaña principal
        """
        if self.current_subtab in self.subtabs:
            current_subtab = self.subtabs[self.current_subtab]
            if hasattr(current_subtab, 'on_show'):
                current_subtab.on_show()