# Nouvellando · Design System

Tokens e componentes visuais do site da Nouvellando, em CSS puro (sem build).
O próprio site (`../index.html`) é construído em cima deste design system.

**Documentação visual:** abra `design-system/index.html` no navegador (ou `/design-system/` no site publicado).

## Arquivos

| Arquivo | O que tem |
|---|---|
| `tokens.css` | Variáveis: cores, degradês dos fios, tipografia, espaçamento, raios, sombras, movimento, camadas |
| `base.css` | Reset, tipografia padrão, `.wrap` (container), utilitários de texto, animações |
| `components.css` | Botões, chips, campos, opções, abas, quantidade, preço, seletor de cor, card, item de carrinho, caixa, barra, breadcrumb, acordeão, modal, gaveta, toast |
| `index.html` | Guia visual com exemplos e código de cada componente |

## Como usar em uma página nova

```html
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="design-system/tokens.css">
<link rel="stylesheet" href="design-system/base.css">
<link rel="stylesheet" href="design-system/components.css">
<link rel="stylesheet" href="sua-pagina.css"> <!-- só layout -->
```

## Regras

- **Nunca use valor solto.** Em vez de `#5c4628` ou `18px`, use `var(--color-brand)` e `var(--radius-lg)`.
- **Mudar a marca = mudar `tokens.css`.** Todos os componentes e o site seguem.
- **Componente novo?** Adicione em `components.css` usando só tokens e documente em `index.html`.
- **Layout de seção** (hero, rodapé, grids de página) fica no CSS da página, não no design system.

## Tokens principais

| Token | Valor | Uso |
|---|---|---|
| `--color-brand` | `#5c4628` | CTA, preço, item ativo (marrom do logotipo) |
| `--color-accent` | `#e8a04c` | estrelas, destaques sobre escuro |
| `--color-bg` | `#fbf8f4` | fundo da página |
| `--color-ink` | `#2e251c` | texto (marrom quase preto) |
| `--color-muted` | `#75685b` | texto secundário (taupe quente) |
| `--font-display` | Fraunces | títulos, logo, nome de produto |
| `--font-body` | Inter | texto e interface |
| `--radius-lg` | `18px` | cards |
| `--radius-pill` | `999px` | botões, chips |
