# gui.py
"""
Interfaz gráfica para el Bot de WhatsApp
Implementa una GUI con diseño nocturno y navegación por pestañas que permite
gestionar números, mensajes y controlar la automatización del bot de WhatsApp
utilizando Tkinter con un diseño moderno y minimalista
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from data_manager import DataManager
from whatsapp_bot import WhatsAppBot


class WhatsAppBotGUI:
    """
    Clase principal de la interfaz gráfica del bot de WhatsApp
    """

    def __init__(self):
        """
        Inicializa la interfaz gráfica y sus componentes
        """
        self.root = tk.Tk()
        self.data_manager = DataManager()
        self.whatsapp_bot = WhatsAppBot(status_callback=self.update_status)

        # Variables de estado
        self.current_tab = "numeros"
        self.automation_active = False

        # Configurar la ventana principal
        self._setup_window()

        # Configurar estilos
        self._setup_styles()

        # Crear la interfaz
        self._create_main_layout()

        # Crear las pestañas
        self._create_sidebar()
        self._create_content_area()

        # Mostrar la pestaña inicial
        self.show_tab("numeros")

    def _setup_window(self):
        """
        Configura la ventana principal con diseño nocturno y tamaño fijo
        """
        # Configuración básica
        self.root.title("Bot de WhatsApp")
        self.root.geometry("900x600")
        self.root.resizable(False, False)

        # Intentar cargar el icono
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass  # Si no existe el icono, continúa sin él

        # Colores del tema nocturno
        self.colors = {
            "bg_primary": "#1e1e1e",  # Fondo principal
            "bg_secondary": "#2d2d2d",  # Fondo secundario
            "bg_accent": "#3d3d3d",  # Fondo de acento
            "text_primary": "#ffffff",  # Texto principal
            "text_secondary": "#cccccc",  # Texto secundario
            "accent": "#0078d4",  # Color de acento azul
            "accent_hover": "#106ebe",  # Color de acento hover
            "success": "#107c10",  # Verde éxito
            "warning": "#ff8c00",  # Naranja advertencia
            "error": "#d13438",  # Rojo error
            "border": "#404040"  # Borde
        }

        # Configurar el fondo de la ventana
        self.root.configure(bg=self.colors["bg_primary"])

        # Manejar el cierre de la ventana
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _setup_styles(self):
        """
        Configura los estilos personalizados para ttk widgets
        """
        style = ttk.Style()

        # Configurar estilos para el tema nocturno
        style.configure("Sidebar.TFrame", background=self.colors["bg_secondary"])
        style.configure("Content.TFrame", background=self.colors["bg_primary"])
        style.configure("SidebarButton.TButton",
                        background=self.colors["bg_secondary"],
                        foreground=self.colors["text_primary"],
                        borderwidth=0,
                        focuscolor='none')
        style.map("SidebarButton.TButton",
                  background=[('active', self.colors["bg_accent"])])

        style.configure("ActiveSidebarButton.TButton",
                        background=self.colors["accent"],
                        foreground=self.colors["text_primary"],
                        borderwidth=0,
                        focuscolor='none')

        style.configure("Action.TButton",
                        background=self.colors["accent"],
                        foreground=self.colors["text_primary"],
                        borderwidth=1,
                        focuscolor='none')
        style.map("Action.TButton",
                  background=[('active', self.colors["accent_hover"])])

    def _create_main_layout(self):
        """
        Crea el layout principal con barra lateral y área de contenido
        """
        # Frame principal
        self.main_frame = tk.Frame(self.root, bg=self.colors["bg_primary"])
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Barra lateral (200px de ancho)
        self.sidebar = tk.Frame(self.main_frame,
                                bg=self.colors["bg_secondary"],
                                width=200)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 1))
        self.sidebar.pack_propagate(False)

        # Área de contenido
        self.content_area = tk.Frame(self.main_frame,
                                     bg=self.colors["bg_primary"])
        self.content_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def _create_sidebar(self):
        """
        Crea la barra lateral con los botones de navegación
        """
        # Título
        title_label = tk.Label(self.sidebar,
                               text="WhatsApp Bot",
                               font=("Segoe UI", 16, "bold"),
                               bg=self.colors["bg_secondary"],
                               fg=self.colors["text_primary"])
        title_label.pack(pady=(20, 30))

        # Botones de navegación
        self.nav_buttons = {}

        # Botón Números
        self.nav_buttons["numeros"] = tk.Button(
            self.sidebar,
            text="📱 Números",
            font=("Segoe UI", 11),
            bg=self.colors["bg_secondary"],
            fg=self.colors["text_primary"],
            border=0,
            pady=15,
            cursor="hand2",
            command=lambda: self.show_tab("numeros")
        )
        self.nav_buttons["numeros"].pack(fill=tk.X, padx=10, pady=5)

        # Botón Mensajes
        self.nav_buttons["mensajes"] = tk.Button(
            self.sidebar,
            text="💬 Mensajes",
            font=("Segoe UI", 11),
            bg=self.colors["bg_secondary"],
            fg=self.colors["text_primary"],
            border=0,
            pady=15,
            cursor="hand2",
            command=lambda: self.show_tab("mensajes")
        )
        self.nav_buttons["mensajes"].pack(fill=tk.X, padx=10, pady=5)

        # Botón Automatización
        self.nav_buttons["automatizacion"] = tk.Button(
            self.sidebar,
            text="🤖 Automatización",
            font=("Segoe UI", 11),
            bg=self.colors["bg_secondary"],
            fg=self.colors["text_primary"],
            border=0,
            pady=15,
            cursor="hand2",
            command=lambda: self.show_tab("automatizacion")
        )
        self.nav_buttons["automatizacion"].pack(fill=tk.X, padx=10, pady=5)

        # Espaciador
        spacer = tk.Frame(self.sidebar, bg=self.colors["bg_secondary"])
        spacer.pack(fill=tk.BOTH, expand=True)

        # Información de estado en la parte inferior
        self.status_label = tk.Label(self.sidebar,
                                     text="Listo",
                                     font=("Segoe UI", 9),
                                     bg=self.colors["bg_secondary"],
                                     fg=self.colors["text_secondary"],
                                     wraplength=180)
        self.status_label.pack(side=tk.BOTTOM, pady=10, padx=10)

    def _create_content_area(self):
        """
        Crea el área de contenido donde se mostrarán las pestañas
        """
        # Contenedor para las pestañas
        self.tab_frames = {}

        # Crear las pestañas
        self._create_numbers_tab()
        self._create_messages_tab()
        self._create_automation_tab()

    def _create_numbers_tab(self):
        """
        Crea la pestaña de gestión de números de teléfono
        """
        # Frame principal de la pestaña
        self.tab_frames["numeros"] = tk.Frame(self.content_area,
                                              bg=self.colors["bg_primary"])

        frame = self.tab_frames["numeros"]

        # Título
        title = tk.Label(frame,
                         text="Gestión de Números",
                         font=("Segoe UI", 18, "bold"),
                         bg=self.colors["bg_primary"],
                         fg=self.colors["text_primary"])
        title.pack(pady=(20, 10))

        # Descripción
        desc = tk.Label(frame,
                        text="Agrega y gestiona los números de teléfono a los que se enviarán mensajes",
                        font=("Segoe UI", 10),
                        bg=self.colors["bg_primary"],
                        fg=self.colors["text_secondary"])
        desc.pack(pady=(0, 20))

        # Frame para agregar número
        add_frame = tk.Frame(frame, bg=self.colors["bg_primary"])
        add_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(add_frame,
                 text="Número de teléfono:",
                 font=("Segoe UI", 10),
                 bg=self.colors["bg_primary"],
                 fg=self.colors["text_primary"]).pack(anchor="w")

        input_frame = tk.Frame(add_frame, bg=self.colors["bg_primary"])
        input_frame.pack(fill=tk.X, pady=(5, 0))

        self.number_entry = tk.Entry(input_frame,
                                     font=("Segoe UI", 10),
                                     bg=self.colors["bg_secondary"],
                                     fg=self.colors["text_primary"],
                                     border=1,
                                     relief="solid")
        self.number_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.number_entry.bind("<Return>", lambda e: self.add_number())

        add_btn = tk.Button(input_frame,
                            text="Agregar",
                            font=("Segoe UI", 10),
                            bg=self.colors["accent"],
                            fg=self.colors["text_primary"],
                            border=0,
                            pady=8,
                            padx=15,
                            cursor="hand2",
                            command=self.add_number)
        add_btn.pack(side=tk.RIGHT)

        # Lista de números
        list_frame = tk.Frame(frame, bg=self.colors["bg_primary"])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        tk.Label(list_frame,
                 text="Números guardados:",
                 font=("Segoe UI", 10),
                 bg=self.colors["bg_primary"],
                 fg=self.colors["text_primary"]).pack(anchor="w", pady=(0, 5))

        # Listbox con scrollbar
        listbox_frame = tk.Frame(list_frame, bg=self.colors["bg_primary"])
        listbox_frame.pack(fill=tk.BOTH, expand=True)

        self.numbers_listbox = tk.Listbox(listbox_frame,
                                          font=("Segoe UI", 10),
                                          bg=self.colors["bg_secondary"],
                                          fg=self.colors["text_primary"],
                                          selectbackground=self.colors["accent"],
                                          border=1,
                                          relief="solid")
        self.numbers_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar_numbers = tk.Scrollbar(listbox_frame, orient="vertical")
        scrollbar_numbers.pack(side=tk.RIGHT, fill=tk.Y)

        self.numbers_listbox.config(yscrollcommand=scrollbar_numbers.set)
        scrollbar_numbers.config(command=self.numbers_listbox.yview)

        # Botón eliminar
        delete_btn = tk.Button(list_frame,
                               text="Eliminar Seleccionado",
                               font=("Segoe UI", 10),
                               bg=self.colors["error"],
                               fg=self.colors["text_primary"],
                               border=0,
                               pady=8,
                               cursor="hand2",
                               command=self.delete_number)
        delete_btn.pack(pady=(10, 0))

        # Cargar números existentes
        self.refresh_numbers_list()

    def _create_messages_tab(self):
        """
        Crea la pestaña de gestión de mensajes
        """
        # Frame principal de la pestaña
        self.tab_frames["mensajes"] = tk.Frame(self.content_area,
                                               bg=self.colors["bg_primary"])

        frame = self.tab_frames["mensajes"]

        # Título
        title = tk.Label(frame,
                         text="Gestión de Mensajes",
                         font=("Segoe UI", 18, "bold"),
                         bg=self.colors["bg_primary"],
                         fg=self.colors["text_primary"])
        title.pack(pady=(20, 10))

        # Descripción
        desc = tk.Label(frame,
                        text="Crea y gestiona los mensajes que el bot enviará aleatoriamente",
                        font=("Segoe UI", 10),
                        bg=self.colors["bg_primary"],
                        fg=self.colors["text_secondary"])
        desc.pack(pady=(0, 20))

        # Frame para agregar mensaje
        add_frame = tk.Frame(frame, bg=self.colors["bg_primary"])
        add_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(add_frame,
                 text="Nuevo mensaje:",
                 font=("Segoe UI", 10),
                 bg=self.colors["bg_primary"],
                 fg=self.colors["text_primary"]).pack(anchor="w")

        # Área de texto para el mensaje
        self.message_text = scrolledtext.ScrolledText(add_frame,
                                                      height=4,
                                                      font=("Segoe UI", 10),
                                                      bg=self.colors["bg_secondary"],
                                                      fg=self.colors["text_primary"],
                                                      border=1,
                                                      relief="solid",
                                                      wrap=tk.WORD)
        self.message_text.pack(fill=tk.X, pady=(5, 10))

        add_msg_btn = tk.Button(add_frame,
                                text="Agregar Mensaje",
                                font=("Segoe UI", 10),
                                bg=self.colors["accent"],
                                fg=self.colors["text_primary"],
                                border=0,
                                pady=8,
                                padx=15,
                                cursor="hand2",
                                command=self.add_message)
        add_msg_btn.pack()

        # Lista de mensajes
        list_frame = tk.Frame(frame, bg=self.colors["bg_primary"])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        tk.Label(list_frame,
                 text="Mensajes guardados:",
                 font=("Segoe UI", 10),
                 bg=self.colors["bg_primary"],
                 fg=self.colors["text_primary"]).pack(anchor="w", pady=(0, 5))

        # Listbox para mensajes
        listbox_frame = tk.Frame(list_frame, bg=self.colors["bg_primary"])
        listbox_frame.pack(fill=tk.BOTH, expand=True)

        self.messages_listbox = tk.Listbox(listbox_frame,
                                           font=("Segoe UI", 10),
                                           bg=self.colors["bg_secondary"],
                                           fg=self.colors["text_primary"],
                                           selectbackground=self.colors["accent"],
                                           border=1,
                                           relief="solid")
        self.messages_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar_messages = tk.Scrollbar(listbox_frame, orient="vertical")
        scrollbar_messages.pack(side=tk.RIGHT, fill=tk.Y)

        self.messages_listbox.config(yscrollcommand=scrollbar_messages.set)
        scrollbar_messages.config(command=self.messages_listbox.yview)

        # Botones de acción
        buttons_frame = tk.Frame(list_frame, bg=self.colors["bg_primary"])
        buttons_frame.pack(pady=(10, 0))

        edit_btn = tk.Button(buttons_frame,
                             text="Editar",
                             font=("Segoe UI", 10),
                             bg=self.colors["warning"],
                             fg=self.colors["text_primary"],
                             border=0,
                             pady=8,
                             padx=15,
                             cursor="hand2",
                             command=self.edit_message)
        edit_btn.pack(side=tk.LEFT, padx=(0, 10))

        delete_msg_btn = tk.Button(buttons_frame,
                                   text="Eliminar",
                                   font=("Segoe UI", 10),
                                   bg=self.colors["error"],
                                   fg=self.colors["text_primary"],
                                   border=0,
                                   pady=8,
                                   padx=15,
                                   cursor="hand2",
                                   command=self.delete_message)
        delete_msg_btn.pack(side=tk.LEFT)

        # Cargar mensajes existentes
        self.refresh_messages_list()

    def _create_automation_tab(self):
        """
        Crea la pestaña de automatización
        """
        # Frame principal de la pestaña
        self.tab_frames["automatizacion"] = tk.Frame(self.content_area,
                                                     bg=self.colors["bg_primary"])

        frame = self.tab_frames["automatizacion"]

        # Título
        title = tk.Label(frame,
                         text="Automatización",
                         font=("Segoe UI", 18, "bold"),
                         bg=self.colors["bg_primary"],
                         fg=self.colors["text_primary"])
        title.pack(pady=(20, 10))

        # Descripción
        desc = tk.Label(frame,
                        text="Controla la automatización del envío de mensajes",
                        font=("Segoe UI", 10),
                        bg=self.colors["bg_primary"],
                        fg=self.colors["text_secondary"])
        desc.pack(pady=(0, 30))

        # Configuración
        config_frame = tk.LabelFrame(frame,
                                     text="Configuración",
                                     font=("Segoe UI", 12, "bold"),
                                     bg=self.colors["bg_primary"],
                                     fg=self.colors["text_primary"],
                                     border=1,
                                     relief="solid")
        config_frame.pack(fill=tk.X, padx=20, pady=10)

        # Intervalos
        intervals_frame = tk.Frame(config_frame, bg=self.colors["bg_primary"])
        intervals_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(intervals_frame,
                 text="Intervalo entre mensajes (segundos):",
                 font=("Segoe UI", 10),
                 bg=self.colors["bg_primary"],
                 fg=self.colors["text_primary"]).pack(anchor="w")

        interval_inputs = tk.Frame(intervals_frame, bg=self.colors["bg_primary"])
        interval_inputs.pack(fill=tk.X, pady=(5, 0))

        tk.Label(interval_inputs,
                 text="Mínimo:",
                 font=("Segoe UI", 10),
                 bg=self.colors["bg_primary"],
                 fg=self.colors["text_primary"]).pack(side=tk.LEFT)

        self.min_interval = tk.Entry(interval_inputs,
                                     font=("Segoe UI", 10),
                                     bg=self.colors["bg_secondary"],
                                     fg=self.colors["text_primary"],
                                     width=10,
                                     border=1,
                                     relief="solid")
        self.min_interval.pack(side=tk.LEFT, padx=(5, 15))
        self.min_interval.insert(0, "30")

        tk.Label(interval_inputs,
                 text="Máximo:",
                 font=("Segoe UI", 10),
                 bg=self.colors["bg_primary"],
                 fg=self.colors["text_primary"]).pack(side=tk.LEFT)

        self.max_interval = tk.Entry(interval_inputs,
                                     font=("Segoe UI", 10),
                                     bg=self.colors["bg_secondary"],
                                     fg=self.colors["text_primary"],
                                     width=10,
                                     border=1,
                                     relief="solid")
        self.max_interval.pack(side=tk.LEFT, padx=(5, 0))
        self.max_interval.insert(0, "60")

        # Estadísticas
        stats_frame = tk.LabelFrame(frame,
                                    text="Estadísticas",
                                    font=("Segoe UI", 12, "bold"),
                                    bg=self.colors["bg_primary"],
                                    fg=self.colors["text_primary"],
                                    border=1,
                                    relief="solid")
        stats_frame.pack(fill=tk.X, padx=20, pady=10)

        stats_content = tk.Frame(stats_frame, bg=self.colors["bg_primary"])
        stats_content.pack(fill=tk.X, padx=10, pady=10)

        self.stats_numbers = tk.Label(stats_content,
                                      text="Números: 0",
                                      font=("Segoe UI", 10),
                                      bg=self.colors["bg_primary"],
                                      fg=self.colors["text_primary"])
        self.stats_numbers.pack(anchor="w")

        self.stats_messages = tk.Label(stats_content,
                                       text="Mensajes: 0",
                                       font=("Segoe UI", 10),
                                       bg=self.colors["bg_primary"],
                                       fg=self.colors["text_primary"])
        self.stats_messages.pack(anchor="w")

        # Control de automatización
        control_frame = tk.Frame(frame, bg=self.colors["bg_primary"])
        control_frame.pack(fill=tk.X, padx=20, pady=20)

        self.start_btn = tk.Button(control_frame,
                                   text="▶ Iniciar Automatización",
                                   font=("Segoe UI", 12, "bold"),
                                   bg=self.colors["success"],
                                   fg=self.colors["text_primary"],
                                   border=0,
                                   pady=15,
                                   cursor="hand2",
                                   command=self.start_automation)
        self.start_btn.pack(fill=tk.X, pady=(0, 10))

        self.stop_btn = tk.Button(control_frame,
                                  text="⏹ Detener Automatización",
                                  font=("Segoe UI", 12, "bold"),
                                  bg=self.colors["error"],
                                  fg=self.colors["text_primary"],
                                  border=0,
                                  pady=15,
                                  cursor="hand2",
                                  command=self.stop_automation,
                                  state="disabled")
        self.stop_btn.pack(fill=tk.X)

        # Log de actividad
        log_frame = tk.LabelFrame(frame,
                                  text="Registro de Actividad",
                                  font=("Segoe UI", 12, "bold"),
                                  bg=self.colors["bg_primary"],
                                  fg=self.colors["text_primary"],
                                  border=1,
                                  relief="solid")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 20))

        self.log_text = scrolledtext.ScrolledText(log_frame,
                                                  height=8,
                                                  font=("Consolas", 9),
                                                  bg=self.colors["bg_secondary"],
                                                  fg=self.colors["text_primary"],
                                                  border=0,
                                                  state="disabled",
                                                  wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Actualizar estadísticas
        self.update_stats()

    def show_tab(self, tab_name):
        """
        Muestra la pestaña especificada y actualiza la navegación

        Args:
            tab_name: Nombre de la pestaña a mostrar
        """
        # Ocultar todas las pestañas
        for frame in self.tab_frames.values():
            frame.pack_forget()

        # Mostrar la pestaña seleccionada
        if tab_name in self.tab_frames:
            self.tab_frames[tab_name].pack(fill=tk.BOTH, expand=True)
            self.current_tab = tab_name

        # Actualizar estilos de los botones
        for name, button in self.nav_buttons.items():
            if name == tab_name:
                button.configure(bg=self.colors["accent"])
            else:
                button.configure(bg=self.colors["bg_secondary"])

    def add_number(self):
        """
        Agrega un número de teléfono a la lista
        """
        number = self.number_entry.get().strip()

        if not number:
            messagebox.showwarning("Advertencia", "Por favor ingresa un número de teléfono")
            return

        if self.data_manager.add_number(number):
            self.number_entry.delete(0, tk.END)
            self.refresh_numbers_list()
            self.update_stats()
            messagebox.showinfo("Éxito", "Número agregado correctamente")
        else:
            messagebox.showerror("Error", "El número ya existe o es inválido")

    def delete_number(self):
        """
        Elimina el número seleccionado
        """
        selection = self.numbers_listbox.curselection()

        if not selection:
            messagebox.showwarning("Advertencia", "Por favor selecciona un número para eliminar")
            return

        number = self.numbers_listbox.get(selection[0])

        if messagebox.askyesno("Confirmar", f"¿Eliminar el número {number}?"):
            if self.data_manager.remove_number(number):
                self.refresh_numbers_list()
                self.update_stats()
                messagebox.showinfo("Éxito", "Número eliminado correctamente")

    def refresh_numbers_list(self):
        """
        Actualiza la lista de números en la interfaz
        """
        self.numbers_listbox.delete(0, tk.END)
        numbers = self.data_manager.get_numbers()

        for number in numbers:
            self.numbers_listbox.insert(tk.END, number)

    def add_message(self):
        """
        Agrega un mensaje a la lista
        """
        message = self.message_text.get(1.0, tk.END).strip()

        if not message:
            messagebox.showwarning("Advertencia", "Por favor ingresa un mensaje")
            return

        if self.data_manager.add_message(message):
            self.message_text.delete(1.0, tk.END)
            self.refresh_messages_list()
            self.update_stats()
            messagebox.showinfo("Éxito", "Mensaje agregado correctamente")
        else:
            messagebox.showerror("Error", "Error al agregar el mensaje")

    def edit_message(self):
        """
        Edita el mensaje seleccionado
        """
        selection = self.messages_listbox.curselection()

        if not selection:
            messagebox.showwarning("Advertencia", "Por favor selecciona un mensaje para editar")
            return

        index = selection[0]
        current_message = self.data_manager.get_messages()[index]

        # Crear ventana de edición
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Editar Mensaje")
        edit_window.geometry("400x300")
        edit_window.resizable(False, False)
        edit_window.configure(bg=self.colors["bg_primary"])
        edit_window.grab_set()

        tk.Label(edit_window,
                 text="Editar mensaje:",
                 font=("Segoe UI", 10),
                 bg=self.colors["bg_primary"],
                 fg=self.colors["text_primary"]).pack(pady=10)

        edit_text = scrolledtext.ScrolledText(edit_window,
                                              height=10,
                                              font=("Segoe UI", 10),
                                              bg=self.colors["bg_secondary"],
                                              fg=self.colors["text_primary"],
                                              wrap=tk.WORD)
        edit_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        edit_text.insert(1.0, current_message)

        def save_edit():
            new_message = edit_text.get(1.0, tk.END).strip()
            if new_message and self.data_manager.update_message(index, new_message):
                self.refresh_messages_list()
                self.update_stats()
                edit_window.destroy()
                messagebox.showinfo("Éxito", "Mensaje actualizado correctamente")
            else:
                messagebox.showerror("Error", "Error al actualizar el mensaje")

        tk.Button(edit_window,
                  text="Guardar",
                  font=("Segoe UI", 10),
                  bg=self.colors["accent"],
                  fg=self.colors["text_primary"],
                  border=0,
                  pady=8,
                  padx=15,
                  cursor="hand2",
                  command=save_edit).pack(pady=10)

    def delete_message(self):
        """
        Elimina el mensaje seleccionado
        """
        selection = self.messages_listbox.curselection()

        if not selection:
            messagebox.showwarning("Advertencia", "Por favor selecciona un mensaje para eliminar")
            return

        if messagebox.askyesno("Confirmar", "¿Eliminar el mensaje seleccionado?"):
            if self.data_manager.remove_message(selection[0]):
                self.refresh_messages_list()
                self.update_stats()
                messagebox.showinfo("Éxito", "Mensaje eliminado correctamente")

    def refresh_messages_list(self):
        """
        Actualiza la lista de mensajes en la interfaz
        """
        self.messages_listbox.delete(0, tk.END)
        messages = self.data_manager.get_messages()

        for i, message in enumerate(messages):
            # Mostrar solo las primeras 50 caracteres
            display_text = message[:50] + "..." if len(message) > 50 else message
            self.messages_listbox.insert(tk.END, f"{i + 1}. {display_text}")

    def start_automation(self):
        """
        Inicia la automatización
        """
        numbers = self.data_manager.get_numbers()
        messages = self.data_manager.get_messages()

        if not numbers:
            messagebox.showerror("Error", "No hay números configurados")
            return

        if not messages:
            messagebox.showerror("Error", "No hay mensajes configurados")
            return

        try:
            min_interval = int(self.min_interval.get())
            max_interval = int(self.max_interval.get())

            if min_interval <= 0 or max_interval <= 0 or min_interval > max_interval:
                messagebox.showerror("Error",
                                     "Los intervalos deben ser números positivos y el mínimo debe ser menor al máximo")
                return
        except ValueError:
            messagebox.showerror("Error", "Los intervalos deben ser números válidos")
            return

        # Iniciar automatización
        self.automation_active = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

        # Iniciar en un hilo separado
        threading.Thread(target=self._start_automation_thread,
                         args=(numbers, messages, min_interval, max_interval),
                         daemon=True).start()

    def _start_automation_thread(self, numbers, messages, min_interval, max_interval):
        """
        Hilo para ejecutar la automatización
        """
        try:
            self.whatsapp_bot.start_automation(numbers, messages, min_interval, max_interval)
        except Exception as e:
            self.update_status(f"Error en automatización: {e}")
        finally:
            self.automation_active = False
            self.root.after(0, self._automation_finished)

    def _automation_finished(self):
        """
        Callback cuando termina la automatización
        """
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.automation_active = False

    def stop_automation(self):
        """
        Detiene la automatización
        """
        self.whatsapp_bot.stop_automation()
        self.automation_active = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")

    def update_stats(self):
        """
        Actualiza las estadísticas mostradas
        """
        if hasattr(self, 'stats_numbers'):
            numbers_count = len(self.data_manager.get_numbers())
            messages_count = len(self.data_manager.get_messages())

            self.stats_numbers.configure(text=f"Números: {numbers_count}")
            self.stats_messages.configure(text=f"Mensajes: {messages_count}")

    def update_status(self, message):
        """
        Actualiza el estado y el log de actividad

        Args:
            message: Mensaje de estado
        """
        # Actualizar label de estado
        if hasattr(self, 'status_label'):
            # Limitar la longitud del mensaje para el label
            short_message = message[:30] + "..." if len(message) > 30 else message
            self.status_label.configure(text=short_message)

        # Actualizar log de actividad
        if hasattr(self, 'log_text'):
            self.log_text.configure(state="normal")
            self.log_text.insert(tk.END, f"{message}\n")
            self.log_text.see(tk.END)
            self.log_text.configure(state="disabled")

    def on_closing(self):
        """
        Maneja el cierre de la aplicación
        """
        if self.automation_active:
            if messagebox.askyesno("Confirmar",
                                   "La automatización está en ejecución. ¿Deseas detenerla y cerrar la aplicación?"):
                self.stop_automation()
                self.whatsapp_bot.close()
                self.root.destroy()
        else:
            self.whatsapp_bot.close()
            self.root.destroy()

    def run(self):
        """
        Inicia la aplicación
        """
        self.root.mainloop()