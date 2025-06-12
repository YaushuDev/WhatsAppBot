# gui_styles.py
"""
Gestor de estilos y configuración visual para el Bot de WhatsApp
Centraliza toda la configuración de colores, estilos y temas de la interfaz gráfica,
proporcionando un tema moderno con paleta verde armónica y diseño horizontal compacto
optimizado para pantallas de cualquier tamaño y resolución.
"""

import tkinter as tk
from tkinter import ttk


class StyleManager:
    """
    Gestor centralizado de estilos para la GUI del bot de WhatsApp
    Optimizado para layout horizontal compacto de 1000x600px
    """

    def __init__(self):
        """
        Inicializa el gestor de estilos con paleta verde armónica
        y configuraciones optimizadas para layout horizontal
        """
        # Paleta de colores verde armónica y moderna
        self.colors = {
            "bg_primary": "#0d1117",  # Fondo principal - negro azulado muy oscuro
            "bg_secondary": "#161b22",  # Fondo secundario - gris muy oscuro
            "bg_accent": "#21262d",  # Fondo de acento - gris oscuro
            "bg_card": "#1c2128",  # Fondo de tarjetas
            "text_primary": "#f0f6fc",  # Texto principal - blanco suave
            "text_secondary": "#8b949e",  # Texto secundario - gris claro
            "text_muted": "#6e7681",  # Texto silenciado
            "accent": "#238636",  # Verde principal - más suave
            "accent_light": "#2ea043",  # Verde claro
            "accent_dark": "#1a7f37",  # Verde oscuro
            "success": "#2da44e",  # Verde éxito
            "warning": "#fb8500",  # Naranja advertencia - más suave
            "error": "#da3633",  # Rojo error - más suave
            "border": "#30363d",  # Borde principal
            "border_light": "#21262d",  # Borde suave
            "hover": "#262c36"  # Color hover
        }

        # Configuración de fuentes optimizada para espacio compacto
        self.fonts = {
            "title": ("Segoe UI", 18, "bold"),  # Reducido de 20 a 18
            "subtitle": ("Segoe UI", 14, "bold"),  # Reducido de 16 a 14
            "heading": ("Segoe UI", 12, "bold"),  # Reducido de 13 a 12
            "normal": ("Segoe UI", 9),  # Reducido de 10 a 9
            "button": ("Segoe UI", 9, "bold"),  # Reducido de 10 a 9
            "button_large": ("Segoe UI", 10, "bold"),  # Reducido de 11 a 10
            "small": ("Segoe UI", 8),  # Reducido de 9 a 8
            "console": ("Consolas", 8)  # Reducido de 9 a 8
        }

        # Configuración de espaciado compacto para layout horizontal
        self.spacing = {
            "small": 3,  # Reducido de 5 a 3
            "medium": 6,  # Reducido de 10 a 6
            "large": 12,  # Reducido de 20 a 12
            "xlarge": 18  # Reducido de 30 a 18
        }

    def setup_ttk_styles(self):
        """
        Configura los estilos personalizados para widgets ttk
        """
        style = ttk.Style()

        # Estilos para frames
        style.configure("Sidebar.TFrame", background=self.colors["bg_secondary"])
        style.configure("Content.TFrame", background=self.colors["bg_primary"])

        # Estilos para botones de navegación más compactos
        style.configure("SidebarButton.TButton",
                        background=self.colors["bg_secondary"],
                        foreground=self.colors["text_primary"],
                        borderwidth=0,
                        focuscolor='none',
                        padding=(12, 8))  # Reducido de (15, 12) a (12, 8)
        style.map("SidebarButton.TButton",
                  background=[('active', self.colors["hover"])])

        style.configure("ActiveSidebarButton.TButton",
                        background=self.colors["accent"],
                        foreground=self.colors["text_primary"],
                        borderwidth=0,
                        focuscolor='none',
                        padding=(12, 8))  # Reducido de (15, 12) a (12, 8)

        # Estilos para botones de acción más compactos
        style.configure("Action.TButton",
                        background=self.colors["accent"],
                        foreground=self.colors["text_primary"],
                        borderwidth=1,
                        focuscolor='none',
                        padding=(8, 6))  # Reducido de (10, 8) a (8, 6)
        style.map("Action.TButton",
                  background=[('active', self.colors["accent_light"])])

        # Estilos específicos para Treeview (vista previa de Excel)
        self._configure_treeview_styles(style)

    def _configure_treeview_styles(self, style):
        """
        Configura estilos específicos para el Treeview usado en la vista previa de Excel

        Args:
            style: Instancia de ttk.Style
        """
        # Configurar estilo personalizado para Treeview más compacto
        style.configure("Dark.Treeview",
                        background=self.colors["bg_card"],
                        foreground=self.colors["text_primary"],
                        fieldbackground=self.colors["bg_card"],
                        borderwidth=0,
                        relief="flat",
                        rowheight=20)  # Reducido de 25 a 20

        # Configurar headers del Treeview
        style.configure("Dark.Treeview.Heading",
                        background=self.colors["bg_accent"],
                        foreground=self.colors["text_primary"],
                        borderwidth=1,
                        relief="solid",
                        font=self.fonts["heading"])

        # Configurar selección y hover
        style.map("Dark.Treeview",
                  background=[('selected', self.colors["accent"]),
                              ('focus', self.colors["accent"])],
                  foreground=[('selected', self.colors["text_primary"]),
                              ('focus', self.colors["text_primary"])])

        # Configurar separadores
        style.configure("Dark.Treeview.Separator",
                        background=self.colors["border"])

    def create_styled_button(self, parent, text, command=None, style="normal", **kwargs):
        """
        Crea un botón con estilo personalizado compacto

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
                "bg": self.colors["bg_accent"],
                "fg": self.colors["text_primary"],
                "activebackground": self.colors["hover"]
            },
            "accent": {
                "bg": self.colors["accent"],
                "fg": self.colors["text_primary"],
                "activebackground": self.colors["accent_light"]
            },
            "success": {
                "bg": self.colors["success"],
                "fg": self.colors["text_primary"],
                "activebackground": self.colors["accent_light"]
            },
            "warning": {
                "bg": self.colors["warning"],
                "fg": self.colors["text_primary"],
                "activebackground": "#ffb347"
            },
            "error": {
                "bg": self.colors["error"],
                "fg": self.colors["text_primary"],
                "activebackground": "#ff6b6b"
            }
        }

        config = style_configs.get(style, style_configs["normal"])

        # Configuración base del botón más compacta
        button_config = {
            "font": self.fonts["button"],
            "border": 0,
            "cursor": "hand2",
            "pady": 6,  # Reducido de 10 a 6
            "padx": 12,  # Reducido de 20 a 12
            "relief": "flat",
            "bd": 0,
            **config,
            **kwargs
        }

        if command:
            button_config["command"] = command

        button = tk.Button(parent, text=text, **button_config)

        # Agregar efecto hover
        self._add_hover_effect(button, config["activebackground"], config["bg"])

        return button

    def create_styled_label(self, parent, text, style="normal", **kwargs):
        """
        Crea una etiqueta con estilo personalizado mejorado

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
                "fg": self.colors["accent_light"]
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
            },
            "muted": {
                "font": self.fonts["small"],
                "fg": self.colors["text_muted"]
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
        Crea un campo de entrada con estilo personalizado compacto

        Args:
            parent: Widget padre
            **kwargs: Argumentos adicionales

        Returns:
            Widget Entry configurado
        """
        entry_config = {
            "font": self.fonts["normal"],
            "bg": self.colors["bg_card"],
            "fg": self.colors["text_primary"],
            "border": 1,
            "relief": "solid",
            "borderwidth": 1,
            "highlightthickness": 1,
            "highlightcolor": self.colors["accent"],
            "highlightbackground": self.colors["border"],
            "insertbackground": self.colors["text_primary"],
            **kwargs
        }

        return tk.Entry(parent, **entry_config)

    def create_styled_listbox(self, parent, **kwargs):
        """
        Crea una listbox con estilo personalizado y altura más compacta

        Args:
            parent: Widget padre
            **kwargs: Argumentos adicionales

        Returns:
            Widget Listbox configurado
        """
        # Altura por defecto más compacta para layout horizontal
        default_height = kwargs.get('height', 6)  # Reducido de 8 a 6

        listbox_config = {
            "font": self.fonts["normal"],
            "bg": self.colors["bg_card"],
            "fg": self.colors["text_primary"],
            "selectbackground": self.colors["accent"],
            "selectforeground": self.colors["text_primary"],
            "border": 1,
            "relief": "solid",
            "borderwidth": 1,
            "highlightthickness": 0,
            "activestyle": "none",
            "height": default_height,
            **kwargs
        }

        return tk.Listbox(parent, **listbox_config)

    def create_styled_frame(self, parent, style="primary", **kwargs):
        """
        Crea un frame con estilo personalizado mejorado

        Args:
            parent: Widget padre
            style: Tipo de estilo (primary, secondary, accent, card, border)
            **kwargs: Argumentos adicionales

        Returns:
            Widget Frame configurado
        """
        # Configuraciones de estilo por tipo
        style_configs = {
            "primary": {"bg": self.colors["bg_primary"]},
            "secondary": {"bg": self.colors["bg_secondary"]},
            "accent": {"bg": self.colors["bg_accent"]},
            "card": {"bg": self.colors["bg_card"]},
            "border": {"bg": self.colors["border"]}
        }

        config = style_configs.get(style, style_configs["primary"])

        frame_config = {
            "relief": "flat",
            "bd": 0,
            **config,
            **kwargs
        }

        return tk.Frame(parent, **frame_config)

    def create_styled_labelframe(self, parent, text, **kwargs):
        """
        Crea un LabelFrame con estilo personalizado compacto

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
            "fg": self.colors["accent_light"],
            "border": 1,
            "relief": "solid",
            "bd": 1,
            "highlightthickness": 0,
            "labelanchor": "nw",
            **kwargs
        }

        return tk.LabelFrame(parent, **labelframe_config)

    def configure_window(self, window, title="Bot de WhatsApp", size="1000x600", icon_path="icon.ico"):
        """
        Configura una ventana con el estilo del tema optimizado para layout horizontal

        Args:
            window: Ventana a configurar
            title: Título de la ventana
            size: Tamaño de la ventana (ahora por defecto 1000x600)
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

        # Centrar ventana en pantalla
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

    def _add_hover_effect(self, widget, hover_color, normal_color):
        """
        Aplica efecto hover a un widget

        Args:
            widget: Widget al que aplicar el efecto
            hover_color: Color cuando se hace hover
            normal_color: Color normal
        """

        def on_enter(event):
            widget.configure(bg=hover_color)

        def on_leave(event):
            widget.configure(bg=normal_color)

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def apply_hover_effect(self, widget, hover_color=None):
        """
        Aplica efecto hover a un widget (método público)

        Args:
            widget: Widget al que aplicar el efecto
            hover_color: Color cuando se hace hover (opcional)
        """
        if hover_color is None:
            hover_color = self.colors["hover"]

        original_color = widget.cget("bg")
        self._add_hover_effect(widget, hover_color, original_color)