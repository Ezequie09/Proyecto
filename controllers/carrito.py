from flask import session
from flask import Blueprint, request, jsonify
from models.producto import Producto

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
            'precio': float(producto.precio),  # Convertimos el precio a número
            'imagen': producto.imagen,
            'cantidad': cantidad
        })
        session.modified = True

    def eliminar_producto(self, id_producto):
        carrito = session['carrito']
        for item in carrito:
            if item['id_producto'] == id_producto:
                carrito.remove(item)
                session.modified = True
                return

    def obtener_carrito(self):
        return session.get('carrito', [])

carrito_bp = Blueprint('carrito', __name__)

@carrito_bp.route('/agregar_carrito', methods=['POST'])
def agregar_carrito():
    data = request.json
    producto_id = data['producto_id']
    cantidad = int(data['cantidad'])

    # Obtener el producto desde la base de datos
    producto = Producto.obtener_producto_por_id(producto_id)

    if producto and producto['cantidad_disponible'] >= cantidad:
        # Reducir inventario en la base de datos
        Producto.reducir_inventario(producto_id, cantidad)

        # Agregar el producto al carrito
        p = Producto(producto['id_producto'], producto['nombre'], producto['precio'], producto['imagen'])
        carrito = Carrito()
        carrito.agregar_producto(p, cantidad)

        # Responder con éxito y la nueva cantidad disponible
        nueva_cantidad = producto['cantidad_disponible'] - cantidad
        return jsonify({'success': True, 'nueva_cantidad': nueva_cantidad})
    
    # Responder con error si no hay suficiente inventario
    return jsonify({'success': False, 'message': 'Inventario insuficiente'})

@carrito_bp.route('/eliminar_carrito', methods=['POST'])
def eliminar_carrito():
    data = request.json
    producto_id = data['producto_id']
    
    # Eliminar el producto del carrito
    carrito = Carrito()
    carrito.eliminar_producto(producto_id)

    return jsonify({'success': True, 'message': 'Producto eliminado del carrito'})
