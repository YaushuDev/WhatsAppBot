# gui_main.py
"""
Interfaz gráfica principal para el Bot de WhatsApp con configuración de selectores
Coordina todos los componentes modulares de la GUI con layout horizontal compacto.
Implementa una interfaz moderna de 1000x600px que permite gestionar números, mensajes,
controlar la automatización del bot de WhatsApp y configurar selectores CSS/XPath de forma
intuitiva y organizada, optimizada para pantallas de cualquier tamaño.
"""

import tkinter as tk
from tkinter import messagebox
from data_manager import DataManager
from whatsapp_bot import WhatsAppBot
from gui_styles import StyleManager
from gui_components import NavigationSidebar
from gui_tab_manager import TabManager


class ConfigurableNavigationSidebar:
    """
    Barra lateral de navegación extendida que incluye la pestaña de configuración
    """

    def __init__(self, parent, style_manager: StyleManager, tab_callback):
        """
        Inicializa la barra lateral con soporte para configuración

        Args:
            parent: Widget padre
            style_manager: Gestor de estilos
            tab_callback: Función callback para cambio de pestañas
        """
        self.style_manager = style_manager
        self.tab_callback = tab_callback
        self.nav_buttons = {}

        # Crear frame principal de la sidebar con ancho mejorado
        self.sidebar = style_manager.create_styled_frame(parent, "secondary")
        self.sidebar.configure(width=220)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 2))
        self.sidebar.pack_propagate(False)

        self._create_elements()

    def _create_elements(self):
        """
        Crea los elementos de la barra lateral con configuración incluida
        """
        # Contenedor principal con padding mejorado
        main_container = self.style_manager.create_styled_frame(self.sidebar, "secondary")
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=20)

        # Título con mejor espaciado
        title_label = self.style_manager.create_styled_label(
            main_container,
            "WhatsApp Bot",
            "subtitle"
        )
        title_label.configure(bg=self.style_manager.colors["bg_secondary"])
        title_label.pack(pady=(0, 35))

        # Contenedor para botones de navegación
        nav_container = self.style_manager.create_styled_frame(main_container, "secondary")
        nav_container.pack(fill=tk.X, pady=(0, 20))

        # Botones de navegación incluyendo configuración
        nav_items = [
            ("numeros", "📱 Contactos", "Gestionar contactos de teléfono"),
            ("mensajes", "💬 Mensajes", "Crear y editar mensajes"),
            ("automatizacion", "🤖 Automatización", "Controlar el envío automático"),
            ("configuracion", "⚙️ Configuración", "Personalizar selectores CSS/XPath")
        ]

        for i, (tab_id, text, tooltip) in enumerate(nav_items):
            # Frame contenedor para cada botón
            btn_frame = self.style_manager.create_styled_frame(nav_container, "secondary")
            btn_frame.pack(fill=tk.X, pady=(0, 8))

            button = tk.Button(
                btn_frame,
                text=text,
                font=self.style_manager.fonts["button"],
                bg=self.style_manager.colors["bg_accent"],
                fg=self.style_manager.colors["text_primary"],
                border=0,
                pady=15,
                padx=20,
                cursor="hand2",
                anchor="w",
                relief="flat",
                command=lambda t=tab_id: self.tab_callback(t)
            )
            button.pack(fill=tk.X)

            # Agregar efecto hover mejorado
            self.style_manager._add_hover_effect(
                button,
                self.style_manager.colors["hover"],
                self.style_manager.colors["bg_accent"]
            )

            self.nav_buttons[tab_id] = button

        # Espaciador flexible
        spacer = self.style_manager.create_styled_frame(main_container, "secondary")
        spacer.pack(fill=tk.BOTH, expand=True)

        # Sección de estado en la parte inferior
        status_container = self.style_manager.create_styled_frame(main_container, "card")
        status_container.pack(fill=tk.X, pady=(10, 0))
        status_container.configure(relief="solid", bd=1, highlightthickness=0)

        # Título de estado
        status_title = self.style_manager.create_styled_label(
            status_container,
            "Estado:",
            "small"
        )
        status_title.configure(
            bg=self.style_manager.colors["bg_card"],
            fg=self.style_manager.colors["accent_light"]
        )
        status_title.pack(pady=(10, 5), padx=15, anchor="w")

        # Mensaje de estado
        self.status_label = self.style_manager.create_styled_label(
            status_container,
            "Listo",
            "small"
        )
        self.status_label.configure(
            bg=self.style_manager.colors["bg_card"],
            wraplength=180,
            justify="left"
        )
        self.status_label.pack(pady=(0, 10), padx=15, anchor="w")

    def update_active_tab(self, active_tab):
        """
        Actualiza el botón activo en la navegación incluyendo configuración

        Args:
            active_tab: ID de la pestaña activa
        """
        for tab_id, button in self.nav_buttons.items():
            if tab_id == active_tab:
                button.configure(
                    bg=self.style_manager.colors["accent"],
                    fg=self.style_manager.colors["text_primary"]
                )
                # Actualizar hover effect para botón activo
                self.style_manager._add_hover_effect(
                    button,
                    self.style_manager.colors["accent_light"],
                    self.style_manager.colors["accent"]
                )
            else:
                button.configure(
                    bg=self.style_manager.colors["bg_accent"],
                    fg=self.style_manager.colors["text_primary"]
                )
                # Restaurar hover effect normal
                self.style_manager._add_hover_effect(
                    button,
                    self.style_manager.colors["hover"],
                    self.style_manager.colors["bg_accent"]
                )

    def update_status(self, message):
        """
        Actualiza el mensaje de estado con mejor formato

        Args:
            message: Nuevo mensaje de estado
        """
        # Truncar mensaje si es muy largo
        short_message = message[:35] + "..." if len(message) > 35 else message
        self.status_label.configure(text=short_message)


class WhatsAppBotGUI:
    """
    Clase principal de la interfaz gráfica del bot de WhatsApp con configuración
    Coordina todos los módulos especializados y proporciona una API simple para la GUI
    con soporte para personalización de selectores CSS/XPath
    """

    def __init__(self):
        """
        Inicializa la interfaz gráfica y sus componentes con configuración
        """
        # Inicializar componentes base
        self.root = tk.Tk()
        self.style_manager = StyleManager()
        self.data_manager = DataManager()
        self.whatsapp_bot = WhatsAppBot(status_callback=self._update_status)

        # Variables de estado
        self.automation_active = False

        # Configurar la aplicación
        self._setup_application()
        self._create_interface()

    def _setup_application(self):
        """
        Configura la ventana principal y estilos con dimensiones horizontales compactas
        """
        # Configurar ventana principal con nueva dimensión horizontal
        self.style_manager.configure_window(
            self.root,
            "Bot de WhatsApp",
            "1050x750",
            "icon.ico"
        )

        # Configurar estilos TTK
        self.style_manager.setup_ttk_styles()

        # Configurar cierre de aplicación
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_interface(self):
        """
        Crea la interfaz principal con layout horizontal optimizado y navegación de configuración
        """
        # Frame principal
        self.main_frame = self.style_manager.create_styled_frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Barra lateral de navegación con configuración incluida
        self.sidebar = ConfigurableNavigationSidebar(
            self.main_frame,
            self.style_manager,
            self._on_tab_change
        )

        # Área de contenido para las pestañas (ahora más ancha y menos alta)
        self.content_area = self.style_manager.create_styled_frame(self.main_frame)
        self.content_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Gestor de pestañas con configuración incluida
        self.tab_manager = TabManager(
            self.content_area,
            self.style_manager,
            self.data_manager,
            self.whatsapp_bot,
            self._update_global_stats
        )

        # Mostrar pestaña inicial
        self._on_tab_change("numeros")

    def _on_tab_change(self, tab_name):
        """
        Maneja el cambio de pestaña incluyendo configuración

        Args:
            tab_name: Nombre de la pestaña a mostrar (incluye "configuracion")
        """
        # Validar cambios de configuración si se está saliendo de configuración
        if self.tab_manager.get_current_tab() == "configuracion" and tab_name != "configuracion":
            if not self._validate_config_transition():
                return  # No cambiar de pestaña si hay problemas

        # Cambiar pestaña en el gestor
        self.tab_manager.show_tab(tab_name)

        # Actualizar navegación visual
        self.sidebar.update_active_tab(tab_name)

        # Actualizar estadísticas si es necesario
        if tab_name == "automatizacion":
            self._update_global_stats()
        elif tab_name == "configuracion":
            self._on_config_tab_shown()

    def _validate_config_transition(self):
        """
        Valida la transición desde la pestaña de configuración

        Returns:
            bool: True si se puede cambiar de pestaña
        """
        try:
            # Verificar si hay automatización activa
            if self.whatsapp_bot.is_active():
                messagebox.showwarning(
                    "Automatización Activa",
                    "Los cambios en la configuración no se aplicarán hasta que termine la automatización actual."
                )
                return True  # Permitir cambio pero con advertencia

            return True
        except Exception as e:
            messagebox.showerror("Error", f"Error validando configuración: {str(e)}")
            return False

    def _on_config_tab_shown(self):
        """
        Callback ejecutado cuando se muestra la pestaña de configuración
        """
        try:
            # Informar al usuario sobre el estado actual
            if self.whatsapp_bot.is_active():
                self._update_status("⚠️ Configuración: Cambios se aplicarán al finalizar automatización")
            else:
                self._update_status("🔧 Configuración: Personaliza selectores de WhatsApp Web")

            # Obtener resumen de configuración
            config_summary = self.tab_manager.get_config_tab_summary()
            if config_summary:
                custom_count = sum(
                    1 for info in config_summary.values() if isinstance(info, dict) and info.get('is_custom', False))
                if custom_count > 0:
                    self._update_status(f"🎯 {custom_count} selector(es) personalizado(s) activo(s)")

        except Exception as e:
            print(f"Error en callback de configuración: {e}")

    def _update_status(self, message):
        """
        Actualiza el estado en la barra lateral y en la pestaña de automatización

        Args:
            message: Mensaje de estado
        """
        # Actualizar estado en sidebar
        self.sidebar.update_status(message)

        # Actualizar log en pestaña de automatización
        self.tab_manager.update_automation_status(message)

    def _update_global_stats(self):
        """
        Actualiza las estadísticas globales en toda la aplicación
        """
        # Las estadísticas se actualizan automáticamente en cada pestaña
        # cuando se muestran o cuando se modifican los datos
        pass

    def _on_closing(self):
        """
        Maneja el cierre de la aplicación de forma segura con validación de configuración
        """
        # Verificar si hay automatización activa
        if self.whatsapp_bot.is_active():
            response = messagebox.askyesno(
                "Confirmar",
                "La automatización está en ejecución. ¿Deseas detenerla y cerrar la aplicación?"
            )
            if response:
                self._cleanup_and_exit()
        else:
            # Verificar si hay cambios de configuración pendientes
            current_tab = self.tab_manager.get_current_tab()
            if current_tab == "configuracion":
                response = messagebox.askyesno(
                    "Confirmar Cierre",
                    "¿Estás seguro de que quieres cerrar la aplicación?\n\nAsegúrate de haber guardado los cambios de configuración."
                )
                if response:
                    self._cleanup_and_exit()
            else:
                self._cleanup_and_exit()

    def _cleanup_and_exit(self):
        """
        Limpia recursos y cierra la aplicación con limpieza de configuración
        """
        try:
            # Detener automatización si está activa
            if self.whatsapp_bot.is_active():
                self.whatsapp_bot.stop_automation()

            # Cerrar bot y limpiar recursos
            self.whatsapp_bot.close()

            # Log de configuración final
            config_summary = self.tab_manager.get_config_tab_summary()
            if config_summary:
                custom_count = sum(
                    1 for info in config_summary.values() if isinstance(info, dict) and info.get('is_custom', False))
                print(f"[GUI] Cerrando con {custom_count} selector(es) personalizado(s)")

        except Exception as e:
            print(f"Error durante limpieza: {e}")
        finally:
            # Cerrar aplicación
            self.root.destroy()

    def run(self):
        """
        Inicia el bucle principal de la aplicación
        """
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"Error en el bucle principal: {e}")
            messagebox.showerror("Error", f"Error inesperado: {e}")
        finally:
            # Asegurar limpieza en caso de error
            try:
                self.whatsapp_bot.close()
            except:
                pass

    def get_stats(self):
        """
        Obtiene estadísticas actuales de la aplicación incluyendo configuración

        Returns:
            Diccionario con estadísticas incluyendo información de configuración
        """
        base_stats = {
            'numbers_count': len(self.data_manager.get_numbers()),
            'messages_count': len(self.data_manager.get_messages()),
            'automation_active': self.whatsapp_bot.is_active(),
            'current_tab': self.tab_manager.get_current_tab()
        }

        # Agregar información de configuración
        try:
            config_summary = self.tab_manager.get_config_tab_summary()
            if config_summary:
                custom_selectors = sum(
                    1 for info in config_summary.values() if isinstance(info, dict) and info.get('is_custom', False))
                base_stats['custom_selectors_count'] = custom_selectors
                base_stats['config_available'] = True
            else:
                base_stats['custom_selectors_count'] = 0
                base_stats['config_available'] = False
        except Exception:
            base_stats['custom_selectors_count'] = 0
            base_stats['config_available'] = False

        return base_stats

    def get_navigation_info(self):
        """
        Obtiene información sobre el estado de navegación incluyendo configuración

        Returns:
            Dict: Información de navegación y pestañas disponibles
        """
        return {
            'current_tab': self.tab_manager.get_current_tab(),
            'available_tabs': self.tab_manager.get_available_tabs(),
            'tab_dependencies': self.tab_manager.get_tab_dependencies(),
            'config_tab_available': 'configuracion' in self.tab_manager.get_available_tabs()
        }