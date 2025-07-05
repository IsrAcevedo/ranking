from functools import wraps
from flask import session, redirect, url_for

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:  # Verifica si el usuario está en la sesión
            return redirect(url_for('login'))  # Redirige a la página de login si no está logeado
        return f(*args, **kwargs)  # Si está logeado, ejecuta la función
    return decorated_function

