# gui_components.py
"""
Punto de entrada principal para todos los componentes GUI del Bot de WhatsApp
Este módulo actúa como facade, importando y exponiendo todos los componentes
de los módulos especializados para mantener compatibilidad con el código existente
y proporcionar una API unificada y limpia para toda la interfaz gráfica.
"""

# Importar todos los componentes base
from gui_base_components import (
    # Componentes de navegación
    NavigationSidebar,
    TabHeader,
    SubTabNavigator,

    # Componentes base reutilizables
    ListManager,
    InputSection,
    StatsDisplay,
    ActivityLog,

    # Menú de emoticones
    EmojiMenu,

    # Funciones de diálogo
    show_validation_error,
    show_success_message,
    show_error_message,
    show_confirmation_dialog
)

# Importar todos los componentes avanzados
from gui_advanced_components import (
    # Componentes especializados de contactos
    ContactListManager,
    ContactInputSection,
    ContactEditDialog,

    # Componentes de importación de datos
    ExcelUploadComponent
)


# NUEVO: Función específica para restricción del primer mensaje
def show_first_message_image_restriction():
    """
    Muestra un mensaje de advertencia sobre la restricción de imagen en el primer mensaje

    Returns:
        None - Solo muestra el mensaje informativo
    """
    from tkinter import messagebox

    message = (
        "❌ Primer mensaje: solo texto permitido\n\n"
        "WhatsApp Web tiene un error al inicio que envía la primera imagen como \"Ver una vez\".\n\n"
        "Use texto para el primer mensaje."
    )

    messagebox.showwarning("⚠️ Restricción de Imagen", message)


# Exportar todo para mantener compatibilidad
__all__ = [
    # Navegación
    'NavigationSidebar',
    'TabHeader',
    'SubTabNavigator',

    # Componentes base
    'ListManager',
    'InputSection',
    'StatsDisplay',
    'ActivityLog',

    # Emoticones
    'EmojiMenu',

    # Contactos especializados
    'ContactListManager',
    'ContactInputSection',
    'ContactEditDialog',

    # Importación de datos
    'ExcelUploadComponent',

    # Diálogos
    'show_validation_error',
    'show_success_message',
    'show_error_message',
    'show_confirmation_dialog',
    'show_first_message_image_restriction',  # NUEVO
]