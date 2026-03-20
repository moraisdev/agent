# Namastex Report Agent

Agente de inteligencia de negocios no WhatsApp. Usa Claude Code como agente nativo via **Genie** (Omni) + **MCP server** custom como backend de dados (vendas, financeiro, clientes) em PostgreSQL.

## Arquitetura

```
                         ┌─────────────┐
                         │  WhatsApp    │
                         └──────┬──────┘
                                │ mensagem
                         ┌──────┴──────┐
                         │    Omni     │  Plataforma omnichannel
                         │  (Baileys)  │  github.com/automagik-dev/omni
                         └──────┬──────┘
                                │ agent-dispatcher → Genie provider
                         ┌──────┴──────┐
                         │ Team Inbox   │  ~/.claude/teams/namastex-{chat_id}/
                         │ (filesystem) │  inboxes/nex.json
                         └──────┬──────┘
                                │ auto-spawn
                         ┌──────┴──────┐
                         │ Claude Code  │  Le o inbox, entende a mensagem
                         │ (agente)     │  Decide se precisa de dados ou nao
                         └──────┬──────┘
                                │ MCP Protocol (tool_use)
                         ┌──────┴──────┐
                         │ MCP Server   │  FastMCP (Python) — porta 8000
                         │ 9 tools      │  Conecta no PostgreSQL
                         │ PostgreSQL   │  Retorna dados reais
                         └──────┬──────┘
                                │ resposta
                         ┌──────┴──────┐
                         │ Claude Code  │  Formata resposta natural
                         │ SendMessage  │  Escreve no inbox do Omni
                         └──────┬──────┘
                                │ inbox-bridge (poll a cada 2s)
                         ┌──────┴──────┐
                         │    Omni     │  Roteia resposta pro chat correto
                         └──────┬──────┘
                                │
                         ┌──────┴──────┐
                         │  WhatsApp    │  Usuario recebe a resposta
                         └─────────────┘
```

## Como os componentes se conectam

O projeto tem 3 partes que trabalham juntas:

### 1. MCP Server (`server/`) — Backend de dados

Servidor MCP custom em Python que expoe 9 tools via protocolo MCP. Nao tem logica de conversacao — so serve dados do PostgreSQL. Roda em Docker na porta 8000.

Quando Claude Code precisa de dados (vendas, clientes, financeiro), ele chama essas tools via MCP protocol. O servidor valida inputs, consulta o banco, formata e retorna.

### 2. Omni (`omni/` — nao commitado, instalar separado)

Plataforma omnichannel open-source que conecta no WhatsApp via Baileys. Funciona como ponte entre WhatsApp e o agente. Nao e commitado no repo — deve ser clonado separadamente (ver Quick Start).

O Omni usa o **Genie provider** para rotear mensagens pro Claude Code. Quando uma mensagem chega no WhatsApp:

1. O `agent-dispatcher` detecta a mensagem
2. O `Genie provider` escreve a mensagem no filesystem (team inbox)
3. O `inbox-bridge` fica fazendo poll a cada 2s pra pegar respostas e enviar de volta pro WhatsApp

### 3. Claude Code (agente) — Cerebro

Claude Code e o agente que processa as mensagens. Ele e configurado por 2 arquivos na raiz do projeto:

| Arquivo | O que faz |
|---------|-----------|
| `.mcp.json` | Diz ao Claude Code onde esta o MCP server (`http://localhost:8000/mcp`). Ele descobre as 9 tools automaticamente via MCP protocol. |
| `.claude/CLAUDE.md` | Instrucoes do agente: quem ele e (Nex), como se comportar (pt-BR, conciso, WhatsApp), quando usar tools vs conversar, como parsear o header de roteamento das mensagens. |

Quando o Genie auto-spawna o Claude Code no diretorio do projeto, ele le esses 2 arquivos e sabe exatamente o que fazer. Nao tem codigo custom pra isso — e configuracao pura do Claude Code.

## Stack

| Componente | Tecnologia | Porta |
|------------|------------|-------|
| MCP Server | Python, FastMCP, SQLAlchemy, asyncpg | 8000 |
| Banco de dados | PostgreSQL 16 (Docker) | 5433 |
| Omni | Node.js, Hono, Baileys, NATS | 8882 |
| Agente | Claude Code (nativo) | — |
| WhatsApp | Via Baileys (Omni) | — |

## Estrutura do Projeto

```
namastex/
├── .claude/CLAUDE.md        ← Instrucoes pro agente Claude Code
├── .mcp.json                ← Conexao MCP: aponta pro server na porta 8000
├── .env                     ← Variaveis do MCP server (banco, auth)
├── .env.example             ← Template
├── docker-compose.yml       ← PostgreSQL + MCP server
├── Makefile                 ← Atalhos (make up, make logs, etc)
├── scripts/
│   ├── seed-demo-data.sql   ← Dados de demo (vendas, clientes, financeiro)
│   └── setup-genie.sh       ← Cria provider Genie + agent + instancia no Omni
├── server/                  ← MCP Server (Python)
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic/             ← Migrations do banco
│   └── src/
│       ├── server.py        ← FastMCP app + middleware + /ping
│       ├── config/          ← Pydantic settings
│       ├── infra/           ← SQLAlchemy async engine
│       ├── models/          ← ORM (business + memory)
│       ├── repositories/    ← Data access (sales, clients, financial, memory)
│       ├── schemas/         ← Dataclasses (pipeline, business, auth)
│       ├── services/
│       │   ├── report_service.py   ← Pipeline: gather → analyze → format
│       │   ├── gatherer.py         ← Busca dados do banco em paralelo
│       │   ├── analyzer.py         ← Detecta anomalias via EMA, compara periodos
│       │   ├── memory_service.py   ← Memoria cross-session + baselines
│       │   └── context_service.py  ← Monta contexto do usuario
│       ├── tools/           ← 9 MCP tools registradas no FastMCP
│       ├── guards/          ← Auth HMAC, circuit breaker, validacao, sanitizacao
│       └── utils/           ← Formatacao BRL + i18n (pt-BR/en-US)
└── omni/                    ← NAO COMMITADO — clonar separadamente
```

## Quick Start

### 1. Configurar

```bash
cp .env.example .env
```

### 2. Subir MCP Server + Banco

```bash
make up
```

Sobe 2 containers:
- `business-db` — PostgreSQL com dados de demo (vendas, clientes, financeiro)
- `mcp-server` — MCP server na porta 8000 (migration automatica no startup)

Verificar: `curl http://localhost:8000/ping`

### 3. Instalar o Omni

O Omni nao e commitado no repo. Clonar separadamente:

```bash
git clone https://github.com/automagik-dev/omni.git
cd omni && bun install
```

Criar o database `omni` no PostgreSQL:
```bash
docker exec namastex-business-db-1 psql -U readonly -d postgres -c "CREATE DATABASE omni OWNER readonly;"
```

Configurar o `.env` do Omni:
```bash
# omni/.env — ajustar:
DATABASE_URL=postgresql://readonly:readonly@localhost:5433/omni
PGSERVE_EMBEDDED=false
ANTHROPIC_API_KEY=sk-ant-api03-...  # sua key da Anthropic
```

Subir:
```bash
cd omni
set -a && source .env && set +a && npx pm2 start ecosystem.config.cjs
```

Verificar: `curl http://localhost:8882/api/v2/health`

### 4. Criar API Key do Omni

```bash
PLAIN_KEY="omni_sk_$(openssl rand -hex 24)"
KEY_PREFIX="${PLAIN_KEY:8:8}"
KEY_HASH=$(echo -n "$PLAIN_KEY" | shasum -a 256 | cut -d' ' -f1)

docker exec namastex-business-db-1 psql -U readonly -d omni -c "
INSERT INTO api_keys (name, key_prefix, key_hash, scopes, status)
VALUES ('namastex-dev', '${KEY_PREFIX}', '${KEY_HASH}', '{\"*\"}', 'active');
"

echo "Sua API key: $PLAIN_KEY"
```

Guardar a key — vai usar nos proximos passos.

### 5. Setup Genie

O script cria tudo no Omni: provider Genie, agent, instancia WhatsApp.

```bash
OMNI_KEY="<sua-api-key>" ./scripts/setup-genie.sh
```

O que ele configura:
- **Genie provider** `nex-genie` com `teamName: namastex-{chat_id}` — cada conversa vira uma team separada
- **Agent** `nex` linkado ao provider
- **Instancia WhatsApp** `report-bot` linkada ao agent

### 6. Conectar WhatsApp

```bash
OMNI_KEY="<sua-api-key>"
INSTANCE_ID="<id-do-passo-anterior>"
PHONE="+5511999999999"

curl -s -X POST "http://localhost:8882/api/v2/instances/${INSTANCE_ID}/connect" \
  -H "x-api-key: $OMNI_KEY"

sleep 4

curl -s -X POST "http://localhost:8882/api/v2/instances/${INSTANCE_ID}/pair" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $OMNI_KEY" \
  -d "{\"phoneNumber\": \"${PHONE}\"}"
```

No WhatsApp: **Settings > Linked Devices > Link a Device > Link with phone number** e digitar o codigo.

### 7. Testar

Manda mensagem no WhatsApp. Claude Code le da team inbox e usa MCP tools:

- **"oi"** — conversa natural, sem chamar tools
- **"tudo bem?"** — conversa natural
- **"relatorio do mes"** — chama `generate_business_report` via MCP
- **"vendas por produto"** — chama `query_sales(group_by=product)` via MCP
- **"quantos clientes?"** — chama `query_clients` via MCP
- **"como ta o financeiro?"** — chama `query_financial` via MCP
- **"obrigado"** — conversa natural

Verificar se a inbox foi criada:
```bash
ls ~/.claude/teams/namastex-*
```

## Fluxo Detalhado de uma Mensagem

```
1. Pedro manda "relatorio do mes" no WhatsApp

2. Omni recebe via Baileys
   → agent-dispatcher detecta message.received
   → Genie provider ativado

3. Genie escreve no filesystem (atomico, com lock):
   ~/.claude/teams/namastex-5511999/inboxes/nex.json
   {
     "from": "omni",
     "text": "[channel:whatsapp instance:uuid chat:5511999@s.whatsapp.net]\nrelatorio do mes",
     "timestamp": "2026-03-20T15:00:00Z",
     "read": false
   }

4. Genie auto-spawna Claude Code no diretorio do projeto
   → Claude Code le .claude/CLAUDE.md (sabe que e o Nex)
   → Claude Code le .mcp.json (descobre 9 tools em localhost:8000)

5. Claude Code processa a mensagem:
   → "relatorio do mes" → precisa de dados → chama generate_business_report
   → MCP Server consulta PostgreSQL
   → Retorna: vendas, financeiro, clientes, anomalias, comparacoes

6. Claude Code formata resposta natural em pt-BR
   → Responde via SendMessage ao "omni" com header de roteamento

7. inbox-bridge (Omni) detecta nova mensagem no inbox do omni
   → Parseia header [channel:whatsapp instance:uuid chat:5511999]
   → Envia resposta pro WhatsApp via Baileys

8. Pedro recebe o relatorio formatado no WhatsApp
```

## MCP Tools (9)

Todas expostas via MCP protocol em `http://localhost:8000/mcp`. Claude Code as descobre automaticamente via `.mcp.json`.

### Relatorio
| Tool | Parametros | Retorno |
|------|------------|---------|
| `generate_business_report` | `time_range` (today/7d/this_month/etc), `user_id` | Relatorio completo: vendas + financeiro + top clientes + produtos + anomalias + comparacao com periodo anterior |

### Consultas
| Tool | Parametros | Retorno |
|------|------------|---------|
| `query_sales` | `since` (YYYY-MM-DD), `group_by` (date/product/client), `user_id` | Dados de vendas agrupados |
| `query_clients` | `user_id` | Total, novos no mes, distribuicao por plano |
| `query_financial` | `months` (1-12), `user_id` | Receita, lucro, margem por mes |

### Contexto e Memoria
| Tool | Parametros | Retorno |
|------|------------|---------|
| `get_user_context` | `user_id` | Preferencias salvas + historico de relatorios + status do sistema |
| `save_user_preference` | `user_id`, `preferred_report_type`, `preferred_time_range`, `preferred_format` | Salva preferencias para proximos relatorios |
| `get_report_history` | `user_id`, `limit` (1-10) | Relatorios gerados anteriormente com metricas |

### Sistema
| Tool | Retorno |
|------|---------|
| `health_check` | Status do banco de dados |
| `describe_capabilities` | Descricao do que o agente pode fazer (pt-BR/en-US) |

## Variaveis de Ambiente

### MCP Server (`.env` na raiz)

| Variavel | Obrigatoria | Descricao |
|----------|-------------|-----------|
| `BUSINESS_DATABASE_URI` | Nao | URI do PostgreSQL (default: `postgresql://readonly:readonly@localhost:5433/business`) |
| `AUTH_DEV_MODE` | Nao | `true` para dev, `false` para producao |
| `AUTH_SECRET` | Producao | Secret HMAC para autenticacao de tools |
| `AUTH_ADMIN_IDS` | Nao | IDs de admin separados por virgula |

### Omni (`omni/.env` — nao commitado)

| Variavel | Obrigatoria | Descricao |
|----------|-------------|-----------|
| `ANTHROPIC_API_KEY` | Sim | API key da Anthropic (usada pelo Claude Code) |
| `DATABASE_URL` | Sim | PostgreSQL do Omni |
| `NATS_URL` | Sim | Event bus |

## Comandos

```bash
make up          # Subir MCP server + banco
make down        # Parar tudo
make build       # Rebuild Docker images
make logs        # Ver logs do MCP server
make db-shell    # Abrir psql no banco
make clean       # Parar + deletar volumes
```

## Decisoes Tecnicas

- **Genie em vez de webhook direto**: Genie usa o Claude Code nativo como agente, com team inboxes no filesystem. Isso da ao agente acesso completo ao MCP protocol, tools discovery automatica, e conversacao natural sem precisar de codigo custom pra roteamento de intencao.

- **MCP server puro (sem logica de conversacao)**: O server so expoe tools e dados. Toda inteligencia conversacional fica no Claude Code, que decide sozinho quando buscar dados e quando apenas conversar.

- **Isolamento por chat** (`teamName: namastex-{chat_id}`): Cada conversa do WhatsApp vira uma team separada no Claude Code, evitando que mensagens de diferentes usuarios se misturem.

- **Memoria cross-session**: O MCP server persiste preferencias, historico de relatorios e baselines EMA no PostgreSQL. Isso permite deteccao de anomalias e comparacao entre periodos.

- **Pipeline ReSpAct**: A geracao de relatorio segue um pipeline gather → analyze → format com possibilidade de re-gather se os dados estiverem incompletos.
