# gui_main.py
"""
Interfaz gráfica principal para el Bot de WhatsApp
Coordina todos los componentes modulares de la GUI, incluyendo estilos, componentes y pestañas.
Implementa una interfaz moderna con tema nocturno que permite gestionar números, mensajes
y controlar la automatización del bot de WhatsApp de forma intuitiva y organizada
"""

import tkinter as tk
from tkinter import messagebox
from data_manager import DataManager
from whatsapp_bot import WhatsAppBot
from gui_styles import StyleManager
from gui_components import NavigationSidebar
from gui_tab_manager import TabManager


class WhatsAppBotGUI:
    """
    Clase principal de la interfaz gráfica del bot de WhatsApp
    Coordina todos los componentes modulares y maneja el ciclo de vida de la aplicación
    """

    def __init__(self):
        """
        Inicializa la interfaz gráfica y sus componentes
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
        Configura la ventana principal y estilos
        """
        # Configurar ventana principal
        self.style_manager.configure_window(
            self.root,
            "Bot de WhatsApp",
            "900x900",
            "icon.ico"
        )

        # Configurar estilos TTK
        self.style_manager.setup_ttk_styles()

        # Configurar cierre de aplicación
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_interface(self):
        """
        Crea la interfaz principal con layout y componentes
        """
        # Frame principal
        self.main_frame = self.style_manager.create_styled_frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Barra lateral de navegación
        self.sidebar = NavigationSidebar(
            self.main_frame,
            self.style_manager,
            self._on_tab_change
        )

        # Área de contenido para las pestañas
        self.content_area = self.style_manager.create_styled_frame(self.main_frame)
        self.content_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Gestor de pestañas (ahora usando el nuevo TabManager modularizado)
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
        Maneja el cambio de pestaña

        Args:
            tab_name: Nombre de la pestaña a mostrar
        """
        # Cambiar pestaña en el gestor
        self.tab_manager.show_tab(tab_name)

        # Actualizar navegación visual
        self.sidebar.update_active_tab(tab_name)

        # Actualizar estadísticas si es necesario
        if tab_name == "automatizacion":
            self._update_global_stats()

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
        Maneja el cierre de la aplicación de forma segura
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
            self._cleanup_and_exit()

    def _cleanup_and_exit(self):
        """
        Limpia recursos y cierra la aplicación
        """
        try:
            # Detener automatización si está activa
            if self.whatsapp_bot.is_active():
                self.whatsapp_bot.stop_automation()

            # Cerrar bot y limpiar recursos
            self.whatsapp_bot.close()

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
        Obtiene estadísticas actuales de la aplicación

        Returns:
            Diccionario con estadísticas
        """
        return {
            'numbers_count': len(self.data_manager.get_numbers()),
            'messages_count': len(self.data_manager.get_messages()),
            'automation_active': self.whatsapp_bot.is_active(),
            'current_tab': self.tab_manager.get_current_tab()
        }