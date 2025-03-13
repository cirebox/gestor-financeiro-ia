# Financial Tracker

Um sistema de contabilidade financeira pessoal com interface natural por linguagem humana e API REST, construído seguindo os princípios da Clean Architecture.

## Índice

- [Visão Geral](#visão-geral)
- [Recursos](#recursos)
- [Status de Desenvolvimento](#status-de-desenvolvimento)
- [Arquitetura](#arquitetura)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
  - [Usando Docker (Recomendado)](#usando-docker-recomendado)
  - [Instalação Manual](#instalação-manual)
- [Configuração](#configuração)
- [Uso](#uso)
  - [API REST](#api-rest)
  - [Interface por Linguagem Natural](#interface-por-linguagem-natural)
  - [Exemplos de Comandos](#exemplos-de-comandos)
- [Testes](#testes)
- [Documentação da API](#documentação-da-api)
- [Contribuição](#contribuição)
- [Licença](#licença)

## Visão Geral

Financial Tracker é uma aplicação para gerenciamento financeiro pessoal que permite aos usuários registrar despesas e receitas, categorizá-las, gerar relatórios e análises. O diferencial está na interface dual: além da API REST tradicional, o sistema possui um agente que entende comandos em linguagem natural.

## Recursos

- ✅ Cadastro de transações (receitas e despesas)
- ✅ Categorização flexível de transações
- ✅ Busca e filtragem avançada
- ✅ Relatórios e análises financeiras
- ✅ Processamento de linguagem natural para comandos em português
- ✅ API REST para integração com outras aplicações
- ✅ Banco de dados não relacional (MongoDB)
- ✅ Sugestões de orçamento baseadas em histórico
- ✅ Previsão de gastos futuros
- ✅ Análise de tendências financeiras
- ✅ Identificação de gastos recorrentes
- ✅ Score de saúde financeira

## Status de Desenvolvimento

O projeto está em fase beta e pronto para uso. Abaixo está o status de desenvolvimento por funcionalidade:

### Componentes principais
- [x] Estrutura de camadas da Clean Architecture
- [x] Entidades de domínio (Transaction, Category, User)
- [x] Casos de uso da aplicação
- [x] Repositórios MongoDB
- [x] Serviço de processamento de linguagem natural
- [x] Serviço de análises financeiras
- [x] API REST com FastAPI
- [x] Interface CLI
- [x] Dockerização da aplicação

### Funcionalidades
- [x] Gerenciamento de transações
- [x] Gerenciamento de categorias
- [x] Cálculo de balanço financeiro
- [x] Processamento de comandos em linguagem natural
- [x] Relatórios mensais
- [x] Análise de tendências
- [x] Previsão de gastos
- [x] Sugestão de orçamento
- [x] Score de saúde financeira
- [ ] Autenticação de usuários
- [ ] Interface web

## Arquitetura

O projeto segue os princípios da Clean Architecture (Arquitetura Limpa), criada por Robert C. Martin, que separa o software em camadas concêntricas, onde as dependências apontam apenas para dentro.

### Estrutura de Pastas

```
financial_tracker/
├── README.md
├── requirements.txt
├── setup.py
├── .env.example
├── config.py
├── run.py
├── Dockerfile
├── docker-compose.yml
├── src/
│   ├── domain/               # Regras de negócio e entidades
│   │   ├── entities/
│   │   ├── value_objects/
│   │   ├── exceptions/
│   │   └── repositories/
│   ├── application/          # Casos de uso e lógica de aplicação
│   │   ├── interfaces/
│   │   ├── dtos/
│   │   ├── usecases/
│   │   └── services/
│   ├── infrastructure/       # Implementações técnicas (BD, web, etc)
│   │   ├── database/
│   │   ├── nlp/
│   │   └── analytics/
│   └── interfaces/           # Interfaces com o usuário (API, CLI)
│       ├── api/
│       └── cli/
└── tests/                    # Testes unitários e de integração
    ├── unit/
    └── integration/
```

### Camadas da Arquitetura

1. **Domínio** - O núcleo da aplicação, contendo entidades de negócio e regras que são independentes de frameworks externos.
2. **Aplicação** - Contém os casos de uso da aplicação, coordenando o fluxo de dados entre as entidades e os gateways externos.
3. **Infraestrutura** - Implementações concretas de interfaces definidas nas camadas internas (repositórios, serviços externos).
4. **Interfaces** - Mecanismos de entrega como APIs REST, interfaces gráficas, ou linha de comando.

## Pré-requisitos

- Python 3.8+
- MongoDB 4.4+
- Docker e Docker Compose (opcional, mas recomendado)

## Instalação

### Usando Docker (Recomendado)

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/financial-tracker.git
cd financial-tracker
```

2. Inicie a aplicação com Docker Compose:
```bash
docker-compose up -d
```

A API estará disponível em `http://localhost:8000` e a documentação em `http://localhost:8000/api/docs`.

### Instalação Manual

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/financial-tracker.git
cd financial-tracker
```

2. Crie e ative um ambiente virtual:
```bash
python -m venv venv
# No Windows
venv\Scripts\activate
# No Unix ou MacOS
source venv/bin/activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente (copie o arquivo .env.example para .env e ajuste conforme necessário):
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

5. Certifique-se de que o MongoDB está em execução localmente ou ajuste a URL de conexão no arquivo .env.

6. Inicie a API:
```bash
python run.py
```

## Configuração

### Banco de Dados

O sistema utiliza MongoDB como banco de dados. Você pode configurar a conexão no arquivo `.env`:

```
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB=financial_tracker
```

## Uso

### API REST

A API estará disponível em `http://localhost:8000`. Os principais endpoints são:

- `POST /api/v1/transactions` - Adicionar uma nova transação
- `GET /api/v1/transactions` - Listar transações (com filtros)
- `GET /api/v1/balance` - Ver saldo e resumo financeiro
- `GET /api/v1/reports/monthly` - Gerar relatório mensal
- `POST /api/v1/nlp/process` - Processar comandos em linguagem natural

### Interface por Linguagem Natural

Você pode usar a interface por linguagem natural via CLI ou API:

#### CLI:

```bash
python -m src.interfaces.cli.cli_app
```

Uma interface interativa será aberta, onde você pode digitar comandos em linguagem natural.

#### API de Linguagem Natural:

Você também pode enviar comandos via API:

```
POST /api/v1/nlp/process

Body:
{
    "command": "adicionar receita de R$ 1500 como Salário"
}
```

### Exemplos de Comandos

#### Transações
- "adicionar despesa de R$ 50 em Alimentação"
- "registrar gasto de 120,50 com descrição 'Mercado semanal'"
- "adicionar receita de R$ 2000 como Salário"
- "registrar renda de 500 de Freelance descrição 'Projeto XYZ'"

#### Consultas
- "listar todas as transações"
- "mostrar despesas de janeiro"
- "exibir receitas de 01/01/2023 até 31/01/2023"
- "saldo atual"
- "balanço de janeiro"
- "resumo de 01/01/2023 até 31/01/2023"

#### Gerenciamento
- "excluir transação id abc123"
- "atualizar transação id abc123 valor para 75,50"
- "adicionar categoria Educação tipo despesa"
- "listar categorias de despesas"

## Testes

Execute os testes unitários:

```bash
pytest tests/unit
```

Execute os testes de integração:

```bash
pytest tests/integration
```

Execute todos os testes com cobertura:

```bash
pytest --cov=src tests/
```

## Documentação da API

A documentação da API está disponível em:

- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`
- OpenAPI JSON: `http://localhost:8000/api/openapi.json`

## Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/amazing-feature`)
3. Commit suas mudanças (`git commit -m 'Add some amazing feature'`)
4. Push para a branch (`git push origin feature/amazing-feature`)
5. Abra um Pull Request

### Fluxo de Desenvolvimento

1. Identifique uma tarefa para trabalhar (crie ou escolha uma issue)
2. Implemente as mudanças com testes
3. Verifique se todos os testes passam
4. Envie um Pull Request
5. Aguarde a revisão e aprovação

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

Desenvolvido com ❤️ usando Clean Architecture e princípios SOLID.