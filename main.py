from flask import Flask, render_template, redirect, request, session, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
from string import ascii_uppercase
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chatroomtest'
socketio = SocketIO(app)

rooms = {}

def generate_room_code(length):
    while True:
        code = ''
        for _ in range(length):
            code += random.choice(ascii_uppercase)

        if code not in rooms:
            break
    return code

 
@app.route('/', methods=['POST','GET'])
def home():
    session.clear()
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        join = request.form.get('join', False)
        create = request.form.get('create', False)

        if not name:
            return render_template('home.html', err='Please enter a name', name=name, code=code)
        
        if not code and join != False:
            return render_template('home.html', err='Please enter a room code', name=name, code=code)
        
        room = code
        if create != False:
            room = generate_room_code(4)
            rooms[room] = {'members':0, 'messages':[]}
        elif code not in rooms:
            return render_template('home.html', err='Room does not exist', name=name, code=code)
        
        session['room'] = room
        session['name'] = name

        return redirect(url_for('room'))
        
        
    return render_template('home.html')

@app.route('/room')
def room():
    room = session.get('room')
    name = session.get('name')
    if room is None or name is None or room not in rooms:
        return redirect(url_for('home'))
    return render_template('room.html', room=room)


@socketio.on('connect')
def connect(auth):
    room = session.get('room')
    name = session.get('name')

    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return
    
    join_room(room)
    send({'name':name, 'message':'has entered the room'}, to=room)
    rooms[room]['members'] += 1
    print(f'{name} joined room {room}')


@socketio.on('message')
def message(data):
    room = session.get('room')
    name = session.get('name')

    if room not in rooms:
        return
    
    content = {
        'name': name,
        'message': data['data']
    }   

    send(content, to=room)
    rooms[room]['messages'].append(content)
    print(f'{name} said {data["data"]}')

@socketio.on('disconnect')
def disconnect():
    name = session.get('name')
    room = session.get('room')
    leave_room(room)

    if room in rooms:
        rooms[room]['members'] -= 1
        if rooms[room]['members'] <= 0:
            del rooms[room]

    send({'name':name, 'message':'has left the room'}, to=room)
    print(f'{name} left room {room}')

if __name__ == '__main__':
    socketio.run(app, debug=True)