from db import db
from flask_login import UserMixin
from datetime import datetime

class Usuario(UserMixin, db.Model):
    """
    Modelo para autenticación y roles de usuario.
    UserMixin proporciona métodos necesarios para Flask-Login:
    - is_authenticated, is_active, is_anonymous, get_id()
    """
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Rol: 'admin' o 'cliente'
    rol = db.Column(db.String(20), nullable=False, default='cliente')
    
    # Información adicional
    nombre_completo = db.Column(db.String(150))
    telefono = db.Column(db.String(15))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    activo = db.Column(db.Boolean, default=True)
    
    # Relaciones
    eventos = db.relationship('Evento', backref='cliente', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Usuario {self.username} - {self.rol}>'
    
    def es_admin(self):
        """Método helper para verificar si el usuario es administrador"""
        return self.rol == 'admin'


class Servicio(db.Model):
    """
    Catálogo de servicios que ofrece Wedding Plan.
    Los administradores pueden crear, editar y eliminar servicios.
    """
    __tablename__ = 'servicios'
    
    id = db.Column('id_servicios', db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    precio_base = db.Column(db.Numeric(10, 2), nullable=False)
    categoria = db.Column(db.String(50))  # Ej: 'decoracion', 'catering', 'fotografia'
    disponible = db.Column(db.Boolean, default=True)
    imagen_url = db.Column(db.String(255))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relación muchos a muchos con eventos
    eventos = db.relationship('EventoServicio', backref='servicio', lazy=True)
    
    def __repr__(self):
        return f'<Servicio {self.nombre}>'


class Proveedor(db.Model):
    """
    Proveedores externos que colaboran con Wedding Plan.
    Pueden estar asociados a diferentes servicios.
    """
    __tablename__ = 'proveedores'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    tipo_servicio = db.Column(db.String(100))  # Ej: 'fotógrafo', 'florista'
    contacto = db.Column(db.String(100))
    telefono = db.Column(db.String(15))
    email = db.Column(db.String(120))
    calificacion = db.Column(db.Numeric(3, 2))  # De 0.00 a 5.00
    notas = db.Column(db.Text)
    activo = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<Proveedor {self.nombre}>'


class Evento(db.Model):
    """
    Evento principal que un cliente reserva.
    Contiene toda la información de la boda o celebración.
    """
    __tablename__ = 'eventos'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relación con usuario (cliente que reserva)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    # Información del evento
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    fecha_evento = db.Column(db.DateTime, nullable=False)
    lugar = db.Column(db.String(255))
    num_invitados = db.Column(db.Integer)
    presupuesto_estimado = db.Column(db.Numeric(10, 2))
    
    # Estados posibles: 'pendiente', 'confirmado', 'cancelado', 'completado'
    estado = db.Column(db.String(20), default='pendiente')
    
    # Fechas de gestión
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    servicios_contratados = db.relationship('EventoServicio', backref='evento', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Evento {self.titulo} - {self.fecha_evento}>'
    
    def calcular_total(self):
        """Calcula el costo total del evento sumando todos los servicios"""
        total = sum(es.precio_acordado for es in self.servicios_contratados)
        return total


class EventoServicio(db.Model):
    """
    Tabla intermedia para la relación muchos a muchos entre Eventos y Servicios.
    Permite que un evento tenga múltiples servicios y un servicio esté en múltiples eventos.
    """
    __tablename__ = 'evento_servicio'
    
    id = db.Column(db.Integer, primary_key=True)
    evento_id = db.Column(db.Integer, db.ForeignKey('eventos.id'), nullable=False)
    servicio_id = db.Column(db.Integer, db.ForeignKey('servicios.id_servicios'), nullable=False)
    
    # El precio puede variar del precio base según negociación
    precio_acordado = db.Column(db.Numeric(10, 2), nullable=False)
    notas = db.Column(db.Text)
    fecha_agregado = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<EventoServicio {self.evento_id}-{self.servicio_id}>'


# Modelo Cliente original (lo mantenemos por compatibilidad)
class Cliente(db.Model):
    """
    Modelo legado de Cliente. Considerar migrar datos a Usuario.
    Se mantiene temporalmente para no romper funcionalidad existente.
    """
    __tablename__ = 'clientes'
    
    id_cliente = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    telefono = db.Column(db.String(15))
    direccion = db.Column(db.String(200))

    def __repr__(self):
        return f'<Cliente {self.nombre}>'