from app import create_app, socketio
import eventlet
eventlet.monkey_patch()


app = create_app()

gunicorn_app = app

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
