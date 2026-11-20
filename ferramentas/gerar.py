"""Gera o site estático da Nouvellando a partir de conteudo/.

Cada página do site atual vira site/<mesmo-caminho>/index.html, com o mesmo
título, descrição e texto, no design novo. As páginas de produto passam a
morar dentro da linha (/fio-original/805-805u/) e o endereço antigo
(/original-805-805u/) vira um redirecionamento para o novo.

Uso:
  python3 ferramentas/gerar.py              # versão de teste (noindex)
  python3 ferramentas/gerar.py --producao   # versão final, indexável, com sitemap

Só usa a biblioteca padrão do Python.
"""
import html
import json
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CONTEUDO = RAIZ / "conteudo"
SAIDA = RAIZ / "site"
PRODUCAO = "--producao" in sys.argv

SITE = json.loads((CONTEUDO / "site.json").read_text(encoding="utf-8"))
DOMINIO = SITE["dominio"]

# Fotos hospedadas no próprio site (geradas por ferramentas/otimizar-fotos.ps1 em
# wp-content/uploads/). Endereço do WordPress -> endereço da foto otimizada.
FOTOS_DIR = RAIZ / "wp-content"
_fotos = CONTEUDO / "fotos.json"
FOTOS = json.loads(_fotos.read_text(encoding="utf-8")) if _fotos.exists() else {}
FAVICON = "/wp-content/uploads/2022/12/cropped-logo-nouvellando_page-0001-1.jpg"
FOTOS_FALTANDO = set()

# Títulos e descrições escritos à mão para as páginas principais (o resto é montado
# automaticamente em descricao()). Chave: endereço da página.
_seo = CONTEUDO / "seo.json"
SEO = {k: v for k, v in json.loads(_seo.read_text(encoding="utf-8")).items()
       if k.startswith("/")} if _seo.exists() else {}

# Prefixo do endereço antigo do produto -> página da linha
PREFIXOS = {
    "original": "fio-original", "twinkle": "fio-twinkle", "stardust": "fio-stardust",
    "breezy": "fio-breezy", "aura": "fio-aura", "fluffinho": "fio-fluffinho",
    "boucle": "fio-boucle", "peluche": "fio-peluche", "paillettes": "fio-paillettes",
}
CATEGORIAS = {"fio-original", "fio-original-2", "fio-twinkle", "fio-stardust", "fio-breezy",
              "fio-aura", "fio-fluffinho", "fio-boucle", "fio-peluche", "fio-paillettes",
              "fio-ice", "fio-cor-unica", "novelos-sem-degrade", "fios-nouvellando"}

ICONES_CUIDADO = {
    "Lavagem à mão": "lavagem-mao.svg",
    "Secar na horizontal": "secar-horizontal.svg",
    "Secar na sombra": "secar-sombra.svg",
}

esc = html.escape


# ---------------------------------------------------------------- dados

def carrega_paginas():
    pags = {}
    for arq in sorted((CONTEUDO / "paginas").glob("*.json")):
        p = json.loads(arq.read_text(encoding="utf-8"))
        pags[p["slug"]] = p
    return pags


def folhas(blocos):
    for b in blocos:
        if b["tipo"] == "grupo":
            yield from folhas(b["blocos"])
        else:
            yield b


def links_do_bloco(b):
    if b.get("link"):
        yield b["link"]
    for s in b.get("slides", []):
        if s.get("link"):
            yield s["link"]
    for h in [b.get("html", "")] + [i.get("html", "") for i in b.get("itens", [])]:
        yield from re.findall(r'href="([^"]+)"', h)


def eh_produto(slug):
    return slug.split("-")[0] in PREFIXOS and slug not in CATEGORIAS


def mapa_produtos(pags):
    """Endereço antigo do produto -> endereço novo dentro da linha."""
    entradas = Counter()
    for p in pags.values():
        if p["slug"] in CATEGORIAS:
            for b in folhas(p["blocos"]):
                for l in links_do_bloco(b):
                    entradas[l] += 1
    grupos = defaultdict(list)
    for slug in pags:
        if not eh_produto(slug):
            continue
        prefixo, resto = slug.split("-", 1)
        base = re.sub(r"(-\d)+$", "", resto)
        grupos[(PREFIXOS[prefixo], base)].append(slug)

    novo, redireciona = {}, {}
    for (linha, base), slugs in grupos.items():
        # Página mais linkada pelas categorias fica com o endereço; as duplicadas redirecionam
        slugs.sort(key=lambda s: (-entradas[f"/{s}/"], len(s), s))
        destino = f"/{linha}/{base}/"
        novo[f"/{slugs[0]}/"] = destino
        for s in slugs[1:]:
            redireciona[f"/{s}/"] = destino
    return novo, redireciona


# ---------------------------------------------------------------- caminhos

class Ctx:
    def __init__(self, caminho, mapa):
        self.caminho = caminho
        self.prof = caminho.strip("/").count("/") + 1 if caminho != "/" else 0
        self.mapa = mapa

    def rel(self, destino):
        """Link relativo, para funcionar tanto no domínio quanto num endereço de teste."""
        if not destino.startswith("/") or destino.startswith("//"):
            return destino
        destino = self.mapa.get(destino, destino)
        pre = "../" * self.prof
        alvo = destino.lstrip("/")
        return (pre + alvo) or "./"

    def asset(self, nome):
        return "../" * self.prof + "assets/" + nome


def link_externo(href):
    return href.startswith("http") and not href.startswith(DOMINIO)


def a_attrs(href, ctx, extra=""):
    if not href:
        return ""
    alvo = ctx.rel(href)
    s = f' href="{esc(alvo)}"'
    if link_externo(href):
        s += ' target="_blank" rel="noopener"'
    return s + extra


def foto_local(src):
    """Endereço da foto otimizada no próprio site, ou None se ela não existir.
    As versões redimensionadas do WordPress (foto-300x300.jpg) usam a foto única."""
    if not src.startswith("/wp-content/"):
        return None
    base = re.sub(r"-\d+x\d+(\.[A-Za-z]+)$", r"\1", src)
    return FOTOS.get(base) or FOTOS.get(src)


def img_url(src, largura):
    local = foto_local(src)
    if local:
        return local
    if src.startswith("/wp-content/"):
        # Foto que ainda não foi otimizada: continua vindo do WordPress (avisado no fim)
        FOTOS_FALTANDO.add(re.sub(r"-\d+x\d+(\.[A-Za-z]+)$", r"\1", src))
        return f"https://i0.wp.com/nouvellando.com.br{src}?w={largura}&ssl=1"
    return src


def foto_do_card(img, link, ctx):
    """Card que leva a um produto mas cuja foto não existe mais (já quebrada no WordPress):
    usa a foto do próprio produto. Ex.: card 'Original 149' com 149.jpg -> Original-149.jpg."""
    if not img or not img.get("src", "").startswith("/wp-content/") or foto_local(img["src"]) or not link:
        return img
    destino = ctx.mapa.get(link, link)
    d = PRODUTOS.get(destino)
    if d and d.get("img") and foto_local(d["img"]):
        return {**img, "src": d["img"], "w": None, "h": None}
    return img


def img_tag(img, largura=600, classe="", lazy=True, ctx=None, sizes=None):
    if not img or not img.get("src"):
        return ""
    src = img["src"]
    # Sem texto alternativo no conteúdo: usa a legenda da foto (ex.: "Original 805 | 1200m+")
    alt = img.get("alt") or (img.get("legenda") or "").split("|")[0].strip()
    attrs = f'src="{esc(img_url(src, largura))}" alt="{esc(alt)}"'
    if src.startswith("/wp-content/") and not foto_local(src):
        attrs += f' srcset="{esc(img_url(src, largura // 2))} {largura // 2}w, {esc(img_url(src, largura))} {largura}w, {esc(img_url(src, largura * 2))} {largura * 2}w"'
        attrs += f' sizes="{sizes or f"(max-width: 600px) 100vw, {largura}px"}"'
    if img.get("w") and img.get("h"):
        attrs += f' width="{img["w"]}" height="{img["h"]}"'
    if lazy:
        attrs += ' loading="lazy" decoding="async"'
    if classe:
        attrs += f' class="{classe}"'
    return f"<img {attrs}>"


# ---------------------------------------------------------------- HTML dos textos

RE_PRECO = re.compile(r"^\s*\d[\d.,]*\s*m\b.*\|.*R\$", re.I)


def ajusta_html(h, ctx):
    def troca_link(m):
        href = html.unescape(m.group(1))
        return a_attrs(href, ctx)[1:] if href else m.group(0)

    h = re.sub(r'href="([^"]*)"(?:\s+target="_blank")?', troca_link, h)

    def troca_img(m):
        tag = m.group(0)
        src = re.search(r'src="([^"]*)"', tag)
        alt = re.search(r'alt="([^"]*)"', tag)
        src = html.unescape(src.group(1)) if src else ""
        alt = html.unescape(alt.group(1)) if alt else ""
        depois = h[m.end():m.end() + 40]
        if "s.w.org/images/core/emoji" in src:
            return esc(alt)
        for texto, arquivo in ICONES_CUIDADO.items():
            if depois.lstrip().startswith(texto):
                return f'<img class="ico-cuidado" src="{ctx.asset("icones/" + arquivo)}" alt="" width="22" height="22">'
        if src.startswith("/wp-content/"):
            return img_tag({"src": src, "alt": alt}, 600)
        if re.match(r"https?://(encrypted-tbn\d\.gstatic\.com|cdn-icons-png\.flaticon\.com)/", src):
            # Ícone copiado do Google Imagens/Flaticon que não foi reconhecido acima: já
            # dá erro e a página mostra os ícones de cuidado do próprio site
            return ""
        return f'<img src="{esc(src)}" alt="{esc(alt)}" loading="lazy">'

    h = re.sub(r"<img\b[^>]*>", troca_img, h)
    h = re.sub(r"<p>(\s|&nbsp;|\xa0)*</p>", "", h)
    return h


def tabela_precos(h):
    """Linhas "1000m | R$ 85,00 | ≅ 268g" viram uma tabela, com o mesmo texto."""
    paras = re.findall(r"<p>(.*?)</p>", h, re.S)
    resto = re.sub(r"<p>(.*?)</p>", "", h, flags=re.S).strip()
    if not paras or resto:
        return None
    linhas = []
    for p in paras:
        for l in re.split(r"<br\s*/?>", p):
            l = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", l)).strip()
            if l and l != "\xa0":
                linhas.append(l)
    if not linhas or not all(RE_PRECO.match(l) for l in linhas):
        return None
    corpo = "".join(
        "<tr>" + "".join(f"<td>{c.strip()}</td>" for c in l.split("|")) + "</tr>" for l in linhas)
    return f'<table class="precos"><tbody>{corpo}</tbody></table>'


# ---------------------------------------------------------------- blocos

def cls_oculto(b):
    m = {"desktop": "hide-d", "tablet": "hide-t", "mobile": "hide-m"}
    return " ".join(m[x] for x in b.get("oculto", []))


def junta(*classes):
    return " ".join(c for c in classes if c)


def r_carrossel(b, ctx, largura=600, variante=""):
    slides = b.get("slides", [])
    if not slides:
        return ""
    card = any(s.get("link") for s in slides) and any(s.get("legenda") for s in slides)
    por = b.get("por_tela", {})
    estilo = ""
    if por:
        d = por.get("desktop", 1)
        estilo = (f' style="--por-d:{d};--por-t:{por.get("tablet", min(d, 2))};'
                  f'--por-m:{por.get("mobile", 1)}"')
    itens = []
    for i, s in enumerate(slides):
        s = foto_do_card(s, s.get("link"), ctx)
        fig = img_tag(s, largura, lazy=(i > 0 or variante != "hero"))
        if s.get("link"):
            fig = f'<a class="carrossel__img"{a_attrs(s["link"], ctx)}>{fig}</a>'
        else:
            fig = f'<div class="carrossel__img">{fig}</div>'
        cap = ""
        if s.get("legenda"):
            leg = esc(s["legenda"])
            if s.get("link"):
                leg = f'<a{a_attrs(s["link"], ctx)}>{leg}</a>'
            cap = f"<figcaption>{leg}</figcaption>"
        itens.append(f'<figure class="carrossel__slide">{fig}{cap}</figure>')
    auto = f' data-autoplay="{b["autoplay"]}"' if b.get("autoplay") and len(slides) > 1 else ""
    classe = junta("carrossel", "carrossel--card" if card else "", f"carrossel--{variante}" if variante else "",
                   "carrossel--multi" if por.get("desktop", 1) > 1 else "", cls_oculto(b))
    nav = ""
    if len(slides) > 1:
        nav = ('<button class="carrossel__seta carrossel__seta--ant" aria-label="Anterior">‹</button>'
               '<button class="carrossel__seta carrossel__seta--prox" aria-label="Próximo">›</button>'
               '<div class="carrossel__pontos"></div>')
    preco = preco_card(next(s["link"] for s in slides if s.get("link")), ctx) if card else ""
    return (f'<div class="{classe}"{estilo}{auto}><div class="carrossel__trilho">{"".join(itens)}</div>{nav}{preco}</div>')


def r_bloco(b, ctx, opcoes=None):
    t = b["tipo"]
    oc = cls_oculto(b)
    if t == "grupo":
        return r_grupo(b, ctx)
    if t == "heading":
        tag = b.get("tag", "h2")
        if tag not in ("h1", "h2", "h3", "h4", "h5", "h6"):
            tag = "p"
        txt = esc(b["texto"])
        if b.get("link"):
            txt = f'<a{a_attrs(b["link"], ctx)}>{txt}</a>'
        return f'<{tag} class="{junta("titulo", "titulo--" + tag, oc)}">{txt}</{tag}>'
    if t in ("text-editor", "html"):
        return f'<div class="{junta("texto", oc)}">{ajusta_html(b.get("html", ""), ctx)}</div>'
    if t == "image":
        img = foto_do_card(b.get("img"), b.get("link"), ctx)
        fig = img_tag({**img, "legenda": b.get("legenda", "")} if img else None, 700)
        if b.get("link"):
            fig = f'<a{a_attrs(b["link"], ctx)}>{fig}</a>'
        cap = f'<figcaption>{esc(b["legenda"])}</figcaption>' if b.get("legenda") else ""
        card = "imagem--card" if b.get("link") and b.get("legenda") else ""
        if card and cap:
            cap = f'<figcaption><a{a_attrs(b["link"], ctx)}>{esc(b["legenda"])}</a></figcaption>'
        if card:
            cap += preco_card(b["link"], ctx)
        return f'<figure class="{junta("imagem", card, oc)}">{fig}{cap}</figure>'
    if t == "image-carousel":
        return r_carrossel(b, ctx, **(opcoes or {}))
    if t == "button":
        link = b.get("link", "")
        wa = "whatsapp.com" in link or "wa.me" in link
        classe = junta("btn", "btn--wa" if wa else "btn--primary", oc)
        icone = '<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2Zm5.3 14.1c-.2.6-1.3 1.2-1.8 1.3-.5 0-1 .2-3.2-.7-2.7-1.1-4.4-3.8-4.5-4-.1-.2-1.1-1.4-1.1-2.7 0-1.3.7-1.9.9-2.2.2-.3.5-.3.7-.3h.5c.2 0 .4 0 .6.5l.8 2c.1.2.1.4 0 .5l-.3.5-.4.4c-.1.2-.3.3-.1.6.2.3.8 1.3 1.7 2.1 1.1 1 2.1 1.3 2.4 1.5.3.1.5.1.6-.1l.9-1.1c.2-.3.4-.2.7-.1l1.9.9c.3.1.5.2.5.3.1.2.1.7-.1 1.4Z"/></svg>' if wa else ""
        return f'<a class="{classe}"{a_attrs(link, ctx)}>{icone}{esc(b["texto"])}</a>'
    if t in ("accordion", "toggle", "n-accordion"):
        partes = []
        for i, it in enumerate(b.get("itens", [])):
            corpo = tabela_precos(it["html"]) or f'<div class="texto">{ajusta_html(it["html"], ctx)}</div>'
            partes.append(f"<details><summary>{esc(it['titulo'])}</summary>{corpo}</details>")
        return f'<div class="{junta("acordeao", oc)}">{"".join(partes)}</div>'
    if t == "abas":
        botoes, paineis = [], []
        for i, aba in enumerate(b.get("abas", [])):
            sel = "true" if i == 0 else "false"
            botoes.append(f'<button role="tab" aria-selected="{sel}" class="{"on" if i == 0 else ""}">{esc(aba["titulo"])}</button>')
            oculto = "" if i == 0 else " hidden"
            paineis.append(f'<div role="tabpanel" class="abas__painel"{oculto}>'
                           f'{r_blocos(aba["blocos"], ctx)}</div>')
        return (f'<div class="{junta("abas", oc)}"><div class="tabs" role="tablist">{"".join(botoes)}</div>'
                f'{"".join(paineis)}</div>')
    if t == "divider":
        return f'<hr class="{junta("divisor", oc)}">'
    if t == "icon-list":
        lis = []
        for it in b.get("itens", []):
            txt = esc(it["texto"])
            if it.get("link"):
                txt = f'<a{a_attrs(it["link"], ctx)}>{txt}</a>'
            lis.append(f"<li>{txt}</li>")
        return f'<ul class="{junta("lista", oc)}">{"".join(lis)}</ul>'
    if t == "image-box":
        fig = img_tag({**(b.get("img") or {}), "legenda": b.get("titulo", "")} if b.get("img") else None, 500)
        tag = b.get("titulo_tag", "h3")
        tit = f'<{tag} class="titulo">{esc(b["titulo"])}</{tag}>' if b.get("titulo") else ""
        return f'<div class="{junta("caixa-img", oc)}">{fig}{tit}<div class="texto">{ajusta_html(b.get("descricao", ""), ctx)}</div></div>'
    if t == "video":
        url = b.get("url", "")
        m = re.search(r"(?:youtu\.be/|v=|embed/)([\w-]{11})", url)
        if m:
            return (f'<div class="{junta("video", oc)}"><iframe src="https://www.youtube-nocookie.com/embed/{m.group(1)}" '
                    'title="Vídeo" loading="lazy" allowfullscreen></iframe></div>')
        return ""
    if b.get("html"):
        return f'<div class="{junta("texto", oc)}">{ajusta_html(b["html"], ctx)}</div>'
    return ""


def eh_card(grupo):
    """Coluna que só tem um novelo com link (carrossel ou imagem com legenda)."""
    fl = list(folhas(grupo["blocos"]))
    if len(fl) != 1:
        return False
    b = fl[0]
    if b["tipo"] == "image-carousel":
        return any(s.get("link") for s in b.get("slides", []))
    return b["tipo"] == "image" and bool(b.get("link")) and bool(b.get("legenda"))


def r_grupo(b, ctx):
    filhos = b["blocos"]
    oc = cls_oculto(b)
    if len(filhos) >= 2 and all(f["tipo"] == "grupo" for f in filhos):
        n = len(filhos)
        cards = all(eh_card(f) for f in filhos)
        if cards:
            classe = "linha linha--cards"
        else:
            classe = "linha linha--grade" if n > 4 else f"linha linha--{n}"
        # Catálogos grandes: mostra POR_PAGINA cores e um botão "Ver mais cores".
        # Todas continuam no HTML (o Google segue os links); só ficam escondidas na tela.
        paginar = cards and n > 2 * POR_PAGINA   # só vale a pena em catálogo bem grande (Fio Original)
        cols = "".join(
            f'<div class="{junta("col", "mais" if paginar and i >= POR_PAGINA else "", cls_oculto(f))}">'
            f'{r_blocos(f["blocos"], ctx)}</div>'
            for i, f in enumerate(filhos))
        grade = f'<div class="{junta(classe, oc)}">{cols}</div>'
        if paginar:
            grade += (f'<div class="ver-mais"><button type="button" class="btn btn--ghost" data-ver-mais>'
                      f'Ver mais cores <span data-restam>({n - POR_PAGINA})</span></button></div>')
        return grade
    return f'<div class="{junta("pilha", oc)}">{r_blocos(filhos, ctx)}</div>'


def r_blocos(blocos, ctx):
    return "".join(r_bloco(b, ctx) for b in blocos)


# ---------------------------------------------------------------- produtos (loja)

RE_FAIXA = re.compile(r"(\d[\d.]*)\s*m\b[^|]*\|\s*R\$\s*([\d.]+,\d{2})\s*(?:\|\s*(?:≅|&#8773;)?\s*(\d+)\s*g)?", re.I)
RE_FIXO = re.compile(r"(\d)\s*cabos\s*\|\s*(\d[\d.]*)\s*m\s*\|\s*R\$\s*([\d.]+,\d{2})", re.I)
PRODUTOS = {}  # caminho novo -> dados do produto (preenchido em main)


def reais(v):
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def linhas_de_preco(h):
    h = re.sub(r"<br\s*/?>|</p>", "\n", h)
    h = html.unescape(re.sub(r"<[^>]+>", "", h))
    out = []
    for l in h.split("\n"):
        m = RE_FAIXA.search(l)
        if m:
            out.append({"m": int(m.group(1).replace(".", "")),
                        "preco": float(m.group(2).replace(".", "").replace(",", ".")),
                        "g": int(m.group(3)) if m.group(3) else None})
    return out


def eh_tabela_preco(b):
    if b["tipo"] == "accordion":
        return True
    if b["tipo"] == "text-editor":
        t = html.unescape(re.sub(r"<[^>]+>", " ", b.get("html", "")))
        return bool(RE_FIXO.search(t)) or len(linhas_de_preco(b.get("html", ""))) >= 2
    return False


def dados_produto(p, caminho, linha):
    """Lê as tabelas de preço da página e monta as opções de compra."""
    fl = list(folhas(p["blocos"]))
    info_txt = " ".join(re.sub(r"<[^>]+>", " ", b.get("html", "")) for b in fl if b["tipo"] == "text-editor")
    cabos_info = re.search(r"(\d)\s*cabos", info_txt)
    variacoes = []
    for b in fl:
        if b["tipo"] == "accordion":
            for it in b["itens"]:
                faixas = linhas_de_preco(it["html"])
                if faixas:
                    variacoes.append({"titulo": it["titulo"], "faixas": faixas})
        elif b["tipo"] == "text-editor":
            t = html.unescape(re.sub(r"<[^>]+>", " ", b.get("html", "")))
            m = RE_FIXO.search(t)
            if m:
                variacoes.append({"titulo": f"{m.group(1)} cabos", "faixas": [{
                    "m": int(m.group(2).replace(".", "")),
                    "preco": float(m.group(3).replace(".", "").replace(",", ".")), "g": None}]})
            elif len(linhas_de_preco(b.get("html", ""))) >= 2:
                variacoes.append({"titulo": "", "faixas": linhas_de_preco(b["html"])})
    for v in variacoes:
        m = re.search(r"(\d)\s*cabos", v["titulo"])
        v["cabos"] = f"{m.group(1)} cabos" if m else (f"{cabos_info.group(1)} cabos" if cabos_info else "")
        tl = v["titulo"].lower()
        v["brilho"] = "Com brilho" if "com brilho" in tl else ("Sem brilho" if "sem brilho" in tl else "")
        del v["titulo"]

    midia = next((b for b in fl if b["tipo"] in ("image-carousel", "image")), None)
    cores = []
    if midia and midia["tipo"] == "image-carousel":
        fontes = midia["slides"]
    elif midia:
        fontes = [{**(midia.get("img") or {}), "legenda": midia.get("legenda", "")}]
    else:
        fontes = []
    for s in fontes:
        legenda = s.get("legenda") or s.get("alt") or ""
        cores.append({"nome": legenda.split("|")[0].strip() or nome_pagina(p),
                      "legenda": legenda, "src": s.get("src", ""), "alt": s.get("alt", "")})
    h1 = next((b["texto"] for b in fl if b["tipo"] == "heading" and b.get("tag") == "h1"), nome_pagina(p))
    precos = [f["preco"] for v in variacoes for f in v["faixas"]]
    botao = next((b for b in fl if b["tipo"] == "button"), None)
    return {
        "caminho": caminho, "linha": linha, "linha_nome": SITE["nomes_linhas"].get(linha, linha),
        "nome": h1, "cores": cores, "variacoes": variacoes,
        "preco_min": min(precos) if precos else None, "preco_max": max(precos) if precos else None,
        "botao": botao["texto"] if botao else "Compre pelo WhatsApp",
        "img": cores[0]["src"] if cores else "",
    }


def preco_card(link, ctx):
    destino = ctx.mapa.get(link, link)
    d = PRODUTOS.get(destino)
    if not d or d["preco_min"] is None:
        return ""
    return f'<div class="price">a partir de {reais(d["preco_min"])}</div>'


SVG_WA = '<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2Zm5.3 14.1c-.2.6-1.3 1.2-1.8 1.3-.5 0-1 .2-3.2-.7-2.7-1.1-4.4-3.8-4.5-4-.1-.2-1.1-1.4-1.1-2.7 0-1.3.7-1.9.9-2.2.2-.3.5-.3.7-.3h.5c.2 0 .4 0 .6.5l.8 2c.1.2.1.4 0 .5l-.3.5-.4.4c-.1.2-.3.3-.1.6.2.3.8 1.3 1.7 2.1 1.1 1 2.1 1.3 2.4 1.5.3.1.5.1.6-.1l.9-1.1c.2-.3.4-.2.7-.1l1.9.9c.3.1.5.2.5.3.1.2.1.7-.1 1.4Z"/></svg>'


def corpo_produto(p, ctx, trilha, d):
    """Página de produto com cara de loja: cor, cabos, brilho, metragem, quantidade e carrinho."""
    fl = list(folhas(p["blocos"]))
    midia = next((b for b in fl if b["tipo"] in ("image-carousel", "image")), None)
    h1_feito = False
    resto = []
    for b in fl:
        if b is midia or eh_tabela_preco(b) or b["tipo"] == "button":
            continue
        if b["tipo"] == "heading" and b.get("tag") == "h1" and not h1_feito:
            h1_feito = True
            continue
        if b["tipo"] == "heading" and b.get("texto", "").strip().lower() == "informações do produto":
            continue
        resto.append(b)

    # Galeria: foto grande + miniaturas (uma por cor)
    fotos = "".join(
        f'<figure class="galeria__foto" data-cor="{i}"{"" if i == 0 else " hidden"}>'
        f'{img_tag({"src": c["src"], "alt": c["alt"] or c["legenda"]}, 900, lazy=i > 0, sizes="(max-width: 900px) 100vw, 600px")}'
        f'<figcaption>{esc(c["legenda"])}</figcaption></figure>'
        for i, c in enumerate(d["cores"]))

    # Opções
    v0 = d["variacoes"][0] if d["variacoes"] else None
    f0 = v0["faixas"][0] if v0 else None
    def grupo_opcoes(nome, chave, valores):
        if len(valores) < 2:
            return f'<div class="opcao opcao--fixa"><span class="vlabel">{nome}:</span> <b>{esc(valores[0])}</b></div>' if valores and valores[0] else ""
        botoes = "".join(f'<button type="button" class="chip{" on" if i == 0 else ""}" data-{chave}="{esc(v)}" aria-pressed="{str(i == 0).lower()}">{esc(v)}</button>'
                         for i, v in enumerate(valores))
        return f'<div class="opcao"><span class="vlabel">{nome}: <b data-rotulo="{chave}">{esc(valores[0])}</b></span><div class="chips">{botoes}</div></div>'

    cores_html = ""
    if len(d["cores"]) > 1:
        sw = "".join(
            f'<button type="button" class="swatch{" on" if i == 0 else ""}" data-cor="{i}" aria-pressed="{str(i == 0).lower()}" aria-label="{esc(c["nome"])}">'
            f'{img_tag({"src": c["src"], "alt": ""}, 120, lazy=False, sizes="56px")}</button>'
            for i, c in enumerate(d["cores"]))
        cores_html = (f'<div class="opcao"><span class="vlabel">Cor: <b data-rotulo="cor">{esc(d["cores"][0]["nome"])}</b></span>'
                      f'<div class="swatches">{sw}</div></div>')

    cabos = list(dict.fromkeys(v["cabos"] for v in d["variacoes"]))
    brilhos = list(dict.fromkeys(v["brilho"] for v in d["variacoes"] if v["brilho"]))
    opcoes = cores_html + grupo_opcoes("Cabos", "cabos", cabos) + grupo_opcoes("Acabamento", "brilho", brilhos)
    if f0:
        metragens = "".join(f'<option value="{f["m"]}">{f["m"]} m</option>' for f in v0["faixas"])
        unica = len(v0["faixas"]) == 1
        opcoes += (f'<div class="opcao"><label class="vlabel" for="metragem">Metragem</label>'
                   f'<select class="input metragem" id="metragem"{" disabled" if unica else ""}>{metragens}</select></div>')
        preco = (f'<div class="price price--lg" data-preco>{reais(f0["preco"])}'
                 f'<small data-peso>{"≅ " + str(f0["g"]) + " g · " if f0["g"] else ""}{f0["m"]} m</small></div>')
        compra = (f'<div class="qty-row"><div class="qty"><button type="button" data-qtd="-1" aria-label="Diminuir">−</button><span data-qtd-valor>1</span>'
                  f'<button type="button" data-qtd="1" aria-label="Aumentar">+</button></div>'
                  f'<button type="button" class="btn btn--primary btn--block" data-adicionar>Adicionar ao carrinho</button></div>'
                  f'<a class="btn btn--wa btn--block" data-comprar-wa href="{esc(SITE["whatsapp"])}" target="_blank" rel="noopener">{SVG_WA}{esc(d["botao"])}</a>')
    else:
        preco = ""
        compra = f'<a class="btn btn--wa btn--block" href="{esc(SITE["whatsapp"])}" target="_blank" rel="noopener">{SVG_WA}{esc(d["botao"])}</a>'

    info = r_blocos(resto, ctx)
    dados_js = {"nome": d["nome"], "url": d["caminho"], "linha": d["linha_nome"],
                "cores": [{"nome": c["nome"], "img": img_url(c["src"], 200)} for c in d["cores"]],
                "variacoes": d["variacoes"]}
    return f"""<div class="wrap pdp-wrap">{migalhas(trilha, ctx)}
<div class="pdp loja" data-produto>
  <div class="pdp__media galeria">{fotos}</div>
  <div class="pdp__info">
    <a class="eyebrow" href="{esc(ctx.rel('/' + d['linha'] + '/'))}">{esc(d['linha_nome'])}</a>
    <h1 class="titulo titulo--h1">{esc(d['nome'])}</h1>
    {preco}
    <div class="opcoes">{opcoes}</div>
    {compra}
    <ul class="trust"><li>🧶 Feito à mão, novelo a novelo</li><li>⏱ Produção de 7 a 15 dias após o pagamento</li><li>💬 Pedido finalizado pelo WhatsApp</li></ul>
    <details class="pdp__detalhes" open><summary>Informações do produto</summary><div class="pilha">{info}</div></details>
  </div>
</div>
<script type="application/json" id="produto-dados">{json.dumps(dados_js, ensure_ascii=False).replace("</", "<\\/")}</script>
</div>"""


# ---------------------------------------------------------------- moldes de página

def nome_pagina(p):
    t = p.get("og_title") or p["title"].replace(" – Nouvellando®", "")
    return html.unescape(t)


# ---------------------------------------------------------------- SEO

def corta(texto, limite=158):
    """Texto em uma linha, com no máximo `limite` caracteres, cortado em palavra inteira."""
    t = re.sub(r"\s+", " ", texto).strip()
    if len(t) <= limite:
        return t
    t = t[:limite - 1].rsplit(" ", 1)[0].rstrip(" ,.;:–-")
    return t + "…"


def descricao(p, ctx, tipo):
    """Meta description: a de conteudo/seo.json, ou montada com os dados da página."""
    sob = SEO.get(ctx.caminho) or SEO.get(p["url"]) or {}
    if sob.get("description"):
        return sob["description"]
    if tipo == "produto" and PRODUTOS.get(ctx.caminho):
        d = PRODUTOS[ctx.caminho]
        texto = (d["nome"] + " " + " ".join(c["legenda"] for c in d["cores"])).lower()
        nome = re.sub(r"\s*\(sem degradê\)", "", d["nome"], flags=re.I).strip()
        estilo = "sem degradê" if "sem degrad" in texto else "degradê"
        cabos = sorted({v["cabos"].split()[0] for v in d["variacoes"] if v["cabos"]})
        partes = [f"Novelo {nome}, artesanal {estilo} e feito à mão por Claudia Gerth."]
        lista = ", ".join(cabos[:-1]) + " ou " + cabos[-1] if len(cabos) > 1 else "".join(cabos)
        detalhe = (lista + " cabos") if cabos else ""
        if d["preco_min"] is not None:
            detalhe = (detalhe + ", a partir de " if detalhe else "A partir de ") + reais(d["preco_min"])
        if detalhe:
            partes.append(detalhe[0].upper() + detalhe[1:] + ".")
        partes.append("Escolha a metragem e peça pelo WhatsApp.")
        return corta(" ".join(partes))
    if tipo == "categoria":
        sub = SITE["menu"][1]["submenu"]
        nome = next((m["texto"] for m in sub if m["link"] == p["url"]), nome_pagina(p))
        prods = produtos_da_pagina(p, ctx)
        if prods:
            precos = [d["preco_min"] for d in prods if d["preco_min"] is not None]
            estilo = "sem degradê" if "sem degrad" in nome.lower() else "degradê"
            preco = f", a partir de {reais(min(precos))}" if precos else ""
            n = len(prods)
            return corta(f"{nome}: novelos artesanais {estilo} feitos à mão por Claudia Gerth. "
                         f"{n} {'cor' if n == 1 else 'cores'}{preco}. Escolha a sua e peça pelo WhatsApp.")
    # Demais páginas: o texto do site atual, sem o título repetido no começo e sem palavras grudadas
    base = html.unescape(p.get("description", ""))
    nome = nome_pagina(p)
    for repetido in (nome, re.sub(r"^Videoaula\s+", "", nome)):
        if base.startswith(repetido):
            base = base[len(repetido):]
            break
    base = re.sub(r"([a-zà-ú\.!?])([A-ZÀ-Ú])", r"\1 \2", base).replace("Whats App", "WhatsApp")
    return corta(base)


def um_h1(corpo):
    """Deixa só o primeiro <h1> da página; os outros viram <p> com a mesma aparência."""
    n = 0

    def troca(m):
        nonlocal n
        n += 1
        if n == 1:
            return m.group(0)
        return f"<p{m.group(1)}>{m.group(2)}</p>"

    return re.sub(r"<h1(\b[^>]*)>(.*?)</h1>", troca, corpo, flags=re.S)


def migalhas(itens, ctx):
    partes = []
    for i, (nome, link) in enumerate(itens):
        if i:
            partes.append("<i>›</i>")
        partes.append(f'<a href="{esc(ctx.rel(link))}">{esc(nome)}</a>' if link else f"<span>{esc(nome)}</span>")
    return f'<nav class="crumbs" aria-label="Você está em">{"".join(partes)}</nav>'


CURSOS = []  # videoaulas, na ordem da página /cursos/ (preenchido em main)


def resumo(h, limite=190):
    t = re.sub(r"</?(?:p|br|h\d|li|ul|ol)\b[^>]*>", " ", h)
    t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", t))).strip()
    if len(t) <= limite:
        return t
    return t[:limite].rsplit(" ", 1)[0].rstrip(",.;:") + "…"


def carrega_cursos(pags):
    """Lê a página /cursos/: cada grupo tem fotos (com link para a página da aula), preço e botão Comprar."""
    p = pags.get("cursos")
    if not p:
        return
    for g in folhas_grupos(p["blocos"]):
        car = next((b for b in g["blocos"] if b["tipo"] == "image-carousel"), None)
        if not car or not car.get("slides"):
            continue
        preco = next((resumo(b["html"]) for b in g["blocos"] if b["tipo"] == "text-editor"), "")
        botao = next((b for b in g["blocos"] if b["tipo"] == "button"), None)
        nome = next((s["legenda"] for s in car["slides"] if s.get("legenda")), "")
        pagina = next((s["link"] for s in car["slides"] if s.get("link")), "")
        desc = ""
        aula = pags.get(pagina.strip("/"))
        if aula:
            fl = list(folhas(aula["blocos"]))
            desc = next((resumo(b["html"]) for b in fl if b["tipo"] == "text-editor"), "")
        CURSOS.append({"nome": nome, "slides": car["slides"], "preco": preco,
                       "comprar": botao.get("link", "") if botao else "", "comprar_txt": botao["texto"] if botao else "Comprar",
                       "pagina": pagina, "desc": desc})


def folhas_grupos(blocos):
    """Grupos que só têm blocos (sem subgrupos)."""
    for b in blocos:
        if b["tipo"] == "grupo":
            if any(x["tipo"] == "grupo" for x in b["blocos"]):
                yield from folhas_grupos(b["blocos"])
            else:
                yield b


SVG_PLAY = '<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M7 4.5v15a1 1 0 0 0 1.5.86l12.5-7.5a1 1 0 0 0 0-1.72L8.5 3.64A1 1 0 0 0 7 4.5Z"/></svg>'
SVG_INFO = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="9.5"/><path d="M12 11v6M12 7.5v.01" stroke-linecap="round"/></svg>'


def card_curso(c, ctx, mostra_preco=True):
    img = img_tag(c["slides"][0], 500, sizes="(max-width: 700px) 42vw, 240px")
    preco = f'<span class="nf-card__preco">{esc(c["preco"])}</span>' if mostra_preco and c["preco"] else ""
    comprar = (f'<a class="btn btn--primary btn--sm"{a_attrs(c["comprar"], ctx)}>{SVG_PLAY}{esc(c["comprar_txt"])}</a>'
               if mostra_preco and c["comprar"] else "")
    return (f'<article class="nf-card"><a class="nf-card__capa"{a_attrs(c["pagina"], ctx)}>{img}'
            f'<span class="nf-card__nome">{esc(c["nome"])}</span></a>'
            f'<div class="nf-card__info"><a class="nf-card__titulo"{a_attrs(c["pagina"], ctx)}>{esc(c["nome"])}</a>{preco}'
            f'<div class="nf-card__acoes">{comprar}<a class="nf-icone"{a_attrs(c["pagina"], ctx)} aria-label="Detalhes de {esc(c["nome"])}">{SVG_INFO}</a></div></div></article>')


def fileira(titulo, cursos, ctx, mostra_preco=True, classe=""):
    cards = "".join(card_curso(c, ctx, mostra_preco) for c in cursos)
    return (f'<section class="nf-fileira {classe}"><div class="wrap"><h2 class="nf-fileira__titulo">{esc(titulo)}</h2></div>'
            f'<div class="nf-fileira__corpo"><button class="nf-seta nf-seta--ant" aria-label="Voltar">‹</button>'
            f'<div class="nf-trilho">{cards}</div>'
            f'<button class="nf-seta nf-seta--prox" aria-label="Avançar">›</button></div></section>')


def corpo_cursos(p, ctx):
    titulos = "".join(r_bloco(b, ctx) for b in folhas(p["blocos"][:1]))
    destaques = CURSOS[:5]
    slides = []
    for i, c in enumerate(destaques):
        fundo = img_tag(c["slides"][0], 1400, lazy=i > 0, sizes="100vw", classe="nf-hero__fundo")
        comprar = (f'<a class="btn btn--light"{a_attrs(c["comprar"], ctx)}>{SVG_PLAY}{esc(c["comprar_txt"])}</a>' if c["comprar"] else "")
        slides.append(
            f'<div class="nf-hero__slide{" on" if i == 0 else ""}" data-destaque="{i}"{"" if i == 0 else " aria-hidden=\"true\""}>{fundo}'
            f'<div class="wrap nf-hero__info"><span class="nf-selo">Lançamento</span>'
            f'<p class="nf-hero__nome">{esc(c["nome"])}</p>'
            f'<p class="nf-hero__desc">{esc(c["desc"])}</p>'
            f'<p class="nf-hero__preco">{esc(c["preco"])} <small>· Videoaula na Hotmart</small></p>'
            f'<div class="nf-hero__acoes">{comprar}<a class="btn nf-btn-cinza"{a_attrs(c["pagina"], ctx)}>{SVG_INFO}Mais informações</a></div></div></div>')
    pontos = "".join(f'<button class="{"on" if i == 0 else ""}" data-ir="{i}" aria-label="Destaque {i + 1}"></button>' for i in range(len(destaques)))
    hero = (f'<section class="nf-hero" data-hero><div class="wrap nf-marca">{titulos}</div>{"".join(slides)}'
            f'<div class="wrap nf-hero__pontos">{pontos}</div></section>')
    xales = [c for c in CURSOS if c["nome"].lower().startswith("xale")]
    mantas = [c for c in CURSOS if not c["nome"].lower().startswith("xale")]
    linhas = (fileira("Lançamentos", CURSOS[:8], ctx, mostra_preco=False, classe="nf-fileira--destaque")
              + fileira("Xales", xales, ctx) + fileira("Mantas", mantas, ctx))
    return f'<div class="nf">{hero}{linhas}</div>'


# ---------------------------------------------------------------- página Nossos fios

def linhas_html(h):
    """Quebra um bloco de texto em linhas (por parágrafo e <br>), sem tags."""
    out = []
    for parte in re.split(r"<br\s*/?>|</p>", h):
        t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", parte))).replace("\xa0", " ").strip()
        if t:
            out.append(t)
    return out


def ficha_tecnica(h):
    """Organiza 'Composição', 'N cabos TEX' + 'Agulha' e observações em estrutura."""
    comp, cabos, notas = [], [], []
    atual = None
    for l in linhas_html(h):
        m = re.match(r"^(\d) cabos TEX\s*:?\s*(.*)$", l)
        if m:
            atual = {"cabos": f"{m.group(1)} cabos", "tex": m.group(2).strip(), "agulha": ""}
            cabos.append(atual)
            continue
        m = re.match(r"^Agulha\s*:?\s*(.*)$", l)
        if m and atual is not None:
            atual["agulha"] = m.group(1).strip()
            continue
        if l.lower().startswith("atenção"):
            notas.append(l)
            continue
        if ":" in l:
            rot, val = l.split(":", 1)
            comp.append([rot.strip(), val.strip()])
        elif comp and not comp[-1][1]:
            comp[-1][1] = l
        elif comp and comp[-1][1].endswith("/"):
            comp[-1][1] += " " + l
        else:
            notas.append(l)
    return comp, cabos, notas


def r_ficha(comp, cabos, notas):
    partes = []
    if comp:
        itens = "".join(
            (f"<div><dt>{esc(r)}</dt><dd>{esc(v)}</dd></div>" if v else f'<div class="ficha__rotulo"><dt>{esc(r)}</dt></div>')
            for r, v in comp)
        partes.append(f'<dl class="ficha__comp">{itens}</dl>')
    if cabos:
        linhas = "".join(f'<tr><th scope="row">{esc(c["cabos"])}</th><td>{esc(c["tex"])}</td><td>{esc(c["agulha"])}</td></tr>' for c in cabos)
        partes.append(f'<table class="ficha__tabela"><thead><tr><th>Cabos</th><th>TEX</th><th>Agulha</th></tr></thead><tbody>{linhas}</tbody></table>')
    for n in notas:
        rot, _, val = n.partition(":")
        partes.append(f'<p class="ficha__nota"><strong>{esc(rot)}:</strong>{esc(val)}</p>' if val else f'<p class="ficha__nota">{esc(n)}</p>')
    return f'<div class="ficha">{"".join(partes)}</div>' if partes else ""


def corpo_fios(p, ctx):
    blocos = p["blocos"]
    intro = r_bloco(blocos[0], ctx)
    cards = [list(folhas([g])) for g in blocos[1]["blocos"]]
    detalhes = [list(folhas([g])) for g in blocos[2:]]

    def chave(nome):
        return re.sub(r"^fio\s+", "", nome.strip().lower())

    por_nome = {}
    for fl in detalhes:
        h = next((b for b in fl if b["tipo"] == "heading"), None)
        if h:
            por_nome[chave(h["texto"])] = fl

    fios = []
    for fl in cards:
        h = next(b for b in fl if b["tipo"] == "heading")
        img = next((b for b in fl if b["tipo"] == "image"), None)
        txt = next((b for b in fl if b["tipo"] == "text-editor"), None)
        btn = next((b for b in fl if b["tipo"] == "button"), None)
        det = por_nome.get(chave(h["texto"]), [])
        d_h = next((b for b in det if b["tipo"] == "heading"), None)
        d_txts = [b for b in det if b["tipo"] == "text-editor"]
        d_btn = next((b for b in det if b["tipo"] == "button"), None)
        d_img = next((b for b in det if b["tipo"] == "image"), None)
        # Textos do bloco de computador: legenda da foto (antes do título), descrição, ficha
        idx_h = det.index(d_h) if d_h in det else 0
        legenda = [b for b in d_txts if det.index(b) < idx_h]
        depois = [b for b in d_txts if det.index(b) > idx_h]
        linhas_card = linhas_html(txt["html"]) if txt else []
        selo = ""
        if linhas_card:
            prim = linhas_card[0]
            selo = prim if ":" not in prim else prim.split(":")[0]
        # Ficha: a do bloco de computador (mais completa); se não houver, a do card
        ficha_html = ""
        descricao = []
        for b in depois:
            if re.search(r"Composição|cabos TEX|Agulha", b["html"]):
                ficha_html = b["html"]
            else:
                descricao.append(b)
        if not ficha_html and txt and re.search(r"Composição|cabos TEX", txt["html"]):
            ficha_html = txt["html"]
        # Card de 'Cor única' tem um parágrafo que é a própria descrição
        sobras = [l for l in linhas_card[1:] if not re.search(r"Composição|cabos TEX|Agulha|^Fio \d|:", l)]
        fios.append({
            "curto": h["texto"], "nome": d_h["texto"] if d_h else h["texto"],
            "id": re.sub(r"[^a-z0-9]+", "-", chave(h["texto"]).replace("é", "e").replace("ú", "u")).strip("-"),
            "selo": selo, "img": (img or d_img or {}).get("img"), "link": (img or {}).get("link") or (d_img or {}).get("link", ""),
            "legenda": legenda, "descricao": descricao, "sobras": sobras if not descricao else [],
            "ficha": ficha_tecnica(ficha_html) if ficha_html else None,
            "botoes": [b for b in (btn, d_btn) if b],
        })

    # Navegação: miniaturas de cada linha
    nav = "".join(
        f'<a class="fios-nav__item" href="#{f["id"]}">{img_tag(f["img"], 160, sizes="72px")}<span>{esc(f["curto"])}</span></a>'
        for f in fios)
    secoes = []
    for i, f in enumerate(fios):
        img_fio = {**f["img"], "alt": f["img"].get("alt") or f["nome"]} if f["img"] else None
        foto = img_tag(img_fio, 800, sizes="(max-width: 900px) 100vw, 480px")
        if f["link"]:
            foto = f'<a class="fio__foto"{a_attrs(f["link"], ctx)}>{foto}</a>'
        else:
            foto = f'<div class="fio__foto">{foto}</div>'
        legenda = "".join(f'<div class="texto fio__legenda">{ajusta_html(b["html"], ctx)}</div>' for b in f["legenda"])
        desc = "".join(f'<div class="texto fio__desc">{ajusta_html(b["html"], ctx)}</div>' for b in f["descricao"])
        desc += "".join(f'<p class="texto fio__desc">{esc(l)}</p>' for l in f["sobras"])
        ficha = r_ficha(*f["ficha"]) if f["ficha"] else ""
        # Botões: catálogo primeiro; dos botões de WhatsApp fica o mais descritivo
        cat = [b for b in f["botoes"] if b.get("link", "").startswith("/")]
        wa = [b for b in f["botoes"] if "whatsapp" in b.get("link", "")]
        wa = sorted(wa, key=lambda b: -len(b["texto"]))[:1]
        botoes = "".join(f'<a class="btn btn--primary"{a_attrs(b["link"], ctx)}>{esc(b["texto"])} <span aria-hidden="true">→</span></a>' for b in cat)
        botoes += "".join(f'<a class="btn btn--wa"{a_attrs(b["link"], ctx)}>{SVG_WA}{esc(b["texto"])}</a>' for b in wa)
        selo = f'<span class="eyebrow">{esc(f["selo"])}</span>' if f["selo"] and f["selo"] != f["curto"] else ""
        secoes.append(
            f'<article class="fio{" fio--inv" if i % 2 else ""}" id="{f["id"]}">'
            f'<div class="fio__midia">{foto}{legenda}</div>'
            f'<div class="fio__info"><div class="fio__cab"><h3 class="fio__curto">{esc(f["curto"])}</h3>{selo}</div>'
            f'<h2 class="titulo">{esc(f["nome"])}</h2>{desc}{ficha}<div class="fio__botoes">{botoes}</div></div></article>')

    hero = (f'<section class="cat-hero"><div class="wrap">{migalhas([("Início", "/"), ("Nossos fios", None)], ctx)}'
            f'{intro}<span class="pill">{len(fios)} fios</span></div></section>')
    return (f'{hero}<div class="wrap fios-nav-wrap"><nav class="fios-nav" aria-label="Fios">{nav}</nav></div>'
            f'<div class="wrap fios">{"".join(secoes)}</div>')


NOVIDADES = []  # caminhos dos produtos mais novos (ordem do catálogo do Fio Original)


def card_produto(d, ctx):
    """Card de produto no estilo do design system (home)."""
    img = img_tag({"src": d["img"], "alt": d["nome"]}, 500, sizes="(max-width: 900px) 50vw, 260px")
    cores = len(d["cores"])
    return (f'<article class="card"><a class="card__img" href="{esc(ctx.rel(d["caminho"]))}">{img}</a>'
            f'<div class="card__body"><span class="card__cat">{esc(d["linha_nome"])}</span>'
            f'<h3 class="card__name"><a href="{esc(ctx.rel(d["caminho"]))}">{esc(d["nome"])}</a></h3>'
            f'{f"<small class=card__cores>{cores} cores</small>" if cores > 1 else ""}'
            f'<div class="price">a partir de {reais(d["preco_min"])}</div></div>'
            f'<a class="card__add" href="{esc(ctx.rel(d["caminho"]))}">Escolher opções</a></article>')


def produtos_da_pagina(p, ctx):
    vistos = []
    for b in folhas(p["blocos"]):
        for l in links_do_bloco(b):
            d = PRODUTOS.get(ctx.mapa.get(l, l))
            if d and d not in vistos:
                vistos.append(d)
    return vistos


def topo_categoria(p, ctx, primeira):
    """Faixa do topo dos catálogos: caminho, nome da linha, total de cores e atalhos para as outras linhas."""
    sub = SITE["menu"][1]["submenu"]
    nome = next((m["texto"] for m in sub if m["link"] == p["url"]), nome_pagina(p))
    prods = produtos_da_pagina(p, ctx)
    precos = [d["preco_min"] for d in prods if d["preco_min"] is not None]
    pill = ""
    if prods:
        pill = f'<span class="pill">{len(prods)} {"cor" if len(prods) == 1 else "cores"}' + (f" · a partir de {reais(min(precos))}" if precos else "") + "</span>"
    # Sem título no conteúdo: o nome da linha vira o H1 da página (antes era um <p>)
    titulo = primeira or f'<h1 class="cat-hero__nome">{esc(nome)}</h1>'
    chips = "".join(
        f'<a class="chip{" on" if m["link"] == p["url"] else ""}" href="{esc(ctx.rel(m["link"]))}">{esc(m["texto"].replace("Fio ", ""))}</a>'
        for m in sub)
    return (f'<section class="cat-hero"><div class="wrap">{migalhas([("Início", "/"), ("Nossos fios", "/fios-nouvellando/"), (nome, None)] if p["url"] != "/fios-nouvellando/" else [("Início", "/"), (nome, None)], ctx)}'
            f'{titulo}{pill}</div></section>'
            f'<div class="wrap cat-chips"><nav class="chips chips--scroll" aria-label="Linhas de fio">{chips}</nav></div>')


def eh_textual(b):
    return all(x["tipo"] in ("heading", "text-editor") for x in folhas([b]))


def corpo_secoes(p, ctx, tipo):
    secoes = []
    blocos = p["blocos"]
    if tipo == "categoria":
        primeira = ""
        if blocos and eh_textual(blocos[0]):
            primeira = r_bloco(blocos[0], ctx)
            blocos = blocos[1:]
        secoes.append(topo_categoria(p, ctx, primeira))
    for i, b in enumerate(blocos):
        if tipo == "home" and CURSOS and secao_videoaulas(b):
            secoes.append(home_videoaulas(b, ctx))
            continue
        conteudo = r_bloco(b, ctx, {"variante": "hero", "largura": 1600} if (tipo == "home" and i < 2) else None)
        if not conteudo:
            continue
        classe = junta("secao", f"secao--{i + 1}", cls_oculto(b) if b["tipo"] == "grupo" else "")
        secoes.append(f'<section class="{classe}"><div class="wrap">{conteudo}</div></section>')
        if tipo == "home" and i == 2:
            secoes.append(faixa_beneficios() + novidades(ctx))
    return "".join(secoes)


def secao_videoaulas(b):
    return any(x["tipo"] == "heading" and x["texto"].startswith("Videoaulas de") for x in folhas([b]))


def home_videoaulas(b, ctx):
    """Seção de videoaulas da home no estilo streaming: título, texto e botão do site atual + fileira de capas."""
    fl = [x for x in folhas([b]) if x["tipo"] != "image-carousel"]
    titulo = next((r_bloco(x, ctx) for x in fl if x["tipo"] == "heading"), "")
    resto = "".join(r_bloco(x, ctx) for x in fl if x["tipo"] != "heading")
    linha = fileira("", CURSOS[:12], ctx).replace('<h2 class="nf-fileira__titulo"></h2>', "")
    return (f'<section class="nf nf--home"><div class="wrap nf-home__topo"><div>{titulo}</div>'
            f'<div class="pilha">{resto}</div></div>{linha}</section>')


def faixa_beneficios():
    itens = [("🧶", "Mais de 600 cores degradê", "Novelos artesanais por Claudia Gerth"),
             ("✋", "Feito à mão", "Produção de 7 a 15 dias"),
             ("🎨", "Cor única sob encomenda", "Qualquer cor, em qualquer fio"),
             ("💬", "Pedido pelo WhatsApp", "Atendimento direto com a artesã")]
    cel = "".join(f"<div><span>{a}</span><b>{b}</b><small>{c}</small></div>" for a, b, c in itens)
    return f'<section class="strip"><div class="wrap strip__grid">{cel}</div></section>'


def novidades(ctx):
    cards = "".join(card_produto(PRODUTOS[c], ctx) for c in NOVIDADES[:8])
    return (f'<section class="secao secao--loja"><div class="wrap"><div class="section__head section__head--linha">'
            f'<div><span class="eyebrow">Novidades</span><h2 class="titulo">Cores recém-chegadas</h2></div>'
            f'<a class="btn btn--ghost btn--sm" href="{esc(ctx.rel("/fio-original/"))}">Ver todas as cores</a></div>'
            f'<div class="grid">{cards}</div></div></section>')


def corpo_dividido(p, ctx, trilha):
    """Produto e videoaula: primeira mídia à esquerda, o resto à direita."""
    fl = list(folhas(p["blocos"]))
    midia = next((b for b in fl if b["tipo"] in ("image-carousel", "image")), None)
    resto = [b for b in fl if b is not midia]
    if midia and midia["tipo"] == "image-carousel":
        m = r_carrossel(midia, ctx, largura=900, variante="galeria")
    else:
        m = r_bloco(midia, ctx) if midia else ""
    info = "".join(r_bloco(b, ctx, {"variante": "mini"} if b["tipo"] == "image-carousel" else None) for b in resto)
    return (f'<div class="wrap pdp-wrap">{migalhas(trilha, ctx)}<div class="pdp">'
            f'<div class="pdp__media">{m}</div><div class="pdp__info">{info}</div></div></div>')


def json_ld(p, ctx, trilha):
    if p["url"] == "/":
        dados = {"@context": "https://schema.org", "@graph": [
            {"@type": "Organization", "name": SITE["nome"], "url": DOMINIO + "/",
             "logo": DOMINIO + "/wp-content/uploads/2022/12/cropped-novo-logo-espero-que-esse-esteja-certo.png",
             "sameAs": [r["link"] for r in SITE["rodape"]["redes"][:2]]},
            {"@type": "WebSite", "name": SITE["nome"], "url": DOMINIO + "/"}]}
    else:
        itens = []
        for i, (nome, link) in enumerate(trilha, 1):
            item = {"@type": "ListItem", "position": i, "name": nome}
            if link:
                item["item"] = DOMINIO + link
            itens.append(item)
        dados = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": itens}
        prod = PRODUTOS.get(ctx.caminho)
        if prod and prod["preco_min"] is not None:
            dados = {"@context": "https://schema.org", "@graph": [
                {k: v for k, v in dados.items() if k != "@context"},
                {"@type": "Product", "name": prod["nome"], "url": DOMINIO + ctx.caminho,
                 "image": [DOMINIO + img_url(c["src"], 800) if c["src"].startswith("/") else c["src"]
                           for c in prod["cores"]],
                 "brand": {"@type": "Brand", "name": "Nouvellando"},
                 "category": prod["linha_nome"],
                 "offers": {"@type": "AggregateOffer", "priceCurrency": "BRL",
                            "lowPrice": f'{prod["preco_min"]:.2f}', "highPrice": f'{prod["preco_max"]:.2f}',
                            "availability": "https://schema.org/MadeToOrder"}}]}
    return f'<script type="application/ld+json">{json.dumps(dados, ensure_ascii=False)}</script>'


def cabecalho(ctx):
    itens = []
    for m in SITE["menu"]:
        ativo = ' aria-current="page"' if ctx.caminho == m["link"] else ""
        if m.get("submenu"):
            sub = "".join(f'<li><a href="{esc(ctx.rel(s["link"]))}"{" aria-current=\"page\"" if ctx.caminho == s["link"] else ""}>{esc(s["texto"])}</a></li>'
                          for s in m["submenu"])
            itens.append(f'<li class="nav__sub"><a href="{esc(ctx.rel(m["link"]))}"{ativo}>{esc(m["texto"])}</a>'
                         f'<button class="nav__abre" aria-label="Abrir {esc(m["texto"])}" aria-expanded="false">▾</button>'
                         f'<ul>{sub}</ul></li>')
        else:
            itens.append(f'<li><a href="{esc(ctx.rel(m["link"]))}"{ativo}>{esc(m["texto"])}</a></li>')
    aviso = SITE["aviso"]
    return f"""<div class="announce"><b>{esc(aviso['titulo'])}</b> {esc(aviso['texto'])}</div>
<header class="header">
  <div class="wrap header__row">
    <a href="{ctx.rel('/')}" class="logo">Nouvellando<sup>®</sup></a>
    <button class="icon-btn menu-btn" aria-label="Menu" aria-expanded="false" aria-controls="nav">☰</button>
    <nav class="nav" id="nav" aria-label="Menu principal"><ul>{''.join(itens)}</ul></nav>
    <div class="header__actions">
      <button class="icon-btn" data-abre-busca aria-label="Buscar" aria-expanded="false"><svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg></button>
      <button class="icon-btn cart-btn" data-abre-carrinho aria-label="Carrinho"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 7h12l-1 13H7L6 7z"/><path d="M9 7a3 3 0 0 1 6 0"/></svg><span class="badge" data-contador hidden>0</span></button>
    </div>
  </div>
  <div class="searchbar" data-busca hidden>
    <div class="wrap"><input class="input input--pill" type="search" placeholder="Buscar cor ou fio: 785, Twinkle, Aura…" autocomplete="off" aria-label="Buscar" data-busca-campo>
      <div class="busca__resultados" data-busca-resultados></div></div>
  </div>
</header>"""


def rodape(ctx):
    r = SITE["rodape"]
    redes = "".join(f'<a href="{esc(x["link"])}" target="_blank" rel="noopener">{esc(x["texto"])}</a>' for x in r["redes"])
    produtos = "".join(f"<span>{esc(x)}</span>" for x in r["produtos"])
    return f"""<footer class="footer">
  <div class="wrap footer__grid">
    <div><a href="{ctx.rel('/')}" class="logo">Nouvellando<sup>®</sup></a><p>{esc(r['sobre'])}</p><div class="footer__redes">{redes}</div></div>
    <div><h4>{esc(r['produtos_titulo'])}</h4>{produtos}</div>
    <div><h4>{esc(r['contato_titulo'])}</h4><span>{esc(r['cidade'])}</span><a href="mailto:{r['email']}">Email: {esc(r['email'])}</a></div>
  </div>
  <div class="wrap footer__copy">{esc(r['copyright'])}</div>
</footer>
<div class="drawer" data-carrinho hidden>
  <div class="modal__backdrop" data-fecha-carrinho></div>
  <aside class="drawer__panel" aria-label="Carrinho">
    <div class="drawer__head"><h3>Seu carrinho</h3><button class="icon-btn" data-fecha-carrinho aria-label="Fechar">✕</button></div>
    <div class="drawer__items" data-carrinho-itens></div>
    <div class="drawer__foot">
      <div class="row"><span>Subtotal</span><b data-carrinho-total>R$ 0,00</b></div>
      <small>Frete e pagamento combinados no WhatsApp</small>
      <a class="btn btn--wa btn--block" data-finalizar href="{esc(SITE['whatsapp'])}" target="_blank" rel="noopener">Finalizar pedido pelo WhatsApp</a>
    </div>
  </aside>
</div>
<div class="toast" data-toast></div>
<a class="wa-float" href="{esc(SITE['whatsapp'])}" target="_blank" rel="noopener" aria-label="WhatsApp"><svg width="30" height="30" viewBox="0 0 24 24" aria-hidden="true"><path fill="#fff" d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2Zm5.3 14.1c-.2.6-1.3 1.2-1.8 1.3-.5 0-1 .2-3.2-.7-2.7-1.1-4.4-3.8-4.5-4-.1-.2-1.1-1.4-1.1-2.7 0-1.3.7-1.9.9-2.2.2-.3.5-.3.7-.3h.5c.2 0 .4 0 .6.5l.8 2c.1.2.1.4 0 .5l-.3.5-.4.4c-.1.2-.3.3-.1.6.2.3.8 1.3 1.7 2.1 1.1 1 2.1 1.3 2.4 1.5.3.1.5.1.6-.1l.9-1.1c.2-.3.4-.2.7-.1l1.9.9c.3.1.5.2.5.3.1.2.1.7-.1 1.4Z"/></svg></a>"""


def documento(p, ctx, corpo, tipo, trilha, canonica):
    robots = "" if PRODUCAO else '<meta name="robots" content="noindex, nofollow">\n'
    sob = SEO.get(ctx.caminho) or SEO.get(p["url"]) or {}
    titulo = sob.get("title") or p["title"]
    desc = descricao(p, ctx, tipo) if tipo != "404" else ""
    corpo = um_h1(corpo)
    og_img = p.get("og_image") or ""
    og_img = foto_local(og_img) or og_img
    if not foto_local(og_img) and not og_img.startswith("/wp-content/"):
        # Imagem de compartilhamento (WhatsApp, Facebook) que não é do site, ex. o
        # endereço vazio s0.wp.com/_si/ do WordPress: usa a foto do produto ou a
        # primeira foto da página
        prod = PRODUTOS.get(ctx.caminho)
        primeira = re.search(r'src="(/wp-content/[^"]+)"', corpo)
        if prod and prod.get("img") and foto_local(prod["img"]):
            og_img = foto_local(prod["img"])
        elif primeira:
            og_img = primeira.group(1)
    if og_img.startswith("/"):
        og_img = DOMINIO + og_img
    og = (f'<meta property="og:type" content="{esc(p.get("og_type") or "website")}">\n'
          f'<meta property="og:title" content="{esc(sob.get("title") or p.get("og_title") or p["title"])}">\n'
          f'<meta property="og:url" content="{esc(canonica)}">\n'
          f'<meta property="og:description" content="{esc(desc)}">\n'
          f'<meta property="og:site_name" content="{esc(SITE["nome"])}">\n'
          f'<meta property="og:locale" content="pt_BR">\n')
    if og_img and "flaticon" not in og_img and "gstatic" not in og_img:
        og += f'<meta property="og:image" content="{esc(og_img)}">\n'
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>document.documentElement.classList.add('js')</script>
{robots}<title>{esc(titulo)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{esc(canonica)}">
{og}<link rel="icon" href="{esc(img_url(FAVICON, 32))}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&amp;family=Inter:wght@400;500;600&amp;display=swap" rel="stylesheet">
<link rel="stylesheet" href="{ctx.asset('ds/tokens.css')}">
<link rel="stylesheet" href="{ctx.asset('ds/base.css')}">
<link rel="stylesheet" href="{ctx.asset('ds/components.css')}">
<link rel="stylesheet" href="{ctx.asset('site.css')}">
{json_ld(p, ctx, trilha)}
</head>
<body class="pg-{tipo}">
{cabecalho(ctx)}
<main id="conteudo">
{corpo}
</main>
{rodape(ctx)}
<script src="{ctx.asset('site.js')}" data-raiz="{'../' * ctx.prof or './'}" defer></script>
</body>
</html>
"""


def tipo_de(slug):
    if slug == "home":
        return "home"
    if eh_produto(slug):
        return "produto"
    if slug in CATEGORIAS:
        return "categoria"
    if slug.startswith("videoaula-") or slug == "echarpe-wheel-of-time":
        return "videoaula"
    return slug


def redirecionamento(destino, ctx):
    alvo = ctx.rel(destino)
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<title>Nouvellando®</title>
<link rel="canonical" href="{DOMINIO}{destino}">
<meta http-equiv="refresh" content="0; url={alvo}">
<script>location.replace("{alvo}"+location.search+location.hash)</script>
</head><body><a href="{alvo}">{DOMINIO}{destino}</a></body></html>
"""


# Endereços típicos do WordPress que não existem no site novo -> página mais próxima
REDIRECIONA_WORDPRESS = {
    "/feed/": "/", "/comments/feed/": "/", "/wp-admin/": "/", "/wp-login.php": "/",
    "/carrinho/": "/", "/finalizar-compra/": "/", "/checkout/": "/", "/cart/": "/",
    "/shop/": "/fios-nouvellando/", "/sitemap_index.xml": "/sitemap.xml",
    "/wp-sitemap.xml": "/sitemap.xml", "/image-sitemap.xml": "/sitemap.xml",
}
POR_PAGINA = 48           # cores mostradas por vez nos catálogos grandes ("Ver mais cores")
LIMITE_REDIRECTS = 2000   # regras estáticas que o Cloudflare Pages aceita no _redirects


def arquivos_cloudflare(mapa, pags):
    """Gera site/_redirects (301 de verdade no Cloudflare) e site/_headers.

    O GitHub Pages ignora esses arquivos; lá continuam valendo as páginas de
    redirecionamento em HTML, geradas para cada endereço antigo.
    Retorna o número de regras do _redirects."""
    regras = {}

    def regra(de, para):
        if de != para and de not in regras:
            regras[de] = para

    # 1) Páginas: endereço antigo de cada produto, páginas duplicadas e links que
    #    o WordPress já redirecionava. Com e sem a barra no fim, para cobrir os dois jeitos
    #    que o link pode ter sido salvo.
    for antigo, destino in sorted(mapa.items()):
        regra(antigo, destino)
        if antigo.endswith("/") and len(antigo) > 1:
            regra(antigo.rstrip("/"), destino)
    for antigo, destino in REDIRECIONA_WORDPRESS.items():
        regra(antigo, destino)
    # 2) Fotos: versões redimensionadas do WordPress (foto-1024x1024.jpg) e PNG que
    #    virou JPG -> foto otimizada. Mantém links do Google Imagens funcionando.
    variantes = set()
    for p in pags.values():
        variantes |= set(re.findall(r'/wp-content/uploads/[^"?) ]+-\d+x\d+\.[A-Za-z]+', json.dumps(p)))
    for v in sorted(variantes):
        local = foto_local(v)
        if local:
            regra(v, local)
    for antigo, novo in sorted(FOTOS.items()):
        regra(antigo, novo)

    texto = ["# Gerado por ferramentas/gerar.py. Nao editar a mao: mude conteudo/redirecionamentos.json.",
             "# Endereco antigo -> endereco novo, 301 (permanente)."]
    texto += [f"{de} {para} 301" for de, para in regras.items()]
    (SAIDA / "_redirects").write_text("\n".join(texto) + "\n", encoding="utf-8")

    # Endereços *.pages.dev (teste e prévias) nunca entram no Google, mesmo na versão de
    # produção: só o domínio oficial deve ser indexado.
    (SAIDA / "_headers").write_text(
        "# Gerado por ferramentas/gerar.py\n"
        "https://:project.pages.dev/*\n  X-Robots-Tag: noindex\n"
        "https://:version.:project.pages.dev/*\n  X-Robots-Tag: noindex\n"
        "/wp-content/*\n  Cache-Control: public, max-age=604800\n",
        encoding="utf-8")
    return len(regras)


def grava(caminho, conteudo):
    destino = SAIDA / caminho.strip("/") / "index.html" if caminho != "/" else SAIDA / "index.html"
    destino.parent.mkdir(parents=True, exist_ok=True)
    # Fotos do próprio site com caminho relativo, para funcionar também num
    # endereço de teste dentro de uma pasta (ex.: usuario.github.io/nouvellando/)
    prof = caminho.strip("/").count("/") + 1 if caminho != "/" else 0
    conteudo = conteudo.replace('="/wp-content/', '="' + "../" * prof + "wp-content/")
    destino.write_text(conteudo, encoding="utf-8")


def main():
    pags = carrega_paginas()
    novo, duplicadas = mapa_produtos(pags)
    mapa = {**novo, **duplicadas}
    # Redirecionamentos que o site atual já tinha (seguindo até o endereço novo)
    antigos = json.loads((CONTEUDO / "redirecionamentos.json").read_text(encoding="utf-8"))
    for de, para in antigos.items():
        if de.startswith("/"):
            mapa[de] = mapa.get(para, para)

    if SAIDA.exists():
        shutil.rmtree(SAIDA)
    (SAIDA / "assets").mkdir(parents=True)
    shutil.copytree(RAIZ / "assets", SAIDA / "assets", dirs_exist_ok=True)
    for css in ("tokens.css", "base.css", "components.css"):
        (SAIDA / "assets" / "ds").mkdir(exist_ok=True)
        shutil.copy(RAIZ / "design-system" / css, SAIDA / "assets" / "ds" / css)
    (SAIDA / ".nojekyll").write_text("", encoding="utf-8")
    if FOTOS_DIR.exists():
        shutil.copytree(FOTOS_DIR, SAIDA / "wp-content")

    for slug, p in pags.items():
        if tipo_de(slug) == "produto" and p["url"] not in duplicadas:
            caminho = novo[p["url"]]
            PRODUTOS[caminho] = dados_produto(p, caminho, caminho.split("/")[1])

    carrega_cursos(pags)
    if "fio-original" in pags:
        cat = pags["fio-original"]
        for d in produtos_da_pagina(cat, Ctx("/fio-original/", mapa)):
            if d["preco_min"] is not None:
                NOVIDADES.append(d["caminho"])

    publicadas = []
    for slug, p in pags.items():
        tipo = tipo_de(slug)
        caminho = novo.get(p["url"], p["url"]) if tipo == "produto" else p["url"]
        if tipo == "produto" and p["url"] in duplicadas:
            continue
        if tipo != "produto" and p["url"] in mapa:
            continue  # página redirecionada (conteudo/redirecionamentos.json): não entra no site nem no sitemap
        ctx = Ctx(caminho, mapa)
        nome = nome_pagina(p)
        if tipo == "produto":
            linha = caminho.split("/")[1]
            trilha = [("Início", "/"), (SITE["nomes_linhas"].get(linha, linha), f"/{linha}/"), (nome, None)]
            corpo = corpo_produto(p, ctx, trilha, PRODUTOS[caminho])
        elif tipo == "videoaula":
            trilha = [("Início", "/"), ("Videoaulas", "/cursos/"), (nome, None)]
            corpo = corpo_dividido(p, ctx, trilha)
        elif slug == "fios-nouvellando":
            trilha = [("Início", "/"), (nome, None)]
            corpo = corpo_fios(p, ctx)
        elif tipo == "cursos" and CURSOS:
            trilha = [("Início", "/"), (nome, None)]
            corpo = corpo_cursos(p, ctx)
        else:
            trilha = [("Início", "/"), (nome, None)]
            corpo = corpo_secoes(p, ctx, tipo)
        canonica = DOMINIO + caminho
        grava(caminho, documento(p, ctx, corpo, tipo, trilha, canonica))
        publicadas.append((caminho, p.get("modificado") or p.get("publicado") or ""))

    # Índice da busca (produtos e linhas)
    indice = [{"n": d["nome"], "u": c, "i": img_url(d["img"], 120) if d["img"] else "", "l": d["linha_nome"],
               "p": reais(d["preco_min"]) if d["preco_min"] is not None else ""} for c, d in PRODUTOS.items()]
    indice += [{"n": m["texto"], "u": m["link"], "i": "", "l": "Linha de fio", "p": ""}
               for m in SITE["menu"][1]["submenu"]]
    (SAIDA / "assets" / "busca.json").write_text(json.dumps(indice, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    # Endereços antigos dos produtos e páginas duplicadas -> endereço novo
    for antigo, destino in mapa.items():
        grava(antigo, redirecionamento(destino, Ctx(antigo, {})))

    # Página 404
    ctx404 = Ctx("/404/", mapa)
    p404 = {"url": "/404/", "title": "Página não encontrada – Nouvellando®", "description": "", "blocos": []}
    corpo404 = (f'<div class="wrap vazio"><h1>Página não encontrada</h1>'
                f'<a class="btn btn--primary" href="{ctx404.rel("/fios-nouvellando/")}">Nossos fios</a></div>')
    doc404 = documento(p404, ctx404, corpo404, "404", [("Início", "/")], DOMINIO + "/")
    # O 404 é servido em qualquer profundidade, então usa caminhos absolutos
    (SAIDA / "404.html").write_text(doc404.replace('href="../', 'href="/').replace('src="../', 'src="/'), encoding="utf-8")

    # Lista de redirecionamentos (para configurar 301 no servidor final)
    linhas = ["endereco_antigo,endereco_novo"] + [f"{a},{d}" for a, d in sorted(mapa.items())]
    (RAIZ / "migracao" / "redirecionamentos-produtos.csv").write_text("\n".join(linhas) + "\n", encoding="utf-8")

    n_redir = arquivos_cloudflare(mapa, pags)

    if PRODUCAO:
        urls = "".join(f"<url><loc>{DOMINIO}{c}</loc>{f'<lastmod>{m[:10]}</lastmod>' if m else ''}</url>"
                       for c, m in sorted(publicadas))
        (SAIDA / "sitemap.xml").write_text(
            f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n',
            encoding="utf-8")
        (SAIDA / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {DOMINIO}/sitemap.xml\n", encoding="utf-8")
    else:
        (SAIDA / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")

    print(f"{len(publicadas)} páginas geradas, {len(mapa)} redirecionamentos, em {SAIDA}"
          f" ({'produção' if PRODUCAO else 'teste, noindex'})")
    print(f"_redirects do Cloudflare: {n_redir} regras 301 (limite do Cloudflare Pages: {LIMITE_REDIRECTS})")
    if n_redir > LIMITE_REDIRECTS:
        print("ATENÇÃO: passou do limite; o Cloudflare ignora o que vier depois. Mover parte para Bulk Redirects.")
    if FOTOS_FALTANDO:
        print(f"Atenção: {len(FOTOS_FALTANDO)} foto(s) ainda vêm do WordPress (não estão em conteudo/fotos.json):")
        for f in sorted(FOTOS_FALTANDO):
            print("  " + f)


if __name__ == "__main__":
    main()
