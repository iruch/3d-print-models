# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "manifold3d", "matplotlib", "fonttools"]
# ///
"""Кейс-микрофон: геометрия эскиза. Файла для печати пока нет, модель в разработке.
Три детали и надпись: шар-голова, бокс с крыльями, ручка. Передатчик Aksdom M31 вставляется сверху.
Все размеры в мм. X — вправо, Y — от зрителя (перед = -Y), Z — вверх. Z = 0 — низ бокса.
Рисунок бокса: ref/sketch.png, масштаб шар Ø52 = 180 пикселей, то есть 0,289 мм на пиксель.

uv run mic_case.py      -> проверка: габариты деталей и пересечения в сборке
Без uv: pip install numpy manifold3d matplotlib fonttools, дальше python вместо uv run.
"""
import math
import numpy as np
import manifold3d as m3
from manifold3d import Manifold, CrossSection, FillRule, JoinType, OpType
import lettering

m3.set_circular_segments(72)

K = 52.0 / 180.0                     # мм на пиксель рисунка

# ---------- надпись: две строки, задаётся параметром ----------
TEXT = ('be', 'louder!')

# ---------- передатчик: оценка по фото покупателя, штангенциркулем не проверялось ----------
TX_L, TX_W, TX_T = 55.0, 17.0, 12.0
CLIP_T = 5.0
CLIP_L, CLIP_W = 36.0, 13.0
TX_SIDE = 0.9       # на сколько выступают кнопка и ползунок сбоку (оценка)
TX_GAP = 1.0        # запас вокруг передатчика со всех сторон: входит и вынимается свободно
TX_Y = CLIP_T / 2   # передатчик с прищепкой стоит по центру бокса

# ---------- бокс: снято с рисунка ----------
BOX_W = 56.0        # 195 пикселей
BOX_H = 82.0        # 284 пикселя
BOX_R = 8.5         # скругление углов по фронту
BOX_D = 44.0        # глубина: на рисунке её нет, выбрана под передатчик и посадку головы
EDGE_R = 3.0        # скругление рёбер по глубине
PANEL_W, PANEL_H = 47.7, 56.3    # панель под надпись
PANEL_R = 7.0
PANEL_Z = 45.4      # центр панели от низа бокса
PANEL_D = 1.2       # глубина панели, край со скосом 45°

TIP_X = 42.0        # кончик крыла от оси
APEX_X = 29.3       # самое узкое место крыла на половине высоты
ARC_R = 76.6        # радиус вогнутой дуги
EDGE_DIP = 0.9      # верх и низ крыла чуть проваливаются к боксу, как на рисунке
WING_TIP = 4.0      # толщина кончика крыла

# ---------- надпись на боксе ----------
LETTER_T = 3.0      # толщина
POCKET_D = 1.5      # половина в выемке, половина снаружи
POCKET_GAP = 0.15   # зазор выемки на сторону

# ---------- шар и ручка ----------
BALL_D = 52.0
NECK_D, NECK_H = 36.0, 4.3
BALL_CZ = BOX_H + 25.0
HANDLE_D, HANDLE_END_D, HANDLE_L = 30.0, 25.0, 78.0   # у бокса шире, к низу сужается

# ---------- байонеты: пандусы и язычки щелчка ещё не смоделированы ----------
TOP_BORE = 31.0     # отверстие под голову
TOP_THROAT = 27.0   # через него проходит передатчик
TOP_PLATE = 6.0     # толщина верхней плиты
SPIGOT_D = 25.2     # хвостовик ручки
SPIGOT_L = 20.0     # длинный, чтобы ручка не качалась
BOT_PLATE = 6.0
PEDESTAL_Z = 34.0   # дно колодца: верх передатчика на 8 мм выше бокса, за него можно взять пальцами


def rrect(w, h, r):
    return CrossSection.square([w - 2 * r, h - 2 * r], True).offset(r, JoinType.Round, 8, 24)


def revolve(profile):
    return CrossSection([profile], FillRule.EvenOdd).revolve(120)


def rotz(m, deg):
    return m.rotate([0, 0, deg])


def on_front(solid, x=0.0, z=0.0, y=0.0):
    """Плоскую заготовку (XY, толщина по +Z) ставит лицом к -Y: занимает от y до y - толщина."""
    return solid.rotate([90, 0, 0]).translate([x, y, z])


def rounded_box(w, d, h, r):
    pts = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            for z in (r, h - r):
                pts.append(Manifold.sphere(r, 32).translate([sx * (w / 2 - r), sy * (d / 2 - r), z]))
    return Manifold.batch_hull(pts)


def body():
    """Скруглённый прямоугольник по фронту с мягкими рёбрами по глубине."""
    layers = []
    n = 10
    for side in (-1, 1):
        for i in range(n + 1):
            a = i / n * math.pi / 2
            inset = EDGE_R * (1 - math.cos(a))
            yy = side * (BOX_D / 2 - EDGE_R + EDGE_R * math.sin(a))
            cs = rrect(BOX_W - 2 * inset, BOX_H - 2 * inset, max(BOX_R - inset, 0.5))
            layers.append(cs.extrude(0.01).rotate([90, 0, 0]).translate([0, yy, BOX_H / 2]))
    return Manifold.batch_hull(layers)


def wing_profile():
    """Контур крыльев в плоскости XZ: квадрат с вогнутыми боками, как на рисунке."""
    cx = APEX_X + ARC_R
    half = math.sqrt(ARC_R ** 2 - (cx - TIP_X) ** 2)
    pts = []
    n = 60
    a0 = math.asin(half / ARC_R)
    for i in range(n + 1):
        a = -a0 + 2 * a0 * i / n
        pts.append([cx - ARC_R * math.cos(a), BOX_H / 2 + ARC_R * math.sin(a)])
    m = 24
    for i in range(1, m):
        t = i / m
        pts.append([TIP_X * (1 - 2 * t), BOX_H - EDGE_DIP * math.sin(math.pi * t) ** 0.5])
    for i in range(n + 1):
        a = a0 - 2 * a0 * i / n
        pts.append([-cx + ARC_R * math.cos(a), BOX_H / 2 + ARC_R * math.sin(a)])
    for i in range(1, m):
        t = i / m
        pts.append([-TIP_X * (1 - 2 * t), EDGE_DIP * math.sin(math.pi * t) ** 0.5])
    cs = CrossSection([pts], FillRule.EvenOdd)
    return cs.offset(-0.9, JoinType.Round, 8, 24).offset(0.9, JoinType.Round, 8, 24)


def arc_cutter(T, f):
    """Вырез под вогнутую дугу со скруглёнными кромками."""
    prof = [[0, -T / 2 - 2], [ARC_R + f, -T / 2 - 2], [ARC_R + f, -T / 2]]
    for i in range(1, 13):
        a = i / 12 * math.pi / 2
        prof.append([ARC_R + f - f * math.sin(a), -T / 2 + f - f * math.cos(a)])
    for i in range(0, 13):
        a = (12 - i) / 12 * math.pi / 2
        prof.append([ARC_R + f - f * math.sin(a), T / 2 - f + f * math.cos(a)])
    prof += [[ARC_R + f, T / 2 + 2], [0, T / 2 + 2]]
    return CrossSection([prof], FillRule.EvenOdd).revolve(360)


def wings(kind):
    """kind: taper — сходятся к кончикам (выбрано), flat — пластина 12 мм, full — почти на всю глубину."""
    if kind == 'flat':
        T, f = 12.0, 2.5
    elif kind == 'full':
        T, f = 37.0, 3.0
    else:
        T, f = BOX_D - 1.0, 3.0
    prof = wing_profile().extrude(T).rotate([90, 0, 0]).translate([0, T / 2, 0])
    blk = rounded_box(2 * TIP_X + 4, T, BOX_H, 2.2)
    w = prof ^ blk
    cx = APEX_X + ARC_R
    for s in (-1, 1):
        cut = arc_cutter(T, f).rotate([90, 0, 0]).translate([s * cx, 0, BOX_H / 2])
        w = w - cut
    if kind == 'taper':
        # вид сверху: от боковой стенки бокса глубина сходится к кончику
        x0 = BOX_W / 2 - 2.0
        hd = BOX_D / 2 - 1.0
        pts = []
        n = 24
        for i in range(n + 1):
            t = i / n
            pts.append([x0 + (TIP_X + 1.5 - x0) * t, WING_TIP / 2 + (hd - WING_TIP / 2) * (1 - t) ** 1.6])
        for p in reversed(pts):
            pts.append([p[0], -p[1]])
        right = CrossSection([pts], FillRule.EvenOdd)
        left = right.mirror([1, 0])
        core = CrossSection.square([2 * x0 + 0.2, 2 * hd], True)
        plan = (right + left + core).extrude(BOX_H + 2).translate([0, 0, -1])
        w = w ^ plan
    return w


def text_lines():
    """Надпись: слова с окнами и контур без окон для выемки."""
    full, solid, _ = lettering.lines(TEXT[0], TEXT[1], PANEL_Z)
    return full, solid


def blade():
    """Пластина, на которую садится прищепка: с зазором передатчик иначе болтался бы и стучал в запись."""
    return Manifold.cube([15, 3.0, 20], True).translate([0, TX_Y - TX_T / 2 - 1.6, PEDESTAL_Z + 10])


def well():
    """Колодец под передатчик с зазором TX_GAP со всех сторон, сверху воронка к посадке головы."""
    x = TX_W / 2 + TX_SIDE + TX_GAP
    y = (TX_T + CLIP_T) / 2 + TX_GAP
    z0, z1, z2 = PEDESTAL_Z, BOX_H - TOP_PLATE - 16, BOX_H - TOP_PLATE - 4
    low = Manifold.cube([2 * x, 2 * y, z1 - z0]).translate([-x, -y, z0])
    base = Manifold.cube([2 * x, 2 * y, 0.2]).translate([-x, -y, z1 - 0.2])
    top = CrossSection.circle(18.5, 96).extrude(0.2).translate([0, 0, z2 - 0.2])
    return low + Manifold.batch_hull([base, top])


def top_socket():
    z = BOX_H
    bore = Manifold.cylinder(TOP_PLATE + 4, TOP_BORE / 2, TOP_BORE / 2, 96).translate([0, 0, z - TOP_PLATE - 2])
    notches = [rotz(Manifold.cube([7, 9.0, TOP_PLATE + 4], True).translate([TOP_BORE / 2 + 0.2, 0, z - TOP_PLATE / 2]), a + 30) for a in (0, 120, 240)]
    groove = Manifold.cylinder(4.0, 18.7, 18.7, 96).translate([0, 0, z - TOP_PLATE - 4.0])
    return bore + Manifold.batch_boolean(notches, OpType.Add) + groove


def bottom_socket():
    d = SPIGOT_D + 0.4
    bore = Manifold.cylinder(SPIGOT_L + 1.5, d / 2, d / 2, 96).translate([0, 0, -0.5])
    notches = [rotz(Manifold.cube([7, 8.5, BOT_PLATE + 4.5], True).translate([d / 2 + 0.2, 0, (BOT_PLATE + 4) / 2 - 0.2]), a + 30) for a in (0, 120, 240)]
    groove = Manifold.cylinder(4.0, 15.4, 15.4, 96).translate([0, 0, BOT_PLATE])
    return bore + Manifold.batch_boolean(notches, OpType.Add) + groove


def box(kind='taper'):
    full, solid = text_lines()
    b = body() + wings(kind)
    # панель со скосом: край на грани совпадает с рисунком, дно меньше на глубину
    inner = rrect(PANEL_W - 2 * PANEL_D, PANEL_H - 2 * PANEL_D, PANEL_R - PANEL_D).extrude(0.01)
    outer = rrect(PANEL_W + 1.0, PANEL_H + 1.0, PANEL_R + 0.5).extrude(0.01).translate([0, 0, PANEL_D + 0.5])
    pan = Manifold.batch_hull([inner, outer])
    front = on_front(pan, z=PANEL_Z, y=-BOX_D / 2 + PANEL_D)
    back = rotz(front, 180)
    b = b - front - back
    # выемка под надпись с двух сторон: внешний контур слова без внутренних окон, плюс зазор
    pocket = solid.offset(POCKET_GAP, JoinType.Round, 6, 18).extrude(POCKET_D + PANEL_D + 2)
    pocket = on_front(pocket, y=-BOX_D / 2 + PANEL_D + POCKET_D)
    b = b - pocket - rotz(pocket, 180)
    return b - well() - top_socket() - bottom_socket() + blade()


def letters():
    """Надпись спереди и сзади: сзади та же, развёрнута, чтобы читалась."""
    full, _ = text_lines()
    front = on_front(full.extrude(LETTER_T), y=-BOX_D / 2 + PANEL_D + POCKET_D)
    return front + rotz(front, 180)


def head():
    """Шар со сквозными отверстиями, шейка, юбка байонета с тремя лапками."""
    R = BALL_D / 2
    base_z = BOX_H
    cz = BALL_CZ
    shell = Manifold.sphere(R, 128).translate([0, 0, cz])
    inside = Manifold.sphere(R - 2.0, 96).translate([0, 0, cz])
    prof = [[0, base_z], [NECK_D / 2, base_z], [NECK_D / 2, base_z + NECK_H - 0.8], [NECK_D / 2 - 0.8, base_z + NECK_H], [15.0, base_z + NECK_H + 2], [0, base_z + NECK_H + 2]]
    neck = revolve(prof)
    band = Manifold.cylinder(4.0, R + 1.3, R + 1.3, 128).translate([0, 0, cz - 2.0])
    band = band - Manifold.cylinder(6, R - 1.0, R - 1.0, 128).translate([0, 0, cz - 3.0])
    b = (shell + neck) - inside + band
    holes = []
    pitch, hole_d = 3.5, 2.2
    dth = pitch / R
    th = 0.0
    while th < math.radians(128):
        deg = math.degrees(th)
        if abs(deg - 90) > 7.5:
            n = max(1, round(2 * math.pi * R * math.sin(th) / pitch))
            for i in range(n):
                ph = 360 * (i + 0.5 * (round(th / dth) % 2)) / n
                c = Manifold.cylinder(9, hole_d / 2, hole_d / 2, 10).translate([0, 0, R - 5])
                holes.append(c.rotate([0, deg, 0]).rotate([0, 0, ph]).translate([0, 0, cz]))
        th += dth
    b = b - Manifold.batch_boolean(holes, OpType.Add)
    skirt_h = TOP_PLATE + 4
    skirt = Manifold.cylinder(skirt_h + 0.5, TOP_BORE / 2 - 0.2, TOP_BORE / 2 - 0.2, 96).translate([0, 0, base_z - skirt_h])
    lugs = [rotz(Manifold.cube([3.2, 8.0, 2.8], True).translate([TOP_BORE / 2 + 1.0, 0, base_z - TOP_PLATE - 2.0]), a + 30) for a in (0, 120, 240)]
    throat = Manifold.cylinder(skirt_h + NECK_H + 6, TOP_THROAT / 2, TOP_THROAT / 2, 96).translate([0, 0, base_z - skirt_h - 1])
    return (b + skirt + Manifold.batch_boolean(lugs, OpType.Add)) - throat


def handle():
    """Ручка с длинным хвостовиком: хвостовик держит рычаг, лапки только фиксируют."""
    R = HANDLE_D / 2
    prof = [[0, 0], [R - 3, 0]]
    for i in range(1, 9):
        a = i / 8 * math.pi / 2
        prof.append([R - 3 + 3 * math.sin(a), -3 + 3 * math.cos(a)])
    r_end = HANDLE_END_D / 2
    for i in range(0, 13):
        a = i / 12 * math.pi / 2
        prof.append([r_end - 6 + 6 * math.cos(a), -HANDLE_L + 6 - 6 * math.sin(a)])
    prof.append([0, -HANDLE_L])
    b = revolve(prof)
    spig = revolve([[0, -0.1], [SPIGOT_D / 2, -0.1], [SPIGOT_D / 2, SPIGOT_L - 1.2], [SPIGOT_D / 2 - 1.2, SPIGOT_L], [0, SPIGOT_L]])
    lugs = [rotz(Manifold.cube([3.0, 7.5, 2.8], True).translate([SPIGOT_D / 2 + 0.9, 0, BOT_PLATE + 2.0]), a + 30) for a in (0, 120, 240)]
    return b + spig + Manifold.batch_boolean(lugs, OpType.Add)


def transmitter():
    """Передатчик для проверки посадки: низ на подставке, лицо к +Y, прищепка к -Y."""
    body_ = rounded_box(TX_W, TX_T, TX_L, 2.2)
    grille = rounded_box(TX_W - 2.4, TX_T - 2.4, 3.0, 1.0).translate([0, 0, TX_L - 2.2])
    btn = rounded_box(1.4, 3.6, 9.0, 0.5).translate([TX_W / 2 + 0.2, 0, TX_L - 18])
    sld = rounded_box(1.2, 3.0, 6.0, 0.4).translate([TX_W / 2 + 0.1, 0, TX_L - 30])
    arm = rounded_box(CLIP_W, 1.8, CLIP_L, 0.7).translate([0, -TX_T / 2 - CLIP_T + 0.9, 8.0])
    pivot = Manifold.cube([CLIP_W - 2, CLIP_T - 1.5, 7], True).translate([0, -TX_T / 2 - (CLIP_T - 1.5) / 2 + 0.4, 8 + CLIP_L - 14])
    at = [0, TX_Y, PEDESTAL_Z + TX_GAP]
    return (body_ + btn + sld).translate(at), grille.translate(at), (arm + pivot).translate(at)


def build(kind='taper'):
    tb, tg, tc = transmitter()
    return dict(box=box(kind), head=head(), handle=handle(), letters=letters(), tx_body=tb, tx_grille=tg, tx_clip=tc)


def to_mesh(m):
    me = m.to_mesh()
    return np.asarray(me.vert_properties)[:, :3].astype(float), np.asarray(me.tri_verts).astype(np.int64)


if __name__ == '__main__':
    p = build()
    tx = p['tx_body'] + p['tx_grille'] + p['tx_clip']
    for k in ('box', 'head', 'handle', 'letters'):
        b = p[k].bounding_box()
        print(k, p[k].status().name, [round(b[i + 3] - b[i], 1) for i in range(3)])
    for a, b_, n in ((tx, p['box'], 'передатчик/бокс'), (tx, p['head'], 'передатчик/голова'), (p['head'], p['box'], 'голова/бокс'), (p['handle'], p['box'], 'ручка/бокс'), (p['letters'], p['box'], 'надпись/бокс')):
        print(n, 'пересечение', round((a ^ b_).volume(), 3))
    # запас считаем без пластины: на неё прищепка и должна садиться
    walls = body() - well() - top_socket()
    print('зазор передатчик/стенки', round(tx.min_gap(walls, 5.0), 2))
    print('зазор передатчик/голова', round(tx.min_gap(p['head'], 5.0), 2))
    print('вся длина', round(p['head'].bounding_box()[5] - p['handle'].bounding_box()[2], 1))
