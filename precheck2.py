from flask import Flask, render_template
from threading import Lock
from flask_socketio import SocketIO, emit, disconnect
import paramiko, select

async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()


def background_thread():
    """Example of how to send server generated events to clients."""
    trans = paramiko.Transport(('10.221.155.200', 22))
    trans.start_client()
    trans.auth_password(username='root', password='Changeme123')
    channel = trans.open_session()
    channel.get_pty()
    channel.invoke_shell()
    channel.sendall('cd /opt/app/lyan/pythonworkspace/ && sh test.sh\n')
    while True:
        readlist, writelist, errlist = select.select([channel], [], [])
        if channel in readlist:
            result = channel.recv(1024)
            if len(result) == 0:
                socketio.emit('my_response', {'data': "EOF"}, namespace='/test')
                break
            socketio.emit('my_response', {'data': result}, namespace='/test')
    channel.close()
    trans.close()
    # count = 0
    # while True:
    #     socketio.sleep(10)
    #     count += 1
    #     socketio.emit('my_response',
    #                   {'data': 'Server generated event', 'count': count},
    #                   namespace='/test')


@app.route('/')
def hello_world():
    return render_template('index.html', async_mode=socketio.async_mode)



# @socketio.on('my_ping', namespace='/test')
# def ping_pong():
#     emit('my_pong')


@socketio.on('disconnect_request', namespace='/test')
def disconnect_request():
    emit('my_response',
         {'data': 'Disconnected!'})
    disconnect()


@socketio.on('connect', namespace='/test')
def test_connect():
    # global thread
    # with thread_lock:
    #     if thread is None:
    #         thread = socketio.start_background_task(target=background_thread)
    emit('my_response', {'data': 'Connected', 'count': 0})


@socketio.on('exec_remote_command', namespace='/test')
def exec_remote_command():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=background_thread)
    emit('my_response', {'data': 'Cexec', 'count': 0})



if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5555)
