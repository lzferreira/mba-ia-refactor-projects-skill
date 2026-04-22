import logging
from flask import request, jsonify
from models import produto_model
from validators.produto_validator import validar_produto
from middlewares.errors import NotFound

logger = logging.getLogger(__name__)


def listar_produtos():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    offset = (page - 1) * per_page
    produtos = produto_model.get_todos(limit=per_page, offset=offset)
    return jsonify({"dados": produtos, "sucesso": True}), 200


def buscar_produtos():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria")
    preco_min = request.args.get("preco_min", type=float)
    preco_max = request.args.get("preco_max", type=float)
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    offset = (page - 1) * per_page

    resultados = produto_model.buscar(termo, categoria, preco_min, preco_max, limit=per_page, offset=offset)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200


def buscar_produto(id):
    produto = produto_model.get_por_id(id)
    if not produto:
        raise NotFound("Produto não encontrado")
    return jsonify({"dados": produto, "sucesso": True}), 200


def criar_produto():
    dados = request.get_json()
    validar_produto(dados)

    produto_id = produto_model.criar(
        dados["nome"],
        dados.get("descricao", ""),
        dados["preco"],
        dados["estoque"],
        dados.get("categoria", "geral"),
    )
    logger.info("Produto criado com ID: %d", produto_id)
    return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201


def atualizar_produto(id):
    dados = request.get_json()

    produto_existente = produto_model.get_por_id(id)
    if not produto_existente:
        raise NotFound("Produto não encontrado")

    validar_produto(dados)

    produto_model.atualizar(
        id,
        dados["nome"],
        dados.get("descricao", ""),
        dados["preco"],
        dados["estoque"],
        dados.get("categoria", "geral"),
    )
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar_produto(id):
    produto = produto_model.get_por_id(id)
    if not produto:
        raise NotFound("Produto não encontrado")

    produto_model.deletar(id)
    logger.info("Produto %d deletado", id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
