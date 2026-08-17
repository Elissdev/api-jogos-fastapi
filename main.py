"""
API REST de Jogos — Atividade Prática Unidade III
==================================================
API REST construída com FastAPI para gerenciar um catálogo de jogos.

Tema escolhido: Jogos (videogames) — diferente do exemplo utilizado em
sala de aula (alunos e professores).

Recurso: Jogo
    Atributos:
        - id             (int)  -> identificador único (obrigatório)
        - titulo         (str)  -> nome do jogo
        - genero         (str)  -> gênero (Ação, RPG, Esporte, ...)
        - plataforma     (str)  -> plataforma (PC, PlayStation, Xbox, ...)
        - ano_lancamento (int)  -> ano de lançamento

Rotas:
    POST /jogos            -> cria um novo jogo (201 Created)
    GET  /jogos            -> lista todos os jogos (200 OK)
                              ?genero=... filtra por gênero (opcional)
    GET  /jogos/{id}       -> consulta um jogo pelo id (200 OK / 404)

Os registros são mantidos temporariamente em memória (lista de dicionários).
"""

from typing import List, Optional

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Modelo do recurso
# ---------------------------------------------------------------------------
class Jogo(BaseModel):
    id: int
    titulo: str
    genero: str
    plataforma: str
    ano_lancamento: int


# ---------------------------------------------------------------------------
# "Banco de dados" em memória: uma lista Python cujos itens são dicionários
# ---------------------------------------------------------------------------
jogos: List[dict] = []


app = FastAPI(
    title="API de Jogos",
    description="API REST para gerenciamento de um catálogo de jogos "
                "(Atividade Prática - Unidade III).",
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# 1) Criar um novo registro  ->  POST /jogos  (201 Created)
# ---------------------------------------------------------------------------
@app.post("/jogos", response_model=Jogo, status_code=status.HTTP_201_CREATED)
def criar_jogo(jogo: Jogo):
    """Cria um novo jogo e o adiciona à lista em memória.

    O id informado no corpo da requisição deve ser único.
    Retorna 201 Created em caso de sucesso e 409 Conflict se o id já
    estiver em uso.
    """
    if any(j["id"] == jogo.id for j in jogos):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe um jogo cadastrado com o id {jogo.id}.",
        )

    jogos.append(jogo.model_dump())
    return jogos[-1]


# ---------------------------------------------------------------------------
# 2) Listar todos os registros  ->  GET /jogos  (200 OK)
#    Filtro opcional: ?genero=... (parâmetro de consulta)
# ---------------------------------------------------------------------------
@app.get("/jogos", response_model=List[Jogo])
def listar_jogos(genero: Optional[str] = None):
    """Lista todos os jogos cadastrados.

    Se o parâmetro de consulta `genero` for informado (ex.: ?genero=RPG),
    retorna apenas os jogos desse gênero. Se não for informado, retorna a
    lista completa. A comparação ignora diferenças entre maiúsculas e
    minúsculas.
    """
    if genero is None:
        return jogos

    return [j for j in jogos if j["genero"].lower() == genero.lower()]


# ---------------------------------------------------------------------------
# 3) Consultar um registro por ID  ->  GET /jogos/{id}  (200 OK / 404)
# ---------------------------------------------------------------------------
@app.get("/jogos/{jogo_id}", response_model=Jogo)
def consultar_jogo(jogo_id: int):
    """Retorna o jogo cujo id corresponde a `jogo_id` (parâmetro de caminho).

    Retorna 404 Not Found caso não exista nenhum jogo com esse id.
    """
    for j in jogos:
        if j["id"] == jogo_id:
            return j

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Jogo com id {jogo_id} não encontrado.",
    )
