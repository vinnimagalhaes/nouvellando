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
- [ ] **Teste geral no endereço de teste:**
  ```bash
  python ferramentas/testar-redirecionamentos.py https://nouvellando.pages.dev
  ```
  Tem que dar **0 erros**. Último resultado (20/11): 937 endereços, 0 erros, 0 sem 301.
- [ ] **Escolher o horário:** de pouco movimento, fora de promoção ou lançamento. Ter umas 2 a 3 horas livres.

---

## B. No dia, em ordem

### 1. Projeto atualizado
- [ ] `git status` e `git pull`, para pegar tudo o que o primo subiu.
- [ ] Gerar localmente com `python ferramentas/gerar.py --producao`. Conferir:
  - "836 páginas geradas" (ou o número atual);
  - nenhum aviso de foto vindo do WordPress;
  - `_redirects` dentro do limite de 2.000 regras.

### 2. Ligar o modo produção no Cloudflare
- [ ] Cloudflare → Workers & Pages → `nouvellando` → Settings → Build → Build configuration.
  Trocar o comando para `python3 ferramentas/gerar.py --producao`.
- [ ] Deployments → **Retry deployment** (ou fazer um push) e esperar terminar.
- [ ] Conferir em `https://nouvellando.pages.dev`:
  - [ ] `/robots.txt` mostra `Allow: /` e a linha `Sitemap:`;
  - [ ] `/sitemap.xml` abre e lista as páginas;
  - [ ] o código da home **não** tem `<meta name="robots" content="noindex`;
  - [ ] o pages.dev continua com o cabeçalho `X-Robots-Tag: noindex`. **É o esperado**: só o domínio oficial deve entrar no Google.
- [ ] Rodar de novo `python ferramentas/testar-redirecionamentos.py https://nouvellando.pages.dev`, que deve dar 0 erros.

### 3. Apontar o domínio para o Cloudflare
- [ ] Registro.br → domínio `nouvellando.com.br` → DNS → **alterar servidores DNS**.
  Trocar `ns1/ns2/ns3.wordpress.com` pelos 2 nameservers do Cloudflare.
- [ ] Cloudflare → o domínio → esperar o aviso **"Active"**. Leva de minutos a algumas horas.
- [ ] Cloudflare → Workers & Pages → `nouvellando` → **Custom domains**:
  - [ ] adicionar `nouvellando.com.br`;
  - [ ] adicionar `www.nouvellando.com.br`.
  - O HTTPS é emitido sozinho.
- [ ] **`www` → domínio sem `www` (301):** Cloudflare → o domínio → Rules → Redirect Rules → modelo "Redirect from WWW to root", com status 301 e mantendo o caminho.
- [ ] Cloudflare → o domínio → SSL/TLS → Edge Certificates → **Always Use HTTPS**: ligado.
- [ ] Colocar no DNS do Cloudflare o **registro TXT** do Search Console, preparado na etapa A.

### 4. Testar no domínio de verdade
- [ ] Abrir `https://nouvellando.com.br`: aparece o site novo, com o cadeado do HTTPS.
- [ ] `http://nouvellando.com.br` e `https://www.nouvellando.com.br` levam para `https://nouvellando.com.br`.
- [ ] Um produto antigo, por exemplo `https://nouvellando.com.br/original-805-805u/`, leva para `/fio-original/805-805u/`.
- [ ] Teste completo:
  ```bash
  python ferramentas/testar-redirecionamentos.py https://nouvellando.com.br
  ```
  Tem que dar **0 erros** e **0 sem 301**. Se aparecer erro, o script lista o endereço exato.
- [ ] Fotos carregando, carrinho e botão do WhatsApp funcionando, celular ok.
- [ ] `https://nouvellando.com.br/robots.txt` com `Allow: /` e sem `noindex` nas páginas.

### 5. Google
- [ ] Search Console → verificar a propriedade Domínio (pelo TXT).
- [ ] Sitemaps → enviar `https://nouvellando.com.br/sitemap.xml`. Remover o sitemap antigo do WordPress, se estiver lá.
- [ ] Inspeção de URL → pedir indexação da home, de 2 ou 3 linhas de fio e de alguns produtos.
- [ ] **Não** usar a ferramenta "Mudança de endereço": o domínio continua o mesmo.

### 6. Arrumar a casa
- [ ] GitHub → repositório → Settings → Pages → desativar.
- [ ] Remover ou ajustar `.github/workflows/publicar.yml`, para não publicar mais no GitHub Pages.
- [ ] **Não cancelar o WordPress.com ainda** (ver o item 8).

### 7. Se der errado: como voltar atrás
- No Registro.br, colocar de volta `ns1.wordpress.com`, `ns2.wordpress.com` e `ns3.wordpress.com`.
- O WordPress volta a responder pelo domínio, depois da propagação.
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
