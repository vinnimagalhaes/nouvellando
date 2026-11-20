# Publicar o site novo no Cloudflare (sair do WordPress.com)

Levantamento feito em 19/11/2026, olhando o código do repositório e o DNS atual do domínio.

## Como está hoje

| Item | Situação |
|---|---|
| Hospedagem do site atual | **WordPress.com** (IPs 192.0.78.151 / 192.0.78.233) |
| DNS do domínio | Também no WordPress.com (`ns1/ns2/ns3.wordpress.com`) |
| Registro do domínio `.com.br` | Registro.br (é onde se troca os nameservers) |
| E-mail no domínio | **Não há** registro MX, então não existe e-mail `@nouvellando.com.br` para perder |
| Outros registros | Só um SPF do WordPress.com (`include:_spf.wpcloud.com`), que deixa de ser necessário |
| Site novo | Gerado por `ferramentas/gerar.py`, publicado hoje no GitHub Pages (versão de teste, `noindex`) |

## Erros possíveis (e como evitar cada um)

### Críticos: quebram o site no dia da troca

1. **As imagens somem.**
   Todas as fotos do site novo vêm de `i0.wp.com/nouvellando.com.br/wp-content/uploads/...`, ou seja, do WordPress.
   Quando o domínio apontar para o Cloudflare, esse endereço deixa de existir.
   **Solução:** baixar a biblioteca de mídia, colocar só os arquivos usados (cerca de 1.773) no próprio site, no mesmo caminho `/wp-content/uploads/...`, e trocar o `img_url()` do `gerar.py` para usar esses arquivos.
   Para os tamanhos (`srcset`), a opção mais simples é o redimensionamento de imagens do Cloudflare.
   Isso inclui o logo e o favicon, que também apontam para o `i0.wp.com`.

2. **Os redirecionamentos não são 301 de verdade.**
   Os 801 endereços antigos de produto (`/original-805-805u/` → `/fio-original/805-805u/`) hoje são páginas HTML com `meta refresh`.
   O Google aceita esse tipo de redirecionamento, mas transfere o ranqueamento de forma mais lenta e menos garantida.
   **Feito (20/11):** o `gerar.py` gera `site/_redirects`, que o Cloudflare transforma em 301. São cerca de 1.940 regras
   (produtos e páginas com e sem barra no fim, fotos redimensionadas, PNG que virou JPG e endereços do WordPress),
   para um limite de 2.000. O gerar.py avisa se passar do limite.

3. **Site no ar sem o modo produção.**
   Se o build não usar `--producao`, o site entra no ar com `noindex` e `robots.txt` bloqueando tudo, e some do Google.
   **Solução:** no dia da troca, conferir se `/robots.txt` mostra `Allow: /` e se o código da página não tem `noindex`.

4. **Indexação antes da hora / conteúdo duplicado.**
   Se o build de produção rodar antes da troca, o endereço `xxx.pages.dev` fica indexável com o mesmo conteúdo do site atual.
   **Solução:** só ligar o `--producao` no dia da troca. **Feito (20/11):** o `gerar.py` gera `site/_headers` com
   `X-Robots-Tag: noindex` para os endereços `*.pages.dev`, que valem também depois da troca.
   Desligar também o GitHub Pages depois que o Cloudflare estiver funcionando.

### Importantes: prejudicam o SEO ou a operação

5. **Redirecionamentos antigos do WordPress.** Só 6 são conhecidos (`conteudo/redirecionamentos.json`). O WordPress.com também redireciona sozinho as páginas que mudaram de endereço. Exportar ou levantar a lista antes de desligar.
6. **`www` e domínio sem `www`.** O endereço oficial é `https://nouvellando.com.br`. É preciso adicionar o `www` no Cloudflare e redirecionar com 301 para o domínio sem `www`.
7. **Endereços típicos do WordPress** (`/feed/`, `/wp-admin/`, `/loja/`, `/minha-conta/`, `/sitemap.xml` antigo). **Feito (20/11):** redirecionam para a home ou a página mais próxima (`REDIRECIONA_WORDPRESS` no `gerar.py` e `conteudo/redirecionamentos.json`).
   Fotos em tamanhos que o site não usa (o WordPress cria vários por foto) ainda dariam 404; só afeta o Google Imagens.
8. **Ícones externos.** Há mais de 2.400 links para ícones do Google Imagens e do Flaticon no conteúdo. O `gerar.py` já troca os ícones de cuidado por arquivos locais, mas é bom conferir no site gerado se sobrou algum endereço externo.
9. **Verificação do Google Search Console.** Se hoje a verificação é feita pelo WordPress.com, ela se perde na troca. Antes da troca, verificar o domínio por DNS (registro TXT) no Cloudflare.
10. **Pendências de conteúdo** (de `migracao/README.md`):
    - páginas duplicadas;
    - tabela de preços única por linha, confirmada pela cliente;
    - aviso de férias do topo (`conteudo/site.json`) com datas.

### Menores

11. **Gerar o site no Windows.** O `gerar.py` lê e grava arquivos sem informar `encoding="utf-8"`. No Windows isso pode estragar os acentos ou dar erro. No Cloudflare (Linux) funciona. Vale corrigir para quem testa em casa.
12. **Rodar o `gerar.py` no computador** reescreve `migracao/redirecionamentos-produtos.csv`, que é um arquivo do repositório. Conferir o `git status` antes de commitar.

## Passo a passo

### Fase 1: preparar (sem mexer no site atual)

1. **Acessos necessários:**
   - painel do WordPress.com;
   - Registro.br (titular do domínio);
   - conta do Cloudflare;
   - Google Search Console;
   - GitHub (o dono do repositório autoriza o Cloudflare).
2. **Backup do WordPress.com:** Ferramentas → Exportar → exportar todo o conteúdo e a biblioteca de mídia. Guardar fora do WordPress.
3. **Ajustes no código** (erros 1, 2, 4, 6, 7, 11):
   - imagens hospedadas no próprio site;
   - geração do `_redirects` e do `_headers`;
   - leitura e gravação em UTF-8.
4. **Fechar as pendências de conteúdo** (erro 10).

### Fase 2: publicar em endereço de teste no Cloudflare

5. **Cloudflare → Workers & Pages → Create → Pages → Connect to Git**, escolhendo o repositório `nouvellando`:
   - Branch de produção: `main`
   - Comando de build: `python ferramentas/gerar.py` (ainda **sem** `--producao`)
   - Pasta de saída: `site`
6. **Testar o endereço `xxx.pages.dev`:**
   - menu e páginas;
   - busca;
   - carrinho e WhatsApp;
   - fotos (já servidas pelo próprio site);
   - celular;
   - página 404.
7. **Conferir os endereços** com `python ferramentas/testar-redirecionamentos.py https://nouvellando.pages.dev`:
   - testa as 843 URLs do site atual, os redirecionamentos conhecidos e uma amostra de fotos;
   - todas devem abrir (200) ou redirecionar com **301** para uma página que existe;
   - nenhum endereço pode dar 404. Repetir no dia da troca com `https://nouvellando.com.br`.

### Fase 3: preparar o DNS (ainda sem trocar)

8. **Cloudflare → Add a domain → `nouvellando.com.br`** (plano Free).
   O Cloudflare importa os registros atuais. Conferir a lista; hoje não há e-mail para preservar.
9. **Anotar os dois nameservers** que o Cloudflare informar.

### Fase 4: o dia da troca (de preferência num horário de pouco movimento)

10. **Mudar o comando de build** para `python ferramentas/gerar.py --producao`, fazer um novo deploy e conferir o `robots.txt` e o `sitemap.xml` no endereço `pages.dev`.
11. **Registro.br → domínio → DNS → trocar os nameservers** do WordPress.com pelos do Cloudflare.
    A troca leva de alguns minutos a algumas horas para valer em todo lugar.
12. **Cloudflare Pages → Custom domains:** adicionar `nouvellando.com.br` e `www.nouvellando.com.br`.
    O certificado HTTPS é emitido sozinho.
13. **Testar no domínio real:**
    - home, uma categoria e um produto;
    - um endereço antigo de produto, que deve dar 301;
    - `www` redirecionando para o domínio sem `www`;
    - HTTPS funcionando;
    - fotos carregando.
14. **Search Console:**
    - verificar o domínio por DNS;
    - enviar `https://nouvellando.com.br/sitemap.xml`;
    - pedir a indexação da home.

### Fase 5: depois da troca

15. **Desligar o GitHub Pages** (Settings → Pages) e remover ou ajustar o `.github/workflows/publicar.yml`.
16. **Acompanhar o Search Console por 4 a 8 semanas:** erros 404, cobertura e posições.
17. **Manter o plano do WordPress.com ativo** (ou pelo menos o backup) até tudo estabilizar. Só depois cancelar a renovação.

## Como voltar atrás se der errado

No Registro.br, trocar os nameservers de volta para `ns1.wordpress.com`, `ns2.wordpress.com` e `ns3.wordpress.com`.
O WordPress.com volta a responder pelo domínio. Por isso o plano do WordPress.com não pode ser cancelado antes da hora.
