// Картинки модели из 3mf: общий вид и четыре проекции (спереди, слева, справа, сверху) с габаритами.
//
//   node tools/render-3mf.mjs <модель.3mf> <папка_для_картинок> [--name "Название"] [--color "#RRGGBB"] [--filled]
//
// Создаёт iso.png, front.png, left.png, right.png, top.png и preview.png (если в 3mf есть миниатюра).
// С --filled на вход идёт сцена «модель с содержимым», а на выходе один общий вид filled.png.
// Цвета деталей берутся из 3mf (basematerials, displaycolor), детали без цвета красятся в --color.
// Перед первым запуском: `npm install` в папке tools/.
// Оси как в слайсере: X — слева направо, Y — от себя (перед = минимальный Y), Z — вверх.

import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import { Resvg } from '@resvg/resvg-js';

const SS = 2;                 // суперсэмплинг: рендер в SS раз крупнее, потом усреднение
const ORTHO_PX = 900;         // самый большой габарит модели на проекциях, px
const ISO_PX = 1000;          // ширина общего вида, px
const BG = [255, 255, 255];
const INK = '#2b3036';        // размерные линии и подписи
const FONT = 'Segoe UI, Arial, sans-serif';

// ---------- zip ----------

function readZip(buf) {
  let eocd = -1;
  for (let i = buf.length - 22; i >= Math.max(0, buf.length - 65557); i--) {
    if (buf.readUInt32LE(i) === 0x06054b50) { eocd = i; break; }
  }
  if (eocd < 0) throw new Error('это не zip-архив (3mf — это zip)');
  const count = buf.readUInt16LE(eocd + 10);
  let p = buf.readUInt32LE(eocd + 16);
  const entries = new Map();
  for (let n = 0; n < count; n++) {
    if (buf.readUInt32LE(p) !== 0x02014b50) throw new Error('битый каталог zip');
    const method = buf.readUInt16LE(p + 10);
    let csize = buf.readUInt32LE(p + 20);
    let usize = buf.readUInt32LE(p + 24);
    const nameLen = buf.readUInt16LE(p + 28), extraLen = buf.readUInt16LE(p + 30), commentLen = buf.readUInt16LE(p + 32);
    let local = buf.readUInt32LE(p + 42);
    const name = buf.toString('utf8', p + 46, p + 46 + nameLen);
    // zip64: настоящие размеры и смещение лежат в дополнительном поле 0x0001
    if (csize === 0xffffffff || usize === 0xffffffff || local === 0xffffffff) {
      for (let e = p + 46 + nameLen; e + 4 <= p + 46 + nameLen + extraLen;) {
        const id = buf.readUInt16LE(e), size = buf.readUInt16LE(e + 2);
        if (id === 0x0001) {
          let q = e + 4;
          if (usize === 0xffffffff) { usize = Number(buf.readBigUInt64LE(q)); q += 8; }
          if (csize === 0xffffffff) { csize = Number(buf.readBigUInt64LE(q)); q += 8; }
          if (local === 0xffffffff) { local = Number(buf.readBigUInt64LE(q)); }
        }
        e += 4 + size;
      }
    }
    const start = local + 30 + buf.readUInt16LE(local + 26) + buf.readUInt16LE(local + 28);
    entries.set(name, { method, data: buf.subarray(start, start + csize) });
    p += 46 + nameLen + extraLen + commentLen;
  }
  return {
    names: [...entries.keys()],
    get(name) {
      const e = entries.get(name.replace(/^\//, ''));
      if (!e) return null;
      if (e.method === 0) return e.data;
      if (e.method === 8) return zlib.inflateRawSync(e.data);
      throw new Error(`метод сжатия ${e.method} не поддерживается: ${name}`);
    },
  };
}

// ---------- 3mf ----------

const IDENTITY = [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0];

function attrs(s) {
  const a = {};
  for (const m of s.matchAll(/([\w:]+)\s*=\s*"([^"]*)"/g)) a[m[1]] = m[2];
  return a;
}

function parseTransform(s) {
  if (!s) return IDENTITY;
  const t = s.trim().split(/\s+/).map(Number);
  return t.length === 12 ? t : IDENTITY;
}

// Матрица 3mf — 4×3 для вектора-строки: p' = p · M. mul(a, b) — сначала a, потом b.
function mul(a, b) {
  const r = new Array(12);
  for (let i = 0; i < 4; i++) {
    for (let j = 0; j < 3; j++) {
      r[i * 3 + j] = a[i * 3] * b[j] + a[i * 3 + 1] * b[3 + j] + a[i * 3 + 2] * b[6 + j] + (i === 3 ? b[9 + j] : 0);
    }
  }
  return r;
}

function parseHexColor(s) {
  const m = /^#?([0-9a-f]{6})([0-9a-f]{2})?$/i.exec(s ?? '');
  if (!m) return null;
  const v = parseInt(m[1], 16);
  return [(v >> 16) & 255, (v >> 8) & 255, v & 255];
}

function parseModel(xml) {
  const materials = new Map();
  for (const m of xml.matchAll(/<basematerials\b([^>]*)>([\s\S]*?)<\/basematerials>/g)) {
    materials.set(attrs(m[1]).id, [...m[2].matchAll(/<base\b([^>]*)>/g)].map((b) => parseHexColor(attrs(b[1]).displaycolor)));
  }
  const objects = new Map();
  for (const m of xml.matchAll(/<object\b([^>]*)>([\s\S]*?)<\/object>/g)) {
    const a = attrs(m[1]);
    const body = m[2];
    const obj = { mesh: null, components: [], pid: a.pid ?? null, pindex: +(a.pindex ?? 0) };
    const mesh = /<mesh\b[^>]*>([\s\S]*?)<\/mesh>/.exec(body);
    if (mesh) {
      const v = [], t = [], tm = [];
      for (const x of mesh[1].matchAll(/<vertex\b([^>]*)>/g)) { const q = attrs(x[1]); v.push(+q.x, +q.y, +q.z); }
      for (const x of mesh[1].matchAll(/<triangle\b([^>]*)>/g)) {
        const q = attrs(x[1]);
        t.push(+q.v1, +q.v2, +q.v3);
        tm.push(q.p1 !== undefined ? { pid: q.pid ?? obj.pid, p1: +q.p1 } : null);
      }
      obj.mesh = { v, t, tm };
    }
    for (const c of body.matchAll(/<component\b([^>]*)>/g)) {
      const q = attrs(c[1]);
      obj.components.push({ id: q.objectid, path: q['p:path'] || null, transform: parseTransform(q.transform) });
    }
    objects.set(a.id, obj);
  }
  const items = [];
  const build = /<build\b[^>]*>([\s\S]*?)<\/build>/.exec(xml);
  if (build) {
    for (const it of build[1].matchAll(/<item\b([^>]*)>/g)) {
      const q = attrs(it[1]);
      items.push({ id: q.objectid, path: q['p:path'] || null, transform: parseTransform(q.transform) });
    }
  }
  return { objects, items, materials };
}

// Все треугольники сборки в мировых координатах: Float64Array, 9 чисел на треугольник.
// colors — цвет треугольника (0xRRGGBB) или -1, parts — номер детали, которой он принадлежит.
function loadTriangles(zip) {
  const rels = zip.get('_rels/.rels')?.toString('utf8') ?? '';
  const root = (/Target="([^"]+\.model)"/.exec(rels)?.[1] ?? '/3D/3dmodel.model').replace(/^\//, '');
  const cache = new Map();
  const model = (p) => {
    if (!cache.has(p)) {
      const data = zip.get(p);
      if (!data) throw new Error(`в 3mf нет файла ${p}`);
      cache.set(p, parseModel(data.toString('utf8')));
    }
    return cache.get(p);
  };
  const out = [], colors = [], parts = [];
  let part = 0;
  const pack = (c) => (c ? (c[0] << 16) | (c[1] << 8) | c[2] : -1);
  const visit = (file, id, m) => {
    const { objects, materials } = model(file);
    const obj = objects.get(id);
    if (!obj) throw new Error(`объект ${id} не найден в ${file}`);
    if (obj.mesh) {
      const { v, t, tm } = obj.mesh;
      const objColor = obj.pid !== null ? materials.get(obj.pid)?.[obj.pindex] : null;
      for (let k = 0; k < t.length / 3; k++) {
        for (let j = 0; j < 3; j++) {
          const idx = t[k * 3 + j];
          const x = v[idx * 3], y = v[idx * 3 + 1], z = v[idx * 3 + 2];
          out.push(x * m[0] + y * m[3] + z * m[6] + m[9], x * m[1] + y * m[4] + z * m[7] + m[10], x * m[2] + y * m[5] + z * m[8] + m[11]);
        }
        const own = tm[k] ? materials.get(tm[k].pid)?.[tm[k].p1] : null;
        colors.push(pack(own ?? objColor));
        parts.push(part);
      }
      part++;
    }
    for (const c of obj.components) visit(c.path ? c.path.replace(/^\//, '') : file, c.id, mul(c.transform, m));
  };
  const { items } = model(root);
  for (const it of items) visit(it.path ? it.path.replace(/^\//, '') : root, it.id, it.transform);
  return { tris: Float64Array.from(out), colors: Int32Array.from(colors), parts: Int32Array.from(parts), items: items.length };
}

function thumbnail(zip) {
  const pngs = zip.names.filter((n) => /^Metadata\/.*\.png$/i.test(n));
  const pick = ['Metadata/plate_1.png', 'Metadata/thumbnail.png'].find((n) => pngs.includes(n)) ?? pngs[0];
  return pick ? zip.get(pick) : null;
}

// ---------- геометрия ----------

const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const norm = (a) => { const l = Math.hypot(...a) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };

function bounds(tris) {
  const min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity];
  for (let i = 0; i < tris.length; i += 3) {
    for (let k = 0; k < 3; k++) {
      if (tris[i + k] < min[k]) min[k] = tris[i + k];
      if (tris[i + k] > max[k]) max[k] = tris[i + k];
    }
  }
  return { min, max, size: [max[0] - min[0], max[1] - min[1], max[2] - min[2]] };
}

function volume(tris) {
  let v = 0;
  for (let i = 0; i < tris.length; i += 9) {
    const a = [tris[i], tris[i + 1], tris[i + 2]];
    v += dot(a, cross([tris[i + 3], tris[i + 4], tris[i + 5]], [tris[i + 6], tris[i + 7], tris[i + 8]]));
  }
  return Math.abs(v) / 6;
}

// Камера: forward — куда смотрим, up — что считается верхом картинки.
function camera(forward, up) {
  const f = norm(forward);
  const r = norm(cross(f, up));
  const u = cross(r, f);
  return { f, r, u };
}

const VIEWS = {
  front: { cam: camera([0, 1, 0], [0, 0, 1]), title: 'Вид спереди', depthShade: 0.45 },
  left: { cam: camera([1, 0, 0], [0, 0, 1]), title: 'Вид слева', depthShade: 0.45 },
  right: { cam: camera([-1, 0, 0], [0, 0, 1]), title: 'Вид справа', depthShade: 0.45 },
  top: { cam: camera([0, 0, -1], [0, 1, 0]), title: 'Вид сверху', depthShade: 0.45 },
  iso: { cam: camera([1, 1.3, -1], [0, 0, 1]), title: 'Общий вид', depthShade: 0.18 },
  // с содержимым смотрим чуть сверху, чтобы высокие предметы меньше заслоняли нижние
  filled: { cam: camera([1, 1.3, -1.6], [0, 0, 1]), title: 'С содержимым', depthShade: 0.18 },
};

// ---------- растеризация ----------

// scale — px на мм итоговой картинки, padF — поле вокруг модели, px.
// color — цвет треугольников, у которых в 3mf нет своего цвета.
function render(scene, view, scale, color, padF = 3) {
  const { tris, colors, parts } = scene;
  const { f, r, u } = view.cam;
  const n = tris.length / 9;
  const P = new Float64Array(tris.length);
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity, minD = Infinity, maxD = -Infinity;
  for (let i = 0; i < tris.length; i += 3) {
    const p = [tris[i], tris[i + 1], tris[i + 2]];
    const x = dot(p, r), y = dot(p, u), d = dot(p, f);
    P[i] = x; P[i + 1] = y; P[i + 2] = d;
    if (x < minX) minX = x; if (x > maxX) maxX = x;
    if (y < minY) minY = y; if (y > maxY) maxY = y;
    if (d < minD) minD = d; if (d > maxD) maxD = d;
  }
  const Wf = Math.ceil((maxX - minX) * scale) + 2 * padF;
  const Hf = Math.ceil((maxY - minY) * scale) + 2 * padF;
  const W = Wf * SS, H = Hf * SS, s = scale * SS, pad = padF * SS;

  // нормали и освещённость граней; свет — сверху из-за плеча наблюдателя, чуть слева
  const light = norm([-0.16 * r[0] + 0.52 * u[0] - 0.83 * f[0], -0.16 * r[1] + 0.52 * u[1] - 0.83 * f[1], -0.16 * r[2] + 0.52 * u[2] - 0.83 * f[2]]);
  const N = new Float64Array(n * 3);
  const shade = new Float64Array(n);
  const C = new Float64Array(n * 3);
  for (let t = 0; t < n; t++) {
    const c = colors[t];
    if (c < 0) { C[t * 3] = color[0]; C[t * 3 + 1] = color[1]; C[t * 3 + 2] = color[2]; }
    else { C[t * 3] = (c >> 16) & 255; C[t * 3 + 1] = (c >> 8) & 255; C[t * 3 + 2] = c & 255; }
  }
  for (let t = 0; t < n; t++) {
    const o = t * 9;
    let nn = norm(cross(
      [tris[o + 3] - tris[o], tris[o + 4] - tris[o + 1], tris[o + 5] - tris[o + 2]],
      [tris[o + 6] - tris[o], tris[o + 7] - tris[o + 1], tris[o + 8] - tris[o + 2]]));
    if (dot(nn, f) > 0) nn = [-nn[0], -nn[1], -nn[2]];
    N[t * 3] = nn[0]; N[t * 3 + 1] = nn[1]; N[t * 3 + 2] = nn[2];
    shade[t] = 0.4 + 0.6 * Math.max(0, dot(nn, light));
  }

  const zbuf = new Float32Array(W * H).fill(Infinity);
  const tid = new Int32Array(W * H).fill(-1);
  for (let t = 0; t < n; t++) {
    const o = t * 9;
    const X0 = (P[o] - minX) * s + pad, Y0 = (maxY - P[o + 1]) * s + pad, Z0 = P[o + 2];
    const X1 = (P[o + 3] - minX) * s + pad, Y1 = (maxY - P[o + 4]) * s + pad, Z1 = P[o + 5];
    const X2 = (P[o + 6] - minX) * s + pad, Y2 = (maxY - P[o + 7]) * s + pad, Z2 = P[o + 8];
    const area = (X1 - X0) * (Y2 - Y0) - (X2 - X0) * (Y1 - Y0);
    if (Math.abs(area) < 1e-9) continue;
    const x0 = Math.max(0, Math.floor(Math.min(X0, X1, X2))), x1 = Math.min(W - 1, Math.ceil(Math.max(X0, X1, X2)));
    const y0 = Math.max(0, Math.floor(Math.min(Y0, Y1, Y2))), y1 = Math.min(H - 1, Math.ceil(Math.max(Y0, Y1, Y2)));
    for (let py = y0; py <= y1; py++) {
      const cy = py + 0.5;
      for (let px = x0; px <= x1; px++) {
        const cx = px + 0.5;
        const w0 = ((X1 - cx) * (Y2 - cy) - (X2 - cx) * (Y1 - cy)) / area;
        const w1 = ((X2 - cx) * (Y0 - cy) - (X0 - cx) * (Y2 - cy)) / area;
        const w2 = 1 - w0 - w1;
        if (w0 < -1e-6 || w1 < -1e-6 || w2 < -1e-6) continue;
        const z = w0 * Z0 + w1 * Z1 + w2 * Z2;
        const i = py * W + px;
        if (z < zbuf[i]) { zbuf[i] = z; tid[i] = t; }
      }
    }
  }

  // контуры: край силуэта, ступенька по глубине, излом поверхности или граница двух деталей
  const edge = new Uint8Array(W * H);
  const depthJump = Math.max(1.5, 8 / s);
  const creaseCos = Math.cos((35 * Math.PI) / 180);
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      const i = y * W + x, a = tid[i];
      for (const j of [x + 1 < W ? i + 1 : -1, y + 1 < H ? i + W : -1]) {
        if (j < 0) continue;
        const b = tid[j];
        if (a === b) continue;
        let hit = a < 0 || b < 0 || Math.abs(zbuf[i] - zbuf[j]) > depthJump;
        if (!hit) hit = parts[a] !== parts[b];
        if (!hit) hit = N[a * 3] * N[b * 3] + N[a * 3 + 1] * N[b * 3 + 1] + N[a * 3 + 2] * N[b * 3 + 2] < creaseCos;
        if (hit) { edge[i] = 1; edge[j] = 1; }
      }
    }
  }

  // цвет пикселя и усреднение SS×SS → итоговая картинка
  const edgeColor = color.map((c) => c * 0.18 + 30 * 0.82);
  const rgb = new Uint8Array(Wf * Hf * 3);
  const range = maxD - minD || 1;
  for (let y = 0; y < Hf; y++) {
    for (let x = 0; x < Wf; x++) {
      const acc = [0, 0, 0];
      for (let sy = 0; sy < SS; sy++) {
        for (let sx = 0; sx < SS; sx++) {
          const i = (y * SS + sy) * W + (x * SS + sx);
          let c;
          if (edge[i]) c = edgeColor;
          else if (tid[i] < 0) c = BG;
          else {
            const t = tid[i];
            const k = shade[t] * (1 - view.depthShade * ((zbuf[i] - minD) / range));
            c = [C[t * 3] * k, C[t * 3 + 1] * k, C[t * 3 + 2] * k];
          }
          acc[0] += c[0]; acc[1] += c[1]; acc[2] += c[2];
        }
      }
      const o = (y * Wf + x) * 3;
      for (let k = 0; k < 3; k++) rgb[o + k] = Math.round(Math.min(255, acc[k] / (SS * SS)));
    }
  }
  return { png: encodePng(rgb, Wf, Hf), w: Wf, h: Hf, pad: padF };
}

// ---------- png ----------

const CRC_TABLE = (() => {
  const t = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    t[n] = c >>> 0;
  }
  return t;
})();

function crc32(buf) {
  let c = 0xffffffff;
  for (const b of buf) c = CRC_TABLE[(c ^ b) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}

function chunk(type, data) {
  const len = Buffer.alloc(4);
  len.writeUInt32BE(data.length);
  const body = Buffer.concat([Buffer.from(type, 'ascii'), data]);
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(body));
  return Buffer.concat([len, body, crc]);
}

function encodePng(rgb, w, h) {
  const raw = Buffer.alloc((w * 3 + 1) * h);
  for (let y = 0; y < h; y++) raw.set(rgb.subarray(y * w * 3, (y + 1) * w * 3), y * (w * 3 + 1) + 1);
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(w, 0);
  ihdr.writeUInt32BE(h, 4);
  ihdr[8] = 8; ihdr[9] = 2; // 8 бит, RGB
  return Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    chunk('IHDR', ihdr),
    chunk('IDAT', zlib.deflateSync(raw, { level: 9 })),
    chunk('IEND', Buffer.alloc(0)),
  ]);
}

// ---------- svg с размерами ----------

const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const mm = (v) => `${v.toFixed(1)} мм`;

function arrow(x, y, dx, dy) {
  const L = 9, Wd = 3.2;
  return `<polygon points="${x},${y} ${x - dx * L + dy * Wd},${y - dy * L - dx * Wd} ${x - dx * L - dy * Wd},${y - dy * L + dx * Wd}" fill="${INK}"/>`;
}

function image(img, x, y) {
  return `<image x="${x}" y="${y}" width="${img.w}" height="${img.h}" href="data:image/png;base64,${img.png.toString('base64')}"/>`;
}

function titleText(name, viewTitle) {
  return `<text x="24" y="30" font-family="${FONT}" font-size="17" font-weight="600" fill="${INK}">${esc(name ? `${name} · ${viewTitle.toLowerCase()}` : viewTitle)}</text>`;
}

function orthoSvg(img, name, viewTitle, hValue, vValue) {
  const ml = 24, mt = 48, mr = 96, mb = 72;
  const W = Math.max(ml + img.w + mr, 420), H = mt + img.h + mb;
  const x0 = ml + img.pad, x1 = ml + img.w - img.pad;
  const y0 = mt + img.pad, y1 = mt + img.h - img.pad;
  const hy = y1 + 38, vx = x1 + 38;
  const line = (ax, ay, bx, by, w = 1) => `<line x1="${ax}" y1="${ay}" x2="${bx}" y2="${by}" stroke="${INK}" stroke-width="${w}"/>`;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
<rect width="100%" height="100%" fill="#fff"/>
${titleText(name, viewTitle)}
${image(img, ml, mt)}
${line(x0, y1 + 6, x0, hy + 7, 0.8)}${line(x1, y1 + 6, x1, hy + 7, 0.8)}${line(x0, hy, x1, hy, 1.2)}
${arrow(x0, hy, -1, 0)}${arrow(x1, hy, 1, 0)}
<text x="${(x0 + x1) / 2}" y="${hy - 7}" text-anchor="middle" font-family="${FONT}" font-size="15" fill="${INK}">${mm(hValue)}</text>
${line(x1 + 6, y0, vx + 7, y0, 0.8)}${line(x1 + 6, y1, vx + 7, y1, 0.8)}${line(vx, y0, vx, y1, 1.2)}
${arrow(vx, y0, 0, -1)}${arrow(vx, y1, 0, 1)}
<text transform="translate(${vx + 20} ${(y0 + y1) / 2}) rotate(-90)" text-anchor="middle" font-family="${FONT}" font-size="15" fill="${INK}">${mm(vValue)}</text>
</svg>`;
}

function isoSvg(img, name, viewTitle, caption) {
  const ml = 24, mt = 48, mb = 48;
  const W = Math.max(ml * 2 + img.w, 420), H = mt + img.h + mb;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
<rect width="100%" height="100%" fill="#fff"/>
${titleText(name, viewTitle)}
${image(img, ml, mt)}
<text x="${W / 2}" y="${mt + img.h + 30}" text-anchor="middle" font-family="${FONT}" font-size="15" fill="${INK}">${esc(caption)}</text>
</svg>`;
}

function svgToPng(svg) {
  return new Resvg(svg, { font: { loadSystemFonts: true, defaultFontFamily: 'Segoe UI' } }).render().asPng();
}

// ---------- запуск ----------

const FLAGS = new Set(['filled']);   // опции без значения

function parseArgs(argv) {
  const pos = [], opt = {};
  for (let i = 0; i < argv.length; i++) {
    if (!argv[i].startsWith('--')) pos.push(argv[i]);
    else if (FLAGS.has(argv[i].slice(2))) opt[argv[i].slice(2)] = true;
    else opt[argv[i].slice(2)] = argv[++i];
  }
  return { pos, opt };
}

function parseColor(hex) {
  return parseHexColor(hex) ?? [185, 194, 204];
}

// общий вид: масштаб подбирается по проекции модели на экран камеры
function renderIso(scene, color, view = VIEWS.iso) {
  const { r, u } = view.cam;
  const { tris } = scene;
  let a = Infinity, b = -Infinity, c = Infinity, d = -Infinity;
  for (let i = 0; i < tris.length; i += 3) {
    const p = [tris[i], tris[i + 1], tris[i + 2]];
    const x = dot(p, r), y = dot(p, u);
    a = Math.min(a, x); b = Math.max(b, x); c = Math.min(c, y); d = Math.max(d, y);
  }
  return render(scene, view, Math.min(ISO_PX / (b - a), (ISO_PX * 0.8) / (d - c)), color);
}

const { pos, opt } = parseArgs(process.argv.slice(2));
if (pos.length < 2) {
  console.error('Использование: node tools/render-3mf.mjs <модель.3mf> <папка_для_картинок> [--name "Название"] [--color "#RRGGBB"] [--filled]');
  process.exit(1);
}
const [input, outDir] = pos;
const name = opt.name ?? '';
const color = parseColor(opt.color);

const zip = readZip(fs.readFileSync(input));
const scene = loadTriangles(zip);
const { tris, items } = scene;
if (!tris.length) throw new Error('в 3mf нет треугольников');
const box = bounds(tris);
fs.mkdirSync(outDir, { recursive: true });

if (opt.filled) {
  // сцена с содержимым: только общий вид, габариты не подписываем — в сцене не только сама модель
  const img = renderIso(scene, color, VIEWS.filled);
  const caption = 'Содержимое показано условно — печатается только сама модель';
  fs.writeFileSync(path.join(outDir, 'filled.png'), svgToPng(isoSvg(img, name, VIEWS.filled.title, caption)));
  console.log(`Деталей в сцене: ${new Set(scene.parts).size}, треугольников: ${tris.length / 9}`);
  console.log(`Картинка: ${path.resolve(outDir, 'filled.png')}`);
} else {
  const scale = ORTHO_PX / Math.max(...box.size);
  const views = [
    ['front', box.size[0], box.size[2]],
    ['left', box.size[1], box.size[2]],
    ['right', box.size[1], box.size[2]],
    ['top', box.size[0], box.size[1]],
  ];
  for (const [key, h, v] of views) {
    const img = render(scene, VIEWS[key], scale, color);
    fs.writeFileSync(path.join(outDir, `${key}.png`), svgToPng(orthoSvg(img, name, VIEWS[key].title, h, v)));
  }
  const caption = `Габариты: ${box.size.map((v) => v.toFixed(1)).join(' × ')} мм (ширина × глубина × высота)`;
  fs.writeFileSync(path.join(outDir, 'iso.png'), svgToPng(isoSvg(renderIso(scene, color), name, VIEWS.iso.title, caption)));

  const thumb = thumbnail(zip);
  if (thumb) fs.writeFileSync(path.join(outDir, 'preview.png'), thumb);

  console.log(`Объектов в сборке: ${items}, треугольников: ${tris.length / 9}`);
  console.log(`Габариты: ${box.size.map((v) => v.toFixed(1)).join(' × ')} мм`);
  console.log(`Объём тела: ${(volume(tris) / 1000).toFixed(1)} см³`);
  console.log(`Миниатюра из 3mf: ${thumb ? 'есть → preview.png' : 'нет'}`);
  console.log(`Картинки: ${path.resolve(outDir)}`);
}
