# 📦 Sistema de Controle de Estoque para Restaurante

Sistema local em Python para controle rigoroso de estoque, projetado com **arquitetura limpa em camadas**. A interface ativa é uma **API RESTful em FastAPI**, preparada para ser consumida por aplicações frontend (ex.: tablets de autoatendimento, dashboards web ou mobile).

---

## 🛠️ Stack Tecnológica
- **Linguagem:** Python 3.10+
- **ORM / Banco de Dados:** SQLAlchemy 2.x + SQLite
- **API Web:** FastAPI + Pydantic v2
- **Servidor ASGI:** Uvicorn
- **Interface ativa:** Web API (FastAPI / Swagger)
- **Autenticação:** cookie HttpOnly assinado e sessão persistida no SQLite

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
   - `api/app.py`: Middleware de Origin e tratador central de erros HTTP (401, 403, 404, 409, 422).
10. **Foreign Keys ativas no SQLite**: Hook via SQLAlchemy event listener executando `PRAGMA foreign_keys = ON` em cada conexão.
11. **Usuários e auditoria**: Usuários têm `id`, `nome`, `login` único, `senha_hash`, `papel`, `ativo` e `criado_em`. Senhas são armazenadas com Argon2, nunca em texto puro. Cada movimentação referencia obrigatoriamente o usuário responsável; o extrato retorna seu nome.

---

## 📁 Estrutura de Arquivos

```
estoque-restaurante/
├── api/
│   ├── __init__.py          # Pacote da API
│   ├── app.py               # Instância FastAPI, lifespan e exception handler central
│   ├── dependencias.py      # Injeção de get_db e get_current_user
│   ├── schemas.py           # Modelos Pydantic de entrada e saída (DTOs)
│   └── rotas/
│       ├── __init__.py      # Pacote de rotas
│       ├── auth.py          # Login, logout e usuário autenticado
│       ├── itens.py         # Endpoints de /itens (CRUD, alerta e extrato)
│       ├── movimentacoes.py # Endpoints de /movimentacoes (registro de entrada/saída)
│       └── usuarios.py      # Endpoints administrativos de /usuarios
├── db.py                    # Engine, SessionLocal e ativação de FKs do SQLite
├── config.py                # Leitura e validação das variáveis de ambiente
├── models.py                # Modelos ORM (Item, Usuario, Movimentacao, Sessao e Enums)
├── services.py              # Regras, validações, autenticação e permissões
├── legacy/
│   └── terminal.py          # CLI arquivada, não mantida nem usada pelo fluxo principal
├── scripts/
│   ├── __init__.py           # Pacote de scripts operacionais
│   └── criar_admin.py        # Cria o primeiro administrador com senha oculta
├── erros.py                 # Exceções customizadas de domínio (herdeiras de EstoqueError)
├── main.py                  # Ponto de entrada da API
├── requirements.txt         # Dependências do projeto
├── .gitignore               # Arquivos ignorados pelo Git (banco local, caches, etc.)
├── .env.example              # Modelo das configurações locais, sem segredos
└── estoque.db               # Banco de dados local SQLite (gerado na execução)
```

---

## 🚀 Como Executar

### 1. Instalar as dependências
```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. Configurar o ambiente local

Copie o exemplo para `.env`:

```powershell
Copy-Item .env.example .env
```

Gere uma chave aleatória forte:

```powershell
.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

Coloque a chave gerada em `SECRET_KEY` no `.env`. O arquivo `.env` é local e ignorado pelo Git; nunca o adicione ao repositório. A aplicação recusa iniciar se a chave estiver ausente, for o valor de exemplo ou tiver menos de 32 caracteres.

Configuração local esperada:

```dotenv
SECRET_KEY=<chave aleatoria gerada localmente>
SESSION_TTL_MINUTES=480
COOKIE_SECURE=false
```

`SESSION_TTL_MINUTES` é inteiro positivo; `480` corresponde a oito horas fixas, sem renovação por atividade. `COOKIE_SECURE` aceita somente `true` ou `false`; use `true` em produção com HTTPS.

### 3. Executar a API Web (FastAPI)
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

O módulo é executado a partir da raiz, oculta a senha e pede confirmação. O serviço recusa criar o administrador inicial se já houver um administrador ativo. O script não depende da `SECRET_KEY`. Depois do bootstrap, entre como administrador para cadastrar outros usuários em `/docs`.

Todas as rotas de estoque exigem login. Operações administrativas de usuários também exigem papel ADMINISTRADOR.

---

## 🔐 Autenticação e Sessões

O login cria uma sessão no banco e envia um cookie `session` assinado. O cookie contém um identificador aleatório; o banco armazena somente o SHA-256 desse identificador. Em cada requisição autenticada, a API valida a assinatura, procura a sessão, confere expiração/revogação e verifica no banco se o usuário ainda está ativo.

O cookie usa `HttpOnly`, `SameSite=Lax`, `Path=/` e expiração fixa configurada por `SESSION_TTL_MINUTES`. Ao desativar um usuário, suas sessões são revogadas. O logout é idempotente e remove o cookie do navegador.

| Método | Rota | Descrição | Status |
|---|---|---|---|
| `POST` | `/auth/login` | Valida credenciais e cria sessão | `200` |
| `POST` | `/auth/logout` | Revoga a sessão atual quando possível e apaga o cookie | `200` |
| `GET` | `/auth/me` | Retorna o usuário da sessão autenticada | `200` |

No Swagger em `/docs`, execute `POST /auth/login` com login e senha. O navegador guarda o cookie HttpOnly e o envia automaticamente nas chamadas seguintes feitas na mesma origem; não há botão **Authorize** para esse mecanismo. Confirme a sessão com `GET /auth/me`. Para sair, use `POST /auth/logout`; `/auth/me` deve então responder `401`.

No início de cada login, sessões expiradas são removidas; a sessão nova recebe o TTL integral e não é renovada por atividade.

O middleware valida `Origin` em todas as requisições `POST`, `PUT`, `PATCH` e `DELETE`. Origin ausente, `null` ou de outra origem recebe `403`. Clientes que não são navegadores, como `curl` e scripts, precisam enviar `Origin: http://127.0.0.1:8000` no desenvolvimento local.

## 👥 Permissões

| Ação | ADMINISTRADOR | ESTOQUISTA | COZINHA |
|---|---:|---:|---:|
| Consultar itens, saldos, extratos e alertas | Sim | Sim | Sim |
| Registrar ENTRADA / COMPRA | Sim | Sim | Não |
| Registrar SAIDA / USO | Sim | Sim | Sim |
| Registrar SAIDA / PERDA ou VENCIMENTO | Sim | Sim | Não |
| Cadastrar e editar item | Sim | Sim | Não |
| Desativar e reativar item | Sim | Não | Não |
| Gerenciar usuários | Sim | Não | Não |

As permissões são verificadas em `services.py`, antes de buscar o recurso ou validar as demais regras de negócio. A resposta de permissão negada é `403` com `{"erro":"PermissaoNegadaError","mensagem":"Voce nao tem permissao para esta acao."}`.

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
| `POST` | `/movimentacoes` | Registra entrada ou saída em nome do usuário autenticado | `201 Created` |

### Usuários (`/usuarios`)

Todas estas rotas exigem login e o papel ADMINISTRADOR.

| Método | Rota | Descrição | Status Sucesso |
|---|---|---|---|
| `POST` | `/usuarios` | Cadastra usuário; a resposta não inclui `senha_hash` | `201 Created` |
| `GET` | `/usuarios` | Lista usuários (`?apenas_ativos=false` inclui inativos) | `200 OK` |
| `GET` | `/usuarios/{usuario_id}` | Busca usuário por ID | `200 OK` |
| `PATCH` | `/usuarios/{usuario_id}/papel` | Altera papel | `200 OK` |
| `PATCH` | `/usuarios/{usuario_id}/desativar` | Desativa usuário | `200 OK` |
| `PATCH` | `/usuarios/{usuario_id}/reativar` | Reativa usuário | `200 OK` |

O roteiro completo de autenticação e permissões está na seção de verificação manual da Etapa 3 abaixo.

---

## 🛑 Tratamento de Erros Semântico (HTTP)

As exceções de domínio disparadas pelo `services.py` são interceptadas e convertidas em respostas JSON padronizadas com o status HTTP correto:

| Exceção | Status HTTP | Significado |
|---|---|---|
| `CredenciaisInvalidasError` | **401 Unauthorized** | Credencial ausente, inválida, expirada ou usuário inativo. |
| `PermissaoNegadaError` | **403 Forbidden** | Usuário autenticado sem permissão para a ação. |
| `ItemNaoEncontradoError`<br>`UsuarioNaoEncontradoError` | **404 Not Found** | O item ou usuário informado não existe. |
| `NomeInvalidoError`<br>`UnidadeInvalidaError`<br>`EstoqueMinimoInvalidoError`<br>`QuantidadeInvalidaError`<br>`SenhaInvalidaError` | **422 Unprocessable Content** | Violação dos requisitos de formato ou dos dados aceitos pelo domínio. |
| `EstoqueInsuficienteError`<br>`ItemInativoError`<br>`MotivoIncompativelError`<br>`AlteracaoUnidadeProibidaError`<br>`LoginDuplicadoError`<br>`UsuarioInativoError`<br>`UltimoAdministradorError`<br>`AdministradorJaExisteError` | **409 Conflict** | Conflito com o estado atual, login duplicado ou proteção do último administrador. |

**Exemplo de resposta de erro:**
```json
{
  "erro": "EstoqueInsuficienteError",
  "mensagem": "Saldo insuficiente para 'Farinha de Trigo'. Disponivel: 3000g, solicitado: 5000g."
}
```

Erros de validação estrutural dos schemas Pydantic também são tratados pelo FastAPI como `422 Unprocessable Entity`. O tratador central mantém a mensagem original da exceção no campo `mensagem` da resposta.

---

## ✅ Roteiro de Verificação Manual da Etapa 3

Execute localmente pelo Swagger em `http://127.0.0.1:8000/docs`. O navegador deve abrir o Swagger pela mesma origem da API para enviar o cookie de sessão automaticamente. Use dados de teste e garanta saldo suficiente antes dos testes de saída.

1. **Preparar ambiente e administrador:** configure `.env` conforme a seção acima; rode `.venv\Scripts\python.exe -m scripts.criar_admin`, informe nome/login e digite a senha duas vezes nos prompts ocultos. Suba a API e abra `/docs`.
2. **Sem login:** antes de autenticar, chame `GET /itens` e `GET /auth/me`. Esperado: `401` com erro de credenciais. Rotas de escrita chamadas pelo navegador também exigem Origin válido.
3. **Login válido:** `POST /auth/login` com o administrador. Esperado: `200`, resposta sem `senha_hash` e cookie `session` com HttpOnly, SameSite=Lax e Path=/; `GET /auth/me` retorna `200` sem `senha_hash`.
4. **Credenciais inválidas:** faça login com senha errada e com login inexistente. Esperado: ambos `401` e a mesma mensagem genérica `Credenciais invalidas.`.
5. **Criar usuários de teste:** autenticado como administrador, use `POST /usuarios` para criar ESTOQUISTA, COZINHA e um segundo ADMINISTRADOR. Esperado: `201`; nenhuma resposta deve conter `senha_hash`. Anote os IDs.
6. **Acesso inativo:** como administrador, desative um usuário de teste. Esperado: `200`; o cookie/sessão antigo desse usuário deve falhar imediatamente em `GET /auth/me` com `401`. Reative-o para continuar os testes, e ele deve fazer login novamente.
7. **Consultas de estoque:** faça login como cada papel e use `GET /itens`, `GET /itens/{id}`, saldo, extrato e alertas. Esperado: `200` para ADMINISTRADOR, ESTOQUISTA e COZINHA.
8. **Cadastro e edição de item:** como ADMINISTRADOR e ESTOQUISTA, `POST /itens` e `PUT /itens/{id}` devem retornar `201` e `200`. Como COZINHA, ambas devem retornar `403`.
9. **Desativar/reativar item:** ADMINISTRADOR deve obter `200` em ambos os PATCH. ESTOQUISTA e COZINHA devem obter `403`.
10. **Ordem autorização/busca de item:** envie um corpo válido para `PUT /itens/999999`. Como COZINHA, esperado `403`; como ESTOQUISTA, esperado `404`.
11. **Preparar saldo:** como ADMINISTRADOR ou ESTOQUISTA, cadastre um item e registre entrada COMPRA suficiente para os testes seguintes. Esperado `201` em cada operação permitida.
12. **Movimentações de ADMINISTRADOR e ESTOQUISTA:** cada um deve conseguir registrar ENTRADA/COMPRA, SAIDA/USO, SAIDA/PERDA e SAIDA/VENCIMENTO. Esperado `201` para cada par, desde que haja saldo nas saídas.
13. **Movimentações de COZINHA:** SAIDA/USO deve retornar `201`. ENTRADA/COMPRA, SAIDA/PERDA e SAIDA/VENCIMENTO devem retornar `403` com a mensagem genérica de permissão.
14. **Validações de movimentação:** ENTRADA/USO deve retornar `409`; saída acima do saldo deve retornar `409`. Envie `usuario_id` extra no JSON: esperado `422`, pois o schema rejeita campos extras. O extrato do item deve mostrar `usuario_nome` do usuário que está logado, não um ID escolhido pelo cliente.
15. **Gerenciamento de usuários:** ADMINISTRADOR deve criar, listar, buscar, alterar papel, desativar e reativar usuários com status `2xx` quando a regra permitir. ESTOQUISTA e COZINHA devem receber `403` em todas as rotas de usuários. Login duplicado retorna `409`; senha curta retorna `422`.
16. **Cookie adulterado:** altere o valor do cookie `session` nas ferramentas de desenvolvedor do navegador e chame `GET /auth/me`. Esperado: `401`.
17. **Logout:** execute `POST /auth/logout`, depois `GET /auth/me`. Esperado: logout `200`; `/auth/me` `401`. Repetir logout sem cookie também retorna sucesso.
18. **Sessão expirada:** em um ambiente local de teste, configure `SESSION_TTL_MINUTES=1`, reinicie a API, faça login e aguarde mais de um minuto; `/auth/me` deve retornar `401`. Depois restaure `480` no `.env`.
19. **Origin:** faça uma chamada mutável sem cabeçalho Origin, por exemplo com `curl.exe`; esperado `403`. Repita incluindo `Origin: http://127.0.0.1:8000`; a requisição deve passar pelo middleware e retornar o status próprio da operação. O Swagger no mesmo host envia Origin pelo navegador.
20. **Último administrador:** mantenha dois administradores ativos. Desative um deles (`200`) e tente desativar ou rebaixar o último ativo; esperado `409` com `UltimoAdministradorError`. O último deve permanecer ativo.

## Riscos Abertos e Próximos Passos

- **Tentativas de login:** ainda não há limite ou atraso progressivo; considerar proteção contra força bruta numa etapa futura.
- **HTTPS e rede/tablet:** `COOKIE_SECURE=true` e HTTPS são obrigatórios antes de expor o sistema à rede ou usar tablets fora do host local.
- **Senha:** troca e redefinição de senha não estão implementadas.
- **Correções de estoque:** não há tipo AJUSTE; movimentações continuam imutáveis e erros devem ser corrigidos por lançamentos compensatórios aprovados.
- **Banco:** planejar backup e restauração do SQLite; mudanças de esquema futuras exigirão estratégia de migração.
- **Frontend/XSS:** ao implementar a interface, não inserir conteúdo do usuário com `innerHTML`; preferir `textContent` e tratar saída conforme o contexto.
