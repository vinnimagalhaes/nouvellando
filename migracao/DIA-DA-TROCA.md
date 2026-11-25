# Dia da troca: sair do WordPress e colocar o site novo no ar

Roteiro completo para o dia em que o nouvellando.com.br passar a apontar para o site novo, no Cloudflare.
Ele junta todos os avisos levantados até agora. **Vá acrescentando aqui** qualquer cuidado novo que aparecer.

Última atualização: 24/11/2026.

---

## A. Antes do dia (dá para fazer com calma, nada muda no site atual)

- [ ] **Acessos em mãos:**
  - [ ] painel do WordPress.com (hoje ele hospeda o site **e** o DNS);
  - [ ] Registro.br, com o login do titular do domínio. É lá que se trocam os nameservers;
  - [ ] Cloudflare (conta Nouvellando@gmail.com), com você e o seu primo como membros;
  - [ ] Google Search Console do domínio;
  - [ ] GitHub (repositório `vinnimagalhaes/nouvellando`).
- [ ] **Backup do WordPress.com:** Ferramentas → Exportar → exportar todo o conteúdo **e** a biblioteca de mídia. Guardar fora do WordPress (Google Drive, HD…).
- [x] **Redirecionamentos que só o WordPress conhece:** feito em 24/11. A Amanda exportou os 33 do painel, e todos estão em `conteudo/redirecionamentos.json`:
  - Ruby → Nossos fios;
  - Novelos mesclados → Sem degradê;
  - xales prontos → Instagram do Recanto dos Xales;
  - Paillettes antigos → Fio Paillettes.
- [x] **Limite de 2.000 redirecionamentos do Cloudflare Pages:** resolvido em 24/11.
  - O teste mostrou que o Cloudflare **não** acha a regra quando falta a barra no fim (`/carrinho` dava 404, `/carrinho/` dava 301).
  - Agora só existe a regra com a barra. A página 404 acrescenta a barra sozinha e manda de novo, aí o 301 leva para a página nova.
  - Com isso, caiu de 1.995 para cerca de 1.160 regras. O `gerar.py` mostra a conta no fim.
  - Se um dia faltar espaço de novo: **Bulk Redirects** do Cloudflare (no domínio, plano Free).
- [ ] **Conteúdo:**
  - [x] aviso do topo (`conteudo/site.json`): "pedidos retomados em 01/12", confirmado pela Amanda em 24/11;
  - [ ] tabela de preços única por linha, confirmada pela cliente;
  - [x] páginas duplicadas: a Fio Original 2 redireciona para a Fio Original (24/11); as cores 443, 712 e 340V já redirecionam para a versão principal;
  - [ ] descrições escritas à mão em `conteudo/seo.json`, revisadas.
- [x] **Imagens que dependiam do WordPress:** resolvido em 20/11. As 6.411 imagens das páginas e as 836 imagens de compartilhamento vêm do próprio site:
  - os cards das cores 149 e 287 usam a foto do produto;
  - a imagem de compartilhamento vazia do WordPress foi trocada pela foto da página;
  - os ícones do Google na Coleção Jeans 673 foram removidos.
  - [ ] No dia, rodar `python ferramentas/gerar.py` e confirmar que **não aparece** o aviso "foto(s) ainda vêm do WordPress". Se aparecer, é uma foto nova adicionada depois.
- [x] **Cloudflare, domínio cadastrado sem trocar nada ainda:** feito em 24/11, no plano Free.
  - Registros importados: 2 A do WordPress (192.0.78.151 e .233), `www` e `*` (CNAME), SPF e DMARC (TXT). **Não existe e-mail no domínio** (nenhum MX).
  - Os registros do site ficaram em **DNS only** (nuvem cinza). Assim, até ligar o site novo, o WordPress responde direto, com o certificado dele, e não há erro de HTTPS na transição.
  - "Bot Preference Sync" desligado, para o Cloudflare não mexer no `robots.txt`.
  - DNSSEC: desligado no Registro.br (não há registro DS), então não há nada a fazer.
  - **Nameservers do Cloudflare: `carioca.ns.cloudflare.com` e `ganz.ns.cloudflare.com`.**
- [x] **Search Console:** conferido em 24/11.
  - A propriedade `https://nouvellando.com.br/` era verificada pelo **Google Tag Manager** (GTM-MFH2VBXM, instalado no WordPress).
  - Para não perder a verificação, o registro TXT dela (`google-site-verification=Ns4Z9u…`) já foi colocado no DNS do Cloudflare.
  - Depois que o domínio ficar "Active": Search Console → Configurações → Verificação de propriedade → **Provedor de nome de domínio → Verificar**. Assim fica a mesma propriedade, com o histórico.
- [x] **Google Tag Manager (GTM-MFH2VBXM):** decidido em 24/11 manter. O site novo carrega o mesmo código do WordPress, **só no domínio oficial**: os endereços de teste não entram nas estatísticas. No passo 4, conferir que ele carrega em `https://nouvellando.com.br`.
- [x] **Teste geral no endereço de teste:**
  ```bash
  python ferramentas/testar-redirecionamentos.py https://nouvellando.pages.dev
  ```
  Tem que dar **0 erros**. Último resultado (20/11): 937 endereços, 0 erros, 0 sem 301.
- [ ] **Escolher o horário:** de pouco movimento, fora de promoção ou lançamento. Ter umas 2 a 3 horas livres.

---

## B. No dia, em ordem

### 1. Projeto atualizado
- [x] `git status` e `git pull`, para pegar tudo o que o primo subiu.
- [x] Gerar localmente com `python ferramentas/gerar.py --producao`. Conferir:
  - "836 páginas geradas" (ou o número atual);
  - nenhum aviso de foto vindo do WordPress;
  - `_redirects` dentro do limite de 2.000 regras.

### 2. Ligar o modo produção no Cloudflare
- [x] Cloudflare → Workers & Pages → `nouvellando` → Settings → Build → Build configuration.
  Trocar o comando para `python3 ferramentas/gerar.py --producao`.
- [x] Deployments → **Retry deployment** (ou fazer um push) e esperar terminar.
- [x] Conferir em `https://nouvellando.pages.dev`:
  - [x] `/robots.txt` mostra `Allow: /` e a linha `Sitemap:`;
  - [x] `/sitemap.xml` abre e lista as páginas;
  - [x] o código da home **não** tem `<meta name="robots" content="noindex`;
  - [x] o pages.dev continua com o cabeçalho `X-Robots-Tag: noindex`. **É o esperado**: só o domínio oficial deve entrar no Google.
- [x] Rodar de novo `python ferramentas/testar-redirecionamentos.py https://nouvellando.pages.dev`, que deve dar 0 erros. Feito em 24/11: 879 endereços, 0 erros, 0 com mais de um salto.

### 3. Apontar o domínio para o Cloudflare
- [x] Registro.br → domínio `nouvellando.com.br` → DNS → **alterar servidores DNS**.
  Trocar `ns1/ns2/ns3.wordpress.com` pelos 2 nameservers do Cloudflare. (Amanda, 24/11; o .br publicou às 20:51.)
- [x] Cloudflare → o domínio → esperar o aviso **"Active"**. (Ativo minutos depois.)
- [x] Cloudflare → Workers & Pages → `nouvellando` → **Custom domains**:
  - [x] adicionar `nouvellando.com.br`. O Cloudflare trocou os 2 registros A do WordPress por um CNAME para `nouvellando.pages.dev`;
  - `www.nouvellando.com.br` **não** foi ligado ao projeto, de propósito. O registro `www` ficou "Proxied" e a regra abaixo leva tudo para o endereço sem www. A Amanda decidiu manter sem www, como o Google já conhece.
  - O HTTPS foi emitido sozinho.
- [x] **`www` → domínio sem `www` (301):** regra "Redirect from WWW to root" ativa (`https://www.*` → `https://${1}`, 301, mantendo o `?…`).
- [x] Cloudflare → o domínio → SSL/TLS → Edge Certificates → **Always Use HTTPS**: ligado.
- [x] Colocar no DNS do Cloudflare o **registro TXT** do Search Console, preparado na etapa A. (Feito em 24/11.)

### 4. Testar no domínio de verdade
- [x] Abrir `https://nouvellando.com.br`: aparece o site novo, com o cadeado do HTTPS.
- [x] `http://nouvellando.com.br` e `https://www.nouvellando.com.br` levam para `https://nouvellando.com.br`.
- [x] Um produto antigo, por exemplo `https://nouvellando.com.br/original-805-805u/`, leva para `/fio-original/805-805u/`.
- [x] Teste completo (24/11: 879 endereços, 0 erros, 0 sem 301, 0 com mais de um salto):
  ```bash
  python ferramentas/testar-redirecionamentos.py https://nouvellando.com.br
  ```
  Tem que dar **0 erros** e **0 sem 301**. Se aparecer erro, o script lista o endereço exato.
- [ ] Fotos carregando, carrinho e botão do WhatsApp funcionando, celular ok. (Em 24/11: fotos, ficha técnica e Tag Manager conferidos no domínio, sem erros. Falta a Amanda testar um pedido pelo celular.)
- [x] `https://nouvellando.com.br/robots.txt` com `Allow: /` e sem `noindex` nas páginas.

### 5. Google
- [x] Search Console → verificar pelo TXT. Feito na **mesma propriedade** `https://nouvellando.com.br/`, pelo método "Provedor de nome de domínio" (24/11). Assim o histórico continua.
- [x] Sitemaps → enviado `https://nouvellando.com.br/sitemap.xml` (24/11). Não havia sitemap antigo do WordPress cadastrado.
- [ ] Inspeção de URL → pedir indexação da home, de 2 ou 3 linhas de fio e de alguns produtos.
- [ ] **Não** usar a ferramenta "Mudança de endereço": o domínio continua o mesmo.

### 6. Arrumar a casa
- [ ] GitHub → repositório → Settings → Pages → desativar.
- [ ] Remover ou ajustar `.github/workflows/publicar.yml`, para não publicar mais no GitHub Pages.
- [ ] **Não cancelar o WordPress.com ainda** (ver o item 8).

### 7. Se der errado: como voltar atrás
- **Jeito rápido (minutos), pelo Cloudflare:**
  1. Cloudflare → o domínio → DNS → Records: apagar o CNAME `nouvellando.com.br → nouvellando.pages.dev`.
  2. Criar de novo os 2 registros A, em **DNS only**: `nouvellando.com.br → 192.0.78.151` e `nouvellando.com.br → 192.0.78.233`.
  3. O WordPress volta a responder.
- **Jeito completo (horas):** no Registro.br, colocar de volta `ns1.wordpress.com`, `ns2.wordpress.com` e `ns3.wordpress.com`.
- Por isso o plano do WordPress.com só pode ser cancelado depois que tudo estabilizar.

### 8. Depois da troca (4 a 8 semanas)
- [ ] Search Console toda semana:
  - erros 404 e "Páginas" não indexadas;
  - posições das buscas principais ("novelos degradê", "novelos").
- [ ] Endereço antigo dando 404 no Search Console: acrescentar em `conteudo/redirecionamentos.json`, fazer push e testar de novo.
- [ ] Quando estiver tudo estável: cancelar a renovação do WordPress.com, mantendo o backup da etapa A.

---

## O que já está pronto (não precisa fazer no dia)

- Fotos hospedadas no próprio site (`wp-content/uploads/`), otimizadas sem perder qualidade.
- 1.939 redirecionamentos 301 no Cloudflare (`site/_redirects`, gerado pelo `gerar.py`). Cobrem:
  - produtos e páginas antigas, com e sem a barra no fim;
  - fotos redimensionadas;
  - endereços do WordPress (`/feed/`, `/wp-admin/`, `/loja/`, `/minha-conta/`…).
- `noindex` permanente nos endereços `*.pages.dev` (`site/_headers`).
- SEO: um H1 por página, descrições novas, título da home.
- Script de teste dos endereços antigos: `ferramentas/testar-redirecionamentos.py`.

Limite conhecido: fotos em tamanhos do WordPress que o site não usa ainda dão 404. Isso só afeta o Google Imagens.
