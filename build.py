#!/usr/bin/env python3
"""Gerador do site do CCF/UFPR.

Lê os arquivos JSON em content/, monta as páginas HTML e grava tudo em dist/.
Usa apenas a biblioteca padrão do Python 3.8+ — não há dependências a instalar.

    python3 build.py           # gera dist/
    python3 build.py --serve   # gera e serve em http://localhost:8000
"""
import argparse
import datetime
import functools
import html
import http.server
import json
import math
import random
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
STATIC = ROOT / "static"
DIST = ROOT / "dist"

PAGES = [
    ("index.html", "Início"),
    ("sobre.html", "Sobre"),
    ("atuacao.html", "Atuação"),
    ("projetos.html", "Projetos"),
    ("laboratorios.html", "Laboratórios"),
    ("equipe.html", "Equipe"),
    ("contato.html", "Contato"),
]


def load(name):
    return json.loads((CONTENT / f"{name}.json").read_text(encoding="utf-8"))


def e(text):
    return html.escape(str(text), quote=True)


def pct(valor, total):
    p = valor / total * 100
    return "<1%" if 0 < p < 1 else f"{p:.0f}%"


def tel_href(phone):
    digits = re.sub(r"\D", "", phone)
    return f"tel:+55{digits}"


def arcs_svg(seed=7, size=640):
    """Arcos concêntricos no espírito do símbolo do CCF (digital + circuito)."""
    rnd = random.Random(seed)
    c = size / 2
    colors = ["#0b1215", "#0b1215", "#0d4a5c", "#17808c", "#14b89a"]
    parts = []
    r = 26
    while r < c - 10:
        angle = rnd.uniform(0, 360)
        end = angle + 360
        while angle < end - 20:
            span = rnd.uniform(18, 95)
            gap = rnd.uniform(8, 30)
            a0, a1 = math.radians(angle), math.radians(min(angle + span, end - 8))
            x0, y0 = c + r * math.cos(a0), c + r * math.sin(a0)
            x1, y1 = c + r * math.cos(a1), c + r * math.sin(a1)
            color = rnd.choice(colors)
            large = 1 if (a1 - a0) > math.pi else 0
            parts.append(
                f'<path d="M{x0:.1f} {y0:.1f}A{r:.0f} {r:.0f} 0 {large} 1 {x1:.1f} {y1:.1f}" stroke="{color}"/>'
            )
            if rnd.random() < 0.28:
                parts.append(f'<circle cx="{x1:.1f}" cy="{y1:.1f}" r="5.5" fill="{color}"/>')
            angle += span + gap
        r += 23
    return (
        f'<svg class="arcs" viewBox="0 0 {size} {size}" aria-hidden="true" focusable="false">'
        f'<g fill="none" stroke-width="4.5" stroke-linecap="round">{"".join(parts)}</g></svg>'
    )


def layout(site, current, title, description, body):
    atual = ' aria-current="page"'
    nav = "".join(
        f'<li><a href="{href}"{atual if href == current else ""}>{e(label)}</a></li>'
        for href, label in PAGES
    )
    c = site["contato"]
    full_title = site["nome"] + " — UFPR" if current == "index.html" else f"{title} — CCF/UFPR"
    year = datetime.date.today().year
    endereco = "<br>".join(e(l) for l in c["endereco"])
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(description)}">
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:type" content="website">
<meta property="og:locale" content="pt_BR">
<link rel="icon" type="image/png" href="img/favicon.png">
<link rel="stylesheet" href="css/style.css">
</head>
<body>
<a class="skip" href="#conteudo">Pular para o conteúdo</a>
<header class="topo">
  <div class="wrap topo-in">
    <a class="marca" href="index.html" aria-label="{e(site['nome'])} — página inicial">
      <img src="img/logo-ccf.png" alt="{e(site['nome'])}" width="170" height="80">
    </a>
    <button class="menu-btn" type="button" aria-expanded="false" aria-controls="menu">Menu</button>
    <nav id="menu" aria-label="Principal"><ul>{nav}</ul></nav>
  </div>
</header>
<main id="conteudo">
{body}
</main>
<footer class="rodape">
  <div class="wrap rodape-in">
    <div>
      <img src="img/logo-ccf-claro.png" alt="{e(site['nome'])}" width="190" height="90">
      <p>{e(site['vinculo'])}<br>{e(site['instituicao'])}</p>
    </div>
    <div>
      <h2>Contato</h2>
      <p><a href="mailto:{e(c['email'])}">{e(c['email'])}</a><br>
      <a href="{tel_href(c['telefone'])}">{e(c['telefone'])}</a></p>
      <p>{endereco}</p>
    </div>
    <div>
      <h2>Navegação</h2>
      <ul>{nav}</ul>
    </div>
  </div>
  <div class="wrap rodape-fim">
    <span>© {year} {e(site['nome'])} — {e(site['instituicao'])}</span>
    <a href="https://ufpr.br/">ufpr.br</a>
  </div>
</footer>
<script src="js/main.js" defer></script>
</body>
</html>
"""


def page_head(etiqueta, titulo, texto=""):
    lede = f'<p class="lede">{e(texto)}</p>' if texto else ""
    return f"""<section class="cabeca">
  <div class="wrap">
    <p class="etiqueta">{e(etiqueta)}</p>
    <h1>{e(titulo)}</h1>
    {lede}
  </div>
</section>"""


# ---------------------------------------------------------------- páginas

def render_index(site, areas, labs, projetos, numeros):
    h = site["hero"]
    fatos = [
        ("1º", "centro multidisciplinar de ciências forenses criado em ambiente acadêmico no Brasil"),
        (str(len(areas)), "áreas de atuação"),
        (str(len(labs)), "laboratórios integrados"),
        ("2020", "ano de inauguração"),
    ]
    fatos_html = "".join(f"<div><dt>{e(v)}</dt><dd>{e(t)}</dd></div>" for v, t in fatos)
    pilares = "".join(
        f"<li><h3>{e(p['titulo'])}</h3><p>{e(p['texto'])}</p></li>" for p in site["pilares"]
    )
    areas_html = "".join(
        f'<li><a href="atuacao.html#{e(a["id"])}"><span class="num">{i:02d}</span>'
        f'<span>{e(a["titulo"])}</span></a></li>'
        for i, a in enumerate(areas, 1)
    )
    destaque = "".join(
        f'<article class="cartao"><p class="etiqueta">{e(p["area"])}</p><h3>{e(p["titulo"])}</h3>'
        f'<p>{e(p["texto"])}</p><p class="meta">{e(p["parceiros"])}</p></article>'
        for p in projetos if p.get("destaque")
    )
    total = sum(x["valor"] for x in numeros["analises_por_solicitante"])
    maior = max(x["valor"] for x in numeros["analises_por_solicitante"])
    barras = "".join(
        f'<li><span class="b-nome">{e(x["nome"])}</span>'
        f'<span class="b-trilho"><span class="b-barra" style="width:{max(x["valor"] / maior * 100, 0.6):.1f}%"></span></span>'
        f'<span class="b-valor">{x["valor"]} <small>{e(pct(x["valor"], total))}</small></span></li>'
        for x in numeros["analises_por_solicitante"]
    )
    amostras = "".join(f"<li>{e(t)}</li>" for t in numeros["tipos_de_amostra"])
    formacao = "".join(
        f"<div><dt>{e(f['valor'])}</dt><dd>{e(f['rotulo'])}</dd></div>" for f in numeros["formacao"]
    )
    parceiros = "".join(
        f"<li><strong>{e(p['nome'])}</strong><span>{e(p['detalhe'])}</span></li>" for p in site["parceiros"]
    )
    noticias = "".join(
        f'<li><a href="{e(n["url"])}" rel="noopener"><span class="meta">{e(n["data"])} · {e(n["veiculo"])}</span>'
        f'<span class="n-titulo">{e(n["titulo"])}</span></a></li>'
        for n in site["noticias"]
    )
    return f"""<section class="hero">
  <div class="wrap hero-in">
    <div class="hero-txt">
      <p class="etiqueta">{e(h['etiqueta'])}</p>
      <h1>{e(h['titulo'])}</h1>
      <p class="lede">{e(h['texto'])}</p>
      <p class="acoes">
        <a class="btn" href="atuacao.html">Conheça as áreas de atuação</a>
        <a class="btn btn-sec" href="contato.html">Fale com o CCF</a>
      </p>
    </div>
    <div class="hero-arte">{arcs_svg()}</div>
  </div>
  <div class="wrap"><dl class="fatos">{fatos_html}</dl></div>
</section>

<section class="secao">
  <div class="wrap">
    <p class="etiqueta">Pilares</p>
    <h2>Cinco frentes sustentam o trabalho do Centro</h2>
    <ol class="pilares">{pilares}</ol>
  </div>
</section>

<section class="secao secao-tinta">
  <div class="wrap">
    <p class="etiqueta">Atuação</p>
    <h2>Nove áreas, da molécula ao mapa</h2>
    <ul class="areas-lista">{areas_html}</ul>
  </div>
</section>

<section class="secao">
  <div class="wrap">
    <p class="etiqueta">Projetos</p>
    <h2>Casos em que a universidade apoiou a perícia</h2>
    <div class="grade-3">{destaque}</div>
    <p class="mais"><a href="projetos.html">Ver todos os projetos →</a></p>
  </div>
</section>

<section class="secao secao-clara">
  <div class="wrap numeros">
    <div>
      <p class="etiqueta">O CCF em números</p>
      <h2>{total} análises de {e(numeros['periodo'])}</h2>
      <p>Mais de dois terços das análises atenderam a pedidos da Polícia Federal.</p>
      <ul class="barras" aria-label="Análises por solicitante">{barras}</ul>
      <p class="meta">Fonte: {e(numeros['fonte'])}.</p>
    </div>
    <div>
      <h3>Tipos de amostra analisados</h3>
      <ul class="chips">{amostras}</ul>
      <h3>Formação e difusão</h3>
      <dl class="mini-fatos">{formacao}</dl>
    </div>
  </div>
</section>

<section class="secao">
  <div class="wrap duas">
    <div>
      <p class="etiqueta">Parcerias</p>
      <h2>Academia e criminalística lado a lado</h2>
      <ul class="parceiros">{parceiros}</ul>
    </div>
    <div>
      <p class="etiqueta">Na imprensa</p>
      <h2>O CCF em pauta</h2>
      <ul class="noticias">{noticias}</ul>
    </div>
  </div>
</section>

<section class="chamada">
  <div class="wrap chamada-in">
    <h2>Precisa de apoio técnico-científico ou quer integrar um laboratório ao Centro?</h2>
    <a class="btn btn-claro" href="contato.html">Entre em contato</a>
  </div>
</section>"""


def render_sobre(site):
    linha = "".join(
        f'<li><p class="quando">{e(h["quando"])}</p><h3>{e(h["titulo"])}</h3><p>{e(h["texto"])}</p></li>'
        for h in site["historia"]
    )
    objetivos = "".join(
        f"<li><h3>{e(o['titulo'])}</h3><p>{e(o['texto'])}</p></li>" for o in site["objetivos"]
    )
    docs = "".join(
        f'<li><a href="{e(d["url"])}" rel="noopener">{e(d["titulo"])} <span class="meta">{e(d["formato"])}</span></a></li>'
        for d in site["documentos"]
    )
    return page_head(
        "Sobre o CCF",
        "Um centro em rede, formado por laboratórios que já trabalhavam com a perícia",
        "O CCF nasceu no Setor de Ciências Exatas da UFPR, a partir de demandas e parcerias com a Polícia "
        "Científica do Paraná e a Polícia Federal. Funciona como órgão auxiliar do Setor, com regimento próprio.",
    ) + f"""
<section class="secao">
  <div class="wrap duas">
    <div>
      <p class="etiqueta">Missão</p>
      <p class="citacao">{e(site['missao'])}</p>
    </div>
    <div>
      <p class="etiqueta">Como funciona</p>
      <p>O Centro não é um prédio: é a articulação de laboratórios consolidados da universidade, cada um com
      seu foco de pesquisa, que passam a responder em conjunto a demandas forenses. Essa integração permite
      combinar, em um mesmo caso, química analítica, geologia, computação, física e geoprocessamento.</p>
      <p>Novos laboratórios interessados em participar podem procurar o Comitê Gestor por meio da coordenação.</p>
    </div>
  </div>
</section>

<section class="secao secao-clara">
  <div class="wrap">
    <p class="etiqueta">Objetivos</p>
    <h2>O que o Centro se propõe a fazer</h2>
    <ul class="objetivos">{objetivos}</ul>
  </div>
</section>

<section class="secao">
  <div class="wrap">
    <p class="etiqueta">História</p>
    <h2>Linha do tempo</h2>
    <ol class="linha">{linha}</ol>
  </div>
</section>

<section class="secao secao-clara" id="documentos">
  <div class="wrap">
    <p class="etiqueta">Documentos</p>
    <h2>Publicações institucionais</h2>
    <ul class="docs">{docs}</ul>
  </div>
</section>"""


def render_atuacao(areas, labs):
    by_id = {l["id"]: l for l in labs}
    blocos = []
    for i, a in enumerate(areas, 1):
        ls = "".join(
            f'<li><a href="laboratorios.html#{e(k)}">{e(by_id[k]["sigla"])}</a></li>' for k in a["laboratorios"]
        )
        blocos.append(
            f'<article class="area" id="{e(a["id"])}"><span class="num">{i:02d}</span>'
            f'<div><h2>{e(a["titulo"])}</h2><p>{e(a["texto"])}</p>'
            f'<ul class="chips chips-link" aria-label="Laboratórios relacionados">{ls}</ul></div></article>'
        )
    return page_head(
        "Áreas de atuação",
        "Nove áreas em que o CCF pesquisa, analisa e forma profissionais",
        "Cada área reúne laboratórios de departamentos diferentes. Os laboratórios indicados são os mais "
        "diretamente relacionados a cada tema.",
    ) + f'<section class="secao"><div class="wrap areas">{"".join(blocos)}</div></section>'


def render_projetos(projetos):
    itens = "".join(
        f'<article class="cartao"><p class="etiqueta">{e(p["area"])}</p><h2>{e(p["titulo"])}</h2>'
        f'<p>{e(p["texto"])}</p><p class="meta">{e(p["parceiros"])}</p></article>'
        for p in projetos
    )
    return page_head(
        "Projetos",
        "Pesquisa aplicada a casos e demandas reais",
        "Uma seleção de projetos e casos em que laboratórios do CCF atuaram com órgãos de perícia e de investigação.",
    ) + f'<section class="secao"><div class="wrap grade-2">{itens}</div></section>'


def render_labs(labs):
    itens = []
    for l in labs:
        link = (
            f'<p><a href="{e(l["url"])}" rel="noopener">Site do laboratório →</a></p>' if l.get("url") else ""
        )
        itens.append(
            f'<article class="cartao lab" id="{e(l["id"])}"><p class="etiqueta">{e(l["unidade"])}</p>'
            f'<h2><span class="sigla">{e(l["sigla"])}</span> {e(l["nome"])}</h2><p>{e(l["texto"])}</p>{link}</article>'
        )
    return page_head(
        "Infraestrutura",
        f"{len(labs)} laboratórios da UFPR compõem o parque do CCF",
        "Laboratórios equipados e pesquisadores de sete áreas do conhecimento, aptos a atuar em diferentes "
        "campos das ciências forenses.",
    ) + f'<section class="secao"><div class="wrap grade-2">{"".join(itens)}</div></section>'


def render_equipe(equipe):
    coord = "".join(
        f'<li><strong>{e(p["nome"])}</strong><span>{e(p["papel"])} · {e(p["area"])}</span></li>'
        for p in equipe["coordenacao"]
    )
    comite = "".join(
        f'<li><strong>{e(p["nome"])}</strong><span>{e(p["area"])}</span></li>' for p in equipe["comite"]
    )
    return page_head(
        "Equipe",
        "Coordenação e Comitê Gestor",
        "O Comitê Gestor reúne representantes dos laboratórios que integram o Centro.",
    ) + f"""
<section class="secao">
  <div class="wrap">
    <h2>Coordenação</h2>
    <ul class="pessoas">{coord}</ul>
    <h2>Comitê Gestor</h2>
    <ul class="pessoas">{comite}</ul>
  </div>
</section>"""


def render_contato(site):
    c = site["contato"]
    endereco = "<br>".join(e(l) for l in c["endereco"])
    return page_head(
        "Contato",
        "Fale com o CCF",
        "Pedidos de análise, propostas de cooperação, imprensa e laboratórios interessados em integrar o Centro.",
    ) + f"""
<section class="secao">
  <div class="wrap duas">
    <div class="contato-bloco">
      <h2>Canais</h2>
      <dl class="contato">
        <div><dt>E-mail</dt><dd><a href="mailto:{e(c['email'])}">{e(c['email'])}</a></dd></div>
        <div><dt>Telefone</dt><dd><a href="{tel_href(c['telefone'])}">{e(c['telefone'])}</a></dd></div>
        <div><dt>Endereço</dt><dd>{endereco}</dd></div>
      </dl>
    </div>
    <div>
      <h2>Como podemos ajudar</h2>
      <ul class="lista">
        <li><strong>Órgãos de perícia e de investigação.</strong> Descreva a demanda e o tipo de amostra ou de
        evidência; a coordenação indica o laboratório mais adequado.</li>
        <li><strong>Laboratórios da UFPR.</strong> Grupos interessados em integrar o Centro podem escrever
        à coordenação, que leva o pedido ao Comitê Gestor.</li>
        <li><strong>Estudantes.</strong> Há disciplinas e linhas de pesquisa em ciências forenses na graduação
        e na pós-graduação; consulte os laboratórios para oportunidades de orientação.</li>
        <li><strong>Imprensa.</strong> Pedidos de entrevista devem ser enviados por e-mail.</li>
      </ul>
      <p><a class="btn" href="mailto:{e(c['email'])}">Escrever para {e(c['email'])}</a></p>
    </div>
  </div>
</section>"""


def render_404():
    return page_head("Erro 404", "Página não encontrada", "O endereço pode ter mudado com a atualização do site.") + (
        '<section class="secao"><div class="wrap"><p><a class="btn" href="index.html">Ir para a página inicial</a></p></div></section>'
    )


# ---------------------------------------------------------------- build

def check_links(pages):
    """Falha o build se algum link interno apontar para página ou âncora inexistente."""
    ids = {name: set(re.findall(r'\bid="([^"]+)"', htm)) for name, htm in pages.items()}
    errors = []
    for name, htm in pages.items():
        for href in re.findall(r'href="([^"]+)"', htm):
            if re.match(r"^(https?:|mailto:|tel:|#)", href):
                continue
            target, _, anchor = href.partition("#")
            if target.endswith(".html"):
                if target not in pages:
                    errors.append(f"{name}: página inexistente {href}")
                elif anchor and anchor not in ids[target]:
                    errors.append(f"{name}: âncora inexistente {href}")
            elif not (STATIC / target).exists():
                errors.append(f"{name}: arquivo inexistente {href}")
    return errors


def build():
    site, areas, labs = load("site"), load("areas"), load("laboratorios")
    projetos, equipe, numeros = load("projetos"), load("equipe"), load("numeros")

    lab_ids = {l["id"] for l in labs}
    for a in areas:
        missing = set(a["laboratorios"]) - lab_ids
        if missing:
            sys.exit(f"content/areas.json: laboratório desconhecido em '{a['id']}': {sorted(missing)}")

    d = site["descricao"]
    bodies = {
        "index.html": ("Início", d, render_index(site, areas, labs, projetos, numeros)),
        "sobre.html": ("Sobre", "História, missão, objetivos e documentos do CCF/UFPR.", render_sobre(site)),
        "atuacao.html": ("Atuação", "As nove áreas de atuação do CCF/UFPR.", render_atuacao(areas, labs)),
        "projetos.html": ("Projetos", "Projetos e casos com participação do CCF/UFPR.", render_projetos(projetos)),
        "laboratorios.html": ("Laboratórios", "Laboratórios que integram o CCF/UFPR.", render_labs(labs)),
        "equipe.html": ("Equipe", "Coordenação e Comitê Gestor do CCF/UFPR.", render_equipe(equipe)),
        "contato.html": ("Contato", "Como entrar em contato com o CCF/UFPR.", render_contato(site)),
        "404.html": ("Página não encontrada", d, render_404()),
    }
    pages = {name: layout(site, name, t, desc, body) for name, (t, desc, body) in bodies.items()}

    errors = check_links(pages)
    if errors:
        sys.exit("Links quebrados:\n  " + "\n  ".join(errors))

    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(STATIC, DIST)
    for name, htm in pages.items():
        (DIST / name).write_text(htm, encoding="utf-8")
    (DIST / ".nojekyll").write_text("", encoding="utf-8")
    print(f"OK: {len(pages)} páginas geradas em {DIST.relative_to(ROOT)}/")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--serve", action="store_true", help="serve dist/ em http://localhost:8000 após gerar")
    args = ap.parse_args()
    build()
    if args.serve:
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DIST))
        print("Servindo em http://localhost:8000 (Ctrl+C para sair)")
        http.server.ThreadingHTTPServer(("127.0.0.1", 8000), handler).serve_forever()
