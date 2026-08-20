from flask import Flask, request, render_template, session, url_for, redirect
from consultas import consulta,insertar
from decoradores import login_required
from werkzeug.security import check_password_hash
from datetime import date
import os
import mysql.connector
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
  # Top aprendiz por ficha para el carrusel de la landing
  query_top = """
    SELECT a.di, a.nombre, a.apellidos, a.puntos, a.puesto, a.curso_id, c.cantidad_clases
    FROM (
      SELECT *, RANK() OVER(PARTITION BY curso_id ORDER BY puntos DESC) as puesto
      FROM aprendices
    ) as a
    INNER JOIN cursos as c ON a.curso_id = c.ficha
    WHERE a.puesto = 1
  """
  top_aprendices = []
  for ap in consulta(query_top):
    total_clases = ap['cantidad_clases']
    if total_clases != 0:
      puntos_maximos = total_clases * 20
      rendimiento = (ap['puntos'] / puntos_maximos) * 100
    else:
      rendimiento = 0
    ap['rendimiento'] = round(rendimiento, 2)
    ap['iniciales'] = f"{ap['nombre'][0]}{ap['apellidos'][0]}"
    top_aprendices.append(ap)
    
  # Programas de formación y conteo de aprendices
  query_programas = """
    SELECT c.ficha, c.nombre_curso, COUNT(a.di) as total_aprendices
    FROM cursos as c
    LEFT JOIN aprendices as a ON c.ficha = a.curso_id
    GROUP BY c.ficha, c.nombre_curso
  """
  programas = consulta(query_programas)
  
  return render_template('index.html', formulario=None, top_aprendices=top_aprendices, programas=programas)

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
    query = ('select username, password,id from admins where username=%s')
    parametros=(usuariotxt,)
    respuesta = consulta(query, parametros)
    if not respuesta:
      return render_template('login.html',error='usuario no existe')
    usuario=respuesta[0]
    contra=usuario['password']
    if check_password_hash(contra,password):
      session['user']=usuario['username']
      session['id_user']=usuario['id']
      return redirect(url_for('panel'))
    else:
      return render_template('login.html',error='contraseña incorrecta')
  else:
    return render_template('login.html', error=None)


@app.route('/panel')
@login_required
def panel():
  query=('select ficha from cursos where admin_id = %s')
  parametros=(session['id_user'],)
  cursos=consulta(query,parametros)
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
    query_clases=('select id_clase, titulo, descripcion, fecha from clases where curso_id = %s ORDER BY fecha desc')
    lista_clases=consulta(query_clases, parametros)
    return render_template('admin.html', aprendices= lista_aprendices, ficha=ficha, clases=lista_clases, fecha_actual=date.today() )
  return render_template('admin.html')

@app.route('/agregar_calificacion/<codigo>/<puntaje>')
@login_required
def agregar_calificacion(codigo,puntaje):
  ficha = request.args.get('ficha')
  query_clases = 'SELECT id_clase, titulo, fecha FROM clases WHERE curso_id = %s ORDER BY fecha DESC'
  clases = consulta(query_clases, (ficha,))
  return render_template('calificar.html', codigo=codigo, observacion=None, puntaje=puntaje, ficha=ficha, clases=clases )  
    
@app.route('/calificando',methods=['GET','POST'])
@login_required
def calificar():
  if request.method=="POST":
    doc=request.form.get('documento')
    ficha = request.form.get('ficha')
    acumulado=int(request.form.get('puntos'))
    cal= int(request.form.get('calificacion'))
    id_clase = request.form.get('id_clase')
    puntos=acumulado+cal
    
    # Obtener el `id` auto-incremental del aprendiz basado en su documento `di`
    query_get_id = 'SELECT id FROM aprendices WHERE di = %s'
    res_id = consulta(query_get_id, (doc,))
    if not res_id:
        return render_template('calificar.html', error="Aprendiz no encontrado.", codigo=doc, observacion=None, puntaje=acumulado, ficha=ficha, clases=[], calificacion=True)
    
    id_auto = res_id[0]['id']
    
    query_cal = 'insert into calificaciones(id_aprendiz, id_clase, nota) values(%s, %s, %s)'
    parametros_cal = (id_auto, id_clase, cal)
    try:
        insertar(query_cal, parametros_cal)
    except mysql.connector.Error as err:
        query_clases = 'SELECT id_clase, titulo, fecha FROM clases WHERE curso_id = %s ORDER BY fecha DESC'
        clases = consulta(query_clases, (ficha,))
        if err.errno == 1062:
            return render_template('calificar.html', error="Este aprendiz ya fue calificado para la actividad seleccionada.", codigo=doc, observacion=None, puntaje=acumulado, ficha=ficha, clases=clases, calificacion=True)
        else:
            return render_template('calificar.html', error=f"Error en BD: {err}", codigo=doc, observacion=None, puntaje=acumulado, ficha=ficha, clases=clases, calificacion=True)
    except Exception as e:
        query_clases = 'SELECT id_clase, titulo, fecha FROM clases WHERE curso_id = %s ORDER BY fecha DESC'
        clases = consulta(query_clases, (ficha,))
        return render_template('calificar.html', error=f"Ocurrió un error inesperado: {e}", codigo=doc, observacion=None, puntaje=acumulado, ficha=ficha, clases=clases, calificacion=True)

    query=('update aprendices set puntos = %s where di=%s')
    parametros=(puntos,doc)
    insertar(query,parametros)
    return redirect(url_for('admin',ficha=ficha))
  
#ruta para pagina de informacion especifica del aprendiz      
@app.route('/info_aprendiz/<codigo>')
def info_aprendiz(codigo):
  documento = codigo
  query_obs = ('select id_observacion, tipo,descripcion,DATE_SUB(fecha, INTERVAL 5 HOUR) AS fecha,estado from observaciones where id_aprendiz = %s ORDER BY fecha DESC')
  observaciones = consulta(query_obs, (documento,))
  # Obtener el id interno del aprendiz para buscar sus calificaciones
  query_id = 'SELECT id FROM aprendices WHERE di = %s'
  res_id = consulta(query_id, (documento,))
  calificaciones = []
  if res_id:
    id_aprendiz = res_id[0]['id']
    query_cal = '''
      SELECT c.id_calificacion, c.nota, c.fecha_registro, cl.titulo, cl.fecha AS fecha_clase
      FROM aprendices a INNER JOIN clases cl ON cl.curso_id = a.curso_id LEFT JOIN calificaciones c  ON c.id_clase = cl.id_clase
    AND c.id_aprendiz = a.id WHERE a.id = %s ORDER BY cl.fecha DESC
    '''
    calificaciones = consulta(query_cal, (id_aprendiz,))
    MESES_CORTO = ['', 'ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
    '''
    for cal in calificaciones:
      t = cal['titulo'].lower() if cal.get('titulo') else ''
      if 'quiz' in t:
        cal['tipo'] = 'Quiz'
        cal['tipo_badge_class'] = 'bg-emerald-100 text-emerald-800'
      elif 'practica' in t or 'práctica' in t:
        cal['tipo'] = 'Práctica'
        cal['tipo_badge_class'] = 'bg-blue-100 text-blue-800'
      elif 'taller' in t:
        cal['tipo'] = 'Taller'
        cal['tipo_badge_class'] = 'bg-amber-100 text-amber-800'
      elif 'evaluacion' in t or 'evaluación' in t:
        cal['tipo'] = 'Evaluación'
        cal['tipo_badge_class'] = 'bg-purple-100 text-purple-800'
      else:
        cal['tipo'] = 'Actividad'
        cal['tipo_badge_class'] = 'bg-emerald-100 text-emerald-800'

      if cal.get('fecha_clase'):
        try:
          fc = cal['fecha_clase']
          cal['fecha_formateada'] = f"{fc.day:02d} {MESES_CORTO[fc.month]} {fc.year}"
        except Exception:
          cal['fecha_formateada'] = str(cal.get('fecha_clase'))
      else:
        cal['fecha_formateada'] = ''
'''
  return render_template('aprendiz.html', observaciones=observaciones, calificaciones=calificaciones, codigo=codigo)


@app.route('/editar_calificacion/<id_calificacion>', methods=['GET', 'POST'])
@login_required
def editar_calificacion(id_calificacion):
  if request.method == 'POST':
    nueva_nota = float(request.form.get('calificacion'))
    codigo = request.form.get('documento')
    ficha = request.form.get('ficha')

    # Obtener la nota anterior para calcular la diferencia
    query_old = 'SELECT nota, id_aprendiz FROM calificaciones WHERE id_calificacion = %s'
    res_old = consulta(query_old, (id_calificacion,))
    if not res_old:
      return redirect(url_for('panel'))

    nota_anterior = float(res_old[0]['nota'])
    id_aprendiz_interno = res_old[0]['id_aprendiz']
    diferencia = nueva_nota - nota_anterior

    # Actualizar la nota en la tabla calificaciones
    query_upd_cal = 'UPDATE calificaciones SET nota = %s WHERE id_calificacion = %s'
    insertar(query_upd_cal, (nueva_nota, id_calificacion))

    # Ajustar los puntos acumulados del aprendiz sumando la diferencia
    query_upd_pts = 'UPDATE aprendices SET puntos = puntos + %s WHERE id = %s'
    insertar(query_upd_pts, (diferencia, id_aprendiz_interno))

    return redirect(url_for('info_aprendiz', codigo=codigo))
  else:
    # GET: obtener la calificacion actual y la clase asociada
    query_get = '''
      SELECT c.id_calificacion, c.nota, c.id_aprendiz,
             cl.titulo AS titulo_clase, cl.fecha AS fecha_clase,
             a.di
      FROM calificaciones c
      INNER JOIN clases cl ON c.id_clase = cl.id_clase
      INNER JOIN aprendices a ON c.id_aprendiz = a.id
      WHERE c.id_calificacion = %s
    '''
    res = consulta(query_get, (id_calificacion,))
    if not res:
      return redirect(url_for('panel'))

    cal = res[0]
    codigo = cal['di']
    ficha_res = consulta('SELECT curso_id FROM aprendices WHERE di = %s', (codigo,))
    ficha = ficha_res[0]['curso_id'] if ficha_res else None

    return render_template(
      'calificar.html',
      codigo=codigo,
      observacion=None,
      calificacion=True,
      editar_cal=True,
      cal_actual=cal,
      puntaje=None,
      ficha=ficha,
      clases=[]
    )

#ruta para agregar observacion al aprendiz
@app.route('/agregar_observacion/<codigo>')
@login_required
def agregar_observacion(codigo):
  ficha = request.args.get('ficha')
  return render_template('calificar.html', codigo=codigo, calificacion=None, ficha=ficha)   

@app.route('/guardar_observacion_masiva', methods=['POST'])
@login_required
def guardar_observacion_masiva():
  ficha = request.form.get('ficha')
  tipo = request.form.get('tipo')
  obs = request.form.get('observacion')
  estado = request.form.get('estado')
  aprendices_seleccionados = request.form.getlist('aprendices')

  if not aprendices_seleccionados:
    return redirect(url_for('admin', ficha=ficha))

  query = 'INSERT INTO observaciones(id_aprendiz, tipo, descripcion, estado) VALUES(%s, %s, %s, %s)'
  errores = []
  for doc in aprendices_seleccionados:
    try:
      insertar(query, (doc, tipo, obs, estado))
    except Exception as e:
      errores.append(f'{doc}: {e}')

  return redirect(url_for('admin', ficha=ficha))


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

@app.route('/eliminar_observacion/<id_observacion>')
@login_required
def eliminar_observacion(id_observacion):
  query_get = 'select id_aprendiz from observaciones where id_observacion = %s'
  resultado = consulta(query_get, (id_observacion,))
  if not resultado:
    return redirect(url_for('panel'))
  
  codigo = resultado[0]['id_aprendiz']
  query_del = 'delete from observaciones where id_observacion = %s'
  try:
    insertar(query_del, (id_observacion,))
  except Exception as e:
    pass
  
  return redirect(url_for('info_aprendiz', codigo=codigo))

@app.route('/editar_observacion/<id_observacion>', methods=['GET', 'POST'])
@login_required
def editar_observacion(id_observacion):
  if request.method == 'POST':
    tipo = request.form.get('tipo')
    obs = request.form.get('observacion')
    estado = request.form.get('estado')
    
    query_get = 'select id_aprendiz from observaciones where id_observacion = %s'
    resultado = consulta(query_get, (id_observacion,))
    if not resultado:
      return redirect(url_for('panel'))
    codigo = resultado[0]['id_aprendiz']
    
    query_upd = 'update observaciones set tipo=%s, descripcion=%s, estado=%s where id_observacion=%s'
    parametros = (tipo, obs, estado, id_observacion)
    try:
      insertar(query_upd, parametros)
      return redirect(url_for('info_aprendiz', codigo=codigo))
    except Exception as e:
      ficha = request.form.get('ficha')
      observacion = {
        'id_observacion': id_observacion,
        'tipo': tipo,
        'descripcion': obs,
        'estado': estado,
        'id_aprendiz': codigo
      }
      return render_template('calificar.html', codigo=codigo, calificacion=None, ficha=ficha, observacion=observacion, editar_obs=True, error=f'No se pudo editar: {e}')
  else:
    query_get = 'select id_observacion, id_aprendiz, tipo, descripcion, estado from observaciones where id_observacion = %s'
    resultado = consulta(query_get, (id_observacion,))
    if not resultado:
      return redirect(url_for('panel'))
    
    observacion = resultado[0]
    codigo = observacion['id_aprendiz']
    
    query_aprendiz = 'select curso_id from aprendices where di = %s'
    res_aprendiz = consulta(query_aprendiz, (codigo,))
    ficha = res_aprendiz[0]['curso_id'] if res_aprendiz else None
    
    return render_template('calificar.html', codigo=codigo, calificacion=None, ficha=ficha, observacion=observacion, editar_obs=True)


@app.route('/inasistencia_grupal/<ficha>', methods=['GET', 'POST'])
def inasistencia_grupal(ficha):
  fecha_seleccionada = request.values.get('fecha')
  
  query_fechas = """
    SELECT DISTINCT DATE(o.fecha) AS fecha 
    FROM observaciones o 
    INNER JOIN aprendices a ON a.di = o.id_aprendiz 
    WHERE o.tipo = 'Inasistencia' AND a.curso_id = %s 
    ORDER BY fecha DESC
  """
  lista_fechas_raw = consulta(query_fechas, (ficha,))
  
  lista_fechas = []
  if lista_fechas_raw:
    for f in lista_fechas_raw:
      lista_fechas.append(str(f['fecha']))
  
  if lista_fechas and not fecha_seleccionada:
    fecha_seleccionada = lista_fechas[0]
    
  aprendices = []
  if fecha_seleccionada:
    query_aprendices = """
      SELECT concat(a.nombre, ' ', a.apellidos) AS nombre, o.descripcion 
      FROM observaciones o 
      INNER JOIN aprendices a ON a.di = o.id_aprendiz 
      WHERE o.tipo = 'Inasistencia' AND DATE(o.fecha) = %s AND a.curso_id = %s 
      ORDER BY concat(a.nombre, ' ', a.apellidos)
    """
    aprendices = consulta(query_aprendices, (fecha_seleccionada, ficha))
    
  return render_template('inasistencias_grupal.html', 
                         ficha=ficha, 
                         lista_fechas=lista_fechas, 
                         fecha_seleccionada=fecha_seleccionada, 
                         aprendices=aprendices)

@app.route('/registrar_clase', methods=['GET','POST'])
@login_required
def registrar_clase():
  if request.method=="POST":
    ficha = request.form.get('ficha')
    titulo = request.form.get('titulo')
    descripcion = request.form.get('descripcion')
    # if '\\n' in descripcion: #guarda saltos de linea reales.
    #   descripcion = descripcion.encode().decode('unicode_escape')
    fecha = request.form.get('fecha') 
    print(descripcion)
    query=('insert into clases(curso_id,titulo,descripcion,fecha) values(%s,%s,%s,%s)')
    parametros=(ficha,titulo,descripcion,fecha)
    query_update = ('update cursos set cantidad_clases = cantidad_clases + 1 WHERE ficha = %s')
    parametros_update=(ficha,)
    
    try:
      insertar(query,parametros)
      insertar(query_update,parametros_update)
      return redirect(url_for('admin',ficha=ficha))
    except Exception as e:
      return render_template('admin.html',ficha=ficha, error= f'clases no registrada \n {e}')
  else:
    return redirect(url_for('panel'))  
   
@app.route('/editar_clase/<id_clase>', methods=['GET', 'POST'])
@login_required
def editar_clase(id_clase):
  if request.method == 'GET':
    query_get = 'SELECT id_clase, curso_id, titulo, descripcion, fecha FROM clases WHERE id_clase = %s'
    res = consulta(query_get, (id_clase,))
    if not res:
      return redirect(url_for('panel'))
    
    clase = res[0]
    ficha = clase['curso_id']
    
    query_aprendices = ('select di, puntos, fecha_nac, concat(nombre, " ", apellidos) as nombre_completo from aprendices where curso_id = %s order by nombre asc')
    lista_aprendices = consulta(query_aprendices, (ficha,))
    
    query_clases = ('select id_clase, titulo, descripcion, fecha from clases where curso_id = %s ORDER BY fecha desc')
    lista_clases = consulta(query_clases, (ficha,))
    
    return render_template('admin.html', 
                           aprendices=lista_aprendices, 
                           ficha=ficha, 
                           clases=lista_clases, 
                           fecha_actual=date.today(), 
                           clase_editar=clase, 
                           editar_clase=True)
  else:
    ficha = request.form.get('ficha')
    titulo = request.form.get('titulo')
    descripcion = request.form.get('descripcion')
    fecha = request.form.get('fecha')
    
    query_update = 'UPDATE clases SET titulo = %s, descripcion = %s, fecha = %s WHERE id_clase = %s'
    parametros_update = (titulo, descripcion, fecha, id_clase)
    
    try:
      insertar(query_update, parametros_update)
      return redirect(url_for('admin', ficha=ficha))
    except Exception as e:
      return render_template('admin.html', ficha=ficha, error=f'Clase no actualizada \n {e}')
   
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
    admin_id = session['id_user']
    query=('insert into cursos(ficha,nombre_curso,admin_id) values(%s,%s,%s)')
    parametros=(ficha,nombre,admin_id)
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

        query = 'INSERT INTO blog_entradas (admin_id, titulo, contenido, fecha) VALUES (%s, %s, %s, NOW())'
        parametros = (autor_id,titulo, contenido)

        try:
            insertar(query, parametros)
            return redirect(url_for('panel'))  
        except Exception as e:
            return render_template('entradas.html', error=f"No se pudo guardar la entrada: {e}")
    else:
        return render_template('entradas.html')

  
  
  
@app.route('/blog')
def blog():
  query=('select b.titulo, b.contenido, b.fecha, a.nombre as autor from blog_entradas as b inner join admins as a on b.admin_id = a.id')
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
      query = "SELECT ficha from cursos where admin_id=%s"
      cursos = consulta(query, (session['id_user'],))
      return render_template('añadir_aprendiz.html',ficha=ficha, editar=False, cursos=cursos)  
    
    
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
  
  
@app.route('/configuracion')
@login_required
def configuracion():
  return render_template('configuracion.html')


@app.route('/cerrar_sesion')
def cerrar_sesion():
  session.pop('user',None)
  error=None
  return render_template('login.html', error=error)


if __name__ == '__main__':
  app.run(debug=True, port=7000)