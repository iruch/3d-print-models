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
import zipfile
import numpy as np
import manifold3d as m3
from manifold3d import Manifold, CrossSection, FillRule, JoinType, OpType
import lettering

m3.set_circular_segments(72)

K = 52.0 / 180.0                     # мм на пиксель рисунка

# ---------- надпись: две строки, задаётся параметром ----------
TEXT = ('be', 'louder!')

# ---------- передатчик: сняты с фото рядом с линейкой, штангенциркулем не проверялось ----------
# Линейка лежит на листе, а передатчик выше неё, поэтому на фото он крупнее настоящего, примерно на 3–8 %.
# Здесь верхняя оценка без этой поправки: настоящий около 47 × 17 × 11, запас выйдет не меньше TX_GAP.
TX_L, TX_W, TX_T = 50.5, 18.0, 12.2
TX_SIDE = 0.8       # на сколько выступают кнопка и ползунок, они на одной стороне, +X
TX_R = 2.2          # скругление рёбер корпуса
TX_GAP = 1.0        # запас вокруг передатчика со всех сторон: входит и вынимается свободно

# Прищепка закрыта и стоит с наклоном: у зажима дальше от корпуса, у зубцов почти вплотную.
CLIP_L, CLIP_W = 40.5, 11.0
CLIP_TOP = 2.7      # от верхнего торца передатчика до конца зажима
CLIP_PRESS = 6.8    # толщина прищепки вместе с зазором у зажима, спереди назад
CLIP_TIP = 3.5      # то же у зубцов
CLIP_PLATE = 2.3    # толщина планки
PIVOT_FROM_TOP = 14.3   # ось прищепки от верхнего торца
PIVOT_BACK = 1.7        # ось за спинкой корпуса
EAR_L, EAR_W, EAR_D = 10.0, 7.0, 4.3    # проушина оси на спинке, ширина под планкой не видна, взята примерно
PRONG_L = 2.0       # штырьки на зубцах, упираются в пластину и отжимают планку
BODY_PIN = 1.0      # выступ на корпусе напротив них, отжимает корпус от пластины

TX_Y = CLIP_PRESS / 2   # закрытый передатчик с прищепкой идёт по центру прохода Ø27

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

# ---------- байонеты: поворот на 45° до упора и щелчок ----------
# Бокс печатается вверх дном, голова юбкой вниз, ручка хвостовиком вниз. Скосы подобраны под это: поддержки не нужны.
BAYONET = (30.0, 150.0, 270.0)      # углы вырезов под лапки
TURN = 45.0         # поворот до упора
TOP_SENSE = -1      # голова закрывается по часовой, если смотреть сверху
BOT_SENSE = 1       # ручка закрывается по часовой, если смотреть на неё снизу
RAMP_H = 0.6        # у выреза лапка идёт с таким запасом, дальше пандус
RAMP_A = 12.0       # длина пандуса, градусов
STOP_A = 6.5        # длина упора, градусов

TOP_BORE = 31.0     # отверстие под голову
TOP_THROAT = 27.0   # через него проходит передатчик
TOP_PLATE = 6.0     # толщина верхней плиты
TOP_SKIRT_R = 15.3  # юбка головы
GROOVE_R = 18.7     # кольцевой паз под лапки
NOTCH_W = 9.4       # ширина выреза под лапку
NOTCH_R = 17.95     # наружный край выреза
LUG_R = 17.7        # лапка головы
LUG_A = 14.0        # половина ширины лапки, градусов
LUG_H = 3.8         # высота лапки от торца юбки: зазор до плиты 0,2 мм, подбирается на пробнике
SEAT_Z = 79.8       # в боксе тут начинается конус под скос головы
TONGUE_A = 66.0     # корень язычка щелчка, градусов от выреза, свободный конец у следующего выреза
TONGUE_R = 17.3     # наружный край язычка, дальше прорезь
SLIT_R = 18.0       # наружный край прорези, спрятан под шейкой головы
BUMP_A = 97.0       # зуб на язычке, градусов от выреза
BUMP_H = 0.5        # высота зуба
GROOVE_V = 14.85    # дно канавки на юбке, зуб заходит в неё в двух положениях: открыто и закрыто

SPIGOT_D = 25.2     # хвостовик ручки
SPIGOT_L = 20.0     # длинный, чтобы ручка не качалась
BOT_PLATE = 6.0
BOT_GROOVE_R = 15.4 # паз под лапки ручки
BOT_GROOVE_TOP = 12.4
BOT_NOTCH_W = 9.0
BOT_NOTCH_R = 15.3
BOT_LUG_R = 15.0    # лапка ручки: косая с обеих сторон, зуб резьбы
BOT_LUG_A = 15.0
BOT_LUG_GAP = 0.2   # зазор лапки до конуса плиты по высоте, подбирается на пробнике
SPRING_R = 10.6     # внутри конца хвостовика полость, стенка 2 мм работает язычком
SPRING_Z = 15.0     # от этой высоты до торца хвостовика
SPRING_A = 45.0     # длина язычка, градусов
BOT_BUMP_A = 5.0    # зуб отстоит от оси лапки назад на столько градусов
BOT_BUMP_R = 13.2   # вершина зуба на хвостовике
BOT_V_R = 13.35     # дно канавки в отверстии бокса

PEDESTAL_Z = 43.0  # дно колодца: верх передатчика на 9–12 мм выше бокса, за него берутся и сжимают прищепку
BLADE_T = 2.0       # пластина, на которую садится прищепка
BLADE_H = 15.0      # заходит за штырьки, но не доходит до проушины
JAW_ROOM = 0.5      # добавка к глубине колодца: зубцы раскрываются на пластине


def rrect(w, h, r):
    return CrossSection.square([w - 2 * r, h - 2 * r], True).offset(r, JoinType.Round, 8, 24)


def revolve(profile):
    return CrossSection([profile], FillRule.EvenOdd).revolve(120)


def rotz(m, deg):
    return m.rotate([0, 0, deg])


def union(parts):
    return Manifold.batch_boolean(parts, OpType.Add)


def arc(pts, at, sense, a0, a1):
    """Сектор кольца: профиль (r, z) от a0 до a1 градусов, считая от угла at в сторону sense."""
    start = at + a0 if sense > 0 else at - a1
    return CrossSection([pts], FillRule.EvenOdd).revolve(240, a1 - a0).rotate([0, 0, start])


def ramp(profile, at, sense, a0, a1, h0, h1, n=12):
    """Пологий подъём сектором ступеньками: profile(h) даёт профиль, h идёт от h0 к h1."""
    step = (a1 - a0) / n
    return union([arc(profile(h0 + (h1 - h0) * (i + 0.5) / n), at, sense, a0 + i * step, a0 + (i + 1) * step + 0.02) for i in range(n)])


def prism(pts, z0, z1, ang):
    """Призма: контур в плане задан у оси X и поворачивается на угол ang."""
    return CrossSection([pts], FillRule.EvenOdd).extrude(z1 - z0).translate([0, 0, z0]).rotate([0, 0, ang])


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


def well_half():
    return TX_W / 2 + TX_SIDE + TX_GAP, (TX_T + CLIP_PRESS) / 2 + TX_GAP + JAW_ROOM


def blade_y():
    """Лицо и спина пластины: лицо за спинкой передатчика на высоту выступа корпуса."""
    y1 = TX_Y - TX_T / 2 - BODY_PIN
    return y1 - BLADE_T, y1


def blade():
    """Пластина на всю ширину колодца: с запасом передатчик иначе болтался бы и стучал в запись.
    Верх скошен со стороны прищепки, чтобы зубцы находили пластину на ощупь."""
    x = well_half()[0] + 0.5
    y0, y1 = blade_y()
    z0, z1 = PEDESTAL_Z - 0.5, PEDESTAL_Z + BLADE_H
    base = Manifold.cube([2 * x, y1 - y0, z1 - 2.5 - z0]).translate([-x, y0, z0])
    tip = Manifold.cube([2 * x, 0.8, 0.01]).translate([-x, y1 - 0.8, z1 - 0.01])
    return Manifold.batch_hull([base, tip])


def well():
    """Колодец под передатчик с зазором TX_GAP со всех сторон, сверху воронка к посадке головы."""
    x, y = well_half()
    z0, z1, z2 = PEDESTAL_Z, BOX_H - TOP_PLATE - 16, BOX_H - TOP_PLATE - 4
    low = Manifold.cube([2 * x, 2 * y, z1 - z0]).translate([-x, -y, z0])
    base = Manifold.cube([2 * x, 2 * y, 0.2]).translate([-x, -y, z1 - 0.2])
    top = CrossSection.circle(18.5, 96).extrude(0.2).translate([0, 0, z2 - 0.2])
    return low + Manifold.batch_hull([base, top])


def top_socket():
    """Гнездо головы: отверстие, вырезы, паз под плитой, пандусы, упоры и прорези язычков."""
    z = BOX_H
    zb = z - TOP_PLATE
    r = TOP_BORE / 2
    rc = r + z - SEAT_Z
    s = TOP_SENSE
    void = [revolve([[0, zb - 2], [r, zb - 2], [r, SEAT_Z], [rc, z], [rc, z + 1], [0, z + 1]]),
            Manifold.cylinder(4.0, GROOVE_R, GROOVE_R, 120).translate([0, 0, zb - 4.0])]
    stops = []
    notch_a = math.degrees(math.asin(NOTCH_W / 2 / r))
    # вырез заканчивается под шейкой головы, снаружи его не видно
    notch = Manifold.cube([8, NOTCH_W, TOP_PLATE + 4], True).translate([NOTCH_R - 4, 0, z - TOP_PLATE / 2]) ^ Manifold.cylinder(40, NOTCH_R, NOTCH_R, 120).translate([0, 0, z - 20])
    for a in BAYONET:
        void.append(rotz(notch, a))
        void.append(ramp(lambda h: [[r - 0.1, zb - 0.5], [GROOVE_R, zb - 0.5], [GROOVE_R, zb + h], [r - 0.1, zb + h]], a, s, notch_a - 1, notch_a + RAMP_A, RAMP_H, 0.0))
        void.append(arc([[TONGUE_R, zb - 0.5], [SLIT_R, zb - 0.5], [SLIT_R, z + 1], [TONGUE_R, z + 1]], a, s, TONGUE_A, 112.0))
        stops.append(arc([[r + 0.2, zb - 3.6], [GROOVE_R + 0.2, zb - 3.6], [GROOVE_R + 0.2, zb + 0.2], [r + 0.2, zb + 0.2]], a, s, TURN + LUG_A + 0.4, TURN + LUG_A + 0.4 + STOP_A))
    return union(void) - union(stops)


def top_bumps():
    """Зубы на свободных концах язычков. Гнутся только язычки, поэтому зуб считается отдельно от сборки."""
    r = TOP_BORE / 2
    zb = BOX_H - TOP_PLATE
    pts = [[r + 0.2, -1.5], [r - BUMP_H, -0.35], [r - BUMP_H, 0.35], [r + 0.2, 1.5]]
    return union([prism(pts, zb + 0.3, SEAT_Z - 0.3, a + TOP_SENSE * BUMP_A) for a in BAYONET])


def bottom_socket():
    """Гнездо ручки: плита косая изнутри, в печати вверх дном этот скос держит сам себя."""
    r = (SPIGOT_D + 0.4) / 2
    s = BOT_SENSE
    p = BOT_PLATE
    rg, top = BOT_GROOVE_R, BOT_GROOVE_TOP
    cone = lambda h: [[r - 0.1, p - 0.1 - h], [rg, p + rg - r - h], [rg, top], [r - 0.1, top]]
    void = [Manifold.cylinder(SPIGOT_L + 1.5, r, r, 120).translate([0, 0, -0.5]), revolve(cone(0.0))]
    stops = []
    v = [[r - 0.1, -1.9], [BOT_V_R, -0.5], [BOT_V_R, 0.5], [r - 0.1, 1.9]]
    notch_a = math.degrees(math.asin(BOT_NOTCH_W / 2 / r))
    notch = Manifold.cube([8, BOT_NOTCH_W, p + 3], True).translate([BOT_NOTCH_R - 4, 0, (p + 3) / 2 - 0.5]) ^ Manifold.cylinder(20, BOT_NOTCH_R, BOT_NOTCH_R, 120).translate([0, 0, -2])
    for a in BAYONET:
        void.append(rotz(notch, a))
        void.append(ramp(cone, a, s, notch_a - 1, notch_a + RAMP_A, RAMP_H, 0.0))
        void.append(prism(v, top - 0.5, SPIGOT_L + 1, a - s * BOT_BUMP_A))
        void.append(prism(v, top - 0.5, SPIGOT_L + 1, a + s * (TURN - BOT_BUMP_A)))
        stops.append(arc([[r + 0.2, p - 1], [rg + 0.2, p - 1], [rg + 0.2, top + 0.2], [r + 0.2, top + 0.2]], a, s, TURN + BOT_LUG_A + 0.4, TURN + BOT_LUG_A + 0.4 + STOP_A))
    return union(void) - union(stops)


def box(kind='taper', bumps=True):
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
    b = b - well() - top_socket() - bottom_socket() + blade()
    return b + top_bumps() if bumps else b


def letters():
    """Надпись спереди и сзади: сзади та же, развёрнута, чтобы читалась."""
    full, _ = text_lines()
    front = on_front(full.extrude(LETTER_T), y=-BOX_D / 2 + PANEL_D + POCKET_D)
    return front + rotz(front, 180)


def neck_prof():
    z = BOX_H
    return [[0, z], [NECK_D / 2, z], [NECK_D / 2, z + NECK_H - 0.8], [NECK_D / 2 - 0.8, z + NECK_H], [15.0, z + NECK_H + 2], [0, z + NECK_H + 2]]


def head():
    """Шар со сквозными отверстиями, шейка, юбка байонета с тремя лапками."""
    R = BALL_D / 2
    base_z = BOX_H
    cz = BALL_CZ
    shell = Manifold.sphere(R, 128).translate([0, 0, cz])
    inside = Manifold.sphere(R - 2.0, 96).translate([0, 0, cz])
    neck = revolve(neck_prof())
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
    return collar(b)


def collar(b):
    """Юбка с лапками, скос под шейкой и канавки щелчка. Деталь нарисована в закрытом положении."""
    base_z = BOX_H
    skirt_h = TOP_PLATE + 4
    z0 = base_z - skirt_h
    rs = TOP_SKIRT_R
    s = TOP_SENSE
    rt = TOP_THROAT / 2
    # скос в зазоре с конусом бокса: шейка печатается без поддержек, садится плоским кольцом снаружи
    skirt = revolve([[rt - 0.5, z0], [rs - 0.4, z0], [rs, z0 + 0.4], [rs, base_z - 2], [rs + 2, base_z], [rs + 2, base_z + 0.5], [rt - 0.5, base_z + 0.5]])
    lug = lambda h: [[rs - 0.3, z0], [LUG_R, z0], [LUG_R, z0 + LUG_H - h], [rs - 0.3, z0 + LUG_H - h]]
    lugs = []
    cuts = [Manifold.cylinder(skirt_h + NECK_H + 6, rt, rt, 120).translate([0, 0, z0 - 1])]
    v = [[rs + 0.3, -1.9], [GROOVE_V, -0.45], [GROOVE_V, 0.45], [rs + 0.3, 1.9]]
    for a in BAYONET:
        c = a + s * TURN
        lugs.append(arc(lug(0.0), c, s, -LUG_A, LUG_A - 3))
        lugs.append(ramp(lug, c, s, LUG_A - 3, LUG_A, 0.0, 0.8, n=6))
        cuts.append(prism(v, z0 - 1, SEAT_Z + 0.4, a + s * BUMP_A))
        cuts.append(prism(v, z0 - 1, SEAT_Z + 0.4, a + s * (BUMP_A + TURN)))
    return (b + skirt + union(lugs)) - union(cuts)


def shoulder():
    """Плечо ручки от оси до полного диаметра."""
    R = HANDLE_D / 2
    rho = 6.1
    prof = [[0, 0]]
    for i in range(0, 9):
        a = (1 - i / 8) * math.pi / 4
        prof.append([R - rho + rho * math.cos(a), rho * (math.sin(a) - math.sin(math.pi / 4))])
    return prof


def handle(bumps=True):
    """Ручка с длинным хвостовиком: хвостовик держит рычаг, лапки только фиксируют.
    Печатается торцом хвостовика на столе, поэтому плечо начинается со скоса 45°. Нарисована в закрытом положении."""
    prof = shoulder()
    r_end = HANDLE_END_D / 2
    for i in range(0, 13):
        a = i / 12 * math.pi / 2
        prof.append([r_end - 6 + 6 * math.cos(a), -HANDLE_L + 6 - 6 * math.sin(a)])
    prof.append([0, -HANDLE_L])
    return spigot(revolve(prof), bumps)


def spigot(b, with_bumps=True):
    """Хвостовик с косыми лапками и пружинящими язычками на конце."""
    r = SPIGOT_D / 2
    s = BOT_SENSE
    p, g = BOT_PLATE, BOT_LUG_GAP
    rl = BOT_LUG_R
    r0 = r - 0.2
    spig = revolve([[0, -0.1], [r, -0.1], [r, SPIGOT_L - 0.6], [r - 0.6, SPIGOT_L], [0, SPIGOT_L]])
    # низ лапки вдоль конуса плиты, верх под 45°, чтобы лапка печаталась сверху вниз без поддержек
    lug_prof = [[r0, p + r0 - r - 0.2 + g], [rl, p + rl - r - 0.2 + g], [rl, p + 3.6], [r0, p + 3.6 + rl - r0]]
    lugs, cuts, bumps = [], [Manifold.cylinder(SPIGOT_L - SPRING_Z + 1.5, SPRING_R, SPRING_R, 120).translate([0, 0, SPRING_Z - 1])], []
    bump = [[r - 0.2, -1.6], [BOT_BUMP_R, -0.35], [BOT_BUMP_R, 0.35], [r - 0.2, 1.6]]
    for a in BAYONET:
        c = a + s * TURN
        lugs.append(arc(lug_prof, c, s, -BOT_LUG_A, BOT_LUG_A))
        # язычок: сверху горизонтальный пропил, у свободного конца радиальный
        cuts.append(arc([[SPRING_R - 0.4, SPRING_Z - 1], [r + 0.5, SPRING_Z - 1], [r + 0.5, SPRING_Z], [SPRING_R - 0.4, SPRING_Z]], c, s, 2.0 - SPRING_A, 6.0))
        cuts.append(arc([[SPRING_R - 0.4, SPRING_Z - 1], [r + 0.5, SPRING_Z - 1], [r + 0.5, SPIGOT_L + 0.5], [SPRING_R - 0.4, SPIGOT_L + 0.5]], c, s, 2.0, 6.0))
        bumps.append(prism(bump, SPRING_Z + 0.5, SPIGOT_L - 0.8, c - s * BOT_BUMP_A))
    b = b + ((spig + union(lugs)) - union(cuts))
    return b + union(bumps) if with_bumps else b


def clip_arm(open_deg=0.0):
    """Планка прищепки в координатах передатчика: зажим вверху, зубцы внизу. open_deg раскрывает зубцы вокруг оси."""
    z_press, z_tip = TX_L - CLIP_TOP, TX_L - CLIP_TOP - CLIP_L
    y_press, y_tip = -TX_T / 2 - CLIP_PRESS, -TX_T / 2 - CLIP_TIP
    pts = [[y_tip, z_tip], [y_press, z_press], [y_press + CLIP_PLATE, z_press], [y_tip + CLIP_PLATE, z_tip]]
    arm = CrossSection([pts], FillRule.EvenOdd).extrude(CLIP_W).rotate([90, 0, 90]).translate([-CLIP_W / 2, 0, 0])
    yp, zp = -TX_T / 2 - PIVOT_BACK, TX_L - PIVOT_FROM_TOP
    return arm.translate([0, -yp, -zp]).rotate([-open_deg, 0, 0]).translate([0, yp, zp])


def seated_open():
    """На сколько раскрыта прищепка на пластине: штырьки упёрлись в спину пластины, худший случай."""
    y_inner = -TX_T / 2 - CLIP_TIP + CLIP_PLATE     # внутренняя грань планки у зубцов, закрыта
    need = (TX_Y + y_inner) - (blade_y()[0] - PRONG_L)
    return math.degrees(math.atan(need / (TX_L - PIVOT_FROM_TOP - (TX_L - CLIP_TOP - CLIP_L))))


def transmitter(open_deg=None, dz=0.0):
    """Передатчик для проверки посадки: лицо к +Y, прищепка к -Y, сверху торец с микрофоном.
    Кнопки и ось сняты с фото. Штырьки в модели не показаны, они учтены в раскрытии прищепки."""
    if open_deg is None:
        open_deg = seated_open()
    body_ = rounded_box(TX_W, TX_T, TX_L, TX_R)
    grille = rounded_box(TX_W - 2.4, TX_T - 2.4, 3.0, 1.0).translate([0, 0, TX_L - 3.0])
    btn = rounded_box(2 * TX_SIDE + 2, 5.0, 6.5, 0.5).translate([TX_W / 2 - 1, 0.8, TX_L - 12.5])
    sld = rounded_box(2 * TX_SIDE + 2, 5.0, 8.0, 0.5).translate([TX_W / 2 - 1, 0.8, TX_L - 25.0])
    ear = Manifold.cube([EAR_W, EAR_D + 0.4, EAR_L]).translate([-EAR_W / 2, -TX_T / 2 - EAR_D, TX_L - PIVOT_FROM_TOP - EAR_L / 2])
    clip = clip_arm(open_deg) + ear
    at = [0, TX_Y, PEDESTAL_Z + TX_GAP + dz]
    return (body_ + btn + sld).translate(at), grille.translate(at), clip.translate(at)


def build(kind='taper'):
    tb, tg, tc = transmitter()
    return dict(box=box(kind), head=head(), handle=handle(), letters=letters(), tx_body=tb, tx_grille=tg, tx_clip=tc)


def turned(m, sense, deg, dz=0.0):
    """Деталь нарисована закрытой: deg — на сколько она не довёрнута до упора, dz — на сколько не дошла до посадки."""
    return m.rotate([0, 0, -sense * deg]).translate([0, 0, dz])


def joint(name, part, free, mate, free_mate, sense, sign):
    """Вход лапок в вырезы и поворот до упора. part и mate с зубами, free и free_mate без них: зуб гнёт язычок, это норма."""
    miss = [d for d in (16, 12, 8, 4, 2, 1, 0) if (turned(part, sense, TURN, sign * d) ^ mate).volume() > 0.001]
    jam = {d: round((turned(free, sense, d) ^ free_mate).volume(), 3) for d in range(int(TURN), -1, -5) if (turned(free, sense, d) ^ free_mate).volume() > 0.001}
    print(name, 'вход: мешает на высотах', miss, '; поворот: мешает на градусах', jam)
    print(name, 'открыто и закрыто с зубами, пересечение', round((turned(part, sense, TURN) ^ mate).volume(), 3), round((part ^ mate).volume(), 3))
    print(name, 'перегон за упор на 2°, пересечение', round((turned(free, sense, -2.0) ^ free_mate).volume(), 2))


def bayonet_check(p):
    top = box(bumps=False).trim_by_plane([0, 0, 1], 60.0)
    bot = box(bumps=False).trim_by_plane([0, 0, -1], -26.0)
    hr = p['head'].trim_by_plane([0, 0, -1], -90.0)
    joint('голова', hr, hr, top + top_bumps(), top, TOP_SENSE, 1)
    hd = p['handle'].trim_by_plane([0, 0, 1], -6.0)
    free = handle(False).trim_by_plane([0, 0, 1], -6.0)
    joint('ручка', hd, free, bot, bot, BOT_SENSE, -1)


def to_mesh(m):
    me = m.to_mesh()
    return np.asarray(me.vert_properties)[:, :3].astype(float), np.asarray(me.tri_verts).astype(np.int64)


def write_3mf(path, parts, title):
    """parts — список (имя, Manifold, цвет '#RRGGBB' или None). Цвета нужны только картинкам."""
    colored = [(name, color) for name, _, color in parts if color]
    resources, items = [], []
    if colored:
        base = ''.join(f'<base name="{name}" displaycolor="{color}"/>' for name, color in colored)
        resources.append(f'<basematerials id="1">{base}</basematerials>')
    pindex = 0
    for i, (name, model, color) in enumerate(parts):
        oid = i + 2 if colored else i + 1
        verts, tris = to_mesh(model)
        v = ''.join(f'<vertex x="{a:.4f}" y="{b:.4f}" z="{c:.4f}"/>' for a, b, c in verts)
        t = ''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tris)
        mat = ''
        if color:
            mat = f' pid="1" pindex="{pindex}"'
            pindex += 1
        resources.append(f'<object id="{oid}" type="model" name="{name}"{mat}><mesh><vertices>{v}</vertices><triangles>{t}</triangles></mesh></object>')
        items.append(f'<item objectid="{oid}"/>')
    res = ''.join(resources)
    model_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
<metadata name="Title">{title}</metadata>
<resources>
{res}
</resources>
<build>{"".join(items)}</build>
</model>'''
    ct = '''<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
</Types>'''
    rels = '''<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>'''
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', ct)
        z.writestr('_rels/.rels', rels)
        z.writestr('3D/3dmodel.model', model_xml)


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
    print('раскрытие прищепки на пластине, градусов', round(seated_open(), 1))
    print('зазор передатчик/стенки', round(tx.min_gap(walls, 5.0), 2))
    print('зазор передатчик/голова', round(tx.min_gap(p['head'], 5.0), 2))
    print('высота над боксом', round(PEDESTAL_Z + TX_GAP + TX_L - BOX_H, 1), 'при настоящей длине 47:', round(PEDESTAL_Z + TX_GAP + 47 - BOX_H, 1))
    # прогон сверху до посадки: закрытый передатчик до пластины, ниже прищепка сжата
    tip_seated = PEDESTAL_Z + TX_GAP + TX_L - CLIP_TOP - CLIP_L
    start = PEDESTAL_Z + BLADE_H - tip_seated
    full = p['box']
    worst = 99.0
    for dz in range(70, -1, -1):
        parts = transmitter(0.0 if dz > start else None, float(dz))
        t = parts[0] + parts[1] + parts[2]
        v = (t ^ full).volume()
        if v > 0.001:
            print('  застревает при подъёме', dz, 'объём', round(v, 2))
        worst = min(worst, t.min_gap(walls, 5.0))
    print('прогон: наименьший зазор к стенкам', round(worst, 2))
    bayonet_check(p)
    print('вся длина', round(p['head'].bounding_box()[5] - p['handle'].bounding_box()[2], 1))
