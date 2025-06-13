# data_manager.py
"""
Gestor de datos para el Bot de WhatsApp
Maneja la persistencia y gestión de contactos (nombre y número) y mensajes con soporte
para texto e imágenes utilizando archivos JSON para almacenar la información localmente.
Incluye compatibilidad con formatos anteriores, migración automática de datos, nueva
funcionalidad para envío conjunto de imagen con texto como caption y configuración
de preferencias del navegador.
CORREGIDO: Manejo correcto de eliminación de imágenes en la edición de mensajes.
"""

import json
import os
import shutil
from typing import List, Dict, Any, Tuple, Optional


class DataManager:
    """
    Clase para gestionar la persistencia de datos del bot
    Maneja contactos con nombre y número, mensajes con texto, imágenes, opciones de envío
    y configuraciones de automatización incluyendo preferencias del navegador
    """

    def __init__(self):
        """
        Inicializa el gestor de datos y crea los archivos si no existen
        """
        self.numbers_file = "numeros.json"
        self.messages_file = "mensajes.json"
        self.config_file = "config.json"
        self.images_folder = "imagenes_mensajes"

        # Crear archivos y carpetas si no existen
        self._initialize_files()
        self._create_images_folder()

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
        else:
            # Migrar formato de mensajes si es necesario
            self._migrate_messages_format()

        # Archivo de configuración
        if not os.path.exists(self.config_file):
            default_config = {
                "intervalo_min": 30,
                "intervalo_max": 60,
                "activo": False,
                "mantener_navegador_abierto": False  # NUEVO: Configuración del navegador
            }
            self._save_json(self.config_file, default_config)
        else:
            # NUEVO: Migrar configuración antigua si no tiene la nueva opción
            self._migrate_config_format()

    def _migrate_config_format(self):
        """
        NUEVO: Migra la configuración antigua para incluir la opción del navegador
        """
        try:
            config = self._load_json(self.config_file)

            # Si no tiene la nueva configuración, agregarla
            if "mantener_navegador_abierto" not in config:
                config["mantener_navegador_abierto"] = False
                self._save_json(self.config_file, config)
                print("Configuración actualizada con opción de navegador")

        except Exception as e:
            print(f"Error migrando configuración: {e}")
            # En caso de error, crear configuración por defecto
            default_config = {
                "intervalo_min": 30,
                "intervalo_max": 60,
                "activo": False,
                "mantener_navegador_abierto": False
            }
            self._save_json(self.config_file, default_config)

    def _create_images_folder(self):
        """
        Crea la carpeta para almacenar imágenes de mensajes
        """
        if not os.path.exists(self.images_folder):
            os.makedirs(self.images_folder)

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
            print(f"Error en migración de contactos: {e}")
            # En caso de error, crear estructura nueva
            self._save_json(self.numbers_file, {"contactos": []})

    def _migrate_messages_format(self):
        """
        Migra el formato de mensajes a la estructura más reciente con soporte para envío conjunto
        """
        try:
            data = self._load_json(self.messages_file)
            messages = data.get("mensajes", [])
            migrated = False

            # Verificar si hay mensajes en formato antiguo y migrarlos
            for i, message in enumerate(messages):
                # Formato muy antiguo (solo strings)
                if isinstance(message, str):
                    messages[i] = {
                        "texto": message,
                        "imagen": None,
                        "envio_conjunto": False  # Mantener comportamiento actual por defecto
                    }
                    migrated = True

                # Formato intermedio (texto + imagen, sin envio_conjunto)
                elif isinstance(message, dict) and "envio_conjunto" not in message:
                    messages[i] = {
                        "texto": message.get("texto", ""),
                        "imagen": message.get("imagen", None),
                        "envio_conjunto": False  # Mantener comportamiento actual por defecto
                    }
                    migrated = True

            # Guardar si se hizo alguna migración
            if migrated:
                self._save_json(self.messages_file, {"mensajes": messages})
                print("Mensajes migrados al formato con soporte para envío conjunto")

        except Exception as e:
            print(f"Error en migración de mensajes: {e}")
            # En caso de error, crear estructura nueva
            self._save_json(self.messages_file, {"mensajes": []})

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

    def _copy_image_to_folder(self, image_path: str) -> Optional[str]:
        """
        Copia una imagen a la carpeta de imágenes del bot

        Args:
            image_path: Ruta de la imagen original

        Returns:
            Nombre del archivo copiado o None si hay error
        """
        try:
            if not os.path.exists(image_path):
                return None

            # Generar nombre único para la imagen
            import time
            timestamp = str(int(time.time()))
            file_extension = os.path.splitext(image_path)[1].lower()
            new_filename = f"img_{timestamp}{file_extension}"
            destination = os.path.join(self.images_folder, new_filename)

            # Copiar archivo
            shutil.copy2(image_path, destination)
            return new_filename

        except Exception as e:
            print(f"Error al copiar imagen: {e}")
            return None

    def _delete_message_image(self, image_filename: str):
        """
        Elimina una imagen de mensaje de la carpeta

        Args:
            image_filename: Nombre del archivo de imagen
        """
        if image_filename:
            try:
                image_path = os.path.join(self.images_folder, image_filename)
                if os.path.exists(image_path):
                    os.remove(image_path)
            except Exception as e:
                print(f"Error al eliminar imagen {image_filename}: {e}")

    def get_image_path(self, image_filename: str) -> Optional[str]:
        """
        Obtiene la ruta completa de una imagen

        Args:
            image_filename: Nombre del archivo de imagen

        Returns:
            Ruta completa de la imagen o None si no existe
        """
        if not image_filename:
            return None

        image_path = os.path.join(self.images_folder, image_filename)
        return image_path if os.path.exists(image_path) else None

    # Gestión de contactos (sin cambios)
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

    # Métodos de compatibilidad para contactos
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

    # Gestión de mensajes (actualizada para soporte de envío conjunto)
    def get_messages(self) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de mensajes guardados con formato completo

        Returns:
            Lista de diccionarios con 'texto', 'imagen' y 'envio_conjunto'
        """
        data = self._load_json(self.messages_file)
        messages = data.get("mensajes", [])

        # Asegurar que todos los mensajes tengan el formato correcto
        formatted_messages = []
        for message in messages:
            if isinstance(message, str):
                # Formato muy antiguo - convertir
                formatted_messages.append({
                    "texto": message,
                    "imagen": None,
                    "envio_conjunto": False
                })
            elif isinstance(message, dict):
                # Asegurar que tenga todos los campos
                formatted_messages.append({
                    "texto": message.get("texto", ""),
                    "imagen": message.get("imagen", None),
                    "envio_conjunto": message.get("envio_conjunto", False)
                })

        return formatted_messages

    def get_messages_legacy(self) -> List[str]:
        """
        Método de compatibilidad: obtiene solo los textos de los mensajes

        Returns:
            Lista de strings con los textos de los mensajes
        """
        messages = self.get_messages()
        return [msg.get("texto", "") for msg in messages]

    def add_message(self, text: str, image_path: str = None, envio_conjunto: bool = False) -> bool:
        """
        Agrega un mensaje con texto, imagen opcional y configuración de envío

        Args:
            text: Texto del mensaje
            image_path: Ruta de la imagen (opcional)
            envio_conjunto: Si debe enviar imagen y texto juntos como caption

        Returns:
            True si se agregó correctamente
        """
        if not text.strip():
            return False

        # Procesar imagen si se proporciona
        image_filename = None
        if image_path and os.path.exists(image_path):
            image_filename = self._copy_image_to_folder(image_path)

        # Crear mensaje con nueva estructura
        new_message = {
            "texto": text.strip(),
            "imagen": image_filename,
            "envio_conjunto": envio_conjunto and image_filename is not None  # Solo puede ser True si hay imagen
        }

        # Agregar a la lista
        messages = self.get_messages()
        messages.append(new_message)
        self._save_json(self.messages_file, {"mensajes": messages})
        return True

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
            message = messages[index]

            # Eliminar imagen asociada si existe
            if message.get("imagen"):
                self._delete_message_image(message["imagen"])

            # Eliminar mensaje
            messages.pop(index)
            self._save_json(self.messages_file, {"mensajes": messages})
            return True
        return False

    def update_message(self, index: int, new_text: str, new_image_path: str = None,
                       envio_conjunto: bool = None) -> bool:
        """
        CORREGIDO: Actualiza un mensaje existente con soporte correcto para eliminación de imágenes

        Args:
            index: Índice del mensaje a actualizar
            new_text: Nuevo texto del mensaje
            new_image_path: Nueva ruta de imagen (None=no cambiar, ""=eliminar, ruta=cambiar)
            envio_conjunto: Nuevo modo de envío (None para mantener actual)

        Returns:
            True si se actualizó correctamente
        """
        if not new_text.strip():
            return False

        messages = self.get_messages()

        if not (0 <= index < len(messages)):
            return False

        current_message = messages[index]

        # CORREGIDO: Manejar imagen con lógica explícita para eliminación
        new_image_filename = current_message.get("imagen")  # Mantener la actual por defecto

        if new_image_path is not None:  # Se especificó cambio de imagen
            if new_image_path == "":
                # CASO 1: String vacío = eliminar imagen actual
                if current_message.get("imagen"):
                    self._delete_message_image(current_message["imagen"])
                new_image_filename = None
                print(f"[DataManager] Imagen eliminada del mensaje {index}")

            elif new_image_path and os.path.exists(new_image_path):
                # CASO 2: Nueva ruta válida = cambiar imagen
                # Eliminar imagen anterior si existe
                if current_message.get("imagen"):
                    self._delete_message_image(current_message["imagen"])
                # Agregar nueva imagen
                new_image_filename = self._copy_image_to_folder(new_image_path)
                print(f"[DataManager] Imagen cambiada en mensaje {index}")
            else:
                # CASO 3: Ruta inválida = mantener imagen actual (no hacer nada)
                print(f"[DataManager] Ruta de imagen inválida, manteniendo imagen actual")
        # Si new_image_path es None, mantener imagen actual (new_image_filename ya está establecido)

        # Determinar envio_conjunto
        final_envio_conjunto = current_message.get("envio_conjunto", False)
        if envio_conjunto is not None:
            # Solo puede ser True si hay imagen
            final_envio_conjunto = envio_conjunto and new_image_filename is not None

        # Actualizar mensaje
        messages[index] = {
            "texto": new_text.strip(),
            "imagen": new_image_filename,
            "envio_conjunto": final_envio_conjunto
        }

        self._save_json(self.messages_file, {"mensajes": messages})

        # Debug: confirmar el estado del mensaje actualizado
        print(
            f"[DataManager] Mensaje {index} actualizado - imagen: {new_image_filename}, envio_conjunto: {final_envio_conjunto}")

        return True

    def get_message_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene un mensaje por su índice

        Args:
            index: Índice del mensaje

        Returns:
            Diccionario con 'texto', 'imagen' y 'envio_conjunto' o None si no existe
        """
        messages = self.get_messages()
        if 0 <= index < len(messages):
            return messages[index].copy()
        return None

    # Gestión de configuración (actualizada con navegador)
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

    # NUEVOS: Métodos específicos para configuración del navegador
    def get_browser_keep_open_setting(self) -> bool:
        """
        NUEVO: Obtiene la configuración de mantener navegador abierto

        Returns:
            True si debe mantener el navegador abierto
        """
        config = self.get_config()
        return config.get("mantener_navegador_abierto", False)

    def set_browser_keep_open_setting(self, keep_open: bool):
        """
        NUEVO: Establece la configuración de mantener navegador abierto

        Args:
            keep_open: True para mantener navegador abierto, False para cerrar
        """
        config = self.get_config()
        config["mantener_navegador_abierto"] = keep_open
        self.save_config(config)