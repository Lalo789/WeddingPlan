from flask import Flask, render_template, jsonify, url_for, redirect, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from functools import wraps
from datetime import datetime
from email_validator import validate_email, EmailNotValidError

from db import db  
from models import Usuario, Cliente, Servicio, Proveedor, Evento, EventoServicio
from forms import LoginForm, RegistroForm, EventoForm, ServicioForm, ProveedorForm, AgregarServicioEventoForm

app = Flask(__name__)
app.config.from_object('config')
db.init_app(app)

with app.app_context():
    db.create_all()

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'  
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
login_manager.login_message_category = 'warning'


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('login'))
        if not current_user.es_admin():
            flash('No tienes permisos para acceder a esta página.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


# RUTAS PÚBLICAS
@app.route('/')
def index():
    """Página principal - Accesible para todos"""
    return render_template('index.html')


@app.route('/servicios')
def servicios():
    servicios_lista = Servicio.query.filter_by(disponible=True).all()
    return render_template('servicios.htm', servicios=servicios_lista)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.es_admin():
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('cliente_dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(username=form.username.data).first()
        
        if usuario and bcrypt.check_password_hash(usuario.password_hash, form.password.data):
            if not usuario.activo:
                flash('Tu cuenta está desactivada. Contacta al administrador.', 'danger')
                return redirect(url_for('login'))
            
            login_user(usuario, remember=form.remember.data)
            flash(f'¡Bienvenido {usuario.nombre_completo}!', 'success')
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            if usuario.es_admin():
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('cliente_dashboard'))
        else:
            flash('Usuario o contraseña incorrectos.', 'danger')
    
    return render_template('login.htm', form=form)


@app.route('/registro', methods=['GET', 'POST'])
def registro():

    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistroForm()
    
    if form.validate_on_submit():
        password_hash = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        
        nuevo_usuario = Usuario(
            username=form.username.data,
            nombre_completo=form.nombre_completo.data,
            email=form.email.data,
            telefono=form.telefono.data,
            password_hash=password_hash,
            rol='cliente'  
        )
        
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        flash('¡Cuenta creada exitosamente! Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))
    
    return render_template('registro.htm', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión exitosamente.', 'info')
    return redirect(url_for('index'))


@app.route('/cliente/dashboard')
@login_required
def cliente_dashboard():

    if current_user.es_admin():
        return redirect(url_for('admin_dashboard'))
    
    eventos = Evento.query.filter_by(usuario_id=current_user.id).order_by(Evento.fecha_evento.desc()).all()
    return render_template('cliente/dashboard.htm', eventos=eventos)


@app.route('/cliente/evento/nuevo', methods=['GET', 'POST'])
@login_required
def cliente_nuevo_evento():
    form = EventoForm()
    
    if form.validate_on_submit():
        try:
            fecha_evento = datetime.strptime(form.fecha_evento.data, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Formato de fecha inválido.', 'danger')
            return render_template('cliente/evento_form.htm', form=form)
        
        nuevo_evento = Evento(
            usuario_id=current_user.id,
            titulo=form.titulo.data,
            descripcion=form.descripcion.data,
            fecha_evento=fecha_evento,
            lugar=form.lugar.data,
            num_invitados=form.num_invitados.data,
            presupuesto_estimado=form.presupuesto_estimado.data,
            estado='pendiente' 
        )
        
        db.session.add(nuevo_evento)
        db.session.commit()
        
        flash('¡Evento creado exitosamente!', 'success')
        return redirect(url_for('cliente_ver_evento', evento_id=nuevo_evento.id))
    
    return render_template('cliente/evento_form.htm', form=form, accion='Crear')


@app.route('/cliente/evento/<int:evento_id>')
@login_required
def cliente_ver_evento(evento_id):
 
    evento = Evento.query.get_or_404(evento_id)
    
    if evento.usuario_id != current_user.id and not current_user.es_admin():
        flash('No tienes permiso para ver este evento.', 'danger')
        return redirect(url_for('cliente_dashboard'))
    
    servicios_disponibles = Servicio.query.filter_by(disponible=True).all()
    return render_template('cliente/evento_detalle.htm', evento=evento, servicios_disponibles=servicios_disponibles)


@app.route('/cliente/evento/<int:evento_id>/editar', methods=['GET', 'POST'])
@login_required
def cliente_editar_evento(evento_id):

    evento = Evento.query.get_or_404(evento_id)
    
    if evento.usuario_id != current_user.id and not current_user.es_admin():
        flash('No tienes permiso para editar este evento.', 'danger')
        return redirect(url_for('cliente_dashboard'))
    
    form = EventoForm(obj=evento)
    
    if request.method == 'GET':
        form.fecha_evento.data = evento.fecha_evento.strftime('%Y-%m-%dT%H:%M')
    
    if form.validate_on_submit():
        try:
            fecha_evento = datetime.strptime(form.fecha_evento.data, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Formato de fecha inválido.', 'danger')
            return render_template('cliente/evento_form.htm', form=form, accion='Editar')
        
        evento.titulo = form.titulo.data
        evento.descripcion = form.descripcion.data
        evento.fecha_evento = fecha_evento
        evento.lugar = form.lugar.data
        evento.num_invitados = form.num_invitados.data
        evento.presupuesto_estimado = form.presupuesto_estimado.data
        
        if current_user.es_admin():
            evento.estado = form.estado.data
        
        db.session.commit()
        flash('Evento actualizado exitosamente.', 'success')
        return redirect(url_for('cliente_ver_evento', evento_id=evento.id))
    
    return render_template('cliente/evento_form.htm', form=form, accion='Editar', evento=evento)


@app.route('/cliente/evento/<int:evento_id>/cancelar', methods=['POST'])
@login_required
def cliente_cancelar_evento(evento_id):

    evento = Evento.query.get_or_404(evento_id)
    
    if evento.usuario_id != current_user.id and not current_user.es_admin():
        flash('No tienes permiso para cancelar este evento.', 'danger')
        return redirect(url_for('cliente_dashboard'))
    
    evento.estado = 'cancelado'
    db.session.commit()
    
    flash('Evento cancelado exitosamente.', 'info')
    return redirect(url_for('cliente_dashboard'))


@app.route('/cliente/evento/<int:evento_id>/servicio/agregar', methods=['POST'])
@login_required
def cliente_agregar_servicio(evento_id):

    evento = Evento.query.get_or_404(evento_id)
    
    if evento.usuario_id != current_user.id and not current_user.es_admin():
        flash('No tienes permiso para modificar este evento.', 'danger')
        return redirect(url_for('cliente_dashboard'))
    
    servicio_id = request.form.get('servicio_id', type=int)
    precio_acordado = request.form.get('precio_acordado', type=float)
    
    if not servicio_id or not precio_acordado:
        flash('Datos incompletos.', 'danger')
        return redirect(url_for('cliente_ver_evento', evento_id=evento_id))
    
    servicio = Servicio.query.get_or_404(servicio_id)
    
    existe = EventoServicio.query.filter_by(evento_id=evento_id, servicio_id=servicio_id).first()
    if existe:
        flash('Este servicio ya está agregado al evento.', 'warning')
        return redirect(url_for('cliente_ver_evento', evento_id=evento_id))
    
    evento_servicio = EventoServicio(
        evento_id=evento_id,
        servicio_id=servicio_id,
        precio_acordado=precio_acordado
    )
    
    db.session.add(evento_servicio)
    db.session.commit()
    
    flash(f'Servicio "{servicio.nombre}" agregado exitosamente.', 'success')
    return redirect(url_for('cliente_ver_evento', evento_id=evento_id))


@app.route('/cliente/evento/<int:evento_id>/servicio/<int:servicio_id>/eliminar', methods=['POST'])
@login_required
def cliente_eliminar_servicio(evento_id, servicio_id):
    
    evento = Evento.query.get_or_404(evento_id)
    
    if evento.usuario_id != current_user.id and not current_user.es_admin():
        flash('No tienes permiso para modificar este evento.', 'danger')
        return redirect(url_for('cliente_dashboard'))
    
    evento_servicio = EventoServicio.query.filter_by(evento_id=evento_id, servicio_id=servicio_id).first_or_404()
    
    db.session.delete(evento_servicio)
    db.session.commit()
    
    flash('Servicio eliminado del evento.', 'info')
    return redirect(url_for('cliente_ver_evento', evento_id=evento_id))



@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():

    total_usuarios = Usuario.query.count()
    total_eventos = Evento.query.count()
    total_servicios = Servicio.query.count()
    eventos_pendientes = Evento.query.filter_by(estado='pendiente').count()
    
    eventos_recientes = Evento.query.order_by(Evento.fecha_creacion.desc()).limit(5).all()
    
    return render_template('admin/dashboard.htm', 
                         total_usuarios=total_usuarios,
                         total_eventos=total_eventos,
                         total_servicios=total_servicios,
                         eventos_pendientes=eventos_pendientes,
                         eventos_recientes=eventos_recientes)


@app.route('/admin/servicios')
@admin_required
def admin_servicios():
    servicios_lista = Servicio.query.all()
    return render_template('admin/servicios.htm', servicios=servicios_lista)


@app.route('/admin/servicio/nuevo', methods=['GET', 'POST'])
@admin_required
def admin_nuevo_servicio():
    form = ServicioForm()
    
    if form.validate_on_submit():
        nuevo_servicio = Servicio(
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            precio_base=form.precio_base.data,
            categoria=form.categoria.data,
            imagen_url=form.imagen_url.data,
            disponible=form.disponible.data
        )
        
        db.session.add(nuevo_servicio)
        db.session.commit()
        
        flash(f'Servicio "{nuevo_servicio.nombre}" creado exitosamente.', 'success')
        return redirect(url_for('admin_servicios'))
    
    return render_template('admin/servicio_form.htm', form=form, accion='Crear')


@app.route('/admin/servicio/<int:servicio_id>/editar', methods=['GET', 'POST'])
@admin_required
def admin_editar_servicio(servicio_id):
    servicio = Servicio.query.get_or_404(servicio_id)
    form = ServicioForm(obj=servicio)
    
    if form.validate_on_submit():
        servicio.nombre = form.nombre.data
        servicio.descripcion = form.descripcion.data
        servicio.precio_base = form.precio_base.data
        servicio.categoria = form.categoria.data
        servicio.imagen_url = form.imagen_url.data
        servicio.disponible = form.disponible.data
        
        db.session.commit()
        flash(f'Servicio "{servicio.nombre}" actualizado exitosamente.', 'success')
        return redirect(url_for('admin_servicios'))
    
    return render_template('admin/servicio_form.htm', form=form, accion='Editar', servicio=servicio)


@app.route('/admin/servicio/<int:servicio_id>/eliminar', methods=['POST'])
@admin_required
def admin_eliminar_servicio(servicio_id):
    servicio = Servicio.query.get_or_404(servicio_id)
    
    en_uso = EventoServicio.query.filter_by(servicio_id=servicio_id).count()
    if en_uso > 0:
        flash(f'No se puede eliminar el servicio "{servicio.nombre}" porque está en uso en {en_uso} evento(s).', 'danger')
        return redirect(url_for('admin_servicios'))
    
    db.session.delete(servicio)
    db.session.commit()
    
    flash(f'Servicio "{servicio.nombre}" eliminado exitosamente.', 'success')
    return redirect(url_for('admin_servicios'))



@app.route('/admin/eventos')
@admin_required
def admin_eventos():
    eventos = Evento.query.order_by(Evento.fecha_evento.desc()).all()
    return render_template('admin/eventos.htm', eventos=eventos)


@app.route('/admin/evento/<int:evento_id>')
@admin_required
def admin_ver_evento(evento_id):
    evento = Evento.query.get_or_404(evento_id)
    return render_template('admin/evento_detalle.htm', evento=evento)


@app.route('/admin/usuarios')
@admin_required
def admin_usuarios():
    usuarios = Usuario.query.all()
    return render_template('admin/usuarios.htm', usuarios=usuarios)


@app.route('/admin/usuario/<int:usuario_id>/toggle-activo', methods=['POST'])
@admin_required
def admin_toggle_usuario_activo(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    
    if usuario.id == current_user.id:
        flash('No puedes desactivar tu propia cuenta.', 'danger')
        return redirect(url_for('admin_usuarios'))
    
    usuario.activo = not usuario.activo
    db.session.commit()
    
    estado = 'activado' if usuario.activo else 'desactivado'
    flash(f'Usuario "{usuario.username}" {estado} exitosamente.', 'success')
    return redirect(url_for('admin_usuarios'))



@app.route('/admin/proveedores')
@admin_required
def admin_proveedores():
    proveedores = Proveedor.query.all()
    return render_template('admin/proveedores.htm', proveedores=proveedores)


@app.route('/admin/proveedor/nuevo', methods=['GET', 'POST'])
@admin_required
def admin_nuevo_proveedor():
    form = ProveedorForm()
    
    if form.validate_on_submit():
        nuevo_proveedor = Proveedor(
            nombre=form.nombre.data,
            tipo_servicio=form.tipo_servicio.data,
            contacto=form.contacto.data,
            telefono=form.telefono.data,
            email=form.email.data,
            calificacion=form.calificacion.data,
            notas=form.notas.data,
            activo=form.activo.data
        )
        
        db.session.add(nuevo_proveedor)
        db.session.commit()
        
        flash(f'Proveedor "{nuevo_proveedor.nombre}" creado exitosamente.', 'success')
        return redirect(url_for('admin_proveedores'))
    
    return render_template('admin/proveedor_form.htm', form=form, accion='Crear')


@app.route('/admin/proveedor/<int:proveedor_id>/editar', methods=['GET', 'POST'])
@admin_required
def admin_editar_proveedor(proveedor_id):
    """Editar un proveedor existente"""
    proveedor = Proveedor.query.get_or_404(proveedor_id)
    form = ProveedorForm(obj=proveedor)
    
    if form.validate_on_submit():
        proveedor.nombre = form.nombre.data
        proveedor.tipo_servicio = form.tipo_servicio.data
        proveedor.contacto = form.contacto.data
        proveedor.telefono = form.telefono.data
        proveedor.email = form.email.data
        proveedor.calificacion = form.calificacion.data
        proveedor.notas = form.notas.data
        proveedor.activo = form.activo.data
        
        db.session.commit()
        flash(f'Proveedor "{proveedor.nombre}" actualizado exitosamente.', 'success')
        return redirect(url_for('admin_proveedores'))
    
    return render_template('admin/proveedor_form.htm', form=form, accion='Editar', proveedor=proveedor)


@app.route('/admin/proveedor/<int:proveedor_id>/eliminar', methods=['POST'])
@admin_required
def admin_eliminar_proveedor(proveedor_id):
    proveedor = Proveedor.query.get_or_404(proveedor_id)
    
    db.session.delete(proveedor)
    db.session.commit()
    
    flash(f'Proveedor "{proveedor.nombre}" eliminado exitosamente.', 'success')
    return redirect(url_for('admin_proveedores'))



@app.route('/test-db')
def test_db():
    try:
        db.session.execute(db.text('SELECT 1'))
        return jsonify({'status': 'success', 'message': 'Conexión a la base de datos exitosa.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error en la conexión: {e}'})


@app.route('/cliente')
def mostrar_cliente():
    clientes = Cliente.query.all()
    return render_template('clientes.htm', clientes=clientes)


@app.route('/cliente/nuevo', methods=['GET', 'POST'])
def nuevo_cliente():
    return redirect(url_for('registro'))


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.htm', error=str(e)), 404


@app.errorhandler(403)
def forbidden(e):
    return render_template('403.htm', error=str(e)), 403


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.htm', error=str(e)), 500


@app.template_filter('currency')
def currency_filter(value):
    if value is None:
        return "$0.00"
    return f"${value:,.2f}"


@app.template_filter('datetime_format')
def datetime_format_filter(value, format='%d/%m/%Y %H:%M'):
    if value is None:
        return ""
    return value.strftime(format)


@app.context_processor
def utility_processor():
    return dict(
        now=datetime.utcnow,
        enumerate=enumerate
    )


@app.route('/api/verificar-username', methods=["POST"])
def verificar_username():
    "Endpoint AJAX para verificar si user esta disponible. Retorna JSON"
    
    data = request.get_json()
    username = data.get('username', '').strip()
    
    if not username:
        return jsonify({'disponible': False, 'mensaje': 'El username puede estar vacío.'})
    
    if len(username) < 3:
        return jsonify({'disponible': False, 'mensaje': 'Minimo 3 caracteres'})
    
    #Buscar en DB
    usuario_existente = Usuario.query.filter_by(username=username).first()
    
    if usuario_existente:
        return jsonify({'disponible': False, 'mensaje': 'El username ya esta en uso'})
    else:
        return jsonify({'disponible': True, 'mensaje': 'Username disponible'})
    
@app.route('/api/buscar-servicios', methods=["GET"])
def buscar_servicios():
    "Endpoint AJAX para buscar servicios en tiempo real"
    query = request.args.get('q', '').strip().lower()
    
    if len(query) < 2:
        return jsonify({'servicios':[]})
    
    #Buscar servicios con el query
    servicios = Servicio.query.filter(
        Servicio.nombre.ilike(f'%{query}%'),
        Servicio.disponible == True
    ).limit(10).all()
    
    #Convertir a JSON
    resultados = [
        {
            'id': s.id,
            'nombre': s.nombre,
            'descripcion': s.descripcion,
            'precio_base': s.precio_base,
            'categoria': s.categoria,
            'imagen_url': s.imagen_url
        }
        for s in servicios
    ]
    
    return jsonify({'servicios': resultados})

@app.route('/api/verificar-email', methods=["POST"])
def verificar_email():
    "Endpoint AJAX para verificar si email esta disponible"
    
    data = request.get_json()
    email = data.get('email', '').strip()
    
    if not email:
        return jsonify({'disponible': False, 'mensaje': 'El email no puede estar vacío.'})
    
   #Validacion robusta de emial
    try:
        validate_email(email, check_deliverability=False)
    except EmailNotValidError as e:
        return jsonify({'disponible': False, 'mensaje': str(e)})
    
    usuario_existente = Usuario.query.filter_by(email=email).first()
    
    if usuario_existente:
        return jsonify({'disponible': False, 'mensaje': 'El email ya está en uso.'})
    else:
        return jsonify({'disponible': True, 'mensaje': 'Email disponible.'})
    
if __name__ == '__main__':
    import os
    
    # Variable para activar HTTPS local
    usar_https_local = os.environ.get('HTTPS_LOCAL', 'False') == 'True'
    
    if usar_https_local:
        print("Ejecutando con HTTPS")
        print(" Tu navegador mostrará advertencia de seguridad")
        print(" Accede a: https://localhost:5000")
        app.run(
            debug=True,
            ssl_context='adhoc' 
        )
    else:
        print(" Ejecutando en HTTP")
        print("Accede a: http://localhost:5000")
        app.run(debug=True)
    