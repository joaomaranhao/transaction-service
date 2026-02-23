# Transaction Service

Serviço de transações financeiras com processamento assíncrono via RabbitMQ.

## Arquitetura

![Arquitetura](./docs/arquitetura.png)

### Fluxo de Transação

1. **API** recebe requisição e cria transação com status `pending`
2. **Mensagem** é publicada na fila `transactions`
3. **Worker** consome a mensagem e processa com o parceiro bancário
4. **Sucesso**: status atualizado para `completed`
5. **Falha**: mensagem vai para fila de retry (máx. 3 tentativas)
6. **Falha final**: mensagem vai para DLQ (`transactions.dlq`)

### Filas RabbitMQ

| Fila                 | Descrição                       |
| -------------------- | ------------------------------- |
| `transactions`       | Fila principal de processamento |
| `transactions.retry` | Retry com TTL de 5s e DLX       |
| `transactions.dlq`   | Dead Letter Queue               |

## Stack

- **Python 3.11+**
- **FastAPI** - API REST
- **SQLModel** - ORM (SQLAlchemy + Pydantic)
- **aio-pika** - Cliente RabbitMQ assíncrono
- **Loguru** - Logging estruturado
- **Docker Compose** - Orquestração

## Quick Start

### Com Docker

```bash
docker compose up --build
```

Serviços disponíveis:

- API: http://localhost:8000
- RabbitMQ Management: http://localhost:15672 (guest/guest)

### Local (desenvolvimento)

```bash
# Instalar dependências
uv sync

# RabbitMQ em container
docker compose -f docker-compose.dev.yaml up -d

# Rodar API
uv run uvicorn app.main:app --reload

# Rodar Worker (outro terminal)
uv run python -m app.worker
```

## API Endpoints

### Transações

#### Criar Transação

```http
POST /transactions
Content-Type: application/json
X-Request-ID: <trace_id> (opcional)

{
  "external_id": "550e8400-e29b-41d4-a716-446655440000",
  "amount": 100.50,
  "kind": "credit",
  "account_id": "ACC123" (campo criado para poder gerar o balanço da conta, não estava no escopo original, mas achei necessário para a funcionalidade de consultar saldo)
}
```

**Responses:**

- `201 Created` - Transação criada
- `200 OK` - Transação já existente (idempotência)
- `400 Bad Request` - Dados inválidos

### Contas

#### Consultar Saldo

```http
GET /accounts/{account_id}/balance
```

**Response:**

```json
{
  "account_id": "ACC123",
  "balance": 250.75
}
```

### Health Check

```http
GET /health
```

## Variáveis de Ambiente

| Variável       | Default                              | Descrição             |
| -------------- | ------------------------------------ | --------------------- |
| `DATABASE_URL` | `sqlite:///./data/database.db`       | URL do banco de dados |
| `RABBITMQ_URL` | `amqp://guest:guest@localhost:5672/` | URL do RabbitMQ       |
| `LOG_LEVEL`    | `INFO`                               | Nível de log          |
| `RETRY_TTL_MS` | `5000`                               | TTL do retry em ms    |
| `MAX_RETRIES`  | `3`                                  | Máximo de tentativas  |

## Estrutura do Projeto

```
app/
├── api/
│   ├── routes.py           # Agregador de rotas
│   └── endpoints/          # Endpoints por domínio
├── core/
│   ├── config.py           # Configurações (Pydantic Settings)
│   ├── database.py         # Engine SQLModel
│   ├── exceptions.py       # Exceções customizadas
│   └── logger.py           # Configuração Loguru
├── integrations/
│   └── bank_partner.py     # Integração com parceiro bancário
├── messaging/
│   └── publisher.py        # Publisher RabbitMQ (singleton)
├── models/
│   └── transaction.py      # Modelo SQLModel
├── repositories/
│   └── transaction_repository.py
├── schemas/
│   └── transaction.py      # DTOs Pydantic
├── services/
│   ├── account_services.py
│   └── transaction_service.py
├── main.py                 # FastAPI app
└── worker.py               # Consumer RabbitMQ
```

## Testes

```bash
# Rodar todos os testes
uv run pytest

# Com coverage
uv run pytest --cov=app

# Verbose
uv run pytest -v
```
