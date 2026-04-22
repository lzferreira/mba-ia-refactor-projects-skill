import logging
from flask import request, jsonify
from models import pedido_model
from services import pedido_service
from services.pedido_service import VALID_STATUSES
from middlewares.errors import ValidationError

logger = logging.getLogger(__name__)


def criar_pedido():
    dados = request.get_json()
    if not dados:
        raise ValidationError("Dados inválidos")

    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")

    resultado = pedido_service.criar_pedido(usuario_id, itens)
    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201


def listar_pedidos_usuario(usuario_id):
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    offset = (page - 1) * per_page
    pedidos = pedido_model.get_por_usuario(usuario_id, limit=per_page, offset=offset)
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def listar_todos_pedidos():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    offset = (page - 1) * per_page
    pedidos = pedido_model.get_todos(limit=per_page, offset=offset)
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def atualizar_status_pedido(pedido_id):
    dados = request.get_json()
    novo_status = dados.get("status", "")

    if novo_status not in VALID_STATUSES:
        raise ValidationError("Status inválido")

    pedido_model.atualizar_status(pedido_id, novo_status)
    logger.info("Pedido %d status atualizado para %s", pedido_id, novo_status)
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
