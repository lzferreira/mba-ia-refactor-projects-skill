from models import pedido_model

# Discount tiers: (min_revenue, discount_rate)
DISCOUNT_TIERS = [
    (10000, 0.10),
    (5000, 0.05),
    (1000, 0.02),
]


def calcular_desconto(faturamento):
    for limite, taxa in DISCOUNT_TIERS:
        if faturamento > limite:
            return round(faturamento * taxa, 2)
    return 0


def gerar_relatorio():
    stats = pedido_model.get_estatisticas()
    faturamento = stats["faturamento"]
    desconto = calcular_desconto(faturamento)

    total_pedidos = stats["total_pedidos"]
    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": desconto,
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": stats["pendentes"],
        "pedidos_aprovados": stats["aprovados"],
        "pedidos_cancelados": stats["cancelados"],
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }
