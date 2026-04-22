from config.database import get_db


def criar(usuario_id, total):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
        (usuario_id, total),
    )
    return cursor.lastrowid


def inserir_item(pedido_id, produto_id, quantidade, preco_unitario):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
        (pedido_id, produto_id, quantidade, preco_unitario),
    )


def baixar_estoque(produto_id, quantidade):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
        (quantidade, produto_id),
    )


def get_produto_para_pedido(produto_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, nome, preco, estoque FROM produtos WHERE id = ?", (produto_id,))
    return cursor.fetchone()


def get_por_usuario(usuario_id, limit=20, offset=0):
    return _get_pedidos_com_itens(
        "WHERE p.usuario_id = ?", [usuario_id], limit, offset
    )


def get_todos(limit=20, offset=0):
    return _get_pedidos_com_itens("", [], limit, offset)


def atualizar_status(pedido_id, novo_status):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE pedidos SET status = ? WHERE id = ?",
        (novo_status, pedido_id),
    )
    db.commit()


def get_estatisticas():
    """Return aggregate stats for the sales report."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM pedidos")
    total_pedidos = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(total), 0) FROM pedidos")
    faturamento = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'pendente'")
    pendentes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'aprovado'")
    aprovados = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'cancelado'")
    cancelados = cursor.fetchone()[0]

    return {
        "total_pedidos": total_pedidos,
        "faturamento": faturamento,
        "pendentes": pendentes,
        "aprovados": aprovados,
        "cancelados": cancelados,
    }


def _get_pedidos_com_itens(where_clause, params, limit, offset):
    """Fetch orders with items using JOINs instead of N+1 queries."""
    db = get_db()
    cursor = db.cursor()

    query = f"""
        SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
               ip.produto_id, ip.quantidade, ip.preco_unitario,
               pr.nome AS produto_nome
        FROM pedidos p
        LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
        LEFT JOIN produtos pr ON pr.id = ip.produto_id
        {where_clause}
        ORDER BY p.id DESC
        LIMIT ? OFFSET ?
    """
    params_full = params + [limit, offset]
    cursor.execute(query, params_full)
    rows = cursor.fetchall()

    pedidos = {}
    for row in rows:
        pid = row["id"]
        if pid not in pedidos:
            pedidos[pid] = {
                "id": pid,
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": row["total"],
                "criado_em": row["criado_em"],
                "itens": [],
            }
        if row["produto_id"] is not None:
            pedidos[pid]["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"] or "Desconhecido",
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"],
            })

    return list(pedidos.values())
