from models.usuario import Usuario

@auth_bp.route('/login', methods=['POST'])
def login():
    correo = request.form['correo']
    contrasena = request.form['contrasena']

    cursor = mysql.connection.cursor()
    usuario = Usuario.validar_usuario(cursor, correo)

    if usuario and check_password_hash(usuario[2], contrasena):
        session['usuario_id'] = usuario[0]
        session['usuario'] = usuario[1]
        return redirect(url_for('productos'))
    else:
        return "Usuario o contraseña incorrectos", 401
