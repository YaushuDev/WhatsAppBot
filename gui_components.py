# gui_components.py
"""
Componentes reutilizables para el Bot de WhatsApp
Contiene widgets personalizados y layouts comunes que se utilizan
en múltiples partes de la interfaz, con diseño mejorado y disposición optimizada
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox
from gui_styles import StyleManager


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
            ("numeros", "📱 Números", "Gestionar números de teléfono"),
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


class ListManager:
    """
    Componente reutilizable para gestión de listas con diseño mejorado
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
    Sección reutilizable para entrada de datos con diseño mejorado
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

        # Estadística de números
        self.stats_numbers = style_manager.create_styled_label(left_col, "📱 Números: 0", "normal")
        self.stats_numbers.pack(anchor="w")

        # Estadística de mensajes
        self.stats_messages = style_manager.create_styled_label(right_col, "💬 Mensajes: 0", "normal")
        self.stats_messages.pack(anchor="e")

    def update_stats(self, numbers_count, messages_count):
        """
        Actualiza las estadísticas mostradas

        Args:
            numbers_count: Cantidad de números
            messages_count: Cantidad de mensajes
        """
        self.stats_numbers.configure(text=f"📱 Números: {numbers_count}")
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