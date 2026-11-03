# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "manifold3d", "matplotlib", "fonttools"]
# ///
"""Кейс-микрофон: геометрия эскиза. Файла для печати пока нет, модель в разработке.
Три детали и надпись: шар-голова, бокс, ручка. Передатчик Aksdom M31 вставляется сверху.
Все размеры в мм. X — вправо, Y — от зрителя (перед = -Y), Z — вверх. Z = 0 — низ бокса.
Фронт бокса и панель взяты с рисунка автора. Крылья с рисунка убраны, бокс и шар уменьшены: размер задаёт передатчик.

uv run mic_case.py      -> проверка: габариты деталей, пересечения в сборке, байонеты, нависания
uv run mic_case.py --print [--top слово --bottom слово --out файл.3mf]   -> все детали на одном столе, одним цветом
uv run mic_case.py --plates [--top слово --bottom слово --out папка]   -> раскладки по цветам и таблица наборов в ../plates
Без uv: pip install numpy manifold3d matplotlib fonttools, дальше python вместо uv run.
"""
import argparse
import itertools
import math
import zipfile
from pathlib import Path

import numpy as np
import manifold3d as m3
from manifold3d import Manifold, CrossSection, FillRule, JoinType, OpType
import lettering

m3.set_circular_segments(72)

# ---------- надпись: две строки, задаётся параметром ----------
TEXT = ('be', 'louder!')
EXAMPLE = TEXT      # пример для репозитория: настоящие имена заказчиков в публичный репозиторий не кладём

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

# ---------- бокс: фронт с рисунка, высота по передатчику ----------
PEDESTAL_Z = 24.0  # дно колодца вплотную к гнезду ручки: посередине долина уходит прямо в гнездо
TX_OUT = 25.0      # на столько верх передатчика выходит из бокса в шар. Больше нельзя: ушко прищепки
                   # должно остаться выше перегородки. Зато за верх легко взяться и сжать прищепку
BOX_H = PEDESTAL_Z + TX_GAP + TX_L - TX_OUT
BOX_W = 44.0        # квадрат: меньше не даёт байонет головы вокруг горла Ø27
BOX_R = 8.5         # скругление углов по фронту
BOX_D = 44.0        # глубина: вокруг горла Ø27 кольцевой паз байонета головы Ø37,4 и стенка 3,3 мм
EDGE_R = 2.5        # скругление рёбер по глубине
PANEL_W = BOX_W - 2 * (EDGE_R + 1.15)    # панель под надпись: до скругления рёбер остаётся 1,15 мм
PANEL_H = BOX_H - 14.0
PANEL_Z = BOX_H / 2  # центр панели от низа бокса
PANEL_R = 7.0
PANEL_D = 1.2       # глубина панели, край со скосом 45°

# ---------- надпись на боксе ----------
LETTER_T = 3.0      # толщина
POCKET_D = 1.5      # половина в выемке, половина снаружи
POCKET_GAP = 0.4    # зазор выемки на сторону. При 0,15 слова не вошли: выемка в вертикальной стенке, её верхние края печатаются навесом
WORD_MARGIN = 0.95  # от слова до края дна панели. Задан отдельно, чтобы размер слов не зависел от зазора выемки
lettering.WORD_W = PANEL_W - 2 * PANEL_D - 2 * WORD_MARGIN          # нижнее слово во всю панель
lettering.MAX_SIZE = 11.0 * lettering.WORD_W / 43.5                 # короткое слово уменьшается так же

# ---------- шар и ручка ----------
BALL_D = 44.0       # по ширине бокса; верх передатчика внутри помещается с запасом
NECK_D, NECK_H = 36.0, 4.3
BALL_CZ = BOX_H + BALL_D / 2 - 1.0
BALL_ROOF = 52.0    # верх полости шара конус с таким нависанием от вертикали, None — полость сферой; снаружи шар не меняется
HANDLE_D, HANDLE_END_D, HANDLE_L = 30.0, 25.0, 55.0   # у бокса шире, к низу сужается

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
LUG_H = 3.8         # высота лапки от торца юбки: зазор до плиты 0,2 мм, подбирается по пробной печати
SEAT_Z = BOX_H - 2.2  # у этой высоты кончаются зуб язычка и канавки щелчка на юбке
TONGUE_A = 66.0     # корень язычка щелчка, градусов от выреза, свободный конец у следующего выреза
TONGUE_R = 17.3     # наружный край язычка, дальше прорезь. Тоньше нельзя: верх язычка срежет конус, и он начнётся в воздухе
SLIT_R = 18.0       # наружный край прорези, спрятан под шейкой головы
BUMP_A = 97.0       # зуб на язычке, градусов от выреза
BUMP_H = 0.4        # высота зуба: язычок гнётся на 0,2 мм. Бокс бывает из PLA+, она жёстче и хрупче PETG, поэтому изгиб меньше
GROOVE_V = 14.85    # дно канавки на юбке, зуб заходит в неё в двух положениях: открыто и закрыто
# Голова садится скосом под шейкой на такой же конус в боксе и встаёт по оси. Раньше между ними был зазор, голова стояла
# шейкой на лице бокса, а по бокам лицо срезано скруглением углов: голова опиралась на две дужки и качалась.
# Лапки под плитой с зазором 0,2: ступеньки слоёв на конусе и на скосе ложатся друг в друга и голову не поднимают,
# а провис навесов может поднять её и выбрать часть зазора. Плита 6 мм кратна слою, на 0,1 тоньше слайсер её не сделает.

SPIGOT_D = 25.2     # хвостовик ручки
SPIGOT_L = 20.0     # длинный, чтобы ручка не качалась
BOT_PLATE = 6.0
BOT_GROOVE_R = 15.4 # паз под лапки ручки
BOT_GROOVE_TOP = 12.4
BOT_NOTCH_W = 9.0
BOT_NOTCH_R = 15.3
BOT_LUG_R = 15.0    # лапка ручки: косая с обеих сторон, зуб резьбы
BOT_LUG_A = 15.0
BOT_LUG_GAP = 0.2   # зазор лапки до конуса плиты по высоте, подбирается по пробной печати
SPRING_R = 10.6     # внутри конца хвостовика полость, стенка 2 мм работает язычком
SPRING_Z = 15.0     # от этой высоты до торца хвостовика
SPRING_A = 45.0     # длина язычка, градусов
BOT_BUMP_A = 5.0    # зуб отстоит от оси лапки назад на столько градусов
BOT_BUMP_R = 13.2   # вершина зуба на хвостовике
BOT_V_R = 13.35     # дно канавки в отверстии бокса

BLADE_T = 2.0       # перегородка, которую зажимает прищепка
JAW_ROOM = 0.5      # добавка к глубине колодца: зубцы раскрываются на пластине

# ---------- стол ----------
BRIM_W = 10.0       # кайма вокруг головы и ручки: обе высокие, стоят на узком кольце, а сверху шире
BRIM_T = 0.2        # кайма в один слой, после печати отрезается
PLATE_GAP = 4.0     # зазор между деталями и каймами на столе: детали стоят тесно, сопло меньше ездит


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
    b = Manifold.batch_hull(layers)
    # Бокс печатается верхом на столе, а у стола скругления углов почти горизонтальны и висели бы в воздухе:
    # на первой печати кромка там вышла рваной. Поэтому у верха скругления переходят в скос 45°.
    tops = []
    for h in [0.2 * i for i in range(1, 13)] + [BOX_R * (1 - math.cos(math.pi / 4))]:
        s = b.slice(BOX_H - h)
        tops.append(Manifold.batch_hull([s.extrude(0.01).translate([0, 0, BOX_H - h]),
                                         s.offset(-h, JoinType.Round, 8, 24).extrude(0.01).translate([0, 0, BOX_H - 0.01])]))
    return b + union(tops)


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
    """Перегородка поперёк колодца между передатчиком и прищепкой. Прищепка зажимает её, как край кармана,
    поэтому передатчик не болтается и не стучит в запись. Идёт от дна до верха бокса: вверх дном она стоит
    прямо на столе и печатается без поддержек. Внизу расходится под 45° в стенки воронки, выше идёт
    шириной колодца, чтобы не задеть юбку головы."""
    y0, y1 = blade_y()
    z0, z2 = PEDESTAL_Z - 0.5, BOX_H - TOP_PLATE - 4
    xn, xe = TX_W / 2 + TX_SIDE + TX_GAP, 20.0
    pts = [[-xe, z0], [xe, z0], [xe, z2 - (xe - xn)], [xn, z2], [xn, BOX_H], [-xn, BOX_H], [-xn, z2], [-xe, z2 - (xe - xn)]]
    return CrossSection([pts], FillRule.EvenOdd).extrude(y1 - y0).rotate([90, 0, 0]).translate([0, y1, 0])


def well():
    """Колодец под передатчик с зазором TX_GAP со всех сторон, сверху воронка к посадке головы."""
    x, y = well_half()
    z0, z1, z2 = PEDESTAL_Z, BOX_H - TOP_PLATE - 16, BOX_H - TOP_PLATE - 4
    low = Manifold.cube([2 * x, 2 * y, z1 - z0]).translate([-x, -y, z0])
    # дно перед перегородкой двускатное: вверх дном плоское было бы мостом 15 мм, позади перегородки мост короткий.
    # Посередине долина уходит прямо в гнездо ручки, по краям дно остаётся на 1,5 мм выше пазов щелчка
    b1 = blade_y()[1]
    valley = [[b1, z0 + 0.01], [y, z0 + 0.01], [(b1 + y) / 2, z0 - (y - b1) / 2]]
    valley = CrossSection([valley], FillRule.EvenOdd).extrude(2 * x).rotate([90, 0, 90]).translate([-x, 0, 0])
    floor = SPIGOT_L + 2.5
    keep = Manifold.cube([2 * x + 2, 2 * y + 2, z0 - floor + 1]).translate([-x - 1, -y - 1, floor])
    keep = keep + Manifold.cylinder(z0 - SPIGOT_L, SPIGOT_D / 2, SPIGOT_D / 2, 96).translate([0, 0, SPIGOT_L + 1])
    low = low + (valley ^ keep)
    base = Manifold.cube([2 * x, 2 * y, 0.2]).translate([-x, -y, z1 - 0.2])
    top = CrossSection.circle(18.5, 96).extrude(0.2).translate([0, 0, z2 - 0.2])
    return low + Manifold.batch_hull([base, top])


def top_socket():
    """Гнездо головы: отверстие, конус под скос шейки, вырезы, паз под плитой, пандусы, упоры и прорези язычков."""
    z = BOX_H
    zb = z - TOP_PLATE
    z4 = zb - 4.0               # низ паза под лапками
    r = TOP_BORE / 2
    rc = TOP_SKIRT_R + 2.02     # конус по скосу под шейкой головы; 0,02 — чтобы в проверке поворота не цеплялись грани многоугольников
    s = TOP_SENSE
    void = [revolve([[0, zb - 2], [r, zb - 2], [r, z - (rc - r)], [rc, z], [rc, z + 1], [0, z + 1]]),
            Manifold.cylinder(zb - z4, GROOVE_R, GROOVE_R, 120).translate([0, 0, z4])]
    stops = []
    notch_a = math.degrees(math.asin(NOTCH_W / 2 / r))
    # вырез заканчивается под шейкой головы, снаружи его не видно
    notch = Manifold.cube([8, NOTCH_W, TOP_PLATE + 4], True).translate([NOTCH_R - 4, 0, z - TOP_PLATE / 2]) ^ Manifold.cylinder(40, NOTCH_R, NOTCH_R, 120).translate([0, 0, z - 20])
    for a in BAYONET:
        void.append(rotz(notch, a))
        void.append(ramp(lambda h: [[r - 0.1, zb - 0.5], [GROOVE_R, zb - 0.5], [GROOVE_R, zb + h], [r - 0.1, zb + h]], a, s, notch_a - 1, notch_a + RAMP_A, RAMP_H, 0.0))
        void.append(arc([[TONGUE_R, zb - 0.5], [SLIT_R, zb - 0.5], [SLIT_R, z + 1], [TONGUE_R, z + 1]], a, s, TONGUE_A, 112.0))
        stops.append(arc([[r + 0.2, z4 + 0.4], [GROOVE_R + 0.2, z4 + 0.4], [GROOVE_R + 0.2, zb + 0.2], [r + 0.2, zb + 0.2]], a, s, TURN + LUG_A + 0.4, TURN + LUG_A + 0.4 + STOP_A))
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


def box(bumps=True):
    full, solid = text_lines()
    b = body()
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


def ball_cavity():
    """Полость шара. Купол сверху слишком пологий и сам не напечатается, поэтому верх полости идёт прямым конусом
    от сферы к вершине под макушкой: дальше всё нависание равно BALL_ROOF, стенка у макушки 2 мм."""
    r = BALL_D / 2 - 2.0
    cz = BALL_CZ
    s = Manifold.sphere(r, 96).translate([0, 0, cz])
    if BALL_ROOF is None:
        return s
    a = math.radians(2 * (90.0 - BALL_ROOF))    # хорда от вершины сферы до точки a от неё идёт под углом 90 - a / 2
    z0, r0 = r * math.cos(a), r * math.sin(a)
    return s.trim_by_plane([0, 0, -1], -(cz + z0)) + revolve([[0, cz + z0 - 0.01], [r0, cz + z0 - 0.01], [0, cz + r]])


def head():
    """Шар со сквозными отверстиями, шейка, юбка байонета с тремя лапками."""
    R = BALL_D / 2
    base_z = BOX_H
    cz = BALL_CZ
    shell = Manifold.sphere(R, 128).translate([0, 0, cz])
    inside = ball_cavity()
    neck = revolve(neck_prof())
    # поясок снизу со скосом 45°: шар печатается вверх, плоская кромка висела бы в воздухе
    band = revolve([[R - 1.0, cz - 3.3], [R, cz - 3.3], [R + 1.3, cz - 2.0], [R + 1.3, cz + 2.0], [R - 1.0, cz + 2.0]])
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
                c = Manifold.cylinder(11, hole_d / 2, hole_d / 2, 10).translate([0, 0, R - 8])
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
    # потолок полости и пропилов под 45°: плоский провис бы при печати и прирос к язычкам, а поддержку сюда не поставить
    z1 = SPRING_Z - 1
    hollow = revolve([[0, z1 - SPRING_R], [SPRING_R, z1], [SPRING_R, SPIGOT_L + 0.5], [0, SPIGOT_L + 0.5]])
    ri, ro = SPRING_R - 0.4, r + 0.5
    under = [[ro, z1 + SPRING_R - ro], [SPRING_R, z1], [ri, z1]]        # низ тела над пропилом, продолжает верх лапки
    lugs, cuts, bumps = [], [hollow], []
    bump = [[r - 0.2, -1.6], [BOT_BUMP_R, -0.35], [BOT_BUMP_R, 0.35], [r - 0.2, 1.6]]
    for a in BAYONET:
        c = a + s * TURN
        lugs.append(arc(lug_prof, c, s, -BOT_LUG_A, BOT_LUG_A))
        # язычок: сверху пропил поперёк стенки, у свободного конца радиальный
        cuts.append(arc([[ri, SPRING_Z], [ro, SPRING_Z]] + under, c, s, 2.0 - SPRING_A, 6.0))
        cuts.append(arc([[ri, SPIGOT_L + 0.5], [ro, SPIGOT_L + 0.5]] + under, c, s, 2.0, 6.0))
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


def build():
    tb, tg, tc = transmitter()
    return dict(box=box(), head=head(), handle=handle(), letters=letters(), tx_body=tb, tx_grille=tg, tx_clip=tc)


def overhangs(name, m, limit=61.0):
    """Нависания в положении печати: грани круче limit от вертикали, кроме лежащих на столе. Края круглых отверстий всегда попадают сюда."""
    b = m.bounding_box()
    v, t = to_mesh(m.translate([0, 0, -b[2]]))
    a, e, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    n = np.cross(e - a, c - a)
    area = np.linalg.norm(n, axis=1) / 2
    down = np.degrees(np.arcsin(np.clip(-n[:, 2] / (2 * area + 1e-12), -1, 1)))     # 0 — стенка, 90 — потолок
    zc = (a[:, 2] + e[:, 2] + c[:, 2]) / 3
    bad = (down > limit) & (zc > 0.3)
    print(f'{name}: круче {limit:.0f}° {area[bad].sum():.0f} мм² из {area.sum():.0f}, самый большой пояс по высоте:', end=' ')
    bands = np.floor(zc[bad] / 2) * 2
    print(', '.join(f'{z:.0f}–{z + 2:.0f} мм {area[bad][bands == z].sum():.0f} мм²' for z in sorted(np.unique(bands), key=lambda z: -area[bad][bands == z].sum())[:3]))


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
    top = box(bumps=False).trim_by_plane([0, 0, 1], BOX_H - 22.0)
    bot = box(bumps=False).trim_by_plane([0, 0, -1], -26.0)
    hr = p['head'].trim_by_plane([0, 0, -1], -(BOX_H + 8.0))
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


def brim(m):
    """Кайма в один слой вокруг кольца, которым деталь стоит на столе. Ось детали в начале координат.
    Край кольца берётся по первому слою на каждом угле, медиана: лапки и пропилы её не сдвигают,
    и кайма заходит на кольцо на 0,3 мм по всей окружности, а не только на лапки.
    Возвращает деталь с каймой и наружный радиус каймы."""
    cs = m.slice(BRIM_T / 2)
    edge = []
    for a in range(0, 360, 2):
        ray = CrossSection.square([60, 0.2]).translate([0, -0.1]).rotate(a)
        edge.append(max((math.hypot(x, y) for poly in (cs ^ ray).to_polygons() for x, y in poly), default=0.0))
    r_in, r = sorted(edge)[len(edge) // 2], max(edge)
    ring = CrossSection.circle(r + BRIM_W, 144) - CrossSection.circle(r_in - 0.3, 144)
    return m + ring.extrude(BRIM_T), r + BRIM_W


def bed_parts():
    """Детали в положении печати, каждая осью в начале координат, низом на столе: бокс вверх дном, голова юбкой вниз,
    ручка хвостовиком вниз, слова лицом вниз. Голова и ручка с каймой: без неё на пробной печати одну из них сорвало со стола.
    Возвращает {деталь: Manifold, 'words': [четыре слова]} и наружные радиусы кайм головы и ручки."""
    def base(m):
        b = m.bounding_box()
        return m.translate([-(b[0] + b[3]) / 2, -(b[1] + b[4]) / 2, -b[2]])
    p = build()
    head, r_head = brim(base(p['head']))
    handle, r_handle = brim(base(p['handle'].rotate([180, 0, 0])))
    # слова лицом вниз: лицо выходит гладким, а сторона, которая входит в паз, без наплыва первого слоя
    words = sorted(text_lines()[0].decompose(), key=lambda c: c.bounds()[2] - c.bounds()[0])
    words = [base(w.extrude(LETTER_T).rotate([180, 0, 0])) for w in words + words]
    return dict(box=base(p['box'].rotate([180, 0, 0])), head=head, handle=handle, words=words), r_head, r_handle


def to_bed_center(parts):
    """Сдвигает всю раскладку в центр стола 220 × 220. parts — [(имя, Manifold)]."""
    b = Manifold.batch_boolean([m for _, m in parts], OpType.Add).bounding_box()
    dx, dy = 110 - (b[0] + b[3]) / 2, 110 - (b[1] + b[4]) / 2
    return [(n, m.translate([dx, dy, 0]), None) for n, m in parts]


def word_size(words):
    w = max(m.bounding_box()[3] - m.bounding_box()[0] for m in words)
    h = max(m.bounding_box()[4] - m.bounding_box()[1] for m in words)
    return w, h


def plate():
    """Все детали на одном столе, для печати одним цветом.
    Стоят тесно: бокс в углу, голова справа от него, ручка спереди, слова между ними."""
    bp, r_head, r_handle = bed_parts()
    g = PLATE_GAP
    parts = [('box', bp['box']),
             ('head', bp['head'].translate([BOX_W / 2 + g + r_head, 0, 0])),
             ('handle', bp['handle'].translate([0, -(BOX_D / 2 + g + r_handle), 0]))]
    w_max, h_max = word_size(bp['words'])
    for i, w in enumerate(bp['words']):
        x = r_handle + g + w_max / 2               # правее каймы ручки
        y = -(r_head + g + h_max / 2) - i * (h_max + g)   # ниже каймы головы
        parts.append((f'word-{i + 1}', w.translate([x, y, 0])))
    return to_bed_center(parts)


def pack(sizes, g=PLATE_GAP):
    """Плотная раскладка прямоугольников (ширина, глубина) с зазором g. Перебирает порядок, каждый ставит вплотную
    справа или сзади от уже поставленных и берёт раскладку с самым маленьким столом.
    Возвращает левые передние углы и размер стола."""
    best = None
    for order in itertools.permutations(range(len(sizes))):
        pos = {}
        for i in order:
            w, h = sizes[i]
            cands = [(0.0, 0.0)] + [c for j, (x, y) in pos.items() for c in ((x + sizes[j][0] + g, y), (x, y + sizes[j][1] + g))]
            choice = None
            for cx, cy in cands:
                if any(cx < x + sizes[j][0] + g and x < cx + w + g and cy < y + sizes[j][1] + g and y < cy + h + g
                       for j, (x, y) in pos.items()):
                    continue
                W = max([cx + w] + [x + sizes[j][0] for j, (x, y) in pos.items()])
                H = max([cy + h] + [y + sizes[j][1] for j, (x, y) in pos.items()])
                key = (max(W, H), W * H)
                if choice is None or key < choice[0]:
                    choice = (key, (cx, cy))
            pos[i] = choice[1]
        W = max(pos[i][0] + sizes[i][0] for i in pos)
        H = max(pos[i][1] + sizes[i][1] for i in pos)
        key = (max(W, H), W * H)
        if best is None or key < best[0]:
            best = (key, [pos[i] for i in range(len(sizes))], (W, H))
    return best[1], best[2]


def plate_of(group):
    """Детали одного цвета на одном столе, например только голова и ручка. group — имена из color_sets.PARTS.
    Каждая деталь занимает свой прямоугольник, слова идут блоком: столбиком или два на два, что выйдет теснее."""
    bp, _, _ = bed_parts()
    g = PLATE_GAP
    single = []
    for name in ('box', 'head', 'handle'):
        if name in group:
            b = bp[name].bounding_box()
            single.append(([(name, bp[name])], (b[3] - b[0], b[4] - b[1])))
    variants = [[]]
    if 'words' in group:
        w, h = word_size(bp['words'])
        variants = []
        for cols in (1, 2):
            rows = 4 // cols
            cell = [(f'word-{i + 1}', m.translate([(i % cols) * (w + g) + w / 2, -(i // cols) * (h + g) - h / 2, 0]))
                    for i, m in enumerate(bp['words'])]
            # блок от левого переднего угла
            cell = [(n, m.translate([0, rows * h + (rows - 1) * g, 0])) for n, m in cell]
            variants.append([(cell, (cols * w + (cols - 1) * g, rows * h + (rows - 1) * g))])
    best = None
    for extra in variants:
        blocks = single + extra
        corners, (W, H) = pack([size for _, size in blocks], g)
        if best is None or (max(W, H), W * H) < best[0]:
            best = ((max(W, H), W * H), blocks, corners)
    _, blocks, corners = best
    parts = []
    for (items, (w, h)), (x, y) in zip(blocks, corners):
        for n, m in items:
            if n.startswith('word'):
                parts.append((n, m.translate([x, y, 0])))
            else:
                parts.append((n, m.translate([x + w / 2, y + h / 2, 0])))
    return to_bed_center(parts)


def write_plates(out):
    """Раскладки по цветам для принтера с одной нитью: каждое сочетание деталей одного цвета, какое встречается
    в наборах color_sets, ложится в свой 3mf один раз. Рядом README с таблицей: какой набор какими файлами
    и какой нитью печатать."""
    from color_sets import NAMES, PARTS, PART_NAMES, sets, prints
    name = 'aksdom-m31-reporter-mic-case-v1'
    count = {}
    for _, _, cc in sets():
        for _, group in prints(cc):
            count[group] = count.get(group, 0) + 1
    groups = sorted(count, key=lambda gr: (-count[gr], [PARTS.index(x) for x in gr]))
    files, rows = {}, []
    for gr in groups:
        fn = f'{name}-{"-".join(gr)}.3mf'
        parts = plate_of(gr)
        write_3mf(out / fn, parts, fn[:-4])
        b = Manifold.batch_boolean([m for _, m, _ in parts], OpType.Add).bounding_box()
        what = ', '.join(PART_NAMES[x] for x in gr)
        files[gr] = (fn, what)
        rows.append(f'| [`{fn}`]({fn}) | {what} | {b[3] - b[0]:.0f} × {b[4] - b[1]:.0f} × {b[5] - b[2]:.0f} | {count[gr]} |')
        print(fn, what, f'{b[3] - b[0]:.1f} × {b[4] - b[1]:.1f} × {b[5] - b[2]:.1f}', 'наборов', count[gr], flush=True)
    table = []
    for n, _, cc in sets():
        steps = '<br>'.join(f'{i + 1}. [{files[gr][1]}]({files[gr][0]}) — {NAMES[c]}' for i, (c, gr) in enumerate(prints(cc)))
        table.append(f'| {n} | ' + ' | '.join(NAMES[c] for c in cc) + f' | {steps} |')
    text = f"""# Кейс-микрофон: раскладки по цветам

Принтер с одной нитью печатает кейс в несколько заходов: одна печать — один цвет. Детали одного цвета стоят на одном столе, между печатями меняется нить. Порядок печатей в наборе любой.

Каждая раскладка лежит здесь один раз и подходит всем наборам с таким сочетанием деталей. Цвета в файлах нет: его даёт нить, которой печатаете. Номера наборов те же, что на картинках цветов в [README модели](../../README.md#виды). Все детали одним цветом, например для пробной сборки, — в файле [`../{name}.3mf`](../{name}.3mf).

Настройки печати — в [README модели](../../README.md#печать). Кайма у головы и ручки уже в модели, в слайсере её надо выключить, поддержки тоже.

Файлы и таблица сделаны скриптом `v1/src/mic_case.py --plates`, надпись в них — {'пример' if TEXT == EXAMPLE else '«' + ' '.join(TEXT) + '»'}. Своя надпись: `--top слово --bottom слово --out папка`. От надписи зависят и слова, и выемки в боксе, поэтому пересобирается всё.

## Файлы

| Файл | Что на столе | Габариты, мм (Ш × Г × В) | В скольких наборах |
|---|---|---|---|
""" + '\n'.join(rows) + """

## Наборы

Цвета названы как в [FILAMENTS.md](../../../../FILAMENTS.md).

| № | Голова | Бокс | Ручка | Надпись | Печати |
|---|---|---|---|---|---|
""" + '\n'.join(table) + """

## Лицензия

Как у модели: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.ru), автор — iruch.
"""
    (out / 'README.md').write_text(text, encoding='utf8')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--print', dest='to_print', action='store_true', help='записать детали в 3mf и выйти')
    ap.add_argument('--plates', action='store_true', help='раскладки по цветам и таблица наборов в папку и выйти')
    ap.add_argument('--top', default=TEXT[0])
    ap.add_argument('--bottom', default=TEXT[1])
    ap.add_argument('--out')
    args = ap.parse_args()
    TEXT = (args.top, args.bottom)
    if args.plates:
        out = Path(args.out) if args.out else Path(__file__).resolve().parents[1] / 'plates'
        out.mkdir(parents=True, exist_ok=True)
        write_plates(out)
        raise SystemExit
    if args.to_print:
        name = 'aksdom-m31-reporter-mic-case-v1'
        out = Path(args.out) if args.out else Path(__file__).resolve().parents[1] / f'{name}.3mf'
        parts = plate()
        write_3mf(out, parts, name)
        for n, m, _ in parts:
            b = m.bounding_box()
            area = m.surface_area()
            print(f'{n}: {b[3] - b[0]:.1f} × {b[4] - b[1]:.1f} × {b[5] - b[2]:.1f}, X {b[0]:.0f}–{b[3]:.0f}, Y {b[1]:.0f}–{b[4]:.0f}, объём {m.volume() / 1000:.1f} см³, поверхность {area / 100:.0f} см², кусков {len(m.decompose())}, {m.status().name}')
        raise SystemExit
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
    # прогон сверху до посадки: прищепка закрыта, пока зубцы выше перегородки, ниже сжата
    tip_seated = PEDESTAL_Z + TX_GAP + TX_L - CLIP_TOP - CLIP_L
    start = BOX_H + 1.0 - tip_seated
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
    overhangs('бокс вверх дном', p['box'].rotate([180, 0, 0]))
    overhangs('голова юбкой вниз', p['head'])
    overhangs('ручка хвостовиком вниз', p['handle'].rotate([180, 0, 0]))
    print('вся длина', round(p['head'].bounding_box()[5] - p['handle'].bounding_box()[2], 1))
