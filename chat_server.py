from threading import Lock
from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
import eventlet

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.

# покоже request.sid для каждого конекта индивидуален , к этому можно прикрутить бд с комнатами при выходе брать сид и удалять

async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
thread = None
thread_lock = Lock()

roomscount = 0
maxroomscount = 5
userscount = 0

usersdata={}





roomstats = {'first': ['password', 'close_close']}

roomlist = ['first', 'second']


def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        socketio.sleep(150)
        count += 1
        socketio.emit('my_response',
                      {'data': 'Server generated event', 'count': count},
                      namespace='/test')


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if request.form['nick'] != "":
            nick1 = request.form['nick']
            print(nick1)
            return render_template('chat_klient.html', nick=nick1)
    return render_template('entrance.html')


@socketio.on('my_event', namespace='/test')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']})


@socketio.on('mybroadcast_event', namespace='/test')
def test_broadcast_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']},
         broadcast=True)


@socketio.on('join', namespace='/test')
def join(message):
    rname = message['room']
    rpass = message['rpass']
    if rname in roomlist:
        if roomstats[rname[0]] == rpass:
            join_room(rname)

    # session['receive_count'] = session.get('receive_count', 0) + 1
    # emit('my_response',{'data': 'In rooms: ' + ', '.join(rooms()),'count': session['receive_count']})
    # roomlist.append(message['room'])


@socketio.on('createroom', namespace='/test')
def create(data):
    rname = data['room_name']
    rpassword = data['room_enter_password']
    rclosepassword = data['room_close_password']
    if rname not in roomlist:
        roomstats[rname] = [rpassword, rclosepassword]
        emit('nm', {'data': rname}, broadcast=True)
        roomlist.append(rname)





        usersdata[request.sid]=rname


@socketio.on('roomenter', namespace='/test')
def newroom(data):
    rm = data['rname']
    rp = data['password']
    print('newRoom')
    global roomscount
    if rm not in roomlist:

        if roomscount < maxroomscount:
            emit('nm', {'data': rm}, broadcast=True)
            roomlist.append(rm)
    if (data['rname'] in roomlist) and (roomstats[rm][0] == rp):
        join_room(rm)
        emit('my_response', {'data': 'some joined'})
        print('eeeerock')


@socketio.on('loaddata', namespace='/test')
def load_data():
    emit('loadd', roomlist)
    print('loadd')


@socketio.on('leave', namespace='/test')
def leave(message):
    leave_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})
    roomstats[message['room']] -= 1
    if roomstats[message['room']] < 1:
        close_room(message['room'])
        emit('delete_room', message['room'])


@socketio.on('close_room', namespace='/test')
def close(message):
    cpas = message['close_password']
    rtoclose = message['roomtoclose']
    print(cpas, rtoclose)
    if rtoclose in roomlist:
        if roomstats[rtoclose][1] == cpas:
            close_room(rtoclose)
            emit('my_response', {'data': 'GLOBAL EVENT:' + rtoclose + 'was closed'})
            emit('delete_room', rtoclose,broadcast=True)
            roomlist.remove(rtoclose)
            del roomstats[rtoclose]
            print('roomclosed')

    # session['receive_count'] = session.get('receive_count', 0) + 1
    # emit('my_response', {'data': 'Room ' + message['room'] + ' is closing.',
    #                    'count': session['receive_count']},
    #   room=message['room'])
    # close_room(message['room'])


@socketio.on('create_room', namespace='/test')
def createnakonez(data):
    rname = data['rname']
    renter_pas = data['renter_password']
    rclose_pas = data['rclose_password']
    print(rname, renter_pas, rclose_pas)
    if rname not in roomlist:
        roomstats[rname] = [renter_pas, rclose_pas]
        emit('nm', {'data': rname}, broadcast=True)
        roomlist.append(rname)


@socketio.on('my_room_event', namespace='/test')
def send_room_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']},
         room=message['room'])


@socketio.on('disconnect_request', namespace='/test')
def disconnect_request():
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'Disconnected!', 'count': session['receive_count']})
    print('disconnect')
    if request.sid in usersdata:
        rtoclose=usersdata[request.sid]
        close_room(rtoclose)
        emit('my_response', {'data': 'GLOBAL EVENT:' + rtoclose + 'was closed after leave'})
        emit('delete_room', rtoclose, broadcast=True)
        roomlist.remove(rtoclose)
        del roomstats[rtoclose]
        print('closed after leave the chat')
    disconnect()


@socketio.on('my_ping', namespace='/test')
def ping_pong():
    emit('my_pong')


@socketio.on('connect', namespace='/test')
def test_connect():
    global userscount
    userscount += 1
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=background_thread)
    emit('my_response', {'data': 'Connected', 'count': 0})
    print(userscount,request.sid)


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    global userscount
    userscount -= 1
    print('Client disconnected', request.sid, userscount)
    if request.sid in usersdata:
        rtoclose=usersdata[request.sid]
        close_room(rtoclose)
        emit('my_response', {'data': 'GLOBAL EVENT:' + rtoclose + 'was closed after leave'})
        emit('delete_room', rtoclose, broadcast=True)
        roomlist.remove(rtoclose)
        del roomstats[rtoclose]
        print('closed after leave the chat')


# [ERROR] Socket error processing request.

host=['0.0.0.0','127.0.0.1']

if __name__ == '__main__':
    socketio.run(app, debug=True,host=host[0],port=4000)


#7137ec7d45b74334b6b01ee8b4e5c0b8
#7137ec7d45b74334b6b01ee8b4e5c0b8