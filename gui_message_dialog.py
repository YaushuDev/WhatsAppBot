# gui_message_dialog.py
"""
Diálogos de edición de mensajes para el Bot de WhatsApp
Este módulo implementa los diálogos modales para editar mensajes existentes,
reutilizando los componentes de entrada de texto e imagen. Proporciona una
interfaz intuitiva para modificar mensajes con validación y preview en tiempo real.
"""

import tkinter as tk
import os
from gui_styles import StyleManager
from gui_message_input import TextInputComponent, ImagePreviewComponent
from gui_components import show_validation_error


class DialogWindowManager:
    """
    Gestor especializado para configuración y manejo de ventanas modales
    Se encarga de crear, centrar y configurar ventanas de diálogo
    """

    def __init__(self, parent, style_manager: StyleManager, title="Diálogo", size="600x700"):
        """
        Inicializa el gestor de ventana modal

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
            title: Título de la ventana
            size: Tamaño de la ventana en formato "WxH"
        """
        self.style_manager = style_manager
        self.parent = parent
        self.title = title
        self.size = size
        self.dialog = None

        # Crear la ventana
        self._create_modal_window()

    def _create_modal_window(self):
        """
        Crea y configura la ventana modal
        """
        self.dialog = tk.Toplevel(self.parent)
        self._configure_window_properties()
        self._make_modal()
        self._center_window()

    def _configure_window_properties(self):
        """
        Configura las propiedades básicas de la ventana
        """
        self.style_manager.configure_window(
            self.dialog,
            self.title,
            self.size
        )

    def _make_modal(self):
        """
        Hace la ventana modal (bloquea interacción con ventana padre)
        """
        self.dialog.grab_set()
        self.dialog.transient(self.parent)

    def _center_window(self):
        """
        Centra la ventana en la pantalla
        """
        self.dialog.update_idletasks()

        # Obtener dimensiones
        width = int(self.size.split('x')[0])
        height = int(self.size.split('x')[1])

        # Calcular posición central
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)

        self.dialog.geometry(f"{width}x{height}+{x}+{y}")

    def get_dialog(self):
        """
        Obtiene la ventana de diálogo

        Returns:
            tk.Toplevel: Ventana de diálogo
        """
        return self.dialog

    def close(self):
        """
        Cierra la ventana de diálogo
        """
        if self.dialog:
            self.dialog.destroy()

    def bind_escape(self, callback):
        """
        Vincula la tecla Escape a un callback

        Args:
            callback: Función a ejecutar al presionar Escape
        """
        self.dialog.bind("<Escape>", lambda e: callback())


class DialogButtonsSection:
    """
    Sección especializada para botones de acción en diálogos
    Maneja los botones de guardar, cancelar y sus eventos
    """

    def __init__(self, parent, style_manager: StyleManager, save_callback=None, cancel_callback=None):
        """
        Inicializa la sección de botones

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
            save_callback: Función para guardar cambios
            cancel_callback: Función para cancelar
        """
        self.style_manager = style_manager
        self.save_callback = save_callback
        self.cancel_callback = cancel_callback

        # Crear interfaz de botones
        self._create_buttons_interface(parent)

    def _create_buttons_interface(self, parent):
        """
        Crea la interfaz de botones de acción

        Args:
            parent: Widget padre
        """
        # Frame para botones
        self.buttons_frame = self.style_manager.create_styled_frame(parent)
        self.buttons_frame.pack(fill=tk.X, pady=(20, 0))

        # Crear botones
        self._create_save_button()
        self._create_cancel_button()

    def _create_save_button(self):
        """
        Crea el botón de guardar
        """
        self.save_btn = self.style_manager.create_styled_button(
            self.buttons_frame,
            "💾 Guardar",
            self._on_save_clicked,
            "success"
        )
        self.save_btn.pack(side=tk.LEFT, padx=(0, 10))

    def _create_cancel_button(self):
        """
        Crea el botón de cancelar
        """
        self.cancel_btn = self.style_manager.create_styled_button(
            self.buttons_frame,
            "❌ Cancelar",
            self._on_cancel_clicked,
            "error"
        )
        self.cancel_btn.pack(side=tk.LEFT)

    def _on_save_clicked(self):
        """
        Maneja el clic en el botón guardar
        """
        if self.save_callback:
            self.save_callback()

    def _on_cancel_clicked(self):
        """
        Maneja el clic en el botón cancelar
        """
        if self.cancel_callback:
            self.cancel_callback()

    def enable_save(self, enabled=True):
        """
        Habilita o deshabilita el botón de guardar

        Args:
            enabled: True para habilitar, False para deshabilitar
        """
        state = "normal" if enabled else "disabled"
        self.save_btn.configure(state=state)


class MessageEditDialogContent:
    """
    Contenido principal del diálogo de edición de mensajes
    Reutiliza componentes de entrada y maneja la lógica específica de edición
    """

    def __init__(self, parent, style_manager: StyleManager, message_data, data_manager):
        """
        Inicializa el contenido del diálogo de edición

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
            message_data: Datos del mensaje a editar
            data_manager: Gestor de datos para manejo de imágenes
        """
        self.style_manager = style_manager
        self.data_manager = data_manager
        self.message_data = message_data
        self.original_image_filename = message_data.get('imagen')

        # Crear contenido
        self._create_dialog_content(parent)

        # Cargar datos existentes
        self._load_existing_data()

    def _create_dialog_content(self, parent):
        """
        Crea el contenido principal del diálogo

        Args:
            parent: Widget padre
        """
        # Frame principal del contenido
        self.main_frame = self.style_manager.create_styled_frame(parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Crear secciones
        self._create_title_section()
        self._create_text_section()
        self._create_image_section()

    def _create_title_section(self):
        """
        Crea la sección del título del diálogo
        """
        title_label = self.style_manager.create_styled_label(
            self.main_frame,
            "Editar Mensaje",
            "heading"
        )
        title_label.pack(pady=(0, 20))

    def _create_text_section(self):
        """
        Crea la sección de edición de texto reutilizando el componente
        """
        # Label personalizado para el contexto de edición
        text_label = self.style_manager.create_styled_label(
            self.main_frame,
            "Texto del mensaje:",
            "normal"
        )
        text_label.pack(anchor="w")

        # Reutilizar componente de texto (sin el label, ya que lo creamos arriba)
        self.text_component = self._create_text_component_for_dialog()

    def _create_text_component_for_dialog(self):
        """
        Crea un componente de texto adaptado para el diálogo

        Returns:
            TextInputComponent: Componente de texto configurado
        """
        # Crear frame temporal para el componente
        temp_frame = self.style_manager.create_styled_frame(self.main_frame)
        temp_frame.pack(fill=tk.X, pady=(5, 15))

        # Crear componente personalizado sin label (ya tenemos uno)
        text_component = TextInputComponent.__new__(TextInputComponent)
        text_component.style_manager = self.style_manager

        # Crear solo el área de texto y emoji menu
        text_component._create_text_interface = lambda parent: self._create_dialog_text_area(text_component, parent)
        text_component.__init__(temp_frame, self.style_manager)

        return text_component

    def _create_dialog_text_area(self, text_component, parent):
        """
        Crea el área de texto adaptada para el diálogo

        Args:
            text_component: Componente de texto
            parent: Widget padre
        """
        # Área de texto con altura mayor para edición
        text_component.text_widget = tk.Text(
            parent,
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
        text_component.text_widget.pack(fill=tk.X)

        # Agregar scrollbar para texto largo
        scrollbar = tk.Scrollbar(parent, orient="vertical", command=text_component.text_widget.yview)
        text_component.text_widget.configure(yscrollcommand=scrollbar.set)

    def _create_image_section(self):
        """
        Crea la sección de edición de imagen reutilizando el componente
        """
        # Agregar espacio superior para separar de la sección de texto
        spacer = self.style_manager.create_styled_frame(self.main_frame)
        spacer.pack(pady=(10, 0))

        # Reutilizar componente de imagen (ya incluye su propio label)
        self.image_component = ImagePreviewComponent(
            self.main_frame,
            self.style_manager
        )

        # Personalizar botones para el contexto de edición
        self._customize_image_buttons()

    def _customize_image_buttons(self):
        """
        Personaliza los botones de imagen para el contexto de edición
        """
        # Cambiar texto de los botones para mayor claridad en el diálogo
        self.image_component.select_btn.configure(text="📁 Cambiar")
        self.image_component.clear_btn.configure(
            text="🗑️ Eliminar",
            fg=self.style_manager.colors["text_primary"]  # Mantener texto blanco en botón rojo
        )

    def _load_existing_data(self):
        """
        Carga los datos existentes del mensaje en los componentes
        """
        # Cargar texto
        existing_text = self.message_data.get('texto', '')
        self.text_component.set_text(existing_text)

        # Cargar imagen si existe
        self._load_existing_image()

        # Poner foco en el texto
        self.text_component.focus()

    def _load_existing_image(self):
        """
        Carga la imagen existente del mensaje si está disponible
        """
        if self.original_image_filename:
            current_image_path = self.data_manager.get_image_path(self.original_image_filename)
            if current_image_path and os.path.exists(current_image_path):
                self.image_component.set_image_path(current_image_path)

    def get_edited_data(self):
        """
        Obtiene los datos editados del mensaje

        Returns:
            dict: Diccionario con los datos editados
        """
        text = self.text_component.get_text()
        new_image_path = self.image_component.get_image_path()

        # Determinar si la imagen cambió
        original_image_path = None
        if self.original_image_filename:
            original_image_path = self.data_manager.get_image_path(self.original_image_filename)

        image_changed = new_image_path != original_image_path

        return {
            'texto': text,
            'nueva_imagen': new_image_path if image_changed else None,
            'imagen_cambio': image_changed
        }

    def validate_data(self):
        """
        Valida los datos editados

        Returns:
            tuple: (is_valid, error_message)
        """
        if self.text_component.is_empty():
            return False, "El texto del mensaje es obligatorio"

        return True, ""

    def get_main_frame(self):
        """
        Obtiene el frame principal del contenido

        Returns:
            tk.Frame: Frame principal
        """
        return self.main_frame


class MessageEditDialog:
    """
    Diálogo principal para editar mensajes
    Coordina todos los componentes y maneja el flujo de edición
    """

    def __init__(self, parent, style_manager: StyleManager, message_data, data_manager, callback):
        """
        Inicializa el diálogo de edición de mensaje

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
            message_data: Datos del mensaje a editar
            data_manager: Gestor de datos
            callback: Función callback para los datos actualizados
        """
        self.style_manager = style_manager
        self.data_manager = data_manager
        self.callback = callback
        self.result = None

        # Crear componentes del diálogo
        self._create_dialog_components(parent, message_data)

        # Configurar eventos
        self._setup_dialog_events()

    def _create_dialog_components(self, parent, message_data):
        """
        Crea todos los componentes del diálogo

        Args:
            parent: Widget padre
            message_data: Datos del mensaje
        """
        # Gestor de ventana
        self.window_manager = DialogWindowManager(
            parent,
            self.style_manager,
            "Editar Mensaje",
            "600x700"
        )

        # Contenido del diálogo
        self.content = MessageEditDialogContent(
            self.window_manager.get_dialog(),
            self.style_manager,
            message_data,
            self.data_manager
        )

        # Botones de acción
        self.buttons = DialogButtonsSection(
            self.content.get_main_frame(),
            self.style_manager,
            save_callback=self._save_changes,
            cancel_callback=self._cancel_dialog
        )

    def _setup_dialog_events(self):
        """
        Configura los eventos del diálogo
        """
        # Tecla Escape para cancelar
        self.window_manager.bind_escape(self._cancel_dialog)

    def _save_changes(self):
        """
        Guarda los cambios y cierra el diálogo
        """
        # Validar datos
        is_valid, error_message = self.content.validate_data()
        if not is_valid:
            show_validation_error(error_message)
            return

        # Obtener datos editados
        self.result = self.content.get_edited_data()

        # Ejecutar callback y cerrar
        if self.callback:
            self.callback(self.result)

        self._close_dialog()

    def _cancel_dialog(self):
        """
        Cancela la edición y cierra el diálogo
        """
        self.result = None
        self._close_dialog()

    def _close_dialog(self):
        """
        Cierra el diálogo de forma segura
        """
        self.window_manager.close()

    def get_result(self):
        """
        Obtiene el resultado de la edición

        Returns:
            dict: Datos editados o None si se canceló
        """
        return self.result