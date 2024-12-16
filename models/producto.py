from flask_mysqldb import MySQL

# Asegúrate de que la conexión a la base de datos esté configurada correctamente en tu aplicación principal
mysql = MySQL()

class Producto:
    def __init__(self, id_producto, nombre, precio, imagen, cantidad_disponible=None):
        self.id_producto = id_producto
        self.nombre = nombre
        self.precio = precio
        self.imagen = imagen
        self.cantidad_disponible = cantidad_disponible

    @staticmethod
    def obtener_producto_por_id(producto_id):
        """Obtiene un producto específico de la base de datos por su ID."""
        cursor = mysql.connection.cursor()
        query = "SELECT id_producto, nombre, precio, imagen, cantidad_disponible FROM productos WHERE id_producto = %s"
        cursor.execute(query, (producto_id,))
        resultado = cursor.fetchone()

        if resultado:
            return Producto(*resultado)  # Crear una instancia de Producto con los datos obtenidos
        return None

    @staticmethod
    def reducir_inventario(producto_id, cantidad):
        """Reduce el inventario disponible de un producto."""
        cursor = mysql.connection.cursor()
        query = "UPDATE productos SET cantidad_disponible = cantidad_disponible - %s WHERE id_producto = %s"
        cursor.execute(query, (cantidad, producto_id))
        mysql.connection.commit()

    @staticmethod
    def restaurar_inventario(producto_id, cantidad):
        """Restaura el inventario de un producto (en caso de eliminación del carrito, por ejemplo)."""
        cursor = mysql.connection.cursor()
        query = "UPDATE productos SET cantidad_disponible = cantidad_disponible + %s WHERE id_producto = %s"
        cursor.execute(query, (cantidad, producto_id))
        mysql.connection.commit()

    @staticmethod
    def obtener_todos_los_productos():
        """Obtiene todos los productos de la base de datos."""
        cursor = mysql.connection.cursor()
        query = "SELECT id_producto, nombre, precio, imagen, cantidad_disponible FROM productos"
        cursor.execute(query)
        resultados = cursor.fetchall()

        return [Producto(*producto) for producto in resultados]

    def guardar(self):
        """Guarda un nuevo producto en la base de datos."""
        cursor = mysql.connection.cursor()
        query = "INSERT INTO productos (nombre, precio, imagen, cantidad_disponible) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (self.nombre, self.precio, self.imagen, self.cantidad_disponible))
        mysql.connection.commit()

    def actualizar(self):
        """Actualiza los datos de un producto existente en la base de datos."""
        cursor = mysql.connection.cursor()
        query = "UPDATE productos SET nombre = %s, precio = %s, imagen = %s, cantidad_disponible = %s WHERE id_producto = %s"
        cursor.execute(query, (self.nombre, self.precio, self.imagen, self.cantidad_disponible, self.id_producto))
        mysql.connection.commit()
