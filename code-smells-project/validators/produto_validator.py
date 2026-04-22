from middlewares.errors import ValidationError

CATEGORIAS_VALIDAS = ("informatica", "moveis", "vestuario", "geral", "eletronicos", "livros")


def validar_produto(dados):
    """Validate product payload. Raises ValidationError on failure."""
    if not dados:
        raise ValidationError("Dados inválidos")

    erros = []

    nome = dados.get("nome")
    if not nome:
        erros.append("Nome é obrigatório")
    elif len(nome) < 2:
        erros.append("Nome muito curto")
    elif len(nome) > 200:
        erros.append("Nome muito longo")

    preco = dados.get("preco")
    if preco is None:
        erros.append("Preço é obrigatório")
    elif preco < 0:
        erros.append("Preço não pode ser negativo")

    estoque = dados.get("estoque")
    if estoque is None:
        erros.append("Estoque é obrigatório")
    elif estoque < 0:
        erros.append("Estoque não pode ser negativo")

    categoria = dados.get("categoria", "geral")
    if categoria not in CATEGORIAS_VALIDAS:
        erros.append(f"Categoria inválida. Válidas: {list(CATEGORIAS_VALIDAS)}")

    if erros:
        raise ValidationError(", ".join(erros))
