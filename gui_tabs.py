# gui_tabs.py
"""
Pestañas del Bot de WhatsApp con soporte completo para emoticones
Implementa la lógica específica de cada pestaña (contactos, mensajes, automatización)
utilizando los componentes reutilizables para mantener el código organizado y conciso.
Incluye soporte completo para mensajes con texto e imágenes, gestión de contactos
con funcionalidad manual y carga masiva desde archivos Excel, además de un menú
de emoticones integrado para una mejor experiencia de usuario.
"""

import tkinter as tk
from tkinter import scrolledtext, filedialog
import threading
import os
from PIL import Image, ImageTk
from gui_styles import StyleManager
from gui_components import (TabHeader, ListManager, InputSection, StatsDisplay,
                            ActivityLog, SubTabNavigator, ContactListManager,
                            ContactInputSection, ExcelUploadComponent, ContactEditDialog,
                            EmojiMenu, show_validation_error, show_success_message,
                            show_error_message, show_confirmation_dialog)


class MessageInputSection:
    """
    Sección especializada para entrada de mensajes con texto, imagen y emoticones
    """

    def __init__(self, parent, style_manager: StyleManager, button_callback=None):
        """
        Inicializa la sección de entrada de mensajes

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
            button_callback: Función del botón
        """
        self.style_manager = style_manager
        self.selected_image_path = None

        # Frame principal
        self.input_frame = style_manager.create_styled_labelframe(parent, "💬 Nuevo mensaje:")
        self.input_frame.pack(fill=tk.X, padx=25, pady=(0, 20))

        # Contenido interno
        content_frame = style_manager.create_styled_frame(self.input_frame)
        content_frame.pack(fill=tk.X, padx=15, pady=15)

        # Área de texto para el mensaje
        text_label = style_manager.create_styled_label(content_frame, "Texto del mensaje:", "normal")
        text_label.pack(anchor="w")

        self.text_widget = scrolledtext.ScrolledText(
            content_frame,
            height=4,
            font=style_manager.fonts["normal"],
            bg=style_manager.colors["bg_card"],
            fg=style_manager.colors["text_primary"],
            border=1,
            relief="solid",
            wrap=tk.WORD,
            highlightthickness=1,
            highlightcolor=style_manager.colors["accent"],
            highlightbackground=style_manager.colors["border"],
            insertbackground=style_manager.colors["text_primary"]
        )
        self.text_widget.pack(fill=tk.X, pady=(5, 15))

        # Menú de emoticones
        self._create_emoji_menu(content_frame)

        # Sección de imagen
        self._create_image_section(content_frame)

        # Botón agregar
        if button_callback:
            button = style_manager.create_styled_button(
                content_frame,
                "➕ Agregar Mensaje",
                button_callback,
                "accent"
            )
            button.pack(pady=(10, 0))

    def _create_emoji_menu(self, parent):
        """
        Crea el menú de emoticones integrado

        Args:
            parent: Widget padre
        """
        self.emoji_menu = EmojiMenu(parent, self.style_manager, self._insert_emoji)

    def _insert_emoji(self, emoji):
        """
        Inserta un emoji en la posición del cursor

        Args:
            emoji: Emoji a insertar
        """
        try:
            # Obtener posición actual del cursor
            cursor_pos = self.text_widget.index(tk.INSERT)

            # Insertar emoji en la posición del cursor
            self.text_widget.insert(cursor_pos, emoji)

            # Mantener el foco en el área de texto
            self.text_widget.focus_set()

        except Exception as e:
            print(f"Error insertando emoji: {e}")

    def _create_image_section(self, parent):
        """
        Crea la sección de manejo de imágenes
        """
        # Frame para imagen
        image_frame = self.style_manager.create_styled_frame(parent)
        image_frame.pack(fill=tk.X, pady=(0, 10))

        # Label y botón de imagen en la misma línea
        image_header = self.style_manager.create_styled_frame(image_frame)
        image_header.pack(fill=tk.X, pady=(0, 10))

        image_label = self.style_manager.create_styled_label(image_header, "Imagen (opcional):", "normal")
        image_label.pack(side=tk.LEFT)

        # Botones de imagen
        buttons_frame = self.style_manager.create_styled_frame(image_header)
        buttons_frame.pack(side=tk.RIGHT)

        self.select_image_btn = self.style_manager.create_styled_button(
            buttons_frame,
            "📁 Seleccionar",
            self._select_image,
            "normal"
        )
        self.select_image_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.clear_image_btn = self.style_manager.create_styled_button(
            buttons_frame,
            "🗑️ Quitar",
            self._clear_image,
            "error"
        )
        self.clear_image_btn.pack(side=tk.LEFT)
        self.clear_image_btn.configure(state="disabled")

        # Vista previa de imagen
        self.preview_frame = self.style_manager.create_styled_frame(image_frame, "card")
        self.preview_frame.configure(relief="solid", bd=1, height=120)
        self.preview_frame.pack(fill=tk.X)
        self.preview_frame.pack_propagate(False)

        # Label de estado de imagen
        self.image_status_label = self.style_manager.create_styled_label(
            self.preview_frame,
            "No hay imagen seleccionada",
            "secondary"
        )
        self.image_status_label.configure(bg=self.style_manager.colors["bg_card"])
        self.image_status_label.pack(expand=True)

    def _select_image(self):
        """
        Abre el diálogo para seleccionar imagen
        """
        file_types = [
            ("Imágenes", "*.jpg;*.jpeg;*.png;*.gif;*.bmp"),
            ("JPEG", "*.jpg;*.jpeg"),
            ("PNG", "*.png"),
            ("GIF", "*.gif"),
            ("Todos los archivos", "*.*")
        ]

        image_path = filedialog.askopenfilename(
            title="Seleccionar imagen para el mensaje",
            filetypes=file_types
        )

        if image_path:
            # Validar que sea una imagen
            if self._validate_image(image_path):
                self.selected_image_path = image_path
                self._update_image_preview()
                self.clear_image_btn.configure(state="normal")
            else:
                show_validation_error("El archivo seleccionado no es una imagen válida")

    def _clear_image(self):
        """
        Quita la imagen seleccionada
        """
        self.selected_image_path = None
        self._update_image_preview()
        self.clear_image_btn.configure(state="disabled")

    def _validate_image(self, image_path):
        """
        Valida que el archivo sea una imagen válida

        Args:
            image_path: Ruta de la imagen

        Returns:
            True si es válida
        """
        try:
            with Image.open(image_path) as img:
                img.verify()
            return True
        except Exception:
            return False

    def _update_image_preview(self):
        """
        Actualiza la vista previa de la imagen
        """
        # Limpiar preview actual
        for widget in self.preview_frame.winfo_children():
            widget.destroy()

        if self.selected_image_path and os.path.exists(self.selected_image_path):
            try:
                # Cargar y redimensionar imagen
                with Image.open(self.selected_image_path) as img:
                    # Calcular dimensiones manteniendo proporción
                    max_width, max_height = 200, 100
                    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

                    # Convertir para Tkinter
                    photo = ImageTk.PhotoImage(img)

                    # Mostrar imagen
                    image_label = tk.Label(
                        self.preview_frame,
                        image=photo,
                        bg=self.style_manager.colors["bg_card"]
                    )
                    image_label.image = photo  # Mantener referencia
                    image_label.pack(expand=True)

                    # Info de la imagen
                    filename = os.path.basename(self.selected_image_path)
                    info_label = self.style_manager.create_styled_label(
                        self.preview_frame,
                        f"📷 {filename}",
                        "small"
                    )
                    info_label.configure(bg=self.style_manager.colors["bg_card"])
                    info_label.pack()

            except Exception as e:
                self._show_no_image_message("Error al cargar la imagen")
        else:
            self._show_no_image_message("No hay imagen seleccionada")

    def _show_no_image_message(self, message="No hay imagen seleccionada"):
        """
        Muestra mensaje cuando no hay imagen

        Args:
            message: Mensaje a mostrar
        """
        self.image_status_label = self.style_manager.create_styled_label(
            self.preview_frame,
            message,
            "secondary"
        )
        self.image_status_label.configure(bg=self.style_manager.colors["bg_card"])
        self.image_status_label.pack(expand=True)

    def get_values(self):
        """
        Obtiene los valores de texto e imagen

        Returns:
            Tupla (texto, ruta_imagen)
        """
        text = self.text_widget.get(1.0, tk.END).strip()
        return text, self.selected_image_path

    def clear_values(self):
        """
        Limpia ambos campos
        """
        self.text_widget.delete(1.0, tk.END)
        self._clear_image()

    def set_values(self, text, image_path=None):
        """
        Establece valores en los campos

        Args:
            text: Texto del mensaje
            image_path: Ruta de la imagen (opcional)
        """
        self.clear_values()
        self.text_widget.insert(1.0, text)
        if image_path and os.path.exists(image_path):
            self.selected_image_path = image_path
            self._update_image_preview()
            self.clear_image_btn.configure(state="normal")

    def focus_text(self):
        """
        Pone el foco en el área de texto
        """
        self.text_widget.focus_set()


class MessageEditDialog:
    """
    Diálogo para editar mensajes con texto, imagen y emoticones
    """

    def __init__(self, parent, style_manager: StyleManager, message_data, data_manager, callback):
        """
        Inicializa el diálogo de edición

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
            message_data: Datos del mensaje {'texto': str, 'imagen': str}
            data_manager: Gestor de datos para obtener rutas de imágenes
            callback: Función callback con los nuevos datos
        """
        self.style_manager = style_manager
        self.data_manager = data_manager
        self.callback = callback
        self.result = None
        self.selected_image_path = None
        self.original_image_filename = message_data.get('imagen')

        # Crear ventana modal
        self.dialog = tk.Toplevel(parent)
        self.style_manager.configure_window(
            self.dialog,
            "Editar Mensaje",
            "600x700"
        )
        self.dialog.grab_set()
        self.dialog.transient(parent)

        # Centrar la ventana
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (700 // 2)
        self.dialog.geometry(f"600x700+{x}+{y}")

        self._create_content(message_data)

    def _create_content(self, message_data):
        """
        Crea el contenido del diálogo

        Args:
            message_data: Datos del mensaje
        """
        # Frame principal
        main_frame = self.style_manager.create_styled_frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Título
        title_label = self.style_manager.create_styled_label(
            main_frame,
            "Editar Mensaje",
            "heading"
        )
        title_label.pack(pady=(0, 20))

        # Campo texto
        text_label = self.style_manager.create_styled_label(main_frame, "Texto del mensaje:", "normal")
        text_label.pack(anchor="w")

        self.text_widget = scrolledtext.ScrolledText(
            main_frame,
            height=6,
            font=self.style_manager.fonts["normal"],
            bg=self.style_manager.colors["bg_card"],
            fg=self.style_manager.colors["text_primary"],
            border=1,
            relief="solid",
            wrap=tk.WORD,
            highlightthickness=1,
            highlightcolor=self.style_manager.colors["accent"],
            highlightbackground=self.style_manager.colors["border"],
            insertbackground=self.style_manager.colors["text_primary"]
        )
        self.text_widget.pack(fill=tk.X, pady=(5, 15))
        self.text_widget.insert(1.0, message_data.get('texto', ''))

        # Menú de emoticones en el diálogo
        self._create_emoji_menu(main_frame)

        # Sección de imagen
        self._create_image_section(main_frame, message_data)

        # Frame para botones
        buttons_frame = self.style_manager.create_styled_frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(20, 0))

        # Botón guardar
        save_btn = self.style_manager.create_styled_button(
            buttons_frame,
            "💾 Guardar",
            self._save_changes,
            "success"
        )
        save_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Botón cancelar
        cancel_btn = self.style_manager.create_styled_button(
            buttons_frame,
            "❌ Cancelar",
            self._cancel,
            "error"
        )
        cancel_btn.pack(side=tk.LEFT)

        # Configurar eventos
        self.dialog.bind("<Escape>", lambda e: self._cancel())

        # Foco inicial
        self.text_widget.focus_set()

    def _create_emoji_menu(self, parent):
        """
        Crea el menú de emoticones en el diálogo

        Args:
            parent: Widget padre
        """
        self.emoji_menu = EmojiMenu(parent, self.style_manager, self._insert_emoji)

    def _insert_emoji(self, emoji):
        """
        Inserta un emoji en la posición del cursor

        Args:
            emoji: Emoji a insertar
        """
        try:
            # Obtener posición actual del cursor
            cursor_pos = self.text_widget.index(tk.INSERT)

            # Insertar emoji en la posición del cursor
            self.text_widget.insert(cursor_pos, emoji)

            # Mantener el foco en el área de texto
            self.text_widget.focus_set()

        except Exception as e:
            print(f"Error insertando emoji: {e}")

    def _create_image_section(self, parent, message_data):
        """
        Crea la sección de manejo de imágenes

        Args:
            parent: Widget padre
            message_data: Datos del mensaje
        """
        # Label de imagen
        image_label = self.style_manager.create_styled_label(parent, "Imagen:", "normal")
        image_label.pack(anchor="w")

        # Botones de imagen
        buttons_frame = self.style_manager.create_styled_frame(parent)
        buttons_frame.pack(fill=tk.X, pady=(5, 10))

        self.select_image_btn = self.style_manager.create_styled_button(
            buttons_frame,
            "📁 Cambiar imagen",
            self._select_image,
            "normal"
        )
        self.select_image_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.clear_image_btn = self.style_manager.create_styled_button(
            buttons_frame,
            "🗑️ Quitar imagen",
            self._clear_image,
            "error"
        )
        self.clear_image_btn.pack(side=tk.LEFT)

        # Vista previa de imagen
        self.preview_frame = self.style_manager.create_styled_frame(parent, "card")
        self.preview_frame.configure(relief="solid", bd=1, height=150)
        self.preview_frame.pack(fill=tk.X, pady=(0, 10))
        self.preview_frame.pack_propagate(False)

        # Cargar imagen actual si existe
        if message_data.get('imagen'):
            current_image_path = self.data_manager.get_image_path(message_data['imagen'])
            if current_image_path:
                self.selected_image_path = current_image_path
                self.clear_image_btn.configure(state="normal")

        self._update_image_preview()

    def _select_image(self):
        """
        Abre el diálogo para seleccionar imagen
        """
        file_types = [
            ("Imágenes", "*.jpg;*.jpeg;*.png;*.gif;*.bmp"),
            ("JPEG", "*.jpg;*.jpeg"),
            ("PNG", "*.png"),
            ("GIF", "*.gif"),
            ("Todos los archivos", "*.*")
        ]

        image_path = filedialog.askopenfilename(
            title="Seleccionar nueva imagen",
            filetypes=file_types
        )

        if image_path:
            if self._validate_image(image_path):
                self.selected_image_path = image_path
                self._update_image_preview()
                self.clear_image_btn.configure(state="normal")
            else:
                show_error_message("El archivo seleccionado no es una imagen válida")

    def _clear_image(self):
        """
        Quita la imagen seleccionada
        """
        self.selected_image_path = None
        self._update_image_preview()
        self.clear_image_btn.configure(state="disabled")

    def _validate_image(self, image_path):
        """
        Valida que el archivo sea una imagen válida
        """
        try:
            with Image.open(image_path) as img:
                img.verify()
            return True
        except Exception:
            return False

    def _update_image_preview(self):
        """
        Actualiza la vista previa de la imagen
        """
        # Limpiar preview actual
        for widget in self.preview_frame.winfo_children():
            widget.destroy()

        if self.selected_image_path and os.path.exists(self.selected_image_path):
            try:
                # Cargar y redimensionar imagen
                with Image.open(self.selected_image_path) as img:
                    # Calcular dimensiones manteniendo proporción
                    max_width, max_height = 250, 130
                    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

                    # Convertir para Tkinter
                    photo = ImageTk.PhotoImage(img)

                    # Mostrar imagen
                    image_label = tk.Label(
                        self.preview_frame,
                        image=photo,
                        bg=self.style_manager.colors["bg_card"]
                    )
                    image_label.image = photo  # Mantener referencia
                    image_label.pack(expand=True)

                    # Info de la imagen
                    filename = os.path.basename(self.selected_image_path)
                    info_label = self.style_manager.create_styled_label(
                        self.preview_frame,
                        f"📷 {filename}",
                        "small"
                    )
                    info_label.configure(bg=self.style_manager.colors["bg_card"])
                    info_label.pack()

            except Exception as e:
                self._show_no_image_message("Error al cargar la imagen")
        else:
            self._show_no_image_message("Sin imagen")

    def _show_no_image_message(self, message="Sin imagen"):
        """
        Muestra mensaje cuando no hay imagen
        """
        status_label = self.style_manager.create_styled_label(
            self.preview_frame,
            message,
            "secondary"
        )
        status_label.configure(bg=self.style_manager.colors["bg_card"])
        status_label.pack(expand=True)

    def _save_changes(self):
        """
        Guarda los cambios y cierra el diálogo
        """
        text = self.text_widget.get(1.0, tk.END).strip()

        if not text:
            show_validation_error("El texto del mensaje es obligatorio")
            return

        # Determinar cambio de imagen
        new_image_path = None
        if self.selected_image_path != self.data_manager.get_image_path(self.original_image_filename):
            new_image_path = self.selected_image_path

        self.result = {
            'texto': text,
            'nueva_imagen': new_image_path
        }

        if self.callback:
            self.callback(self.result)
        self.dialog.destroy()

    def _cancel(self):
        """
        Cancela la edición y cierra el diálogo
        """
        self.result = None
        self.dialog.destroy()


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

        # Estadísticas de importación con mejor espaciado
        self._create_import_stats()

    def _create_import_stats(self):
        """
        Crea la sección de estadísticas de importación con espaciado optimizado
        """
        stats_frame = self.style_manager.create_styled_labelframe(
            self.frame,
            "📊 Estadísticas de Importación"
        )
        stats_frame.pack(fill=tk.X, padx=25, pady=(15, 0))

        content = self.style_manager.create_styled_frame(stats_frame)
        content.pack(fill=tk.X, padx=15, pady=12)

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
    Pestaña principal de gestión de contactos con sub-pestañas compactas
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

        # Navegador de sub-pestañas compacto
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
    Pestaña de gestión de mensajes con soporte para texto, imágenes y emoticones
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
            "Crea mensajes con texto e imágenes que el bot enviará aleatoriamente. Usa el menú de emoticones para hacer tus mensajes más expresivos 😊🎉"
        )

        # Sección de entrada para mensajes con emoticones
        self.input_section = MessageInputSection(
            self.frame,
            style_manager,
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
        Agrega un mensaje con texto e imagen opcional
        """
        text, image_path = self.input_section.get_values()

        if not text:
            show_validation_error("Por favor ingresa el texto del mensaje")
            self.input_section.focus_text()
            return

        if self.data_manager.add_message(text, image_path):
            self.input_section.clear_values()
            self.input_section.focus_text()
            self._refresh_messages()

            if image_path:
                show_success_message("Mensaje con imagen agregado correctamente")
            else:
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
        message_data = self.data_manager.get_message_by_index(index)
        if not message_data:
            show_error_message("Mensaje no encontrado")
            return

        # Crear y mostrar diálogo de edición
        def on_edit_complete(new_data):
            if new_data:
                success = self.data_manager.update_message(
                    index,
                    new_data['texto'],
                    new_data.get('nueva_imagen')
                )
                if success:
                    self._refresh_messages()
                    show_success_message("Mensaje actualizado correctamente")
                else:
                    show_error_message("Error al actualizar el mensaje")

        MessageEditDialog(
            self.frame.winfo_toplevel(),
            self.style_manager,
            message_data,
            self.data_manager,
            on_edit_complete
        )

    def _delete_message(self):
        """
        Elimina el mensaje seleccionado
        """
        index, display_text = self.list_manager.get_selection()

        if index is None:
            show_validation_error("Por favor selecciona un mensaje para eliminar")
            return

        if show_confirmation_dialog(
                "¿Eliminar el mensaje seleccionado?\n\nSi tiene imagen asociada, también se eliminará."):
            if self.data_manager.remove_message(index):
                self._refresh_messages()
                show_success_message("Mensaje eliminado correctamente")

    def _refresh_messages(self):
        """
        Actualiza la lista de mensajes mostrando indicador de imagen y emoticones
        """
        messages = self.data_manager.get_messages()
        display_messages = []

        for i, message in enumerate(messages):
            text = message.get("texto", "")
            has_image = message.get("imagen") is not None

            # Mostrar solo las primeras 40 caracteres para dejar espacio a los indicadores
            display_text = text[:40] + "..." if len(text) > 40 else text

            # Agregar indicadores
            indicators = ""
            if has_image:
                indicators += " 📷"

            # Detectar si hay emoticones en el texto
            import re
            emoji_pattern = re.compile(
                "["
                "\U0001F600-\U0001F64F"  # emoticones faciales
                "\U0001F300-\U0001F5FF"  # símbolos & pictogramas
                "\U0001F680-\U0001F6FF"  # transporte & símbolos de mapa
                "\U0001F1E0-\U0001F1FF"  # banderas (iOS)
                "\U00002500-\U00002BEF"  # símbolos varios
                "\U00002702-\U000027B0"
                "\U000024C2-\U0001F251"
                "\u2640-\u2642"
                "\u2600-\u2B55"
                "\u200d"
                "\u23cf"
                "\u23e9"
                "\u231a"
                "\ufe0f"  # variaciones de emoji
                "\u3030"
                "]+", flags=re.UNICODE)

            if emoji_pattern.search(text):
                indicators += " 😀"

            # Número del mensaje
            display_messages.append(f"{i + 1}. {display_text}{indicators}")

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
            "Controla la automatización del envío de mensajes a tus contactos con soporte completo para emoticones"
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