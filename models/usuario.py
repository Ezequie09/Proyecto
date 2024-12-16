from werkzeug.security import generate_password_hash, check_password_hash


class Usuario:
    def __init__(self, id_usuario, nombre, correo):
        """
        Constructor de la clase Usuario.
        """
        self.id_usuario = id_usuario
        self.nombre = nombre
        self.correo = correo

    @staticmethod
    def obtener_usuario_por_id(cursor, usuario_id):
        """
        Obtiene un usuario por su ID desde la base de datos.

        :param cursor: Cursor de la base de datos.
        :param usuario_id: ID del usuario que se desea obtener.
        :return: Instancia de Usuario o None si no se encuentra.
        """
        query = "SELECT id_usuario, usuario, correo FROM usuarios WHERE id_usuario = %s"
        cursor.execute(query, (usuario_id,))
        resultado = cursor.fetchone()
        if resultado:
            return Usuario(*resultado)
        return None

    @staticmethod
    def obtener_usuario_por_correo(cursor, correo):
        """
        Obtiene un usuario por su correo desde la base de datos.

        :param cursor: Cursor de la base de datos.
        :param correo: Correo del usuario que se desea obtener.
        :return: Instancia de Usuario o None si no se encuentra.
        """
        query = "SELECT id_usuario, usuario, correo FROM usuarios WHERE correo = %s"
        cursor.execute(query, (correo,))
        resultado = cursor.fetchone()
        if resultado:
            return Usuario(*resultado)
        return None

    @staticmethod
    def registrar_usuario(cursor, conexion, nombre, correo, contrasena):
        """
        Registra un nuevo usuario en la base de datos.

        :param cursor: Cursor de la base de datos.
        :param conexion: Conexión a la base de datos.
        :param nombre: Nombre del usuario.
        :param correo: Correo del usuario.
        :param contrasena: Contraseña encriptada del usuario.
        """
        hashed_password = generate_password_hash(contrasena)
        query = "INSERT INTO usuarios (usuario, correo, contrasena) VALUES (%s, %s, %s)"
        cursor.execute(query, (nombre, correo, hashed_password))
        conexion.commit()

    @staticmethod
    def validar_usuario(cursor, correo, contrasena):
        """
        Valida las credenciales del usuario comparando el correo y la contraseña.

        :param cursor: Cursor de la base de datos.
        :param correo: Correo del usuario.
        :param contrasena: Contraseña proporcionada por el usuario.
        :return: True si las credenciales son correctas, False en caso contrario.
        """
        query = "SELECT contrasena FROM usuarios WHERE correo = %s"
        cursor.execute(query, (correo,))
        resultado = cursor.fetchone()
        if resultado and check_password_hash(resultado[0], contrasena):
            return True
        return False
