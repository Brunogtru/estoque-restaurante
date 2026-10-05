# 📦 Sistema de Controle de Estoque para Restaurante

Sistema local em Python para controle rigoroso de estoque, projetado com arquitetura em camadas para possibilitar a reutilização da lógica de negócios em futuras interfaces (ex.: FastAPI para tablet de autoatendimento).

---

## 🛠️ Stack Tecnológica
- **Python 3**
- **SQLAlchemy (ORM)**
- **SQLite**
- Interface interativa via Terminal

---

## 📐 Decisões de Design e Engenharia

1. **Sem coluna de saldo atual**: O saldo é **sempre calculado** sob demanda (`SUM(entradas) - SUM(saídas)`). Elimina risco de inconsistência e dessincronização.
2. **Menor unidade de medida**: Quantidades em números inteiros na menor unidade (`g`, `ml`, `un`).
3. **Quantidades estritamente positivas**: O `tipo` (`ENTRADA` / `SAIDA`) define o sinal matemático.
4. **Imutabilidade das movimentações**: Transações de estoque nunca são editadas ou deletadas. Erros são corrigidos com novos lançamentos.
5. **Soft Delete**: Itens nunca são excluídos do banco, apenas marcados como inativos (`ativo = False`), preservando o histórico de movimentações.
6. **Validação antes da persistência**: Se qualquer regra de negócio falhar, nenhuma alteração entra no banco de dados.
7. **Foreign Keys ativas no SQLite**: Hook com `PRAGMA foreign_keys = ON` na abertura de cada conexão.

---

## 📁 Estrutura de Arquivos

```
Estoque_laparme/
├── main.py          # Inicialização e ponto de entrada
├── db.py            # Engine, sessionmaker e ativação de FKs
├── models.py        # Modelos ORM (Item, Movimentacao, Enums)
├── services.py      # Lógica de negócio pura (saldo, validações, transações)
├── terminal.py      # Interface do usuário via terminal
├── erros.py         # Exceções customizadas de domínio
└── estoque.db       # Banco SQLite local
```

---

## 🚀 Como Executar

No terminal dentro da pasta do projeto:

```bash
# Rodar o sistema
py main.py
```
