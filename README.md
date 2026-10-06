# 📦 Sistema de Controle de Estoque para Restaurante

Sistema local em Python para controle rigoroso de estoque, projetado com arquitetura limpa em camadas para possibilitar a reutilização total da lógica de negócios em futuras interfaces (ex.: API FastAPI para tablet de autoatendimento).

---

## 🛠️ Stack Tecnológica
- **Python 3**
- **SQLAlchemy 2.x (ORM)**
- **SQLite**
- Interface interativa via Terminal

---

## 📐 Decisões de Design e Engenharia

1. **Sem coluna de saldo**: O saldo é **sempre calculado** sob demanda com SQL condicional (`SUM(CASE WHEN tipo='ENTRADA' THEN qtd ELSE -qtd END)`). Elimina risco de inconsistência e dessincronização.
2. **Menor unidade de medida**: Quantidades em números inteiros na menor unidade (`g`, `ml`, `un`). Dinheiro em centavos.
3. **Quantidades estritamente positivas**: O `tipo` (`ENTRADA` / `SAIDA`) define o sinal matemático.
4. **Compatibilidade estrita de Tipo e Motivo**:
   - `ENTRADA` aceita apenas `COMPRA`.
   - `SAIDA` aceita apenas `USO`, `PERDA` ou `VENCIMENTO`.
5. **Imutabilidade das movimentações**: Transações de estoque nunca são editadas ou deletadas. Erros são corrigidos com novos lançamentos.
6. **Soft Delete**: Itens nunca são excluídos do banco, apenas marcados como inativos (`ativo = False`), preservando a rastreabilidade do histórico.
7. **Regras de Edição de Itens**:
   - Itens inativos não podem ser editados (devem ser reativados primeiro).
   - A unidade de medida só pode ser alterada se o item ainda **não possuir** nenhuma movimentação registrada.
8. **Alerta de Estoque Mínimo Otimizado**: Consulta agregada única no banco com `LEFT JOIN` e cláusula `HAVING saldo < estoque_minimo`, evitando problemas de performance N+1.
9. **Validação antes da persistência**: Todas as regras de negócio residem exclusivamente em `services.py`. Se qualquer validação falhar, nada entra no banco.
10. **Foreign Keys ativas no SQLite**: Hook com `PRAGMA foreign_keys = ON` na abertura de cada conexão via SQLAlchemy event listener.
11. **Fábrica de Sessões Desacoplada**: Utilização de `SessionLocal = sessionmaker(bind=engine)` para conexões curtas e sem conflito de tipagem.

---

## 📁 Estrutura de Arquivos

```
estoque-restaurante/
├── main.py          # Inicialização e ponto de entrada da aplicação
├── db.py            # Engine, SessionLocal e ativação de FKs do SQLite
├── models.py        # Modelos ORM (Item, Movimentacao, Enums)
├── services.py      # Lógica de negócio pura (saldo, validações, consultas agregadas)
├── terminal.py      # Interface do usuário via terminal (menus e parsing)
├── erros.py         # Exceções customizadas de domínio (herdeiras de EstoqueError)
├── requirements.txt # Dependências do projeto
├── .gitignore       # Arquivos ignorados pelo controle de versão
└── estoque.db       # Banco de dados local SQLite (gerado na execução)
```

---

## 🚀 Como Executar

No terminal dentro da pasta do projeto:

```bash
# 1. Instalar dependências (caso ainda não tenha feito)
py -m pip install -r requirements.txt

# 2. Executar o sistema
py main.py
```
