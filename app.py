from flask import Flask, request, render_template, session, url_for, redirect
from consultas import consulta,insertar
from decoradores import login_required
from werkzeug.security import check_password_hash
from datetime import date
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('API_KEY') 
usuario=None
contraseña=''

@app.context_processor
def agregar_usuario_a_templates():
    return {'usuario': session.get('user')}

#ruta para carga pagina de inicio
@app.route('/')
def index():
  return render_template('index.html', formulario = None)

#ruta para mostrar en pantalla todos los aprendices de un curso especifico
@app.route('/ranking', methods=['GET','POST'])
def ranking():
  if request.method=='POST':
    ficha = request.form.get('ficha') 
    lista_aprendices = []
    query = "Select a.di, a.nombre, a.apellidos, a.puntos, a.puesto,a.curso_id, c.cantidad_clases FROM (Select *, RANK() OVER(order by puntos DESC) as puesto  from aprendices where curso_id = %s) as a INNER JOIN cursos as c ON a.curso_id=c.ficha"
    parametros=(ficha,)
    for aprendiz in consulta(query, parametros):
      total_clases=aprendiz['cantidad_clases']
      if total_clases !=0:
        puntos_maximos=total_clases*20
        rendimiento = (aprendiz['puntos'] / puntos_maximos) * 100
      else:
        rendimiento=0
      aprendiz['rendimiento'] = round(rendimiento, 2)
      aprendiz['iniciales']=f'{aprendiz['nombre'][0]}{aprendiz['apellidos'][0]}'      
      lista_aprendices.append(aprendiz)
    return render_template('index.html', aprendices=lista_aprendices, ficha=ficha )
  else:
    return render_template('index.html', formulario=None)

#ruta para buscar un aprendiz especifico
  
@app.route('/aprendiz', methods=['GET','POST'])  
def aprendiz():
  if request.method=='POST':
    n_aprendiz=request.form.get('buscar_aprendiz')
    query = ('Select a.di, a.nombre, a.apellidos, a.puntos, a.puesto, a.curso_id, c.cantidad_clases FROM (Select *, RANK() OVER(PARTITION BY curso_id order by puntos DESC) as puesto  from aprendices) as a INNER JOIN cursos as c ON a.curso_id = c.ficha where concat(a.nombre,a.apellidos) like %s')
    parametros=(f'%{n_aprendiz}%',)
    aprendices = consulta(query,parametros)
    lista_aprendices = []
    for aprendiz in aprendices:
      total_clases=aprendiz['cantidad_clases']
      if total_clases !=0:
        puntos_maximos=total_clases*20
        rendimiento = (aprendiz['puntos'] / puntos_maximos) * 100
      else:
        rendimiento=0
      aprendiz['rendimiento'] = round(rendimiento, 2)
      aprendiz['iniciales']=f'{aprendiz['nombre'][0]}{aprendiz['apellidos'][0]}'
      lista_aprendices.append(aprendiz)
     
    return render_template('index.html', aprendices=lista_aprendices)
  else:
    return render_template('index.html', formulario=None)


@app.route('/login')
def login():
  return render_template('login.html', error=None)


@app.route('/iniciar_sesion', methods=['GET','POST'])
def iniciar_sesion():
  if request.method=='POST':
    usuariotxt=request.form.get('usuario')
    password= request.form.get('contra')
    query = ('select username, password from admins where username=%s')
    parametros=(usuariotxt,)
    respuesta = consulta(query, parametros)
    if not respuesta:
      return render_template('login.html',error='usuario no existe')
    usuario=respuesta[0]
    contra=usuario['password']
    if check_password_hash(contra,password):
      session['user']=usuario['username']
      return redirect(url_for('panel'))
    else:
      return render_template('login.html',error='contraseña incorrecta')
  else:
    return render_template('login.html', error=None)


@app.route('/panel')
@login_required
def panel():
  query=('select ficha from cursos')
  cursos=consulta(query)
  return render_template('panel.html', cursos=cursos )



@app.route('/admin', methods=['GET','POST'])
@login_required
def admin():
  ficha = None
  if request.method=="POST":
    ficha = request.form.get('ficha')
  elif request.method=="GET":
    ficha= request.args.get('ficha')
  if ficha:    
    query = ('select di, puntos,fecha_nac, concat(nombre, " ",apellidos) as nombre_completo from aprendices where curso_id = %s order by nombre asc')
    parametros=(ficha,)
    lista_aprendices = consulta(query, parametros)
    query_clases=('select titulo, fecha from clases where curso_id = %s ORDER BY fecha desc')
    lista_clases=consulta(query_clases, parametros)
    return render_template('admin.html', aprendices= lista_aprendices, ficha=ficha, clases=lista_clases, fecha_actual=date.today() )
  return render_template('admin.html')

@app.route('/agregar_calificacion/<codigo>/<puntaje>')
@login_required
def agregar_calificacion(codigo,puntaje):
  ficha = request.args.get('ficha')
  return render_template('calificar.html', codigo=codigo, observacion=None, puntaje=puntaje, ficha=ficha )  
    
@app.route('/calificando',methods=['GET','POST'])
@login_required
def calificar():
  if request.method=="POST":
    doc=request.form.get('documento')
    ficha = request.form.get('ficha')
    acumulado=int(request.form.get('puntos'))
    cal= int(request.form.get('calificacion'))
    puntos=acumulado+cal
    query=('update aprendices set puntos = %s where di=%s')
    parametros=(puntos,doc)
    insertar(query,parametros)
    return redirect(url_for('admin',ficha=ficha))
  
#ruta para pagina de informacion especifica del aprendiz      
@app.route('/info_aprendiz/<codigo>')
def info_aprendiz(codigo):
  documento = codigo
  query = ('select tipo,descripcion,fecha,estado from observaciones where id_aprendiz = %s ORDER BY fecha DESC')
  parametros=(documento,)
  observaciones = consulta(query,parametros)
  return render_template('aprendiz.html', observaciones=observaciones, codigo=codigo )   



#ruta para agregar observacion al aprendiz
@app.route('/agregar_observacion/<codigo>')
@login_required
def agregar_observacion(codigo):
  ficha = request.args.get('ficha')
  return render_template('calificar.html', codigo=codigo, calificacion=None, ficha=ficha)   

@app.route('/guardar_observacion', methods=['GET','POST'])
@login_required
def guardar_observacion():
  if request.method=="POST":
    ficha = request.form.get('ficha') 
    doc=request.form.get('documento')
    tipo=request.form.get('tipo')
    obs=request.form.get('observacion')
    estado=request.form.get('estado')
   
    query=('insert into observaciones(id_aprendiz,tipo,descripcion,estado) values(%s,%s,%s,%s)')
    parametros=(doc,tipo,obs,estado)
    try:
      respuesta = insertar(query, parametros)
      return redirect(url_for('admin',ficha=ficha))
    except Exception as e:
      return render_template('admin.html',respuesta= f'datos no insertados \n {e}')
   
  return render_template('calificar.html')   


@app.route('/registrar_clase', methods=['GET','POST'])
@login_required
def registrar_clase():
  if request.method=="POST":
    ficha = request.form.get('ficha')
    titulo = request.form.get('titulo')
    descripcion = request.form.get('descripcion')
    fecha = request.form.get('fecha') 
    query=('insert into clases(curso_id,titulo,descripcion,fecha) values(%s,%s,%s,%s)')
    parametros=(ficha,titulo,descripcion,fecha)
    update=('UPDATE cursos SET cantidad_clases = cantidad_clases + 1 where ficha = %s')
    parametro_update=(ficha,)
    
    try:
      exito=insertar(query,parametros)
      if exito:
        insertar(update,parametro_update)
      return redirect(url_for('admin',ficha=ficha))
    except Exception as e:
      return render_template('admin.html',ficha=ficha, error= f'clases no registrada \n {e}')
  else:
    return redirect(url_for('panel'))  
   
#mostrar clases filtradas por ficha
@app.route('/temas_de_formacion/<ficha>')
def temas_formacion(ficha):
  if ficha:
   query=('select titulo, descripcion,fecha from clases where curso_id = %s ORDER BY fecha desc')
   parametros=(ficha,)
   lista_clases=consulta(query, parametros)
  return render_template('temas_formacion.html', clases= lista_clases)   

@app.route('/crear_curso')
def crear_curso():
  return render_template('registrar_curso.html', error=None , curso=None) 

@app.route('/guardando_curso', methods=['GET','POST'])
@login_required
def guardando_curso():
  if request.method=='POST':
    ficha = int(request.form.get('ficha'))
    nombre = request.form.get('nombre')
    query=('insert into cursos(ficha,nombre_curso) values(%s,%s)')
    parametros=(ficha,nombre)
    try:
      insertar(query,parametros)
      return redirect(url_for('panel'))  
    except Exception as e: 
      return render_template('registrar_curso.html', error=f'No fue posible registrar el curso, intentalo nuevamente error: {e}', curso=parametros) 
  else:
    return redirect(url_for('crear_curso', error=f'no se envio el formulario '))  
  
  
  
  
@app.route('/nueva_entrada', methods=['GET', 'POST'])
@login_required
def nueva_entrada():
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        contenido = request.form.get('contenido')  
        autor_id = session.get('user')  

        query = 'INSERT INTO blog_entradas (titulo, contenido, autor_nombre, fecha) VALUES (%s, %s, %s, NOW())'
        parametros = (titulo, contenido, autor_id)

        try:
            insertar(query, parametros)
            return redirect(url_for('panel'))  
        except Exception as e:
            return render_template('entradas.html', error=f"No se pudo guardar la entrada: {e}")
    else:
        return render_template('entradas.html')

  
  
  
@app.route('/blog')
def blog():
  query=('select titulo, contenido,autor_nombre,fecha from blog_entradas')
  blog=consulta(query,)
  return render_template('mostrar_entradas.html', blog=blog)     
  
@app.route('/añadir_aprendiz', methods=['GET', 'POST'])
@login_required
def añadir_aprendiz():
    if request.method == 'POST':
        di = int(request.form.get('di'))
        nombre = request.form.get('nombre')  
        apellidos = request.form.get('apellidos')  
        fecha= request.form.get('fecha') 
        ficha= int(request.form.get('ficha') )  
       

        query = 'INSERT INTO aprendices (di, nombre, apellidos, curso_id, fecha_nac) VALUES (%s, %s, %s, %s,%s)'
        parametros = (di, nombre, apellidos, ficha, fecha)

        try:
            insertar(query, parametros)
            return redirect(url_for('admin',ficha=ficha))
        except Exception as e:
            return render_template('añadir_aprendiz.html',ficha=ficha, error=f"No se pudo guardar el registro: {e}")
    else:
      ficha = request.args.get('ficha')
      return render_template('añadir_aprendiz.html',ficha=ficha, editar=False)  
    
    
@app.route('/editar_aprendiz/<di>', methods=['GET', 'POST'])
@login_required
def editar_aprendiz(di):
  if request.method=='GET':
    query=('select di,nombre, apellidos,curso_id,fecha_nac from aprendices where di=%s')
    parametros=(int(di),)
    aprendiz=consulta(query,parametros)
    return render_template('añadir_aprendiz.html',aprendiz=aprendiz, editar=True)
  else:
    if request.method == 'POST':
      di=int(di)
      nombre = request.form.get('nombre')  
      apellidos = request.form.get('apellidos')  
      fecha= request.form.get('fecha') 
      ficha= int(request.form.get('ficha') )  

      query = 'UPDATE aprendices SET nombre=%s, apellidos=%s, curso_id=%s, fecha_nac=%s WHERE di=%s'
      parametros = (nombre, apellidos, ficha, fecha,di)

      try:
        insertar(query, parametros)
        return redirect(url_for('admin',ficha=ficha))
      except Exception as e:
        return render_template('admin.html',ficha=ficha, error=f"No se pudo editar el registro: {e}")
  
  
    
@app.route('/cerrar_sesion')
def cerrar_sesion():
  session.pop('user',None)
  error=None
  return render_template('login.html', error=error)

