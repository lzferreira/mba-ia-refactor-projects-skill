import logging
from flask import request, jsonify
from models import usuario_model
from middlewares.errors import NotFound, ValidationError, Unauthorized

logger = logging.getLogger(__name__)


def listar_usuarios():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    offset = (page - 1) * per_page
    usuarios = usuario_model.get_todos(limit=per_page, offset=offset)
    return jsonify({"dados": usuarios, "sucesso": True}), 200


def buscar_usuario(id):
    usuario = usuario_model.get_por_id(id)
    if not usuario:
        raise NotFound("Usuário não encontrado")
    return jsonify({"dados": usuario, "sucesso": True}), 200


def criar_usuario():
    dados = request.get_json()
    if not dados:
        raise ValidationError("Dados inválidos")

    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")

    if not nome or not email or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")

    usuario_id = usuario_model.criar(nome, email, senha)
    logger.info("Usuário criado: %s", email)
    return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201


def login():
    dados = request.get_json()
    email = dados.get("email", "")
    senha = dados.get("senha", "")

    if not email or not senha:
        raise ValidationError("Email e senha são obrigatórios")

    usuario = usuario_model.verificar_login(email, senha)
    if not usuario:
        raise Unauthorized("Email ou senha inválidos")

    logger.info("Login bem-sucedido: %s", email)
    return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
