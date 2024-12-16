from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_mysqldb import MySQL
from functools import wraps
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime
from flask import send_from_directory
from datetime import timedelta

import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Configuración de la base de datos
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'ferreteria'

mysql = MySQL(app)

# Decorador para proteger rutas
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:  # Si no hay un usuario en la sesión
            return redirect(url_for('login'))  # Redirige al inicio de sesión
        return f(*args, **kwargs)
    return decorated_function

# Modelo base
class Producto:
    def __init__(self, id_producto, nombre, precio, imagen):
        self.id_producto = id_producto
        self.nombre = nombre
        self.precio = precio
        self.imagen = imagen

# Controlador
class Carrito:
    def __init__(self):
        if 'carrito' not in session:
            session['carrito'] = []

    def agregar_producto(self, producto, cantidad):
        carrito = session['carrito']
        for item in carrito:
            if item['id_producto'] == producto.id_producto:
                # Si el producto ya está en el carrito, incrementamos la cantidad
                item['cantidad'] += cantidad
                session.modified = True
                return
        # Si el producto no está en el carrito, lo agregamos con la cantidad especificada
        carrito.append({
            'id_producto': producto.id_producto,
            'nombre': producto.nombre,
            'precio': float(producto.precio),
            'imagen': producto.imagen,
            'cantidad': cantidad
        })
        session.modified = True

    def eliminar_producto(self, id_producto):
        session['carrito'] = [p for p in session['carrito'] if p['id_producto'] != id_producto]
        session.modified = True

    def obtener_carrito(self):
        return session.get('carrito', [])

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_user():
    correo = request.form['correo']
    contrasena = request.form['contrasena']

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id_usuario, usuario FROM usuarios WHERE correo=%s AND contrasena=%s", (correo, contrasena))
    user = cursor.fetchone()

    if user:
        session['usuario_id'] = user[0]
        session['usuario'] = user[1]
        return redirect(url_for('productos'))
    else:
        return "Usuario o contraseña incorrectos", 401

@app.route('/registro')
def registro():
    return render_template('registro.html')

@app.route('/registro', methods=['POST'])
def registrar_usuario():
    usuario = request.form['usuario']
    correo = request.form['correo']
    contrasena = request.form['contrasena']

    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO usuarios (usuario, correo, contrasena) VALUES (%s, %s, %s)", (usuario, correo, contrasena))
    mysql.connection.commit()

    return redirect(url_for('login'))

@app.route('/productos')
@login_required
def productos():
    cursor = mysql.connection.cursor()

    # Obtener todas las categorías
    cursor.execute("SELECT id_categoria, nombre FROM categorias")
    categorias = cursor.fetchall()

    # Obtener productos agrupados por categoría
    cursor.execute("""
        SELECT p.id_producto, p.nombre, p.precio, p.imagen, c.nombre AS categoria, p.cantidad_disponible
        FROM productos p
        JOIN categorias c ON p.id_categoria = c.id_categoria
        ORDER BY c.nombre, p.nombre
    """)
    productos = cursor.fetchall()

    # Organizar productos por categoría
    productos_por_categoria = {}
    for producto in productos:
        categoria = producto[4].replace(" ", "_").lower()  # Formatear categoría para IDs
        if categoria not in productos_por_categoria:
            productos_por_categoria[categoria] = []
        productos_por_categoria[categoria].append(producto)

    # Formatear las categorías para los botones
    categorias_formateadas = [(cat[0], cat[1].replace(" ", "_").lower()) for cat in categorias]

    return render_template('productos.html', productos_por_categoria=productos_por_categoria, categorias=categorias_formateadas)

@app.route('/agregar_carrito', methods=['POST'])
@login_required
def agregar_carrito():
    data = request.json
    producto_id = data.get('producto_id')
    cantidad = int(data.get('cantidad', 1))

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id_producto, nombre, precio, imagen, cantidad_disponible FROM productos WHERE id_producto = %s", (producto_id,))
    producto = cursor.fetchone()

    if producto:
        if producto[4] >= cantidad:
            cursor.execute("UPDATE productos SET cantidad_disponible = cantidad_disponible - %s WHERE id_producto = %s", (cantidad, producto_id))
            mysql.connection.commit()

            p = Producto(producto[0], producto[1], producto[2], producto[3])
            carrito = Carrito()
            carrito.agregar_producto(p, cantidad)

            return jsonify({'success': True, 'message': 'Producto agregado al carrito'})
        else:
            return jsonify({'success': False, 'message': 'No hay suficiente inventario disponible'}), 400
    return jsonify({'success': False, 'message': 'Producto no encontrado'}), 404

@app.route('/carrito')
@login_required
def ver_carrito():
    carrito = Carrito()
    productos_en_carrito = carrito.obtener_carrito()
    total = sum([float(item['precio']) * item['cantidad'] for item in productos_en_carrito])
    return render_template('carrito.html', carrito=productos_en_carrito, total=total)

@app.route('/eliminar_carrito', methods=['GET', 'POST'])
@login_required
def eliminar_carrito():
    if request.method == 'GET':  # Si el método es GET
        id_producto = request.args.get('id_producto')  # Obtiene el ID del producto desde la URL
    else:  # Si el método es POST
        id_producto = request.form.get('id_producto')  # Obtiene el ID del producto desde el formulario

    # Validar el ID del producto
    if not id_producto:
        return jsonify({'success': False, 'message': 'ID de producto no proporcionado'}), 400

    # Convertir a entero
    id_producto = int(id_producto)

    # Actualizar inventario en la base de datos
    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE productos SET cantidad_disponible = cantidad_disponible + 1 WHERE id_producto = %s", (id_producto,))
    mysql.connection.commit()

    # Eliminar el producto del carrito
    carrito = Carrito()
    carrito.eliminar_producto(id_producto)

    return jsonify({'success': True, 'message': 'Producto eliminado del carrito'})

@app.route('/comprar', methods=['POST'])
@login_required
def comprar():
    carrito = Carrito()
    productos = carrito.obtener_carrito()

    cursor = mysql.connection.cursor()
    total = 0

    for producto in productos:
        total += float(producto['precio']) * producto['cantidad']
        cursor.execute(
            "INSERT INTO compras (id_producto, id_usuario, cantidad, nombre, precio) VALUES (%s, %s, %s, %s, %s)",
            (producto['id_producto'], session['usuario_id'], producto['cantidad'], producto['nombre'], float(producto['precio']))
        )
    mysql.connection.commit()

    ticket_path = generar_ticket(productos, total)
    session.pop('carrito', None)

    return f"Compra realizada con éxito. <a href='/{ticket_path}' target='_blank'>Descargar Ticket</a>"

def generar_ticket(productos, total):
    ticket_dir = "tickets"
    if not os.path.exists(ticket_dir):
        os.makedirs(ticket_dir)

    now = datetime.now().strftime("%Y%m%d%H%M%S")
    ticket_path = os.path.join(ticket_dir, f"ticket_{now}.pdf")

    c = canvas.Canvas(ticket_path, pagesize=letter)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 750, "FERRETERÍA ONLINE - TICKET DE COMPRA")
    c.setFont("Helvetica", 12)
    c.drawString(50, 735, f"Fecha y Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    y = 700
    for producto in productos:
        c.drawString(50, y, f"Producto: {producto['nombre']} x{producto['cantidad']}")
        c.drawString(300, y, f"Subtotal: ${float(producto['precio']) * producto['cantidad']:.2f}")
        y -= 20

    c.drawString(50, y, "------------------------------------------------------------")
    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, f"TOTAL A PAGAR: ${total:.2f}")

    c.save()
    return ticket_path

@app.route('/tickets/<filename>')
@login_required
def descargar_ticket(filename):
    return send_from_directory('tickets', filename)


#compras realizadas
@app.route('/compras_realizadas', methods=['GET'])
@login_required
def compras_realizadas():
    # Obtener el parámetro del rango (7 días o 30 días) desde la URL
    rango = request.args.get('rango', '7')  # Por defecto, se usa 7 días
    rango_dias = int(rango)

    # Calcular la fecha inicial para el filtro
    fecha_inicio = datetime.now() - timedelta(days=rango_dias)

    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT c.id_compra, p.nombre, c.cantidad, c.precio, c.fecha
        FROM compras c
        JOIN productos p ON c.id_producto = p.id_producto
        WHERE c.fecha >= %s AND c.id_usuario = %s
        ORDER BY c.fecha DESC
    """, (fecha_inicio, session['usuario_id']))

    compras = cursor.fetchall()

    return render_template('compras_realizadas.html', compras=compras, rango=rango_dias)


@app.route('/checkout', methods=['POST'])
def checkout():
    # Asumimos que recibimos una lista de productos comprados
    productos_comprados = request.form.getlist('productos')  # Lista de IDs de productos

    # Por cada producto comprado, actualizamos la cantidad disponible
    for producto_id in productos_comprados:
        cursor = mysql.connection.cursor()
        
        # Restar uno a la cantidad disponible del producto
        cursor.execute("UPDATE productos SET cantidad_disponible = cantidad_disponible - 1 WHERE id_producto = %s", (producto_id,))
        mysql.connection.commit()

        # Verificar si el producto necesita reordenarse
        cursor.execute("SELECT nombre, cantidad_disponible, punto_reorden FROM productos WHERE id_producto = %s", (producto_id,))
        producto = cursor.fetchone()
        if producto[1] < producto[2]:  # Si la cantidad disponible es menor que el punto de reorden
            # Notificar que el producto necesita reordenarse
            enviar_alerta_reorden(producto)
    
    return redirect(url_for('thank_you'))

def enviar_alerta_reorden(producto):
    # Aquí enviarías un correo o una alerta en la interfaz
    print(f"ALERTA: El producto '{producto[0]}' está por debajo del punto de reorden. Solo quedan {producto[1]} unidades.")
    
if __name__ == '__main__':
    app.run(debug=True)
