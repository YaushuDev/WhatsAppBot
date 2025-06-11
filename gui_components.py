# gui_components.py
"""
Componentes reutilizables para el Bot de WhatsApp con soporte para emoticones
Contiene widgets personalizados y layouts comunes que se utilizan en múltiples partes de la interfaz,
con diseño mejorado y disposición optimizada. Incluye componentes especializados para gestión de contactos,
carga masiva de Excel y un menú de emoticones integrado para mejorar la experiencia del usuario.
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog, ttk
import os
from typing import List, Dict, Any, Optional, Callable
from gui_styles import StyleManager


class EmojiMenu:
    """
    Menú de emoticones compacto y fácil de usar
    """

    def __init__(self, parent, style_manager: StyleManager, insert_callback=None):
        """
        Inicializa el menú de emoticones

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
            insert_callback: Función para insertar emoji en el texto
        """
        self.style_manager = style_manager
        self.insert_callback = insert_callback
        self.is_expanded = False

        # Colección de emoticones organizados por categorías
        self.emoji_categories = {
            "😊 Caras": ["😀", "😊", "😍", "🤗", "😂", "🤣", "😉", "😎", "🤩", "🥰",
                        "😘", "😋", "😜", "🤔", "😴", "🤤", "😇", "🙂", "🙃", "😌"],
            "❤️ Amor": ["❤️", "💕", "💖", "💗", "💓", "💘", "💝", "💟", "💜", "🖤",
                        "🤍", "🤎", "💙", "💚", "💛", "🧡", "💋", "😍", "🥰", "😘"],
            "👍 Gestos": ["👍", "👎", "👌", "✌️", "🤞", "🤟", "🤘", "🤙", "👈", "👉",
                         "👆", "👇", "☝️", "✋", "🤚", "🖐️", "🖖", "👋", "🤝", "🙏"],
            "🎉 Celebración": ["🎉", "🎊", "🥳", "🎈", "🎁", "🎂", "🍰", "🎆", "🎇", "✨",
                              "🌟", "⭐", "💫", "🎵", "🎶", "🎤", "🏆", "🥇", "🥈", "🥉"],
            "🌞 Naturaleza": ["🌞", "🌙", "⭐", "🌟", "☀️", "⛅", "🌤️", "⛈️", "🌈", "🔥",
                             "💧", "🌊", "🌸", "🌺", "🌻", "🌹", "🌷", "🌱", "🌿", "🍀"],
            "🚀 Objetos": ["📱", "💻", "📧", "📞", "⏰", "📅", "🎯", "🚀", "⚡", "💡",
                          "🔔", "📢", "💰", "💳", "🎮", "🛠️", "🔑", "📝", "📊", "📈"]
        }

        # Frame principal del menú
        self.menu_frame = style_manager.create_styled_frame(parent)
        self.menu_frame.pack(fill=tk.X, pady=(0, 10))

        self._create_emoji_interface()

    def _create_emoji_interface(self):
        """
        Crea la interfaz del menú de emoticones
        """
        # Header del menú con botón para expandir/contraer
        header_frame = self.style_manager.create_styled_frame(self.menu_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        # Botón expandir/contraer
        self.toggle_btn = self.style_manager.create_styled_button(
            header_frame,
            "😀 Emoticones ▼",
            self._toggle_menu,
            "normal"
        )
        self.toggle_btn.pack(side=tk.LEFT)

        # Botón de ayuda
        help_btn = self.style_manager.create_styled_button(
            header_frame,
            "ℹ️",
            self._show_help,
            "normal"
        )
        help_btn.configure(width=3)
        help_btn.pack(side=tk.RIGHT)

        # Contenedor para el menú expandible (inicialmente oculto)
        self.emoji_container = self.style_manager.create_styled_frame(self.menu_frame, "card")
        self.emoji_container.configure(relief="solid", bd=1)
        # No hacer pack inicialmente - se mostrará al expandir

        self._create_emoji_content()

    def _create_emoji_content(self):
        """
        Crea el contenido del menú de emoticones
        """
        # Frame interno con padding
        content_frame = self.style_manager.create_styled_frame(self.emoji_container, "card")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Crear pestañas para cada categoría
        self.notebook = ttk.Notebook(content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Configurar estilo del notebook
        style = ttk.Style()
        style.configure("TNotebook", background=self.style_manager.colors["bg_card"])
        style.configure("TNotebook.Tab",
                        background=self.style_manager.colors["bg_accent"],
                        foreground=self.style_manager.colors["text_primary"])

        # Crear una pestaña para cada categoría
        for category_name, emojis in self.emoji_categories.items():
            self._create_emoji_tab(category_name, emojis)

        # Frame para emoticones favoritos/recientes (primera fila siempre visible)
        self._create_favorites_section(content_frame)

    def _create_emoji_tab(self, category_name: str, emojis: List[str]):
        """
        Crea una pestaña de categoría de emoticones

        Args:
            category_name: Nombre de la categoría
            emojis: Lista de emoticones
        """
        # Frame para la pestaña
        tab_frame = self.style_manager.create_styled_frame(self.notebook, "card")
        self.notebook.add(tab_frame, text=category_name.split()[0])  # Solo el emoji del título

        # Crear grid de emoticones
        row = 0
        col = 0
        max_cols = 10

        for emoji in emojis:
            btn = tk.Button(
                tab_frame,
                text=emoji,
                font=("Segoe UI Emoji", 16),
                bg=self.style_manager.colors["bg_card"],
                fg=self.style_manager.colors["text_primary"],
                border=0,
                pady=5,
                padx=5,
                cursor="hand2",
                relief="flat",
                command=lambda e=emoji: self._insert_emoji(e)
            )
            btn.grid(row=row, column=col, padx=2, pady=2)

            # Efecto hover
            self.style_manager._add_hover_effect(
                btn,
                self.style_manager.colors["hover"],
                self.style_manager.colors["bg_card"]
            )

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def _create_favorites_section(self, parent):
        """
        Crea una sección de emoticones favoritos/frecuentes

        Args:
            parent: Widget padre
        """
        # Separador
        separator = self.style_manager.create_styled_frame(parent, "border")
        separator.configure(height=1)
        separator.pack(fill=tk.X, pady=(10, 5))

        # Label
        fav_label = self.style_manager.create_styled_label(
            parent,
            "⭐ Más usados:",
            "small"
        )
        fav_label.configure(bg=self.style_manager.colors["bg_card"])
        fav_label.pack(anchor="w", pady=(0, 5))

        # Frame para favoritos
        fav_frame = self.style_manager.create_styled_frame(parent, "card")
        fav_frame.pack(fill=tk.X)

        # Emoticones más comunes
        common_emojis = ["😀", "😊", "❤️", "👍", "🎉", "💯", "🔥", "✨", "🚀", "💪"]

        for i, emoji in enumerate(common_emojis):
            btn = tk.Button(
                fav_frame,
                text=emoji,
                font=("Segoe UI Emoji", 16),
                bg=self.style_manager.colors["bg_card"],
                fg=self.style_manager.colors["text_primary"],
                border=0,
                pady=5,
                padx=5,
                cursor="hand2",
                relief="flat",
                command=lambda e=emoji: self._insert_emoji(e)
            )
            btn.grid(row=0, column=i, padx=2, pady=2)

            # Efecto hover
            self.style_manager._add_hover_effect(
                btn,
                self.style_manager.colors["hover"],
                self.style_manager.colors["bg_card"]
            )

    def _toggle_menu(self):
        """
        Alterna la visibilidad del menú de emoticones
        """
        if self.is_expanded:
            # Contraer
            self.emoji_container.pack_forget()
            self.toggle_btn.configure(text="😀 Emoticones ▼")
            self.is_expanded = False
        else:
            # Expandir
            self.emoji_container.pack(fill=tk.X, pady=(0, 10))
            self.toggle_btn.configure(text="😀 Emoticones ▲")
            self.is_expanded = True

    def _insert_emoji(self, emoji: str):
        """
        Inserta un emoji usando el callback

        Args:
            emoji: Emoji a insertar
        """
        if self.insert_callback:
            self.insert_callback(emoji)

    def _show_help(self):
        """
        Muestra ayuda sobre el uso de emoticones
        """
        help_text = """🎯 Ayuda - Menú de Emoticones

✨ Cómo usar:
• Haz clic en cualquier emoji para insertarlo
• Navega por las categorías usando las pestañas
• Los más usados están en la parte inferior

📱 Soporte mejorado:
• Todos los emoticones son compatibles
• Se envían correctamente por WhatsApp
• Funcionan en cualquier dispositivo

💡 Consejo:
Usa emoticones para hacer tus mensajes más expresivos y amigables."""

        messagebox.showinfo("😀 Ayuda - Emoticones", help_text)


class NavigationSidebar:
    """
    Barra lateral de navegación con diseño mejorado
    """

    def __init__(self, parent, style_manager: StyleManager, tab_callback):
        """
        Inicializa la barra lateral

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
            tab_callback: Función callback para cambio de pestañas
        """
        self.style_manager = style_manager
        self.tab_callback = tab_callback
        self.nav_buttons = {}

        # Crear frame principal de la sidebar con ancho mejorado
        self.sidebar = style_manager.create_styled_frame(parent, "secondary")
        self.sidebar.configure(width=220)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 2))
        self.sidebar.pack_propagate(False)

        self._create_elements()

    def _create_elements(self):
        """
        Crea los elementos de la barra lateral con mejor disposición
        """
        # Contenedor principal con padding mejorado
        main_container = self.style_manager.create_styled_frame(self.sidebar, "secondary")
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=20)

        # Título con mejor espaciado
        title_label = self.style_manager.create_styled_label(
            main_container,
            "WhatsApp Bot",
            "subtitle"
        )
        title_label.configure(bg=self.style_manager.colors["bg_secondary"])
        title_label.pack(pady=(0, 35))

        # Contenedor para botones de navegación
        nav_container = self.style_manager.create_styled_frame(main_container, "secondary")
        nav_container.pack(fill=tk.X, pady=(0, 20))

        # Botones de navegación con mejor diseño
        nav_items = [
            ("numeros", "📱 Contactos", "Gestionar contactos de teléfono"),
            ("mensajes", "💬 Mensajes", "Crear y editar mensajes"),
            ("automatizacion", "🤖 Automatización", "Controlar el envío automático")
        ]

        for i, (tab_id, text, tooltip) in enumerate(nav_items):
            # Frame contenedor para cada botón
            btn_frame = self.style_manager.create_styled_frame(nav_container, "secondary")
            btn_frame.pack(fill=tk.X, pady=(0, 8))

            button = tk.Button(
                btn_frame,
                text=text,
                font=self.style_manager.fonts["button"],
                bg=self.style_manager.colors["bg_accent"],
                fg=self.style_manager.colors["text_primary"],
                border=0,
                pady=15,
                padx=20,
                cursor="hand2",
                anchor="w",
                relief="flat",
                command=lambda t=tab_id: self.tab_callback(t)
            )
            button.pack(fill=tk.X)

            # Agregar efecto hover mejorado
            self.style_manager._add_hover_effect(
                button,
                self.style_manager.colors["hover"],
                self.style_manager.colors["bg_accent"]
            )

            self.nav_buttons[tab_id] = button

        # Espaciador flexible
        spacer = self.style_manager.create_styled_frame(main_container, "secondary")
        spacer.pack(fill=tk.BOTH, expand=True)

        # Sección de estado en la parte inferior
        status_container = self.style_manager.create_styled_frame(main_container, "card")
        status_container.pack(fill=tk.X, pady=(10, 0))
        status_container.configure(relief="solid", bd=1, highlightthickness=0)

        # Título de estado
        status_title = self.style_manager.create_styled_label(
            status_container,
            "Estado:",
            "small"
        )
        status_title.configure(
            bg=self.style_manager.colors["bg_card"],
            fg=self.style_manager.colors["accent_light"]
        )
        status_title.pack(pady=(10, 5), padx=15, anchor="w")

        # Mensaje de estado
        self.status_label = self.style_manager.create_styled_label(
            status_container,
            "Listo",
            "small"
        )
        self.status_label.configure(
            bg=self.style_manager.colors["bg_card"],
            wraplength=180,
            justify="left"
        )
        self.status_label.pack(pady=(0, 10), padx=15, anchor="w")

    def update_active_tab(self, active_tab):
        """
        Actualiza el botón activo en la navegación con mejor feedback visual

        Args:
            active_tab: ID de la pestaña activa
        """
        for tab_id, button in self.nav_buttons.items():
            if tab_id == active_tab:
                button.configure(
                    bg=self.style_manager.colors["accent"],
                    fg=self.style_manager.colors["text_primary"]
                )
                # Actualizar hover effect para botón activo
                self.style_manager._add_hover_effect(
                    button,
                    self.style_manager.colors["accent_light"],
                    self.style_manager.colors["accent"]
                )
            else:
                button.configure(
                    bg=self.style_manager.colors["bg_accent"],
                    fg=self.style_manager.colors["text_primary"]
                )
                # Restaurar hover effect normal
                self.style_manager._add_hover_effect(
                    button,
                    self.style_manager.colors["hover"],
                    self.style_manager.colors["bg_accent"]
                )

    def update_status(self, message):
        """
        Actualiza el mensaje de estado con mejor formato

        Args:
            message: Nuevo mensaje de estado
        """
        # Truncar mensaje si es muy largo
        short_message = message[:35] + "..." if len(message) > 35 else message
        self.status_label.configure(text=short_message)


class TabHeader:
    """
    Cabecera reutilizable para pestañas con diseño mejorado
    """

    def __init__(self, parent, style_manager: StyleManager, title, description):
        """
        Inicializa la cabecera de pestaña

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
            title: Título de la pestaña
            description: Descripción de la pestaña
        """
        self.style_manager = style_manager

        # Contenedor principal para la cabecera
        header_frame = style_manager.create_styled_frame(parent)
        header_frame.pack(fill=tk.X, padx=25, pady=(25, 30))

        # Título
        title_label = style_manager.create_styled_label(header_frame, title, "title")
        title_label.pack(anchor="w")

        # Descripción con mejor espaciado
        desc_label = style_manager.create_styled_label(header_frame, description, "secondary")
        desc_label.pack(anchor="w", pady=(8, 0))

        # Línea separadora sutil
        separator = style_manager.create_styled_frame(header_frame, "accent")
        separator.configure(height=2)
        separator.pack(fill=tk.X, pady=(15, 0))


class SubTabNavigator:
    """
    Navegador de sub-pestañas compacto y elegante para la sección de contactos
    """

    def __init__(self, parent, style_manager: StyleManager, tabs_info: List[tuple], callback):
        """
        Inicializa el navegador de sub-pestañas

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
            tabs_info: Lista de tuplas (id, texto, icono)
            callback: Función callback para cambio de sub-pestaña
        """
        self.style_manager = style_manager
        self.callback = callback
        self.buttons = {}
        self.current_tab = None

        # Frame compacto para los botones de sub-pestañas
        self.nav_frame = style_manager.create_styled_frame(parent)
        self.nav_frame.pack(fill=tk.X, padx=25, pady=(0, 15))

        # Crear botones de navegación compactos
        button_frame = style_manager.create_styled_frame(self.nav_frame)
        button_frame.pack()

        for tab_id, text, icon in tabs_info:
            # Botón compacto tipo "pill"
            button = tk.Button(
                button_frame,
                text=f"{icon} {text}",
                font=self.style_manager.fonts["normal"],
                bg=self.style_manager.colors["bg_accent"],
                fg=self.style_manager.colors["text_secondary"],
                border=0,
                pady=8,
                padx=20,
                cursor="hand2",
                relief="flat",
                command=lambda t=tab_id: self._on_tab_change(t)
            )
            button.pack(side=tk.LEFT, padx=(0, 8))

            # Efecto hover sutil
            self.style_manager._add_hover_effect(
                button,
                self.style_manager.colors["hover"],
                self.style_manager.colors["bg_accent"]
            )

            self.buttons[tab_id] = button

    def _on_tab_change(self, tab_id):
        """
        Maneja el cambio de sub-pestaña

        Args:
            tab_id: ID de la sub-pestaña
        """
        self.set_active_tab(tab_id)
        self.callback(tab_id)

    def set_active_tab(self, tab_id):
        """
        Establece la sub-pestaña activa visualmente con diseño mejorado

        Args:
            tab_id: ID de la sub-pestaña activa
        """
        self.current_tab = tab_id
        for btn_id, button in self.buttons.items():
            if btn_id == tab_id:
                # Estilo activo más elegante
                button.configure(
                    bg=self.style_manager.colors["accent"],
                    fg=self.style_manager.colors["text_primary"],
                    relief="flat"
                )
                # Hover effect para botón activo
                self.style_manager._add_hover_effect(
                    button,
                    self.style_manager.colors["accent_light"],
                    self.style_manager.colors["accent"]
                )
            else:
                # Estilo inactivo sutil
                button.configure(
                    bg=self.style_manager.colors["bg_accent"],
                    fg=self.style_manager.colors["text_secondary"],
                    relief="flat"
                )
                # Hover effect normal
                self.style_manager._add_hover_effect(
                    button,
                    self.style_manager.colors["hover"],
                    self.style_manager.colors["bg_accent"]
                )


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


class ExcelUploadComponent:
    """
    Componente para carga masiva desde Excel con vista previa en tema oscuro
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


# Componentes de compatibilidad (mantenidos para no romper código existente)

class ListManager:
    """
    Componente reutilizable para gestión de listas (versión de compatibilidad)
    """

    def __init__(self, parent, style_manager: StyleManager, title,
                 add_callback=None, delete_callback=None, edit_callback=None):
        """
        Inicializa el gestor de lista

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
            title: Título de la lista
            add_callback: Función para agregar elementos
            delete_callback: Función para eliminar elementos
            edit_callback: Función para editar elementos (opcional)
        """
        self.style_manager = style_manager
        self.add_callback = add_callback
        self.delete_callback = delete_callback
        self.edit_callback = edit_callback

        # Frame principal con mejor contenedor
        self.list_frame = style_manager.create_styled_labelframe(parent, title)
        self.list_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=(0, 20))

        # Contenido interno con padding
        content_frame = style_manager.create_styled_frame(self.list_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Frame para listbox con scrollbar
        listbox_frame = style_manager.create_styled_frame(content_frame, "card")
        listbox_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        listbox_frame.configure(relief="solid", bd=1)

        # Listbox con altura fija mejorada
        self.listbox = style_manager.create_styled_listbox(listbox_frame, height=12)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Scrollbar con mejor estilo
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

        # Frame para botones con mejor disposición
        self.buttons_frame = style_manager.create_styled_frame(content_frame)
        self.buttons_frame.pack(fill=tk.X)

        self._create_buttons()

    def _create_buttons(self):
        """
        Crea los botones de acción con mejor diseño
        """
        # Botón editar (solo si se proporciona callback)
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
            delete_btn.pack(side=tk.LEFT)

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

    def clear_and_populate(self, items):
        """
        Limpia la lista y la puebla con nuevos elementos

        Args:
            items: Lista de elementos a mostrar
        """
        self.listbox.delete(0, tk.END)
        for item in items:
            self.listbox.insert(tk.END, item)


class InputSection:
    """
    Sección reutilizable para entrada de datos (versión de compatibilidad)
    """

    def __init__(self, parent, style_manager: StyleManager, label_text,
                 input_type="entry", button_text="Agregar", button_callback=None):
        """
        Inicializa la sección de entrada

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
            label_text: Texto de la etiqueta
            input_type: Tipo de entrada ("entry" o "text")
            button_text: Texto del botón
            button_callback: Función del botón
        """
        self.style_manager = style_manager
        self.input_type = input_type

        # Frame principal con mejor contenedor
        self.input_frame = style_manager.create_styled_labelframe(parent, label_text)
        self.input_frame.pack(fill=tk.X, padx=25, pady=(0, 20))

        # Contenido interno con padding
        content_frame = style_manager.create_styled_frame(self.input_frame)
        content_frame.pack(fill=tk.X, padx=15, pady=15)

        # Crear widget de entrada según el tipo
        if input_type == "entry":
            # Frame para entrada y botón
            controls_frame = style_manager.create_styled_frame(content_frame)
            controls_frame.pack(fill=tk.X)

            self.input_widget = style_manager.create_styled_entry(controls_frame)
            self.input_widget.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 15))
            self.input_widget.configure(font=style_manager.fonts["normal"])

            # Agregar evento Enter para entry
            if button_callback:
                self.input_widget.bind("<Return>", lambda e: button_callback())

            # Botón en la misma línea
            if button_callback:
                button = style_manager.create_styled_button(
                    controls_frame,
                    button_text,
                    button_callback,
                    "accent"
                )
                button.pack(side=tk.RIGHT)

        else:  # text
            self.input_widget = scrolledtext.ScrolledText(
                content_frame,
                height=5,
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
            self.input_widget.pack(fill=tk.X, pady=(0, 15))

            # Botón debajo del texto
            if button_callback:
                button = style_manager.create_styled_button(
                    content_frame,
                    button_text,
                    button_callback,
                    "accent"
                )
                button.pack()

    def get_value(self):
        """
        Obtiene el valor del widget de entrada

        Returns:
            Valor ingresado como string
        """
        if self.input_type == "entry":
            return self.input_widget.get().strip()
        else:
            return self.input_widget.get(1.0, tk.END).strip()

    def clear_value(self):
        """
        Limpia el valor del widget de entrada
        """
        if self.input_type == "entry":
            self.input_widget.delete(0, tk.END)
        else:
            self.input_widget.delete(1.0, tk.END)

    def set_value(self, value):
        """
        Establece un valor en el widget de entrada

        Args:
            value: Valor a establecer
        """
        self.clear_value()
        if self.input_type == "entry":
            self.input_widget.insert(0, value)
        else:
            self.input_widget.insert(1.0, value)


class StatsDisplay:
    """
    Componente para mostrar estadísticas con diseño mejorado
    """

    def __init__(self, parent, style_manager: StyleManager):
        """
        Inicializa el display de estadísticas

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
        """
        self.style_manager = style_manager

        # Frame con borde mejorado
        self.stats_frame = style_manager.create_styled_labelframe(parent, "📊 Estadísticas")
        self.stats_frame.pack(fill=tk.X, padx=25, pady=(0, 20))

        # Contenido con mejor disposición
        content_frame = style_manager.create_styled_frame(self.stats_frame)
        content_frame.pack(fill=tk.X, padx=15, pady=15)

        # Contenedor para estadísticas en grid
        stats_container = style_manager.create_styled_frame(content_frame)
        stats_container.pack(fill=tk.X)

        # Columna izquierda
        left_col = style_manager.create_styled_frame(stats_container)
        left_col.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Columna derecha
        right_col = style_manager.create_styled_frame(stats_container)
        right_col.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        # Estadística de contactos
        self.stats_numbers = style_manager.create_styled_label(left_col, "📱 Contactos: 0", "normal")
        self.stats_numbers.pack(anchor="w")

        # Estadística de mensajes
        self.stats_messages = style_manager.create_styled_label(right_col, "💬 Mensajes: 0", "normal")
        self.stats_messages.pack(anchor="e")

    def update_stats(self, numbers_count, messages_count):
        """
        Actualiza las estadísticas mostradas

        Args:
            numbers_count: Cantidad de contactos
            messages_count: Cantidad de mensajes
        """
        self.stats_numbers.configure(text=f"📱 Contactos: {numbers_count}")
        self.stats_messages.configure(text=f"💬 Mensajes: {messages_count}")


class ActivityLog:
    """
    Componente para el registro de actividad con diseño mejorado
    """

    def __init__(self, parent, style_manager: StyleManager, title="📋 Registro de Actividad"):
        """
        Inicializa el log de actividad

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
            title: Título del log
        """
        self.style_manager = style_manager

        # Frame con borde mejorado
        log_frame = style_manager.create_styled_labelframe(parent, title)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=(0, 25))

        # Contenido con padding
        content_frame = style_manager.create_styled_frame(log_frame, "card")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        content_frame.configure(relief="solid", bd=1)

        # Área de texto con scroll mejorada
        self.log_text = scrolledtext.ScrolledText(
            content_frame,
            height=10,
            font=style_manager.fonts["console"],
            bg=style_manager.colors["bg_card"],
            fg=style_manager.colors["text_primary"],
            border=0,
            state="disabled",
            wrap=tk.WORD,
            highlightthickness=0,
            insertbackground=style_manager.colors["text_primary"]
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    def add_message(self, message):
        """
        Agrega un mensaje al log con timestamp mejorado

        Args:
            message: Mensaje a agregar
        """
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")


# Funciones de diálogo mejoradas
def show_validation_error(message):
    """
    Muestra un mensaje de error de validación

    Args:
        message: Mensaje de error
    """
    messagebox.showwarning("⚠️ Advertencia", message)


def show_success_message(message):
    """
    Muestra un mensaje de éxito

    Args:
        message: Mensaje de éxito
    """
    messagebox.showinfo("✅ Éxito", message)


def show_error_message(message):
    """
    Muestra un mensaje de error

    Args:
        message: Mensaje de error
    """
    messagebox.showerror("❌ Error", message)


def show_confirmation_dialog(message):
    """
    Muestra un diálogo de confirmación

    Args:
        message: Mensaje de confirmación

    Returns:
        True si el usuario confirma
    """
    return messagebox.askyesno("🤔 Confirmar", message)