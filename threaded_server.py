import cv2
from flask import Flask, render_template
import socketio
import time
from threading import Thread
import base64

from gevent import monkey
monkey.patch_all()

sio = socketio.Server()
app = Flask(__name__, static_url_path='/static')
app.wsgi_app = socketio.Middleware(sio, app.wsgi_app)
thread = None

sid2 = 0
@sio.on('connect')
def connect(sid, environ):
    global sid2, thread
    sid2 = sid

    if thread is None:
        thread = sio.start_background_task(video_thread)

    print("connect ", sid)
    print("sio.emit('message', room=", sid, ")")


@sio.on('message')
async def message(sid, data):
    print("message ", data)
    await sio.emit('message', "reply to message", room=sid)


@sio.on('disconnect')
def disconnect(sid):
    print('disconnect ', sid)

def video_thread():

    global sio

    cap = cv2.VideoCapture(0)

    currentFrame = 0

    print("STARTING VIDEO CAPTURE")

    while True:

        sio.sleep(1/60)

        # Capture frame-by-frame
        ret, frame = cap.read()

        # Handles the mirroring of the current frame
        frame = cv2.flip(frame, 1)
        # frame = cv2.resize(frame, (200,200))


        retval, buffer = cv2.imencode('.jpg', frame)
        jpg_as_text = base64.b64encode(buffer)

        # Our operations on the frame come here
        # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Saves image of the current frame in jpg file
        # name = 'frame' + str(currentFrame) + '.jpg'
        # cv2.imwrite(name, frame)

        # Display the resulting frame
        # cv2.imshow('frame', frame)

        print("in loop: sio.emit('message', room=", sid2, ")")
        sio.emit('message', str(jpg_as_text))

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        # To stop duplicate images
        currentFrame += 1

    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':

    # deploy with gevent
    from gevent import pywsgi
    try:
        from geventwebsocket.handler import WebSocketHandler
        websocket = True
    except ImportError:
        websocket = False
    if websocket:
        pywsgi.WSGIServer(('', 8080), app, handler_class=WebSocketHandler).serve_forever()
    else:
        pywsgi.WSGIServer(('', 8080), app).serve_forever()



