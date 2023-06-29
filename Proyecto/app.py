from datetime import datetime
from flask import Flask, request, render_template, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from password import PasswordVer

app = Flask(__name__)
app.config.from_pyfile('config.py')

from models import db 
from models import Estudiante, Curso, Asistencia, Padre, Preceptor
		
@app.route('/')
def inicio():
	return render_template('inicio.html')	

@app.route('/iniciopadre')
def iniciopadre():
	return render_template('inicioPadre.html')

@app.route('/iniciopreceptor')
def iniciopreceptor():
	return render_template('inicioPreceptor.html')

@app.route('/loginpadre', methods = ['GET','POST'])
def loginpadre():  
	if request.method == 'POST': 
		if not request.form['ePadre'] or not request.form['passPadre']:
			return render_template('inicioPadre.html')
		else:
			UsuarioPadre = Padre.query.filter_by(correo= request.form['ePadre']).first()
			if UsuarioPadre is None: #si no encuentra el usuario
				return render_template('inicioPadre.html', error="El correo no está registrado")
			else:
				verificacion = PasswordVer(request.form['passPadre'])
				if verificacion.validarPassword(UsuarioPadre.clave) :                    
					return render_template('menuPadre.html', usuario = UsuarioPadre)
				else:
					return render_template('inicioPadre.html', error="La contraseña no es válida")


@app.route('/loginpreceptor', methods = ['GET','POST'])
def loginpreceptor():  
	if request.method == 'POST': 
		if not request.form['ePreceptor'] or not request.form['passPreceptor']:
			return render_template('inicioPreceptor.html')
		else:
			UsuarioPreceptor = Preceptor.query.filter_by(correo= request.form['ePreceptor']).first()
			if UsuarioPreceptor is None: #si no encuentra el usuario
				return render_template('inicioPreceptor.html', error="El correo no está registrado")
			else:
				verificacion = PasswordVer(request.form['passPreceptor'])
				if verificacion.validarPassword(UsuarioPreceptor.clave): 
					session["idpreceptor"]=UsuarioPreceptor.id                   
					return render_template('menuPreceptor.html', usuario = UsuarioPreceptor)
				else:
					return render_template('inicioPreceptor.html', error="La contraseña no es válida")

@app.route('/menupreceptor', methods = ['GET','POST'])
def menupreceptor():
	if request.method == 'GET':
		return render_template('menuPreceptor.html')

@app.route('/menupadre', methods = ['GET','POST'])
def menupadre():
	if request.method == 'GET':
		return render_template('menuPadre.html')

@app.route('/registrarAsistencia')
def registrarAsistencia(): 
	PreceptorOnLine=Preceptor.query.filter(Preceptor.id==session["idpreceptor"]).first()
	return render_template('fecha.html', PreceptorOnLine=PreceptorOnLine)
	
@app.route('/nueva_Asistencia', methods = ['GET','POST'])
def nueva_Asistencia():
	PreceptorOnLine=Preceptor.query.filter(Preceptor.id==session["idpreceptor"]).first()
	if request.method == 'POST':
		if  not request.form['idcurso'] or not request.form['clase'] or not request.form['fecha']:
			return render_template('fecha.html', PreceptorOnLine=PreceptorOnLine)
		else:
			session['tipoclase'] = int(request.form['clase'])
			session['datechose'] = request.form['fecha']
			curso=request.form['idcurso']
			session['cursoselec'] = curso
			cursoActual= Curso.query.filter_by(id=curso).first() #me devuelve el objeto
			estudiantes= Estudiante.query.filter_by(idcurso = cursoActual.id).order_by(Estudiante.apellido, Estudiante.nombre).all()
			longitud=range(len(estudiantes))
			return render_template('regAlumno.html', estudiantes=estudiantes, longitud=longitud)

@app.route('/AsistenciaAlumnos', methods = ['GET','POST'])
def AsistenciaAlumnos():
	if request.method == 'POST':
		date= session.get("datechose")
		clase= session.get("tipoclase")
		curso = Curso.query.filter_by(id=session['cursoselec']).first()
		estudiantes = Estudiante.query.filter_by(idcurso = curso.id).order_by(Estudiante.apellido, Estudiante.nombre).all()
		for i in range(len(estudiantes)):
			asis=request.form[f'asistio{i}']
			just=request.form.get(f'justificacion{i}',"")
			nuevoregistro=Asistencia(fecha=datetime.strptime(date, "%Y-%m-%d").date(), codigoclase=clase, asistio=asis, justificacion=just ,idestudiante=estudiantes[i].id )
			db.session.add(nuevoregistro)
		db.session.commit()
		return render_template('regComplete.html')
	
@app.route('/generarInforme')
def generarInforme():
	PreceptorOnLine=Preceptor.query.filter(Preceptor.id==session["idpreceptor"]).first()
	return render_template('curso.html', PreceptorOnLine=PreceptorOnLine)

@app.route('/mostrarInforme', methods = ['POST'])
def mostrarInforme():
	listado=[]
	if request.method== 'POST':
		idcurso = request.form['idcurso'] 
		curso= Curso.query.filter_by(id=idcurso).first() #me devuelve el objeto
		estudiantes= Estudiante.query.order_by(Estudiante.apellido, Estudiante.nombre).all()

		for estudiante in estudiantes:
			if estudiante.idcurso == curso.id:
				aulaP = 0
				aulaJ = 0
				aulaI = 0
				gymP = 0
				gymJ = 0
				gymI = 0
				total= 0.0
				asistencias = Asistencia.query.filter_by(idestudiante=estudiante.id).all()
				for asistencia in asistencias:
					if asistencia.codigoclase == 1:
						if asistencia.asistio == 's':
							aulaP += 1
						else: 
							if asistencia.justificacion == None: 
								aulaI += 1
							else:
								aulaJ += 1
							total +=1
					else:
						if asistencia.asistio == 'n':
							if asistencia.justificacion == None:
								gymI +=1
							else:
								gymJ +=1
							total += 0.5
						else:
							gymP += 1
						
					info_asistencia = {
                    'apellido': estudiante.apellido,
                    'nombre': estudiante.nombre,
                    'aulaPresentes': aulaP,
                    'aulaJustificadas': aulaJ,
                    'aulaInjustificadas':aulaI,
		    		'gymPresentes': gymP,
                    'gymJustificadas':gymJ,
                    'gymInjustificadas':gymI,
                    'total':total
                    }
				listado.append(info_asistencia)
							
		return render_template('informe.html', curso=curso, listado=listado)

if __name__ == '__main__':
	    app.run(debug = True)
