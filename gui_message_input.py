# gui_message_input.py
"""
Componentes de entrada de mensajes para el Bot de WhatsApp
Este módulo implementa los componentes especializados para la creación de mensajes
con texto, imágenes y emoticones. Proporciona una interfaz intuitiva para entrada
de contenido multimedia con validación y vista previa en tiempo real.
"""

import tkinter as tk
from tkinter import scrolledtext, filedialog
import os
from PIL import Image, ImageTk
from gui_styles import StyleManager
from gui_components import EmojiMenu, show_validation_error


class ImagePreviewComponent:
    """
    Componente especializado para vista previa y manejo de imágenes
    Se encarga de mostrar, validar y gestionar imágenes en mensajes
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

        # Crear interfaz
        self._create_image_interface(parent)

    def _create_image_interface(self, parent):
        """
        Crea la interfaz completa de manejo de imágenes

        Args:
            parent: Widget padre
        """
        # Frame principal para imagen
        self.image_frame = self.style_manager.create_styled_frame(parent)
        self.image_frame.pack(fill=tk.X, pady=(0, 10))

        # Header con label y botones
        self._create_header()

        # Área de vista previa
        self._create_preview_area()

    def _create_header(self):
        """
        Crea el header con label y botones de control
        """
        header_frame = self.style_manager.create_styled_frame(self.image_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        # Label de imagen
        image_label = self.style_manager.create_styled_label(
            header_frame,
            "Imagen (opcional):",
            "normal"
        )
        image_label.pack(side=tk.LEFT)

        # Botones de control
        self._create_control_buttons(header_frame)

    def _create_control_buttons(self, parent):
        """
        Crea los botones de selección y eliminación de imagen

        Args:
            parent: Widget padre
        """
        buttons_frame = self.style_manager.create_styled_frame(parent)
        buttons_frame.pack(side=tk.RIGHT)

        # Botón seleccionar
        self.select_btn = self.style_manager.create_styled_button(
            buttons_frame,
            "📁 Seleccionar",
            self._select_image,
            "normal"
        )
        self.select_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Botón quitar
        self.clear_btn = self.style_manager.create_styled_button(
            buttons_frame,
            "🗑️ Quitar",
            self._clear_image,
            "error"
        )
        self.clear_btn.pack(side=tk.LEFT)
        self.clear_btn.configure(state="disabled")

    def _create_preview_area(self):
        """
        Crea el área de vista previa de imagen
        """
        self.preview_frame = self.style_manager.create_styled_frame(self.image_frame, "card")
        self.preview_frame.configure(relief="solid", bd=1, height=120)
        self.preview_frame.pack(fill=tk.X)
        self.preview_frame.pack_propagate(False)

        # Mostrar mensaje inicial
        self._show_no_image_message("No hay imagen seleccionada")

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
            self.clear_btn.configure(state="normal")
        else:
            show_validation_error("El archivo seleccionado no es una imagen válida")

    def _clear_image(self):
        """
        Quita la imagen seleccionada
        """
        self.selected_image_path = None
        self._update_preview()
        self.clear_btn.configure(state="disabled")

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
            self._show_image_preview()
        else:
            self._show_no_image_message()

    def _clear_preview_content(self):
        """
        Limpia el contenido actual de la vista previa
        """
        for widget in self.preview_frame.winfo_children():
            widget.destroy()

    def _show_image_preview(self):
        """
        Muestra la vista previa de la imagen seleccionada
        """
        try:
            self._load_and_display_image()
        except Exception as e:
            print(f"Error mostrando preview: {e}")
            self._show_no_image_message("Error al cargar la imagen")

    def _load_and_display_image(self):
        """
        Carga y muestra la imagen en el preview
        """
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

            # Mostrar info de la imagen
            self._show_image_info()

    def _show_image_info(self):
        """
        Muestra información de la imagen seleccionada
        """
        filename = os.path.basename(self.selected_image_path)
        info_label = self.style_manager.create_styled_label(
            self.preview_frame,
            f"📷 {filename}",
            "small"
        )
        info_label.configure(bg=self.style_manager.colors["bg_card"])
        info_label.pack()

    def _show_no_image_message(self, message="No hay imagen seleccionada"):
        """
        Muestra un mensaje cuando no hay imagen

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
            self.clear_btn.configure(state="normal")
        else:
            self._clear_image()

    def clear(self):
        """
        Limpia la imagen seleccionada
        """
        self._clear_image()


class TextInputComponent:
    """
    Componente especializado para entrada de texto con soporte para emoticones
    Maneja el área de texto y la integración con el menú de emoticones
    """

    def __init__(self, parent, style_manager: StyleManager):
        """
        Inicializa el componente de entrada de texto

        Args:
            parent: Widget padre donde se mostrará el componente
            style_manager: Gestor de estilos para mantener consistencia visual
        """
        self.style_manager = style_manager

        # Crear interfaz de texto
        self._create_text_interface(parent)

        # Crear menú de emoticones
        self._create_emoji_menu(parent)

    def _create_text_interface(self, parent):
        """
        Crea la interfaz de entrada de texto

        Args:
            parent: Widget padre
        """
        # Label
        text_label = self.style_manager.create_styled_label(
            parent,
            "Texto del mensaje:",
            "normal"
        )
        text_label.pack(anchor="w")

        # Área de texto
        self.text_widget = scrolledtext.ScrolledText(
            parent,
            height=4,
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

    def _create_emoji_menu(self, parent):
        """
        Crea el menú de emoticones integrado

        Args:
            parent: Widget padre
        """
        self.emoji_menu = EmojiMenu(parent, self.style_manager, self._insert_emoji)

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


class MessageInputSection:
    """
    Sección completa de entrada de mensajes
    Combina texto, imagen y emoticones en una interfaz unificada
    """

    def __init__(self, parent, style_manager: StyleManager, button_callback=None):
        """
        Inicializa la sección completa de entrada de mensajes

        Args:
            parent: Widget padre donde se mostrará la sección
            style_manager: Gestor de estilos para mantener consistencia visual
            button_callback: Función a ejecutar cuando se agrega un mensaje
        """
        self.style_manager = style_manager
        self.button_callback = button_callback

        # Crear frame principal
        self._create_main_frame(parent)

        # Crear componentes
        self._create_components()

        # Crear botón de acción
        if button_callback:
            self._create_action_button()

    def _create_main_frame(self, parent):
        """
        Crea el frame principal de la sección

        Args:
            parent: Widget padre
        """
        self.input_frame = self.style_manager.create_styled_labelframe(
            parent,
            "💬 Nuevo mensaje:"
        )
        self.input_frame.pack(fill=tk.X, padx=25, pady=(0, 20))

        # Contenido interno
        self.content_frame = self.style_manager.create_styled_frame(self.input_frame)
        self.content_frame.pack(fill=tk.X, padx=15, pady=15)

    def _create_components(self):
        """
        Crea los componentes de texto e imagen
        """
        # Componente de texto con emoticones
        self.text_component = TextInputComponent(
            self.content_frame,
            self.style_manager
        )

        # Componente de imagen
        self.image_component = ImagePreviewComponent(
            self.content_frame,
            self.style_manager
        )

    def _create_action_button(self):
        """
        Crea el botón de agregar mensaje
        """
        button = self.style_manager.create_styled_button(
            self.content_frame,
            "➕ Agregar Mensaje",
            self._on_button_clicked,
            "accent"
        )
        button.pack(pady=(10, 0))

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