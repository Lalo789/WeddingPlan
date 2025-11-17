from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, DecimalField, IntegerField, SelectField, DateTimeField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, NumberRange, Optional
from models import Usuario
from datetime import datetime

class LoginForm(FlaskForm):
    """
    Formulario de inicio de sesión.
    Valida que el usuario ingrese credenciales y opcionalmente marque "recordarme".
    """
    username = StringField('Usuario', 
        validators=[
            DataRequired(message='El nombre de usuario es obligatorio'),
            Length(min=3, max=80, message='El usuario debe tener entre 3 y 80 caracteres')
        ],
        render_kw={"placeholder": "Ingresa tu usuario"}
    )
    
    password = PasswordField('Contraseña', 
        validators=[
            DataRequired(message='La contraseña es obligatoria')
        ],
        render_kw={"placeholder": "Ingresa tu contraseña"}
    )
    
    remember = BooleanField('Recordarme')


class RegistroForm(FlaskForm):
    """
    Formulario de registro para nuevos usuarios.
    Valida unicidad de username y email, y confirma la contraseña.
    """
    username = StringField('Nombre de Usuario', 
        validators=[
            DataRequired(message='El nombre de usuario es obligatorio'),
            Length(min=3, max=80, message='El usuario debe tener entre 3 y 80 caracteres')
        ],
        render_kw={"placeholder": "Elige un nombre de usuario"}
    )
    
    nombre_completo = StringField('Nombre Completo', 
        validators=[
            DataRequired(message='El nombre completo es obligatorio'),
            Length(min=3, max=150, message='El nombre debe tener entre 3 y 150 caracteres')
        ],
        render_kw={"placeholder": "Tu nombre completo"}
    )
    
    email = StringField('Correo Electrónico', 
        validators=[
            DataRequired(message='El correo electrónico es obligatorio'),
            Email(message='Ingresa un correo electrónico válido')
        ],
        render_kw={"placeholder": "tu@email.com"}
    )
    
    telefono = StringField('Teléfono', 
        validators=[
            Optional(),
            Length(min=10, max=15, message='El teléfono debe tener entre 10 y 15 caracteres')
        ],
        render_kw={"placeholder": "10 dígitos"}
    )
    
    password = PasswordField('Contraseña', 
        validators=[
            DataRequired(message='La contraseña es obligatoria'),
            Length(min=6, message='La contraseña debe tener al menos 6 caracteres')
        ],
        render_kw={"placeholder": "Mínimo 6 caracteres"}
    )
    
    confirmar_password = PasswordField('Confirmar Contraseña', 
        validators=[
            DataRequired(message='Debes confirmar tu contraseña'),
            EqualTo('password', message='Las contraseñas deben coincidir')
        ],
        render_kw={"placeholder": "Repite tu contraseña"}
    )
    
    def validate_username(self, username):
        """
        Validación personalizada para verificar que el username no esté en uso.
        Se ejecuta automáticamente cuando el formulario se valida.
        """
        usuario = Usuario.query.filter_by(username=username.data).first()
        if usuario:
            raise ValidationError('Este nombre de usuario ya está en uso. Por favor elige otro.')
    
    def validate_email(self, email):
        """
        Validación personalizada para verificar que el email no esté registrado.
        """
        usuario = Usuario.query.filter_by(email=email.data).first()
        if usuario:
            raise ValidationError('Este correo electrónico ya está registrado. ¿Ya tienes cuenta?')


class EventoForm(FlaskForm):
    """
    Formulario para crear y editar eventos.
    Los clientes lo usan para reservar sus celebraciones.
    """
    titulo = StringField('Título del Evento', 
        validators=[
            DataRequired(message='El título es obligatorio'),
            Length(min=5, max=200, message='El título debe tener entre 5 y 200 caracteres')
        ],
        render_kw={"placeholder": "Ej: Boda de Ana y Carlos"}
    )
    
    descripcion = TextAreaField('Descripción', 
        validators=[
            Optional(),
            Length(max=1000, message='La descripción no puede exceder 1000 caracteres')
        ],
        render_kw={
            "placeholder": "Describe tu evento: temática, colores, estilo...",
            "rows": 4
        }
    )
    
    fecha_evento = StringField('Fecha del Evento', 
        validators=[
            DataRequired(message='La fecha del evento es obligatoria')
        ],
        render_kw={
            "type": "datetime-local",
            "placeholder": "dd/mm/aaaa hh:mm"
        }
    )
    
    lugar = StringField('Lugar', 
        validators=[
            DataRequired(message='El lugar es obligatorio'),
            Length(min=5, max=255, message='El lugar debe tener entre 5 y 255 caracteres')
        ],
        render_kw={"placeholder": "Dirección o nombre del lugar"}
    )
    
    num_invitados = IntegerField('Número de Invitados', 
        validators=[
            Optional(),
            NumberRange(min=1, max=10000, message='Ingresa un número válido de invitados')
        ],
        render_kw={"placeholder": "Cantidad estimada"}
    )
    
    presupuesto_estimado = DecimalField('Presupuesto Estimado', 
        validators=[
            Optional(),
            NumberRange(min=0, message='El presupuesto debe ser un valor positivo')
        ],
        render_kw={
            "placeholder": "Presupuesto en pesos",
            "step": "0.01"
        }
    )
    
    estado = SelectField('Estado', 
        choices=[
            ('pendiente', 'Pendiente'),
            ('confirmado', 'Confirmado'),
            ('cancelado', 'Cancelado'),
            ('completado', 'Completado')
        ],
        validators=[DataRequired()]
    )


class ServicioForm(FlaskForm):
    """
    Formulario para que los administradores gestionen el catálogo de servicios.
    """
    nombre = StringField('Nombre del Servicio', 
        validators=[
            DataRequired(message='El nombre del servicio es obligatorio'),
            Length(min=3, max=100, message='El nombre debe tener entre 3 y 100 caracteres')
        ],
        render_kw={"placeholder": "Ej: Decoración Floral"}
    )
    
    descripcion = TextAreaField('Descripción', 
        validators=[
            Optional(),
            Length(max=1000, message='La descripción no puede exceder 1000 caracteres')
        ],
        render_kw={
            "placeholder": "Describe el servicio en detalle",
            "rows": 4
        }
    )
    
    precio_base = DecimalField('Precio Base', 
        validators=[
            DataRequired(message='El precio base es obligatorio'),
            NumberRange(min=0.01, message='El precio debe ser mayor a cero')
        ],
        render_kw={
            "placeholder": "Precio en pesos",
            "step": "0.01"
        }
    )
    
    categoria = SelectField('Categoría', 
        choices=[
            ('decoracion', 'Decoración'),
            ('catering', 'Catering'),
            ('fotografia', 'Fotografía'),
            ('entretenimiento', 'Entretenimiento'),
            ('coordinacion', 'Coordinación'),
            ('reposteria', 'Repostería'),
            ('otro', 'Otro')
        ],
        validators=[DataRequired(message='Selecciona una categoría')]
    )
    
    imagen_url = StringField('URL de Imagen', 
        validators=[
            Optional(),
            Length(max=255, message='La URL no puede exceder 255 caracteres')
        ],
        render_kw={"placeholder": "https://ejemplo.com/imagen.jpg"}
    )
    
    disponible = BooleanField('Disponible')


class ProveedorForm(FlaskForm):
    """
    Formulario para gestionar proveedores externos.
    Solo accesible para administradores.
    """
    nombre = StringField('Nombre del Proveedor', 
        validators=[
            DataRequired(message='El nombre del proveedor es obligatorio'),
            Length(min=3, max=150, message='El nombre debe tener entre 3 y 150 caracteres')
        ],
        render_kw={"placeholder": "Nombre de la empresa o persona"}
    )
    
    tipo_servicio = StringField('Tipo de Servicio', 
        validators=[
            Optional(),
            Length(max=100, message='El tipo de servicio no puede exceder 100 caracteres')
        ],
        render_kw={"placeholder": "Ej: Fotógrafo, Florista, DJ"}
    )
    
    contacto = StringField('Nombre de Contacto', 
        validators=[
            Optional(),
            Length(max=100, message='El nombre de contacto no puede exceder 100 caracteres')
        ],
        render_kw={"placeholder": "Persona de contacto"}
    )
    
    telefono = StringField('Teléfono', 
        validators=[
            Optional(),
            Length(min=10, max=15, message='El teléfono debe tener entre 10 y 15 caracteres')
        ],
        render_kw={"placeholder": "10 dígitos"}
    )
    
    email = StringField('Correo Electrónico', 
        validators=[
            Optional(),
            Email(message='Ingresa un correo electrónico válido')
        ],
        render_kw={"placeholder": "email@proveedor.com"}
    )
    
    calificacion = DecimalField('Calificación', 
        validators=[
            Optional(),
            NumberRange(min=0, max=5, message='La calificación debe estar entre 0 y 5')
        ],
        render_kw={
            "placeholder": "De 0.00 a 5.00",
            "step": "0.01"
        }
    )
    
    notas = TextAreaField('Notas', 
        validators=[
            Optional()
        ],
        render_kw={
            "placeholder": "Información adicional sobre el proveedor",
            "rows": 3
        }
    )
    
    activo = BooleanField('Activo')


class AgregarServicioEventoForm(FlaskForm):
    """
    Formulario para agregar servicios a un evento específico.
    Permite personalizar el precio para cada evento.
    """
    servicio_id = SelectField('Servicio', 
        coerce=int,
        validators=[DataRequired(message='Debes seleccionar un servicio')]
    )
    
    precio_acordado = DecimalField('Precio Acordado', 
        validators=[
            DataRequired(message='El precio acordado es obligatorio'),
            NumberRange(min=0.01, message='El precio debe ser mayor a cero')
        ],
        render_kw={
            "placeholder": "Precio para este evento",
            "step": "0.01"
        }
    )
    
    notas = TextAreaField('Notas', 
        validators=[Optional()],
        render_kw={
            "placeholder": "Detalles específicos de este servicio para el evento",
            "rows": 2
        }
    )