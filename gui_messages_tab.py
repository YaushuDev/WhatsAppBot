# gui_messages_tab.py
"""
Pestaña principal de gestión de mensajes para el Bot de WhatsApp.
Este módulo coordina los componentes de entrada y edición de mensajes con layout horizontal
compacto donde la creación está a la izquierda y la lista a la derecha. Proporciona una
interfaz unificada para la gestión completa de mensajes con texto, imágenes y emoticones
optimizada para pantallas de 1000x600px.
ACTUALIZADO: Restricción del primer mensaje sin imágenes debido a error de WhatsApp Web.
"""

import re
import tkinter as tk
from gui_styles import StyleManager
from gui_components import (ListManager, show_validation_error,
                            show_success_message, show_error_message, show_confirmation_dialog,
                            show_first_message_image_restriction)  # NUEVO: Importar restricción
from gui_message_input import MessageInputSection
from gui_message_dialog import MessageEditDialog


class MessageListManager:
    """
    Gestor especializado para la lista de mensajes con indicadores visuales
    Se encarga de formatear y mostrar mensajes con iconos informativos
    Optimizado para layout horizontal compacto
    ACTUALIZADO: Indicadores visuales para envío conjunto/separado
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

        # Crear lista usando el componente base con altura compacta
        self.list_manager = ListManager(
            parent,
            style_manager,
            "Mensajes guardados:",
            delete_callback=delete_callback,
            edit_callback=edit_callback
        )

        # Ajustar para layout compacto
        self.list_manager.list_frame.pack_configure(padx=0, pady=(0, 8))

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
        Actualiza la lista de mensajes con indicadores visuales mejorados

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
        Crea el texto de visualización para un mensaje con indicadores mejorados

        Args:
            message: Datos del mensaje
            index: Índice del mensaje

        Returns:
            str: Texto formateado con indicadores
        """
        text = message.get("texto", "")
        has_image = message.get("imagen") is not None
        envio_conjunto = message.get("envio_conjunto", False)

        # Texto truncado para mejor visualización en layout compacto
        display_text = self._truncate_text(text, 35)  # Reducido de 40 a 35

        # NUEVO: Agregar indicadores visuales mejorados
        indicators = self._get_enhanced_message_indicators(text, has_image, envio_conjunto)

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

    def _get_enhanced_message_indicators(self, text, has_image, envio_conjunto):
        """
        Obtiene los indicadores visuales mejorados para un mensaje

        Args:
            text: Texto del mensaje
            has_image: Si el mensaje tiene imagen
            envio_conjunto: Si usa envío conjunto

        Returns:
            str: Indicadores concatenados
        """
        indicators = ""

        # NUEVO: Indicadores visuales específicos para modo de envío
        if has_image and text:
            if envio_conjunto:
                indicators += " 🖼️📝"  # Imagen con caption (envío conjunto)
            else:
                indicators += " 📷+📝"  # Imagen y texto separados
        elif has_image:
            indicators += " 📷"  # Solo imagen
        # Si solo hay texto, no agregar indicador de imagen

        # Indicador de emoticones
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
    ACTUALIZADO: Validaciones para restricción del primer mensaje sin imágenes
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
        ACTUALIZADO: Agrega un nuevo mensaje con validación de restricción del primer mensaje
        """
        # Validar entrada
        is_valid, error_message = self.input_section.validate_input()
        if not is_valid:
            show_validation_error(error_message)
            self.input_section.focus_text()
            return

        # Obtener datos incluyendo modo de envío
        text, image_path, envio_conjunto = self.input_section.get_values()

        # NUEVO: Validar restricción del primer mensaje
        current_messages = self.data_manager.get_messages()
        is_first_message = len(current_messages) == 0
        has_image = image_path is not None

        if is_first_message and has_image:
            show_first_message_image_restriction()
            return  # No continuar con la operación

        # Intentar agregar mensaje con nuevo parámetro
        if self.data_manager.add_message(text, image_path, envio_conjunto):
            self._on_message_added_successfully(image_path, envio_conjunto)
        else:
            show_error_message("Error al agregar el mensaje")

    def _on_message_added_successfully(self, image_path, envio_conjunto):
        """
        Maneja el flujo exitoso de adición de mensaje con indicadores mejorados

        Args:
            image_path: Ruta de imagen (si existe)
            envio_conjunto: Si usa envío conjunto
        """
        # Limpiar formulario
        self.input_section.clear_values()
        self.input_section.focus_text()

        # Actualizar lista
        self._refresh_messages_list()

        # NUEVO: Mostrar mensaje apropiado según el modo de envío
        if image_path:
            if envio_conjunto:
                show_success_message("Mensaje con imagen como caption agregado correctamente")
            else:
                show_success_message("Mensaje con imagen (envío separado) agregado correctamente")
        else:
            show_success_message("Mensaje agregado correctamente")

    def edit_message(self):
        """
        ACTUALIZADO: Edita el mensaje seleccionado con validación de restricción del primer mensaje
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

        # NUEVO: Preparar información para validación en el callback
        def on_edit_complete(new_data):
            if new_data:
                # NUEVO: Validar restricción del primer mensaje antes de actualizar
                is_first_message = index == 0
                is_adding_image = new_data.get('imagen_cambio', False) and new_data.get('nueva_imagen') not in [None, ""]

                if is_first_message and is_adding_image:
                    show_first_message_image_restriction()
                    return  # No continuar con la actualización

                # Continuar con la actualización normal
                success = self.data_manager.update_message(
                    index,
                    new_data['texto'],
                    new_data.get('nueva_imagen'),
                    new_data.get('envio_conjunto')
                )
                if success:
                    self._refresh_messages_list()

                    # NUEVO: Mensaje específico según modo de envío
                    envio_conjunto = new_data.get('envio_conjunto', False)
                    has_image = new_data.get('nueva_imagen') is not None or message_data.get('imagen') is not None

                    if has_image and envio_conjunto:
                        show_success_message("Mensaje actualizado (modo conjunto: imagen con caption)")
                    elif has_image:
                        show_success_message("Mensaje actualizado (modo separado: imagen y texto)")
                    else:
                        show_success_message("Mensaje actualizado correctamente")
                else:
                    show_error_message("Error al actualizar el mensaje")

        # Mostrar diálogo de edición
        self._show_edit_dialog(message_data, index, on_edit_complete)

    def _show_edit_dialog(self, message_data, index, on_edit_complete):
        """
        Muestra el diálogo de edición de mensaje

        Args:
            message_data: Datos del mensaje
            index: Índice del mensaje
            on_edit_complete: Callback para completar edición
        """
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

        # NUEVO: Mejorar mensaje de confirmación con información del tipo
        message_data = self.data_manager.get_message_by_index(index)
        confirmation_text = "¿Eliminar el mensaje seleccionado?"

        if message_data:
            has_image = message_data.get('imagen') is not None
            envio_conjunto = message_data.get('envio_conjunto', False)

            if has_image:
                if envio_conjunto:
                    confirmation_text += "\n\n📷📝 Incluye imagen con caption que también se eliminará."
                else:
                    confirmation_text += "\n\n📷+📝 Incluye imagen que también se eliminará."
            else:
                confirmation_text += "\n\n📝 Solo contiene texto."

        # Confirmar eliminación
        if show_confirmation_dialog(confirmation_text):
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
    Pestaña principal de gestión de mensajes con layout horizontal compacto
    Coordina todos los componentes para proporcionar funcionalidad completa optimizada para 1000x600px
    ACTUALIZADO: Soporte completo para envío conjunto de imagen con texto como caption y restricción del primer mensaje
    """

    def __init__(self, parent, style_manager: StyleManager, data_manager):
        """
        Inicializa la pestaña de gestión de mensajes con layout horizontal

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
            data_manager: Gestor de datos
        """
        self.style_manager = style_manager
        self.data_manager = data_manager

        # Frame principal
        self.frame = style_manager.create_styled_frame(parent)

        # Crear layout horizontal
        self._create_horizontal_layout()

        # Crear manejador de operaciones
        self._create_operations_handler()

        # Cargar datos iniciales
        self._load_initial_data()

    def _create_horizontal_layout(self):
        """
        Crea el layout horizontal principal: entrada | lista
        """
        # Header compacto
        self._create_compact_header()

        # Container principal con layout horizontal
        main_container = self.style_manager.create_styled_frame(self.frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        # Columna izquierda: Entrada de mensajes (40% del ancho)
        self.left_column = self.style_manager.create_styled_frame(main_container)
        self.left_column.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 8))
        self.left_column.configure(width=400)  # Ancho fijo para entrada
        self.left_column.pack_propagate(False)

        # Columna derecha: Lista de mensajes (60% del ancho)
        self.right_column = self.style_manager.create_styled_frame(main_container)
        self.right_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))

        # Crear componentes en cada columna
        self._create_input_section()
        self._create_list_section()

    def _create_compact_header(self):
        """
        Crea la cabecera compacta de la pestaña con información del envío conjunto
        """
        # Container del header con padding reducido
        header_container = self.style_manager.create_styled_frame(self.frame)
        header_container.pack(fill=tk.X, padx=12, pady=(12, 8))

        # Título
        title_label = self.style_manager.create_styled_label(header_container, "Gestión de Mensajes", "title")
        title_label.pack(anchor="w")

        # Descripción más concisa
        desc_label = self.style_manager.create_styled_label(
            header_container,
            "Crea y administra mensajes con texto e imágenes",
            "secondary"
        )
        desc_label.pack(anchor="w", pady=(4, 0))

        # Línea separadora más sutil
        separator = self.style_manager.create_styled_frame(header_container, "accent")
        separator.configure(height=1)
        separator.pack(fill=tk.X, pady=(8, 0))

    def _create_input_section(self):
        """
        Crea la sección de entrada en la columna izquierda
        """
        self.input_section = MessageInputSection(
            self.left_column,
            self.style_manager,
            button_callback=self._on_add_message_clicked
        )

        # Ajustar padding para layout compacto
        self.input_section.input_frame.pack_configure(padx=0, pady=(0, 8))

    def _create_list_section(self):
        """
        Crea la sección de lista en la columna derecha
        """
        self.list_manager = MessageListManager(
            self.right_column,
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

    def get_statistics(self):
        """
        NUEVO: Obtiene estadísticas detalladas de los mensajes

        Returns:
            dict: Estadísticas de los mensajes
        """
        messages = self.data_manager.get_messages()

        stats = {
            'total': len(messages),
            'solo_texto': 0,
            'solo_imagen': 0,
            'texto_imagen_separado': 0,
            'texto_imagen_conjunto': 0,
            'con_emoticones': 0
        }

        for message in messages:
            text = message.get('texto', '')
            has_image = message.get('imagen') is not None
            envio_conjunto = message.get('envio_conjunto', False)
            has_emojis = bool(self.list_manager.emoji_pattern.search(text)) if text else False

            if has_emojis:
                stats['con_emoticones'] += 1

            if has_image and text:
                if envio_conjunto:
                    stats['texto_imagen_conjunto'] += 1
                else:
                    stats['texto_imagen_separado'] += 1
            elif has_image:
                stats['solo_imagen'] += 1
            elif text:
                stats['solo_texto'] += 1

        return stats