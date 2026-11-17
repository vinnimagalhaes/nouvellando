# Migração do nouvellando.com.br: levantamento

Levantamento feito em 15/11/2026 a partir do `sitemap.xml` do site atual (WordPress + Elementor + Jetpack).

## Arquivos

| Arquivo | O que tem |
|---|---|
| `inventario-seo-nouvellando.xlsx` | Planilha de migração: resumo, todas as páginas, redirecionamentos, links quebrados, preços e imagens |
| `conteudo/` | Uma página `.md` por URL, com título, descrição, estrutura de títulos, texto completo e lista de imagens, separada por tipo (`0-home`, `1-categorias`, `2-institucional`, `3-videoaulas`, `4-produtos/<linha>`, `5-sistema`) |
| `conteudo-completo.json` | O mesmo conteúdo em formato estruturado, para importar no site novo |

## O que o site tem hoje

- **843 páginas**: 841 no sitemap e 2 achadas só por links internos. Todas respondem normalmente (status 200).
  - 1 home
  - 14 categorias de fio
  - 2 institucionais (Sobre, Videoaulas)
  - 29 páginas de videoaula
  - 795 páginas de produto, uma por cor de fio
  - 2 páginas de sistema vazias (Loja, Minha conta)
- **Produtos por linha:**

  | Linha | Páginas |
  |---|---|
  | Original | 546 |
  | Twinkle | 58 |
  | Peluche | 48 |
  | Breezy | 43 |
  | Aura | 29 |
  | Fluffinho | 20 |
  | Bouclé | 19 |
  | Stardust | 19 |
  | Paillettes | 7 |
  | Original Coleção Jeans | 6 |

- **Endereços:** todos ficam na raiz do domínio (`/original-001/`, `/fio-twinkle/`, `/videoaula-xale-kira/`), sem pasta de categoria. O site novo precisa manter exatamente esse formato.
- **Página de produto:** foto, composição, TEX, cuidados e uma tabela de metragem, preço e peso por variação (3/4 cabos, com ou sem brilho). Não há carrinho; a compra é pelo WhatsApp.
- **SEO técnico:**
  - Não há plugin de SEO.
  - Os títulos são o padrão do WordPress (`Nome – Nouvellando®`), e o título da home é só “Nouvellando®”.
  - As descrições são geradas automaticamente pelo Jetpack com o começo do texto.
  - Os dados estruturados do Google se resumem a breadcrumb nas páginas internas e Organization/WebSite na home.
- **5.959 imagens:**
  - 999 não têm texto alternativo.
  - 2.216 vêm de outros sites. São ícones de lavagem copiados do Google Imagens e do Flaticon, que podem sumir a qualquer momento.

## Pontos de atenção

1. **Redirecionamentos que já existem:** o site já redireciona URLs antigas, como cores Paillettes fora de linha para `/fio-paillettes/`. Detectei 6 pelos links do próprio site, mas a lista completa está no WordPress (plugin de redirecionamento ou `.htaccess`). **Precisa ser exportada antes da troca**, senão esses endereços antigos passam a dar erro.
2. **Páginas duplicadas:**
   - `/fio-original/` e `/fio-original-2/` têm o mesmo título e quase o mesmo conteúdo.
   - O mesmo acontece com as cores 443, 712 e 340V.
   - A aba Redirecionamentos propõe consolidar cada grupo na versão mais linkada. Confira o conteúdo antes.
3. **Preços inconsistentes:** a mesma linha aparece com tabelas de preço diferentes em páginas diferentes. A Original tem 9 tabelas distintas, provavelmente páginas que não foram atualizadas num reajuste. A loja nova vai precisar de uma tabela única por linha, confirmada pela cliente (aba Preços).
4. **Títulos principais (H1):**
   - 7 categorias não têm H1: Breezy, Fluffinho, Paillettes, Peluche, Stardust, Twinkle e Sem degradê.
   - A home e Videoaulas têm dois H1 cada.
   - Corrigir isso no site novo ajuda o ranqueamento sem mexer no texto.
5. **Links quebrados:** 3 links internos levam a páginas que não existem mais (aba Links quebrados).
6. **Páginas sem link:** 9 produtos não recebem link de nenhuma outra página, e 2 páginas quase vazias existem fora do sitemap (`/original-340v/`, `/original-598/`).

## Plano de migração

1. **Antes de construir**
   - Pedir à cliente acesso ao Google Search Console, para ver quais páginas e buscas trazem visitas (“novelos degradê”, “novelos”).
   - Exportar a lista completa de redirecionamentos do WordPress.
   - Confirmar com ela a tabela de preços de cada linha.
2. **Construção**
   - Recriar as 843 URLs com o mesmo endereço, usando os textos de `conteudo/`.
   - Manter os títulos que funcionam, dar um H1 a cada página e escrever meta descriptions de verdade nas páginas principais (home, categorias, videoaulas).
   - Manter os arquivos de imagem nos mesmos caminhos (`/wp-content/uploads/...`) ou redirecioná-los.
   - Hospedar os ícones de lavagem no próprio site.
3. **Testes**
   - Publicar num endereço de teste bloqueado para o Google.
   - Conferir com um rastreador que todas as URLs da planilha respondem 200 ou redirecionam com 301.
4. **Troca**
   - Apontar o DNS do domínio para a hospedagem nova.
   - Ativar todos os redirecionamentos e enviar o sitemap novo no Search Console.
5. **Depois**
   - Acompanhar erros e posições no Search Console por 4 a 8 semanas.
   - Manter o WordPress antigo guardado (backup) até tudo estabilizar.
