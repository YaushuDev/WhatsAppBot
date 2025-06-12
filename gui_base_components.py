# gui_base_components.py
"""
Componentes base y reutilizables para el Bot de WhatsApp.
Este módulo contiene los componentes fundamentales que se usan en múltiples partes
de la interfaz: navegación, elementos base de UI, emoticones y diálogos comunes.
Proporciona la base arquitectónica para el resto de componentes especializados.
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
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


class ListManager:
    """
    Componente reutilizable para gestión de listas
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

        # Listbox con altura más compacta
        self.listbox = style_manager.create_styled_listbox(listbox_frame, height=8)
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
    Sección reutilizable para entrada de datos
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


# Funciones de diálogo
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