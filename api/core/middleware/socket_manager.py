from flask_socketio import SocketIO

# Instância global do SocketIO
socketio = None

def init_socketio(app):
    """Inicializa o SocketIO com a aplicação Flask"""
    global socketio
    socketio = SocketIO(cors_allowed_origins="*", async_mode="eventlet")
    socketio.init_app(app)
    return socketio

def get_socketio():
    """Retorna a instância do SocketIO"""
    if socketio is None:
        raise RuntimeError("SocketIO não foi inicializado. Chame init_socketio() primeiro.")
    return socketio

def emit_event(event_name, data=None, **kwargs):
    """Função helper para emitir eventos"""
    if socketio:
        socketio.emit(event_name, data, **kwargs)
