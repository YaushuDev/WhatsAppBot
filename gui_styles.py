# gui_styles.py
"""
Gestor de estilos y configuración visual para el Bot de WhatsApp
Centraliza toda la configuración de colores, estilos y temas de la interfaz gráfica,
proporcionando un tema nocturno consistente y métodos para aplicar estilos a widgets
"""

import tkinter as tk
from tkinter import ttk


class StyleManager:
    """
    Gestor centralizado de estilos para la GUI del bot de WhatsApp
    """

    def __init__(self):
        """
        Inicializa el gestor de estilos con el tema nocturno
        """
        # Paleta de colores del tema nocturno
        self.colors = {
            "bg_primary": "#1e1e1e",      # Fondo principal
            "bg_secondary": "#2d2d2d",    # Fondo secundario
            "bg_accent": "#3d3d3d",       # Fondo de acento
            "text_primary": "#ffffff",     # Texto principal
            "text_secondary": "#cccccc",   # Texto secundario
            "accent": "#0078d4",          # Color de acento azul
            "accent_hover": "#106ebe",    # Color de acento hover
            "success": "#107c10",         # Verde éxito
            "warning": "#ff8c00",         # Naranja advertencia
            "error": "#d13438",           # Rojo error
            "border": "#404040"           # Borde
        }

        # Configuración de fuentes
        self.fonts = {
            "title": ("Segoe UI", 18, "bold"),
            "subtitle": ("Segoe UI", 16, "bold"),
            "heading": ("Segoe UI", 12, "bold"),
            "normal": ("Segoe UI", 10),
            "button": ("Segoe UI", 11),
            "button_large": ("Segoe UI", 12, "bold"),
            "small": ("Segoe UI", 9),
            "console": ("Consolas", 9)
        }

    def setup_ttk_styles(self):
        """
        Configura los estilos personalizados para widgets ttk
        """
        style = ttk.Style()

        # Estilos para frames
        style.configure("Sidebar.TFrame", background=self.colors["bg_secondary"])
        style.configure("Content.TFrame", background=self.colors["bg_primary"])

        # Estilos para botones de navegación
        style.configure("SidebarButton.TButton",
                        background=self.colors["bg_secondary"],
                        foreground=self.colors["text_primary"],
                        borderwidth=0,
                        focuscolor='none')
        style.map("SidebarButton.TButton",
                  background=[('active', self.colors["bg_accent"])])

        style.configure("ActiveSidebarButton.TButton",
                        background=self.colors["accent"],
                        foreground=self.colors["text_primary"],
                        borderwidth=0,
                        focuscolor='none')

        # Estilos para botones de acción
        style.configure("Action.TButton",
                        background=self.colors["accent"],
                        foreground=self.colors["text_primary"],
                        borderwidth=1,
                        focuscolor='none')
        style.map("Action.TButton",
                  background=[('active', self.colors["accent_hover"])])

    def create_styled_button(self, parent, text, command=None, style="normal", **kwargs):
        """
        Crea un botón con estilo personalizado

        Args:
            parent: Widget padre
            text: Texto del botón
            command: Función a ejecutar al hacer clic
            style: Tipo de estilo (normal, accent, success, warning, error)
            **kwargs: Argumentos adicionales

        Returns:
            Widget Button configurado
        """
        # Configuraciones de estilo por tipo
        style_configs = {
            "normal": {
                "bg": self.colors["bg_secondary"],
                "fg": self.colors["text_primary"]
            },
            "accent": {
                "bg": self.colors["accent"],
                "fg": self.colors["text_primary"]
            },
            "success": {
                "bg": self.colors["success"],
                "fg": self.colors["text_primary"]
            },
            "warning": {
                "bg": self.colors["warning"],
                "fg": self.colors["text_primary"]
            },
            "error": {
                "bg": self.colors["error"],
                "fg": self.colors["text_primary"]
            }
        }

        config = style_configs.get(style, style_configs["normal"])

        # Configuración base del botón
        button_config = {
            "font": self.fonts["button"],
            "border": 0,
            "cursor": "hand2",
            "pady": 8,
            "padx": 15,
            **config,
            **kwargs
        }

        if command:
            button_config["command"] = command

        return tk.Button(parent, text=text, **button_config)

    def create_styled_label(self, parent, text, style="normal", **kwargs):
        """
        Crea una etiqueta con estilo personalizado

        Args:
            parent: Widget padre
            text: Texto de la etiqueta
            style: Tipo de estilo (title, subtitle, heading, normal, small, secondary)
            **kwargs: Argumentos adicionales

        Returns:
            Widget Label configurado
        """
        # Configuraciones de estilo por tipo
        style_configs = {
            "title": {
                "font": self.fonts["title"],
                "fg": self.colors["text_primary"]
            },
            "subtitle": {
                "font": self.fonts["subtitle"],
                "fg": self.colors["text_primary"]
            },
            "heading": {
                "font": self.fonts["heading"],
                "fg": self.colors["text_primary"]
            },
            "normal": {
                "font": self.fonts["normal"],
                "fg": self.colors["text_primary"]
            },
            "small": {
                "font": self.fonts["small"],
                "fg": self.colors["text_secondary"]
            },
            "secondary": {
                "font": self.fonts["normal"],
                "fg": self.colors["text_secondary"]
            }
        }

        config = style_configs.get(style, style_configs["normal"])

        # Configuración base de la etiqueta
        label_config = {
            "bg": self.colors["bg_primary"],
            **config,
            **kwargs
        }

        return tk.Label(parent, text=text, **label_config)

    def create_styled_entry(self, parent, **kwargs):
        """
        Crea un campo de entrada con estilo personalizado

        Args:
            parent: Widget padre
            **kwargs: Argumentos adicionales

        Returns:
            Widget Entry configurado
        """
        entry_config = {
            "font": self.fonts["normal"],
            "bg": self.colors["bg_secondary"],
            "fg": self.colors["text_primary"],
            "border": 1,
            "relief": "solid",
            **kwargs
        }

        return tk.Entry(parent, **entry_config)

    def create_styled_listbox(self, parent, **kwargs):
        """
        Crea una listbox con estilo personalizado

        Args:
            parent: Widget padre
            **kwargs: Argumentos adicionales

        Returns:
            Widget Listbox configurado
        """
        listbox_config = {
            "font": self.fonts["normal"],
            "bg": self.colors["bg_secondary"],
            "fg": self.colors["text_primary"],
            "selectbackground": self.colors["accent"],
            "border": 1,
            "relief": "solid",
            **kwargs
        }

        return tk.Listbox(parent, **listbox_config)

    def create_styled_frame(self, parent, style="primary", **kwargs):
        """
        Crea un frame con estilo personalizado

        Args:
            parent: Widget padre
            style: Tipo de estilo (primary, secondary, accent)
            **kwargs: Argumentos adicionales

        Returns:
            Widget Frame configurado
        """
        # Configuraciones de estilo por tipo
        style_configs = {
            "primary": {"bg": self.colors["bg_primary"]},
            "secondary": {"bg": self.colors["bg_secondary"]},
            "accent": {"bg": self.colors["bg_accent"]}
        }

        config = style_configs.get(style, style_configs["primary"])

        frame_config = {
            **config,
            **kwargs
        }

        return tk.Frame(parent, **frame_config)

    def create_styled_labelframe(self, parent, text, **kwargs):
        """
        Crea un LabelFrame con estilo personalizado

        Args:
            parent: Widget padre
            text: Texto del label
            **kwargs: Argumentos adicionales

        Returns:
            Widget LabelFrame configurado
        """
        labelframe_config = {
            "text": text,
            "font": self.fonts["heading"],
            "bg": self.colors["bg_primary"],
            "fg": self.colors["text_primary"],
            "border": 1,
            "relief": "solid",
            **kwargs
        }

        return tk.LabelFrame(parent, **labelframe_config)

    def configure_window(self, window, title="Bot de WhatsApp", size="900x600", icon_path="icon.ico"):
        """
        Configura una ventana con el estilo del tema

        Args:
            window: Ventana a configurar
            title: Título de la ventana
            size: Tamaño de la ventana
            icon_path: Ruta del icono
        """
        window.title(title)
        window.geometry(size)
        window.resizable(False, False)
        window.configure(bg=self.colors["bg_primary"])

        # Intentar cargar el icono
        try:
            window.iconbitmap(icon_path)
        except:
            pass  # Si no existe el icono, continúa sin él

    def apply_hover_effect(self, widget, hover_color=None):
        """
        Aplica efecto hover a un widget

        Args:
            widget: Widget al que aplicar el efecto
            hover_color: Color cuando se hace hover (opcional)
        """
        if hover_color is None:
            hover_color = self.colors["accent_hover"]

        original_color = widget.cget("bg")

        def on_enter(event):
            widget.configure(bg=hover_color)

        def on_leave(event):
            widget.configure(bg=original_color)

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)