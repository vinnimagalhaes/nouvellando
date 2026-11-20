# Dia da troca: sair do WordPress e colocar o site novo no ar

Roteiro completo para o dia em que o nouvellando.com.br passar a apontar para o site novo, no Cloudflare.
Ele junta todos os avisos levantados até agora. **Vá acrescentando aqui** qualquer cuidado novo que aparecer.

Última atualização: 20/11/2026.

---

## A. Antes do dia (dá para fazer com calma, nada muda no site atual)

- [ ] **Acessos em mãos:**
  - [ ] painel do WordPress.com (hoje ele hospeda o site **e** o DNS);
  - [ ] Registro.br, com o login do titular do domínio. É lá que se trocam os nameservers;
  - [ ] Cloudflare (conta Nouvellando@gmail.com), com você e o seu primo como membros;
  - [ ] Google Search Console do domínio;
  - [ ] GitHub (repositório `vinnimagalhaes/nouvellando`).
- [ ] **Backup do WordPress.com:** Ferramentas → Exportar → exportar todo o conteúdo **e** a biblioteca de mídia. Guardar fora do WordPress (Google Drive, HD…).
- [ ] **Redirecionamentos que só o WordPress conhece:** ver no painel se há plugin ou lista de redirecionamentos e, se houver, acrescentar em `conteudo/redirecionamentos.json`. Hoje o site novo conhece 6, mais os 3 links quebrados já tratados.
- [ ] **Conteúdo:**
  - [ ] aviso do topo (`conteudo/site.json`): hoje fala em "pedidos retomados em 01/12";
  - [ ] tabela de preços única por linha, confirmada pela cliente;
  - [ ] páginas duplicadas (Fio Original e Fio Original 2, cores 443, 712 e 340V);
  - [ ] descrições escritas à mão em `conteudo/seo.json`, revisadas.
- [ ] **Imagens que ainda dependem do WordPress** (somem quando ele sair do ar):
  - [ ] 2 fotos já quebradas hoje: `149.jpg` e `287l-n.jpg`. O `gerar.py` lista as duas no fim. Já existe `Original-149.jpg` para substituir a 149;
  - [ ] 17 imagens `s0.wp.com/_si/...` em páginas do Fio Aura (A025, A028, A030…);
  - [ ] 1 imagem do Google Imagens (`gstatic`) na Coleção Jeans 673.
  - Rodar `python ferramentas/gerar.py` e confirmar que **não aparece** o aviso "foto(s) ainda vêm do WordPress".
- [ ] **Cloudflare, domínio cadastrado sem trocar nada ainda:** Add a domain → `nouvellando.com.br` → plano Free. Conferir os registros que ele importar. **Não existe e-mail no domínio** (nenhum registro MX), então não há e-mail para perder. Anotar os **2 nameservers** que o Cloudflare informar.
- [ ] **Search Console:** se a verificação hoje é pela tag do WordPress, ela vai se perder. Criar a propriedade **Domínio** (`nouvellando.com.br`) com verificação por **registro TXT**, que vai ser colocado no Cloudflare no dia.
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
