# gui_message_dialog.py
"""
Diálogos de edición de mensajes para el Bot de WhatsApp
Este módulo implementa los diálogos modales para editar mensajes existentes,
reutilizando los componentes de entrada de texto e imagen. Proporciona una
interfaz intuitiva para modificar mensajes con validación y preview en tiempo real.
ACTUALIZADO: Soporte para cambiar modo de envío conjunto/separado en edición.
CORREGIDO: Manejo correcto de eliminación de imágenes durante la edición.
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

    def __init__(self, parent, style_manager: StyleManager, title="Diálogo", size="600x750"):
        """
        Inicializa el gestor de ventana modal

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
            title: Título de la ventana
            size: Tamaño de la ventana en formato "WxH" (aumentado para el selector)
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


class SendModeDialogSelector:
    """
    NUEVO: Selector de modo de envío específico para diálogos de edición
    Reutiliza la lógica pero adaptado para el contexto de edición
    """

    def __init__(self, parent, style_manager: StyleManager):
        """
        Inicializa el selector de modo de envío para diálogos

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
        """
        self.style_manager = style_manager
        self.envio_conjunto = tk.BooleanVar(value=False)  # Por defecto separado

        # Crear interfaz (inicialmente oculta)
        self._create_dialog_selector_interface(parent)
        self._hide_selector()

    def _create_dialog_selector_interface(self, parent):
        """
        Crea la interfaz del selector adaptada para diálogos

        Args:
            parent: Widget padre
        """
        # Frame principal
        self.selector_frame = self.style_manager.create_styled_frame(parent)
        self.selector_frame.pack(fill=tk.X, pady=(10, 0))

        # Container interno con estilo de tarjeta
        container = self.style_manager.create_styled_frame(self.selector_frame, "card")
        container.configure(relief="solid", bd=1)
        container.pack(fill=tk.X, padx=5, pady=5)

        # Título explicativo específico para edición
        title_label = self.style_manager.create_styled_label(
            container,
            "📤 Cambiar modo de envío:",
            "small"
        )
        title_label.configure(bg=self.style_manager.colors["bg_card"])
        title_label.pack(anchor="w", padx=8, pady=(8, 4))

        # Descripción informativa
        info_label = self.style_manager.create_styled_label(
            container,
            "Solo disponible cuando hay imagen Y texto",
            "muted"
        )
        info_label.configure(bg=self.style_manager.colors["bg_card"])
        info_label.pack(anchor="w", padx=8, pady=(0, 4))

        # Opciones de envío
        options_frame = self.style_manager.create_styled_frame(container, "card")
        options_frame.pack(fill=tk.X, padx=8, pady=(0, 8))

        # Opción 1: Envío separado
        separated_radio = tk.Radiobutton(
            options_frame,
            text="📷+📝 Separado (imagen primero, luego texto)",
            variable=self.envio_conjunto,
            value=False,
            font=self.style_manager.fonts["small"],
            bg=self.style_manager.colors["bg_card"],
            fg=self.style_manager.colors["text_primary"],
            selectcolor=self.style_manager.colors["bg_accent"],
            activebackground=self.style_manager.colors["bg_card"],
            activeforeground=self.style_manager.colors["text_primary"],
            border=0,
            highlightthickness=0
        )
        separated_radio.pack(anchor="w", pady=(0, 4))

        # Opción 2: Envío conjunto
        together_radio = tk.Radiobutton(
            options_frame,
            text="🖼️📝 Conjunto (imagen con texto como caption)",
            variable=self.envio_conjunto,
            value=True,
            font=self.style_manager.fonts["small"],
            bg=self.style_manager.colors["bg_card"],
            fg=self.style_manager.colors["text_primary"],
            selectcolor=self.style_manager.colors["bg_accent"],
            activebackground=self.style_manager.colors["bg_card"],
            activeforeground=self.style_manager.colors["text_primary"],
            border=0,
            highlightthickness=0
        )
        together_radio.pack(anchor="w")

    def _show_selector(self):
        """
        Muestra el selector de modo de envío
        """
        self.selector_frame.pack(fill=tk.X, pady=(10, 0))

    def _hide_selector(self):
        """
        Oculta el selector de modo de envío
        """
        self.selector_frame.pack_forget()

    def update_visibility(self, has_text, has_image):
        """
        Actualiza la visibilidad del selector según el contenido

        Args:
            has_text: Si hay texto
            has_image: Si hay imagen
        """
        if has_text and has_image:
            self._show_selector()
        else:
            self._hide_selector()

    def get_envio_conjunto(self):
        """
        Obtiene el estado del envío conjunto

        Returns:
            bool: True si debe enviar junto, False si separado
        """
        return self.envio_conjunto.get()

    def set_envio_conjunto(self, value):
        """
        Establece el estado del envío conjunto

        Args:
            value: True para envío conjunto, False para separado
        """
        self.envio_conjunto.set(value)


class MessageEditDialogContent:
    """
    Contenido principal del diálogo de edición de mensajes
    Reutiliza componentes de entrada y maneja la lógica específica de edición
    ACTUALIZADO: Incluye selector de modo de envío conjunto/separado
    CORREGIDO: Manejo correcto de eliminación de imágenes
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

        # NUEVO: Crear selector de modo de envío
        self._create_send_mode_selector()

        # Cargar datos existentes
        self._load_existing_data()

        # NUEVO: Configurar callbacks para actualizar visibilidad
        self._setup_content_change_callbacks()

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

        # NUEVO: Bind para detectar cambios de texto en el diálogo
        text_component.text_widget.bind('<KeyRelease>', text_component._on_text_change)
        text_component.text_widget.bind('<ButtonRelease-1>', text_component._on_text_change)

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

    def _create_send_mode_selector(self):
        """
        NUEVO: Crea el selector de modo de envío para el diálogo
        """
        self.send_mode_selector = SendModeDialogSelector(
            self.main_frame,
            self.style_manager
        )

    def _setup_content_change_callbacks(self):
        """
        NUEVO: Configura callbacks para detectar cambios en contenido
        """
        # Callback para cambios en texto
        self.text_component.set_on_text_change_callback(self._update_send_mode_visibility)

        # Callback para cambios en imagen
        self.image_component.set_on_image_change_callback(self._update_send_mode_visibility)

        # Actualizar visibilidad inicial (se hará después de cargar datos)

    def _update_send_mode_visibility(self):
        """
        NUEVO: Actualiza la visibilidad del selector de modo de envío
        """
        has_text = not self.text_component.is_empty()
        has_image = self.image_component.get_image_path() is not None

        self.send_mode_selector.update_visibility(has_text, has_image)

    def _load_existing_data(self):
        """
        Carga los datos existentes del mensaje en los componentes
        ACTUALIZADO: Incluye carga del modo de envío
        """
        # Cargar texto
        existing_text = self.message_data.get('texto', '')
        self.text_component.set_text(existing_text)

        # Cargar imagen si existe
        self._load_existing_image()

        # NUEVO: Cargar modo de envío
        envio_conjunto = self.message_data.get('envio_conjunto', False)
        self.send_mode_selector.set_envio_conjunto(envio_conjunto)

        # NUEVO: Actualizar visibilidad después de cargar datos
        self._update_send_mode_visibility()

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
        CORREGIDO: Obtiene los datos editados del mensaje con manejo correcto de eliminación de imágenes
        ACTUALIZADO: Incluye el modo de envío

        Returns:
            dict: Diccionario con los datos editados
        """
        text = self.text_component.get_text()
        new_image_path = self.image_component.get_image_path()
        envio_conjunto = self.send_mode_selector.get_envio_conjunto()

        # CORREGIDO: Determinar cambios de imagen y manejo correcto de eliminación
        original_image_path = None
        if self.original_image_filename:
            original_image_path = self.data_manager.get_image_path(self.original_image_filename)

        # Lógica corregida para detectar y manejar cambios de imagen
        nueva_imagen_value = None
        imagen_cambio = False

        if self.original_image_filename and not new_image_path:
            # CASO 1: Había imagen y ahora no hay → Usuario eliminó la imagen
            nueva_imagen_value = ""  # String vacío indica eliminación explícita
            imagen_cambio = True
        elif not self.original_image_filename and new_image_path:
            # CASO 2: No había imagen y ahora hay → Usuario agregó imagen
            nueva_imagen_value = new_image_path
            imagen_cambio = True
        elif self.original_image_filename and new_image_path:
            # CASO 3: Había imagen y sigue habiendo → Verificar si cambió
            if new_image_path != original_image_path:
                # Usuario cambió por otra imagen
                nueva_imagen_value = new_image_path
                imagen_cambio = True
            # Si son iguales, no hay cambio (nueva_imagen_value = None, imagen_cambio = False)
        # CASO 4: No había imagen y sigue sin haber → No hay cambio (valores por defecto)

        return {
            'texto': text,
            'nueva_imagen': nueva_imagen_value,
            'imagen_cambio': imagen_cambio,
            'envio_conjunto': envio_conjunto
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
    ACTUALIZADO: Soporte completo para edición de modo de envío conjunto/separado
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
        # Gestor de ventana (ventana más alta para el selector)
        self.window_manager = DialogWindowManager(
            parent,
            self.style_manager,
            "Editar Mensaje",
            "600x750"  # Aumentado de 700 a 750 para el selector
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
        ACTUALIZADO: Incluye validación y manejo del modo de envío
        """
        # Validar datos
        is_valid, error_message = self.content.validate_data()
        if not is_valid:
            show_validation_error(error_message)
            return

        # Obtener datos editados (ahora incluye envio_conjunto)
        self.result = self.content.get_edited_data()

        # NUEVO: Mostrar información del modo de envío si cambió
        if 'envio_conjunto' in self.result:
            envio_conjunto = self.result['envio_conjunto']
            has_image = self.content.image_component.get_image_path() is not None
            has_text = not self.content.text_component.is_empty()

            if has_image and has_text:
                mode_text = "conjunto (caption)" if envio_conjunto else "separado"
                print(f"[Dialog] Modo de envío: {mode_text}")

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