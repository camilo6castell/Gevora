import os
from flask import Flask, url_for, render_template, request, redirect, session, g, send_file, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import escape
import sqlite3
from sqlite3 import Error
from forms import ReserveForm
import utils

app = Flask(__name__)
app.secret_key = os.urandom( 24 ) #creación de secret key para firmar

#Variable global para validar funciones en las vistas html

@app.before_request
def before_request():
    usuario = session.get('usuario')
    if usuario == None:
        g.usuario = None
    else:
        g.usuario = session.get('usuario')

#Página de inicio e inicio de sesión con validaciones para los diferentes usuarios
@app.route('/')
@app.route('/<login>', methods=['POST'])
def log_in(login=None):
    if g.usuario != None:
        return redirect(url_for('home'))
    else:
        if login == None: 
            return render_template('index.html')
        else:  
            email = escape(request.form.get('user'))
            password = escape(request.form.get('pass'))
            joker = ""

            try:
                with sqlite3.connect('db.db') as con:  #conectando base de datos          
                    cur = con.cursor() # cursor para modificar base de dato
                    result = cur.execute('SELECT * FROM users WHERE email = ? ', [email]).fetchone() #consulta
                    if result == None:
                        joker = 'Usuario o contraseña inválidos, vuelve a intentarlo'
                        return render_template( 'joker.html', joker=joker), {"Refresh":"2;/"}
                    hpassword = result[2]
                    if (check_password_hash(hpassword,password)): #verificación de password
                        session['usuario'] = result[1] #creación de sesión en cookie cifrada
                        session['id'] = result[0] #creación de dato "id" en cookie
                        name = result[1].split('@') #Obtuve el nombre de usuario con el objetivo de usar esta info en una cookie en el paso siguiente
                        if session.get('usuario') == "Superadmin1@superadmin1.com": #creación de sesion especial
                            respuesta = make_response(redirect(url_for('home', special='sa'))) #Creacion de encabezado http adicional para cookie
                            respuesta.set_cookie('name', name[0]) #Creación de la cookie en encabezado adicional ya creado
                            return respuesta
                        if session.get('usuario') == "Admin1@admin1.com": #creación de sesion especial
                            respuesta = make_response(redirect(url_for('home', special="a"))) #Creacion de encabezado http adicional para cookie
                            respuesta.set_cookie('name', name[0]) #Creación de la cookie en encabezado adicional ya creado
                            return respuesta
                        respuesta = make_response(redirect(url_for('home'))) #Creacion de encabezado http adicional para cookie
                        respuesta.set_cookie('name', name[0]) #Creación de la cookie en encabezado adicional ya creado
                        return respuesta
                    else:
                        joker = 'Usuario o contraseña inválidos, vuelve a intentarlo' # variable para mostras en página de información y transicion. 
                        return render_template( 'joker.html', joker=joker), {"Refresh":"2;/"}     
            except Error:
                print("Ocurrió un error", Error)
                return redirect('/')

#Vista de registro y función para registrarse

@app.route('/signup')
@app.route('/signup/<signup>', methods=['POST'])
def signup(signup=None):
    if signup == None: 
        return render_template("signup.html")
    else:
        email = escape(request.form['user']) #recuperación de datos de los form del html
        password = escape(request.form['pass']) #recuperación de datos de los form del html
        joker = ""

        if not utils.isEmailValid( email ): #comprobando validez de email desde backend
            joker = "email invalido, vuelve a intentarlo"
            return render_template( 'joker.html', joker=joker), {"Refresh":"2;/"}                 

        if not utils.isPasswordValid( password ): #comprobando validez de password desde backend
            joker = "password invalido, vuelve a intentarlo"
            return render_template( 'joker.html', joker=joker), {"Refresh":"2;/"}     
            
        hpassword = generate_password_hash(password) #cifrando password

        try:
            with sqlite3.connect('db.db') as con:
                cur = con.cursor()                   
                if cur.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone() is not None: #consulta para saber si el dato ya existe en la db
                    joker = "Email ya registrado, por favor inicia sesión"
                    return render_template( 'joker.html', joker=joker ), {"Refresh": "3;/"}   
                else:
                    cur.execute( 'INSERT INTO users (email, password) VALUES (?,?) ', (email, hpassword) ) #insertar usuaro si no existe
                    con.commit()
                    joker = "Ya te encuentras registrado, por favor inicia sesión"
                    return render_template( 'joker.html', joker=joker ), {"Refresh": "3;/"}  
        except Error:
            print(Error)
            joker = "Ha sucedido un error del servidor. Por favor contacta al administrador para más información"
            return render_template( 'joker.html', joker=joker ), {"Refresh": "3;/"}  

#Páginas de inicio y reserva de usuario final

@app.route('/home')
@app.route('/home/<special>', methods=['GET','POST'])
def home(special=None):
    name = request.cookies.get('name')
    form = ReserveForm()
    if g.usuario == None: #Restricción a que sólo usuarios loggeados puedan acceder a vistas de procesos internos
        joker = "Debes iniciar sesión para poder acceder a nuestros servicios"
        return render_template( 'joker.html', joker=joker ), {"Refresh": "2;/"}
    else:
        if special == None:
            try:
                with sqlite3.connect('db.db') as con: #consulta para mostrar datos de feedback en la vista de home
                    cur = con.cursor()       
                    rowRaw = cur.execute('SELECT * FROM rooms').fetchall()
                    rowRooms = [x[0] for x in rowRaw] #Lista de id de habitaciones disponibles
                    rowRoomsL = len(rowRooms)
                    rowRes = [x[2] for x in rowRaw] #Lista de reservas
                    listRatesRaw = [] #lista de rates de habitaciones disponibles ordenadas
                    for i in range(len(rowRooms)):
                        listRatesRaw.append(cur.execute('SELECT stars FROM feedback WHERE room = ?', [rowRooms[i]]).fetchall())
                    listProm =[] # Lista de promedio por habitación
                    for i in range(len(listRatesRaw)):
                        for j in range(len(listRatesRaw[i])):
                            listRatesRaw[i][j] = listRatesRaw[i][j][0] #Se eliminan las comas de los datos para poder operar
                    for i in range(len(listRatesRaw)):
                        if len(listRatesRaw[i]) != 0:
                            listProm.append(round(sum(listRatesRaw[i])/len(listRatesRaw[i]),1))
                        else:
                            listRatesRaw[i] = 0
                            listProm.append(listRatesRaw[i])
                    return render_template("homeu.html", rowRooms=rowRooms, rowRoomsL=rowRoomsL, listProm=listProm, rowRes=rowRes, form=form, name=name)
            except Error:
                print("Ocurrio un error: ", Error)
                joker = "Ha sucedido un error del servidor. Por favor contacta al administrador para más información"
                return render_template( 'joker.html', joker=joker ), {"Refresh": "3;/"}
        if special == "a":  #Inicio administrador
            return render_template("homea.html", name=name)
        if special == "sa": #Inicio súperadministrador
            return render_template("homesa.html", name=name)
        if special == "re": #Reservas
            idR = request.form.get("id") #Número de habitación
            days = form.days.data #Días de reserva

            print(session.get('id'), days, idR)
            try: 
                with sqlite3.connect("db.db") as con: #consulta para reservar habitaciones
                    cur = con.cursor()
                    cur.execute("UPDATE rooms SET guest = ?, reserved = ? WHERE id = ? ", [session.get('id'), days, idR])
                    con.commit()
                    joker = "Felicitaciones, ¡has reservado con éxito!"
                    return render_template( 'joker.html', joker=joker ), {"Refresh": "2;/home"}              
            except Error:
                print("Ha ocurrido un error", Error)
                return render_template("error.html")
    
#Vista de control de usuarios

@app.route('/controlu')
@app.route('/controlu/<a>', methods=['POST'])
def controlu(a=None):
    if g.usuario == None: #Restricción a que sólo usuarios loggeados puedan acceder a vistas de procesos internos
        joker = "Debes iniciar sesión para poder acceder a nuestros servicios"
        return render_template( 'joker.html', joker=joker ), {"Refresh": "2;/"}
    else:
        if a == None:
            try:
                with sqlite3.connect("db.db") as con: #consulta para mostrar usuarios  en la vista de administrar usuarios
                    cur = con.cursor()
                    rowRaw = cur.execute("SELECT * FROM users").fetchall()
                    rowN = len(rowRaw)
                    return render_template("controlu.html", rowN=rowN, rowRaw=rowRaw)
            except Error:
                print("Ha ocurrido un error", Error)
                return render_template("error.html")
        else:    
            try:
                with sqlite3.connect('db.db') as con: #consulta para mostrar usuarios y ser eliminados en la vista de administrar usuarios
                    cur = con.cursor()
                    cur.execute('DELETE FROM users WHERE id = ?', [a])
                    con.commit()
                    joker = "Eliminado con éxito"
                    return render_template( 'joker.html', joker=joker ), {"Refresh": "2;/controlu"}
            except Error:
                print("Ha ocurrido un error", Error)
                return render_template("error.html") 
            
#Vista de control de habitaciones

@app.route('/controlh')
@app.route('/controlh/<a>', methods=['POST'])
def controlh(a=None):
    if g.usuario == None: #Restricción a que sólo usuarios loggeados puedan acceder a vistas de procesos internos
        joker = "Debes iniciar sesión para poder acceder a nuestros servicios"
        return render_template( 'joker.html', joker=joker ), {"Refresh": "2;/"}
    else:
        if a == None:
            try:
                with sqlite3.connect("db.db") as con:
                    cur = con.cursor()
                    rowRaw = cur.execute("SELECT * FROM rooms").fetchall() #consulta para mostrar habitaciones  en la vista de administrar habitaciones
                    rowN = len(rowRaw)
                    return render_template("controlh.html", rowN=rowN, rowRaw=rowRaw)
            except Error:
                print("Ha ocurrido un error", Error)
                return render_template("error.html")          
        if a == "add":
            try:
                with sqlite3.connect('db.db') as con: #consulta para mostrar agregar habitaciones en la vista de administrar habitaciones
                    cur = con.cursor()
                    cur.execute('INSERT INTO rooms (guest, reserved) VALUES (?, ?)', [None, None])
                    con.commit()
                    joker = "Habitación agregada con éxito"
                    return render_template( 'joker.html', joker=joker ), {"Refresh": "2;/controlh"}
            except Error:
                print("Ha ocurrido un error", Error)
                return render_template("error.html")
        else:
            try:
                with sqlite3.connect('db.db') as con: #consulta para mostrar eliminar habitaciones en la vista de administrar habitaciones
                    cur = con.cursor()
                    cur.execute('DELETE FROM rooms WHERE id = ?', [int(a)])
                    con.commit()
                    joker = "Habitación eliminada con éxito"
                    return render_template( 'joker.html', joker=joker ), {"Refresh": "2;/controlh"} 
            except Error:
                print("Ha ocurrido un error", Error)
                return render_template("error.html") 

#Realizar puntuación con estrellas y comentar

@app.route('/feedback/<int:i>', methods=['GET','POST'])
def feed_back(i):
    if g.usuario == None: #Restricción a que sólo usuarios loggeados puedan acceder a vistas de procesos internos
        joker = "Debes iniciar sesión para poder acceder a nuestros servicios"
        return render_template( 'joker.html', joker=joker ), {"Refresh": "2;/"}
    else:
        c = request.form.get('comentario')
        s = request.form.get('estrellas')
        if s == None :
            return render_template('feedback.html',i=i)
        else:
            try:
                with sqlite3.connect('db.db') as con: #consulta para realizar feedback de habitaciones
                    cur = con.cursor()
                    cur.execute("INSERT INTO feedback (guest, room, stars, coment) VALUES (?,?,?,?)", (session.get('id'), i, s, c))
                    con.commit()
                    joker = "Feedback realizado con éxito"
                    return render_template('joker.html', joker=joker ), {"Refresh": "2;/home"}       
            except Error:
                print("Ha ocurrido un error", Error)
        return redirect("error.html")

#Vista administración de comentarios 

@app.route('/editcom/<int:i>')
@app.route('/editcom/<int:i>/<a>', methods=["POST"])
def editcom(i,a=None):
    if g.usuario == None: #Restricción a que sólo usuarios loggeados puedan acceder a vistas de procesos internos
        joker = "Debes iniciar sesión para poder acceder a nuestros servicios"
        return render_template( 'joker.html', joker=joker ), {"Refresh": "2;/"}
    else: 
        if a == None: #Renderizar página de editar feedback
            try:
                with sqlite3.connect("db.db") as con: #consulta para mostrar datos de estrellas y comentarios listos a editar
                    cur = con.cursor()
                    row = cur.execute("SELECT * FROM feedback where guest = ?", [session.get("id")]).fetchall()
                    rowN = len(row)
                    return render_template("editcom.html", i=i, rowN=rowN, row=row)
            except Error:
                print("Ha ocurrido un error", Error)
                return render_template("error.html")
        if a == "co": #editar comentarios
            idC = request.form.get('id') #ID del feedback
            coment = escape(request.form.get('coment')) #Contenido del comentario modificado
            try:
                with sqlite3.connect("db.db") as con:
                    cur = con.cursor()
                    cur.execute("UPDATE feedback SET coment = ? WHERE id = ? ", [coment, idC,])
                    con.commit()
                    joker = "Se actualizó el comentario correctamente"
                    return render_template('joker.html', joker=joker ), {"Refresh": f"2;/editcom/{i}"}            
            except Error:
                print("Ha ocurrido un error", Error)
                return render_template("error.html")
        if a == "es": #editar estrellas
            idS = request.form.get('id"') #ID del feedback
            stars = request.form.get('stars') #Número de estrellas actualizado
            try:
                with sqlite3.connect("db.db") as con:
                    cur = con.cursor()
                    cur.execute("UPDATE feedback SET stars = ? WHERE id = ? ", [stars, idS,])
                    con.commit()
                    joker = "Se actualizaron estrellas correctamente"
                    return render_template('joker.html', joker=joker ), {"Refresh": f"2;/editcom/{i}"}            
            except Error:
                print("Ha ocurrido un error", Error)
                return render_template("error.html")
        else: #Eliminar feedback completo
                idR = request.form.get("id")
                try:                    
                    with sqlite3.connect("db.db") as con:
                        cur = con.cursor()
                        cur.execute("DELETE FROM feedback WHERE id = ?", [idR])
                        con.commit()
                        joker = "Se eliminó feedback correctamente"
                        return render_template('joker.html', joker=joker ), {"Refresh": f"2;/editcom/{i}"}        
                except Error:
                    print("Ha ocurrido un error", Error)
                    return render_template("error.html")

#Descarga de información

@app.route('/download/<a>')
def download(a):
    if a == "users":
        with open('resources/lista.txt', 'w+', encoding='utf-8') as userslist:
            try:
                with sqlite3.connect('db.db') as con:
                    cur = con.cursor()
                    row = cur.execute('SELECT email from users').fetchall()
                    for user in row:
                        userslist.write(f'{user[0]}' + '\n')
                    userslist.close()
                    return send_file('resources/lista.txt', as_attachment = True)
            except Error:
                print("Ha ocurrido un error", Error)
                return render_template("error.html")
    if a == 'logo':
        return send_file(r'static\images\big_icon.png', as_attachment = True)            

#Acción cerrar sesión

@app.route('/log_out/')
def log_out():
    session.pop('usuario', None)
    joker = "Cerraste sesión"
    return render_template( 'joker.html', joker=joker ), {"Refresh": "1;/"} 

#Manejo de errores

@app.errorhandler(404)
def page_not_found(error):
    return render_template('error.html', error="pagina no encontrada"), 404

if __name__ == '__main__':
    app.run(debug=True, port=8000)