# gui_messages_tab.py
"""
Pestaña principal de gestión de mensajes para el Bot de WhatsApp.
Este módulo coordina los componentes de entrada y edición de mensajes, proporcionando
una interfaz unificada para la gestión completa de mensajes con texto, imágenes y emoticones.
Reutiliza componentes modularizados para mantener el código limpio y escalable.
"""

import re
from gui_styles import StyleManager
from gui_components import (TabHeader, ListManager, show_validation_error,
                            show_success_message, show_error_message, show_confirmation_dialog)
from gui_message_input import MessageInputSection
from gui_message_dialog import MessageEditDialog


class MessageListManager:
    """
    Gestor especializado para la lista de mensajes con indicadores visuales
    Se encarga de formatear y mostrar mensajes con iconos informativos
    """

    def __init__(self, parent, style_manager: StyleManager, edit_callback=None, delete_callback=None):
        """
        Inicializa el gestor de lista de mensajes

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
            edit_callback: Función para editar mensajes
            delete_callback: Función para eliminar mensajes
        """
        self.style_manager = style_manager
        self.edit_callback = edit_callback
        self.delete_callback = delete_callback

        # Crear lista usando el componente base
        self.list_manager = ListManager(
            parent,
            style_manager,
            "Mensajes guardados:",
            delete_callback=delete_callback,
            edit_callback=edit_callback
        )

        # Patrón para detectar emoticones
        self.emoji_pattern = self._create_emoji_pattern()

    def _create_emoji_pattern(self):
        """
        Crea el patrón regex para detectar emoticones

        Returns:
            re.Pattern: Patrón compilado para detectar emoticones
        """
        return re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticones faciales
            "\U0001F300-\U0001F5FF"  # símbolos & pictogramas
            "\U0001F680-\U0001F6FF"  # transporte & símbolos de mapa
            "\U0001F1E0-\U0001F1FF"  # banderas (iOS)
            "\U00002500-\U00002BEF"  # símbolos varios
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "\u2640-\u2642"
            "\u2600-\u2B55"
            "\u200d"
            "\u23cf"
            "\u23e9"
            "\u231a"
            "\ufe0f"  # variaciones de emoji
            "\u3030"
            "]+", flags=re.UNICODE)

    def update_messages_list(self, messages):
        """
        Actualiza la lista de mensajes con indicadores visuales

        Args:
            messages: Lista de mensajes del data manager
        """
        display_messages = []

        for i, message in enumerate(messages):
            display_text = self._create_message_display_text(message, i)
            display_messages.append(display_text)

        self.list_manager.clear_and_populate(display_messages)

    def _create_message_display_text(self, message, index):
        """
        Crea el texto de visualización para un mensaje

        Args:
            message: Datos del mensaje
            index: Índice del mensaje

        Returns:
            str: Texto formateado con indicadores
        """
        text = message.get("texto", "")
        has_image = message.get("imagen") is not None

        # Texto truncado para mejor visualización
        display_text = self._truncate_text(text, 40)

        # Agregar indicadores visuales
        indicators = self._get_message_indicators(text, has_image)

        # Formato: "número. texto + indicadores"
        return f"{index + 1}. {display_text}{indicators}"

    def _truncate_text(self, text, max_length):
        """
        Trunca el texto si es muy largo

        Args:
            text: Texto original
            max_length: Longitud máxima

        Returns:
            str: Texto truncado con "..." si es necesario
        """
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."

    def _get_message_indicators(self, text, has_image):
        """
        Obtiene los indicadores visuales para un mensaje

        Args:
            text: Texto del mensaje
            has_image: Si el mensaje tiene imagen

        Returns:
            str: Indicadores concatenados
        """
        indicators = ""

        if has_image:
            indicators += " 📷"

        if self._has_emojis(text):
            indicators += " 😀"

        return indicators

    def _has_emojis(self, text):
        """
        Detecta si el texto contiene emoticones

        Args:
            text: Texto a analizar

        Returns:
            bool: True si contiene emoticones
        """
        return bool(self.emoji_pattern.search(text))

    def get_selection(self):
        """
        Obtiene el elemento seleccionado de la lista

        Returns:
            tuple: (índice, texto_mostrado) o (None, None)
        """
        return self.list_manager.get_selection()


class MessageOperationsHandler:
    """
    Manejador especializado para operaciones CRUD de mensajes
    Centraliza la lógica de negocio para agregar, editar y eliminar mensajes
    """

    def __init__(self, data_manager, input_section, list_manager):
        """
        Inicializa el manejador de operaciones

        Args:
            data_manager: Gestor de datos
            input_section: Sección de entrada de mensajes
            list_manager: Gestor de lista de mensajes
        """
        self.data_manager = data_manager
        self.input_section = input_section
        self.list_manager = list_manager

    def add_message(self):
        """
        Agrega un nuevo mensaje al sistema
        """
        # Validar entrada
        is_valid, error_message = self.input_section.validate_input()
        if not is_valid:
            show_validation_error(error_message)
            self.input_section.focus_text()
            return

        # Obtener datos
        text, image_path = self.input_section.get_values()

        # Intentar agregar mensaje
        if self.data_manager.add_message(text, image_path):
            self._on_message_added_successfully(image_path)
        else:
            show_error_message("Error al agregar el mensaje")

    def _on_message_added_successfully(self, image_path):
        """
        Maneja el flujo exitoso de adición de mensaje

        Args:
            image_path: Ruta de imagen (si existe)
        """
        # Limpiar formulario
        self.input_section.clear_values()
        self.input_section.focus_text()

        # Actualizar lista
        self._refresh_messages_list()

        # Mostrar mensaje apropiado
        if image_path:
            show_success_message("Mensaje con imagen agregado correctamente")
        else:
            show_success_message("Mensaje agregado correctamente")

    def edit_message(self):
        """
        Edita el mensaje seleccionado
        """
        # Obtener selección
        index, display_text = self.list_manager.get_selection()

        if index is None:
            show_validation_error("Por favor selecciona un mensaje para editar")
            return

        # Obtener datos del mensaje
        message_data = self.data_manager.get_message_by_index(index)
        if not message_data:
            show_error_message("Mensaje no encontrado")
            return

        # Mostrar diálogo de edición
        self._show_edit_dialog(message_data, index)

    def _show_edit_dialog(self, message_data, index):
        """
        Muestra el diálogo de edición de mensaje

        Args:
            message_data: Datos del mensaje
            index: Índice del mensaje
        """

        def on_edit_complete(new_data):
            if new_data:
                success = self.data_manager.update_message(
                    index,
                    new_data['texto'],
                    new_data.get('nueva_imagen')
                )
                if success:
                    self._refresh_messages_list()
                    show_success_message("Mensaje actualizado correctamente")
                else:
                    show_error_message("Error al actualizar el mensaje")

        # Crear diálogo (necesitamos el toplevel, lo obtenemos de input_section)
        parent_window = self.input_section.input_frame.winfo_toplevel()

        MessageEditDialog(
            parent_window,
            self.input_section.style_manager,
            message_data,
            self.data_manager,
            on_edit_complete
        )

    def delete_message(self):
        """
        Elimina el mensaje seleccionado
        """
        index, display_text = self.list_manager.get_selection()

        if index is None:
            show_validation_error("Por favor selecciona un mensaje para eliminar")
            return

        # Confirmar eliminación
        if show_confirmation_dialog(
                "¿Eliminar el mensaje seleccionado?\n\nSi tiene imagen asociada, también se eliminará."):
            self._perform_message_deletion(index)

    def _perform_message_deletion(self, index):
        """
        Ejecuta la eliminación del mensaje

        Args:
            index: Índice del mensaje a eliminar
        """
        if self.data_manager.remove_message(index):
            self._refresh_messages_list()
            show_success_message("Mensaje eliminado correctamente")
        else:
            show_error_message("Error al eliminar el mensaje")

    def _refresh_messages_list(self):
        """
        Actualiza la lista de mensajes mostrados
        """
        messages = self.data_manager.get_messages()
        self.list_manager.update_messages_list(messages)


class MessagesTab:
    """
    Pestaña principal de gestión de mensajes
    Coordina todos los componentes para proporcionar funcionalidad completa
    """

    def __init__(self, parent, style_manager: StyleManager, data_manager):
        """
        Inicializa la pestaña de gestión de mensajes

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
            data_manager: Gestor de datos
        """
        self.style_manager = style_manager
        self.data_manager = data_manager

        # Frame principal
        self.frame = style_manager.create_styled_frame(parent)

        # Crear componentes
        self._create_components()

        # Crear manejador de operaciones
        self._create_operations_handler()

        # Cargar datos iniciales
        self._load_initial_data()

    def _create_components(self):
        """
        Crea todos los componentes de la pestaña
        """
        # Cabecera
        self._create_header()

        # Sección de entrada
        self._create_input_section()

        # Lista de mensajes
        self._create_list_section()

    def _create_header(self):
        """
        Crea la cabecera de la pestaña
        """
        TabHeader(
            self.frame,
            self.style_manager,
            "Gestión de Mensajes",
            "Crea y administra mensajes con texto e imágenes"
        )

    def _create_input_section(self):
        """
        Crea la sección de entrada reutilizando el componente modularizado
        """
        self.input_section = MessageInputSection(
            self.frame,
            self.style_manager,
            button_callback=self._on_add_message_clicked
        )

    def _create_list_section(self):
        """
        Crea la sección de lista de mensajes
        """
        self.list_manager = MessageListManager(
            self.frame,
            self.style_manager,
            edit_callback=self._on_edit_message_clicked,
            delete_callback=self._on_delete_message_clicked
        )

    def _create_operations_handler(self):
        """
        Crea el manejador de operaciones CRUD
        """
        self.operations_handler = MessageOperationsHandler(
            self.data_manager,
            self.input_section,
            self.list_manager
        )

    def _load_initial_data(self):
        """
        Carga los datos iniciales en la interfaz
        """
        self._refresh_messages()

    def _on_add_message_clicked(self):
        """
        Callback cuando se hace clic en agregar mensaje
        """
        self.operations_handler.add_message()

    def _on_edit_message_clicked(self):
        """
        Callback cuando se hace clic en editar mensaje
        """
        self.operations_handler.edit_message()

    def _on_delete_message_clicked(self):
        """
        Callback cuando se hace clic en eliminar mensaje
        """
        self.operations_handler.delete_message()

    def _refresh_messages(self):
        """
        Actualiza la lista de mensajes mostrados
        """
        messages = self.data_manager.get_messages()
        self.list_manager.update_messages_list(messages)

    def get_frame(self):
        """
        Obtiene el frame principal de la pestaña

        Returns:
            tk.Frame: Frame contenedor de la pestaña
        """
        return self.frame

    def on_show(self):
        """
        Callback ejecutado cuando se muestra la pestaña
        Actualiza los datos mostrados
        """
        self._refresh_messages()