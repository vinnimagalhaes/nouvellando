// Nouvellando · comportamento das páginas (menu e carrosséis)
(function () {
  // Menu no celular
  var btn = document.querySelector('.menu-btn');
  var nav = document.getElementById('nav');
  if (btn && nav) {
    btn.addEventListener('click', function () {
      var aberto = nav.classList.toggle('open');
      btn.setAttribute('aria-expanded', aberto);
    });
  }
  document.querySelectorAll('.nav__abre').forEach(function (b) {
    b.addEventListener('click', function () {
      var li = b.parentElement;
      var aberto = li.classList.toggle('aberto');
      b.setAttribute('aria-expanded', aberto);
    });
  });

  // Abas (página Sem degradê)
  document.querySelectorAll('.abas').forEach(function (a) {
    var botoes = a.querySelectorAll('[role=tab]');
    var paineis = a.querySelectorAll('[role=tabpanel]');
    botoes.forEach(function (b, i) {
      b.addEventListener('click', function () {
        botoes.forEach(function (x, k) { x.classList.toggle('on', k === i); x.setAttribute('aria-selected', k === i); });
        paineis.forEach(function (p, k) { p.hidden = k !== i; });
        window.dispatchEvent(new Event('resize'));
      });
    });
  });

  // Carrosséis
  var reduzido = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  document.querySelectorAll('.carrossel').forEach(function (c) {
    var trilho = c.querySelector('.carrossel__trilho');
    var slides = trilho.children;
    if (slides.length < 2) return;
    var pontos = c.querySelector('.carrossel__pontos');

    function porTela() {
      var w = slides[0].getBoundingClientRect().width;
      return Math.max(1, Math.round(trilho.clientWidth / (w || 1)));
    }
    function paginas() { return Math.max(1, slides.length - porTela() + 1); }
    function atual() {
      var w = slides[0].getBoundingClientRect().width + parseFloat(getComputedStyle(trilho).columnGap || 0);
      return Math.round(trilho.scrollLeft / (w || 1));
    }
    function vai(i) {
      var n = paginas();
      i = (i + n) % n;
      trilho.scrollTo({ left: slides[i].offsetLeft - trilho.offsetLeft });
    }
    function desenhaPontos() {
      if (!pontos) return;
      var n = paginas();
      pontos.innerHTML = '';
      if (n < 2) return;
      for (var i = 0; i < n; i++) {
        var p = document.createElement('button');
        p.setAttribute('aria-label', 'Ir para ' + (i + 1));
        (function (k) { p.addEventListener('click', function () { vai(k); }); })(i);
        pontos.appendChild(p);
      }
      marca();
    }
    function marca() {
      if (!pontos) return;
      var a = atual();
      Array.prototype.forEach.call(pontos.children, function (p, i) {
        if (i === a) p.setAttribute('aria-current', 'true'); else p.removeAttribute('aria-current');
      });
    }
    var ant = c.querySelector('.carrossel__seta--ant');
    var prox = c.querySelector('.carrossel__seta--prox');
    if (ant) ant.addEventListener('click', function (e) { e.preventDefault(); vai(atual() - 1); });
    if (prox) prox.addEventListener('click', function (e) { e.preventDefault(); vai(atual() + 1); });
    var t;
    trilho.addEventListener('scroll', function () { clearTimeout(t); t = setTimeout(marca, 60); }, { passive: true });
    window.addEventListener('resize', desenhaPontos);
    desenhaPontos();

    var tempo = parseInt(c.getAttribute('data-autoplay'), 10);
    if (tempo && !reduzido && 'IntersectionObserver' in window) {
      var timer = null, visivel = false, pausa = false;
      function liga() { desliga(); if (visivel && !pausa) timer = setInterval(function () { vai(atual() + 1); }, tempo); }
      function desliga() { if (timer) clearInterval(timer); timer = null; }
      new IntersectionObserver(function (es) { visivel = es[0].isIntersecting; liga(); }).observe(c);
      c.addEventListener('mouseenter', function () { pausa = true; desliga(); });
      c.addEventListener('mouseleave', function () { pausa = false; liga(); });
      c.addEventListener('touchstart', function () { pausa = true; desliga(); }, { passive: true });
    }
  });
})();

// =========================================================
// Loja: produto, carrinho (guardado no navegador) e busca
// =========================================================
(function () {
  var script = document.querySelector('script[data-raiz]');
  var RAIZ = new URL(script.getAttribute('data-raiz'), location.href).href;
  var WA = 'https://api.whatsapp.com/send?phone=5516988081463';
  var $ = function (s, el) { return (el || document).querySelector(s); };
  var $$ = function (s, el) { return Array.prototype.slice.call((el || document).querySelectorAll(s)); };
  var brl = function (n) { return n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }); };
  var url = function (caminho) { return RAIZ + caminho.replace(/^\//, ''); };
  // Foto do próprio site (/wp-content/...) vira endereço relativo; foto externa fica como está
  var foto = function (s) { return s && s.charAt(0) === '/' && s.charAt(1) !== '/' ? url(s) : (s || ''); };

  function toast(msg) {
    var t = $('[data-toast]'); if (!t) return;
    t.textContent = msg; t.classList.add('show');
    clearTimeout(toast.t); toast.t = setTimeout(function () { t.classList.remove('show'); }, 2400);
  }

  // ---------- carrinho ----------
  var carrinho = [];
  try { carrinho = JSON.parse(localStorage.getItem('nv-carrinho')) || []; } catch (e) {}
  function salva() { try { localStorage.setItem('nv-carrinho', JSON.stringify(carrinho)); } catch (e) {} }
  function descricao(i) { return [i.cor, i.cabos, i.brilho, i.m + ' m'].filter(Boolean).join(' · '); }
  function mensagem(itens) {
    var linhas = itens.map(function (i) {
      return '• ' + i.q + 'x ' + i.nome + ' — ' + descricao(i) + ' — ' + brl(i.preco * i.q);
    });
    var total = itens.reduce(function (s, i) { return s + i.preco * i.q; }, 0);
    return 'Olá! Gostaria de fazer este pedido:\n\n' + linhas.join('\n') + '\n\nTotal: ' + brl(total);
  }
  function desenhaCarrinho() {
    var n = carrinho.reduce(function (s, i) { return s + i.q; }, 0);
    var total = carrinho.reduce(function (s, i) { return s + i.preco * i.q; }, 0);
    $$('[data-contador]').forEach(function (b) { b.textContent = n; b.hidden = !n; });
    var lista = $('[data-carrinho-itens]'); if (!lista) return;
    $('[data-carrinho-total]').textContent = brl(total);
    $('[data-finalizar]').href = WA + '&text=' + encodeURIComponent(mensagem(carrinho));
    $('[data-finalizar]').classList.toggle('is-disabled', !carrinho.length);
    lista.innerHTML = carrinho.length ? carrinho.map(function (i, k) {
      return '<div class="item"><a class="item__img" href="' + url(i.url) + '"><img src="' + foto(i.img) + '" alt=""></a>' +
        '<div><b><a href="' + url(i.url) + '">' + i.nome + '</a></b><small>' + descricao(i) + '</small>' +
        '<div class="qty qty--sm"><button data-menos="' + k + '" aria-label="Diminuir">−</button><span>' + i.q + '</span><button data-mais="' + k + '" aria-label="Aumentar">+</button></div></div>' +
        '<div class="item__p">' + brl(i.preco * i.q) + '<button class="item__rm" data-remove="' + k + '">remover</button></div></div>';
    }).join('') : '<p class="drawer__empty">Seu carrinho está vazio.<br>Que tal escolher algumas cores?</p>';
  }
  function abreCarrinho() { $('[data-carrinho]').hidden = false; document.body.style.overflow = 'hidden'; }
  function fechaCarrinho() { $('[data-carrinho]').hidden = true; document.body.style.overflow = ''; }

  document.addEventListener('click', function (e) {
    var el;
    if (e.target.closest('[data-abre-carrinho]')) return abreCarrinho();
    if (e.target.closest('[data-fecha-carrinho]')) return fechaCarrinho();
    if ((el = e.target.closest('[data-mais]'))) { carrinho[+el.dataset.mais].q++; salva(); return desenhaCarrinho(); }
    if ((el = e.target.closest('[data-menos]'))) { var it = carrinho[+el.dataset.menos]; if (it.q > 1) it.q--; salva(); return desenhaCarrinho(); }
    if ((el = e.target.closest('[data-remove]'))) { carrinho.splice(+el.dataset.remove, 1); salva(); return desenhaCarrinho(); }
    if ((el = e.target.closest('[data-finalizar]')) && !carrinho.length) { e.preventDefault(); toast('Seu carrinho está vazio'); }
  });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && $('[data-carrinho]') && !$('[data-carrinho]').hidden) fechaCarrinho(); });
  window.addEventListener('storage', function (e) {
    if (e.key === 'nv-carrinho') { try { carrinho = JSON.parse(e.newValue) || []; } catch (x) { carrinho = []; } desenhaCarrinho(); }
  });
  desenhaCarrinho();

  // ---------- página de produto ----------
  var pdp = $('[data-produto]');
  var dadosEl = $('#produto-dados');
  if (pdp && dadosEl) {
    var P = JSON.parse(dadosEl.textContent);
    var sel = { cor: 0, cabos: null, brilho: null, m: null, q: 1 };
    var v0 = P.variacoes[0];
    if (v0) { sel.cabos = v0.cabos; sel.brilho = v0.brilho; sel.m = v0.faixas[0].m; }
    var selectM = $('.metragem', pdp);

    function variacao() {
      return P.variacoes.filter(function (v) { return v.cabos === sel.cabos && (!sel.brilho || v.brilho === sel.brilho); })[0] ||
             P.variacoes.filter(function (v) { return v.cabos === sel.cabos; })[0] || P.variacoes[0];
    }
    function faixa(v) {
      return v.faixas.filter(function (f) { return f.m === sel.m; })[0] || v.faixas[0];
    }
    function pinta() {
      var v = variacao(); if (!v) return;
      // Metragens disponíveis nesta variação
      if (selectM) {
        var atual = sel.m;
        selectM.innerHTML = v.faixas.map(function (f) { return '<option value="' + f.m + '">' + f.m + ' m</option>'; }).join('');
        var f = v.faixas.filter(function (x) { return x.m === atual; })[0] || v.faixas[0];
        sel.m = f.m; selectM.value = f.m; selectM.disabled = v.faixas.length < 2;
      }
      var fx = faixa(v);
      var preco = $('[data-preco]', pdp);
      preco.firstChild.nodeValue = brl(fx.preco);
      $('[data-peso]', pdp).textContent = (fx.g ? '≅ ' + fx.g + ' g · ' : '') + fx.m + ' m' + (sel.q > 1 ? ' · ' + sel.q + ' novelos: ' + brl(fx.preco * sel.q) : '');
      $$('[data-cabos]', pdp).forEach(function (b) { var on = b.dataset.cabos === sel.cabos; b.classList.toggle('on', on); b.setAttribute('aria-pressed', on); });
      $$('[data-brilho]', pdp).forEach(function (b) {
        var on = b.dataset.brilho === sel.brilho; b.classList.toggle('on', on); b.setAttribute('aria-pressed', on);
        b.disabled = !P.variacoes.some(function (x) { return x.cabos === sel.cabos && x.brilho === b.dataset.brilho; });
      });
      $$('.swatch', pdp).forEach(function (b) { var on = +b.dataset.cor === sel.cor; b.classList.toggle('on', on); b.setAttribute('aria-pressed', on); });
      $$('.galeria__foto', pdp).forEach(function (f) { f.hidden = +f.dataset.cor !== sel.cor; });
      var r;
      if ((r = $('[data-rotulo="cor"]', pdp))) r.textContent = P.cores[sel.cor].nome;
      if ((r = $('[data-rotulo="cabos"]', pdp))) r.textContent = sel.cabos;
      if ((r = $('[data-rotulo="brilho"]', pdp))) r.textContent = sel.brilho;
      $('[data-qtd-valor]', pdp).textContent = sel.q;
      var wa = $('[data-comprar-wa]', pdp);
      if (wa) wa.href = WA + '&text=' + encodeURIComponent(mensagem([item()]));
    }
    function item() {
      var v = variacao(), fx = faixa(v), c = P.cores[sel.cor] || { nome: P.nome, img: '' };
      return { url: P.url, nome: P.nome, cor: P.cores.length > 1 ? c.nome : '', img: c.img,
               cabos: v.cabos, brilho: v.brilho, m: fx.m, g: fx.g, preco: fx.preco, q: sel.q };
    }
    pdp.addEventListener('click', function (e) {
      var b;
      if ((b = e.target.closest('.swatch'))) { sel.cor = +b.dataset.cor; return pinta(); }
      if ((b = e.target.closest('[data-cabos]'))) {
        sel.cabos = b.dataset.cabos;
        if (!P.variacoes.some(function (x) { return x.cabos === sel.cabos && x.brilho === sel.brilho; })) sel.brilho = variacao().brilho;
        return pinta();
      }
      if ((b = e.target.closest('[data-brilho]'))) { sel.brilho = b.dataset.brilho; return pinta(); }
      if ((b = e.target.closest('[data-qtd]'))) { sel.q = Math.max(1, sel.q + +b.dataset.qtd); return pinta(); }
      if (e.target.closest('[data-adicionar]')) {
        var novo = item();
        var chave = function (i) { return [i.url, i.cor, i.cabos, i.brilho, i.m].join('|'); };
        var igual = carrinho.filter(function (i) { return chave(i) === chave(novo); })[0];
        if (igual) igual.q += novo.q; else carrinho.push(novo);
        salva(); desenhaCarrinho(); abreCarrinho();
        sel.q = 1; pinta();
      }
    });
    if (selectM) selectM.addEventListener('change', function () { sel.m = +selectM.value; pinta(); });
    pinta();
  }

  // ---------- busca ----------
  var botaoBusca = $('[data-abre-busca]');
  var barra = $('[data-busca]');
  if (botaoBusca && barra) {
    var campo = $('[data-busca-campo]'), saida = $('[data-busca-resultados]'), indice = null;
    var normal = function (s) { return s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, ''); };
    botaoBusca.addEventListener('click', function () {
      barra.hidden = !barra.hidden;
      botaoBusca.setAttribute('aria-expanded', !barra.hidden);
      if (!barra.hidden) {
        campo.focus();
        if (!indice) fetch(RAIZ + 'assets/busca.json').then(function (r) { return r.json(); })
          .then(function (j) { indice = j; busca(); }).catch(function () { indice = []; });
      }
    });
    function busca() {
      var q = normal(campo.value.trim());
      if (!q || !indice) { saida.innerHTML = ''; return; }
      var termos = q.split(/\s+/);
      var achados = indice.filter(function (i) {
        var alvo = normal(i.n + ' ' + i.l);
        return termos.every(function (t) { return alvo.indexOf(t) >= 0; });
      }).slice(0, 12);
      saida.innerHTML = achados.length ? achados.map(function (i) {
        return '<a class="busca__item" href="' + url(i.u) + '">' + (i.i ? '<img src="' + foto(i.i) + '" alt="" loading="lazy">' : '<span class="busca__sem"></span>') +
          '<span><b>' + i.n + '</b><small>' + i.l + '</small></span>' + (i.p ? '<em>a partir de ' + i.p + '</em>' : '') + '</a>';
      }).join('') : '<p class="busca__vazio">Nenhum fio encontrado para “' + campo.value + '”.</p>';
    }
    campo.addEventListener('input', busca);
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !barra.hidden) { barra.hidden = true; botaoBusca.focus(); } });
  }
})();

// Videoaulas: destaque que alterna e fileiras com setas
(function () {
  var hero = document.querySelector('[data-hero]');
  if (hero) {
    var slides = hero.querySelectorAll('[data-destaque]');
    var pontos = hero.querySelectorAll('[data-ir]');
    var atual = 0, timer = null;
    var reduzido = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    function mostra(i) {
      atual = (i + slides.length) % slides.length;
      slides.forEach(function (s, k) { s.classList.toggle('on', k === atual); s.setAttribute('aria-hidden', k !== atual); });
      pontos.forEach(function (p, k) { p.classList.toggle('on', k === atual); });
    }
    function liga() { if (reduzido || slides.length < 2) return; clearInterval(timer); timer = setInterval(function () { mostra(atual + 1); }, 7000); }
    pontos.forEach(function (p) { p.addEventListener('click', function () { mostra(+p.dataset.ir); liga(); }); });
    hero.addEventListener('mouseenter', function () { clearInterval(timer); });
    hero.addEventListener('mouseleave', liga);
    liga();
  }
  document.querySelectorAll('.nf-fileira__corpo').forEach(function (f) {
    var trilho = f.querySelector('.nf-trilho');
    var ant = f.querySelector('.nf-seta--ant'), prox = f.querySelector('.nf-seta--prox');
    function marca() {
      ant.disabled = trilho.scrollLeft < 10;
      prox.disabled = trilho.scrollLeft + trilho.clientWidth >= trilho.scrollWidth - 10;
    }
    ant.addEventListener('click', function () { trilho.scrollBy({ left: -trilho.clientWidth * 0.85 }); });
    prox.addEventListener('click', function () { trilho.scrollBy({ left: trilho.clientWidth * 0.85 }); });
    trilho.addEventListener('scroll', marca, { passive: true });
    window.addEventListener('resize', marca);
    marca();
  });

  // Abas "Com degradê / Sem degradê" no topo de cada fio + "Ver mais cores" (que conta
  // separado em cada aba). Link direto para a aba: /fio-original/#sem-degrade
  var POR_VEZ = 48;
  var abasDegrade = document.querySelector('[data-abas-degrade]');
  function abaAtual() { return abasDegrade ? (abasDegrade.querySelector('[aria-selected="true"]') || {}).getAttribute('data-aba-tipo') : ''; }
  function escondidas(grade) {
    var tipo = grade.getAttribute('data-aba');
    return Array.prototype.slice.call(grade.querySelectorAll('.col.mais' + (tipo ? '[data-tipo="' + tipo + '"]' : '')));
  }
  function atualizaVerMais() {
    document.querySelectorAll('[data-ver-mais]').forEach(function (btn) {
      var caixa = btn.closest('.ver-mais'), grade = caixa.previousElementSibling, n = escondidas(grade).length;
      // Com filtro de cor ligado aparecem todas as cores que combinam, sem "Ver mais"
      caixa.hidden = n === 0 || grade.classList.contains('filtrando');
      btn.querySelector('[data-restam]').textContent = '(' + n + ')';
    });
  }
  // Ao trocar de fio (Original -> Fluffinho…), a aba Com/Sem degradê e as cores marcadas
  // continuam: só muda a lista de novelos. Guardado só nesta aba do navegador (sessionStorage).
  function lembra(chave, valor) { try { sessionStorage.setItem('nf-filtro-' + chave, valor); } catch (e) {} }
  function lembrado(chave) { try { return sessionStorage.getItem('nf-filtro-' + chave); } catch (e) { return null; } }
  function escolheAba(tipo, foco) {
    abasDegrade.querySelectorAll('[data-aba-tipo]').forEach(function (b) {
      var on = b.getAttribute('data-aba-tipo') === tipo;
      b.setAttribute('aria-selected', on);
      b.tabIndex = on ? 0 : -1;
      if (on && foco) b.focus();
    });
    document.querySelectorAll('[data-pill-tipo]').forEach(function (p) { p.hidden = p.getAttribute('data-pill-tipo') !== tipo; });
    document.querySelectorAll('.linha--cards[data-aba]').forEach(function (g) { g.setAttribute('data-aba', tipo); });
    aplicaCores();
    if (history.replaceState) history.replaceState(null, '', tipo === 'sem' ? '#sem-degrade' : location.pathname + location.search);
  }
  if (abasDegrade) {
    abasDegrade.addEventListener('click', function (e) {
      var b = e.target.closest('[data-aba-tipo]');
      if (b) { escolheAba(b.getAttribute('data-aba-tipo')); lembra('aba', b.getAttribute('data-aba-tipo')); }
    });
    abasDegrade.addEventListener('keydown', function (e) {
      var outra = abaAtual() === 'com' ? 'sem' : 'com';
      var bOutra = abasDegrade.querySelector('[data-aba-tipo="' + outra + '"]');
      if ((e.key === 'ArrowRight' || e.key === 'ArrowLeft') && bOutra && !bOutra.disabled) { escolheAba(outra, true); lembra('aba', outra); }
    });
    var bSem = abasDegrade.querySelector('[data-aba-tipo="sem"]');
    var abaSalva = location.hash === '#sem-degrade' ? 'sem' : lembrado('aba');
    var bSalva = abaSalva && abasDegrade.querySelector('[data-aba-tipo="' + abaSalva + '"]');
    if (bSalva && !bSalva.disabled && abaSalva !== abaAtual()) escolheAba(abaSalva);
  }

  // Filtro por cor no topo de cada fio (cores de conteudo/cores.json, em data-cores de cada card).
  // Várias cores marcadas = mostra os novelos que têm QUALQUER uma delas. Funciona junto com as
  // abas Com/Sem degradê: só aparecem os botões das cores que existem na aba atual.
  function aplicaCores() {
    var filtro = document.querySelector('[data-filtro-cores]');
    var grades = document.querySelectorAll('.linha--cards');
    var tipo = abaAtual();
    var sel = filtro ? Array.prototype.map.call(filtro.querySelectorAll('[data-cor][aria-pressed="true"]'),
      function (b) { return b.getAttribute('data-cor'); }) : [];
    var existem = {}, achados = 0;
    grades.forEach(function (g) {
      g.classList.toggle('filtrando', sel.length > 0);
      Array.prototype.forEach.call(g.children, function (c) {
        if (!c.classList.contains('col')) return;
        var cores = (c.getAttribute('data-cores') || '').split(' ');
        var naAba = !tipo || !g.hasAttribute('data-aba') || c.getAttribute('data-tipo') === tipo;
        if (naAba) cores.forEach(function (x) { if (x) existem[x] = true; });
        var ok = !sel.length || sel.some(function (x) { return cores.indexOf(x) >= 0; });
        c.classList.toggle('fora-cor', !ok);
        if (ok && naAba && sel.length) achados++;
      });
    });
    if (filtro) {
      // Cor que não existe na aba atual: botão some (e deixa de estar marcado)
      var apagou = false;
      filtro.querySelectorAll('[data-cor]').forEach(function (b) {
        var tem = !!existem[b.getAttribute('data-cor')];
        b.hidden = !tem;
        if (!tem && b.getAttribute('aria-pressed') === 'true') { b.setAttribute('aria-pressed', 'false'); apagou = true; }
      });
      if (apagou) return aplicaCores();
      filtro.querySelector('[data-limpar-cores]').hidden = !sel.length;
      var conta = filtro.querySelector('[data-conta-cores]');
      conta.hidden = !sel.length;
      conta.textContent = sel.length;
      filtro.querySelector('[data-status-cores]').textContent = !sel.length ? '' :
        achados === 0 ? 'Nenhum novelo com essa cor aqui.' :
        achados + (achados === 1 ? ' novelo com ' : ' novelos com ') + (sel.length === 1 ? 'essa cor' : 'essas cores');
    }
    atualizaVerMais();
  }
  var filtroCores = document.querySelector('[data-filtro-cores]');
  if (filtroCores) {
    var abrirCores = filtroCores.querySelector('[data-abrir-cores]');
    var painelCores = filtroCores.querySelector('[data-painel-cores]');
    function mostraCores(abrir, devolveFoco) {
      painelCores.hidden = !abrir;
      abrirCores.setAttribute('aria-expanded', abrir);
      if (abrir) { var b = painelCores.querySelector('[data-cor]:not([hidden])'); if (b) b.focus(); }
      else if (devolveFoco) abrirCores.focus();
    }
    filtroCores.addEventListener('click', function (e) {
      if (e.target.closest('[data-abrir-cores]')) return mostraCores(painelCores.hidden);
      if (e.target.closest('[data-fechar-cores]')) return mostraCores(false, true);
      var b = e.target.closest('[data-cor]');
      if (b) b.setAttribute('aria-pressed', b.getAttribute('aria-pressed') === 'true' ? 'false' : 'true');
      else if (e.target.closest('[data-limpar-cores]'))
        filtroCores.querySelectorAll('[data-cor]').forEach(function (x) { x.setAttribute('aria-pressed', 'false'); });
      else return;
      lembra('cores', Array.prototype.map.call(filtroCores.querySelectorAll('[data-cor][aria-pressed="true"]'),
        function (x) { return x.getAttribute('data-cor'); }).join(' '));
      aplicaCores();
    });
    // Fecha o menu ao clicar fora ou apertar Esc
    document.addEventListener('click', function (e) { if (!painelCores.hidden && !filtroCores.contains(e.target)) mostraCores(false); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !painelCores.hidden) mostraCores(false, true); });
    (lembrado('cores') || '').split(' ').forEach(function (c) {
      var x = c && filtroCores.querySelector('[data-cor="' + c + '"]');
      if (x) x.setAttribute('aria-pressed', 'true');
    });
    aplicaCores();
  }

  // Catálogos grandes: "Ver mais cores" mostra o próximo bloco de cores da aba atual
  // (as fotos escondidas só são baixadas quando aparecem).
  document.querySelectorAll('[data-ver-mais]').forEach(function (btn) {
    var grade = btn.closest('.ver-mais').previousElementSibling;
    btn.addEventListener('click', function () {
      var mostrar = escondidas(grade).slice(0, POR_VEZ);
      mostrar.forEach(function (c) { c.classList.remove('mais'); });
      atualizaVerMais();
      // Leva o foco para a primeira cor nova (teclado e leitor de tela)
      var link = mostrar[0] && mostrar[0].querySelector('a');
      if (link) link.focus({ preventScroll: true });
    });
  });
})();
