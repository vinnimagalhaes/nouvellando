"""Testa se TODOS os endereços do site antigo (WordPress) funcionam no site novo.

Para cada endereço antigo, segue os redirecionamentos e confere:
  - que termina numa página que existe (200), nunca num erro 404;
  - que o primeiro redirecionamento é 301 (permanente), o que o Google usa
    para transferir o ranqueamento;
  - quantos saltos foram necessários (o ideal é 1).

Uso:
  python ferramentas/testar-redirecionamentos.py https://nouvellando.pages.dev
  python ferramentas/testar-redirecionamentos.py https://nouvellando.com.br     (no dia da troca)

Só usa a biblioteca padrão do Python. Grava o relatório completo em
migracao/teste-redirecionamentos.csv.
"""
import csv
import json
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urljoin, urlparse

RAIZ = Path(__file__).resolve().parent.parent
MAX_SALTOS = 5


class SemSeguir(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


abrir = urllib.request.build_opener(SemSeguir).open


def enderecos_antigos():
    """Todos os endereços do levantamento do site atual + redirecionamentos conhecidos."""
    caminhos = set()
    for item in json.loads((RAIZ / "migracao" / "conteudo-completo.json").read_text(encoding="utf-8")):
        caminhos.add(urlparse(item["url"]).path or "/")
    for de in json.loads((RAIZ / "conteudo" / "redirecionamentos.json").read_text(encoding="utf-8")):
        if de.startswith("/"):
            caminhos.add(de)
    # Uma amostra de fotos: o endereço original e as versões redimensionadas que o site atual usa
    fotos = json.loads((RAIZ / "conteudo" / "fotos.json").read_text(encoding="utf-8"))
    for f in list(fotos)[:: max(1, len(fotos) // 40)]:
        caminhos.add(f)
    variantes = set()
    for arq in (RAIZ / "conteudo" / "paginas").glob("*.json"):
        variantes |= set(re.findall(r'/wp-content/uploads/[^"?) ]+-\d+x\d+\.[A-Za-z]+', arq.read_text(encoding="utf-8")))
    caminhos |= set(sorted(variantes)[:: max(1, len(variantes) // 40)])
    return sorted(caminhos)


def testa(base, caminho):
    url = base + caminho
    saltos, primeiro = [], None
    for _ in range(MAX_SALTOS + 1):
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": "teste-redirecionamentos"})
        try:
            r = abrir(req, timeout=30)
            status = r.status
            inicio = r.read(3000) if "html" in (r.headers.get("Content-Type") or "") else b""
            r.close()
            if b'http-equiv="refresh"' in inicio:
                # Página que só redireciona pelo navegador (não é 301 de verdade)
                return {"antigo": caminho, "primeiro": "html", "saltos": len(saltos) + 1,
                        "final_status": "so-navegador", "final": urlparse(url).path}
        except urllib.error.HTTPError as e:
            status = e.code
            if 300 <= status < 400:
                destino = e.headers.get("Location")
                primeiro = primeiro or status
                saltos.append(status)
                url = urljoin(url, destino)
                continue
        return {"antigo": caminho, "primeiro": primeiro or status, "saltos": len(saltos),
                "final_status": status, "final": urlparse(url).path}
    return {"antigo": caminho, "primeiro": primeiro, "saltos": len(saltos),
            "final_status": "loop", "final": urlparse(url).path}


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    base = sys.argv[1].rstrip("/")
    caminhos = enderecos_antigos()
    print(f"Testando {len(caminhos)} endereços antigos em {base} …")
    with ThreadPoolExecutor(max_workers=12) as ex:
        res = list(ex.map(lambda c: testa(base, c), caminhos))

    so_navegador = [r for r in res if r["final_status"] == "so-navegador"]
    erros = [r for r in res if r["final_status"] not in (200, "so-navegador")]
    nao_301 = [r for r in res if r["saltos"] and r["primeiro"] != 301]
    longos = [r for r in res if r["saltos"] > 1]
    print(f"  {sum(1 for r in res if r['final_status'] == 200 and not r['saltos'])} abrem direto (200)")
    print(f"  {sum(1 for r in res if r['final_status'] == 200 and r['saltos'])} redirecionam e chegam numa página que existe")
    print(f"  {len(so_navegador)} redirecionam só pelo navegador (página HTML, sem 301)")
    print(f"  {len(erros)} terminam em erro (404 ou outro)")
    print(f"  {len(nao_301)} redirecionam sem ser 301 (Google transfere pior)")
    print(f"  {len(longos)} precisam de mais de um salto")
    for r in (erros + nao_301)[:15]:
        print(f"    {r['antigo']} -> {r['final']} ({r['final_status']}, primeiro {r['primeiro']})")

    saida = RAIZ / "migracao" / "teste-redirecionamentos.csv"
    with saida.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(res[0]))
        w.writeheader()
        w.writerows(res)
    print(f"Relatório completo: {saida.relative_to(RAIZ)}")
    sys.exit(1 if erros else 0)


if __name__ == "__main__":
    main()
