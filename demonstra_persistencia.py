#!/usr/bin/env python3
"""
demonstra_persistencia.py — Comprova que os registros continuam no
Cloud Firestore mesmo após a reinicialização da aplicação.

Uso:
    python3 demonstra_persistencia.py

Como funciona:
    1. Verifica se a API está no ar.
    2. Se o jogo de demonstração (id fixo, ex.: 777) ainda não existir,
       cria-o via POST /jogos (201 Created) — ele é gravado no Firestore.
    3. Mostra a listagem atual (GET /jogos).
    4. PEDE PARA VOCÊ REINICIAR o servidor (Ctrl+C no uvicorn e iniciar
       novamente: uvicorn main:app --reload). Enquanto isso, o documento
       continua salvo no Firestore.
    5. Após reiniciar, o script consulta o mesmo registro (GET /jogos/777)
       e compara com o que foi criado — comprovando a persistência.

Obs.: o script usa apenas a biblioteca padrão (urllib).
"""

import json
import sys
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"

# Jogo fixo usado na demonstração (id propositalmente "redondo" para
# facilitar a consulta manual em /docs e no console do Firestore)
JOGO_DEMO = {
    "id": 777,
    "titulo": "Hollow Knight",
    "genero": "Aventura",
    "plataforma": "PC",
    "ano_lancamento": 2017,
}


def chamada(method, path, body=None):
    url = BASE + path
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8"))
        except json.JSONDecodeError:
            return e.code, None
    except urllib.error.URLError:
        print(f"[ERRO] Não foi possível conectar à API em {BASE}.")
        print("       Certifique-se de que ela está rodando: uvicorn main:app --reload")
        sys.exit(1)


def aguardar_enter(mensagem):
    input(mensagem)


def main():
    print("=" * 70)
    print("  DEMONSTRAÇÃO DE PERSISTÊNCIA — Cloud Firestore")
    print("=" * 70)

    # ------------------------------------------------------------------
    # 1) API online?
    # ------------------------------------------------------------------
    status, _ = chamada("GET", "/openapi.json")
    print(f"\n[1] API online (GET /openapi.json -> {status})")

    # ------------------------------------------------------------------
    # 2) Cria o jogo de demonstração se ele ainda não existir
    # ------------------------------------------------------------------
    print(f"\n[2] Verificando se o jogo {JOGO_DEMO['id']} já existe...")
    status, existente = chamada("GET", f"/jogos/{JOGO_DEMO['id']}")

    if status == 200:
        print(f"    Já existe (criado em uma execução anterior) -> {existente}")
    else:
        print(f"    Não existe (GET -> {status}). Criando via POST /jogos...")
        status, criado = chamada("POST", "/jogos", JOGO_DEMO)
        print(f"    POST /jogos -> {status} Created")
        print(f"    Registro gravado no Firestore: {json.dumps(criado, ensure_ascii=False)}")

    # ------------------------------------------------------------------
    # 3) Listagem atual (deve conter o jogo 777)
    # ------------------------------------------------------------------
    print("\n[3] Listagem atual — GET /jogos")
    status, lista = chamada("GET", "/jogos")
    print(f"    GET /jogos -> {status}")
    for j in lista:
        marcador = "  <-- jogo da demonstração" if j["id"] == JOGO_DEMO["id"] else ""
        print(f"      {j}{marcador}")

    # ------------------------------------------------------------------
    # 4) Reinício da aplicação
    # ------------------------------------------------------------------
    print("\n" + "-" * 70)
    aguardar_enter(
        "    [4] AGORA REINICIE A APLICAÇÃO:\n"
        "        1. Pare o servidor (Ctrl+C no terminal do uvicorn);\n"
        "        2. Inicie novamente:  uvicorn main:app --reload;\n"
        "        3. Volte aqui e pressione Enter para continuar.\n"
        "    Pressione Enter depois de reiniciar a API... "
    )

    # ------------------------------------------------------------------
    # 5) Consulta após o reinício — comprova a persistência
    # ------------------------------------------------------------------
    print(f"\n[5] Consultando o mesmo registro após o reinício — GET /jogos/{JOGO_DEMO['id']}")
    status, consultado = chamada("GET", f"/jogos/{JOGO_DEMO['id']}")

    if status == 200 and consultado == JOGO_DEMO:
        print(f"    GET /jogos/{JOGO_DEMO['id']} -> {status} OK")
        print(f"    Registro encontrado: {json.dumps(consultado, ensure_ascii=False)}")
        print("\n" + "=" * 70)
        print("  PERSISTÊNCIA COMPROVADA!")
        print("    O registro criado pela API continuou disponível no")
        print("    Cloud Firestore mesmo após a reinicialização da aplicação.")
        print("=" * 70)
        sys.exit(0)
    else:
        print(f"    GET /jogos/{JOGO_DEMO['id']} -> {status}")
        print("    [FALHA] O registro não foi encontrado após o reinício.")
        print("    Verifique se o Firestore está configurado corretamente.")
        sys.exit(1)


if __name__ == "__main__":
    main()
