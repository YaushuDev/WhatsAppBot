# data_manager.py
"""
Gestor de datos para el Bot de WhatsApp
Maneja la persistencia y gestión de contactos (nombre y número) y mensajes
utilizando archivos JSON para almacenar la información localmente.
Incluye compatibilidad con el formato anterior de solo números.
"""

import json
import os
from typing import List, Dict, Any, Tuple, Optional


class DataManager:
    """
    Clase para gestionar la persistencia de datos del bot
    Maneja contactos con nombre y número, y mensajes
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
        # Archivo de números (ahora contactos)
        if not os.path.exists(self.numbers_file):
            self._save_json(self.numbers_file, {"contactos": []})
        else:
            # Migrar formato antiguo si es necesario
            self._migrate_old_format()

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

    def _migrate_old_format(self):
        """
        Migra el formato antiguo de solo números al nuevo formato con contactos
        """
        try:
            data = self._load_json(self.numbers_file)

            # Si tiene el formato antiguo (solo lista de números)
            if "numeros" in data and "contactos" not in data:
                old_numbers = data.get("numeros", [])
                new_contactos = []

                # Convertir números a contactos con nombre genérico
                for i, number in enumerate(old_numbers):
                    if isinstance(number, str):
                        new_contactos.append({
                            "nombre": f"Contacto {i + 1}",
                            "numero": number
                        })

                # Guardar en nuevo formato
                new_data = {"contactos": new_contactos}
                self._save_json(self.numbers_file, new_data)

        except Exception as e:
            print(f"Error en migración: {e}")
            # En caso de error, crear estructura nueva
            self._save_json(self.numbers_file, {"contactos": []})

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

    # Gestión de contactos (nombre + número)
    def get_contacts(self) -> List[Dict[str, str]]:
        """
        Obtiene la lista de contactos guardados

        Returns:
            Lista de diccionarios con 'nombre' y 'numero'
        """
        data = self._load_json(self.numbers_file)
        return data.get("contactos", [])

    def get_numbers_only(self) -> List[str]:
        """
        Obtiene solo los números de teléfono (para compatibilidad con el bot)

        Returns:
            Lista de números de teléfono
        """
        contacts = self.get_contacts()
        return [contact.get("numero", "") for contact in contacts if contact.get("numero")]

    def add_contact(self, nombre: str, numero: str) -> bool:
        """
        Agrega un contacto a la lista

        Args:
            nombre: Nombre del contacto
            numero: Número de teléfono

        Returns:
            True si se agregó correctamente, False si ya existe o es inválido
        """
        if not nombre.strip() or not numero.strip():
            return False

        contacts = self.get_contacts()

        # Limpiar el número (quitar espacios y caracteres especiales)
        clean_number = ''.join(filter(str.isdigit, numero))
        clean_name = nombre.strip()

        if not clean_number:
            return False

        # Verificar si el número ya existe
        for contact in contacts:
            if contact.get("numero") == clean_number:
                return False

        # Agregar nuevo contacto
        new_contact = {
            "nombre": clean_name,
            "numero": clean_number
        }
        contacts.append(new_contact)
        self._save_json(self.numbers_file, {"contactos": contacts})
        return True

    def remove_contact(self, index: int) -> bool:
        """
        Elimina un contacto por índice

        Args:
            index: Índice del contacto a eliminar

        Returns:
            True si se eliminó correctamente
        """
        contacts = self.get_contacts()

        if 0 <= index < len(contacts):
            contacts.pop(index)
            self._save_json(self.numbers_file, {"contactos": contacts})
            return True
        return False

    def update_contact(self, index: int, nombre: str, numero: str) -> bool:
        """
        Actualiza un contacto existente

        Args:
            index: Índice del contacto a actualizar
            nombre: Nuevo nombre
            numero: Nuevo número

        Returns:
            True si se actualizó correctamente
        """
        if not nombre.strip() or not numero.strip():
            return False

        contacts = self.get_contacts()

        if not (0 <= index < len(contacts)):
            return False

        # Limpiar datos
        clean_number = ''.join(filter(str.isdigit, numero))
        clean_name = nombre.strip()

        if not clean_number:
            return False

        # Verificar si el número ya existe en otro contacto
        for i, contact in enumerate(contacts):
            if i != index and contact.get("numero") == clean_number:
                return False

        # Actualizar contacto
        contacts[index] = {
            "nombre": clean_name,
            "numero": clean_number
        }
        self._save_json(self.numbers_file, {"contactos": contacts})
        return True

    def clear_all_contacts(self) -> bool:
        """
        Elimina todos los contactos

        Returns:
            True si se eliminaron correctamente
        """
        try:
            self._save_json(self.numbers_file, {"contactos": []})
            return True
        except:
            return False

    def add_contacts_bulk(self, contacts_list: List[Dict[str, str]]) -> Tuple[int, int]:
        """
        Agrega múltiples contactos de una vez

        Args:
            contacts_list: Lista de diccionarios con 'nombre' y 'numero'

        Returns:
            Tupla (agregados_exitosamente, total_intentados)
        """
        if not contacts_list:
            return 0, 0

        current_contacts = self.get_contacts()
        existing_numbers = {contact.get("numero") for contact in current_contacts}

        added_count = 0
        total_count = len(contacts_list)

        for contact_data in contacts_list:
            nombre = contact_data.get("nombre", "").strip()
            numero = contact_data.get("numero", "").strip()

            if not nombre or not numero:
                continue

            # Limpiar número
            clean_number = ''.join(filter(str.isdigit, numero))

            if not clean_number or clean_number in existing_numbers:
                continue

            # Agregar contacto
            new_contact = {
                "nombre": nombre,
                "numero": clean_number
            }
            current_contacts.append(new_contact)
            existing_numbers.add(clean_number)
            added_count += 1

        # Guardar todos los cambios
        if added_count > 0:
            self._save_json(self.numbers_file, {"contactos": current_contacts})

        return added_count, total_count

    def get_contact_by_index(self, index: int) -> Optional[Dict[str, str]]:
        """
        Obtiene un contacto por su índice

        Args:
            index: Índice del contacto

        Returns:
            Diccionario con 'nombre' y 'numero' o None si no existe
        """
        contacts = self.get_contacts()
        if 0 <= index < len(contacts):
            return contacts[index].copy()
        return None

    # Métodos de compatibilidad (mantener para no romper código existente)
    def get_numbers(self) -> List[str]:
        """
        Método de compatibilidad: obtiene solo los números

        Returns:
            Lista de números de teléfono
        """
        return self.get_numbers_only()

    def add_number(self, number: str) -> bool:
        """
        Método de compatibilidad: agrega un número con nombre genérico

        Args:
            number: Número de teléfono

        Returns:
            True si se agregó correctamente
        """
        if not number.strip():
            return False

        # Generar nombre automático
        contacts = self.get_contacts()
        next_number = len(contacts) + 1
        auto_name = f"Contacto {next_number}"

        return self.add_contact(auto_name, number)

    def remove_number(self, number: str) -> bool:
        """
        Método de compatibilidad: elimina un contacto por número

        Args:
            number: Número a eliminar

        Returns:
            True si se eliminó correctamente
        """
        contacts = self.get_contacts()
        clean_number = ''.join(filter(str.isdigit, number))

        for i, contact in enumerate(contacts):
            if contact.get("numero") == clean_number:
                return self.remove_contact(i)
        return False

    # Gestión de mensajes (sin cambios)
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

    # Gestión de configuración (sin cambios)
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