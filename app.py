from app import create_app, socketio
import eventlet
eventlet.monkey_patch()

# to run:
#gunicorn -k eventlet -w 1 -b 0.0.0.0:8080 run:gunicorn_app
# python3 dev.py

app = create_app()

gunicorn_app = app

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
