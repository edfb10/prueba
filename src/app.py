from flask import render_template, request, redirect, url_for, session, flash
from flask import Flask, Response
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
import pyrebase
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os

from config import config

app = Flask(__name__)
firebase = pyrebase.initialize_app(config)
db = firebase.database()
auth = firebase.auth()
cred = credentials.Certificate('src/serviceAccountKey.json')
firebase_admin.initialize_app(cred)
db2 = firestore.client()
bootstrap = Bootstrap(app)
storage = firebase.storage()

app.secret_key = 'your_secret_key_here'

@app.route('/')
def raiz():
    return redirect(url_for('inicio_sesion'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error="Página no encontrada"), 404

# Manejador de errores para errores 500
@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error="Error interno del servidor"), 500

# Función inicio_sesion
@app.route("/inicio_sesion", methods=['POST', 'GET'])
def inicio_sesion():
    error_message = None  # Inicializa el mensaje de error
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            profesor_ref = db2.collection('profesor').where('user', '==', email).limit(1).get()
            if not profesor_ref:
                print("Es estudiante")
                print("Profesor no existe")
                session['user'] = user
                return redirect(url_for('index2'))
            elif len(profesor_ref) == 0:
                error_message = f"Error: el correo {email} no está registrado."
            else:
                session['profesor_id'] = profesor_ref[0].id
                session['user'] = user
                return redirect(url_for('index'))
        except Exception as e:
            error_message = " Contraseña incorrecta o Correo no registrado"
    return render_template('inicio_sesion.html', error_message=error_message)


# Función perfil
@app.route('/perfil', methods=['GET', 'POST'])
def perfil():
    if 'profesor_id' in session:
        profesor_id = session['profesor_id']
        user = session['user']
        # Obtener el correo electrónico del usuario autenticado
        email3 = user['email']
        print("user",user)
        if request.method == 'POST':
            image = request.files['image']
            # Subir la imagen a Firebase Storage
            image_blob = storage.child(f"imagenes/{profesor_id}/{image.filename}").put(image)
            # Obtener el nombre real de la imagen subida
            image_name = os.path.basename(image_blob['name'])
            print('nombre foto', image_name)
            # Obtener la URL de la imagen almacenada en Firebase Storage
            image_url = storage.child(f"imagenes/{profesor_id}/{image_name}").get_url(None)
            print("url imagen ", image_url)
            
            # Guardar la URL de la imagen en la base de datos
            db2.collection('profesor').document(profesor_id).update({'imagen_url': image_url})

            return render_template('perfil.html', image_url=image_url, email=email3)  # Pasar la URL de la imagen a la plantilla

        # Consultar la URL de la imagen y el valor de 'user' desde la base de datos
        profesor_doc = db2.collection('profesor').document(profesor_id).get()
        if profesor_doc.exists:
            imagen_url = profesor_doc.to_dict().get('imagen_url')
            
            return render_template('perfil.html', image_url=imagen_url, email=email3 )  # Pasar 'user' a la plantilla

    return render_template('perfil.html') 


@app.route('/perfil2', methods=['GET', 'POST'])
def perfil2():
    if 'estudiante_id' in session:
        estudiante_id = session['estudiante_id']
        email4 = user['email']
        # Obtener el correo electrónico del estudiante autenticado
        if request.method == 'POST':
            image = request.files['image']
            # Subir la imagen a Firebase Storage
            image_blob = storage.child(f"imagenes/{estudiante_id}/{image.filename}").put(image)
            # Obtener la URL de la imagen almacenada en Firebase Storage
            image_url = storage.child(f"imagenes/{estudiante_id}/{image.filename}").get_url(None)
            # Guardar la URL de la imagen en la base de datos
            db2.collection('estudiantes').document(estudiante_id).update({'imagen_url': image_url})
            return render_template('perfil2.html', image_url=image_url, email=email4)
        
        # Consultar la URL de la imagen desde la base de datos
        estudiante_doc = db2.collection('estudiantes').document(estudiante_id).get()
        if estudiante_doc.exists:
            imagen_url = estudiante_doc.to_dict().get('imagen_url')
            return render_template('perfil2.html', image_url=imagen_url, email=email4)

    return render_template('perfil2.html')



@app.route("/profesor_int", methods=['POST', 'GET'])
def profesor_int():
    if request.method == 'POST':
        email = 'juxnpxblojpcd315@gmail.com'
        #100juanCAS
        password = request.form['password']
        try:
            auth.sign_in_with_email_and_password(email, password)
            return redirect(url_for('registro'))
        except:
            unsuccessful = 'Verifica tus credenciales de acceso al panel Registro Docentes.'
            flash(unsuccessful, 'error')
            print("No ingreso")
            return render_template('profesor_int.html')
    return render_template('profesor_int.html')


@app.route("/registro", methods=['POST', 'GET'])
def registro():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            # Intenta crear un usuario con el correo electrónico y contraseña
            user = auth.create_user_with_email_and_password(email, password)
            # Si se crea el usuario correctamente, también guardamos los datos en Firestore
            db2.collection('profesor').add({
                'user': email,
                # Agregar más campos si es necesario
            })
            return render_template('registro.html')
        except Exception as e:
            # Si hay algún error, muestra un mensaje de error personalizado
            error_message = f"Error al registrar el correo {email} ya se encuentra registrado"
            return render_template('registro.html', error_message=error_message)
    return render_template('registro.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if (request.method == 'POST'):
            email = request.form['email']
            auth.send_password_reset_email(email)
            return render_template('inicio_sesion.html')
    return render_template('forgot_password.html')

@app.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/index2', methods=['GET', 'POST'])
def index2():
    return render_template('index2.html')

@app.route('/estudiantes', methods=['GET', 'POST'])
def estudiantes():
    estudiantes = []
    if request.method == 'POST':
        grup = request.form['nombre_g']
        email2 = request.form['email2']
        password2 = 'Ucundi07-12'
        
        grupo = {
            'nombre': grup
        }

        estudiante = {
            'user': email2
        }
        
        profesor_id = session.get('profesor_id', None)
        
        
        if profesor_id:
            # Obtener la referencia al documento del profesor
            profesor_ref = db2.collection('profesor').document(profesor_id)
            
            # Verificar si el grupo ya existe
            grupos_ref = profesor_ref.collection('grupos').where('nombre', '==', grup).get()

            # Si el grupo ya existe, obtener su referencia
            if grupos_ref:
                grupo_ref = grupos_ref[0].reference
            else:
                # El grupo no existe, agregarlo
                grupo_ref = profesor_ref.collection('grupos').add(grupo)[1]
                
            # Agregar el estudiante al grupo
            grupo_doc_ref = grupo_ref.collection('estudiantes').add(estudiante)
            # Iterar sobre los grupos
            for grupo in grupos_ref:
            # Obtener la referencia de la colección de estudiantes en este grupo
                estudiantes_ref = grupo.reference.collection('estudiantes').get()
                
                # Iterar sobre los estudiantes y agregarlos a la lista de estudiantes
                for estudiante in estudiantes_ref:
                    estudiantes.append(estudiante.to_dict())
        else:
            # Manejo de caso donde no hay ID de profesor en la sesión
            pass
    try:
        auth.create_user_with_email_and_password(email2, password2)
        if email2:
            auth.send_password_reset_email(email2)
    except Exception as e:
        return render_template('estudiantes.html', estudiantes=estudiantes)
    return render_template('estudiantes.html', estudiantes=estudiantes)



@app.route('/actividades', methods=['GET', 'POST'])
def actividades():
    # Verificar si el usuario está autenticado como profesor
    if 'profesor_id' in session:
        # Obtener el ID del profesor desde la sesión
        profesor_id = session['profesor_id']
        
        # Obtener los grupos del profesor desde Firestore
        grupos = []
        respuestas_por_grupo = {}  # Diccionario para almacenar las respuestas por grupo
        
        grupos_ref = db2.collection('profesor').document(profesor_id).collection('grupos').get()
        for grupo in grupos_ref:
            grupo_id = grupo.id
            grupos.append({
                'id': grupo_id,
                'nombre': grupo.get('nombre')
            })
            
            # Obtener todas las respuestas para este grupo
            respuestas = []
            actividades_ref = db2.collection('profesor').document(profesor_id).collection('grupos').document(grupo_id).collection('actividades').get()
            for actividad in actividades_ref:
                actividad_id = actividad.id
                respuestas_ref = db2.collection('profesor').document(profesor_id).collection('grupos').document(grupo_id).collection('actividades').document(actividad_id).collection('respuestas').get()
                for respuesta in respuestas_ref:
                    respuestas.append({
                        'nombre_estudiante': respuesta.get('nombre_estudiante'),
                        'respuesta': respuesta.get('respuesta')
                    })
            respuestas_por_grupo[grupo_id] = respuestas
        
        # Renderizar el template con los grupos y las respuestas
        return render_template('actividades.html', grupos=grupos, respuestas_por_grupo=respuestas_por_grupo)
    
    # Si el usuario no está autenticado como profesor, redirigirlo al inicio de sesión
    return redirect(url_for('inicio_sesion'))


@app.route('/crear_actividad/<grupo_id>', methods=['POST'])
def crear_actividad(grupo_id):
    # Obtener los datos del formulario
    nombre_actividad = request.form['nombre_actividad']
    plan_aprendizaje = request.form['plan_aprendizaje']
    socializacion_previa = request.form['socializacion_previa']
    integracion_tecnologica = request.form['integracion_tecnologica']
    participacion = request.form['participacion']
    trabajo_colaborativo = request.form['trabajo_colaborativo']
    logro_aprendizaje = request.form['logro_aprendizaje']
    
    # Crear una nueva colección de actividades dentro del grupo
    grupo_ref = db2.collection('profesor').document(session['profesor_id']).collection('grupos').document(grupo_id)
    actividades_ref = grupo_ref.collection('actividades')

    # Agregar los datos a la nueva colección
    nueva_actividad_ref = actividades_ref.add({
        'nombre_actividad': nombre_actividad,
        'plan_aprendizaje': plan_aprendizaje,
        'socializacion_previa': socializacion_previa,
        'integracion_tecnologica': integracion_tecnologica,
        'participacion': participacion,
        'trabajo_colaborativo': trabajo_colaborativo,
        'logro_aprendizaje': logro_aprendizaje
    })

    # Redirigir de vuelta a la página de actividades
    return redirect(url_for('actividades'))

@app.route('/agregar_respuesta/<profesor_id>/<grupo_id>/<actividad_id>', methods=['POST'])
def agregar_respuesta(profesor_id, grupo_id, actividad_id):
    if request.method == 'POST':
        nombre_estudiante = request.form['nombre_estudiante']
        respuesta_texto = request.form['respuesta']
        
        # Construye la referencia al documento de actividad
        actividad_ref = db2.collection('profesor').document(profesor_id).collection('grupos').document(grupo_id).collection('actividades').document(actividad_id)
        
        # Agrega la respuesta como un subdocumento dentro del documento de actividad
        respuesta_data = {
            'nombre_estudiante': nombre_estudiante,
            'respuesta': respuesta_texto
        }
        actividad_ref.collection('respuestas').add(respuesta_data)
        
        # Redirige de vuelta a la página de actividades
        return redirect(url_for('actividades2'))


@app.route('/actividades2')
def actividades2():
    actividades = []
    profesor_id = None  # Inicializamos profesor_id aquí

    # Consulta Firestore para obtener todas las actividades de todos los profesores
    profesores_ref = db2.collection('profesor').get()
    print("Inicio de consulta de profesores")
    for profesor in profesores_ref:
        profesor_id = profesor.id
        grupos_ref = db2.collection('profesor').document(profesor_id).collection('grupos').get()
        print(f"Actividades del profesor: {profesor_id}")
        
        for grupo in grupos_ref:
            grupo_id = grupo.id
            actividades_ref = db2.collection('profesor').document(profesor_id).collection('grupos').document(grupo_id).collection('actividades').get()
            
            if actividades_ref:
                for actividad in actividades_ref:
                    print("Toma de datos de actividad")
                    actividad_data = {
                        'profesor_id': profesor_id,
                        'grupo_id': grupo_id,
                        'id': actividad.id,
                        'nombre_actividad': actividad.get('nombre_actividad'),
                        'plan_aprendizaje': actividad.get('plan_aprendizaje'),
                        'socializacion_previa': actividad.get('socializacion_previa'),
                        'integracion_tecnologica': actividad.get('integracion_tecnologica'),
                        'participacion': actividad.get('participacion'),
                        'trabajo_colaborativo': actividad.get('trabajo_colaborativo'),
                        'logro_aprendizaje': actividad.get('logro_aprendizaje'),
                        'respuestas': []  # Inicializamos la lista de respuestas vacía
                    }
                    # Obtener todas las respuestas para esta actividad
                    respuestas_ref = actividad.reference.collection('respuestas').get()
                    
                    for respuesta in respuestas_ref:
                        actividad_data['respuestas'].append({
                            'nombre_estudiante': respuesta.get('nombre_estudiante'),
                            'respuesta': respuesta.get('respuesta')
                        })
                    actividades.append(actividad_data)
            else:
                print("No hay actividades para este grupo")
    
    # Renderiza el template con todas las actividades de todos los profesores
    return render_template('actividades2.html', actividades=actividades, profesor_id=profesor_id, grupo_id=grupo_id,)


@app.route('/respuestas', methods=['GET'])
def respuestas():
    # Verificar si el usuario está autenticado como profesor
    if 'profesor_id' in session:
        # Obtener el ID del profesor desde la sesión
        profesor_id = session['profesor_id']
        
        # Crear un diccionario para almacenar las respuestas clasificadas por actividad
        respuestas_por_actividad = {}
        
        # Obtener todos los grupos del profesor en sesión
        grupos_ref = db2.collection('profesor').document(profesor_id).collection('grupos').get()
        for grupo in grupos_ref:
            grupo_id = grupo.id
            
            # Obtener todas las actividades de este grupo
            actividades_ref = db2.collection('profesor').document(profesor_id).collection('grupos').document(grupo_id).collection('actividades').get()
            for actividad in actividades_ref:
                actividad_id = actividad.id
                nombre_actividad = actividad.get('nombre_actividad')
                
                # Obtener todas las respuestas para esta actividad
                respuestas = []
                respuestas_ref = db2.collection('profesor').document(profesor_id).collection('grupos').document(grupo_id).collection('actividades').document(actividad_id).collection('respuestas').get()
                for respuesta in respuestas_ref:
                    respuestas.append({
                        'nombre_estudiante': respuesta.get('nombre_estudiante'),
                        'respuesta': respuesta.get('respuesta')
                    })
                
                # Almacenar las respuestas clasificadas por actividad en el diccionario
                respuestas_por_actividad[actividad_id] = {
                    'nombre_actividad': nombre_actividad,
                    'respuestas': respuestas
                }
        
        # Renderizar el template con las respuestas clasificadas por actividad
        return render_template('respuestas.html', respuestas_por_actividad=respuestas_por_actividad)
    
    # Si el usuario no está autenticado como profesor, redirigirlo al inicio de sesión
    return redirect(url_for('inicio_sesion'))


@app.route('/cerrar_sesion')
def cerrar_sesion():
    # Limpiar todas las variables de sesión
    session.clear()

    # Borrar cualquier cookie relacionada con la sesión
    if 'session' in request.cookies:
        response = Response()
        response.delete_cookie('session')

    # Redirigir al usuario a la página de inicio de sesión
    return redirect(url_for('inicio_sesion'))


if __name__ == "__main__":
    app.run(debug=True, port=6050)

