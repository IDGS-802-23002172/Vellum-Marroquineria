from flask import Blueprint, render_template, session, redirect, url_for

tienda_bp = Blueprint('tiendaCliente', __name__, url_prefix='/store')

@tienda_bp.route('/')
def index():
    if 'user_role' in session and session['user_role'] != 'Cliente':
        return redirect(url_for('dashboard.index')) 
    return render_template('tiendaCliente/index.html')