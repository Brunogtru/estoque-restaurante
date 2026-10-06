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
6. **Soft Delete**: Itens e usuários nunca são excluídos fisicamente; são marcados com `ativo = False`, mantendo a integridade referencial do histórico.
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
11. **Usuários e auditoria**: Usuários têm `id`, `nome`, `login` único, `senha_hash`, `papel`, `ativo` e `criado_em`. Senhas são armazenadas com Argon2, nunca em texto puro. Cada movimentação referencia obrigatoriamente o usuário responsável; o extrato retorna seu nome.

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
├── models.py                # Modelos ORM (Item, Usuario, Movimentacao e Enums)
├── services.py              # Regras de negócio, validações, usuários e consultas de saldo
├── legacy/
│   └── terminal.py          # CLI arquivada, não mantida nem usada pelo fluxo principal
├── scripts/
│   ├── __init__.py           # Pacote de scripts operacionais
│   └── criar_admin.py        # Cria o primeiro administrador com senha oculta
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

### Criar o primeiro administrador

Na raiz do projeto, execute pelo ambiente virtual:

```powershell
.venv\Scripts\python.exe -m scripts.criar_admin
```

O módulo é executado a partir da raiz, permitindo ao Python importar `db.py`, `models.py` e `services.py`. O script cria as tabelas antes do cadastro, oculta a senha e pede confirmação. Ele recusa continuar se já houver um administrador ativo; para cadastrar outros usuários, use `POST /usuarios` em `/docs` (rota aberta provisoriamente até a Etapa 3).

> **Atenção: API sem autenticação nesta etapa.** As rotas `/usuarios` estão abertas provisoriamente; ainda não há login nem permissões nas rotas da API. A proteção será implementada na Etapa 3. Use apenas localmente e não exponha a API a redes ou usuários não confiáveis.

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
| `POST` | `/movimentacoes` | Registra entrada ou saída; resposta inclui o nome de quem lançou | `201 Created` |

> **Campo provisório:** o corpo de `POST /movimentacoes` recebe `usuario_id` nesta etapa. Na Etapa 3, esse campo sairá do schema e o ID virá do usuário autenticado.

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

### Roteiro de verificação manual da Etapa 2

Faça esta verificação localmente pelo Swagger em `/docs`. As rotas estão sem autenticação nesta etapa. Em todas as respostas de usuário, confirme que `senha_hash` não aparece.

1. **Criar o primeiro administrador:** na raiz do projeto, rode `& "$PWD\.venv\Scripts\python.exe" -m scripts.criar_admin` no PowerShell. Informe nome e login; digite a senha duas vezes nos prompts ocultos. O script cria as tabelas se necessário e informa o ID criado.
2. **Subir a API:** rode `& "$PWD\.venv\Scripts\python.exe" main.py` e abra `http://127.0.0.1:8000/docs`.
3. **Criar usuários dos três papéis:** o administrador inicial já cobre `ADMINISTRADOR`. Use `POST /usuarios` para criar um `ESTOQUISTA`, um `COZINHA` e um segundo `ADMINISTRADOR` (necessário para a etapa de teste do último administrador). Cada cadastro válido retorna **201**. Anote os IDs. Os corpos seguem este formato:

    ```json
    {
       "nome": "Bruno Estoquista",
       "login": "estoquista",
       "senha": "senha-segura-123",
       "papel": "ESTOQUISTA"
    }
    ```

    Para os outros dois, altere `nome`, `login` e `papel` para `COZINHA` e `ADMINISTRADOR`.
4. **Login duplicado:** repita `POST /usuarios` com login já cadastrado, inclusive variando maiúsculas ou espaços externos. Esperado: **409 Conflict**, `erro: "LoginDuplicadoError"`.
5. **Senha curta:** envie `POST /usuarios` com uma senha como `"abc"`. Esperado: **422 Unprocessable Entity**, rejeitada pelo schema Pydantic antes de chegar ao serviço.
6. **Usuário inexistente:** chame `GET /usuarios/999999` (use um ID que não exista). Esperado: **404 Not Found**, `erro: "UsuarioNaoEncontradoError"`.
7. **Criar item para movimentar:** use `POST /itens` com `{"nome":"Arroz de teste","unidade":"g","estoque_minimo":0}`. Esperado: **201**; anote o `id` retornado.
8. **Movimentação válida:** use `POST /movimentacoes` com o ID do item, o ID de um usuário ativo e `tipo: "ENTRADA"`, `quantidade: 1000`, `motivo: "COMPRA"`. Esperado: **201** e resposta com `usuario_nome` igual ao nome do responsável.
9. **Movimentação com usuário inexistente:** repita a entrada com `usuario_id: 999999`. Esperado: **404 Not Found**, `UsuarioNaoEncontradoError`; nenhuma movimentação deve ser gravada.
10. **Movimentação com usuário inativo:** chame `PATCH /usuarios/{id_cozinha}/desativar` (esperado **200**) e tente registrar uma entrada com esse `usuario_id`. Esperado: **409 Conflict**, `UsuarioInativoError`; nenhuma movimentação deve ser gravada.
11. **Extrato com responsável:** chame `GET /itens/{id_item}/extrato`. Esperado: **200**; cada movimentação inclui `usuario_nome` e não contém `senha_hash`.
12. **Último administrador:** há dois administradores ativos: o inicial e o segundo criado no passo 3. Desative o segundo com `PATCH /usuarios/{id_admin_2}/desativar`; esperado: **200**. Depois tente desativar o administrador inicial com `PATCH /usuarios/{id_admin_inicial}/desativar`; esperado: **409 Conflict**, `UltimoAdministradorError`. O primeiro deve continuar ativo.

`usuario_id` no corpo de `POST /movimentacoes` é provisório e fornecido pelo cliente apenas para esta etapa. Na Etapa 3, o campo será removido e o responsável virá da sessão autenticada. O teste de senha curta retorna o formato de validação padrão do FastAPI; erros de domínio usam o formato `{ "erro": "...", "mensagem": "..." }`.

---

## 🛑 Tratamento de Erros Semântico (HTTP)

As exceções de domínio disparadas pelo `services.py` são interceptadas e convertidas em respostas JSON padronizadas com o status HTTP correto:

| Exceção | Status HTTP | Significado |
|---|---|---|
| `ItemNaoEncontradoError`<br>`UsuarioNaoEncontradoError` | **404 Not Found** | O item ou usuário informado não existe. |
| `NomeInvalidoError`<br>`UnidadeInvalidaError`<br>`EstoqueMinimoInvalidoError`<br>`QuantidadeInvalidaError`<br>`SenhaInvalidaError` | **422 Unprocessable Content** | Violação dos requisitos de formato ou dos dados aceitos pelo domínio. |
| `EstoqueInsuficienteError`<br>`ItemInativoError`<br>`MotivoIncompativelError`<br>`AlteracaoUnidadeProibidaError`<br>`LoginDuplicadoError`<br>`UsuarioInativoError`<br>`UltimoAdministradorError` | **409 Conflict** | Conflito com o estado atual, login duplicado ou proteção do último administrador. |

**Exemplo de resposta de erro:**
```json
{
  "erro": "EstoqueInsuficienteError",
  "mensagem": "Saldo insuficiente para 'Farinha de Trigo'. Disponivel: 3000g, solicitado: 5000g."
}
```

Erros de validação estrutural dos schemas Pydantic também são tratados pelo FastAPI como `422 Unprocessable Entity`. O tratador central mantém a mensagem original da exceção no campo `mensagem` da resposta.
