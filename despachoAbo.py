import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import hashlib
import re


# Configuración inicial de la base de datos
def inicializar_base_datos():
    conn = sqlite3.connect('despacho_abogados.db')
    cursor = conn.cursor()

    # Crear tabla de usuarios
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        nombre TEXT NOT NULL,
        rol TEXT CHECK(rol IN ('admin', 'abogado', 'asistente')) NOT NULL
    )
    ''')

    # Crear tabla de clientes
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        telefono TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        creado_por INTEGER,
        FOREIGN KEY (creado_por) REFERENCES usuarios (id)
    )
    ''')

    # Crear tabla de casos legales
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS casos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER NOT NULL,
        titulo TEXT NOT NULL,
        descripcion TEXT,
        estado TEXT CHECK(estado IN ('Abierto', 'Cerrado', 'En Proceso')) NOT NULL,
        fecha_inicio DATE NOT NULL,
        fecha_fin DATE,
        asignado_a INTEGER,
        FOREIGN KEY (cliente_id) REFERENCES clientes (id),
        FOREIGN KEY (asignado_a) REFERENCES usuarios (id)
    )
    ''')

    # Insertar usuario admin por defecto si no existe
    cursor.execute('SELECT COUNT(*) FROM usuarios WHERE username = "admin"')
    if cursor.fetchone()[0] == 0:
        password_hash = hashlib.sha256("admin123".encode()).hexdigest()
        cursor.execute('''
        INSERT INTO usuarios (username, password_hash, nombre, rol)
        VALUES (?, ?, ?, ?)
        ''', ("admin", password_hash, "Administrador", "admin"))
        conn.commit()

    return conn, cursor


# Clase para manejar la autenticación
class Autenticacion:
    def __init__(self, conn, cursor):
        self.conn = conn
        self.cursor = cursor
        self.usuario_actual = None

    def validar_login(self, username, password):
        if not username or not password:
            return False, "Debe ingresar usuario y contraseña"

        self.cursor.execute('SELECT id, username, password_hash, nombre, rol FROM usuarios WHERE username = ?',
                            (username,))
        usuario = self.cursor.fetchone()

        if not usuario:
            return False, "Usuario no encontrado"

        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if password_hash != usuario[2]:
            return False, "Contraseña incorrecta"

        self.usuario_actual = {
            'id': usuario[0],
            'username': usuario[1],
            'nombre': usuario[3],
            'rol': usuario[4]
        }
        return True, "Inicio de sesión exitoso"

    def cerrar_sesion(self):
        self.usuario_actual = None


# Ventana de login
class LoginWindow:
    def __init__(self, root, auth, on_login_success):
        self.root = root
        self.auth = auth
        self.on_login_success = on_login_success

        self.window = tb.Toplevel(root)
        self.window.title("Inicio de Sesión")
        self.window.geometry("400x300")
        self.window.resizable(False, False)
        self.window.grab_set()  # Hace la ventana modal

        # Centrar la ventana
        window_width = self.window.winfo_reqwidth()
        window_height = self.window.winfo_reqheight()
        position_right = int(self.window.winfo_screenwidth() / 2 - window_width / 2)
        position_down = int(self.window.winfo_screenheight() / 2 - window_height / 2)
        self.window.geometry(f"+{position_right}+{position_down}")

        # Frame principal
        frame = tb.Frame(self.window, padding=20)
        frame.pack(fill='both', expand=True)

        # Logo o título
        tb.Label(frame, text="Despacho Legal", font=('Helvetica', 18, 'bold'),
                 bootstyle="primary").pack(pady=10)

        # Campos de login
        tb.Label(frame, text="Usuario:").pack(pady=(10, 0), anchor='w')
        self.username_entry = tb.Entry(frame, width=30)
        self.username_entry.pack(pady=5)

        tb.Label(frame, text="Contraseña:").pack(pady=(10, 0), anchor='w')
        self.password_entry = tb.Entry(frame, width=30, show="*")
        self.password_entry.pack(pady=5)

        # Botón de login
        login_btn = tb.Button(frame, text="Iniciar Sesión",
                              command=self.intentar_login, bootstyle="success")
        login_btn.pack(pady=20)

        # Manejar tecla Enter
        self.window.bind('<Return>', lambda event: self.intentar_login())

    def intentar_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        success, msg = self.auth.validar_login(username, password)
        if success:
            messagebox.showinfo("Éxito", msg)
            self.window.destroy()
            self.on_login_success()
        else:
            messagebox.showerror("Error", msg)


# Estilo y configuración de la aplicación
def configurar_interfaz():
    app = tb.Window(themename="litera")
    app.title("Despacho Legal - Sistema de Gestión")
    app.geometry("800x700")
    app.resizable(True, True)

    # Configurar estilo
    estilo = tb.Style()
    estilo.configure('TFrame', padding=10)
    estilo.configure('TLabel', font=('Helvetica', 10))
    estilo.configure('TButton', font=('Helvetica', 10))

    return app


# Funciones para la gestión de clientes
class ClienteManager:
    def __init__(self, conn, cursor, auth):
        self.conn = conn
        self.cursor = cursor
        self.auth = auth

    def validar_datos_cliente(self, nombre, telefono, email):
        if not nombre or not telefono or not email:
            return False, "Todos los campos son obligatorios"

        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            return False, "El email no tiene un formato válido"

        if not re.match(r'^[\d\s\+\-]+$', telefono):
            return False, "El teléfono solo puede contener números, espacios y los caracteres + -"

        return True, "Datos válidos"

    def agregar_cliente(self, datos):
        try:
            self.cursor.execute('''
            INSERT INTO clientes (nombre, telefono, email, creado_por)
            VALUES (?, ?, ?, ?)
            ''', datos)
            self.conn.commit()
            return True, "Cliente agregado exitosamente."
        except sqlite3.IntegrityError:
            return False, "El email ya está registrado."
        except Exception as e:
            return False, f"Error al agregar cliente: {str(e)}"

    def consultar_clientes(self):
        if self.auth.usuario_actual['rol'] == 'admin':
            self.cursor.execute('SELECT * FROM clientes ORDER BY nombre')
        else:
            self.cursor.execute('''
            SELECT * FROM clientes 
            WHERE creado_por = ?
            ORDER BY nombre
            ''', (self.auth.usuario_actual['id'],))
        return self.cursor.fetchall()

    def eliminar_cliente(self, cliente_id):
        try:
            if self.auth.usuario_actual['rol'] != 'admin':
                # Verificar que el cliente fue creado por el usuario actual
                self.cursor.execute('SELECT creado_por FROM clientes WHERE id = ?', (cliente_id,))
                resultado = self.cursor.fetchone()
                if not resultado or resultado[0] != self.auth.usuario_actual['id']:
                    return False, "No tiene permisos para eliminar este cliente"

            self.cursor.execute('DELETE FROM clientes WHERE id = ?', (cliente_id,))
            self.conn.commit()
            return True, "Cliente eliminado correctamente." if self.cursor.rowcount > 0 else (
                False, "No se encontró el cliente.")
        except Exception as e:
            return False, f"Error al eliminar cliente: {str(e)}"


# Funciones para la gestión de casos
class CasoManager:
    def __init__(self, conn, cursor, auth):
        self.conn = conn
        self.cursor = cursor
        self.auth = auth

    def validar_datos_caso(self, cliente_id, titulo, estado, fecha_inicio, fecha_fin=None):
        try:
            cliente_id = int(cliente_id)
        except ValueError:
            return False, "El ID del cliente debe ser un número"

        if not titulo or not estado or not fecha_inicio:
            return False, "Título, estado y fecha de inicio son obligatorios"

        if estado not in ['Abierto', 'Cerrado', 'En Proceso']:
            return False, "Estado no válido"

        # Validar formato de fechas (simple)
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', fecha_inicio):
            return False, "Formato de fecha inválido (YYYY-MM-DD)"

        if fecha_fin and not re.match(r'^\d{4}-\d{2}-\d{2}$', fecha_fin):
            return False, "Formato de fecha inválido (YYYY-MM-DD)"

        return True, "Datos válidos"

    def agregar_caso(self, datos):
        try:
            self.cursor.execute('''
            INSERT INTO casos (cliente_id, titulo, descripcion, estado, fecha_inicio, fecha_fin, asignado_a)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', datos)
            self.conn.commit()
            return True, "Caso legal agregado exitosamente."
        except Exception as e:
            return False, f"Error al agregar caso: {str(e)}"

    def consultar_casos(self):
        if self.auth.usuario_actual['rol'] == 'admin':
            self.cursor.execute('''
            SELECT casos.id, clientes.nombre, casos.titulo, casos.estado, 
                   casos.fecha_inicio, casos.fecha_fin, usuarios.nombre
            FROM casos
            JOIN clientes ON casos.cliente_id = clientes.id
            LEFT JOIN usuarios ON casos.asignado_a = usuarios.id
            ORDER BY casos.fecha_inicio DESC
            ''')
        else:
            self.cursor.execute('''
            SELECT casos.id, clientes.nombre, casos.titulo, casos.estado, 
                   casos.fecha_inicio, casos.fecha_fin, usuarios.nombre
            FROM casos
            JOIN clientes ON casos.cliente_id = clientes.id
            LEFT JOIN usuarios ON casos.asignado_a = usuarios.id
            WHERE casos.asignado_a = ? OR clientes.creado_por = ?
            ORDER BY casos.fecha_inicio DESC
            ''', (self.auth.usuario_actual['id'], self.auth.usuario_actual['id']))
        return self.cursor.fetchall()

    def eliminar_caso(self, caso_id):
        try:
            if self.auth.usuario_actual['rol'] != 'admin':
                # Verificar que el caso está asignado al usuario actual o el cliente fue creado por él
                self.cursor.execute('''
                SELECT casos.asignado_a, clientes.creado_por 
                FROM casos
                JOIN clientes ON casos.cliente_id = clientes.id
                WHERE casos.id = ?
                ''', (caso_id,))
                resultado = self.cursor.fetchone()
                if not resultado or (resultado[0] != self.auth.usuario_actual['id'] and
                                     resultado[1] != self.auth.usuario_actual['id']):
                    return False, "No tiene permisos para eliminar este caso"

            self.cursor.execute('DELETE FROM casos WHERE id = ?', (caso_id,))
            self.conn.commit()
            return True, "Caso eliminado correctamente." if self.cursor.rowcount > 0 else (
                False, "No se encontró el caso.")
        except Exception as e:
            return False, f"Error al eliminar caso: {str(e)}"


# Interfaz gráfica
class Aplicacion:
    def __init__(self, root, conn, cursor, auth):
        self.consulta_text = None
        self.root = root
        self.conn = conn
        self.cursor = cursor
        self.auth = auth
        self.cliente_manager = ClienteManager(conn, cursor, auth)
        self.caso_manager = CasoManager(conn, cursor, auth)

        self.configurar_interfaz()
        self.actualizar_interfaz_segun_rol()

    def configurar_interfaz(self):
        # Barra de menú
        self.crear_barra_menu()

        # Notebook (pestañas)
        notebook = tb.Notebook(self.root, bootstyle="primary")
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Pestaña de Clientes
        self.tab_clientes = tb.Frame(notebook)
        notebook.add(self.tab_clientes, text="Gestión de Clientes")
        self.crear_formulario_clientes(self.tab_clientes)

        # Pestaña de Casos
        self.tab_casos = tb.Frame(notebook)
        notebook.add(self.tab_casos, text="Gestión de Casos")
        self.crear_formulario_casos(self.tab_casos)

        # Pestaña de Consultas
        self.tab_consultas = tb.Frame(notebook)
        notebook.add(self.tab_consultas, text="Consultas")
        self.crear_pestana_consultas(self.tab_consultas)

        # Pestaña de Usuarios (solo para admin)
        self.tab_usuarios = tb.Frame(notebook)
        notebook.add(self.tab_usuarios, text="Gestión de Usuarios", state="hidden")
        self.crear_pestana_usuarios(self.tab_usuarios)

    def crear_barra_menu(self):
        menubar = tk.Menu(self.root)

        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Cerrar Sesión", command=self.cerrar_sesion)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.quit)
        menubar.add_cascade(label="Archivo", menu=file_menu)

        # Menú Ayuda
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Acerca de", command=self.mostrar_acerca_de)
        menubar.add_cascade(label="Ayuda", menu=help_menu)

        self.root.config(menu=menubar)

    def actualizar_interfaz_segun_rol(self):
        # Mostrar u ocultar pestañas según el rol
        notebook = self.root.children['!notebook']
        if self.auth.usuario_actual['rol'] == 'admin':
            notebook.tab(self.tab_usuarios, state="normal")
        else:
            notebook.tab(self.tab_usuarios, state="hidden")

        # Actualizar estado de la barra de título
        self.root.title(
            f"Despacho Legal - Sistema de Gestión (Usuario: {self.auth.usuario_actual['nombre']} - Rol: {self.auth.usuario_actual['rol']})")

    def crear_formulario_clientes(self, parent):
        frame = tb.LabelFrame(parent, text="Registrar Nuevo Cliente", bootstyle="info")
        frame.pack(fill='x', padx=10, pady=10)

        # Campos del formulario
        tb.Label(frame, text="Nombre completo:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.nombre_entry = tb.Entry(frame, width=40)
        self.nombre_entry.grid(row=0, column=1, padx=5, pady=5)

        tb.Label(frame, text="Teléfono:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.telefono_entry = tb.Entry(frame, width=40)
        self.telefono_entry.grid(row=1, column=1, padx=5, pady=5)

        tb.Label(frame, text="Email:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.email_entry = tb.Entry(frame, width=40)
        self.email_entry.grid(row=2, column=1, padx=5, pady=5)

        # Botones
        btn_frame = tb.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)

        tb.Button(btn_frame, text="Guardar Cliente",
                  command=self.agregar_cliente,
                  bootstyle="success").pack(side='left', padx=5)

        tb.Button(btn_frame, text="Limpiar Campos",
                  command=self.limpiar_campos_cliente,
                  bootstyle="warning").pack(side='left', padx=5)

        # Lista de clientes
        list_frame = tb.LabelFrame(parent, text="Clientes Registrados", bootstyle="info")
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)

        columns = ('id', 'nombre', 'telefono', 'email')
        self.clientes_tree = tb.Treeview(
            list_frame, columns=columns, show='headings', bootstyle="primary"
        )

        # Configurar columnas
        self.clientes_tree.heading('id', text='ID')
        self.clientes_tree.heading('nombre', text='Nombre')
        self.clientes_tree.heading('telefono', text='Teléfono')
        self.clientes_tree.heading('email', text='Email')

        self.clientes_tree.column('id', width=50, anchor='center')
        self.clientes_tree.column('nombre', width=200)
        self.clientes_tree.column('telefono', width=120)
        self.clientes_tree.column('email', width=200)

        # Scrollbar
        scrollbar = tb.Scrollbar(list_frame, orient='vertical', command=self.clientes_tree.yview)
        self.clientes_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.clientes_tree.pack(fill='both', expand=True)

        # Botones de gestión
        btn_manage_frame = tb.Frame(list_frame)
        btn_manage_frame.pack(pady=5)

        tb.Button(btn_manage_frame, text="Actualizar Lista",
                  command=self.actualizar_lista_clientes,
                  bootstyle="primary").pack(side='left', padx=5)

        tb.Button(btn_manage_frame, text="Eliminar Seleccionado",
                  command=self.eliminar_cliente_seleccionado,
                  bootstyle="danger").pack(side='left', padx=5)

        # Cargar datos iniciales
        self.actualizar_lista_clientes()

    def crear_formulario_casos(self, parent):
        frame = tb.LabelFrame(parent, text="Registrar Nuevo Caso Legal", bootstyle="info")
        frame.pack(fill='x', padx=10, pady=10)

        # Campos del formulario
        tb.Label(frame, text="Cliente (ID):").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.caso_cliente_entry = tb.Entry(frame, width=40)
        self.caso_cliente_entry.grid(row=0, column=1, padx=5, pady=5)

        tb.Label(frame, text="Título del caso:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.titulo_entry = tb.Entry(frame, width=40)
        self.titulo_entry.grid(row=1, column=1, padx=5, pady=5)

        tb.Label(frame, text="Descripción:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.descripcion_entry = tb.Text(frame, width=38, height=4)
        self.descripcion_entry.grid(row=2, column=1, padx=5, pady=5)

        tb.Label(frame, text="Estado:").grid(row=3, column=0, padx=5, pady=5, sticky='e')
        self.estado_combobox = tb.Combobox(frame, values=["Abierto", "Cerrado", "En Proceso"], state="readonly")
        self.estado_combobox.grid(row=3, column=1, padx=5, pady=5, sticky='w')

        tb.Label(frame, text="Fecha de Inicio (YYYY-MM-DD):").grid(row=4, column=0, padx=5, pady=5, sticky='e')
        self.fecha_inicio_entry = tb.Entry(frame, width=40)
        self.fecha_inicio_entry.grid(row=4, column=1, padx=5, pady=5)

        tb.Label(frame, text="Fecha de Fin (YYYY-MM-DD):").grid(row=5, column=0, padx=5, pady=5, sticky='e')
        self.fecha_fin_entry = tb.Entry(frame, width=40)
        self.fecha_fin_entry.grid(row=5, column=1, padx=5, pady=5)

        # Asignar a (solo para admin y abogados)
        tb.Label(frame, text="Asignar a:").grid(row=6, column=0, padx=5, pady=5, sticky='e')
        self.asignado_a_combobox = tb.Combobox(frame, state="readonly")
        self.asignado_a_combobox.grid(row=6, column=1, padx=5, pady=5, sticky='w')

        # Cargar lista de usuarios para asignación
        self.cargar_usuarios_para_asignacion()

        # Botones
        btn_frame = tb.Frame(frame)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=10)

        tb.Button(btn_frame, text="Guardar Caso",
                  command=self.agregar_caso,
                  bootstyle="success").pack(side='left', padx=5)

        tb.Button(btn_frame, text="Limpiar Campos",
                  command=self.limpiar_campos_caso,
                  bootstyle="warning").pack(side='left', padx=5)

        # Lista de casos
        list_frame = tb.LabelFrame(parent, text="Casos Registrados", bootstyle="info")
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)

        columns = ('id', 'cliente', 'titulo', 'estado', 'fecha_inicio', 'fecha_fin', 'asignado_a')
        self.casos_tree = tb.Treeview(
            list_frame, columns=columns, show='headings', bootstyle="primary"
        )

        # Configurar columnas
        self.casos_tree.heading('id', text='ID')
        self.casos_tree.heading('cliente', text='Cliente')
        self.casos_tree.heading('titulo', text='Título')
        self.casos_tree.heading('estado', text='Estado')
        self.casos_tree.heading('fecha_inicio', text='Fecha Inicio')
        self.casos_tree.heading('fecha_fin', text='Fecha Fin')
        self.casos_tree.heading('asignado_a', text='Asignado a')

        self.casos_tree.column('id', width=50, anchor='center')
        self.casos_tree.column('cliente', width=150)
        self.casos_tree.column('titulo', width=150)
        self.casos_tree.column('estado', width=80, anchor='center')
        self.casos_tree.column('fecha_inicio', width=90, anchor='center')
        self.casos_tree.column('fecha_fin', width=90, anchor='center')
        self.casos_tree.column('asignado_a', width=120)

        # Scrollbar
        scrollbar = tb.Scrollbar(list_frame, orient='vertical', command=self.casos_tree.yview)
        self.casos_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.casos_tree.pack(fill='both', expand=True)

        # Botones de gestión
        btn_manage_frame = tb.Frame(list_frame)
        btn_manage_frame.pack(pady=5)

        tb.Button(btn_manage_frame, text="Actualizar Lista",
                  command=self.actualizar_lista_casos,
                  bootstyle="primary").pack(side='left', padx=5)

        tb.Button(btn_manage_frame, text="Eliminar Seleccionado",
                  command=self.eliminar_caso_seleccionado,
                  bootstyle="danger").pack(side='left', padx=5)

        # Cargar datos iniciales
        self.actualizar_lista_casos()

    def cargar_usuarios_para_asignacion(self):
        self.cursor.execute('SELECT id, nombre FROM usuarios WHERE rol IN ("admin", "abogado")')
        usuarios = self.cursor.fetchall()

        # Formatear como "ID - Nombre" para mostrar en el combobox
        usuarios_formateados = [f"{u[0]} - {u[1]}" for u in usuarios]
        self.asignado_a_combobox['values'] = usuarios_formateados

        # Si el usuario actual es abogado, seleccionarse a sí mismo por defecto
        if self.auth.usuario_actual['rol'] in ['admin', 'abogado']:
            for i, u in enumerate(usuarios):
                if u[0] == self.auth.usuario_actual['id']:
                    self.asignado_a_combobox.current(i)
                    break

    def crear_pestana_consultas(self, parent):
        # Frame para consultas combinadas
        frame = tb.LabelFrame(parent, text="Consultas Generales", bootstyle="info")
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Botones de consulta
        btn_frame = tb.Frame(frame)
        btn_frame.pack(fill='x', pady=10)

        tb.Button(btn_frame, text="Mostrar Todos los Clientes",
                  command=self.mostrar_todos_clientes,
                  bootstyle="primary").pack(side='left', padx=5, fill='x', expand=True)

        tb.Button(btn_frame, text="Mostrar Todos los Casos",
                  command=self.mostrar_todos_casos,
                  bootstyle="primary").pack(side='left', padx=5, fill='x', expand=True)

        tb.Button(btn_frame, text="Mostrar Casos Abiertos",
                  command=self.mostrar_casos_abiertos,
                  bootstyle="success").pack(side='left', padx=5, fill='x', expand=True)

        tb.Button(btn_frame, text="Mostrar Casos Cerrados",
                  command=self.mostrar_casos_cerrados,
                  bootstyle="secondary").pack(side='left', padx=5, fill='x', expand=True)

        # Área de resultados
        self.consulta_text = tb.Text(frame, height=15, wrap='word')
        self.consulta_text.pack(fill='both', expand=True, padx=5, pady=5)

        scrollbar = tb.Scrollbar(frame, command=self.consulta_text.yview)
        self.consulta_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

    def crear_pestana_usuarios(self, parent):
        # Solo visible para admin
        frame = tb.LabelFrame(parent, text="Gestión de Usuarios", bootstyle="info")
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Campos del formulario
        form_frame = tb.Frame(frame)
        form_frame.pack(fill='x', padx=5, pady=5)

        tb.Label(form_frame, text="Nombre de usuario:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.usuario_username_entry = tb.Entry(form_frame, width=30)
        self.usuario_username_entry.grid(row=0, column=1, padx=5, pady=5)

        tb.Label(form_frame, text="Contraseña:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.usuario_password_entry = tb.Entry(form_frame, width=30, show="*")
        self.usuario_password_entry.grid(row=1, column=1, padx=5, pady=5)

        tb.Label(form_frame, text="Nombre completo:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.usuario_nombre_entry = tb.Entry(form_frame, width=30)
        self.usuario_nombre_entry.grid(row=2, column=1, padx=5, pady=5)

        tb.Label(form_frame, text="Rol:").grid(row=3, column=0, padx=5, pady=5, sticky='e')
        self.usuario_rol_combobox = tb.Combobox(form_frame, values=["admin", "abogado", "asistente"], state="readonly")
        self.usuario_rol_combobox.grid(row=3, column=1, padx=5, pady=5, sticky='w')

        # Botones
        btn_frame = tb.Frame(frame)
        btn_frame.pack(pady=5)

        tb.Button(btn_frame, text="Agregar Usuario",
                  command=self.agregar_usuario,
                  bootstyle="success").pack(side='left', padx=5)

        tb.Button(btn_frame, text="Limpiar Campos",
                  command=self.limpiar_campos_usuario,
                  bootstyle="warning").pack(side='left', padx=5)

        # Lista de usuarios
        list_frame = tb.LabelFrame(frame, text="Usuarios Registrados", bootstyle="info")
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)

        columns = ('id', 'username', 'nombre', 'rol')
        self.usuarios_tree = tb.Treeview(
            list_frame, columns=columns, show='headings', bootstyle="primary"
        )

        # Configurar columnas
        self.usuarios_tree.heading('id', text='ID')
        self.usuarios_tree.heading('username', text='Usuario')
        self.usuarios_tree.heading('nombre', text='Nombre')
        self.usuarios_tree.heading('rol', text='Rol')

        self.usuarios_tree.column('id', width=50, anchor='center')
        self.usuarios_tree.column('username', width=120)
        self.usuarios_tree.column('nombre', width=200)
        self.usuarios_tree.column('rol', width=80, anchor='center')

        # Scrollbar
        scrollbar = tb.Scrollbar(list_frame, orient='vertical', command=self.usuarios_tree.yview)
        self.usuarios_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.usuarios_tree.pack(fill='both', expand=True)

        # Botones de gestión
        btn_manage_frame = tb.Frame(list_frame)
        btn_manage_frame.pack(pady=5)

        tb.Button(btn_manage_frame, text="Actualizar Lista",
                  command=self.actualizar_lista_usuarios,
                  bootstyle="primary").pack(side='left', padx=5)

        tb.Button(btn_manage_frame, text="Eliminar Seleccionado",
                  command=self.eliminar_usuario_seleccionado,
                  bootstyle="danger").pack(side='left', padx=5)

        # Cargar datos iniciales
        self.actualizar_lista_usuarios()

    # Métodos para la gestión de clientes
    def agregar_cliente(self):
        nombre = self.nombre_entry.get().strip()
        telefono = self.telefono_entry.get().strip()
        email = self.email_entry.get().strip()

        # Validar datos
        valid, msg = self.cliente_manager.validar_datos_cliente(nombre, telefono, email)
        if not valid:
            messagebox.showwarning("Validación fallida", msg)
            return

        success, msg = self.cliente_manager.agregar_cliente((nombre, telefono, email, self.auth.usuario_actual['id']))
        if success:
            messagebox.showinfo("Éxito", msg)
            self.limpiar_campos_cliente()
            self.actualizar_lista_clientes()
        else:
            messagebox.showerror("Error", msg)

    def limpiar_campos_cliente(self):
        self.nombre_entry.delete(0, 'end')
        self.telefono_entry.delete(0, 'end')
        self.email_entry.delete(0, 'end')

    def actualizar_lista_clientes(self):
        for item in self.clientes_tree.get_children():
            self.clientes_tree.delete(item)

        clientes = self.cliente_manager.consultar_clientes()
        for cliente in clientes:
            self.clientes_tree.insert('', 'end', values=cliente)

    def eliminar_cliente_seleccionado(self):
        seleccion = self.clientes_tree.selection()
        if not seleccion:
            messagebox.showwarning("Selección requerida", "Por favor seleccione un cliente de la lista.")
            return

        item = self.clientes_tree.item(seleccion[0])
        cliente_id = item['values'][0]

        confirmar = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Está seguro que desea eliminar al cliente {item['values'][1]} (ID: {cliente_id})?"
        )

        if confirmar:
            success, msg = self.cliente_manager.eliminar_cliente(cliente_id)
            if success:
                messagebox.showinfo("Éxito", "Cliente eliminado correctamente.")
                self.actualizar_lista_clientes()
            else:
                messagebox.showerror("Error", msg)

    # Métodos para la gestión de casos
    def agregar_caso(self):
        cliente_id = self.caso_cliente_entry.get().strip()
        titulo = self.titulo_entry.get().strip()
        descripcion = self.descripcion_entry.get("1.0", 'end-1c').strip()
        estado = self.estado_combobox.get()
        fecha_inicio = self.fecha_inicio_entry.get().strip()
        fecha_fin = self.fecha_fin_entry.get().strip() or None

        # Obtener ID de usuario asignado
        asignado_a = None
        if self.asignado_a_combobox.get():
            asignado_a = int(self.asignado_a_combobox.get().split(' - ')[0])

        # Validar datos
        valid, msg = self.caso_manager.validar_datos_caso(cliente_id, titulo, estado, fecha_inicio, fecha_fin)
        if not valid:
            messagebox.showwarning("Validación fallida", msg)
            return

        datos = (int(cliente_id), titulo, descripcion, estado, fecha_inicio, fecha_fin, asignado_a)
        success, msg = self.caso_manager.agregar_caso(datos)

        if success:
            messagebox.showinfo("Éxito", msg)
            self.limpiar_campos_caso()
            self.actualizar_lista_casos()
        else:
            messagebox.showerror("Error", msg)

    def limpiar_campos_caso(self):
        self.caso_cliente_entry.delete(0, 'end')
        self.titulo_entry.delete(0, 'end')
        self.descripcion_entry.delete("1.0", 'end')
        self.estado_combobox.set('')
        self.fecha_inicio_entry.delete(0, 'end')
        self.fecha_fin_entry.delete(0, 'end')
        self.asignado_a_combobox.set('')

    def actualizar_lista_casos(self):
        for item in self.casos_tree.get_children():
            self.casos_tree.delete(item)

        casos = self.caso_manager.consultar_casos()
        for caso in casos:
            self.casos_tree.insert('', 'end', values=caso)

    def eliminar_caso_seleccionado(self):
        seleccion = self.casos_tree.selection()
        if not seleccion:
            messagebox.showwarning("Selección requerida", "Por favor seleccione un caso de la lista.")
            return

        item = self.casos_tree.item(seleccion[0])
        caso_id = item['values'][0]

        confirmar = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Está seguro que desea eliminar el caso '{item['values'][2]}' (ID: {caso_id})?"
        )

        if confirmar:
            success, msg = self.caso_manager.eliminar_caso(caso_id)
            if success:
                messagebox.showinfo("Éxito", "Caso eliminado correctamente.")
                self.actualizar_lista_casos()
            else:
                messagebox.showerror("Error", msg)

    # Métodos para la gestión de usuarios
    def agregar_usuario(self):
        if self.auth.usuario_actual['rol'] != 'admin':
            messagebox.showerror("Permiso denegado", "Solo los administradores pueden agregar usuarios.")
            return

        username = self.usuario_username_entry.get().strip()
        password = self.usuario_password_entry.get().strip()
        nombre = self.usuario_nombre_entry.get().strip()
        rol = self.usuario_rol_combobox.get()

        if not all([username, password, nombre, rol]):
            messagebox.showwarning("Campos incompletos", "Todos los campos son obligatorios.")
            return

        if len(password) < 6:
            messagebox.showwarning("Contraseña insegura", "La contraseña debe tener al menos 6 caracteres.")
            return

        try:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            self.cursor.execute('''
            INSERT INTO usuarios (username, password_hash, nombre, rol)
            VALUES (?, ?, ?, ?)
            ''', (username, password_hash, nombre, rol))
            self.conn.commit()
            messagebox.showinfo("Éxito", "Usuario agregado correctamente.")
            self.limpiar_campos_usuario()
            self.actualizar_lista_usuarios()
            self.cargar_usuarios_para_asignacion()  # Actualizar combobox en pestaña de casos
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "El nombre de usuario ya existe.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al agregar usuario: {str(e)}")

    def limpiar_campos_usuario(self):
        self.usuario_username_entry.delete(0, 'end')
        self.usuario_password_entry.delete(0, 'end')
        self.usuario_nombre_entry.delete(0, 'end')
        self.usuario_rol_combobox.set('')

    def actualizar_lista_usuarios(self):
        for item in self.usuarios_tree.get_children():
            self.usuarios_tree.delete(item)

        self.cursor.execute('SELECT id, username, nombre, rol FROM usuarios ORDER BY username')
        usuarios = self.cursor.fetchall()
        for usuario in usuarios:
            self.usuarios_tree.insert('', 'end', values=usuario)

    def eliminar_usuario_seleccionado(self):
        if self.auth.usuario_actual['rol'] != 'admin':
            messagebox.showerror("Permiso denegado", "Solo los administradores pueden eliminar usuarios.")
            return

        seleccion = self.usuarios_tree.selection()
        if not seleccion:
            messagebox.showwarning("Selección requerida", "Por favor seleccione un usuario de la lista.")
            return

        item = self.usuarios_tree.item(seleccion[0])
        usuario_id = item['values'][0]
        username = item['values'][1]

        if username == "admin":
            messagebox.showerror("Error", "No se puede eliminar al usuario admin.")
            return

        confirmar = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Está seguro que desea eliminar al usuario {username} (ID: {usuario_id})?"
        )

        if confirmar:
            try:
                self.cursor.execute('DELETE FROM usuarios WHERE id = ?', (usuario_id,))
                self.conn.commit()
                if self.cursor.rowcount > 0:
                    messagebox.showinfo("Éxito", "Usuario eliminado correctamente.")
                    self.actualizar_lista_usuarios()
                    self.cargar_usuarios_para_asignacion()  # Actualizar combobox en pestaña de casos
                else:
                    messagebox.showerror("Error", "No se encontró el usuario.")
            except Exception as e:
                messagebox.showerror("Error", f"Error al eliminar usuario: {str(e)}")

    # Métodos para consultas
    def mostrar_todos_clientes(self):
        clientes = self.cliente_manager.consultar_clientes()
        self.mostrar_resultados("LISTA COMPLETA DE CLIENTES", clientes)

    def mostrar_todos_casos(self):
        casos = self.caso_manager.consultar_casos()
        self.mostrar_resultados("LISTA COMPLETA DE CASOS", casos)

    def mostrar_casos_abiertos(self):
        if self.auth.usuario_actual['rol'] == 'admin':
            self.cursor.execute('''
            SELECT casos.id, clientes.nombre, casos.titulo, casos.estado, 
                   casos.fecha_inicio, casos.fecha_fin, usuarios.nombre
            FROM casos
            JOIN clientes ON casos.cliente_id = clientes.id
            LEFT JOIN usuarios ON casos.asignado_a = usuarios.id
            WHERE casos.estado = 'Abierto'
            ORDER BY casos.fecha_inicio DESC
            ''')
        else:
            self.cursor.execute('''
            SELECT casos.id, clientes.nombre, casos.titulo, casos.estado, 
                   casos.fecha_inicio, casos.fecha_fin, usuarios.nombre
            FROM casos
            JOIN clientes ON casos.cliente_id = clientes.id
            LEFT JOIN usuarios ON casos.asignado_a = usuarios.id
            WHERE casos.estado = 'Abierto' AND (casos.asignado_a = ? OR clientes.creado_por = ?)
            ORDER BY casos.fecha_inicio DESC
            ''', (self.auth.usuario_actual['id'], self.auth.usuario_actual['id']))

        casos = self.cursor.fetchall()
        self.mostrar_resultados("CASOS ABIERTOS", casos)

    def mostrar_casos_cerrados(self):
        if self.auth.usuario_actual['rol'] == 'admin':
            self.cursor.execute('''
            SELECT casos.id, clientes.nombre, casos.titulo, casos.estado, 
                   casos.fecha_inicio, casos.fecha_fin, usuarios.nombre
            FROM casos
            JOIN clientes ON casos.cliente_id = clientes.id
            LEFT JOIN usuarios ON casos.asignado_a = usuarios.id
            WHERE casos.estado = 'Cerrado'
            ORDER BY casos.fecha_inicio DESC
            ''')
        else:
            self.cursor.execute('''
            SELECT casos.id, clientes.nombre, casos.titulo, casos.estado, 
                   casos.fecha_inicio, casos.fecha_fin, usuarios.nombre
            FROM casos
            JOIN clientes ON casos.cliente_id = clientes.id
            LEFT JOIN usuarios ON casos.asignado_a = usuarios.id
            WHERE casos.estado = 'Cerrado' AND (casos.asignado_a = ? OR clientes.creado_por = ?)
            ORDER BY casos.fecha_inicio DESC
            ''', (self.auth.usuario_actual['id'], self.auth.usuario_actual['id']))

        casos = self.cursor.fetchall()
        self.mostrar_resultados("CASOS CERRADOS", casos)

    def mostrar_resultados(self, titulo, datos):
        self.consulta_text.delete(1.0, 'end')
        self.consulta_text.insert('end', f"{titulo}\n")
        self.consulta_text.insert('end', "=" * len(titulo) + "\n\n")

        if not datos:
            self.consulta_text.insert('end', "No se encontraron registros.\n")
            return

        for registro in datos:
            self.consulta_text.insert('end', f"{registro}\n")

    # Métodos para autenticación
    def cerrar_sesion(self):
        self.auth.cerrar_sesion()
        self.root.destroy()
        main()  # Volver a mostrar la ventana de login

    def mostrar_acerca_de(self):
        messagebox.showinfo("Acerca de",
                            "Sistema de Gestión para Despacho de Abogados\n\n"
                            "Versión 2.0\n"
                            "© 2023 Despacho Legal\n\n"
                            "Desarrollado con Python, Tkinter y SQLite")


# Función principal
def main():
    try:
        conn, cursor = inicializar_base_datos()
        auth = Autenticacion(conn, cursor)

        app = configurar_interfaz()

        # Mostrar ventana de login primero
        def on_login_success():
            # Cuando el login es exitoso, crear la aplicación principal
            Aplicacion(app, conn, cursor, auth)

        LoginWindow(app, auth, on_login_success)

        app.mainloop()
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    main()