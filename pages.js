/* Nouvellando · páginas internas (rotas por hash): produto, categoria, checkout, pedido */
const page = $('#page');
let lastOrder = null;
const FREE_SHIP = 299;

const crumbs = list => `<nav class="crumbs">${list.map(([t, h]) => h ? `<a href="${h}">${t}</a>` : `<span>${t}</span>`).join('<i>/</i>')}</nav>`;
const stars = '<span class="stars">★★★★★ <small>4,9 · 128 avaliações</small></span>';

/* ---------- roteador ---------- */
function route() {
  const h = location.hash;
  const m = h.match(/^#\/([^/?]*)\/?([^?]*)(?:\?(.*))?$/);
  const main = $('#top');
  if (!m) {
    page.hidden = true; main.hidden = false;
    try { if (h.length > 1) document.querySelector(h)?.scrollIntoView(); else scrollTo(0, 0); } catch (e) {}
    return;
  }
  const [, name, arg, qs] = m;
  const params = new URLSearchParams(qs || '');
  main.hidden = true; page.hidden = false; scrollTo(0, 0);
  closeAll();
  if (name === 'produto' && byId(arg)) return productPage(byId(arg), +params.get('cor') || 0);
  if (name === 'fios' && LINES.find(l => l.id === arg)) return categoryPage(LINES.find(l => l.id === arg));
  if (name === 'checkout') return checkoutPage();
  if (name === 'obrigado' && lastOrder) return thanksPage();
  location.hash = '#top';
}
addEventListener('hashchange', route);

/* ---------- categoria ---------- */
function categoryPage(l) {
  const p = byId(l.id);
  page.innerHTML = `
  <section class="cat-hero" style="--c1:${l.c[0]};--c2:${l.c[1]}">
    <div class="wrap">
      ${crumbs([['Início', '#top'], ['Nossos fios', '#fios'], [l.n]])}
      <h1>${l.n}</h1><p>${l.d}</p>
      <span class="pill">a partir de ${brl(l.p)} · ${COLORS.length} cores disponíveis</span>
    </div>
  </section>
  <section class="section"><div class="wrap">
    <div class="chips chips--scroll">${LINES.map(x => `<a class="chip ${x.id === l.id ? 'on' : ''}" href="#/fios/${x.id}">${x.n}</a>`).join('')}</div>
    <div class="grid" style="margin-top:28px">
      ${p.variants.map((v, i) => `
      <article class="card">
        <a href="#/produto/${p.id}?cor=${i}" class="card__img">${i < 2 ? '<span class="tag">Mais vendido</span>' : ''}${media(p, v)}</a>
        <div class="card__body">
          <span class="card__cat">${l.n}</span>
          <h3 class="card__name"><a href="#/produto/${p.id}?cor=${i}">${v.n}</a></h3>
          <div class="price">${brl(p.price)}<small>ou 12x de ${brl(p.price / 12)}</small></div>
        </div>
        <button class="card__add" data-pqa="${p.id}:${i}">Adicionar</button>
      </article>`).join('')}
    </div>
  </div></section>`;
}

/* ---------- produto ---------- */
function productPage(p, v0) {
  const S = { v: Math.min(v0, p.variants.length - 1), q: 1 };
  const isYarn = p.type === 'fio';
  const related = (isYarn ? YARNS : SHAWLS).filter(x => x.id !== p.id).slice(0, 4);
  const draw = () => {
    const v = p.variants[S.v];
    page.innerHTML = `
    <div class="wrap pdp-wrap">
      ${crumbs([['Início', '#top'], isYarn ? ['Nossos fios', '#fios'] : ['Xales', '#xales'], isYarn ? [p.name, '#/fios/' + p.id] : [p.name]])}
      <div class="pdp">
        <div class="pdp__media">${p.tag ? `<span class="tag">${p.tag}</span>` : ''}${media(p, v)}</div>
        <div class="pdp__info">
          <span class="eyebrow">${p.cat}</span>
          <h1>${p.name}${isYarn ? ` <em>· ${v.n}</em>` : ''}</h1>
          ${stars}
          <div class="price price--lg">${brl(p.price)}<small>ou 12x de ${brl(p.price / 12)} sem juros · Pix ${brl(p.price * .95)} (5% off)</small></div>
          <p class="pdp__desc">${p.desc}</p>
          ${isYarn ? `<div class="vlabel">Cor: <b>${v.n}</b></div>
            <div class="variants">${p.variants.map((x, i) => `<button class="var ${i === S.v ? 'on' : ''}" data-pv="${i}" style="${grad(x.c)}" aria-label="${x.n}" title="${x.n}"></button>`).join('')}</div>` : ''}
          <div class="qty-row">
            <div class="qty"><button data-pq="-1">−</button><span>${S.q}</span><button data-pq="1">+</button></div>
            <button class="btn btn--primary btn--block" data-padd>Adicionar ao carrinho</button>
          </div>
          <button class="btn btn--ghost btn--block" data-pbuy>Comprar agora</button>
          <ul class="trust"><li>🧶 Mesmo lote de cor na mesma compra</li><li>🚚 Envio em até 3 dias úteis</li><li>↩ 7 dias para troca</li></ul>
          <div class="cep"><b>Calcular frete</b>
            <div><input id="cepIn" inputmode="numeric" maxlength="9" placeholder="00000-000"><button class="btn btn--ghost" data-cep>Calcular</button></div>
            <div id="cepOut"></div></div>
          <details open><summary>Descrição</summary><p>${isYarn ? 'Novelo artesanal tingido à mão, com degradê único. Cada novelo pode variar levemente de tom, por isso recomendamos comprar toda a quantidade do projeto de uma só vez.' : 'Peça única crochetada à mão com fios degradê Nouvellando. Dimensões e tonalidade podem variar levemente por serem peças artesanais.'}</p></details>
          <details><summary>${isYarn ? 'Composição e metragem' : 'Medidas e composição'}</summary><p>${isYarn ? 'Composição e metragem variam por linha. (Dados de exemplo.)' : 'Aprox. 180 x 80 cm. Fio degradê Nouvellando. (Dados de exemplo.)'}</p></details>
          <details><summary>Cuidados</summary><p>Lavar à mão com água fria e sabão neutro. Secar na horizontal, à sombra.</p></details>
        </div>
      </div>
      <h2 class="rel-title">Você também pode gostar</h2>
      <div class="grid">${related.map(cardHTML).join('')}</div>
    </div>`;
  };
  draw();
  page.onclick = e => {
    const t = e.target; let el;
    if ((el = t.closest('[data-pv]'))) { S.v = +el.dataset.pv; history.replaceState(null, '', `#/produto/${p.id}?cor=${S.v}`); const y = scrollY; draw(); scrollTo(0, y); return; }
    if ((el = t.closest('[data-pq]'))) { S.q = Math.max(1, S.q + +el.dataset.pq); page.querySelector('.pdp .qty span').textContent = S.q; return; }
    if (t.closest('[data-padd]')) { addToCart(p.id, S.v, S.q); $('#drawer').hidden = false; return; }
    if (t.closest('[data-pbuy]')) { addToCart(p.id, S.v, S.q); location.hash = '#/checkout'; return; }
    if (t.closest('[data-cep]')) {
      const d = $('#cepIn').value.replace(/\D/g, '');
      if (d.length !== 8) return ($('#cepOut').innerHTML = '<small class="err">Digite um CEP válido.</small>');
      const base = 18 + (+d[0] * 2);
      $('#cepOut').innerHTML = `<div class="ship-opt"><span>PAC · 5 a 8 dias úteis</span><b>${brl(base)}</b></div><div class="ship-opt"><span>SEDEX · 2 a 3 dias úteis</span><b>${brl(base + 14)}</b></div>`;
      return;
    }
  };
  $('#cepIn').addEventListener('input', e => { e.target.value = e.target.value.replace(/\D/g, '').slice(0, 8).replace(/^(\d{5})(\d)/, '$1-$2'); });
}

/* adicionar direto da página de categoria */
document.addEventListener('click', e => {
  const el = e.target.closest('[data-pqa]');
  if (!el) return;
  const [id, v] = el.dataset.pqa.split(':');
  addToCart(id, +v, 1);
});

/* ---------- checkout ---------- */
function checkoutPage() {
  if (!cart.length) {
    page.innerHTML = `<div class="wrap empty-page"><h1>Seu carrinho está vazio</h1><p>Escolha algumas cores para começar.</p><a class="btn btn--primary" href="#loja">Ver novelos</a></div>`;
    return;
  }
  const S = { ship: 'pac', pay: 'pix', coupon: 0, code: '' };
  const sub = () => cart.reduce((s, i) => s + byId(i.id).price * i.q, 0);
  const shipCost = () => S.ship === 'sedex' ? 39.9 : (sub() >= FREE_SHIP ? 0 : 24.9);
  const discount = () => (S.pay === 'pix' ? sub() * .05 : 0) + sub() * S.coupon;
  const total = () => sub() + shipCost() - discount();

  page.innerHTML = `
  <div class="wrap co">
    <div class="co__top"><a class="logo" href="#top">Nouvellando<sup>®</sup></a>
      <ol class="steps"><li class="done">Carrinho</li><li class="on">Dados e pagamento</li><li>Confirmação</li></ol></div>
    <form class="co__grid" id="coForm">
      <div class="co__main">
        <section class="box"><h2><i>1</i> Contato</h2>
          <div class="f2"><label>E-mail<input type="email" required placeholder="voce@email.com"></label>
          <label>Celular / WhatsApp<input required inputmode="tel" placeholder="(16) 90000-0000"></label></div></section>
        <section class="box"><h2><i>2</i> Entrega</h2>
          <div class="f2"><label>Nome completo<input required></label><label>CPF<input required inputmode="numeric" maxlength="14" id="cpf" placeholder="000.000.000-00"></label></div>
          <div class="f3"><label>CEP<input required id="cep" inputmode="numeric" maxlength="9" placeholder="00000-000"></label>
          <label class="span2">Endereço<input required></label></div>
          <div class="f3"><label>Número<input required></label><label>Complemento<input></label><label>Bairro<input required></label></div>
          <div class="f3"><label class="span2">Cidade<input required></label><label>UF<input required maxlength="2" style="text-transform:uppercase"></label></div>
          <div class="opts" id="shipOpts"></div></section>
        <section class="box"><h2><i>3</i> Pagamento</h2>
          <div class="tabs" id="payTabs">
            <button type="button" class="on" data-pay="pix">Pix <small>−5%</small></button>
            <button type="button" data-pay="card">Cartão</button>
            <button type="button" data-pay="boleto">Boleto</button></div>
          <div data-panel="pix" class="panel"><div class="qr" aria-hidden="true"></div><p>O código Pix será exibido após finalizar o pedido. Aprovação imediata e <b>5% de desconto</b>.</p></div>
          <div data-panel="card" class="panel" hidden>
            <label>Número do cartão<input required id="cc" inputmode="numeric" maxlength="19" placeholder="0000 0000 0000 0000" disabled></label>
            <label>Nome impresso<input required disabled></label>
            <div class="f3"><label>Validade<input required maxlength="5" id="exp" placeholder="MM/AA" disabled></label><label>CVV<input required maxlength="4" inputmode="numeric" disabled></label>
            <label>Parcelas<select disabled id="inst"></select></label></div></div>
          <div data-panel="boleto" class="panel" hidden><p>O boleto vence em 2 dias úteis. O pedido é liberado após a compensação.</p></div>
        </section>
        <button class="btn btn--primary btn--block btn--lg" id="coSubmit">Finalizar pedido</button>
        <p class="demo-note">Ambiente de demonstração: nenhum dado é enviado ou cobrado.</p>
      </div>
      <aside class="co__side"><div class="box sticky">
        <h2>Resumo do pedido</h2>
        <div id="coItems"></div>
        <div class="coupon"><input id="cpIn" placeholder="Cupom de desconto"><button type="button" class="btn btn--ghost" id="cpBtn">Aplicar</button></div>
        <div id="coTotals"></div>
      </div></aside>
    </form>
  </div>`;

  const upd = () => {
    $('#coItems').innerHTML = cart.map(i => { const p = byId(i.id), v = p.variants[i.v];
      return `<div class="sum-item"><div class="item__img">${media(p, v)}<em>${i.q}</em></div><div><b>${p.name}</b><small>${p.type === 'fio' ? v.n : 'Pronta-entrega'}</small></div><span>${brl(p.price * i.q)}</span></div>`; }).join('');
    $('#shipOpts').innerHTML = [['pac', 'PAC · 5 a 8 dias úteis', shipCost() && S.ship === 'pac' ? 24.9 : sub() >= FREE_SHIP ? 0 : 24.9], ['sedex', 'SEDEX · 2 a 3 dias úteis', 39.9]]
      .map(([id, n, c]) => `<label class="opt ${S.ship === id ? 'on' : ''}"><input type="radio" name="ship" value="${id}" ${S.ship === id ? 'checked' : ''}><span>${n}</span><b>${c ? brl(c) : 'Grátis'}</b></label>`).join('');
    $('#inst').innerHTML = [1, 2, 3, 6, 12].map(n => `<option>${n}x de ${brl(total() / n)} sem juros</option>`).join('');
    $('#coTotals').innerHTML = `<div class="row"><span>Subtotal</span><span>${brl(sub())}</span></div>
      <div class="row"><span>Frete</span><span>${shipCost() ? brl(shipCost()) : 'Grátis'}</span></div>
      ${discount() ? `<div class="row ok"><span>Descontos${S.code ? ' (' + S.code + ')' : ''}</span><span>− ${brl(discount())}</span></div>` : ''}
      <div class="row total"><span>Total</span><b>${brl(total())}</b></div>`;
  };
  upd();

  const form = $('#coForm');
  const mask = (id, fn) => $(id).addEventListener('input', e => (e.target.value = fn(e.target.value.replace(/\D/g, ''))));
  mask('#cpf', d => d.slice(0, 11).replace(/(\d{3})(\d)/, '$1.$2').replace(/(\d{3})(\d)/, '$1.$2').replace(/(\d{3})(\d{1,2})$/, '$1-$2'));
  mask('#cep', d => d.slice(0, 8).replace(/^(\d{5})(\d)/, '$1-$2'));
  mask('#cc', d => d.slice(0, 16).replace(/(\d{4})(?=\d)/g, '$1 '));
  mask('#exp', d => d.slice(0, 4).replace(/^(\d{2})(\d)/, '$1/$2'));

  form.addEventListener('change', e => { if (e.target.name === 'ship') { S.ship = e.target.value; upd(); } });
  form.addEventListener('click', e => {
    const t = e.target.closest('[data-pay]');
    if (t) {
      S.pay = t.dataset.pay;
      form.querySelectorAll('[data-pay]').forEach(b => b.classList.toggle('on', b === t));
      form.querySelectorAll('[data-panel]').forEach(p => {
        const on = p.dataset.panel === S.pay; p.hidden = !on;
        p.querySelectorAll('input,select').forEach(i => (i.disabled = !on));
      });
      upd();
    }
    if (e.target.closest('#cpBtn')) {
      const c = $('#cpIn').value.trim().toUpperCase();
      if (c === 'BEMVINDA') { S.coupon = .1; S.code = c; toast('Cupom aplicado: 10% de desconto'); upd(); }
      else toast('Cupom inválido. Dica: BEMVINDA');
    }
  });
  $('#cpIn').addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); $('#cpBtn').click(); } });
  form.addEventListener('submit', e => {
    e.preventDefault();
    lastOrder = { n: 'NV' + Math.floor(100000 + Math.random() * 899999), total: total(), pay: S.pay, ship: S.ship, items: cart.map(i => ({ ...i })) };
    cart.length = 0; save(); renderCart();
    location.hash = '#/obrigado';
  });
}

/* ---------- confirmação ---------- */
function thanksPage() {
  const o = lastOrder;
  const payTxt = { pix: 'Pix', card: 'Cartão de crédito', boleto: 'Boleto' }[o.pay];
  page.innerHTML = `<div class="wrap thanks">
    <div class="check">✓</div>
    <h1>Pedido confirmado!</h1>
    <p>Obrigada pela compra. Enviamos os detalhes para o seu e-mail.</p>
    <div class="box thanks__box">
      <div class="row"><span>Número do pedido</span><b>#${o.n}</b></div>
      <div class="row"><span>Pagamento</span><b>${payTxt}</b></div>
      <div class="row"><span>Entrega</span><b>${o.ship === 'sedex' ? 'SEDEX · 2 a 3 dias úteis' : 'PAC · 5 a 8 dias úteis'}</b></div>
      <div class="row total"><span>Total</span><b>${brl(o.total)}</b></div>
      ${o.pay === 'pix' ? '<div class="qr" aria-hidden="true"></div><small>Código Pix de exemplo, válido apenas na demonstração.</small>' : ''}
    </div>
    <a class="btn btn--primary" href="#top">Voltar para a loja</a>
  </div>`;
}

route();
