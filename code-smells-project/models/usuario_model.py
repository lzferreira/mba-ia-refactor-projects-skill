import bcrypt
from config.database import get_db


def _row_to_public(row):
    """Serialize user WITHOUT sensitive fields."""
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def get_todos(limit=20, offset=0):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios LIMIT ? OFFSET ?", (limit, offset))
    return [_row_to_public(r) for r in cursor.fetchall()]


def get_por_id(usuario_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
    row = cursor.fetchone()
    return _row_to_public(row) if row else None


def criar(nome, email, senha):
    db = get_db()
    cursor = db.cursor()
    hashed = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
    cursor.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, hashed, "cliente"),
    )
    db.commit()
    return cursor.lastrowid


def verificar_login(email, senha):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
    row = cursor.fetchone()
    if row and bcrypt.checkpw(senha.encode(), row["senha"].encode()):
        return _row_to_public(row)
    return None
