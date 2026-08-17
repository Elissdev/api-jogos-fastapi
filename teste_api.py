#!/usr/bin/env python3
"""
teste_api.py — Testa automaticamente todos os cenários da API de Jogos
integrada ao Cloud Firestore.

Uso:
    python3 teste_api.py

Requisitos:
    - A API deve estar rodando em http://127.0.0.1:8000
      (inicie com: uvicorn main:app --reload)
    - O Firestore deve estar configurado (credencial real ou emulador)

O script usa apenas a biblioteca padrão do Python (urllib),
não precisa instalar nada.
"""

import json
import random
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8000"

PASS = 0
FAIL = 0


def chamada(method, path, body=None, params=None):
    """Faz uma requisição HTTP e retorna (status, dados_JSON)."""
    if params:
        path = path + "?" + urllib.parse.urlencode(params)
    url = BASE + path
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, raw
    except urllib.error.URLError:
        print(f"\n  [ERRO] Nao foi possivel conectar ao servidor em {BASE}")
        print("     Certifique-se de que a API está rodando:")
        print('     uvicorn main:app --reload\n')
        sys.exit(1)


def verificar(nome, condicao, detalhe=""):
    """Registra um teste como PASS ou FAIL e imprime o resultado."""
    global PASS, FAIL
    if condicao:
        PASS += 1
        print(f"  [PASS] {nome}")
    else:
        FAIL += 1
        print(f"  [FAIL] {nome} {detalhe}")


def id_inexistente(lista):
    """Gera um id que certamente não existe na coleção atual."""
    while True:
        novo = random.randint(1_000_000, 99_999_999)
        if all(j["id"] != novo for j in lista):
            return novo


def main():
    global PASS, FAIL
    print("=" * 62)
    print("  TESTE AUTOMÁTICO — API de Jogos (FastAPI + Firestore)")
    print(f"  Servidor: {BASE}")
    print("=" * 62)

    # ------------------------------------------------------------------
    # 0) Servidor online
    # ------------------------------------------------------------------
    print("\n[0] Servidor online")
    status, _ = chamada("GET", "/openapi.json")
    verificar("GET /openapi.json responde", status == 200)

    # ------------------------------------------------------------------
    # 1) Criar registros (POST) — gravados no Firestore
    # ------------------------------------------------------------------
    print("\n[1] Criar registros — POST /jogos (persistidos no Firestore)")

    jogo_a = {
        "id": id_inexistente([]),
        "titulo": "Mario Kart 8 Deluxe",
        "genero": "Corrida",
        "plataforma": "Nintendo Switch",
        "ano_lancamento": 2017,
    }
    jogo_b = {
        "id": id_inexistente([jogo_a]),
        "titulo": "Elden Ring",
        "genero": "RPG",
        "plataforma": "PC",
        "ano_lancamento": 2022,
    }

    status, resp = chamada("POST", "/jogos", jogo_a)
    verificar("POST /jogos retorna 201 Created", status == 201, f"(veio {status})")
    verificar("POST /jogos retorna o jogo criado", resp == jogo_a)

    status, _ = chamada("POST", "/jogos", jogo_b)
    verificar("Segundo POST /jogos retorna 201 Created", status == 201, f"(veio {status})")

    # ------------------------------------------------------------------
    # 2) Id duplicado (POST) -> 409
    # ------------------------------------------------------------------
    print("\n[2] Id duplicado — POST /jogos (mesmo id)")
    status, resp = chamada("POST", "/jogos", jogo_a)
    verificar("Id duplicado retorna 409 Conflict", status == 409, f"(veio {status})")
    verificar("Mensagem de erro explicativa", "detail" in resp)

    # ------------------------------------------------------------------
    # 3) Listar todos (GET) — sem parâmetro de consulta
    # ------------------------------------------------------------------
    print("\n[3] Listar todos — GET /jogos (sem parâmetro)")
    status, lista = chamada("GET", "/jogos")
    verificar("GET /jogos retorna 200 OK", status == 200, f"(veio {status})")
    verificar("Retorna uma lista", isinstance(lista, list))
    verificar("Contém os jogos criados no teste",
              any(j["id"] == jogo_a["id"] for j in lista)
              and any(j["id"] == jogo_b["id"] for j in lista))
    verificar("Cada item é um dict com 'id'",
              all(isinstance(j, dict) and "id" in j for j in lista))

    # ------------------------------------------------------------------
    # 4) Filtro por gênero (parâmetro de consulta opcional)
    # ------------------------------------------------------------------
    print("\n[4] Filtrar — GET /jogos?genero=...")
    status, filtrados = chamada("GET", "/jogos", params={"genero": jogo_a["genero"]})
    verificar("GET /jogos?genero=... retorna 200 OK", status == 200, f"(veio {status})")
    verificar("Só retorna jogos do gênero pedido",
              all(j["genero"] == jogo_a["genero"] for j in filtrados))
    verificar("O jogo do gênero pedido está presente",
              any(j["id"] == jogo_a["id"] for j in filtrados))
    verificar("Jogo de outro gênero NÃO aparece",
              all(j["id"] != jogo_b["id"] for j in filtrados))

    status, vazio = chamada("GET", "/jogos", params={"genero": "GêneroInexistenteXYZ"})
    verificar("Gênero inexistente retorna lista vazia []",
              status == 200 and vazio == [])

    status, minusculo = chamada("GET", "/jogos", params={"genero": jogo_a["genero"].lower()})
    verificar("Filtro ignora maiúsculas/minúsculas",
              status == 200 and any(j["id"] == jogo_a["id"] for j in minusculo))

    # ------------------------------------------------------------------
    # 5) Consultar por ID (parâmetro de caminho)
    # ------------------------------------------------------------------
    print("\n[5] Consultar por id — GET /jogos/{id}")
    status, resp = chamada("GET", f"/jogos/{jogo_a['id']}")
    verificar("GET /jogos/{id} retorna 200 OK", status == 200, f"(veio {status})")
    verificar("Retorna o registro correto", resp == jogo_a)

    inexistente = id_inexistente(lista)
    status, resp = chamada("GET", f"/jogos/{inexistente}")
    verificar(f"GET /jogos/{inexistente} retorna 404 Not Found",
              status == 404, f"(veio {status})")
    verificar("Mensagem de erro explicativa", "detail" in resp)

    # ------------------------------------------------------------------
    # 6) Validação de dados (POST com JSON inválido) -> 422
    # ------------------------------------------------------------------
    print("\n[6] Validação — POST /jogos com dados inválidos")
    status, _ = chamada("POST", "/jogos", {"id": id_inexistente(lista), "titulo": "Sem gênero"})
    verificar("Campos obrigatórios faltando retorna 422", status == 422, f"(veio {status})")

    status, _ = chamada("POST", "/jogos", {"id": "não-numérico", "titulo": "X",
                                           "genero": "Y", "plataforma": "Z",
                                           "ano_lancamento": "não-numérico"})
    verificar("Tipos incorretos retornam 422", status == 422, f"(veio {status})")

    # ------------------------------------------------------------------
    # Resumo
    # ------------------------------------------------------------------
    print("\n" + "=" * 62)
    print(f"  RESULTADO: {PASS} passaram | {FAIL} falharam")
    if FAIL == 0:
        print("  Tudo funcionando! A API esta 100% funcional.")
    else:
        print("  ATENCAO: alguns testes falharam — revise o codigo da API.")
    print("=" * 62)
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
