# API de Jogos - REST com FastAPI

API REST construída em Python com **FastAPI** para gerenciar um catálogo de
jogos (videogames). Desenvolvida como atividade prática da disciplina,
utilizando um tema diferente do exemplo visto em sala de aula (alunos e
professores).

- Recebe e retorna dados em **JSON**
- Registros mantidos temporariamente em memória (lista Python de dicionários)
- Documentação interativa (Swagger UI) em `/docs`

## Recurso gerenciado: Jogo

Cada registro possui 5 atributos (mínimo exigido: 4, incluindo o `id`):

| Atributo          | Tipo | Descrição                                   |
|-------------------|------|---------------------------------------------|
| `id`              | int  | Identificador único e obrigatório           |
| `titulo`          | str  | Nome do jogo                                |
| `genero`          | str  | Gênero (Aventura, Ação, RPG, Esporte, ...)  |
| `plataforma`      | str  | Plataforma (PC, PlayStation 5, Xbox, ...)   |
| `ano_lancamento`  | int  | Ano de lançamento                           |

## Rotas, métodos e códigos HTTP

| Método | Rota                | Função                              | Códigos de resposta                    |
|--------|---------------------|-------------------------------------|----------------------------------------|
| POST   | `/jogos`            | Criar um novo jogo                  | `201 Created` / `409 Conflict` / `422` |
| GET    | `/jogos`            | Listar todos os jogos               | `200 OK`                               |
| GET    | `/jogos?genero=RPG` | Listar jogos de um gênero (filtro)  | `200 OK`                               |
| GET    | `/jogos/{jogo_id}`  | Consultar um jogo pelo id           | `200 OK` / `404 Not Found`             |

### Parâmetro de consulta `genero` (filtro opcional)

- Se **não informado**, a rota `GET /jogos` lista **todos** os registros.
- Se **informado** (`/jogos?genero=RPG`), retorna **apenas** os jogos do
  gênero correspondente. A comparação ignora diferenças entre maiúsculas e
  minúsculas (ex.: `?genero=rpg` também encontra "RPG").

### Parâmetro de caminho `{jogo_id}`

A rota `GET /jogos/{jogo_id}` consulta um registro pelo seu identificador
único. Retorna `200 OK` com o registro, ou `404 Not Found` com mensagem
descritiva quando o id não existe.

## Como executar

Requisitos: Python 3.10+

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Acesse a documentação interativa:

```
http://127.0.0.1:8000/docs
```

## Exemplos de uso

Criar um jogo:

```bash
curl -X POST http://127.0.0.1:8000/jogos \
  -H "Content-Type: application/json" \
  -d '{"id": 1, "titulo": "Mario Kart 8 Deluxe", "genero": "Corrida", "plataforma": "Nintendo Switch", "ano_lancamento": 2017}'
```

Listar todos:

```bash
curl http://127.0.0.1:8000/jogos
```

Filtrar por gênero:

```bash
curl "http://127.0.0.1:8000/jogos?genero=RPG"
```

Consultar por id (use `-i` para ver o código HTTP; id inexistente retorna 404):

```bash
curl http://127.0.0.1:8000/jogos/1
curl -i http://127.0.0.1:8000/jogos/999
```

## Testes

O script `teste_api.py` executa 22 verificações automáticas cobrindo todos os
cenários das rotas (201, 200, 404, 409, 422, filtro por gênero e validação de
dados). Ele usa apenas a biblioteca padrão do Python:

```bash
python3 teste_api.py
```

## Estrutura do projeto

```
.
|-- main.py              # Aplicação FastAPI
|-- requirements.txt     # Dependências (fastapi, uvicorn)
|-- teste_api.py         # Testes automáticos (22 cenários)
`-- capturas/            # Capturas de tela dos testes em /docs
```

> Observação: por ser mantida em memória, a lista é reiniciada (esvaziada)
> sempre que o servidor é reiniciado.
