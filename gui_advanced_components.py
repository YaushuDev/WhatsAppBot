# gui_advanced_components.py
"""
Componentes avanzados y especializados para el Bot de WhatsApp
Este módulo contiene componentes especializados para funcionalidades específicas:
gestión avanzada de contactos con edición, importación masiva desde Excel,
y otros componentes complejos que requieren lógica de negocio especializada.
"""

import tkinter as tk
from tkinter import filedialog, ttk
import os
from typing import List, Dict, Any, Optional, Callable
from gui_styles import StyleManager
from gui_base_components import show_validation_error, show_success_message, show_error_message


class ContactListManager:
    """
    Componente especializado para gestión de lista de contactos
    """

    def __init__(self, parent, style_manager: StyleManager, title,
                 edit_callback=None, delete_callback=None, clear_all_callback=None):
        """
        Inicializa el gestor de lista de contactos

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
            title: Título de la lista
            edit_callback: Función para editar contactos
            delete_callback: Función para eliminar contacto
            clear_all_callback: Función para eliminar todos
        """
        self.style_manager = style_manager
        self.edit_callback = edit_callback
        self.delete_callback = delete_callback
        self.clear_all_callback = clear_all_callback

        # Frame principal
        self.list_frame = style_manager.create_styled_labelframe(parent, title)
        self.list_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=(0, 20))

        # Contenido interno
        content_frame = style_manager.create_styled_frame(self.list_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Frame para listbox con scrollbar
        listbox_frame = style_manager.create_styled_frame(content_frame, "card")
        listbox_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        listbox_frame.configure(relief="solid", bd=1)

        # Listbox
        self.listbox = style_manager.create_styled_listbox(listbox_frame, height=10)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Scrollbar
        scrollbar = tk.Scrollbar(listbox_frame, orient="vertical")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 2), pady=2)
        scrollbar.configure(
            bg=style_manager.colors["bg_accent"],
            troughcolor=style_manager.colors["bg_card"],
            borderwidth=0,
            highlightthickness=0
        )

        # Conectar scrollbar
        self.listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.listbox.yview)

        # Frame para botones
        self.buttons_frame = style_manager.create_styled_frame(content_frame)
        self.buttons_frame.pack(fill=tk.X)

        self._create_buttons()

    def _create_buttons(self):
        """
        Crea los botones de acción
        """
        # Botón editar
        if self.edit_callback:
            edit_btn = self.style_manager.create_styled_button(
                self.buttons_frame,
                "✏️ Editar",
                self.edit_callback,
                "warning"
            )
            edit_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Botón eliminar
        if self.delete_callback:
            delete_btn = self.style_manager.create_styled_button(
                self.buttons_frame,
                "🗑️ Eliminar",
                self.delete_callback,
                "error"
            )
            delete_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Botón eliminar todos
        if self.clear_all_callback:
            clear_all_btn = self.style_manager.create_styled_button(
                self.buttons_frame,
                "🗑️ Eliminar Todos",
                self.clear_all_callback,
                "error"
            )
            clear_all_btn.pack(side=tk.RIGHT)

    def get_selection(self):
        """
        Obtiene el elemento seleccionado

        Returns:
            Tupla (índice, valor) o (None, None) si no hay selección
        """
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            value = self.listbox.get(index)
            return index, value
        return None, None

    def clear_and_populate(self, contacts):
        """
        Limpia la lista y la puebla con contactos

        Args:
            contacts: Lista de contactos (dicts con 'nombre' y 'numero')
        """
        self.listbox.delete(0, tk.END)
        for contact in contacts:
            if isinstance(contact, dict):
                display_text = f"{contact.get('nombre', 'Sin nombre')} - {contact.get('numero', 'Sin número')}"
            else:
                display_text = str(contact)
            self.listbox.insert(tk.END, display_text)


class ContactInputSection:
    """
    Sección de entrada para contactos (nombre + número)
    """

    def __init__(self, parent, style_manager: StyleManager, label_text, button_callback=None):
        """
        Inicializa la sección de entrada de contactos

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
            label_text: Texto de la etiqueta
            button_callback: Función del botón
        """
        self.style_manager = style_manager

        # Frame principal
        self.input_frame = style_manager.create_styled_labelframe(parent, label_text)
        self.input_frame.pack(fill=tk.X, padx=25, pady=(0, 20))

        # Contenido interno
        content_frame = style_manager.create_styled_frame(self.input_frame)
        content_frame.pack(fill=tk.X, padx=15, pady=15)

        # Frame para los campos
        fields_frame = style_manager.create_styled_frame(content_frame)
        fields_frame.pack(fill=tk.X, pady=(0, 15))

        # Campo nombre
        name_label = style_manager.create_styled_label(fields_frame, "Nombre:", "normal")
        name_label.pack(anchor="w")

        self.name_entry = style_manager.create_styled_entry(fields_frame)
        self.name_entry.pack(fill=tk.X, pady=(5, 10))

        # Campo número
        number_label = style_manager.create_styled_label(fields_frame, "Número:", "normal")
        number_label.pack(anchor="w")

        self.number_entry = style_manager.create_styled_entry(fields_frame)
        self.number_entry.pack(fill=tk.X, pady=(5, 0))

        # Botón
        if button_callback:
            button = style_manager.create_styled_button(
                content_frame,
                "➕ Agregar Contacto",
                button_callback,
                "accent"
            )
            button.pack()

            # Bind Enter key en ambos campos
            self.name_entry.bind("<Return>", lambda e: button_callback())
            self.number_entry.bind("<Return>", lambda e: button_callback())

    def get_values(self):
        """
        Obtiene los valores de nombre y número

        Returns:
            Tupla (nombre, numero)
        """
        return self.name_entry.get().strip(), self.number_entry.get().strip()

    def clear_values(self):
        """
        Limpia ambos campos
        """
        self.name_entry.delete(0, tk.END)
        self.number_entry.delete(0, tk.END)

    def set_values(self, name, number):
        """
        Establece valores en los campos

        Args:
            name: Nombre del contacto
            number: Número del contacto
        """
        self.clear_values()
        self.name_entry.insert(0, name)
        self.number_entry.insert(0, number)

    def focus_name(self):
        """
        Pone el foco en el campo de nombre
        """
        self.name_entry.focus_set()


class ContactEditDialog:
    """
    Diálogo para editar contactos
    """

    def __init__(self, parent, style_manager: StyleManager, contact_data, callback):
        """
        Inicializa el diálogo de edición

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
            contact_data: Datos del contacto {'nombre': str, 'numero': str}
            callback: Función callback con los nuevos datos
        """
        self.style_manager = style_manager
        self.callback = callback
        self.result = None

        # Crear ventana modal
        self.dialog = tk.Toplevel(parent)
        self.style_manager.configure_window(
            self.dialog,
            "Editar Contacto",
            "400x300"
        )
        self.dialog.grab_set()
        self.dialog.transient(parent)

        # Centrar la ventana
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (300 // 2)
        self.dialog.geometry(f"400x300+{x}+{y}")

        self._create_content(contact_data)

    def _create_content(self, contact_data):
        """
        Crea el contenido del diálogo

        Args:
            contact_data: Datos del contacto
        """
        # Frame principal
        main_frame = self.style_manager.create_styled_frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Título
        title_label = self.style_manager.create_styled_label(
            main_frame,
            "Editar Contacto",
            "heading"
        )
        title_label.pack(pady=(0, 20))

        # Campo nombre
        name_label = self.style_manager.create_styled_label(main_frame, "Nombre:", "normal")
        name_label.pack(anchor="w")

        self.name_entry = self.style_manager.create_styled_entry(main_frame)
        self.name_entry.pack(fill=tk.X, pady=(5, 15))
        self.name_entry.insert(0, contact_data.get('nombre', ''))

        # Campo número
        number_label = self.style_manager.create_styled_label(main_frame, "Número:", "normal")
        number_label.pack(anchor="w")

        self.number_entry = self.style_manager.create_styled_entry(main_frame)
        self.number_entry.pack(fill=tk.X, pady=(5, 20))
        self.number_entry.insert(0, contact_data.get('numero', ''))

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
        self.name_entry.bind("<Return>", lambda e: self._save_changes())
        self.number_entry.bind("<Return>", lambda e: self._save_changes())
        self.dialog.bind("<Escape>", lambda e: self._cancel())

        # Foco inicial
        self.name_entry.focus_set()
        self.name_entry.select_range(0, tk.END)

    def _save_changes(self):
        """
        Guarda los cambios y cierra el diálogo
        """
        name = self.name_entry.get().strip()
        number = self.number_entry.get().strip()

        if not name or not number:
            show_validation_error("Ambos campos son obligatorios")
            return

        self.result = {'nombre': name, 'numero': number}
        if self.callback:
            self.callback(self.result)
        self.dialog.destroy()

    def _cancel(self):
        """
        Cancela la edición y cierra el diálogo
        """
        self.result = None
        self.dialog.destroy()


class ExcelUploadComponent:
    """
    Componente para carga masiva desde Excel con vista previa
    """

    def __init__(self, parent, style_manager: StyleManager, upload_callback=None):
        """
        Inicializa el componente de carga Excel

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
            upload_callback: Función callback para procesar datos
        """
        self.style_manager = style_manager
        self.upload_callback = upload_callback
        self.file_path = None
        self.preview_data = []

        # Frame principal
        self.main_frame = style_manager.create_styled_frame(parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=(0, 25))

        self._create_file_section()
        self._create_columns_section()
        self._create_preview_section()
        self._create_action_buttons()

    def _create_file_section(self):
        """
        Crea la sección de selección de archivo
        """
        file_frame = self.style_manager.create_styled_labelframe(self.main_frame, "📁 Seleccionar Archivo Excel")
        file_frame.pack(fill=tk.X, pady=(0, 15))

        content = self.style_manager.create_styled_frame(file_frame)
        content.pack(fill=tk.X, padx=15, pady=15)

        # Botón seleccionar archivo
        select_btn = self.style_manager.create_styled_button(
            content,
            "📂 Seleccionar Archivo Excel",
            self._select_file,
            "accent"
        )
        select_btn.pack(side=tk.LEFT, padx=(0, 15))

        # Label del archivo seleccionado
        self.file_label = self.style_manager.create_styled_label(
            content,
            "Ningún archivo seleccionado",
            "secondary"
        )
        self.file_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _create_columns_section(self):
        """
        Crea la sección de configuración de columnas
        """
        columns_frame = self.style_manager.create_styled_labelframe(self.main_frame, "🔧 Configurar Columnas")
        columns_frame.pack(fill=tk.X, pady=(0, 15))

        content = self.style_manager.create_styled_frame(columns_frame)
        content.pack(fill=tk.X, padx=15, pady=15)

        # Instrucciones
        instruction = self.style_manager.create_styled_label(
            content,
            "Especifica los nombres de las columnas a buscar (no importa mayúsculas/minúsculas):",
            "secondary"
        )
        instruction.pack(anchor="w", pady=(0, 10))

        # Frame para los campos
        fields_frame = self.style_manager.create_styled_frame(content)
        fields_frame.pack(fill=tk.X)

        # Campo columna nombre
        name_frame = self.style_manager.create_styled_frame(fields_frame)
        name_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 15))

        name_label = self.style_manager.create_styled_label(name_frame, "Columna de Nombres:", "normal")
        name_label.pack(anchor="w")

        self.name_column_entry = self.style_manager.create_styled_entry(name_frame)
        self.name_column_entry.pack(fill=tk.X, pady=(5, 0))
        self.name_column_entry.insert(0, "nombre")

        # Campo columna número
        number_frame = self.style_manager.create_styled_frame(fields_frame)
        number_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        number_label = self.style_manager.create_styled_label(number_frame, "Columna de Números:", "normal")
        number_label.pack(anchor="w")

        self.number_column_entry = self.style_manager.create_styled_entry(number_frame)
        self.number_column_entry.pack(fill=tk.X, pady=(5, 0))
        self.number_column_entry.insert(0, "numero")

    def _create_preview_section(self):
        """
        Crea la sección de vista previa con tema oscuro correcto
        """
        preview_frame = self.style_manager.create_styled_labelframe(self.main_frame, "👁️ Vista Previa")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        content = self.style_manager.create_styled_frame(preview_frame)
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Configurar estilo del Treeview para tema oscuro
        self._configure_treeview_style()

        # Frame contenedor para la tabla con fondo del tema
        tree_frame = self.style_manager.create_styled_frame(content, "card")
        tree_frame.pack(fill=tk.BOTH, expand=True)
        tree_frame.configure(relief="solid", bd=1)

        # Treeview con configuración de tema oscuro
        self.preview_tree = ttk.Treeview(
            tree_frame,
            columns=('nombre', 'numero'),
            show='headings',
            height=8,
            style="Dark.Treeview"
        )

        # Configurar headers
        self.preview_tree.heading('nombre', text='Nombre')
        self.preview_tree.heading('numero', text='Número')

        # Ajustar ancho de columnas para evitar scroll horizontal
        self.preview_tree.column('nombre', width=300, minwidth=200)
        self.preview_tree.column('numero', width=200, minwidth=150)

        # Solo scrollbar vertical
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.preview_tree.yview)
        self.preview_tree.configure(yscrollcommand=v_scrollbar.set)

        # Pack elements - sin scrollbar horizontal
        self.preview_tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        v_scrollbar.pack(side="right", fill="y", pady=5)

        # Label de estadísticas
        self.stats_label = self.style_manager.create_styled_label(
            content,
            "Selecciona un archivo para ver la vista previa",
            "secondary"
        )
        self.stats_label.pack(pady=(10, 0))

    def _configure_treeview_style(self):
        """
        Configura el estilo del Treeview para que use el tema oscuro
        """
        style = ttk.Style()

        # Configurar estilo personalizado para Treeview
        style.theme_use('clam')  # Usar tema base clam

        # Configurar colores del Treeview
        style.configure("Dark.Treeview",
                        background=self.style_manager.colors["bg_card"],
                        foreground=self.style_manager.colors["text_primary"],
                        fieldbackground=self.style_manager.colors["bg_card"],
                        borderwidth=0,
                        relief="flat")

        # Configurar headers
        style.configure("Dark.Treeview.Heading",
                        background=self.style_manager.colors["bg_accent"],
                        foreground=self.style_manager.colors["text_primary"],
                        borderwidth=1,
                        relief="solid")

        # Configurar selección
        style.map("Dark.Treeview",
                  background=[('selected', self.style_manager.colors["accent"])],
                  foreground=[('selected', self.style_manager.colors["text_primary"])])

    def _create_action_buttons(self):
        """
        Crea los botones de acción
        """
        buttons_frame = self.style_manager.create_styled_frame(self.main_frame)
        buttons_frame.pack(fill=tk.X)

        # Botón procesar
        process_btn = self.style_manager.create_styled_button(
            buttons_frame,
            "🔄 Procesar Archivo",
            self._process_file,
            "warning"
        )
        process_btn.pack(side=tk.LEFT, padx=(0, 15))

        # Botón importar
        self.import_btn = self.style_manager.create_styled_button(
            buttons_frame,
            "📥 Importar Contactos",
            self._import_contacts,
            "success"
        )
        self.import_btn.pack(side=tk.LEFT)
        self.import_btn.configure(state="disabled")

    def _select_file(self):
        """
        Abre el diálogo de selección de archivo
        """
        file_types = [
            ("Archivos Excel", "*.xlsx;*.xls"),
            ("Excel 2007-365", "*.xlsx"),
            ("Excel 97-2003", "*.xls"),
            ("Todos los archivos", "*.*")
        ]

        self.file_path = filedialog.askopenfilename(
            title="Seleccionar archivo Excel",
            filetypes=file_types
        )

        if self.file_path:
            filename = os.path.basename(self.file_path)
            self.file_label.configure(text=f"📄 {filename}")
            self._clear_preview()
        else:
            self.file_label.configure(text="Ningún archivo seleccionado")

    def _process_file(self):
        """
        Procesa el archivo Excel y muestra vista previa
        """
        if not self.file_path:
            show_validation_error("Por favor selecciona un archivo Excel")
            return

        name_col = self.name_column_entry.get().strip()
        number_col = self.number_column_entry.get().strip()

        if not name_col or not number_col:
            show_validation_error("Por favor especifica ambas columnas")
            return

        try:
            self._process_excel_file(self.file_path, name_col, number_col)
        except Exception as e:
            show_error_message(f"Error al procesar archivo: {str(e)}")

    def _process_excel_file(self, file_path, name_col, number_col):
        """
        Procesa el archivo Excel

        Args:
            file_path: Ruta del archivo
            name_col: Nombre de la columna de nombres
            number_col: Nombre de la columna de números
        """
        try:
            import pandas as pd

            # Leer archivo Excel
            df = pd.read_excel(file_path)

            # Buscar columnas (case insensitive)
            columns = df.columns.str.lower()
            name_col_lower = name_col.lower()
            number_col_lower = number_col.lower()

            name_column = None
            number_column = None

            # Buscar columna de nombres
            for col in df.columns:
                if col.lower() == name_col_lower or name_col_lower in col.lower():
                    name_column = col
                    break

            # Buscar columna de números
            for col in df.columns:
                if col.lower() == number_col_lower or number_col_lower in col.lower():
                    number_column = col
                    break

            if not name_column or not number_column:
                available_cols = ", ".join(df.columns.tolist())
                raise ValueError(
                    f"No se encontraron las columnas especificadas.\nColumnas disponibles: {available_cols}")

            # Extraer datos
            self.preview_data = []
            valid_count = 0

            for _, row in df.iterrows():
                name = str(row[name_column]).strip() if pd.notna(row[name_column]) else ""
                number = str(row[number_column]).strip() if pd.notna(row[number_column]) else ""

                # Limpiar número (solo dígitos)
                clean_number = ''.join(filter(str.isdigit, number))

                if name and clean_number:
                    self.preview_data.append({
                        'nombre': name,
                        'numero': clean_number
                    })
                    valid_count += 1

            # Actualizar vista previa
            self._update_preview()

            # Actualizar estadísticas
            total_rows = len(df)
            self.stats_label.configure(
                text=f"📊 Total filas: {total_rows} | Contactos válidos: {valid_count} | Se importarán: {len(self.preview_data)}"
            )

            # Habilitar botón importar si hay datos
            if self.preview_data:
                self.import_btn.configure(state="normal")
            else:
                self.import_btn.configure(state="disabled")

        except ImportError:
            show_error_message(
                "Se requiere la librería pandas para procesar archivos Excel.\nPor favor instala: pip install pandas openpyxl")
        except Exception as e:
            show_error_message(f"Error al procesar archivo: {str(e)}")

    def _update_preview(self):
        """
        Actualiza la vista previa con los datos procesados
        """
        # Limpiar tabla
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)

        # Mostrar solo los primeros 50 contactos para rendimiento
        display_data = self.preview_data[:50]

        for contact in display_data:
            self.preview_tree.insert('', 'end', values=(contact['nombre'], contact['numero']))

    def _clear_preview(self):
        """
        Limpia la vista previa
        """
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)

        self.preview_data = []
        self.import_btn.configure(state="disabled")
        self.stats_label.configure(text="Procesa el archivo para ver la vista previa")

    def _import_contacts(self):
        """
        Importa los contactos procesados
        """
        if not self.preview_data:
            show_validation_error("No hay datos para importar")
            return

        if self.upload_callback:
            self.upload_callback(self.preview_data)