# main.py
"""
Punto de entrada principal del Bot de WhatsApp
Este archivo inicializa la aplicación y ejecuta la interfaz gráfica del bot
que permite automatizar el envío de mensajes a través de WhatsApp Web
"""

import sys
import os
from gui import WhatsAppBotGUI

def main():
    """
    Función principal que inicializa y ejecuta la aplicación
    """
    try:
        # Crear e iniciar la interfaz gráfica
        app = WhatsAppBotGUI()
        app.run()
    except Exception as e:
        print(f"Error al iniciar la aplicación: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()