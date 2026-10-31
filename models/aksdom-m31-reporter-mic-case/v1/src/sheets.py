# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "manifold3d", "matplotlib", "fonttools", "pyvista", "pillow"]
# ///
"""Листы эскиза кейса-микрофона: форма, размеры, варианты цветов. Рендер через VTK, подписи шрифтом Segoe UI (Windows).

uv run sheets.py form sizes colors                    -> все листы в ../img
uv run sheets.py colors --top слово --bottom слово --out папка   -> другая надпись, картинки в другую папку
Без uv: pip install numpy manifold3d matplotlib fonttools pyvista pillow, дальше python вместо uv run.
"""
import argparse
import math
from pathlib import Path

import numpy as np
import pyvista as pv
from PIL import Image, ImageDraw, ImageFont

import lettering
import mic_case as D

HERE = Path(__file__).parent
SKETCH = HERE.parent / 'ref' / 'sketch.png'
INK = '#22262B'
MUTED = '#6B7280'
ACC = '#C2410C'
FONT_R = 'C:/Windows/Fonts/segoeui.ttf'
FONT_B = 'C:/Windows/Fonts/segoeuib.ttf'

pv.OFF_SCREEN = True
pv.global_theme.multi_samples = 0

# Материалы: цвет и характер поверхности. Шёлк блестит, обычный пластик матовый.
MAT = {
    'white':  dict(color='#F1EEE7', metallic=0.0, roughness=0.50),
    'yellow': dict(color='#F7B516', metallic=0.18, roughness=0.34),
    'black':  dict(color='#1B1C20', metallic=0.0, roughness=0.42),
    'blue':   dict(color='#2536A8', metallic=0.0, roughness=0.42),
    'red':    dict(color='#D3142A', metallic=0.0, roughness=0.42),
    'teal':   dict(color='#12A69A', metallic=0.2, roughness=0.32),
    'pastel': dict(color='#E9B9C9', metallic=0.1, roughness=0.42, gradient=True),
    'cut_box': dict(color='#DDE3E9', metallic=0.0, roughness=0.6),
    'cap_box': dict(color='#6F8498', metallic=0.0, roughness=0.7),
    'accent': dict(color='#E0531A', metallic=0.0, roughness=0.6),
    'flat_yellow': dict(color='#EDB230', metallic=0.0, roughness=0.5),
    'tx':     dict(color='#17181B', metallic=0.1, roughness=0.32),
    'grille': dict(color='#9EA1A6', metallic=0.7, roughness=0.35),
}
ENV = None
CACHE = {}


def font(sz, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT_R, sz)


def env_texture():
    """Простая студия: светлый купол, мягкие боксы сверху и сбоку."""
    h, w = 256, 512
    v, u = np.mgrid[0:h, 0:w]
    lat = (0.5 - v / h) * math.pi
    lon = (u / w - 0.5) * 2 * math.pi
    img = np.ones((h, w, 3)) * (0.30 + 0.16 * np.sin(lat))[..., None]

    def box(lon0, lat0, dlon, dlat, gain):
        d = np.exp(-(((lon - lon0) / dlon) ** 4 + ((lat - lat0) / dlat) ** 4))
        return d[..., None] * gain
    img = np.clip(img + box(-1.0, 0.9, 0.9, 0.35, 0.8) + box(1.9, 0.4, 0.5, 0.6, 0.5), 0, 1)
    return pv.numpy_to_texture((img * 255).astype(np.uint8))


def linear(hexcol):
    """VTK в PBR считает цвет линейным, поэтому sRGB переводим сами, иначе чёрный выходит серым."""
    c = np.array([int(hexcol[i:i + 2], 16) for i in (1, 3, 5)]) / 255.0
    return tuple(np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4))


def to_pv(m):
    v, f = D.to_mesh(m)
    faces = np.hstack([np.full((len(f), 1), 3, dtype=np.int64), f]).ravel()
    return pv.PolyData(v, faces)


def pastel_scalars(p):
    """Пастельная нить меняет цвет вдоль высоты. Условно: настоящая нить идёт в своём ритме."""
    z = p.points[:, 2]
    t = (z - z.min()) / max(1e-6, z.max() - z.min())
    stops = np.array([[0.58, 0.80, 0.86], [0.78, 0.88, 0.76], [0.97, 0.86, 0.68], [0.95, 0.74, 0.74], [0.82, 0.68, 0.88]])
    i = np.clip(t * (len(stops) - 1), 0, len(stops) - 1 - 1e-6)
    a = i.astype(int)
    f = (i - a)[:, None]
    return stops[a] * (1 - f) + stops[a + 1] * f


def render(items, cam, size=(900, 1400), ss=2, parallel=False, section=False):
    """items: [(PolyData, имя материала, dict доп. опций)]"""
    global ENV
    W, H = size
    pl = pv.Plotter(off_screen=True, window_size=(W * ss, H * ss), lighting='none')
    pl.set_background('#FFFFFF')
    if ENV is None:
        ENV = env_texture()
    pl.set_environment_texture(ENV)
    for pd, mat, opt in items:
        M = dict(MAT[mat])
        grad = M.pop('gradient', False)
        kw = dict(pbr=True, smooth_shading=True, split_sharp_edges=True, feature_angle=28, show_scalar_bar=False)
        kw.update(metallic=M['metallic'], roughness=M['roughness'], diffuse=1.0)
        kw.update(opt)
        if grad:
            pd = pd.copy()
            pd.point_data['rgb'] = (pastel_scalars(pd) * 255).astype(np.uint8)
            pl.add_mesh(pd, scalars='rgb', rgb=True, **kw)
        else:
            pl.add_mesh(pd, color=linear(M['color']), **kw)
    c = pl.camera
    c.position, c.focal_point, c.up = cam['pos'], cam['foc'], cam.get('up', (0, 0, 1))
    if parallel:
        pl.enable_parallel_projection()
        c.parallel_scale = cam['scale']
    else:
        c.view_angle = cam.get('fov', 16)
    d = float(np.linalg.norm(np.array(cam['pos']) - np.array(cam['foc'])))
    c.clipping_range = (d - 260, d + 260)
    key = pv.Light(position=(-300, -500, 700), focal_point=cam['foc'], intensity=3.4, positional=False)
    fill = pv.Light(position=(600, -300, 100), focal_point=cam['foc'], intensity=1.1, positional=False)
    rim = pv.Light(position=(100, 600, 300), focal_point=cam['foc'], intensity=1.2, positional=False)
    if section:
        # срез смотрит на +X, основной свет ставим со стороны камеры
        key = pv.Light(position=(700, -250, 450), focal_point=cam['foc'], intensity=1.7, positional=False)
        fill = pv.Light(position=(600, 350, -200), focal_point=cam['foc'], intensity=0.5, positional=False)
    for l in (key, fill, rim):
        pl.add_light(l)
    pl.enable_ssao(radius=6, bias=2.5, kernel_size=128, blur=True)
    pl.enable_anti_aliasing('ssaa')
    img = pl.screenshot(return_img=True)
    pl.close()
    im = Image.fromarray(img)
    return im.resize((W, H), Image.LANCZOS) if ss != 1 else im


def cam_orbit(foc, dist, az, el, **kw):
    a, e = math.radians(az), math.radians(el)
    pos = (foc[0] + dist * math.sin(a) * math.cos(e), foc[1] - dist * math.cos(a) * math.cos(e), foc[2] + dist * math.sin(e))
    return dict(pos=pos, foc=foc, **kw)


def get(kind):
    if kind not in CACHE:
        CACHE[kind] = D.build(kind)
    return CACHE[kind]


def items(kind, sc, tx=False):
    out = []
    for k, m in get(kind).items():
        is_tx = k.startswith('tx')
        if is_tx and not tx:
            continue
        mat = 'grille' if k == 'tx_grille' else ('tx' if is_tx else sc[k])
        out.append((to_pv(m), mat, dict(smooth_shading=False, split_sharp_edges=False) if k == 'letters' else {}))
    return out


def trim_white(im, pad=8):
    a = np.asarray(im.convert('L'))
    ys, xs = np.where(a < 250)
    return im.crop((max(0, xs.min() - pad), max(0, ys.min() - pad), min(im.width, xs.max() + pad), min(im.height, ys.max() + pad)))


def paste_center(sheet, im, box):
    x0, y0, x1, y1 = box
    k = min((x1 - x0) / im.width, (y1 - y0) / im.height, 1.0)
    if k < 1:
        im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    sheet.paste(im, (x0 + (x1 - x0 - im.width) // 2, y0 + (y1 - y0 - im.height) // 2))


def wrap(draw, text, fnt, width):
    lines = []
    for para in text.split('\n'):
        cur = ''
        for w in para.split(' '):
            t = (cur + ' ' + w).strip()
            if draw.textlength(t, font=fnt) <= width:
                cur = t
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def block(draw, xy, text, fnt, width, fill=INK, gap=8):
    x, y = xy
    for ln in wrap(draw, text, fnt, width):
        draw.text((x, y), ln, font=fnt, fill=fill)
        y += fnt.size + gap
    return y


def poly_area(p):
    return abs(np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1]))


def overlay_image(scale=3):
    """Контур модели красным поверх рисунка в одном масштабе."""
    im = Image.open(SKETCH).convert('RGBA')
    bg = Image.new('RGBA', im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    bg = bg.convert('RGB').resize((im.width * scale, im.height * scale), Image.BICUBIC)
    dr = ImageDraw.Draw(bg)
    cx, by = 229.5, 495.5
    px = lambda x, z: ((cx + x / D.K) * scale, (by - z / D.K) * scale)
    col = (214, 40, 40)

    def stroke(polys, width=2):
        for p in polys:
            p = np.asarray(p)
            dr.line([px(x, z) for x, z in np.vstack([p, p[:1]])], fill=col, width=width)
    parts = get('flat')
    visible = [parts['box'], parts['head'].trim_by_plane([0, 0, 1], D.BOX_H), parts['handle'].trim_by_plane([0, 0, -1], 0.0)]
    for m in visible:
        polys = [np.asarray(p) for p in m.rotate([-90, 0, 0]).project().to_polygons()]
        big = max(poly_area(q) for q in polys)
        stroke([p for p in polys if poly_area(p) > 0.1 * big])
    stroke(D.rrect(D.BOX_W, D.BOX_H, D.BOX_R).translate([0, D.BOX_H / 2]).to_polygons())
    stroke(D.rrect(D.PANEL_W, D.PANEL_H, D.PANEL_R).translate([0, D.PANEL_Z]).to_polygons())
    return bg


SCH = dict(head='black', box='white', handle='black', letters='red')


def hero(kind, sc=SCH, size=(600, 860)):
    return render(items(kind, sc), cam_orbit((0, 0, 27), 1050, 22, 9, fov=12.6), size=size)


def plan_view(kind):
    """Вид сверху контуром: так глубина крыльев читается лучше, чем на рендере."""
    S = 5.0
    W, H = 460, 240
    im = Image.new('RGB', (W, H), 'white')
    dr = ImageDraw.Draw(im)
    polys = [np.asarray(q) for q in get(kind)['box'].project().to_polygons()]
    big = max(polys, key=len)
    pts = [(W / 2 + p[0] * S, H / 2 - p[1] * S) for p in big]
    dr.polygon(pts, fill='#E7EAEE', outline=INK)
    dr.line(pts + pts[:1], fill=INK, width=2)
    r = D.NECK_D / 2 * S
    dr.ellipse([W / 2 - r, H / 2 - r, W / 2 + r, H / 2 + r], outline='#9AA0A6', width=2)
    return im


def sheet_form(out):
    W, H = 2100, 1640
    sh = Image.new('RGB', (W, H), 'white')
    dr = ImageDraw.Draw(sh)
    dr.text((60, 36), 'Бокс по рисунку', font=font(54, True), fill=INK)
    dr.text((60, 106), 'Спереди модель повторяет рисунок. Глубины на рисунке нет: разобраны три варианта крыльев, выбран третий.', font=font(27), fill=MUTED)
    ov = overlay_image(3)
    ov = ov.crop((150, 40, ov.width - 60, ov.height - 20))
    dr.text((60, 170), 'Сверка с рисунком', font=font(32, True), fill=INK)
    block(dr, (60, 214), 'Красный контур модели поверх рисунка, масштаб один. Шар стоит по оси: на рисунке он сдвинут на 2 мм влево.', font(24), 540, fill=MUTED, gap=5)
    paste_center(sh, ov, (60, 330, 620, 1600))
    cols = [(680, 'flat', '1. Тонкие, 12 мм', 'Лёгкий вид, но кончики тонкие. Спереди как на рисунке, сбоку это плоские пластины.'),
            (1150, 'full', '2. Почти на всю глубину, 37 мм', 'Самые прочные кончики, форма проще всего.'),
            (1620, 'taper', '3. Сходятся к кончикам', 'Выбрано. Самая скульптурная форма. Кончик 4 мм, его можно сколоть при падении.')]
    for cx, kind, title, txt in cols:
        block(dr, (cx, 170), title, font(28, True), 440, fill=ACC if kind == 'taper' else INK, gap=4)
        paste_center(sh, trim_white(hero(kind)), (cx, 240, cx + 440, 1090))
        dr.text((cx, 1110), 'вид сверху', font=font(23), fill=MUTED)
        paste_center(sh, plan_view(kind), (cx, 1140, cx + 440, 1380))
        block(dr, (cx, 1396), txt, font(24), 440, gap=6)
    sh.save(out / 'design-form.png')
    print('лист форма', flush=True)


def dim_v(dr, x, y0, y1, label, side=1, ext0=None, ext1=None, fnt=None):
    fnt = fnt or font(25)
    dr.line([(x, y0), (x, y1)], fill=INK, width=2)
    for y, d in ((y0, 1), (y1, -1)):
        dr.polygon([(x, y), (x - 6, y + d * 13), (x + 6, y + d * 13)], fill=INK)
    for yy, e in ((y0, ext0), (y1, ext1)):
        if e is not None:
            dr.line([(e, yy), (x + 8 * (1 if x > e else -1), yy)], fill='#9AA0A6', width=1)
    tw = dr.textlength(label, font=fnt)
    dr.text((x + 12 if side > 0 else x - 12 - tw, (y0 + y1) / 2 - fnt.size * 0.65), label, font=fnt, fill=INK)


def dim_h(dr, y, x0, x1, label, side=-1, fnt=None):
    fnt = fnt or font(25)
    dr.line([(x0, y), (x1, y)], fill=INK, width=2)
    for x, d in ((x0, 1), (x1, -1)):
        dr.polygon([(x, y), (x + d * 13, y - 6), (x + d * 13, y + 6)], fill=INK)
    tw = dr.textlength(label, font=fnt)
    dr.text(((x0 + x1 - tw) / 2, y - fnt.size - 12 if side < 0 else y + 8), label, font=fnt, fill=INK)


def split_caps(pd):
    """Отделяет грани среза (нормаль строго +X в плоскости X = 0) от остальной поверхности."""
    n = pd.compute_normals(cell_normals=True, point_normals=False, auto_orient_normals=False, consistent_normals=False)
    nx = n.cell_data['Normals'][:, 0]
    cx = pd.cell_centers().points[:, 0]
    mask = (nx > 0.999) & (np.abs(cx) < 1e-3)
    return pd.extract_cells(np.where(mask)[0]).extract_surface(), pd.extract_cells(np.where(~mask)[0]).extract_surface()


def section_items(kind):
    mp = dict(head='black', box='cut_box', handle='flat_yellow', letters='red')
    out = []
    for k, m in get(kind).items():
        cut = m.trim_by_plane([-1, 0, 0], 0.0)
        if cut.is_empty():
            continue
        mat = 'grille' if k == 'tx_grille' else ('tx' if k.startswith('tx') else mp[k])
        pd = to_pv(cut)
        if k == 'box':
            cap, rest = split_caps(pd)
            out.append((rest, mat, {}))
            if cap.n_cells:
                out.append((cap, 'cap_box', {}))
        else:
            out.append((pd, mat, {}))
    out.append((to_pv(D.blade().trim_by_plane([-1, 0, 0], 0.0)), 'accent', {}))
    return out


def callout(dr, target, xy, text, width, fnt=None):
    fnt = fnt or font(23)
    x, y = xy
    dr.line([target, (x - 8, y + 14)], fill=ACC, width=2)
    r = 5
    dr.ellipse([target[0] - r, target[1] - r, target[0] + r, target[1] + r], fill=ACC)
    for i, ln in enumerate(wrap(dr, text, fnt, width)):
        dr.text((x, y + i * (fnt.size + 5)), ln, font=fnt, fill=INK)


def sheet_sizes(out, kind='taper'):
    W, H = 2100, 1520
    sh = Image.new('RGB', (W, H), 'white')
    dr = ImageDraw.Draw(sh)
    dr.text((60, 36), 'Размеры, стыки и надпись', font=font(54, True), fill=INK)
    dr.text((60, 106), 'Эскиз, не для печати. Передатчик пока по оценке с фото: 55 × 17 × 12 мм, с прищепкой 17 мм.', font=font(27), fill=MUTED)
    top = D.BALL_CZ + D.BALL_D / 2
    zc = (top - D.HANDLE_L) / 2
    IW, IH = 560, 1250
    scale = 122.0
    k = IH / (2 * scale)
    im = render(items(kind, SCH), dict(pos=(0, -800, zc), foc=(0, 0, zc), scale=scale), size=(IW, IH), parallel=True)
    ox, oy = 90, 190
    sh.paste(im, (ox, oy))
    px = lambda x: ox + IW / 2 + x * k
    pz = lambda z: oy + IH / 2 - (z - zc) * k
    total = top + D.HANDLE_L
    dim_h(dr, pz(top) - 22, px(-D.BALL_D / 2), px(D.BALL_D / 2), 'Ø52')
    dim_h(dr, pz(-5), px(-41.0), px(41.0), '')
    dr.text((px(17), pz(-5) + 6), '82', font=font(25), fill=INK)
    dim_v(dr, 650, pz(top), pz(-D.HANDLE_L), f'{total:.0f}', side=1, ext0=px(10), ext1=px(10))
    dim_v(dr, 76, pz(D.BOX_H), pz(0), '82', side=-1, ext0=px(-41.0), ext1=px(-41.0))
    dim_v(dr, px(-30), pz(0), pz(-D.HANDLE_L), '78', side=-1, ext1=px(-14))
    dr.line([(px(-14.3), pz(-20)), (px(14.3), pz(-20))], fill='#FFFFFF', width=2)
    dr.text((px(17), pz(-20) - 16), 'Ø30', font=font(25), fill=INK)
    dr.line([(px(-12.6), pz(-70)), (px(12.6), pz(-70))], fill='#FFFFFF', width=2)
    dr.text((px(15), pz(-70) - 16), 'Ø25', font=font(25), fill=INK)
    dim_h(dr, pz(77), px(-D.BOX_W / 2), px(D.BOX_W / 2), '')
    dr.text((px(0) - 14, pz(77) + 5), '56', font=font(25), fill=INK)

    SW, SH = 560, 1250
    im = render(section_items(kind), dict(pos=(800, 0, zc), foc=(0, 0, zc), scale=scale), size=(SW, SH), parallel=True, section=True)
    ox2 = 730
    sh.paste(im, (ox2, oy))
    py = lambda y: ox2 + SW / 2 + y * k
    dim_h(dr, pz(0) + 30, py(-D.BOX_D / 2), py(D.BOX_D / 2), 'глубина 44', side=1)
    ft = font(22)
    callout(dr, (py(1), pz(107)), (1310, 190), 'Шар пустой, отверстия сквозные, звук доходит до решётки передатчика.', 330, ft)
    callout(dr, (py(-16), pz(75)), (1310, 300), 'Голова: три лапки, поворот, щелчок.', 330, ft)
    callout(dr, (py(D.TX_Y + 3), pz(62)), (1310, 380), 'Передатчик вставляется сверху в колодец с запасом 1 мм со всех сторон. Верх торчит из бокса на 8 мм, за него удобно взять.', 330, ft)
    callout(dr, (py(D.TX_Y - D.TX_T / 2 - 1.6), pz(44)), (1310, 540), 'Оранжевая пластина: на неё садится родная прищепка, чтобы передатчик не стучал.', 330, ft)
    callout(dr, (py(3), pz(27)), (1310, 640), 'Дно колодца: подгоним под настоящую длину передатчика.', 330, ft)
    callout(dr, (py(8), pz(10)), (1310, 730), 'Ручка: тоже три лапки и щелчок. Хвостовик Ø25 × 20 мм глубоко в боксе держит рычаг. Пандус под лапками и язычок щелчка ещё не нарисованы.', 330, ft)

    bx = 1690
    dr.text((bx, 190), 'Надпись', font=font(32, True), fill=ACC)
    p = get(kind)
    its = [(to_pv(p['box']), 'white', {}), (to_pv(p['letters'].translate([0, -16, 0])), 'red', dict(smooth_shading=False, split_sharp_edges=False))]
    im = render(its, cam_orbit((0, -8, 45), 620, 30, 8, fov=5.6), size=(390, 390))
    paste_center(sh, im, (bx - 10, 236, bx + 380, 626))
    n, th = lettering.stats(*D.TEXT)
    thin = f'{th:.1f}'.replace('.', ',')
    txt = (f'Надпись с двух сторон. Шрифт Satisfy, слегка утолщён, верхнее слово крупнее в 1,5 раза.\nКаждое слово одна деталь: буквы связаны, точки присоединены. Всего деталей {2 * n}.\nСамое тонкое место {thin} мм.\n'
           'Толщина 3 мм: половина в выемке, половина снаружи, клеится на космофен.\nВыемка повторяет внешний контур слова с зазором 0,15 мм на сторону.')
    block(dr, (bx, 640), txt, font(23), 370, gap=6)
    sh.save(out / 'design-sizes.png')
    print('лист размеры', flush=True)


K, Wh, Yl, Bl, Rd, Tl, Pa = 'black', 'white', 'yellow', 'blue', 'red', 'teal', 'pastel'
COMBOS = [
    ('Белый бокс', [(K, Wh, K, Rd), (K, Wh, K, Bl), (Wh, Wh, Yl, Yl), (Tl, Wh, Tl, Tl), (Rd, Wh, Rd, Rd), (Bl, Wh, Bl, Bl)]),
    ('Чёрный бокс', [(K, K, K, Yl), (Yl, K, Yl, Yl), (Wh, K, Wh, Wh), (Rd, K, Rd, Rd), (Tl, K, Tl, Tl), (Bl, K, Bl, Wh)]),
    ('Красный бокс', [(K, Rd, K, Wh), (K, Rd, K, Yl), (Wh, Rd, Wh, Wh), (Wh, Rd, K, Wh), (Yl, Rd, K, Yl), (Bl, Rd, Bl, Wh)]),
    ('Синий бокс', [(Wh, Bl, Wh, Wh), (Wh, Bl, Wh, Yl), (K, Bl, K, Wh), (Yl, Bl, Yl, Yl), (Rd, Bl, Rd, Wh), (Tl, Bl, Tl, Wh)]),
    ('Жёлтый шёлковый бокс', [(K, Yl, K, K), (Wh, Yl, Wh, K), (Bl, Yl, Bl, Bl), (Rd, Yl, Rd, Rd), (K, Yl, K, Rd), (Tl, Yl, Tl, Tl)]),
    ('Сине-зелёный шёлковый бокс', [(K, Tl, K, Wh), (Wh, Tl, Wh, Wh), (Yl, Tl, Yl, Yl), (K, Tl, K, Yl), (Wh, Tl, K, Wh), (Bl, Tl, Bl, Wh)]),
    ('Пастельный бокс', [(Wh, Pa, Wh, K), (Wh, Pa, Wh, Bl), (K, Pa, K, K), (K, Pa, K, Wh), (Rd, Pa, Rd, Rd), (Tl, Pa, Tl, Tl)]),
    ('Смелые сочетания', [(Pa, Wh, Pa, K), (Pa, K, Pa, Wh), (Pa, Bl, Pa, Wh), (Pa, Rd, Pa, Wh), (Rd, Yl, Bl, K), (Tl, Rd, Yl, Wh)]),
]


def swatches(dr, x, y, cols):
    s = 24
    for i, c in enumerate(cols):
        x0 = x + i * (s + 5)
        if c == 'pastel':
            dr.rectangle([x0, y, x0 + s, y + s / 2], fill='#E9B9C9')
            dr.rectangle([x0, y + s / 2, x0 + s, y + s], fill='#9CCFD6')
        else:
            dr.rectangle([x0, y, x0 + s, y + s], fill=MAT[c]['color'])
        dr.rectangle([x0, y, x0 + s, y + s], outline='#8A8F98', width=1)


def sheet_colors(rows, first, path, title):
    cols = 6
    cw, ch = 338, 600
    rh = ch + 104
    sh = Image.new('RGB', (2100, 190 + rh * len(rows) + 20), 'white')
    dr = ImageDraw.Draw(sh)
    dr.text((40, 30), title, font=font(50, True), fill=INK)
    dr.text((40, 96), 'Под каждым вариантом номер и четыре цвета: голова, бокс, ручка, надпись. Цвета по фото катушек, вживую будут другими.', font=font(26), fill=MUTED)
    n = first
    for r, (label, combos) in enumerate(rows):
        y0 = 150 + r * rh
        dr.text((40, y0), label, font=font(29, True), fill=ACC)
        for c, cc in enumerate(combos):
            cx = 40 + c * (cw + 3)
            sc = dict(head=cc[0], box=cc[1], handle=cc[2], letters=cc[3])
            im = hero('taper', sc, size=(430, 650))
            paste_center(sh, trim_white(im), (cx, y0 + 42, cx + cw, y0 + 42 + ch))
            dr.text((cx + 70, y0 + 48 + ch), f'{n}', font=font(28, True), fill=INK)
            swatches(dr, cx + 122, y0 + 54 + ch, cc)
            n += 1
        print('ряд', label, flush=True)
    sh.save(path)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('sheets', nargs='+', choices=['form', 'sizes', 'colors'])
    ap.add_argument('--top', default=D.TEXT[0])
    ap.add_argument('--bottom', default=D.TEXT[1])
    ap.add_argument('--out', default=str(HERE.parent / 'img'))
    args = ap.parse_args()
    D.TEXT = (args.top, args.bottom)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if 'form' in args.sheets:
        sheet_form(out)
    if 'sizes' in args.sheets:
        sheet_sizes(out)
    if 'colors' in args.sheets:
        sheet_colors(COMBOS[:3], 1, out / 'colors-1.png', 'Цвета, часть 1')
        sheet_colors(COMBOS[3:6], 19, out / 'colors-2.png', 'Цвета, часть 2')
        sheet_colors(COMBOS[6:], 37, out / 'colors-3.png', 'Цвета, часть 3')
