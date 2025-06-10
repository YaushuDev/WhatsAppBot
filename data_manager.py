# data_manager.py
"""
Gestor de datos para el Bot de WhatsApp
Maneja la persistencia y gestión de números de teléfono y mensajes
utilizando archivos JSON para almacenar la información localmente
"""

import json
import os
from typing import List, Dict, Any


class DataManager:
    """
    Clase para gestionar la persistencia de datos del bot
    """

    def __init__(self):
        """
        Inicializa el gestor de datos y crea los archivos si no existen
        """
        self.numbers_file = "numeros.json"
        self.messages_file = "mensajes.json"
        self.config_file = "config.json"

        # Crear archivos si no existen
        self._initialize_files()

    def _initialize_files(self):
        """
        Inicializa los archivos JSON con estructuras vacías si no existen
        """
        # Archivo de números
        if not os.path.exists(self.numbers_file):
            self._save_json(self.numbers_file, {"numeros": []})

        # Archivo de mensajes
        if not os.path.exists(self.messages_file):
            self._save_json(self.messages_file, {"mensajes": []})

        # Archivo de configuración
        if not os.path.exists(self.config_file):
            default_config = {
                "intervalo_min": 30,
                "intervalo_max": 60,
                "activo": False
            }
            self._save_json(self.config_file, default_config)

    def _load_json(self, filename: str) -> Dict[str, Any]:
        """
        Carga un archivo JSON

        Args:
            filename: Nombre del archivo a cargar

        Returns:
            Diccionario con los datos del archivo
        """
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_json(self, filename: str, data: Dict[str, Any]):
        """
        Guarda datos en un archivo JSON

        Args:
            filename: Nombre del archivo
            data: Datos a guardar
        """
        try:
            with open(filename, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error al guardar {filename}: {e}")

    # Gestión de números
    def get_numbers(self) -> List[str]:
        """
        Obtiene la lista de números guardados

        Returns:
            Lista de números de teléfono
        """
        data = self._load_json(self.numbers_file)
        return data.get("numeros", [])

    def add_number(self, number: str) -> bool:
        """
        Agrega un número a la lista

        Args:
            number: Número de teléfono a agregar

        Returns:
            True si se agregó correctamente, False si ya existe
        """
        numbers = self.get_numbers()

        # Limpiar el número (quitar espacios y caracteres especiales)
        clean_number = ''.join(filter(str.isdigit, number))

        if clean_number and clean_number not in numbers:
            numbers.append(clean_number)
            self._save_json(self.numbers_file, {"numeros": numbers})
            return True
        return False

    def remove_number(self, number: str) -> bool:
        """
        Elimina un número de la lista

        Args:
            number: Número a eliminar

        Returns:
            True si se eliminó correctamente
        """
        numbers = self.get_numbers()
        clean_number = ''.join(filter(str.isdigit, number))

        if clean_number in numbers:
            numbers.remove(clean_number)
            self._save_json(self.numbers_file, {"numeros": numbers})
            return True
        return False

    # Gestión de mensajes
    def get_messages(self) -> List[str]:
        """
        Obtiene la lista de mensajes guardados

        Returns:
            Lista de mensajes
        """
        data = self._load_json(self.messages_file)
        return data.get("mensajes", [])

    def add_message(self, message: str) -> bool:
        """
        Agrega un mensaje a la lista

        Args:
            message: Mensaje a agregar

        Returns:
            True si se agregó correctamente
        """
        if message.strip():
            messages = self.get_messages()
            messages.append(message.strip())
            self._save_json(self.messages_file, {"mensajes": messages})
            return True
        return False

    def remove_message(self, index: int) -> bool:
        """
        Elimina un mensaje por índice

        Args:
            index: Índice del mensaje a eliminar

        Returns:
            True si se eliminó correctamente
        """
        messages = self.get_messages()

        if 0 <= index < len(messages):
            messages.pop(index)
            self._save_json(self.messages_file, {"mensajes": messages})
            return True
        return False

    def update_message(self, index: int, new_message: str) -> bool:
        """
        Actualiza un mensaje existente

        Args:
            index: Índice del mensaje a actualizar
            new_message: Nuevo contenido del mensaje

        Returns:
            True si se actualizó correctamente
        """
        if new_message.strip():
            messages = self.get_messages()

            if 0 <= index < len(messages):
                messages[index] = new_message.strip()
                self._save_json(self.messages_file, {"mensajes": messages})
                return True
        return False

    # Gestión de configuración
    def get_config(self) -> Dict[str, Any]:
        """
        Obtiene la configuración actual

        Returns:
            Diccionario con la configuración
        """
        return self._load_json(self.config_file)

    def save_config(self, config: Dict[str, Any]):
        """
        Guarda la configuración

        Args:
            config: Configuración a guardar
        """
        self._save_json(self.config_file, config)