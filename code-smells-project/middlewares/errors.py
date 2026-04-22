import logging
from flask import jsonify

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base application error."""
    status = 500
    message = "Internal server error"

    def __init__(self, message=None, status=None):
        if message:
            self.message = message
        if status:
            self.status = status
        super().__init__(self.message)


class NotFound(AppError):
    status = 404
    message = "Resource not found"


class ValidationError(AppError):
    status = 400
    message = "Validation error"


class Forbidden(AppError):
    status = 403
    message = "Forbidden"


class Unauthorized(AppError):
    status = 401
    message = "Unauthorized"


def register_error_handlers(app):
    @app.errorhandler(404)
    def handle_not_found(e):
        return jsonify({"erro": "Recurso não encontrado", "sucesso": False}), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        return jsonify({"erro": "Método não permitido", "sucesso": False}), 405

    @app.errorhandler(AppError)
    def handle_app_error(e):
        return jsonify({"erro": e.message, "sucesso": False}), e.status

    @app.errorhandler(Exception)
    def handle_unexpected(e):
        logger.exception("Unhandled error")
        return jsonify({"erro": "Internal server error", "sucesso": False}), 500
