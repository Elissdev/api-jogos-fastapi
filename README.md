# API de Jogos — REST com FastAPI e Cloud Firestore

API REST construída em Python com **FastAPI** para gerenciar um catálogo de
jogos (videogames). É a evolução da API da **Unidade III**, que mantinha os
registros temporariamente em uma lista Python em memória (perdidos ao
reiniciar o servidor). Nesta unidade, os registros passaram a ser gravados
como **documentos de uma coleção do Cloud Firestore** (Firebase), ficando
disponíveis mesmo após o encerramento ou a reinicialização da aplicação.

- Recebe e retorna dados em **JSON**
- Registros persistidos no **Cloud Firestore** (coleção `jogos`)
- Integração pelo **Firebase Admin SDK** (`firebase-admin`), mecanismo indicado no material da Unidade IV
- Documentação interativa (Swagger UI) em `/docs`

## Recurso gerenciado: Jogo

Cada registro possui os mesmos 5 atributos da Unidade III e é armazenado
como um documento da coleção `jogos` (o **id do documento** é o id do jogo):

| Atributo          | Tipo | Descrição                                   |
|-------------------|------|---------------------------------------------|
| `id`              | int  | Identificador único e obrigatório           |
| `titulo`          | str  | Nome do jogo                                |
| `genero`          | str  | Gênero (Aventura, Ação, RPG, Esporte, ...)  |
| `plataforma`      | str  | Plataforma (PC, PlayStation 5, Xbox, ...)   |
| `ano_lancamento`  | int  | Ano de lançamento                           |

## Rotas, métodos e códigos HTTP (mantidos da Unidade III)

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
  minúsculas (ex.: `?genero=rpg` também encontra "RPG"), mantendo o
  comportamento da Unidade III.

### Parâmetro de caminho `{jogo_id}`

A rota `GET /jogos/{jogo_id}` consulta um registro pelo seu identificador
único — o documento é localizado diretamente no Firestore pelo id
(leitura pontual). Retorna `200 OK` com o registro, ou `404 Not Found`
quando o id não existe.

## Configuração do Cloud Firestore

O mecanismo de integração é o **Firebase Admin SDK** (`firebase-admin`), conforme
a documentação oficial indicada no material da disciplina:
<https://firebase.google.com/docs/firestore/manage-data/add-data>

Para executar, é necessário fornecer a credencial de **uma** das formas abaixo
(nenhuma chave privada está incluída na entrega):

### Opção 1 — Chave da conta de serviço (mecanismo do material)

1. Crie um projeto em <https://console.firebase.google.com> e habilite o
   **Cloud Firestore** (crie o banco de dados no modo de produção ou de
   teste).
2. Em **Configurações do projeto**, aba **Contas de serviço**, clique em
   **Gerar nova chave privada**. Será baixado um arquivo JSON (a chave da
   conta de serviço).
3. Salve esse arquivo na pasta do projeto com o nome **`serviceAccountKey.json`**
   (é o mesmo procedimento mostrado no material da unidade, com
   `credentials.Certificate()`; o arquivo é ignorado pelo `.gitignore`):
   ```bash
   uvicorn main:app --reload
   ```

   Ou informe a chave por variável de ambiente (credenciais padrão do Google):
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS=/caminho/para/chave.json
   uvicorn main:app --reload
   ```

## Testando com o projeto Firebase real (passo a passo)

Passo a passo completo para rodar a API contra o **Cloud Firestore real** e
comprovar a persistência (mesmo procedimento avaliado na atividade):

### 1. Crie o projeto e habilite o Firestore

1. Acesse <https://console.firebase.google.com> com sua conta Google e clique
   em **Criar projeto** (ou use um projeto já existente).
2. Na página do projeto, no menu lateral, clique em **Build** e, em seguida,
   em **Firestore Database** (ou **Cloud Firestore**).
3. Clique em **Criar banco de dados** e escolha:
   - **Modo de produção** (regras restritas) ou **modo de teste** (acesso
     liberado por 30 dias — suficiente para a atividade);
   - Região: escolha uma próxima (ex.: `southamerica-east1`).

### 2. Baixe a chave da conta de serviço

1. No Console, clique em **Configurações do projeto** (ícone de engrenagem)
   e, na aba **Contas de serviço**, clique em **Gerar nova chave privada** e
   confirme. Será baixado um arquivo JSON (ex.:
   `projeto-firebase-adminsdk-xxxxx.json`).
3. **Renomeie para `serviceAccountKey.json`** e salve na mesma pasta do
   `main.py` (o arquivo está no `.gitignore` e não deve ser enviado).

### 3. Instale as dependências e inicie a API

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

A API inicia conectada ao seu projeto real (via `credentials.Certificate()`).
Abra a documentação interativa:

```
http://127.0.0.1:8000/docs
```

### 4. Teste as rotas em /docs

1. Em **POST /jogos**, clique em *Try it out*, informe um jogo (ex.:
   `{"id": 777, "titulo": "Hollow Knight", "genero": "Aventura",
   "plataforma": "PC", "ano_lancamento": 2017}`) e execute — deve retornar
   **201 Created**;
2. Em **GET /jogos**, execute — deve listar o jogo criado (**200 OK**);
3. Em **GET /jogos/{jogo_id}**, informe `777` — deve retornar o registro
   (**200 OK**); informe um id inexistente — deve retornar **404 Not Found**;
4. Teste também o filtro **GET /jogos?genero=Aventura**.

### 5. Confira o documento no Console do Firebase

1. No Console, abra **Build** e, em seguida, **Firestore Database**;
2. Na guia **Dados**, clique na coleção **`jogos`**: o documento **`777`**
   deve aparecer com todos os atributos (`id`, `titulo`, `genero`,
   `plataforma`, `ano_lancamento`) — é a captura de tela pedida na entrega;
3. Atualize a página do Console depois de criar novos jogos para ver os
   documentos aparecerem em tempo real.

### 6. Comprove a persistência (reiniciar a aplicação)

1. Com a API rodando, consulte `GET /jogos/777` (200 OK);
2. **Pare o servidor** (Ctrl+C no terminal do uvicorn);
3. **Inicie novamente**: `uvicorn main:app --reload`;
4. Consulte `GET /jogos/777` **de novo** — o registro continua disponível
   (**200 OK**), pois foi lido do Firestore, não da memória.

   Também é possível automatizar com:
   ```bash
   python3 demonstra_persistencia.py
   ```

### 7. Rode os testes automáticos

```bash
python3 teste_api.py
```

Esperado: **22 verificações, todas PASS**.

### Opção 2 — Emulador local (testes sem custo)

Para testar sem criar um projeto real, use o Firestore Emulator:

```bash
# 1) Instale o Firebase CLI e inicie o emulador (porta 8081)
firebase emulators:start --only firestore --project demo-api-jogos

# 2) Em outro terminal, aponte a API para o emulador
export FIRESTORE_EMULATOR_HOST=127.0.0.1:8081
uvicorn main:app --reload
```

> No código, `obter_app_firebase()` inicializa o Firebase Admin SDK
> (`firebase_admin.initialize_app`) verificando, nesta ordem: primeiro o
> arquivo `serviceAccountKey.json` (`credentials.Certificate`), depois a
> variável de ambiente `GOOGLE_APPLICATION_CREDENTIALS`
> (`credentials.ApplicationDefault`) e, por fim, o emulador
> (`FIRESTORE_EMULATOR_HOST`).

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

## Comprovando a persistência (após reiniciar a aplicação)

A persistência pode ser comprovada manualmente ou com o script automático:

### Manualmente

1. Crie um registro pela API (ex.: `POST /jogos` com `id: 777`);
2. **Reinicie a aplicação** (pare o uvicorn e inicie novamente);
3. Consulte o mesmo registro (`GET /jogos/777`) — ele continua disponível,
   pois foi lido do Firestore, não da memória.

### Com o script automático

```bash
python3 demonstra_persistencia.py
```

O script cria o jogo 777 (se não existir), mostra a listagem, pede para você
reiniciar a aplicação e, depois, consulta o mesmo registro — exibindo
"PERSISTÊNCIA COMPROVADA!" quando tudo funciona.

## Testes

O script `teste_api.py` executa 22 verificações automáticas cobrindo todos os
cenários das rotas (201, 200, 404, 409, 422, filtro por gênero e validação de
dados) — agora contra os dados persistidos no Firestore. Ele usa apenas a
biblioteca padrão do Python:

```bash
python3 teste_api.py
```

## Capturas de tela (`capturas/`)

| Captura | Teste realizado | Resultado |
|---------|-----------------|-----------|
| `01_docs_visao_geral.png` | Visão geral das rotas no Swagger UI | — |
| `02_post_jogos_201_created.png` | POST /jogos (criar jogo) | 201 Created |
| `03_get_jogos_lista_200.png` | GET /jogos (listar todos) | 200 OK |
| `04_get_jogos_filtro_genero.png` | GET /jogos?genero=RPG (filtro) | 200 OK |
| `05_get_jogos_id_200.png` | GET /jogos/777 (consulta por id) | 200 OK |
| `06_get_jogos_id_404_not_found.png` | GET /jogos/999 (id inexistente) | 404 Not Found |
| `07_firestore_documento.png` | Documento armazenado na coleção `jogos` | — |
| `08_persistencia_apos_reinicio.png` | Consulta após reiniciar a aplicação | 200 OK |

As capturas podem ser reproduzidas com o script `capturar_docs.py`:

```bash
# Capturas 01–07
python3 capturar_docs.py

# Reinicie a aplicação e capture a consulta pós-reinício
python3 capturar_docs.py --so-persistencia
```

> Obs.: a captura `07_firestore_documento.png` foi feita na UI do emulador.
> Com um projeto Firebase real, o documento pode ser visto no
> **Console do Firebase**, em **Firestore Database**, coleção **`jogos`** — o
> mesmo documento é exibido com todos os atributos.

## Estrutura do projeto

```
.
|-- main.py                  # Aplicação FastAPI integrada ao Firestore (Firebase Admin SDK)
|-- requirements.txt         # Dependências (fastapi, uvicorn, firebase-admin)
|-- teste_api.py             # Testes automáticos (22 cenários)
|-- demonstra_persistencia.py# Comprova a persistência após reiniciar a API
|-- capturar_docs.py         # Gera as capturas de tela de /docs (Playwright)
|-- README.md                # Este documento
|-- EXPLICACAO.txt/.docx     # Texto explicativo da atividade
|-- capturas/                # Capturas de tela dos testes em /docs
`-- serviceAccountKey.json   # (NÃO enviar) chave privada da conta de serviço
```

> **Segurança:** o arquivo `serviceAccountKey.json` (chave privada) está no
> `.gitignore` e **não deve ser enviado** na entrega — apenas o código e a
> explicação de como a configuração deve ser fornecida.
