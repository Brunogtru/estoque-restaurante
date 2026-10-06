# 📦 Sistema de Controle de Estoque para Restaurante

Sistema local em Python para controle rigoroso de estoque, projetado com **arquitetura limpa em camadas**. A interface ativa é uma **API RESTful em FastAPI**, preparada para ser consumida por aplicações frontend (ex.: tablets de autoatendimento, dashboards web ou mobile).

---

## 🛠️ Stack Tecnológica
- **Linguagem:** Python 3.10+
- **ORM / Banco de Dados:** SQLAlchemy 2.x + SQLite
- **API Web:** FastAPI + Pydantic v2
- **Servidor ASGI:** Uvicorn
- **Interface ativa:** Web API (FastAPI / Swagger)

---

## 📐 Decisões de Design e Engenharia

1. **Sem coluna de saldo**: O saldo é **sempre calculado** sob demanda no banco via SQL condicional (`SUM(CASE WHEN tipo='ENTRADA' THEN qtd ELSE -qtd END)`). Elimina riscos de dessincronização e concorrência suja.
2. **Menor unidade de medida**: Quantidades em números inteiros na menor unidade (`g`, `ml`, `un`). Dinheiro em centavos.
3. **Quantidades estritamente positivas**: O `tipo` (`ENTRADA` / `SAIDA`) define o sinal matemático.
4. **Compatibilidade estrita de Tipo e Motivo**:
   - `ENTRADA` aceita exclusivamente `COMPRA`.
   - `SAIDA` aceita exclusivamente `USO`, `PERDA` ou `VENCIMENTO`.
5. **Imutabilidade das movimentações**: Registros de estoque nunca são editados ou apagados, servindo de trilha de auditoria contábil.
6. **Soft Delete**: Itens nunca são excluídos fisicamente do banco; são marcados com `ativo = False`, mantendo a integridade referencial do histórico.
7. **Regras de Edição de Itens**:
   - Itens inativos não podem ser editados (devem ser reativados primeiro).
   - A unidade de medida só pode ser alterada se o item ainda **não possuir** nenhuma movimentação registrada.
8. **Alerta de Estoque Mínimo Otimizado**: Consulta agregada única no banco com `LEFT JOIN` e cláusula `HAVING saldo < estoque_minimo`, evitando o clássico problema de performance N+1 queries.
9. **Desacoplamento em Camadas**:
   - `models.py`: Apenas o schema do banco (ORM).
   - `services.py`: **100% da lógica de negócio e validações**. Não usa `print`, `input` nem detalhes de HTTP.
   - `api/schemas.py`: Contratos Pydantic de entrada e saída (DTOs), prevenindo ataques de Mass Assignment.
   - `api/rotas/`: Apenas traduzem requisições HTTP, chamam o `services.py` e devolvem JSON.
   - `api/app.py`: Tratador de erros central que converte exceções de domínio em status HTTP semânticos (404, 409, 422).
10. **Foreign Keys ativas no SQLite**: Hook via SQLAlchemy event listener executando `PRAGMA foreign_keys = ON` em cada conexão.

---

## 📁 Estrutura de Arquivos

```
estoque-restaurante/
├── api/
│   ├── __init__.py          # Pacote da API
│   ├── app.py               # Instância FastAPI, lifespan e exception handler central
│   ├── dependencias.py      # Injeção de dependência get_db (SessionLocal por request)
│   ├── schemas.py           # Modelos Pydantic de entrada e saída (DTOs)
│   └── rotas/
│       ├── __init__.py      # Pacote de rotas
│       ├── itens.py         # Endpoints de /itens (CRUD, alerta e extrato)
│       ├── movimentacoes.py # Endpoints de /movimentacoes (registro de entrada/saída)
│       └── usuarios.py      # Endpoints de /usuarios (abertos provisoriamente)
├── db.py                    # Engine, SessionLocal e ativação de FKs do SQLite
├── models.py                # Modelos ORM (Item, Movimentacao, Enums)
├── services.py              # Lógica de negócio pura (saldo, validações, consultas)
├── legacy/
│   └── terminal.py          # CLI arquivada, não mantida nem usada pelo fluxo principal
├── erros.py                 # Exceções customizadas de domínio (herdeiras de EstoqueError)
├── main.py                  # Ponto de entrada da API
├── requirements.txt         # Dependências do projeto
├── .gitignore               # Arquivos ignorados pelo Git (banco local, caches, etc.)
└── estoque.db               # Banco de dados local SQLite (gerado na execução)
```

---

## 🚀 Como Executar

### 1. Instalar as dependências
```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. Executar a API Web (FastAPI)
```powershell
.venv\Scripts\python.exe main.py
```
Ou diretamente com o `uvicorn`:
```powershell
.venv\Scripts\python.exe -m uvicorn api.app:app --reload
```

Acesse a **documentação interativa automática (Swagger UI)** no navegador:
👉 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

> **Terminal arquivado:** `legacy/terminal.py` é mantido apenas como referência histórica. Não faz parte do fluxo principal e não é mais mantido.

> **Atenção: usuários sem autenticação.** As rotas `/usuarios` estão abertas provisoriamente porque o login ainda não foi implementado. Elas serão protegidas na Etapa 3; até lá, não exponha a API a redes ou usuários não confiáveis.

---

## 📡 Endpoints da API REST

### Itens (`/itens`)
| Método | Rota | Descrição | Status Sucesso |
|---|---|---|---|
| `GET` | `/itens` | Lista todos os itens e seus saldos calculados (`?apenas_ativos=true/false`) | `200 OK` |
| `POST` | `/itens` | Cadastra um novo item no estoque | `201 Created` |
| `GET` | `/itens/abaixo-do-minimo` | Relatório de itens com saldo abaixo do estoque mínimo | `200 OK` |
| `GET` | `/itens/{id}` | Busca um item específico por ID com seu saldo | `200 OK` |
| `PUT` | `/itens/{id}` | Edita dados de um item (nome, unidade, estoque mínimo) | `200 OK` |
| `PATCH` | `/itens/{id}/desativar` | Desativa um item (soft delete) | `200 OK` |
| `PATCH` | `/itens/{id}/reativar` | Reativa um item desativado | `200 OK` |
| `GET` | `/itens/{id}/saldo` | Consulta apenas o valor numérico do saldo do item | `200 OK` |
| `GET` | `/itens/{id}/extrato` | Histórico cronológico completo de movimentações do item | `200 OK` |

### Movimentações (`/movimentacoes`)
| Método | Rota | Descrição | Status Sucesso |
|---|---|---|---|
| `POST` | `/movimentacoes` | Registra entrada ou saída validando saldo e compatibilidade | `201 Created` |

### Usuários (`/usuarios`)

Estas rotas estão abertas **provisoriamente** até a implementação de login e permissões na Etapa 3.

| Método | Rota | Descrição | Status Sucesso |
|---|---|---|---|
| `POST` | `/usuarios` | Cadastra usuário; a resposta não inclui `senha_hash` | `201 Created` |
| `GET` | `/usuarios` | Lista usuários (`?apenas_ativos=false` inclui inativos) | `200 OK` |
| `GET` | `/usuarios/{usuario_id}` | Busca usuário por ID | `200 OK` |
| `PATCH` | `/usuarios/{usuario_id}/papel` | Altera papel | `200 OK` |
| `PATCH` | `/usuarios/{usuario_id}/desativar` | Desativa usuário | `200 OK` |
| `PATCH` | `/usuarios/{usuario_id}/reativar` | Reativa usuário | `200 OK` |

---

## 🛑 Tratamento de Erros Semântico (HTTP)

As exceções de domínio disparadas pelo `services.py` são interceptadas e convertidas em respostas JSON padronizadas com o status HTTP correto:

| Exceção | Status HTTP | Significado |
|---|---|---|
| `ItemNaoEncontradoError` | **404 Not Found** | O ID informado não existe. |
| `NomeInvalidoError`<br>`UnidadeInvalidaError`<br>`EstoqueMinimoInvalidoError`<br>`QuantidadeInvalidaError` | **422 Unprocessable Content** | Violação de formato ou tipo de dado. |
| `EstoqueInsuficienteError`<br>`ItemInativoError`<br>`MotivoIncompativelError`<br>`AlteracaoUnidadeProibidaError` | **409 Conflict** | Violação do estado atual ou de regra de negócio do estoque. |

**Exemplo de resposta de erro:**
```json
{
  "erro": "EstoqueInsuficienteError",
  "mensagem": "Saldo insuficiente para 'Farinha de Trigo'. Disponivel: 3000g, solicitado: 5000g."
}
```

**Mapeamento provisório:** o mapeamento HTTP específico das novas exceções de usuário será feito na Parte F. Até lá, exceções de domínio ainda não registradas no tratador central recebem o status genérico `400 Bad Request`; erros de validação estrutural dos schemas Pydantic continuam sendo tratados pelo FastAPI como `422 Unprocessable Entity`.
