"""
db.py — Configuração do banco de dados.

Responsabilidades:
- Criar o engine (conexão com o SQLite)
- Criar a fábrica de sessions
- Garantir que chaves estrangeiras estejam ativas
- Fornecer a Base para os modelos herdarem
"""

# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine, event
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# --- Engine ------------------------------------------------------------------
# "sqlite:///estoque.db" = arquivo local chamado estoque.db, na pasta do projeto.
# echo=False silencia os logs de SQL. Mude para True se quiser ver cada SQL gerado.
engine = create_engine("sqlite:///estoque.db", echo=False)


# --- PRAGMA foreign_keys = ON ------------------------------------------------
# O SQLite NÃO aplica chaves estrangeiras por padrão.
# Este evento roda automaticamente toda vez que o engine abre uma nova conexão.
@event.listens_for(engine, "connect")
def _ativar_fk(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# --- Base declarativa --------------------------------------------------------
# Todos os modelos (Item, Movimentacao) vão herdar desta classe.
# É ela que "ensina" o SQLAlchemy a mapear classes Python ↔ tabelas SQL.
class Base(DeclarativeBase):
    pass


# --- Session factory ---------------------------------------------------------
# sessionmaker cria uma "fábrica". Cada vez que chamamos Session(), ganhamos
# uma sessão nova e limpa para conversar com o banco.
Session = sessionmaker(bind=engine)


# --- Criação das tabelas -----------------------------------------------------
def criar_tabelas():
    """Cria todas as tabelas que herdam de Base, caso ainda não existam."""
    Base.metadata.create_all(engine)


# --- Execução direta (para testar) ------------------------------------------
if __name__ == "__main__":
    criar_tabelas()
    print("[OK] Banco criado com sucesso! Arquivo: estoque.db")

    # Verifica se o PRAGMA está ativo
    with engine.connect() as conn:
        resultado = conn.exec_driver_sql("PRAGMA foreign_keys")
        valor = resultado.scalar()
        print(f"[OK] foreign_keys = {valor} (1 = ativo, 0 = desativado)")
