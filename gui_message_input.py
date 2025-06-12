# gui_message_input.py
"""
Componentes de entrada de mensajes para el Bot de WhatsApp.
Este módulo implementa los componentes especializados para la creación de mensajes
con texto, imágenes y emoticones. Proporciona una interfaz compacta e intuitiva para entrada
de contenido multimedia con validación y vista previa optimizada.
"""

import tkinter as tk
from tkinter import scrolledtext, filedialog
import os
from PIL import Image, ImageTk
from gui_styles import StyleManager
from gui_components import EmojiMenu, show_validation_error


class ImagePreviewComponent:
    """
    Componente compacto para vista previa y manejo de imágenes
    Optimizado para usar menos espacio vertical
    """

    def __init__(self, parent, style_manager: StyleManager):
        """
        Inicializa el componente de vista previa de imagen

        Args:
            parent: Widget padre donde se mostrará el componente
            style_manager: Gestor de estilos para mantener consistencia visual
        """
        self.style_manager = style_manager
        self.selected_image_path = None

        # Crear interfaz compacta
        self._create_compact_interface(parent)

    def _create_compact_interface(self, parent):
        """
        Crea la interfaz compacta de manejo de imágenes

        Args:
            parent: Widget padre
        """
        # Frame principal más compacto
        self.image_frame = self.style_manager.create_styled_frame(parent)
        self.image_frame.pack(fill=tk.X, pady=(0, 8))

        # Header en una sola línea
        self._create_compact_header()

        # Área de vista previa más pequeña
        self._create_compact_preview()

    def _create_compact_header(self):
        """
        Crea el header compacto con controles en línea
        """
        header_frame = self.style_manager.create_styled_frame(self.image_frame)
        header_frame.pack(fill=tk.X, pady=(0, 8))

        # Label de imagen
        image_label = self.style_manager.create_styled_label(
            header_frame,
            "Imagen:",
            "normal"
        )
        image_label.pack(side=tk.LEFT)

        # Botones de control mejorados
        self._create_improved_buttons(header_frame)

    def _create_improved_buttons(self, parent):
        """
        Crea botones mejorados con texto claro

        Args:
            parent: Widget padre
        """
        buttons_frame = self.style_manager.create_styled_frame(parent)
        buttons_frame.pack(side=tk.RIGHT)

        # Botón seleccionar con texto claro
        self.select_btn = self.style_manager.create_styled_button(
            buttons_frame,
            "📁 Subir",
            self._select_image,
            "normal"
        )
        self.select_btn.configure(pady=6)
        self.select_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Botón quitar con texto claro y color mejorado
        self.clear_btn = self.style_manager.create_styled_button(
            buttons_frame,
            "🗑️ Quitar",
            self._clear_image,
            "error"
        )
        self.clear_btn.configure(
            pady=6,
            state="disabled",
            fg=self.style_manager.colors["text_primary"]  # Texto blanco en botón rojo
        )
        self.clear_btn.pack(side=tk.LEFT)

    def _create_compact_preview(self):
        """
        Crea el área de vista previa más compacta
        """
        self.preview_frame = self.style_manager.create_styled_frame(self.image_frame, "card")
        self.preview_frame.configure(relief="solid", bd=1, height=80)  # Más pequeño
        self.preview_frame.pack(fill=tk.X)
        self.preview_frame.pack_propagate(False)

        # Mostrar mensaje inicial
        self._show_no_image_message("Opcional")

    def _select_image(self):
        """
        Abre el diálogo para seleccionar una imagen
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
            self._process_selected_image(image_path)

    def _process_selected_image(self, image_path):
        """
        Procesa la imagen seleccionada

        Args:
            image_path: Ruta de la imagen seleccionada
        """
        if self._validate_image(image_path):
            self.selected_image_path = image_path
            self._update_preview()
            self.clear_btn.configure(
                state="normal",
                fg=self.style_manager.colors["text_primary"]  # Mantener texto blanco
            )
        else:
            show_validation_error("El archivo seleccionado no es una imagen válida")

    def _clear_image(self):
        """
        Quita la imagen seleccionada
        """
        self.selected_image_path = None
        self._update_preview()
        self.clear_btn.configure(
            state="disabled",
            fg=self.style_manager.colors["text_primary"]  # Mantener texto blanco
        )

    def _validate_image(self, image_path):
        """
        Valida que el archivo sea una imagen válida

        Args:
            image_path: Ruta de la imagen a validar

        Returns:
            bool: True si es una imagen válida
        """
        try:
            if not os.path.exists(image_path):
                return False

            with Image.open(image_path) as img:
                img.verify()
            return True
        except Exception:
            return False

    def _update_preview(self):
        """
        Actualiza la vista previa de la imagen
        """
        # Limpiar contenido actual
        self._clear_preview_content()

        if self.selected_image_path and os.path.exists(self.selected_image_path):
            self._show_compact_preview()
        else:
            self._show_no_image_message()

    def _clear_preview_content(self):
        """
        Limpia el contenido actual de la vista previa
        """
        for widget in self.preview_frame.winfo_children():
            widget.destroy()

    def _show_compact_preview(self):
        """
        Muestra la vista previa compacta de la imagen
        """
        try:
            self._load_and_display_compact_image()
        except Exception as e:
            print(f"Error mostrando preview: {e}")
            self._show_no_image_message("Error al cargar")

    def _load_and_display_compact_image(self):
        """
        Carga y muestra la imagen en formato compacto
        """
        # Cargar y redimensionar imagen más pequeña
        with Image.open(self.selected_image_path) as img:
            # Dimensiones más compactas
            max_width, max_height = 150, 60
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

            # Convertir para Tkinter
            photo = ImageTk.PhotoImage(img)

            # Container horizontal para imagen y nombre
            container = self.style_manager.create_styled_frame(self.preview_frame, "card")
            container.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

            # Imagen a la izquierda
            image_label = tk.Label(
                container,
                image=photo,
                bg=self.style_manager.colors["bg_card"]
            )
            image_label.image = photo  # Mantener referencia
            image_label.pack(side=tk.LEFT, padx=(0, 10))

            # Info a la derecha
            filename = os.path.basename(self.selected_image_path)
            if len(filename) > 20:
                filename = filename[:17] + "..."

            info_label = self.style_manager.create_styled_label(
                container,
                f"📷 {filename}",
                "small"
            )
            info_label.configure(bg=self.style_manager.colors["bg_card"])
            info_label.pack(side=tk.LEFT, anchor="w")

    def _show_no_image_message(self, message="Sin imagen"):
        """
        Muestra un mensaje compacto cuando no hay imagen

        Args:
            message: Mensaje a mostrar
        """
        status_label = self.style_manager.create_styled_label(
            self.preview_frame,
            message,
            "secondary"
        )
        status_label.configure(bg=self.style_manager.colors["bg_card"])
        status_label.pack(expand=True)

    def get_image_path(self):
        """
        Obtiene la ruta de la imagen seleccionada

        Returns:
            str: Ruta de la imagen o None si no hay imagen
        """
        return self.selected_image_path

    def set_image_path(self, image_path):
        """
        Establece una imagen específica

        Args:
            image_path: Ruta de la imagen
        """
        if image_path and os.path.exists(image_path):
            self.selected_image_path = image_path
            self._update_preview()
            self.clear_btn.configure(
                state="normal",
                fg=self.style_manager.colors["text_primary"]  # Mantener texto blanco
            )
        else:
            self._clear_image()

    def clear(self):
        """
        Limpia la imagen seleccionada
        """
        self._clear_image()


class TextInputComponent:
    """
    Componente optimizado para entrada de texto con emoticones
    Diseñado para ser más compacto y eficiente
    """

    def __init__(self, parent, style_manager: StyleManager):
        """
        Inicializa el componente de entrada de texto

        Args:
            parent: Widget padre donde se mostrará el componente
            style_manager: Gestor de estilos para mantener consistencia visual
        """
        self.style_manager = style_manager

        # Crear interfaz de texto compacta
        self._create_compact_text_interface(parent)

        # Crear menú de emoticones limpio (sin emoticones rápidos)
        self._create_clean_emoji_menu(parent)

    def _create_compact_text_interface(self, parent):
        """
        Crea la interfaz de entrada de texto más compacta

        Args:
            parent: Widget padre
        """
        # Label más compacto
        text_label = self.style_manager.create_styled_label(
            parent,
            "Texto:",
            "normal"
        )
        text_label.pack(anchor="w")

        # Área de texto más pequeña pero eficiente
        self.text_widget = scrolledtext.ScrolledText(
            parent,
            height=3,  # Más compacto: era 4
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
        self.text_widget.pack(fill=tk.X, pady=(5, 8))  # Menos espacio vertical

    def _create_clean_emoji_menu(self, parent):
        """
        Crea el menú de emoticones limpio (sin emoticones rápidos)

        Args:
            parent: Widget padre
        """
        # Crear una versión del EmojiMenu que inicie contraído y sin emoticones rápidos
        self.emoji_menu = CleanEmojiMenu(parent, self.style_manager, self._insert_emoji)

    def _insert_emoji(self, emoji):
        """
        Inserta un emoji en la posición del cursor del área de texto

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

    def get_text(self):
        """
        Obtiene el texto actual del área de entrada

        Returns:
            str: Texto ingresado (sin espacios al inicio/final)
        """
        return self.text_widget.get(1.0, tk.END).strip()

    def set_text(self, text):
        """
        Establece texto en el área de entrada

        Args:
            text: Texto a establecer
        """
        self.clear_text()
        self.text_widget.insert(1.0, text)

    def clear_text(self):
        """
        Limpia el texto del área de entrada
        """
        self.text_widget.delete(1.0, tk.END)

    def focus(self):
        """
        Pone el foco en el área de texto
        """
        self.text_widget.focus_set()

    def is_empty(self):
        """
        Verifica si el área de texto está vacía

        Returns:
            bool: True si está vacía
        """
        return len(self.get_text()) == 0


class CleanEmojiMenu:
    """
    Versión limpia del menú de emoticones - solo botón de expandir/contraer
    """

    def __init__(self, parent, style_manager: StyleManager, insert_callback=None):
        """
        Inicializa el menú limpio de emoticones

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
            insert_callback: Función para insertar emoji
        """
        self.style_manager = style_manager
        self.insert_callback = insert_callback
        self.is_expanded = False

        # Frame principal más compacto
        self.menu_frame = style_manager.create_styled_frame(parent)
        self.menu_frame.pack(fill=tk.X, pady=(0, 8))

        self._create_clean_interface()

    def _create_clean_interface(self):
        """
        Crea la interfaz limpia del menú (solo botón expandir)
        """
        # Header limpio - solo botón
        header_frame = self.style_manager.create_styled_frame(self.menu_frame)
        header_frame.pack(fill=tk.X, pady=(0, 8))

        # Solo el botón expandir/contraer
        self.toggle_btn = self.style_manager.create_styled_button(
            header_frame,
            "😀 Emoticones ▼",
            self._toggle_menu,
            "normal"
        )
        self.toggle_btn.configure(pady=6)
        self.toggle_btn.pack(side=tk.LEFT)

        # Contenedor expandible (inicialmente oculto)
        self.emoji_container = self.style_manager.create_styled_frame(self.menu_frame, "card")
        self.emoji_container.configure(relief="solid", bd=1)
        # Inicia contraído - no hacer pack

        self._create_expanded_content()

    def _create_expanded_content(self):
        """
        Crea el contenido expandido del menú
        """
        # Reutilizar la lógica del EmojiMenu original pero más compacto
        content_frame = self.style_manager.create_styled_frame(self.emoji_container, "card")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Grid de categorías más compacto
        categories = {
            "😊": ["😀", "😊", "😍", "🤗", "😂", "🤣", "😉", "😎", "🤩", "🥰"],
            "🖤": ["❤️", "💕", "💖", "💗", "💓", "💘", "💝", "💟", "💜", "🖤"],
            "👍": ["👍", "👎", "👌", "✌️", "🤞", "🤟", "🤘", "🤙", "👋", "🙏"],
            "🎉": ["🎉", "🎊", "🥳", "🎈", "🎁", "🎂", "✨", "🌟", "⭐", "💫"]
        }

        for category, emojis in categories.items():
            cat_frame = self.style_manager.create_styled_frame(content_frame, "card")
            cat_frame.pack(fill=tk.X, pady=2)

            # Label de categoría
            cat_label = self.style_manager.create_styled_label(
                cat_frame,
                category,
                "small"
            )
            cat_label.configure(bg=self.style_manager.colors["bg_card"])
            cat_label.pack(side=tk.LEFT, padx=(0, 5))

            # Emojis de la categoría
            for emoji in emojis:
                btn = tk.Button(
                    cat_frame,
                    text=emoji,
                    font=("Segoe UI Emoji", 14),
                    bg=self.style_manager.colors["bg_card"],
                    fg=self.style_manager.colors["text_primary"],
                    border=0,
                    pady=2,
                    padx=2,
                    cursor="hand2",
                    relief="flat",
                    command=lambda e=emoji: self._insert_emoji(e)
                )
                btn.pack(side=tk.LEFT, padx=1)

                # Efecto hover
                self.style_manager._add_hover_effect(
                    btn,
                    self.style_manager.colors["hover"],
                    self.style_manager.colors["bg_card"]
                )

    def _toggle_menu(self):
        """
        Alterna la visibilidad del menú expandido
        """
        if self.is_expanded:
            # Contraer
            self.emoji_container.pack_forget()
            self.toggle_btn.configure(text="😀 Emoticones ▼")
            self.is_expanded = False
        else:
            # Expandir
            self.emoji_container.pack(fill=tk.X, pady=(0, 8))
            self.toggle_btn.configure(text="😀 Emoticones ▲")
            self.is_expanded = True

    def _insert_emoji(self, emoji):
        """
        Inserta un emoji usando el callback

        Args:
            emoji: Emoji a insertar
        """
        if self.insert_callback:
            self.insert_callback(emoji)


class MessageInputSection:
    """
    Sección compacta y reorganizada de entrada de mensajes
    Optimizada para usar el espacio de manera más eficiente
    """

    def __init__(self, parent, style_manager: StyleManager, button_callback=None):
        """
        Inicializa la sección optimizada de entrada de mensajes

        Args:
            parent: Widget padre donde se mostrará la sección
            style_manager: Gestor de estilos para mantener consistencia visual
            button_callback: Función a ejecutar cuando se agrega un mensaje
        """
        self.style_manager = style_manager
        self.button_callback = button_callback

        # Crear frame principal más compacto
        self._create_compact_frame(parent)

        # Crear componentes optimizados
        self._create_optimized_components()

        # Crear botón de acción
        if button_callback:
            self._create_compact_button()

    def _create_compact_frame(self, parent):
        """
        Crea el frame principal más compacto

        Args:
            parent: Widget padre
        """
        self.input_frame = self.style_manager.create_styled_labelframe(
            parent,
            "💬 Nuevo mensaje"
        )
        self.input_frame.pack(fill=tk.X, padx=25, pady=(0, 15))  # Menos padding

        # Contenido interno más compacto
        self.content_frame = self.style_manager.create_styled_frame(self.input_frame)
        self.content_frame.pack(fill=tk.X, padx=12, pady=12)  # Menos padding

    def _create_optimized_components(self):
        """
        Crea los componentes en orden optimizado
        """
        # Texto primero (más importante)
        self.text_component = TextInputComponent(
            self.content_frame,
            self.style_manager
        )

        # Imagen después (opcional)
        self.image_component = ImagePreviewComponent(
            self.content_frame,
            self.style_manager
        )

    def _create_compact_button(self):
        """
        Crea el botón de agregar más compacto
        """
        button_frame = self.style_manager.create_styled_frame(self.content_frame)
        button_frame.pack(pady=(8, 0))

        button = self.style_manager.create_styled_button(
            button_frame,
            "➕ Agregar",
            self._on_button_clicked,
            "accent"
        )
        button.configure(pady=8)  # Más compacto
        button.pack()

    def _on_button_clicked(self):
        """
        Maneja el clic en el botón de agregar
        """
        if self.button_callback:
            self.button_callback()

    def get_values(self):
        """
        Obtiene los valores actuales de texto e imagen

        Returns:
            tuple: (texto, ruta_imagen)
        """
        text = self.text_component.get_text()
        image_path = self.image_component.get_image_path()
        return text, image_path

    def clear_values(self):
        """
        Limpia todos los campos de entrada
        """
        self.text_component.clear_text()
        self.image_component.clear()

    def set_values(self, text, image_path=None):
        """
        Establece valores en los campos

        Args:
            text: Texto del mensaje
            image_path: Ruta de la imagen (opcional)
        """
        self.text_component.set_text(text)
        self.image_component.set_image_path(image_path)

    def focus_text(self):
        """
        Pone el foco en el área de texto
        """
        self.text_component.focus()

    def validate_input(self):
        """
        Valida que haya contenido para crear el mensaje

        Returns:
            tuple: (is_valid, error_message)
        """
        if self.text_component.is_empty():
            return False, "Por favor ingresa el texto del mensaje"

        return True, ""

    def has_image(self):
        """
        Verifica si hay una imagen seleccionada

        Returns:
            bool: True si hay imagen
        """
        return self.image_component.get_image_path() is not None