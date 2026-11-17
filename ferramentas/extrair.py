"""Extrai o conteúdo das páginas do site atual (WordPress + Elementor).

Lê o HTML salvo de cada URL e grava um JSON por página em conteudo/paginas/,
com os blocos na mesma ordem e com o mesmo texto do site atual.

Uso:
  pip install beautifulsoup4
  python3 ferramentas/extrair.py <pasta-com-os-html> [lista-de-urls.txt]

Cada HTML deve se chamar <slug>.html (a home é home.html).
"""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse, unquote

from bs4 import BeautifulSoup, NavigableString, Tag

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "conteudo" / "paginas"
DOMINIO = "https://nouvellando.com.br"

# Tags e atributos mantidos no HTML dos blocos de texto
TAGS_OK = {"p", "br", "strong", "b", "em", "i", "u", "a", "ul", "ol", "li",
           "h1", "h2", "h3", "h4", "h5", "h6", "span", "img", "s", "sup", "sub", "blockquote"}


def limpa_url_imagem(src):
    """Converte a URL do Jetpack (i0.wp.com) no caminho original do WordPress."""
    if not src:
        return ""
    src = src.strip()
    m = re.match(r"https?://i\d\.wp\.com/(.+)", src)
    if m:
        src = "https://" + m.group(1)
    src = src.split("?")[0]
    if src.startswith(DOMINIO):
        src = src[len(DOMINIO):]
    return src


def limpa_link(href):
    if not href:
        return ""
    href = href.strip()
    if href.startswith(DOMINIO):
        caminho = href[len(DOMINIO):] or "/"
        if not caminho.endswith("/") and "." not in caminho.split("/")[-1] and "#" not in caminho and "?" not in caminho:
            caminho += "/"
        return caminho
    return href


def ocultos(el):
    classes = el.get("class") or []
    return [d for d in ("desktop", "tablet", "mobile") if f"elementor-hidden-{d}" in classes]


def html_limpo(el):
    """HTML interno sem estilos, scripts e atributos do Elementor."""
    frag = BeautifulSoup(el.decode_contents(), "html.parser")
    for t in frag.find_all(["script", "style", "svg", "noscript"]):
        t.decompose()
    for t in frag.find_all(True):
        if t.name not in TAGS_OK:
            t.unwrap()
            continue
        attrs = {}
        if t.name == "a" and t.get("href"):
            attrs["href"] = limpa_link(t["href"])
            if t.get("target") == "_blank":
                attrs["target"] = "_blank"
        if t.name == "img":
            attrs["src"] = limpa_url_imagem(t.get("src") or t.get("data-src"))
            attrs["alt"] = t.get("alt", "")
            for k in ("width", "height"):
                if t.get(k):
                    attrs[k] = t[k]
        t.attrs = attrs
    # span sem atributo não serve para nada
    for t in frag.find_all("span"):
        t.unwrap()
    texto = str(frag).strip()
    texto = re.sub(r"\n\s*\n", "\n", texto)
    return texto


def texto(el):
    return re.sub(r"[ \t\r\f\v]+", " ", el.get_text(" ", strip=True)).strip()


def img_dados(img):
    if not img:
        return None
    src = img.get("data-orig-file") or img.get("data-src") or img.get("src") or ""
    return {
        "src": limpa_url_imagem(src),
        "alt": img.get("alt", ""),
        "w": img.get("width") or None,
        "h": img.get("height") or None,
    }


def widget(w):
    tipo = w.get("data-widget_type", "").split(".")[0]
    b = {"tipo": tipo}
    esc = ocultos(w)
    if esc:
        b["oculto"] = esc

    if tipo == "spacer":
        return None
    if tipo == "heading":
        h = w.find(class_="elementor-heading-title") or w
        b["tag"] = h.name if h.name in ("h1", "h2", "h3", "h4", "h5", "h6", "p", "div", "span") else "h2"
        b["texto"] = texto(h)
        a = h.find("a")
        if a and a.get("href"):
            b["link"] = limpa_link(a["href"])
        return b
    if tipo == "text-editor":
        b["html"] = html_limpo(w.find(class_="elementor-widget-container") or w)
        return b
    if tipo == "image":
        img = w.find("img")
        b["img"] = img_dados(img)
        a = w.find("a")
        if a and a.get("href"):
            b["link"] = limpa_link(a["href"])
        cap = w.find("figcaption")
        if cap:
            b["legenda"] = texto(cap)
        return b
    if tipo == "image-carousel":
        slides = []
        for s in w.select(".swiper-slide"):
            if "swiper-slide-duplicate" in (s.get("class") or []):
                continue
            img = s.find("img")
            if not img:
                continue
            item = img_dados(img)
            a = s.find("a")
            if a and a.get("href") and not a["href"].startswith("#"):
                item["link"] = limpa_link(a["href"])
            cap = s.find("figcaption")
            if cap:
                item["legenda"] = texto(cap)
            slides.append(item)
        b["slides"] = slides
        try:
            cfg = json.loads(w.get("data-settings") or "{}")
        except ValueError:
            cfg = {}
        por_tela = {}
        for chave, tela in (("slides_to_show", "desktop"), ("slides_to_show_tablet", "tablet"),
                            ("slides_to_show_mobile", "mobile")):
            if str(cfg.get(chave, "")).isdigit():
                por_tela[tela] = int(cfg[chave])
        if por_tela:
            b["por_tela"] = por_tela
        if cfg.get("autoplay") == "yes":
            b["autoplay"] = int(cfg.get("autoplay_speed") or 5000)
        return b
    if tipo == "button":
        a = w.find("a") or w.find("button")
        b["texto"] = texto(w)
        if a and a.get("href"):
            b["link"] = limpa_link(a["href"])
        return b
    if tipo in ("accordion", "toggle", "n-accordion", "tabs"):
        itens = []
        for item in w.select(".elementor-accordion-item, .elementor-toggle-item"):
            t = item.find(class_="elementor-tab-title")
            c = item.find(class_="elementor-tab-content")
            itens.append({"titulo": texto(t) if t else "", "html": html_limpo(c) if c else ""})
        b["itens"] = itens
        return b
    if tipo == "divider":
        return b
    if tipo == "icon-list":
        itens = []
        for li in w.select(".elementor-icon-list-item"):
            i = {"texto": texto(li)}
            a = li.find("a")
            if a and a.get("href"):
                i["link"] = limpa_link(a["href"])
            itens.append(i)
        b["itens"] = itens
        return b
    if tipo == "image-box":
        b["img"] = img_dados(w.find("img"))
        t = w.find(class_="elementor-image-box-title")
        d = w.find(class_="elementor-image-box-description")
        b["titulo"] = texto(t) if t else ""
        b["titulo_tag"] = t.name if t else "h3"
        b["descricao"] = html_limpo(d) if d else ""
        a = w.find("a")
        if a and a.get("href"):
            b["link"] = limpa_link(a["href"])
        return b
    if tipo == "nested-tabs":
        titulos = [texto(t) for t in w.select(".e-n-tab-title")]
        conteudo = w.select_one(".e-n-tabs-content")
        paineis = [c for c in conteudo.children if isinstance(c, Tag)] if conteudo else []
        abas = []
        for i, painel in enumerate(paineis):
            sub = []
            percorre(painel, sub)
            abas.append({"titulo": titulos[i] if i < len(titulos) else "", "blocos": sub})
        b["tipo"] = "abas"
        b["abas"] = abas
        return b
    if tipo == "video":
        cfg = w.get("data-settings") or ""
        m = re.search(r'"(?:youtube|vimeo|external)_url":"([^"]+)"', cfg)
        b["url"] = m.group(1).replace("\\/", "/") if m else ""
        return b
    if tipo == "html":
        b["html"] = html_limpo(w)
        return b
    # Tipo não previsto: guarda o texto para não perder nada
    b["html"] = html_limpo(w)
    b["texto"] = texto(w)
    return b


def percorre(el, blocos):
    for filho in el.children:
        if not isinstance(filho, Tag):
            continue
        tipo_el = filho.get("data-element_type")
        if tipo_el == "widget":
            b = widget(filho)
            if b:
                blocos.append(b)
        elif tipo_el in ("container", "section", "column"):
            esc = ocultos(filho)
            sub = []
            percorre(filho, sub)
            if not sub:
                continue
            g = {"tipo": "grupo", "blocos": sub}
            if esc:
                g["oculto"] = esc
            blocos.append(g)
        else:
            percorre(filho, blocos)


def meta(soup, nome, prop=False):
    m = soup.find("meta", attrs={("property" if prop else "name"): nome})
    return m.get("content", "") if m else ""


def extrai(html, url):
    soup = BeautifulSoup(html, "html.parser")
    caminho = urlparse(url).path or "/"
    slug = caminho.strip("/") or "home"
    pag = {
        "url": caminho,
        "slug": slug,
        "title": texto(soup.title) if soup.title else "",
        "description": meta(soup, "description"),
        "og_title": meta(soup, "og:title", True),
        "og_type": meta(soup, "og:type", True),
        "og_image": limpa_url_imagem(meta(soup, "og:image", True)),
        "publicado": meta(soup, "article:published_time", True),
        "modificado": meta(soup, "article:modified_time", True),
    }
    principal = soup.find(attrs={"data-elementor-type": re.compile(r"^wp-(page|post)$")})
    blocos = []
    if principal:
        percorre(principal, blocos)
    else:
        corpo = soup.find(class_="entry-content") or soup.find("main")
        if corpo and texto(corpo):
            blocos.append({"tipo": "text-editor", "html": html_limpo(corpo)})
        h1 = soup.find("h1")
        if h1:
            pag["h1_tema"] = texto(h1)
    pag["blocos"] = blocos
    return pag


def main():
    pasta = Path(sys.argv[1])
    urls = None
    if len(sys.argv) > 2:
        urls = [u.strip() for u in Path(sys.argv[2]).read_text().splitlines() if u.strip()]
    SAIDA.mkdir(parents=True, exist_ok=True)
    feitos = 0
    for arq in sorted(pasta.glob("*.html")):
        slug = arq.stem
        url = f"{DOMINIO}/" if slug == "home" else f"{DOMINIO}/{slug}/"
        if urls and url not in urls:
            continue
        pag = extrai(arq.read_text(errors="replace"), url)
        (SAIDA / f"{slug}.json").write_text(json.dumps(pag, ensure_ascii=False, indent=1))
        feitos += 1
    print(f"{feitos} páginas extraídas para {SAIDA}")


if __name__ == "__main__":
    main()
