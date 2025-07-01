# gui_config_tab.py
"""
Pestaña de configuración de selectores para el Bot de WhatsApp
Este módulo implementa la interfaz para configurar y actualizar dinámicamente los selectores
CSS/XPath utilizados por el bot, permitiendo adaptarse fácilmente a los cambios que hace
WhatsApp Web en su estructura. Incluye funcionalidades de edición, prueba y validación
de selectores con layout horizontal compacto optimizado para pantallas de 1000x600px.
"""

import tkinter as tk
from tkinter import scrolledtext
from gui_styles import StyleManager
from gui_components import (show_validation_error, show_success_message,
                            show_error_message, show_confirmation_dialog)
from whatsapp_utils import WhatsAppConstants


class SelectorEditSection:
    """
    Sección para editar un selector específico con validación y pruebas
    """

    def __init__(self, parent, style_manager: StyleManager, selector_key: str, selector_display_name: str):
        """
        Inicializa la sección de edición de selector

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
            selector_key: Clave del selector (ej: 'message_box')
            selector_display_name: Nombre para mostrar (ej: 'Campo de Mensaje')
        """
        self.style_manager = style_manager
        self.selector_key = selector_key
        self.selector_display_name = selector_display_name

        # Crear frame principal para este selector
        self.section_frame = self._create_section_frame(parent)

        # Crear componentes de la sección
        self._create_section_header()
        self._create_selector_list()
        self._create_action_buttons()

        # Cargar selectores actuales
        self._load_current_selectors()

    def _create_section_frame(self, parent):
        """
        Crea el frame principal de la sección

        Args:
            parent: Widget padre

        Returns:
            Frame de la sección
        """
        section_frame = self.style_manager.create_styled_labelframe(
            parent,
            f"🎯 {self.selector_display_name}"
        )
        section_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=(0, 15))

        return section_frame

    def _create_section_header(self):
        """
        Crea el header de la sección con información
        """
        content_frame = self.style_manager.create_styled_frame(self.section_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # Descripción de la sección
        description = self._get_selector_description()
        desc_label = self.style_manager.create_styled_label(
            content_frame,
            description,
            "small"
        )
        desc_label.pack(anchor="w", pady=(0, 8))

        # Label para la lista
        list_label = self.style_manager.create_styled_label(
            content_frame,
            "Selectores CSS/XPath (uno por línea):",
            "normal"
        )
        list_label.pack(anchor="w", pady=(0, 5))

        self.content_frame = content_frame

    def _get_selector_description(self):
        """
        Obtiene la descripción específica del selector

        Returns:
            Descripción del selector
        """
        descriptions = {
            'message_box': "Campo donde se escribe el mensaje antes de enviarlo",
            'attach_button': "Botón para adjuntar archivos (clip o plus icon)"
        }
        return descriptions.get(self.selector_key, f"Selectores para {self.selector_display_name}")

    def _create_selector_list(self):
        """
        Crea el área de texto para editar los selectores
        """
        # Área de texto con scroll
        self.selectors_text = scrolledtext.ScrolledText(
            self.content_frame,
            height=6,
            font=self.style_manager.fonts["small"],
            bg=self.style_manager.colors["bg_card"],
            fg=self.style_manager.colors["text_primary"],
            border=1,
            relief="solid",
            wrap=tk.NONE,  # Sin wrap para mejor lectura de selectores
            highlightthickness=1,
            highlightcolor=self.style_manager.colors["accent"],
            highlightbackground=self.style_manager.colors["border"],
            insertbackground=self.style_manager.colors["text_primary"]
        )
        self.selectors_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    def _create_action_buttons(self):
        """
        Crea los botones de acción para esta sección
        """
        buttons_frame = self.style_manager.create_styled_frame(self.content_frame)
        buttons_frame.pack(fill=tk.X, pady=(5, 0))

        # Botón probar selectores
        test_btn = self.style_manager.create_styled_button(
            buttons_frame,
            "🧪 Probar",
            self._test_selectors,
            "warning"
        )
        test_btn.pack(side=tk.LEFT, padx=(0, 8))

        # Botón guardar
        save_btn = self.style_manager.create_styled_button(
            buttons_frame,
            "💾 Guardar",
            self._save_selectors,
            "success"
        )
        save_btn.pack(side=tk.LEFT, padx=(0, 8))

        # Botón resetear
        reset_btn = self.style_manager.create_styled_button(
            buttons_frame,
            "🔄 Resetear",
            self._reset_selectors,
            "error"
        )
        reset_btn.pack(side=tk.RIGHT)

    def _load_current_selectors(self):
        """
        Carga los selectores actuales en el área de texto
        """
        try:
            current_selectors = WhatsAppConstants.get_selectors(self.selector_key)
            selectors_text = '\n'.join(current_selectors)

            self.selectors_text.delete(1.0, tk.END)
            self.selectors_text.insert(1.0, selectors_text)

        except Exception as e:
            show_error_message(f"Error cargando selectores para {self.selector_display_name}: {str(e)}")

    def _get_edited_selectors(self):
        """
        Obtiene los selectores editados desde el área de texto

        Returns:
            Lista de selectores o None si hay error
        """
        try:
            selectors_text = self.selectors_text.get(1.0, tk.END).strip()

            if not selectors_text:
                return []

            # Dividir por líneas y limpiar
            selectors = [line.strip() for line in selectors_text.split('\n') if line.strip()]

            # Validar que no estén vacíos
            if not selectors:
                show_validation_error(f"Debe especificar al menos un selector para {self.selector_display_name}")
                return None

            return selectors

        except Exception as e:
            show_error_message(f"Error procesando selectores: {str(e)}")
            return None

    def _test_selectors(self):
        """
        Prueba los selectores editados (simulación básica)
        """
        selectors = self._get_edited_selectors()
        if selectors is None:
            return

        try:
            # Validación básica de formato
            invalid_selectors = []

            for selector in selectors:
                # Verificaciones básicas de formato de selector CSS/XPath
                if len(selector) < 3:
                    invalid_selectors.append(f"'{selector}' es demasiado corto")
                elif selector.startswith('//') and not self._is_valid_xpath_format(selector):
                    invalid_selectors.append(f"'{selector}' no parece XPath válido")
                elif not selector.startswith('//') and not self._is_valid_css_format(selector):
                    invalid_selectors.append(f"'{selector}' no parece CSS válido")

            if invalid_selectors:
                error_msg = "Selectores con formato posiblemente incorrecto:\n\n" + '\n'.join(invalid_selectors)
                error_msg += "\n\n⚠️ Nota: Esta es solo una validación básica de formato."
                show_validation_error(error_msg)
                return

            # Si pasan las validaciones básicas
            show_success_message(
                f"✅ Formato de selectores válido para {self.selector_display_name}\n\n"
                f"📊 {len(selectors)} selector(es) configurado(s)\n\n"
                f"💡 Recuerda: Solo se puede probar completamente con WhatsApp Web abierto"
            )

        except Exception as e:
            show_error_message(f"Error probando selectores: {str(e)}")

    def _is_valid_xpath_format(self, selector):
        """
        Validación básica de formato XPath

        Args:
            selector: Selector a validar

        Returns:
            True si parece XPath válido
        """
        # Verificaciones básicas de XPath
        if not selector.startswith('//'):
            return False

        # Caracteres comunes en XPath válidos
        xpath_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789[]@='-_.:/*()\"")

        return all(c in xpath_chars for c in selector)

    def _is_valid_css_format(self, selector):
        """
        Validación básica de formato CSS

        Args:
            selector: Selector a validar

        Returns:
            True si parece CSS válido
        """
        # Verificaciones básicas de CSS
        if selector.startswith('//'):
            return False

        # Caracteres comunes en selectores CSS válidos
        css_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789[]#.=':*-_()\"")

        return all(c in css_chars for c in selector)

    def _save_selectors(self):
        """
        Guarda los selectores editados
        """
        selectors = self._get_edited_selectors()
        if selectors is None:
            return

        try:
            # Crear diccionario para actualizar
            selectors_update = {self.selector_key: selectors}

            # Guardar usando WhatsAppConstants
            if WhatsAppConstants.update_selectors(selectors_update):
                show_success_message(
                    f"✅ Selectores guardados para {self.selector_display_name}\n\n"
                    f"📊 {len(selectors)} selector(es) configurado(s)\n\n"
                    f"🔄 Los cambios se aplicarán en la próxima operación del bot"
                )
            else:
                show_error_message("Error al guardar los selectores")

        except Exception as e:
            show_error_message(f"Error guardando selectores: {str(e)}")

    def _reset_selectors(self):
        """
        Resetea los selectores a valores por defecto
        """
        if not show_confirmation_dialog(
                f"¿Resetear selectores de {self.selector_display_name} a valores por defecto?\n\n"
                f"Se perderán las configuraciones personalizadas."
        ):
            return

        try:
            # Resetear usando WhatsAppConstants
            if WhatsAppConstants.reset_selectors([self.selector_key]):
                # Recargar selectores por defecto
                self._load_current_selectors()

                show_success_message(
                    f"✅ Selectores de {self.selector_display_name} reseteados\n\n"
                    f"🔄 Se han restaurado los valores por defecto"
                )
            else:
                show_error_message("Error al resetear los selectores")

        except Exception as e:
            show_error_message(f"Error reseteando selectores: {str(e)}")

    def refresh_selectors(self):
        """
        Refresca los selectores mostrados (útil para actualizaciones externas)
        """
        self._load_current_selectors()


class GlobalConfigSection:
    """
    Sección de configuración global con acciones que afectan todos los selectores
    """

    def __init__(self, parent, style_manager: StyleManager, selector_sections):
        """
        Inicializa la sección de configuración global

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
            selector_sections: Lista de secciones de selectores para refrescar
        """
        self.style_manager = style_manager
        self.selector_sections = selector_sections

        # Crear frame de configuración global
        self._create_global_config_frame(parent)

    def _create_global_config_frame(self, parent):
        """
        Crea el frame de configuración global

        Args:
            parent: Widget padre
        """
        global_frame = self.style_manager.create_styled_labelframe(parent, "🌐 Configuración Global")
        global_frame.pack(fill=tk.X, padx=0, pady=(0, 15))

        content_frame = self.style_manager.create_styled_frame(global_frame)
        content_frame.pack(fill=tk.X, padx=12, pady=12)

        # Descripción
        desc_label = self.style_manager.create_styled_label(
            content_frame,
            "Acciones que afectan toda la configuración de selectores",
            "small"
        )
        desc_label.pack(anchor="w", pady=(0, 10))

        # Botones de acción global
        buttons_frame = self.style_manager.create_styled_frame(content_frame)
        buttons_frame.pack(fill=tk.X)

        # Botón refrescar todo
        refresh_btn = self.style_manager.create_styled_button(
            buttons_frame,
            "🔄 Refrescar Todo",
            self._refresh_all_sections,
            "normal"
        )
        refresh_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Botón resetear todo
        reset_all_btn = self.style_manager.create_styled_button(
            buttons_frame,
            "🗑️ Resetear Todo",
            self._reset_all_selectors,
            "error"
        )
        reset_all_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Botón exportar configuración
        export_btn = self.style_manager.create_styled_button(
            buttons_frame,
            "📤 Ver Configuración",
            self._show_current_config,
            "accent"
        )
        export_btn.pack(side=tk.RIGHT)

    def _refresh_all_sections(self):
        """
        Refresca todas las secciones de selectores
        """
        try:
            for section in self.selector_sections:
                section.refresh_selectors()

            show_success_message("✅ Todas las secciones han sido refrescadas")

        except Exception as e:
            show_error_message(f"Error refrescando secciones: {str(e)}")

    def _reset_all_selectors(self):
        """
        Resetea todos los selectores a valores por defecto
        """
        if not show_confirmation_dialog(
                "¿Resetear TODOS los selectores a valores por defecto?\n\n"
                "⚠️ Se perderán TODAS las configuraciones personalizadas.\n\n"
                "Esta acción no se puede deshacer."
        ):
            return

        try:
            # Resetear todos los selectores
            if WhatsAppConstants.reset_selectors():
                # Refrescar todas las secciones
                self._refresh_all_sections()

                show_success_message(
                    "✅ Todos los selectores han sido reseteados\n\n"
                    "🔄 Se han restaurado todos los valores por defecto"
                )
            else:
                show_error_message("Error al resetear todos los selectores")

        except Exception as e:
            show_error_message(f"Error reseteando todos los selectores: {str(e)}")

    def _show_current_config(self):
        """
        Muestra la configuración actual en una ventana informativa
        """
        try:
            # Obtener configuración actual
            config_info = self._get_current_config_info()

            # Crear ventana de información
            info_window = tk.Toplevel()
            self.style_manager.configure_window(info_window, "Configuración Actual", "600x400")

            # Frame principal
            main_frame = self.style_manager.create_styled_frame(info_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

            # Título
            title_label = self.style_manager.create_styled_label(
                main_frame,
                "📋 Configuración Actual de Selectores",
                "heading"
            )
            title_label.pack(pady=(0, 10))

            # Área de texto con la configuración
            config_text = scrolledtext.ScrolledText(
                main_frame,
                font=self.style_manager.fonts["small"],
                bg=self.style_manager.colors["bg_card"],
                fg=self.style_manager.colors["text_primary"],
                border=1,
                relief="solid",
                wrap=tk.WORD,
                state="disabled"
            )
            config_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

            # Insertar información
            config_text.configure(state="normal")
            config_text.insert(1.0, config_info)
            config_text.configure(state="disabled")

            # Botón cerrar
            close_btn = self.style_manager.create_styled_button(
                main_frame,
                "✅ Cerrar",
                info_window.destroy,
                "normal"
            )
            close_btn.pack()

        except Exception as e:
            show_error_message(f"Error mostrando configuración: {str(e)}")

    def _get_current_config_info(self):
        """
        Obtiene información formateada de la configuración actual

        Returns:
            String con información de configuración
        """
        try:
            config_info = "🎯 SELECTORES CONFIGURADOS\n"
            config_info += "=" * 50 + "\n\n"

            # Obtener claves disponibles
            available_keys = WhatsAppConstants.get_available_selector_keys()

            for key in available_keys:
                display_names = {
                    'message_box': 'Campo de Mensaje',
                    'attach_button': 'Botón Adjuntar',
                    'search_box': 'Campo de Búsqueda',
                    'send_button': 'Botón Enviar',
                    'file_input': 'Input de Archivo'
                }

                display_name = display_names.get(key, key.replace('_', ' ').title())
                selectors = WhatsAppConstants.get_selectors(key)

                config_info += f"📌 {display_name} ({key}):\n"
                for i, selector in enumerate(selectors, 1):
                    config_info += f"   {i}. {selector}\n"
                config_info += "\n"

            # Información adicional
            config_info += "ℹ️ INFORMACIÓN ADICIONAL\n"
            config_info += "=" * 50 + "\n\n"
            config_info += "• Los selectores se prueban en orden de prioridad\n"
            config_info += "• Si un selector falla, se prueba el siguiente\n"
            config_info += "• Los cambios se guardan automáticamente\n"
            config_info += "• Archivo de configuración: selectores_config.json\n"

            return config_info

        except Exception as e:
            return f"Error obteniendo configuración: {str(e)}"


class ConfigTab:
    """
    Pestaña principal de configuración de selectores con layout horizontal compacto
    """

    def __init__(self, parent, style_manager: StyleManager):
        """
        Inicializa la pestaña de configuración

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
        """
        self.style_manager = style_manager

        # Frame principal
        self.frame = style_manager.create_styled_frame(parent)

        # Crear layout de la pestaña
        self._create_tab_layout()

    def _create_tab_layout(self):
        """
        Crea el layout principal de la pestaña de configuración
        """
        # Header compacto
        self._create_compact_header()

        # Container principal con layout horizontal
        main_container = self.style_manager.create_styled_frame(self.frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        # Columna izquierda: Selectores principales (50%)
        left_column = self.style_manager.create_styled_frame(main_container)
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))

        # Columna derecha: Otros selectores y configuración global (50%)
        right_column = self.style_manager.create_styled_frame(main_container)
        right_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(6, 0))

        # Crear secciones de selectores
        self._create_selector_sections(left_column, right_column)

    def _create_compact_header(self):
        """
        Crea el header compacto de la pestaña
        """
        header_container = self.style_manager.create_styled_frame(self.frame)
        header_container.pack(fill=tk.X, padx=12, pady=(12, 8))

        # Título
        title_label = self.style_manager.create_styled_label(
            header_container,
            "Configuración de Selectores",
            "title"
        )
        title_label.pack(anchor="w")

        # Descripción
        desc_label = self.style_manager.create_styled_label(
            header_container,
            "Personaliza los selectores CSS/XPath para adaptarse a cambios de WhatsApp Web",
            "secondary"
        )
        desc_label.pack(anchor="w", pady=(4, 0))

        # Línea separadora
        separator = self.style_manager.create_styled_frame(header_container, "accent")
        separator.configure(height=1)
        separator.pack(fill=tk.X, pady=(8, 0))

    def _create_selector_sections(self, left_column, right_column):
        """
        Crea las secciones de edición de selectores

        Args:
            left_column: Columna izquierda
            right_column: Columna derecha
        """
        # Sección campo de mensaje (izquierda)
        self.message_box_section = SelectorEditSection(
            left_column,
            self.style_manager,
            'message_box',
            'Campo de Mensaje'
        )

        # Sección botón adjuntar (derecha)
        self.attach_button_section = SelectorEditSection(
            right_column,
            self.style_manager,
            'attach_button',
            'Botón Adjuntar'
        )

        # Lista de secciones para operaciones globales
        self.selector_sections = [
            self.message_box_section,
            self.attach_button_section
        ]

        # Configuración global (derecha, abajo)
        self.global_config = GlobalConfigSection(
            right_column,
            self.style_manager,
            self.selector_sections
        )

    def get_frame(self):
        """
        Obtiene el frame principal de la pestaña

        Returns:
            Frame principal de la pestaña
        """
        return self.frame

    def on_show(self):
        """
        Callback ejecutado cuando se muestra la pestaña
        """
        # Refrescar todas las secciones para mostrar datos actuales
        try:
            for section in self.selector_sections:
                section.refresh_selectors()
        except Exception as e:
            show_error_message(f"Error al mostrar pestaña de configuración: {str(e)}")

    def get_current_config_summary(self):
        """
        Obtiene un resumen de la configuración actual

        Returns:
            Diccionario con resumen de configuración
        """
        try:
            summary = {}

            # Obtener información de cada selector configurado
            for key in ['message_box', 'attach_button']:
                selectors = WhatsAppConstants.get_selectors(key)
                summary[key] = {
                    'count': len(selectors),
                    'selectors': selectors,
                    'is_custom': key in WhatsAppConstants.get_selectors_config().get_all_custom_selectors()
                }

            return summary

        except Exception as e:
            return {'error': str(e)}