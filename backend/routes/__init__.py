from flask import Blueprint

# Создаем blueprints для разных групп маршрутов
main_bp = Blueprint('main', __name__)
api_bp = Blueprint('api', __name__, url_prefix='/api')
editor_bp = Blueprint('editor', __name__)
thumbnails_bp = Blueprint('thumbnails', __name__)

# Импортируем определения маршрутов
from . import main, api, editor, thumbnails

def register_blueprints(app):
    """Регистрирует все blueprints в приложении"""
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(editor_bp)
    app.register_blueprint(thumbnails_bp)