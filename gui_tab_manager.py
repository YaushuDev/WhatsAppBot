# gui_tab_manager.py
"""
Gestor centralizado de pestañas para el Bot de WhatsApp con configuración de selectores
Este módulo se encarga exclusivamente de la coordinación y navegación entre las diferentes
pestañas de la aplicación (contactos, mensajes, automatización, configuración), actuando como
el cerebro organizador sin implementar lógica específica de cada pestaña. Incluye la nueva
pestaña de configuración para personalización de selectores CSS/XPath.
"""

from gui_styles import StyleManager


class TabManager:
    """
    Gestor de pestañas que coordina la navegación entre las diferentes secciones de la aplicación
    Responsable de mostrar/ocultar pestañas y coordinar la comunicación entre ellas
    """

    def __init__(self, parent, style_manager: StyleManager, data_manager, whatsapp_bot, update_stats_callback):
        """
        Inicializa el gestor de pestañas con soporte para configuración de selectores

        Args:
            parent: Widget padre donde se mostrarán las pestañas
            style_manager: Gestor de estilos para mantener consistencia visual
            data_manager: Gestor de datos compartido entre pestañas
            whatsapp_bot: Instancia del bot para automatización
            update_stats_callback: Callback para actualizar estadísticas globales
        """
        self.style_manager = style_manager
        self.data_manager = data_manager
        self.whatsapp_bot = whatsapp_bot
        self.update_stats_callback = update_stats_callback
        self.current_tab = "numeros"
        self.parent = parent

        # Crear pestañas usando imports dinámicos para evitar dependencias circulares
        self._create_tabs()

        # Mostrar pestaña inicial
        self.show_tab("numeros")

    def _create_tabs(self):
        """
        Crea las instancias de todas las pestañas de la aplicación incluyendo configuración
        Utiliza imports locales para evitar dependencias circulares
        """
        # Imports locales para evitar dependencias circulares
        from gui_contacts_tab import NumbersTab
        from gui_messages_tab import MessagesTab
        from gui_automation_tab import AutomationTab
        from gui_config_tab import ConfigTab

        # Crear diccionario de pestañas con la nueva pestaña de configuración
        self.tabs = {
            "numeros": NumbersTab(
                self.parent,
                self.style_manager,
                self.data_manager
            ),
            "mensajes": MessagesTab(
                self.parent,
                self.style_manager,
                self.data_manager
            ),
            "automatizacion": AutomationTab(
                self.parent,
                self.style_manager,
                self.data_manager,
                self.whatsapp_bot,
                self.update_stats_callback
            ),
            "configuracion": ConfigTab(
                self.parent,
                self.style_manager
            )
        }

    def show_tab(self, tab_name):
        """
        Muestra la pestaña especificada y oculta las demás
        Coordina la transición entre pestañas de forma suave incluyendo configuración

        Args:
            tab_name: Nombre de la pestaña a mostrar ("numeros", "mensajes", "automatizacion", "configuracion")
        """
        # Validar que la pestaña existe
        if tab_name not in self.tabs:
            print(f"Advertencia: Pestaña '{tab_name}' no encontrada")
            return

        # Ocultar todas las pestañas actuales
        self._hide_all_tabs()

        # Mostrar la pestaña seleccionada
        self._show_specific_tab(tab_name)

        # Actualizar pestaña actual
        self.current_tab = tab_name

    def _hide_all_tabs(self):
        """
        Oculta todas las pestañas actualmente visibles
        Método auxiliar para limpiar la interfaz antes de mostrar una nueva pestaña
        """
        for tab in self.tabs.values():
            if hasattr(tab, 'get_frame'):
                tab.get_frame().pack_forget()

    def _show_specific_tab(self, tab_name):
        """
        Muestra una pestaña específica y ejecuta su callback de inicialización

        Args:
            tab_name: Nombre de la pestaña a mostrar
        """
        target_tab = self.tabs[tab_name]

        # Mostrar el frame de la pestaña
        if hasattr(target_tab, 'get_frame'):
            target_tab.get_frame().pack(fill="both", expand=True)

        # Ejecutar callback específico de la pestaña si existe
        if hasattr(target_tab, 'on_show'):
            target_tab.on_show()

    def get_current_tab(self):
        """
        Obtiene el nombre de la pestaña actualmente activa

        Returns:
            str: Nombre de la pestaña actual
        """
        return self.current_tab

    def update_automation_status(self, message):
        """
        Actualiza el estado en la pestaña de automatización
        Permite comunicación desde componentes externos hacia la pestaña de automatización

        Args:
            message: Mensaje de estado a mostrar en la pestaña de automatización
        """
        if "automatizacion" in self.tabs:
            automation_tab = self.tabs["automatizacion"]
            if hasattr(automation_tab, 'update_status'):
                automation_tab.update_status(message)

    def refresh_all_tabs(self):
        """
        Fuerza la actualización de todas las pestañas
        Útil cuando hay cambios globales que afectan múltiples pestañas
        """
        for tab_name, tab in self.tabs.items():
            if hasattr(tab, 'on_show'):
                # Solo actualizar si es la pestaña activa para rendimiento
                if tab_name == self.current_tab:
                    tab.on_show()

    def get_tab_instance(self, tab_name):
        """
        Obtiene la instancia de una pestaña específica
        Permite acceso directo a métodos específicos de cada pestaña

        Args:
            tab_name: Nombre de la pestaña

        Returns:
            Instancia de la pestaña o None si no existe
        """
        return self.tabs.get(tab_name, None)

    def is_tab_active(self, tab_name):
        """
        Verifica si una pestaña específica está actualmente activa

        Args:
            tab_name: Nombre de la pestaña a verificar

        Returns:
            bool: True si la pestaña está activa
        """
        return self.current_tab == tab_name

    def get_available_tabs(self):
        """
        Obtiene lista de todas las pestañas disponibles

        Returns:
            List[str]: Lista con nombres de pestañas disponibles
        """
        return list(self.tabs.keys())

    def get_config_tab_summary(self):
        """
        Obtiene resumen de la configuración de selectores desde la pestaña de configuración

        Returns:
            Dict: Resumen de configuración de selectores o None si hay error
        """
        try:
            config_tab = self.tabs.get("configuracion")
            if config_tab and hasattr(config_tab, 'get_current_config_summary'):
                return config_tab.get_current_config_summary()
            return None
        except Exception as e:
            print(f"Error obteniendo resumen de configuración: {e}")
            return None

    def refresh_config_tab(self):
        """
        Refresca específicamente la pestaña de configuración
        Útil cuando se detectan cambios en selectores desde otras partes del sistema
        """
        try:
            config_tab = self.tabs.get("configuracion")
            if config_tab and hasattr(config_tab, 'on_show'):
                config_tab.on_show()
                print("Pestaña de configuración refrescada")
        except Exception as e:
            print(f"Error refrescando pestaña de configuración: {e}")

    def validate_config_changes(self):
        """
        Valida que los cambios de configuración sean compatibles con pestañas activas

        Returns:
            bool: True si la configuración es válida
        """
        try:
            # Si hay automatización activa, advertir sobre cambios de configuración
            if self.whatsapp_bot.is_active():
                print(
                    "Advertencia: Cambios en configuración no se aplicarán hasta que termine la automatización actual")
                return False

            return True
        except Exception as e:
            print(f"Error validando cambios de configuración: {e}")
            return False

    def notify_config_changed(self, selector_type: str):
        """
        Notifica a otras pestañas que la configuración de selectores ha cambiado

        Args:
            selector_type: Tipo de selector que cambió (ej: 'message_box', 'attach_button')
        """
        try:
            # Log del cambio
            print(f"Configuración de selector '{selector_type}' actualizada")

            # Notificar a pestaña de automatización si está disponible
            automation_tab = self.tabs.get("automatizacion")
            if automation_tab and hasattr(automation_tab, 'update_status'):
                automation_tab.update_status(f"🔧 Configuración de {selector_type} actualizada")

            # Actualizar callback de estadísticas si existe
            if self.update_stats_callback:
                self.update_stats_callback()

        except Exception as e:
            print(f"Error notificando cambio de configuración: {e}")

    def get_tab_dependencies(self):
        """
        Obtiene información sobre dependencias entre pestañas

        Returns:
            Dict: Información sobre dependencias y estado de pestañas
        """
        return {
            'current_tab': self.current_tab,
            'available_tabs': self.get_available_tabs(),
            'automation_active': self.whatsapp_bot.is_active() if self.whatsapp_bot else False,
            'config_available': 'configuracion' in self.tabs,
            'total_tabs': len(self.tabs)
        }