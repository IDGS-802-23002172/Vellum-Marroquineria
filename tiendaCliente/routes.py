from flask import Blueprint, render_template, session, redirect, url_for
from models import Venta, db

tienda_bp = Blueprint('tiendaCliente', __name__, url_prefix='/store')

@tienda_bp.route('/')
def index():
    if 'user_role' in session and session['user_role'] != 'Cliente':
        return redirect(url_for('dashboard.index')) 
    return render_template('tiendaCliente/index.html')

@tienda_bp.route('/mis-pedidos')
def mis_pedidos():
    # Validamos que sea un cliente logueado
    usuario_id = session.get('user_id')
    if not usuario_id or session.get('user_role') != 'Cliente':
        return redirect(url_for('login'))
    
    # Consultamos las ventas ligadas a su ID de usuario
    pedidos = Venta.query.filter_by(usuario_id=usuario_id).order_by(Venta.fecha.desc()).all()
    
    return render_template('tiendaCliente/seguimiento.html', pedidos=pedidos)