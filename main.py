"""
API REST de Jogos — Atividade Prática Unidade IV
=================================================
API REST construída com FastAPI para gerenciar um catálogo de jogos,
evoluída a partir da Unidade III para persistir os dados no
Cloud Firestore (Firebase).

Tema escolhido: Jogos (videogames) — diferente do exemplo utilizado em
sala de aula (alunos e professores).

Recurso: Jogo
    Atributos:
        - id             (int)  -> identificador único (obrigatório)
        - titulo         (str)  -> nome do jogo
        - genero         (str)  -> gênero (Ação, RPG, Esporte, ...)
        - plataforma     (str)  -> plataforma (PC, PlayStation, Xbox, ...)
        - ano_lancamento (int)  -> ano de lançamento

Rotas (mesmas da Unidade III):
    POST /jogos            -> cria um novo jogo (201 Created)
    GET  /jogos            -> lista todos os jogos (200 OK)
                              ?genero=... filtra por gênero (opcional)
    GET  /jogos/{id}       -> consulta um jogo pelo id (200 OK / 404)

Persistência:
    Na Unidade III os registros ficavam em uma lista Python em memória
    (perdidos ao reiniciar). Nesta unidade, cada registro passou a ser um
    DOCUMENTO de uma COLEÇÃO do Cloud Firestore ("jogos"), identificado
    pelo id do jogo. Os dados continuam disponíveis após o encerramento
    ou a reinicialização da aplicação.

Mecanismo de integração (indicado no material da Unidade IV):
    Firebase Admin SDK (firebase-admin), conforme a documentação oficial
    indicada no manual da disciplina:
        https://firebase.google.com/docs/firestore/manage-data/add-data
    A credencial é a chave privada da conta de serviço (serviceAccountKey.json)
    baixada no Console do Firebase — o mesmo procedimento do material.
"""

import os
from typing import List, Optional

import firebase_admin
from fastapi import FastAPI, HTTPException, status
from firebase_admin import credentials, firestore
from google.api_core.exceptions import AlreadyExists
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Modelo do recurso (idêntico ao da Unidade III)
# ---------------------------------------------------------------------------
class Jogo(BaseModel):
    id: int
    titulo: str
    genero: str
    plataforma: str
    ano_lancamento: int


# ---------------------------------------------------------------------------
# Nome da coleção do Firestore que armazena os registros
# ---------------------------------------------------------------------------
NOME_COLECAO = "jogos"


class _CredencialEmulador(firebase_admin.credentials.Base):
    """Credencial anônima usada apenas com o Firestore Emulator local.

    O emulador não exige autenticação; essa credencial permite que o
    Firebase Admin SDK seja inicializado apontando para ele (testes sem
    custo, sem projeto real). Em produção usa-se a conta de serviço.
    """

    def get_credential(self):
        from google.auth.credentials import AnonymousCredentials

        return AnonymousCredentials()


def obter_app_firebase() -> firebase_admin.App:
    """Inicializa o Firebase Admin SDK e retorna a aplicação Firebase.

    A credencial necessária é fornecida de uma das formas abaixo (na
    ordem em que são verificadas):

    1) Arquivo serviceAccountKey.json salvo no diretório do projeto —
       o mecanismo indicado no material da Unidade IV: a chave privada
       da conta de serviço baixada em Console do Firebase
       (Configurações do projeto > Contas de serviço > Gerar nova chave
       privada), usada com credentials.Certificate().

    2) Variável de ambiente GOOGLE_APPLICATION_CREDENTIALS apontando
       para o mesmo JSON da conta de serviço (credenciais padrão do
       Google).

    3) Emulador local (testes sem custo): definir a variável de ambiente
       FIRESTORE_EMULATOR_HOST (ex.: FIRESTORE_EMULATOR_HOST=127.0.0.1:8081).

    Nenhuma chave privada é incluída na entrega: o aluno deve baixar o
    arquivo JSON da própria conta de serviço no Console do Firebase.
    """
    # Se o app já foi inicializado neste processo (ex.: reimportação),
    # reaproveita em vez de inicializar novamente
    try:
        return firebase_admin.get_app()
    except ValueError:
        pass

    # 1) Mecanismo indicado no material: serviceAccountKey.json no projeto
    caminho_chave = os.path.join(os.path.dirname(__file__), "serviceAccountKey.json")
    if os.path.exists(caminho_chave):
        return firebase_admin.initialize_app(credentials.Certificate(caminho_chave))

    # 2) Credencial padrão do Google (GOOGLE_APPLICATION_CREDENTIALS)
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        return firebase_admin.initialize_app(credentials.ApplicationDefault())

    # 3) Emulador local (FIRESTORE_EMULATOR_HOST)
    if os.environ.get("FIRESTORE_EMULATOR_HOST"):
        return firebase_admin.initialize_app(
            _CredencialEmulador(),
            options={"projectId": os.environ.get("FIRESTORE_PROJECT_ID", "demo-api-jogos")},
        )

    raise RuntimeError(
        "Nenhuma credencial do Cloud Firestore foi encontrada.\n\n"
        "Siga o mecanismo indicado no material da Unidade IV:\n"
        "  1) No Console do Firebase, baixe a chave privada da conta de serviço\n"
        "     (Configurações do projeto > Contas de serviço > Gerar nova chave\n"
        "     privada) e salve o arquivo como serviceAccountKey.json nesta pasta;\n"
        "  2) Ou defina a variável de ambiente:\n"
        "       export GOOGLE_APPLICATION_CREDENTIALS=/caminho/para/chave.json\n"
        "  3) Ou, para testes locais, use o Firestore Emulator:\n"
        "       export FIRESTORE_EMULATOR_HOST=127.0.0.1:8081"
    )


# ---------------------------------------------------------------------------
# Cliente do Firestore — substitui a lista em memória da Unidade III
# (a variável `jogos = []` foi removida)
# ---------------------------------------------------------------------------
app_firebase = obter_app_firebase()
db = firestore.client(app=app_firebase)
colecao = db.collection(NOME_COLECAO)


def documento_para_dict(documento) -> dict:
    """Converte um documento do Firestore em dicionário (formato JSON)."""
    dados = documento.to_dict()
    dados["id"] = int(documento.id)  # o id do documento é o identificador único
    return dados


app = FastAPI(
    title="API de Jogos",
    description="API REST para gerenciamento de um catálogo de jogos, "
                "com persistência no Cloud Firestore "
                "(Atividade Prática - Unidade IV).",
    version="2.0.0",
)


# ---------------------------------------------------------------------------
# 1) Criar um novo registro  ->  POST /jogos  (201 Created)
# ---------------------------------------------------------------------------
@app.post("/jogos", response_model=Jogo, status_code=status.HTTP_201_CREATED)
def criar_jogo(jogo: Jogo):
    """Cria um novo jogo como documento da coleção "jogos" do Firestore.

    O documento é criado com o id do jogo (ex.: id=7 vira o documento "7").
    Como o Firestore não permite dois documentos com o mesmo id na mesma
    coleção, o identificador único é garantido: se o id já existir, o
    método create() lança AlreadyExists e a API responde 409.
    """
    doc_ref = colecao.document(str(jogo.id))
    try:
        # create() falha (AlreadyExists) se o documento já existir — evita
        # sobrescrever um registro e garante a unicidade do id
        doc_ref.create(jogo.model_dump())
    except AlreadyExists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe um jogo cadastrado com o id {jogo.id}.",
        )

    return jogo.model_dump()


# ---------------------------------------------------------------------------
# 2) Listar todos os registros  ->  GET /jogos  (200 OK)
#    Filtro opcional: ?genero=... (parâmetro de consulta)
# ---------------------------------------------------------------------------
@app.get("/jogos", response_model=List[Jogo])
def listar_jogos(genero: Optional[str] = None):
    """Lista todos os jogos persistidos no Firestore.

    Se o parâmetro de consulta `genero` for informado (ex.: ?genero=RPG),
    retorna apenas os jogos desse gênero. Se não for informado, retorna a
    lista completa. A comparação ignora diferenças entre maiúsculas e
    minúsculas (mesmo comportamento da Unidade III).
    """
    jogos = [documento_para_dict(doc) for doc in colecao.stream()]

    # Ordena por id (numérico) para uma saída estável e previsível
    jogos.sort(key=lambda j: j["id"])

    if genero is None:
        return jogos

    return [j for j in jogos if j["genero"].lower() == genero.lower()]


# ---------------------------------------------------------------------------
# 3) Consultar um registro por ID  ->  GET /jogos/{id}  (200 OK / 404)
# ---------------------------------------------------------------------------
@app.get("/jogos/{jogo_id}", response_model=Jogo)
def consultar_jogo(jogo_id: int):
    """Retorna o jogo cujo id corresponde a `jogo_id` (parâmetro de caminho).

    O documento é localizado diretamente pelo id (leitura pontual no
    Firestore). Retorna 404 Not Found caso não exista nenhum jogo com esse id.
    """
    doc = colecao.document(str(jogo_id)).get()

    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Jogo com id {jogo_id} não encontrado.",
        )

    return documento_para_dict(doc)
