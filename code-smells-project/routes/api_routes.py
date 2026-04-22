from flask import Blueprint, jsonify
from controllers import produto_controller, usuario_controller, pedido_controller, relatorio_controller, health_controller

api = Blueprint("api", __name__)

# --- Index ---
@api.route("/")
def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": "1.0.0",
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    })

# --- Produtos ---
api.add_url_rule("/produtos", "listar_produtos", produto_controller.listar_produtos, methods=["GET"])
api.add_url_rule("/produtos/busca", "buscar_produtos", produto_controller.buscar_produtos, methods=["GET"])
api.add_url_rule("/produtos/<int:id>", "buscar_produto", produto_controller.buscar_produto, methods=["GET"])
api.add_url_rule("/produtos", "criar_produto", produto_controller.criar_produto, methods=["POST"])
api.add_url_rule("/produtos/<int:id>", "atualizar_produto", produto_controller.atualizar_produto, methods=["PUT"])
api.add_url_rule("/produtos/<int:id>", "deletar_produto", produto_controller.deletar_produto, methods=["DELETE"])

# --- Usuarios ---
api.add_url_rule("/usuarios", "listar_usuarios", usuario_controller.listar_usuarios, methods=["GET"])
api.add_url_rule("/usuarios/<int:id>", "buscar_usuario", usuario_controller.buscar_usuario, methods=["GET"])
api.add_url_rule("/usuarios", "criar_usuario", usuario_controller.criar_usuario, methods=["POST"])
api.add_url_rule("/login", "login", usuario_controller.login, methods=["POST"])

# --- Pedidos ---
api.add_url_rule("/pedidos", "criar_pedido", pedido_controller.criar_pedido, methods=["POST"])
api.add_url_rule("/pedidos", "listar_todos_pedidos", pedido_controller.listar_todos_pedidos, methods=["GET"])
api.add_url_rule("/pedidos/usuario/<int:usuario_id>", "listar_pedidos_usuario", pedido_controller.listar_pedidos_usuario, methods=["GET"])
api.add_url_rule("/pedidos/<int:pedido_id>/status", "atualizar_status_pedido", pedido_controller.atualizar_status_pedido, methods=["PUT"])

# --- Relatorios ---
api.add_url_rule("/relatorios/vendas", "relatorio_vendas", relatorio_controller.relatorio_vendas, methods=["GET"])

# --- Health ---
api.add_url_rule("/health", "health_check", health_controller.health_check, methods=["GET"])
