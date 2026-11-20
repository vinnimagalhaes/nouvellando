# Site Nouvellando

Site novo da Nouvellando: **mesmas URLs e mesmos textos** do site atual (nouvellando.com.br, WordPress), com o design novo.
O objetivo é trocar de site sem perder o ranqueamento no Google.

## Como funciona

```
conteudo/paginas/*.json   texto de cada página, copiado do site atual (1 arquivo por URL)
conteudo/site.json        menu, aviso do topo, rodapé, WhatsApp
conteudo/redirecionamentos.json   redirecionamentos que o WordPress já fazia
assets/                   CSS, JS e ícones do site
design-system/            tokens e componentes visuais (cores, fontes, botões…)
ferramentas/gerar.py      monta o site em site/ (só Python, sem instalar nada)
ferramentas/extrair.py    lê o HTML do site atual e grava conteudo/paginas/
```

Para ver o site no computador:

```bash
python3 ferramentas/gerar.py
python3 -m http.server 5173 -d site
```

e abrir http://localhost:5173.

## URLs

| Página | Endereço |
|---|---|
| Home | `/` |
| Nossos fios | `/fios-nouvellando/` |
| Catálogo de cada fio | `/fio-original/`, `/fio-twinkle/`, … `/novelos-sem-degrade/` |
| Videoaulas | `/cursos/` e `/videoaula-xale-…/` |
| Sobre | `/sobre-a-nouvellando/` |
| **Produto (cor)** | **dentro da linha:** `/fio-original/805-805u/` |

Todas as páginas mantêm o endereço do site atual, **menos os produtos**, que passam a ficar dentro da linha do fio.
O endereço antigo de cada produto (`/original-805-805u/`) continua existindo e leva para o novo, para o Google transferir o ranqueamento.
A lista completa fica em `migracao/redirecionamentos-produtos.csv`; no servidor definitivo, o ideal é transformá-la em redirecionamentos 301.

**Página de produto (loja):** as tabelas de preço viram opções (cor, cabos, com ou sem brilho, metragem). Preço e peso saem das próprias tabelas da página, então mudar um preço continua sendo editar a tabela no JSON do produto. O carrinho fica guardado no navegador e o pedido é finalizado pelo WhatsApp, com a mensagem já preenchida.

Também mantidos iguais ao site atual: título da aba (`<title>`), meta description, títulos (H1, H2…) e o que aparece só no computador ou só no celular.

## Editar um texto

Abra o JSON da página em `conteudo/paginas/` (o nome é o endereço antigo, ex.: `fio-original.json`, `original-805-805u.json`), altere o texto e rode `python3 ferramentas/gerar.py`.

## SEO

- Cada página tem **um H1 só** (o `gerar.py` transforma os H1 extras em parágrafo com a mesma aparência).
- **Descrição** (texto que aparece no Google): escrita à mão em `conteudo/seo.json` para as páginas principais (dá para trocar também o título da aba ali). As demais são montadas automaticamente: produtos com nome, cabos e preço; linhas de fio com número de cores e preço.
- Fotos sem texto alternativo usam a legenda (nome da cor).
- Catálogos com mais de 96 cores (Fio Original) mostram 48 por vez, com o botão "Ver mais cores" (`POR_PAGINA` no `gerar.py`). Todas as cores continuam no HTML, para o Google seguir os links; sem JavaScript, aparece tudo.
- Links que nunca existiram e páginas de sistema do WordPress (`/loja/`, `/minha-conta/`) estão em `conteudo/redirecionamentos.json`.

## Publicar

O GitHub Actions (`.github/workflows/publicar.yml`) gera o site e publica no GitHub Pages a cada push na `main`.
Para ativar: **Settings → Pages → Source: GitHub Actions**.

A versão publicada é de teste: não aparece no Google (`noindex` e `robots.txt` bloqueando).
Na troca de domínio, gere com `python3 ferramentas/gerar.py --producao`: tira o bloqueio e cria o `sitemap.xml`.

## Pendências antes da troca de domínio

- **Imagens:** as fotos já ficam no próprio site, em `wp-content/uploads/` (mesmo caminho do WordPress), otimizadas em um arquivo por foto, no tamanho em que ela aparece no site: fotos de novelo com até 1000 px, fotos em pé (xales, videoaulas) com até 900 px de largura, os fundos de tela inteira listados em `conteudo/fotos-grandes.txt` com 1440 px de largura, e banners e artes com texto no tamanho original (até 1920 px de largura, qualidade alta). `conteudo/fotos.json` diz qual arquivo usar para cada endereço antigo. Para foto nova: `powershell -ExecutionPolicy Bypass -File ferramentas\otimizar-fotos.ps1 -Lista <tsv com endereço e arquivo original>`. O `gerar.py` avisa no fim se alguma foto ainda vem do WordPress (hoje só `149.jpg` e `287l-n.jpg`, que já estão quebradas no site atual).
- **Redirecionamentos do WordPress:** exportar a lista completa (só 6 foram achados pelos links do site, em `conteudo/redirecionamentos.json`).
- Detalhes do levantamento em `migracao/README.md`.
