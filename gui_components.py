# gui_components.py
"""
Componentes reutilizables para el Bot de WhatsApp
Contiene widgets personalizados y layouts comunes que se utilizan
en múltiples partes de la interfaz, reduciendo la duplicación de código
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox
from gui_styles import StyleManager


class NavigationSidebar:
    """
    Barra lateral de navegación con botones y estado
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

        # Crear frame principal de la sidebar
        self.sidebar = style_manager.create_styled_frame(parent, "secondary")
        self.sidebar.configure(width=200)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 1))
        self.sidebar.pack_propagate(False)

        self._create_elements()

    def _create_elements(self):
        """
        Crea los elementos de la barra lateral
        """
        # Título
        title_label = self.style_manager.create_styled_label(
            self.sidebar,
            "WhatsApp Bot",
            "subtitle"
        )
        title_label.configure(bg=self.style_manager.colors["bg_secondary"])
        title_label.pack(pady=(20, 30))

        # Botones de navegación
        nav_items = [
            ("numeros", "📱 Números"),
            ("mensajes", "💬 Mensajes"),
            ("automatizacion", "🤖 Automatización")
        ]

        for tab_id, text in nav_items:
            button = tk.Button(
                self.sidebar,
                text=text,
                font=self.style_manager.fonts["button"],
                bg=self.style_manager.colors["bg_secondary"],
                fg=self.style_manager.colors["text_primary"],
                border=0,
                pady=15,
                cursor="hand2",
                command=lambda t=tab_id: self.tab_callback(t)
            )
            button.pack(fill=tk.X, padx=10, pady=5)
            self.nav_buttons[tab_id] = button

        # Espaciador
        spacer = self.style_manager.create_styled_frame(self.sidebar, "secondary")
        spacer.pack(fill=tk.BOTH, expand=True)

        # Estado en la parte inferior
        self.status_label = self.style_manager.create_styled_label(
            self.sidebar,
            "Listo",
            "small"
        )
        self.status_label.configure(
            bg=self.style_manager.colors["bg_secondary"],
            wraplength=180
        )
        self.status_label.pack(side=tk.BOTTOM, pady=10, padx=10)

    def update_active_tab(self, active_tab):
        """
        Actualiza el botón activo en la navegación

        Args:
            active_tab: ID de la pestaña activa
        """
        for tab_id, button in self.nav_buttons.items():
            if tab_id == active_tab:
                button.configure(bg=self.style_manager.colors["accent"])
            else:
                button.configure(bg=self.style_manager.colors["bg_secondary"])

    def update_status(self, message):
        """
        Actualiza el mensaje de estado

        Args:
            message: Nuevo mensaje de estado
        """
        short_message = message[:30] + "..." if len(message) > 30 else message
        self.status_label.configure(text=short_message)


class TabHeader:
    """
    Cabecera reutilizable para pestañas
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

        # Título
        title_label = style_manager.create_styled_label(parent, title, "title")
        title_label.pack(pady=(20, 10))

        # Descripción
        desc_label = style_manager.create_styled_label(parent, description, "secondary")
        desc_label.pack(pady=(0, 20))


class ListManager:
    """
    Componente reutilizable para gestión de listas con scrollbar
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

        # Frame principal
        self.list_frame = style_manager.create_styled_frame(parent)
        self.list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Título de la lista
        title_label = style_manager.create_styled_label(self.list_frame, title, "normal")
        title_label.pack(anchor="w", pady=(0, 5))

        # Frame para listbox con scrollbar
        listbox_frame = style_manager.create_styled_frame(self.list_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True)

        # Listbox
        self.listbox = style_manager.create_styled_listbox(listbox_frame)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar = tk.Scrollbar(listbox_frame, orient="vertical")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Conectar scrollbar
        self.listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.listbox.yview)

        # Frame para botones
        self.buttons_frame = style_manager.create_styled_frame(self.list_frame)
        self.buttons_frame.pack(pady=(10, 0))

        self._create_buttons()

    def _create_buttons(self):
        """
        Crea los botones de acción
        """
        # Botón editar (solo si se proporciona callback)
        if self.edit_callback:
            edit_btn = self.style_manager.create_styled_button(
                self.buttons_frame,
                "Editar",
                self.edit_callback,
                "warning"
            )
            edit_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Botón eliminar
        if self.delete_callback:
            delete_btn = self.style_manager.create_styled_button(
                self.buttons_frame,
                "Eliminar",
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

        # Frame principal
        self.input_frame = style_manager.create_styled_frame(parent)
        self.input_frame.pack(fill=tk.X, padx=20, pady=10)

        # Etiqueta
        label = style_manager.create_styled_label(self.input_frame, label_text, "normal")
        label.pack(anchor="w")

        # Frame para entrada y botón
        controls_frame = style_manager.create_styled_frame(self.input_frame)
        controls_frame.pack(fill=tk.X, pady=(5, 0))

        # Crear widget de entrada según el tipo
        if input_type == "entry":
            self.input_widget = style_manager.create_styled_entry(controls_frame)
            self.input_widget.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
            # Agregar evento Enter para entry
            if button_callback:
                self.input_widget.bind("<Return>", lambda e: button_callback())
        else:  # text
            self.input_widget = scrolledtext.ScrolledText(
                controls_frame,
                height=4,
                font=style_manager.fonts["normal"],
                bg=style_manager.colors["bg_secondary"],
                fg=style_manager.colors["text_primary"],
                border=1,
                relief="solid",
                wrap=tk.WORD
            )
            self.input_widget.pack(fill=tk.X, pady=(0, 10))

        # Botón
        if button_callback and input_type == "entry":
            button = style_manager.create_styled_button(
                controls_frame,
                button_text,
                button_callback,
                "accent"
            )
            button.pack(side=tk.RIGHT)
        elif button_callback and input_type == "text":
            button = style_manager.create_styled_button(
                self.input_frame,
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
    Componente para mostrar estadísticas
    """

    def __init__(self, parent, style_manager: StyleManager):
        """
        Inicializa el display de estadísticas

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
        """
        self.style_manager = style_manager

        # Frame con borde
        self.stats_frame = style_manager.create_styled_labelframe(parent, "Estadísticas")
        self.stats_frame.pack(fill=tk.X, padx=20, pady=10)

        # Contenido
        content_frame = style_manager.create_styled_frame(self.stats_frame)
        content_frame.pack(fill=tk.X, padx=10, pady=10)

        # Labels de estadísticas
        self.stats_numbers = style_manager.create_styled_label(content_frame, "Números: 0", "normal")
        self.stats_numbers.pack(anchor="w")

        self.stats_messages = style_manager.create_styled_label(content_frame, "Mensajes: 0", "normal")
        self.stats_messages.pack(anchor="w")

    def update_stats(self, numbers_count, messages_count):
        """
        Actualiza las estadísticas mostradas

        Args:
            numbers_count: Cantidad de números
            messages_count: Cantidad de mensajes
        """
        self.stats_numbers.configure(text=f"Números: {numbers_count}")
        self.stats_messages.configure(text=f"Mensajes: {messages_count}")


class ActivityLog:
    """
    Componente para el registro de actividad
    """

    def __init__(self, parent, style_manager: StyleManager, title="Registro de Actividad"):
        """
        Inicializa el log de actividad

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
            title: Título del log
        """
        self.style_manager = style_manager

        # Frame con borde
        log_frame = style_manager.create_styled_labelframe(parent, title)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 20))

        # Área de texto con scroll
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=8,
            font=style_manager.fonts["console"],
            bg=style_manager.colors["bg_secondary"],
            fg=style_manager.colors["text_primary"],
            border=0,
            state="disabled",
            wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def add_message(self, message):
        """
        Agrega un mensaje al log

        Args:
            message: Mensaje a agregar
        """
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")


def show_validation_error(message):
    """
    Muestra un mensaje de error de validación

    Args:
        message: Mensaje de error
    """
    messagebox.showwarning("Advertencia", message)


def show_success_message(message):
    """
    Muestra un mensaje de éxito

    Args:
        message: Mensaje de éxito
    """
    messagebox.showinfo("Éxito", message)


def show_error_message(message):
    """
    Muestra un mensaje de error

    Args:
        message: Mensaje de error
    """
    messagebox.showerror("Error", message)


def show_confirmation_dialog(message):
    """
    Muestra un diálogo de confirmación

    Args:
        message: Mensaje de confirmación

    Returns:
        True si el usuario confirma
    """
    return messagebox.askyesno("Confirmar", message)