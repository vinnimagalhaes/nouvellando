/* Nouvellando · front-end demo (dados fictícios, sem backend) */
const IMG = 'https://i0.wp.com/nouvellando.com.br/wp-content/uploads/';

const brl = n => n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
const $ = s => document.querySelector(s);

/* ---------- dados ---------- */
// Cores degradê (nome + 3 tons)
const COLORS = [
  { n: 'Aurora', c: ['#8e2f5b', '#d9578a', '#f3a9b8'] },
  { n: 'Mar Aberto', c: ['#1f6f78', '#58b6a8', '#e8d98a'] },
  { n: 'Pôr do Sol', c: ['#e8a04c', '#e86a4c', '#7a2d5b'] },
  { n: 'Jardim', c: ['#3f7d4e', '#9bc47a', '#f2e29b'] },
  { n: 'Lavanda', c: ['#5b4b9a', '#a58ad6', '#e6d3f2'] },
  { n: 'Terra', c: ['#5a3a2a', '#b2704a', '#f0c9a0'] },
  { n: 'Glacial', c: ['#2c5a8f', '#7fb2e0', '#e4f1fa'] },
  { n: 'Framboesa', c: ['#a3123f', '#e0426b', '#ffb3c1'] },
];
const cw = i => COLORS[i % COLORS.length];

const LINES = [
  { id: 'original', n: 'Fio Original', p: 49.9, d: 'O clássico da casa: macio, versátil e perfeito para xales e echarpes.', c: ['#8e2f5b', '#e8a04c'], img: '2024/04/552U.jpg' },
  { id: 'twinkle', n: 'Twinkle', p: 54.9, d: 'Com fios metalizados que brilham sutilmente a cada ponto.', c: ['#2c5a8f', '#b58ad6'], img: '2024/04/403T.jpg' },
  { id: 'stardust', n: 'Stardust', p: 56.9, d: 'Pontinhos de brilho como poeira estelar, para peças especiais.', c: ['#5b4b9a', '#e8a04c'] },
  { id: 'fluffinho', n: 'Fluffinho', p: 52.9, d: 'Fofinho e leve, ótimo para peças aconchegantes.', c: ['#d9578a', '#f3c9d4'] },
  { id: 'peluche', n: 'Peluche', p: 59.9, d: 'Textura de pelúcia, ideal para mantas e acessórios.', c: ['#5a3a2a', '#d9a27a'] },
  { id: 'breezy', n: 'Breezy', p: 51.9, d: 'Leve e arejado, ótimo para o verão.', c: ['#1f6f78', '#9bd6c8'] },
  { id: 'paillettes', n: 'Paillettes', p: 62.9, d: 'Com lantejoulas delicadas para um toque de festa.', c: ['#a3123f', '#f3b86c'] },
  { id: 'boucle', n: 'Bouclé', p: 57.9, d: 'Textura encaracolada com muito charme.', c: ['#7a6d73', '#efe4d8'], img: '2026/03/Boucle.jpg' },
  { id: 'ice', n: 'Ice', p: 48.9, d: 'Tons frios e delicados, com acabamento gelado.', c: ['#2c5a8f', '#e4f1fa'] },
  { id: 'aura', n: 'Aura', p: 55.9, d: 'Degradês suaves com um brilho especial.', c: ['#3f7d4e', '#f2e29b'] },
  { id: 'cor-unica', n: 'Cor Única', p: 44.9, d: 'Cores sólidas para combinar com seus degradês.', c: ['#2b2227', '#7a6d73'] },
  { id: 'sem-degrade', n: 'Sem degradê', p: 42.9, d: 'Cores lisas, tingidas à mão.', c: ['#e8a04c', '#e86a4c'] },
];

// cada linha tem 4 variações de cor
const YARNS = LINES.map((l, i) => ({
  id: l.id, type: 'fio', cat: l.n, name: l.n, price: l.p, desc: l.d, img: l.img,
  tag: i < 2 ? 'Mais vendido' : null,
  variants: COLORS.map((_, k) => cw(i + k)),
  rel: 100 - i,
}));

const SHAWLS = [
  { id: 'x-tarragona', name: 'Xale Tarragona', price: 489, img: '2023/12/Xale-tarragona-9-rotated.jpg' },
  { id: 'x-september', name: 'Xale September', price: 459, img: '2023/11/Xale-September-7-1-rotated.jpg' },
  { id: 'x-citylights', name: 'Xale Citylights', price: 529, img: '2023/11/Xale-Citylights-1-2-rotated.jpg' },
  { id: 'x-bayka', name: 'Xale Bayka', price: 479 },
  { id: 'x-outlander', name: 'Xale Outlander', price: 499 },
  { id: 'x-kicia', name: 'Xale Kicia', price: 449 },
].map((s, i) => ({
  ...s, type: 'xale', cat: 'Xale pronta-entrega', tag: 'Pronta-entrega',
  desc: 'Peça única feita à mão com fios Nouvellando. Pronta para envio.',
  variants: [cw(i * 3)], rel: 50 - i,
}));

const LESSONS = ['Xale Tarragona', 'Xale Wheel of Time', 'Xale September', 'Xale Citylights', 'Xale Kira', 'Xale Andromeda', 'Xale Magnolia', 'Xale Thistle', 'Manta Tarragona'];

const PRODUCTS = [...YARNS, ...SHAWLS];
const byId = id => PRODUCTS.find(p => p.id === id);

/* ---------- estado ---------- */
let cart = [];
try { cart = JSON.parse(localStorage.getItem('nv-cart')) || []; } catch (e) {}
const save = () => { try { localStorage.setItem('nv-cart', JSON.stringify(cart)); } catch (e) {} };
let filter = 'all', query = '', sort = 'rel';

/* ---------- helpers de visual ---------- */
const grad = c => `--c1:${c[0]};--c2:${c[1]};--c3:${c[2] || c[1]}`;
const media = (p, v) => p.img
  ? `<img src="${IMG}${p.img}" alt="${p.name}" loading="lazy" onerror="this.replaceWith(Object.assign(document.createElement('div'),{className:'skein'}))">`
  : `<div class="skein" style="${grad(v.c)}"></div>`;

/* ---------- renders ---------- */
function renderLines() {
  $('#lines').innerHTML = LINES.map(l =>
    `<button class="line" style="--c1:${l.c[0]};--c2:${l.c[1]}" data-line="${l.id}"><b>${l.n}</b><small>a partir de ${brl(l.p)}</small></button>`).join('');
}

function renderChips() {
  const opts = [['all', 'Todos'], ...LINES.map(l => [l.id, l.n])];
  $('#chips').innerHTML = opts.map(([id, n]) => `<button class="chip ${filter === id ? 'on' : ''}" data-chip="${id}">${n}</button>`).join('');
}

function cardHTML(p) {
  const v = p.variants[0];
  return `<article class="card" data-open="${p.id}" tabindex="0">
    <div class="card__img">${p.tag ? `<span class="tag">${p.tag}</span>` : ''}${media(p, v)}</div>
    <div class="card__body">
      <span class="card__cat">${p.cat}</span>
      <h3 class="card__name">${p.name}</h3>
      ${p.type === 'fio' ? `<div class="dots">${p.variants.slice(0, 5).map(x => `<i style="${grad(x.c)}"></i>`).join('')}</div>` : ''}
      <div class="price">${p.type === 'fio' ? 'a partir de ' : ''}${brl(p.price)}<small>ou 12x de ${brl(p.price / 12)}</small></div>
    </div>
    <button class="card__add" data-quick="${p.id}">Adicionar</button>
  </article>`;
}

function renderGrid() {
  let list = YARNS.filter(p => (filter === 'all' || p.id === filter) &&
    (!query || (p.name + p.variants.map(v => v.n).join(' ')).toLowerCase().includes(query)));
  list.sort((a, b) => ({
    rel: b.rel - a.rel, asc: a.price - b.price, desc: b.price - a.price, az: a.name.localeCompare(b.name),
  })[sort]);
  $('#grid').innerHTML = list.length ? list.map(cardHTML).join('') : '<p class="empty">Nenhum fio encontrado. Tente outra busca.</p>';
  $('#resultInfo').textContent = `${list.length} ${list.length === 1 ? 'linha de fio' : 'linhas de fio'} · cada uma em dezenas de cores`;
}

function renderStatic() {
  $('#shawls').innerHTML = SHAWLS.map(cardHTML).join('');
  $('#lessons').innerHTML = LESSONS.map(l => `<a class="lesson" href="#" data-toast="Redireciona para a Hotmart na versão final"><i>▶</i>${l}</a>`).join('');
}

/* ---------- modal ---------- */
let cur = null, curV = 0, curQ = 1;
function openModal(id) {
  cur = byId(id); curV = 0; curQ = 1;
  $('#mCat').textContent = cur.cat;
  $('#mName').textContent = cur.name;
  $('#mDesc').textContent = cur.desc;
  $('#mPrice').innerHTML = brl(cur.price) + `<small>ou 12x de ${brl(cur.price / 12)} · Pix ${brl(cur.price * .95)}</small>`;
  $('#mVariants').innerHTML = cur.type === 'fio'
    ? `<div class="vlabel">Cor: <span id="vName"></span></div><div class="variants">${cur.variants.map((v, i) => `<button class="var" data-var="${i}" style="${grad(v.c)}" aria-label="${v.n}"></button>`).join('')}</div>`
    : '';
  paintVariant();
  $('#qVal').textContent = 1;
  $('#modal').hidden = false;
  document.body.style.overflow = 'hidden';
}
function paintVariant() {
  const v = cur.variants[curV];
  $('#mMedia').innerHTML = cur.img && cur.type === 'xale' ? media(cur, v) : `<div class="skein" style="${grad(v.c)}"></div>`;
  if (cur.type === 'fio') {
    $('#vName').textContent = v.n;
    document.querySelectorAll('.var').forEach((b, i) => b.classList.toggle('on', i === curV));
  }
}
function closeAll() {
  $('#modal').hidden = true; $('#drawer').hidden = true;
  document.body.style.overflow = '';
}

/* ---------- carrinho ---------- */
const FREE = 299;
function addToCart(id, v, q) {
  const p = byId(id);
  const key = id + ':' + v;
  const it = cart.find(i => i.key === key);
  it ? it.q += q : cart.push({ key, id, v, q });
  save(); renderCart();
  const b = $('#cartCount'); b.classList.add('pop'); setTimeout(() => b.classList.remove('pop'), 300);
  toast(`${p.name} adicionado ao carrinho`);
}
function renderCart() {
  const n = cart.reduce((s, i) => s + i.q, 0);
  const total = cart.reduce((s, i) => s + byId(i.id).price * i.q, 0);
  $('#cartCount').textContent = n;
  $('#subtotal').textContent = brl(total);
  const left = FREE - total;
  $('#ship').innerHTML = left > 0
    ? `Faltam <b>${brl(left)}</b> para o frete grátis<div class="bar"><i style="width:${Math.min(100, total / FREE * 100)}%"></i></div>`
    : `🎉 Você ganhou <b>frete grátis</b>!<div class="bar"><i style="width:100%"></i></div>`;
  $('#cartItems').innerHTML = cart.length ? cart.map((i, idx) => {
    const p = byId(i.id), v = p.variants[i.v];
    return `<div class="item">
      <div class="item__img">${media(p, v)}</div>
      <div><b>${p.name}</b><small>${p.type === 'fio' ? v.n : 'Pronta-entrega'}</small>
        <div class="qty"><button data-dec="${idx}">−</button><span>${i.q}</span><button data-inc="${idx}">+</button></div></div>
      <div class="item__p">${brl(p.price * i.q)}<button class="item__rm" data-rm="${idx}">remover</button></div>
    </div>`;
  }).join('') : '<p class="drawer__empty">Seu carrinho está vazio.<br>Que tal escolher algumas cores?</p>';
}

function toast(msg) {
  const t = $('#toast'); t.textContent = msg; t.classList.add('show');
  clearTimeout(toast.t); toast.t = setTimeout(() => t.classList.remove('show'), 2400);
}

/* ---------- eventos ---------- */
document.addEventListener('click', e => {
  const t = e.target;
  const q = s => t.closest(s);
  let el;
  if ((el = q('[data-quick]'))) { e.stopPropagation(); const p = byId(el.dataset.quick); p.type === 'fio' ? openModal(p.id) : addToCart(p.id, 0, 1); return; }
  if ((el = q('[data-open]'))) { location.hash = '#/produto/' + el.dataset.open; return; }
  if ((el = q('[data-line]'))) { location.hash = '#/fios/' + el.dataset.line; return; }
  if ((el = q('[data-chip]'))) { filter = el.dataset.chip; renderChips(); return renderGrid(); }
  if ((el = q('[data-var]'))) { curV = +el.dataset.var; return paintVariant(); }
  if ((el = q('[data-toast]'))) { e.preventDefault(); return toast(el.dataset.toast); }
  if (q('[data-close]')) return closeAll();
  if (q('[data-close-cart]')) return closeAll();
  if ((el = q('[data-inc]'))) { cart[el.dataset.inc].q++; save(); return renderCart(); }
  if ((el = q('[data-dec]'))) { const i = cart[el.dataset.dec]; if (i.q > 1) i.q--; save(); return renderCart(); }
  if ((el = q('[data-rm]'))) { cart.splice(el.dataset.rm, 1); save(); return renderCart(); }
  if (q('#qPlus')) return ($('#qVal').textContent = ++curQ);
  if (q('#qMinus')) return ($('#qVal').textContent = curQ = Math.max(1, curQ - 1));
  if (q('#mAdd')) { addToCart(cur.id, curV, curQ); closeAll(); $('#drawer').hidden = false; return; }
  if (q('#cartBtn')) { $('#drawer').hidden = false; return; }
  if (q('#checkout')) { if (!cart.length) return toast('Seu carrinho está vazio'); closeAll(); location.hash = '#/checkout'; return; }
  if (q('#searchBtn')) { const s = $('#searchbar'); s.classList.toggle('open'); if (s.classList.contains('open')) $('#globalSearch').focus(); return; }
  if (q('#menuBtn')) return $('#nav').classList.toggle('open');
  if (q('.nav a')) $('#nav').classList.remove('open');
});
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeAll();
  if (e.key === 'Enter' && e.target.matches('.card')) location.hash = '#/produto/' + e.target.dataset.open;
});
$('#sort').addEventListener('change', e => { sort = e.target.value; renderGrid(); });
$('#globalSearch').addEventListener('input', e => {
  query = e.target.value.trim().toLowerCase(); filter = 'all'; renderChips(); renderGrid();
  if (query) $('#loja').scrollIntoView();
});
$('#newsForm').addEventListener('submit', e => { e.preventDefault(); e.target.reset(); toast('Obrigado! Você está na lista ✿'); });

renderLines(); renderChips(); renderGrid(); renderStatic(); renderCart();
