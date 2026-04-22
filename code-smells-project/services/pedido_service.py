import logging
from config.database import get_db
from models import pedido_model
from middlewares.errors import ValidationError

logger = logging.getLogger(__name__)

VALID_STATUSES = ("pendente", "aprovado", "enviado", "entregue", "cancelado")


def criar_pedido(usuario_id, itens):
    """Create an order inside a transaction. Returns dict with pedido_id and total."""
    if not itens:
        raise ValidationError("Pedido deve ter pelo menos 1 item")

    db = get_db()
    total = 0

    # Validate stock and calculate total
    itens_validados = []
    for item in itens:
        produto = pedido_model.get_produto_para_pedido(item["produto_id"])
        if produto is None:
            raise ValidationError(f"Produto {item['produto_id']} não encontrado")
        if produto["estoque"] < item["quantidade"]:
            raise ValidationError(f"Estoque insuficiente para {produto['nome']}")
        preco = produto["preco"]
        total += preco * item["quantidade"]
        itens_validados.append({
            "produto_id": item["produto_id"],
            "quantidade": item["quantidade"],
            "preco_unitario": preco,
        })

    # Execute inside transaction
    try:
        pedido_id = pedido_model.criar(usuario_id, total)
        for iv in itens_validados:
            pedido_model.inserir_item(pedido_id, iv["produto_id"], iv["quantidade"], iv["preco_unitario"])
            pedido_model.baixar_estoque(iv["produto_id"], iv["quantidade"])
        db.commit()
    except Exception:
        db.rollback()
        raise

    logger.info("Pedido %d criado para usuario %d, total=%.2f", pedido_id, usuario_id, total)
    return {"pedido_id": pedido_id, "total": total}
