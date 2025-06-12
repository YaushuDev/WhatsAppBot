# whatsapp_session.py
"""
Gestor de sesión de WhatsApp Web para el Bot de WhatsApp
Este módulo se encarga exclusivamente de la gestión de la sesión de WhatsApp Web,
incluyendo la apertura inicial, manejo del código QR, detección de login exitoso,
verificación de estado de la interfaz y manejo de reconexiones automáticas.
"""

import time
from typing import Optional, Callable
from whatsapp_utils import WhatsAppConstants
from whatsapp_driver import ChromeDriverManager


class WhatsAppSession:
    """
    Gestor especializado para la sesión de WhatsApp Web
    """

    def __init__(self, driver_manager: ChromeDriverManager, status_callback: Optional[Callable] = None):
        """
        Inicializa el gestor de sesión

        Args:
            driver_manager: Instancia del gestor de Chrome
            status_callback: Función callback para reportar estado
        """
        self.driver_manager = driver_manager
        self.status_callback = status_callback
        self._is_logged_in = False
        self._session_validated = False

    def _update_status(self, message: str):
        """
        Actualiza el estado y notifica mediante callback

        Args:
            message: Mensaje de estado
        """
        print(f"[Session] {message}")
        if self.status_callback:
            self.status_callback(message)

    def open_whatsapp_web(self) -> bool:
        """
        Abre WhatsApp Web y gestiona el proceso de login completo

        Returns:
            True si se estableció la sesión correctamente
        """
        try:
            self._update_status("Abriendo WhatsApp Web...")

            # Verificar que el driver esté activo
            if not self.driver_manager.is_session_alive():
                self._update_status("Driver no activo")
                return False

            # Navegar a WhatsApp Web
            if not self.driver_manager.navigate_to(WhatsAppConstants.WHATSAPP_WEB_URL):
                return False

            # Detectar el estado actual de la página
            return self._handle_whatsapp_web_state()

        except Exception as e:
            self._update_status(f"Error al abrir WhatsApp Web: {str(e)}")
            return False

    def _handle_whatsapp_web_state(self) -> bool:
        """
        Maneja los diferentes estados posibles de WhatsApp Web

        Returns:
            True si se logró establecer la sesión
        """
        # Intentar detectar si ya está logueado
        if self._detect_main_interface():
            self._update_status("WhatsApp Web ya está logueado")
            self._is_logged_in = True
            self._session_validated = True
            return True

        # Si no está logueado, buscar QR code
        if self._detect_qr_code():
            return self._handle_qr_login()

        # Intentar esperar un poco más por si está cargando
        self._update_status("Esperando carga completa de WhatsApp Web...")
        time.sleep(3)

        # Intentar nuevamente
        if self._detect_main_interface():
            self._is_logged_in = True
            self._session_validated = True
            return True

        self._update_status("No se pudo determinar el estado de WhatsApp Web")
        return False

    def _detect_main_interface(self) -> bool:
        """
        Detecta si la interfaz principal de WhatsApp Web está cargada

        Returns:
            True si la interfaz principal está presente
        """
        try:
            # Buscar elementos de la interfaz principal
            main_element = self.driver_manager.wait_for_element(
                WhatsAppConstants.SELECTORS['search_box'],
                timeout=5
            )

            if main_element:
                return True

            # Buscar elementos alternativos de la interfaz principal
            alternative_selectors = [
                "//div[@title='Nueva conversación']",
                "//div[@contenteditable='true'][@data-tab='3']",
                "div[data-testid='chatlist']",
                "div[aria-label='Lista de conversaciones']"
            ]

            alternative_element = self.driver_manager.wait_for_element(
                alternative_selectors,
                timeout=3
            )

            return alternative_element is not None

        except Exception:
            return False

    def _detect_qr_code(self) -> bool:
        """
        Detecta si se está mostrando el código QR para login

        Returns:
            True si el código QR está presente
        """
        try:
            qr_selectors = [
                "canvas[aria-label='Scan me!']",
                "canvas",
                "//div[@data-ref]//canvas",
                "div[data-testid='qrcode']"
            ]

            qr_element = self.driver_manager.wait_for_element(qr_selectors, timeout=5)
            return qr_element is not None

        except Exception:
            return False

    def _handle_qr_login(self) -> bool:
        """
        Maneja el proceso de login mediante código QR

        Returns:
            True si el login fue exitoso
        """
        try:
            self._update_status("Código QR detectado. Escanea el código QR en WhatsApp Web para continuar")

            # Esperar hasta 60 segundos por el login
            max_wait_time = 60
            check_interval = 2
            checks_performed = 0
            max_checks = max_wait_time // check_interval

            while checks_performed < max_checks:
                # Verificar si ya se logueó
                if self._detect_main_interface():
                    self._update_status("QR escaneado correctamente, WhatsApp Web listo")
                    self._is_logged_in = True
                    self._session_validated = True
                    return True

                # Verificar si el QR sigue presente (no expiró)
                if not self._detect_qr_code():
                    # El QR desapareció, podría estar cargando
                    self._update_status("QR procesado, verificando login...")
                    time.sleep(3)

                    if self._detect_main_interface():
                        self._is_logged_in = True
                        self._session_validated = True
                        return True

                time.sleep(check_interval)
                checks_performed += 1

                # Mostrar progreso cada 10 segundos
                if checks_performed % 5 == 0:
                    remaining_time = max_wait_time - (checks_performed * check_interval)
                    self._update_status(f"Esperando escaneo del QR... ({remaining_time}s restantes)")

            self._update_status("Tiempo de espera del QR agotado")
            return False

        except Exception as e:
            self._update_status(f"Error durante login con QR: {str(e)}")
            return False

    def validate_session(self) -> bool:
        """
        Valida que la sesión actual sigue activa y funcional

        Returns:
            True si la sesión es válida
        """
        try:
            if not self.driver_manager.is_session_alive():
                self._session_validated = False
                self._is_logged_in = False
                return False

            # Verificar que la interfaz principal siga presente
            if self._detect_main_interface():
                self._session_validated = True
                return True

            # Si no encuentra la interfaz, podría ser un problema temporal
            self._update_status("Interfaz principal no detectada, verificando estado...")

            # Intentar refrescar o recargar si es necesario
            current_url = self.driver_manager.get_current_url()
            if current_url and "web.whatsapp.com" not in current_url:
                self._update_status("No estamos en WhatsApp Web, reestableciendo...")
                return self.open_whatsapp_web()

            self._session_validated = False
            return False

        except Exception as e:
            self._update_status(f"Error validando sesión: {str(e)}")
            self._session_validated = False
            return False

    def reconnect_if_needed(self) -> bool:
        """
        Reconecta a WhatsApp Web si la sesión se perdió

        Returns:
            True si la reconexión fue exitosa
        """
        try:
            self._update_status("Intentando reconexión...")

            if not self.driver_manager.is_session_alive():
                self._update_status("Driver no activo, reconexión no posible")
                return False

            # Intentar recargar la página
            return self.open_whatsapp_web()

        except Exception as e:
            self._update_status(f"Error en reconexión: {str(e)}")
            return False

    def is_logged_in(self) -> bool:
        """
        Verifica si el usuario está logueado

        Returns:
            True si está logueado
        """
        return self._is_logged_in

    def is_session_valid(self) -> bool:
        """
        Verifica si la sesión está validada y activa

        Returns:
            True si la sesión es válida
        """
        return self._session_validated and self._is_logged_in

    def refresh_session(self) -> bool:
        """
        Refresca la sesión actual

        Returns:
            True si el refresco fue exitoso
        """
        try:
            self._update_status("Refrescando sesión...")

            # Recargar página
            if not self.driver_manager.navigate_to(WhatsAppConstants.WHATSAPP_WEB_URL):
                return False

            # Esperar un momento para la carga
            time.sleep(WhatsAppConstants.MEDIUM_DELAY)

            # Validar nueva sesión
            return self.validate_session()

        except Exception as e:
            self._update_status(f"Error refrescando sesión: {str(e)}")
            return False

    def get_session_info(self) -> dict:
        """
        Obtiene información del estado actual de la sesión

        Returns:
            Diccionario con información de la sesión
        """
        return {
            'is_logged_in': self._is_logged_in,
            'session_validated': self._session_validated,
            'driver_active': self.driver_manager.is_session_alive(),
            'current_url': self.driver_manager.get_current_url(),
            'page_title': self.driver_manager.get_page_title()
        }