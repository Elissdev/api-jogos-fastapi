"""
Script auxiliar: automatiza a interface /docs (Swagger UI) no Chrome
headless e captura screenshots demonstrando os testes das rotas e a
persistência no Cloud Firestore.

Capturas geradas (execução padrão):
    01_docs_visao_geral.png              -> visão geral das rotas
    02_post_jogos_201_created.png        -> criar registro (201)
    03_get_jogos_lista_200.png           -> listar todos (200)
    04_get_jogos_filtro_genero.png       -> filtro por gênero (200)
    05_get_jogos_id_200.png              -> consulta por id (200)
    06_get_jogos_id_404_not_found.png    -> id inexistente (404)
    07_firestore_documento.png           -> documento na coleção (emulador/console)

Execução para comprovar a persistência (após REINICIAR a aplicação):
    python3 capturar_docs.py --so-persistencia
    08_persistencia_apos_reinicio.png    -> consulta após reiniciar a aplicação

Requisitos:
    - API rodando em http://127.0.0.1:8000
    - Emulador Firestore (UI) em http://127.0.0.1:4001/firestore  (opcional,
      usado na captura 07; para Firestore real, use o Console do Firebase)
"""
import sys
import time
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000/docs"
EMULADOR_UI = "http://127.0.0.1:4001/firestore"
OUT = "/home/elissandrareis/Área de Trabalho/ATIVIDADE PRÁTICA – UNIDADE IV/capturas"

# Jogo usado na demonstração de persistência (mesmo id do
# demonstra_persistencia.py)
JOGO_DEMO = {
    "id": 777,
    "titulo": "Hollow Knight",
    "genero": "Aventura",
    "plataforma": "PC",
    "ano_lancamento": 2017,
}


def shot(page, name):
    page.screenshot(path=f"{OUT}/{name}.png", full_page=False)
    print(f"salvo: {OUT}/{name}.png")


def click_try_it(page, op_id):
    page.locator(f"#{op_id}").click()  # expande a operação
    page.wait_for_timeout(600)
    page.locator(f"#{op_id} button.btn.try-out__btn").click()  # Try it out
    page.wait_for_timeout(600)


def execute(page, op_id):
    page.locator(f"#{op_id} button.btn.execute").click()
    # aguarda a resposta aparecer
    page.wait_for_selector(f"#{op_id} .responses-wrapper table.live-responses-table",
                           timeout=15000)
    page.wait_for_timeout(1500)


def preencher_body(page, op_id, dicionario):
    import json
    corpo = json.dumps(dicionario, ensure_ascii=False, indent=2)
    page.locator(f"#{op_id} textarea.body-param__text").fill(corpo)


with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    ctx = browser.new_context(viewport={"width": 1440, "height": 950})
    page = ctx.new_page()

    # Modo --so-persistencia: captura apenas a consulta feita APÓS a
    # reinicialização da aplicação (o registro 777 deve já existir).
    if "--so-persistencia" in sys.argv:
        page.goto(BASE)
        page.wait_for_selector("h1", timeout=15000)
        page.wait_for_timeout(1500)
        op = "operations-default-consultar_jogo_jogos__jogo_id__get"
        click_try_it(page, op)
        page.locator(f"#{op} input[placeholder='jogo_id']").fill(str(JOGO_DEMO["id"]))
        execute(page, op)
        shot(page, "08_persistencia_apos_reinicio")
        browser.close()
        print("Concluído!")
        sys.exit(0)

    # ------------------------------------------------------------------
    # 1) Página inicial do /docs (visão geral das rotas)
    # ------------------------------------------------------------------
    page.goto(BASE)
    page.wait_for_selector("h1", timeout=15000)
    page.wait_for_timeout(2000)
    shot(page, "01_docs_visao_geral")

    # ------------------------------------------------------------------
    # 2) POST /jogos -> 201 Created (jogo da demonstração de persistência)
    # ------------------------------------------------------------------
    op = "operations-default-criar_jogo_jogos_post"
    click_try_it(page, op)
    preencher_body(page, op, JOGO_DEMO)
    execute(page, op)
    shot(page, "02_post_jogos_201_created")

    # ------------------------------------------------------------------
    # 3) POST /jogos -> mais registros (para a listagem)
    # ------------------------------------------------------------------
    preencher_body(page, op, {
        "id": 1, "titulo": "The Legend of Zelda: Tears of the Kingdom",
        "genero": "Aventura", "plataforma": "Nintendo Switch",
        "ano_lancamento": 2023,
    })
    execute(page, op)

    preencher_body(page, op, {
        "id": 2, "titulo": "God of War Ragnarök",
        "genero": "Ação", "plataforma": "PlayStation 5",
        "ano_lancamento": 2022,
    })
    execute(page, op)

    preencher_body(page, op, {
        "id": 3, "titulo": "Baldur's Gate 3",
        "genero": "RPG", "plataforma": "PC",
        "ano_lancamento": 2023,
    })
    execute(page, op)

    # ------------------------------------------------------------------
    # 4) GET /jogos -> lista todos (200 OK)
    # ------------------------------------------------------------------
    op = "operations-default-listar_jogos_jogos_get"
    click_try_it(page, op)
    execute(page, op)
    shot(page, "03_get_jogos_lista_200")

    # ------------------------------------------------------------------
    # 5) GET /jogos?genero=RPG -> filtro (200 OK)
    # ------------------------------------------------------------------
    page.locator(f"#{op} input[placeholder='genero']").fill("RPG")
    execute(page, op)
    shot(page, "04_get_jogos_filtro_genero")

    # ------------------------------------------------------------------
    # 6) GET /jogos/{jogo_id} -> id existente (200 OK)
    # ------------------------------------------------------------------
    op = "operations-default-consultar_jogo_jogos__jogo_id__get"
    click_try_it(page, op)
    page.locator(f"#{op} input[placeholder='jogo_id']").fill(str(JOGO_DEMO["id"]))
    execute(page, op)
    shot(page, "05_get_jogos_id_200")

    # ------------------------------------------------------------------
    # 7) GET /jogos/{jogo_id} -> id inexistente (404 Not Found)
    # ------------------------------------------------------------------
    page.locator(f"#{op} input[placeholder='jogo_id']").fill("999")
    execute(page, op)
    shot(page, "06_get_jogos_id_404_not_found")

    # ------------------------------------------------------------------
    # 8) Documento armazenado no Firestore (UI do emulador)
    #    Obs.: com um projeto Firebase real, o documento pode ser visto
    #    no Console do Firebase (Firestore Database > jogos > 777).
    # ------------------------------------------------------------------
    try:
        page.goto(EMULADOR_UI, wait_until="domcontentloaded")
        # aguarda a UI carregar a listagem de coleções/documentos
        page.wait_for_selector("text=jogos", timeout=15000)
        page.wait_for_timeout(5000)
        page.screenshot(path=f"{OUT}/07_firestore_documento.png", full_page=False)
        print(f"salvo: {OUT}/07_firestore_documento.png")
    except Exception as e:
        print(f"[aviso] não foi possível capturar a UI do emulador: {e}")

    browser.close()

print("Concluído!")
print()
print("Para comprovar a persistência:")
print("  1) REINICIE a aplicação (Ctrl+C no uvicorn e inicie novamente);")
print("  2) Execute:  python3 capturar_docs.py --so-persistencia")
print("  3) A captura 08_persistencia_apos_reinicio.png mostrará o")
print("     registro 777 ainda disponível após o reinício.")
