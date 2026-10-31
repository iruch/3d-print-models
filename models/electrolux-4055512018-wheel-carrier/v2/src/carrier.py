# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "manifold3d"]
# ///
"""Каретка с двумя колёсами для верхней корзины посудомоечной машины Electrolux, деталь 4055512018.
В файле для печати пластина с осями и два ролика рядом с ней.
Все размеры в мм. X — вдоль детали (0 = скруглённый конец, дальше к крючку),
Y — поперёк (0 = середина), Z — по толщине (0 = задняя плоскость, плюс — к колёсам).

Как стоит в машине: вертикально, крючком вверх. Крючок надет на горизонтальную проволоку корзины,
пары стенок (усики) держат проволоку, направляющая проходит между колёсами.

uv run carrier.py                 -> деталь для печати: electrolux-4055512018-wheel-carrier.3mf
uv run carrier.py --filled        -> сцена для картинки: деталь, колёса, проволока, не для печати
uv run carrier.py --pose back     -> положение: print — стоя на скруглённом торце (по умолчанию),
                                     wheels — колёсами вверх, back — спинкой вверх
Без uv: pip install numpy manifold3d, дальше python вместо uv run.
"""
import sys
import zipfile
import numpy as np
from manifold3d import Manifold, CrossSection, FillRule, JoinType

# ---------- параметры: сняты с фото детали по рулетке, штангенциркулем не проверялись ----------
L_PLATE = 80.5                 # длина пластины без язычка и крючка
L_TOTAL = 91.0                 # длина вместе с крючком
W = 42.0                       # ширина пластины
T_RIM = 5.0                    # толщина пластины по краю
RIM = 1.4                      # толщина рёбер и бортика с обратной стороны
CORNER_R = 8.0                 # скругление углов со стороны скруглённого конца
POCKET_D = 3.2                 # глубина ячеек между рёбрами

PLATEAU_IN = 0.8               # площадка со стороны колёс: отступ от края
PLATEAU_T = 3.3                # и высота над краем
PLATEAU_END = 78.0             # где она заканчивается по длине
AXLE_CLEAR_D = 20.0            # круглый вырез в площадке вокруг оси

AXLE_X = (13.0, 60.0)          # оси колёс от скруглённого конца; между ними 47 мм
AXLE_D = 8.4                   # диаметр оси под отверстие колеса
AXLE_TOP = 21.5                # торец оси от задней плоскости
AXLE_HOLE_D = 3.4              # сквозное отверстие в оси
SLIT_W, SLIT_L = 1.6, 9.0      # прорезь в оси: ширина и глубина от торца
BARB_D, BARB_H = 9.4, 1.5      # защёлка на конце оси: диаметр и высота
SEAT_Z = T_RIM + PLATEAU_T + 1.5   # отсюда начинается колесо
CONE_D0, CONE_D1 = 15.0, 10.0  # конус в основании оси
FIN_T, FIN_R = 1.4, 8.5        # четыре ребра вокруг конуса: толщина и вылет
DISH_D, DISH_RING_D, DISH_DEPTH = 15.6, 18.6, 6.5   # чаша за осью с обратной стороны

LIP_W = 27.0                   # язычок с крючком на торце: ширина
LIP_T = 1.4                    # толщина
LIP_DROP = 6.5                 # насколько крючок загибается к колёсам
HOOK_R = 1.6                   # внутренний радиус крючка

# Усики: четыре пары стенок. Зацепы стоят на обеих стенках пары и смотрят навстречу друг другу.
# Литые усики в FDM не работают: стенка 1.2 мм и зазор 1.2 мм ломаются ещё при установке.
# Здесь стенки толще и зацепы меньше, а сквозные окна и полукруглые прорези стоят как на оригинале.
CLIP_X = (17.0, 27.0)          # окно и пара стенок у скруглённого конца: от и до по длине
CLIP_H = 4.1                   # высота над задней плоскостью
RIB_Y = (14.2, 15.4)           # продольное ребро
INNER_Y = 13.4                 # внутренняя стенка пары: от INNER_Y до RIB_Y[1], 2.0 мм
OUTER_Y = 19.2                 # наружная стенка пары: от OUTER_Y до края, 1.8 мм
WIRE_NOM = 3.0                 # диаметр проволоки в клипсе: оценка, штангенциркулем не мерили
BARB_SNAP = 0.5                # насколько зазор между зацепами меньше проволоки у рабочей пары
FLAP_SNAP = 0.2                # то же у пары возле крючка: она рядом с крючком и почти не гнётся
BARB_GAP = 2.0                 # от задней плоскости до упора зацепа
NOTCH_W, NOTCH_D = 2.2, 1.9    # полукруглые прорези по бокам наружной стенки: ширина и глубина
SLOPE_Z = NOTCH_D - NOTCH_W / 2   # отсюда нижний по печати угол стенки идёт под 45°, чтобы не нужна была поддержка
FLOOR_Z = POCKET_D             # дно ячеек: сюда доходит утолщение внутренней стенки
WINDOW_Y = (14.9, 19.3)        # отверстие со стороны колёс: закрытое, вокруг него площадка, как на оригинале
FLAP_X = (81.5, 84.8)          # пара у крючка: где стоят зацепы
FLAP_H = (4.5, 3.1)            # высота: скошена, выше со стороны пластины
STUB_X = (69.6, 71.0)          # низкая поперечная стенка перед ячейкой у крючка
STUB_H = 1.8
TIE_X = (44.6, 45.4)           # тонкая перемычка поперёк бокового канала
RING_X = 37.0                  # кольцо посередине спинки
RING_D, RING_HOLE_D = 7.5, 4.6 # его наружный диаметр и отверстие
PIN_X = (25.7, 48.6, 71.8)     # следы от выталкивателей на центральном ребре
PIN_D = 2.2

# Буква F со стороны колёс. На оригинале две одинаковые буквы: вторая сдвинута, а не отзеркалена.
# Размеры сняты с фото оригинала рядом с напечатанной v1, масштаб взят по v1.
F_X0, F_L = 33.4, 12.5         # начало от скруглённого конца и длина буквы
F_Y = (2.1, -10.1)             # край каждой буквы со стороны длинной перекладины
F_W, F_STEM = 6.5, 3.1         # ширина буквы и толщина её стойки
F_TOOTH, F_TOOTH_X = 1.4, (4.5, 6.85)   # короткая перекладина: вылет и где стоит от начала буквы
F_FOOT_L = 3.35                # длинная перекладина: ширина
F_H = 0.3                      # высота рельефа: как на напечатанной v1, там буквы хорошо читаются
RIB_X = (23.0, 50.0)           # продольное ребро между колёсами, от выреза до выреза

# ролик: контур снят с фото, отверстие подогнано под напечатанную ось
WHEEL_D, WHEEL_RIM_H, WHEEL_HUB_D, WHEEL_HUB_H = 25.0, 7.0, 13.7, 5.0
WHEEL_BORE_D = AXLE_D + 0.5    # отверстие: зазор, чтобы ролик свободно крутился
WHEEL_CBORE_D = BARB_D + 1.2   # выборка на торце под защёлку оси
WHEEL_CBORE_H = 2.3            # её глубина; остаётся осевой люфт около 0.5 мм
WHEEL_PRINT_X = 60.0           # где ролики лежат на столе: в стороне от каретки и её поддержек
WHEEL_PRINT_Y = 16.0

# только для картинки: проволока корзины, направляющая
WIRE_D = 3.0                   # проволока: по радиусу крючка
WIRE_Y = 17.5                  # две проволоки вдоль детали
RAIL_H = 20.0                  # направляющая между колёсами
BODY_COLOR, WHEEL_COLOR, WIRE_COLOR, RAIL_COLOR = None, "#5d636e", "#d9822b", "#8d99a8"

HOOK_X = L_TOTAL - LIP_T - HOOK_R   # центр крючка


def rrect(x0, y0, w, h, r, z0, z1):
    """Скруглённый прямоугольник, выдавленный от z0 до z1."""
    r = min(r, w / 2 - 0.01, h / 2 - 0.01)
    cs = (CrossSection.square([w - 2 * r, h - 2 * r]).translate([r, r])
          .offset(r, JoinType.Round, circular_segments=48))
    return Manifold.extrude(cs, z1 - z0).translate([x0, y0, z0])


def box(x0, y0, z0, x1, y1, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def cyl(x, y, z0, z1, d, d1=None):
    h = z1 - z0
    return Manifold.cylinder(h, d / 2, (d1 if d1 is not None else d) / 2, circular_segments=64).translate([x, y, z0])


def extrude_xz(points, y0, y1):
    """Контур в координатах (x, z), вытянутый вдоль Y от y0 до y1."""
    cs = CrossSection([points], FillRule.EvenOdd)
    return Manifold.extrude(cs, y1 - y0).rotate([90, 0, 0]).translate([0, y1, 0])


def extrude_yz(points, x0, x1):
    """Контур в координатах (y, z), вытянутый вдоль X от x0 до x1."""
    cs = CrossSection([points], FillRule.EvenOdd)
    return Manifold.extrude(cs, x1 - x0).rotate([90, 0, 90]).translate([x0, 0, 0])


def both(m):
    """Деталь симметрична поперёк: то же самое с другой стороны."""
    return m + m.mirror([0, 1, 0])


def barb(y_root, sign, x0, x1, tip_z, depth):
    """Зацеп на стенке: со стороны пластины упор, с другой длинный скос для заезда."""
    body = extrude_yz([(y_root, -BARB_GAP), (y_root + sign * depth, -BARB_GAP - 0.2), (y_root, tip_z)], x0, x1)
    d = 1.5 * depth    # нижний по печати торец скошен под 45°, чтобы висеть не над пустотой
    wedge = CrossSection([[(x0 - 0.05, y_root), (x0 + d, y_root + sign * d), (x0 - 0.05, y_root + sign * d)]], FillRule.EvenOdd)
    return body - Manifold.extrude(wedge, 12).translate([0, 0, -11])


def notch(x0, x1, y0, y1, d=NOTCH_D):
    """Прорезь с полукруглым дном, идущая вдоль Y."""
    r = (x1 - x0) / 2
    return (box(x0, y0, -1, x1, y1, d - r)
            + Manifold.cylinder(y1 - y0, r, circular_segments=32).rotate([-90, 0, 0])
            .translate([x0 + r, y0, d - r]))


def wall(y0, y1, x_tip0, x_tip1, tip_z0, tip_z1):
    """Стенка клипсы. Нижний по печати край идёт под 45°, поэтому поддержка не нужна."""
    apex = x_tip0 - tip_z0 - FLOOR_Z
    pts = [(apex, T_RIM), (x_tip1, T_RIM), (x_tip1, -tip_z1), (x_tip0, -tip_z0), (apex, FLOOR_Z)]
    return extrude_xz(pts, y0, y1)


def letter_f(y0):
    """Буква F, если смотреть со стороны колёс крючком вверх. y0 — край со стороны длинной перекладины."""
    y1, ys = y0 + F_W, y0 + F_W - F_STEM
    yt = ys - F_TOOTH
    x0, x1 = F_X0, F_X0 + F_L
    return [(x0, ys), (x0, y1), (x1, y1), (x1, y0), (x1 - F_FOOT_L, y0), (x1 - F_FOOT_L, ys),
            (x0 + F_TOOTH_X[1], ys), (x0 + F_TOOTH_X[1], yt), (x0 + F_TOOTH_X[0], yt), (x0 + F_TOOTH_X[0], ys)]


def back_cells():
    """Ячейки между рёбрами с обратной стороны."""
    rows = ((RIB_Y[1], W / 2 - RIM, ((1.0, 15.4), (28.6, TIE_X[0]), (TIE_X[1], STUB_X[0]), (STUB_X[1], 79.6))),
            (9.8, RIB_Y[0], ((1.0, 12.5), (14.0, 36.0), (38.0, 62.0), (63.5, 79.6))),
            (0.7, 8.9, ((1.0, 36.0), (38.0, 79.6))))
    cells = None
    for y0, y1, spans in rows:
        for x0, x1 in spans:
            c = rrect(x0, y0, x1 - x0, y1 - y0, 1.0, -1, POCKET_D)
            cells = c if cells is None else cells + c
    inner = rrect(RIM, -W / 2 + RIM, 2 * L_PLATE, W - 2 * RIM, CORNER_R - RIM, -2, POCKET_D + 1)
    cells = both(cells) ^ inner
    for x in AXLE_X:
        cells = cells - cyl(x, 0, -2, POCKET_D + 1, DISH_RING_D)
    return cells - cyl(RING_X, 0, -2, POCKET_D + 1, RING_D)


def axle(x):
    """Ось: круглая, с конусом и четырьмя рёбрами в основании и защёлкой на конце."""
    fin = extrude_xz([(-FIN_R, T_RIM - 0.5), (FIN_R, T_RIM - 0.5), (FIN_R, T_RIM), (CONE_D1 / 2, SEAT_Z), (-CONE_D1 / 2, SEAT_Z),
                      (-FIN_R, T_RIM)], -FIN_T / 2, FIN_T / 2)
    return (cyl(x, 0, T_RIM - 0.5, SEAT_Z, CONE_D0, CONE_D1)
            + fin.translate([x, 0, 0]) + fin.rotate([0, 0, 90]).translate([x, 0, 0])
            + cyl(x, 0, T_RIM, AXLE_TOP, AXLE_D)
            + cyl(x, 0, AXLE_TOP - BARB_H, AXLE_TOP - 0.7, AXLE_D, BARB_D)
            + cyl(x, 0, AXLE_TOP - 0.7, AXLE_TOP, BARB_D, AXLE_D - 0.4))


def build():
    plate = (rrect(0, -W / 2, L_PLATE + 2 * CORNER_R, W, CORNER_R, 0, T_RIM)
             - box(L_PLATE, -W, -1, L_PLATE + 3 * CORNER_R, W, T_RIM + 1))
    z_top = T_RIM + PLATEAU_T
    plateau = (rrect(PLATEAU_IN, -W / 2 + PLATEAU_IN, PLATEAU_END, W - 2 * PLATEAU_IN, CORNER_R - PLATEAU_IN,
                     T_RIM - 0.5, z_top)
               - box(PLATEAU_END, -W, 0, PLATEAU_END + 20, W, z_top + 1))
    for x in AXLE_X:
        plateau = plateau - cyl(x, 0, T_RIM, z_top + 1, AXLE_CLEAR_D)

    # язычок вдоль задней плоскости, загнутый в крючок к колёсам
    r = HOOK_R
    arc = [(HOOK_X + (r + LIP_T) * np.sin(a), LIP_T + r - (r + LIP_T) * np.cos(a)) for a in np.linspace(0, np.pi / 2, 12)]
    arc_in = [(HOOK_X + r * np.sin(a), LIP_T + r - r * np.cos(a)) for a in np.linspace(np.pi / 2, 0, 12)]
    lip_pts = ([(L_PLATE - 4.0, 0.0)] + arc + [(L_TOTAL, LIP_DROP), (L_TOTAL - LIP_T - 0.8, LIP_DROP),
                                               (L_TOTAL - LIP_T - 0.8, LIP_DROP - 0.8), (L_TOTAL - LIP_T, LIP_DROP - 1.4)]
               + arc_in + [(L_PLATE - 4.0, LIP_T)])
    lip = extrude_xz(lip_pts, -LIP_W / 2, LIP_W / 2)

    model = plate + plateau + lip - back_cells()

    # пара у скруглённого конца: сквозное окно, у наружной стенки полукруглые прорези по бокам,
    # на обеих стенках зацепы, смотрящие навстречу друг другу
    x0, x1 = CLIP_X
    outer = W / 2 - RIM
    gap = OUTER_Y - RIB_Y[1]
    barb_y = (gap - (WIRE_NOM - BARB_SNAP)) / 2
    flap_y = (gap - (WIRE_NOM - FLAP_SNAP)) / 2
    x_tip = x0 + SLOPE_Z + CLIP_H
    model = model - both(box(x0, RIB_Y[1], -6, x1, OUTER_Y, z_top + 1))
    model = model - both(notch(x0 - NOTCH_W, x0, OUTER_Y, W / 2 + 1) + notch(x1, x1 + NOTCH_W, OUTER_Y, W / 2 + 1))
    outline = [(x0, T_RIM), (x1, T_RIM), (x1, -CLIP_H), (x_tip, -CLIP_H), (x0, SLOPE_Z)]
    barbs = (barb(RIB_Y[1], 1, x0, x1, -CLIP_H, barb_y) + barb(OUTER_Y, -1, x0, x1, -CLIP_H, barb_y)) ^ extrude_xz(outline, 0, W)
    model = model + both(extrude_xz(outline, OUTER_Y, W / 2)
                         + wall(INNER_Y, RIB_Y[1], x_tip, x1, CLIP_H, CLIP_H)
                         + extrude_yz([(INNER_Y, FLOOR_Z), (INNER_Y - 1.2, FLOOR_Z), (INNER_Y, FLOOR_Z - 1.2)], x0 - 1.2, x1)
                         + barbs)
    model = model - both(box(x0, WINDOW_Y[0], FLOOR_Z, x1, WINDOW_Y[1], z_top + 1))

    # пара у крючка: стенки выросли из пластины, а не висят на тонкой полоске,
    # внутренняя стенка срослась с язычком, между стенками сквозной просвет
    fx0, fx1 = FLAP_X
    fh0, fh1 = FLAP_H
    fy = (OUTER_Y, W / 2), (INNER_Y, RIB_Y[1])
    model = model + both(wall(*fy[0], fx0, fx1, fh0, fh1) + wall(*fy[1], fx0, fx1, fh0, fh1)
                         + barb(RIB_Y[1], 1, fx0, fx1, -fh1, flap_y) + barb(OUTER_Y, -1, fx0, fx1, -fh1, flap_y))

    # низкая поперечная стенка
    model = model + both(box(STUB_X[0], RIB_Y[1], -STUB_H, STUB_X[1], outer, 1.0))

    # центральное кольцо, тонкое ребро и рельефные значки со стороны колёс
    model = model + cyl(RING_X, 0, 0, POCKET_D + 0.5, RING_D) - cyl(RING_X, 0, -1, POCKET_D, RING_HOLE_D)
    for x in PIN_X:
        model = model + cyl(x, 0, 0, POCKET_D + 0.5, PIN_D)
    model = model + box(RIB_X[0], -0.5, z_top - 0.2, RIB_X[1], 0.5, z_top + 0.6) + box(72.0, -0.5, z_top - 0.2, 78.0, 0.5, z_top + 0.6)
    for y in F_Y:
        model = model + Manifold.extrude(CrossSection([letter_f(y)], FillRule.EvenOdd), F_H + 0.1).translate([0, 0, z_top - 0.1])

    for x in AXLE_X:
        model = model + axle(x)
        # чаша с обратной стороны, сквозное отверстие и прорезь
        model = model - cyl(x, 0, -0.01, DISH_DEPTH, DISH_D, AXLE_HOLE_D)
        model = model - cyl(x, 0, -1, AXLE_TOP + 1, AXLE_HOLE_D)
        model = model - box(x - BARB_D, -SLIT_W / 2, AXLE_TOP - SLIT_L, x + BARB_D, SLIT_W / 2, AXLE_TOP + 1)
    return model


def wheel_body():
    """Ролик: ступица и обод, вращение контура вокруг оси. Ступица смотрит вниз, к пластине.
    На торце обода только скосы 45°, без плоских ступенек: на столе этот торец внизу, и поддержка не нужна."""
    r_hub, r_rim, c = WHEEL_HUB_D / 2, WHEEL_D / 2, 1.8
    h = WHEEL_HUB_H + WHEEL_RIM_H
    r_bore, r_cbore = WHEEL_BORE_D / 2, WHEEL_CBORE_D / 2
    cone = r_cbore - r_bore
    pts = [(r_bore, 0), (r_hub, 0), (r_hub, WHEEL_HUB_H), (r_rim - c, WHEEL_HUB_H), (r_rim, WHEEL_HUB_H + c),
           (r_rim, h - c), (r_rim - c, h), (r_hub + 1.2, h), (r_hub + 0.3, h - 0.9),
           (r_hub - 0.6, h), (r_cbore, h), (r_cbore, h - WHEEL_CBORE_H + cone), (r_bore, h - WHEEL_CBORE_H)]
    return Manifold.revolve(CrossSection([pts], FillRule.EvenOdd), 96)


def wheel(x):
    """Ролик на оси, для картинки."""
    return wheel_body().translate([x, 0, SEAT_Z])


def wheel_on_bed(y):
    """Ролик на столе: ободом вниз, ступицей вверх, так он печатается без поддержек."""
    h = WHEEL_HUB_H + WHEEL_RIM_H
    return wheel_body().rotate([180, 0, 0]).translate([WHEEL_PRINT_X, y, h])


def basket():
    """Как деталь стоит в машине, только для картинки: проволока корзины и направляющая между колёсами."""
    z_h = LIP_T + WIRE_D / 2
    wires = (Manifold.cylinder(120, WIRE_D / 2, circular_segments=32).rotate([-90, 0, 0])
             .translate([HOOK_X, -60, z_h]))
    length = HOOK_X - 6.0
    for side in (1, -1):
        wires = wires + (Manifold.cylinder(length, WIRE_D / 2, circular_segments=32).rotate([0, 90, 0])
                         .translate([6.0, side * WIRE_Y, z_h - WIRE_D]))
    rail_x = sum(AXLE_X) / 2
    rail = box(rail_x - RAIL_H / 2, -60, SEAT_Z + WHEEL_HUB_H, rail_x + RAIL_H / 2, 60, SEAT_Z + WHEEL_HUB_H + WHEEL_RIM_H)
    return [("basket-wires", wires, WIRE_COLOR), ("rail", rail, RAIL_COLOR)]


def pose(model, name):
    """Положение детали в файле."""
    if name == "back":        # спинкой вверх
        return model.rotate([180, 0, 0]).translate([0, 0, 40])
    if name == "wheels":      # колёсами вверх
        return model.translate([0, 0, 10])
    return model.rotate([0, -90, 0])   # стоя на скруглённом торце


def write_3mf(path, parts, title):
    """parts — список (имя, Manifold, цвет '#RRGGBB' или None). Цвета нужны только картинкам."""
    colored = [(name, color) for name, _, color in parts if color]
    resources, items = [], []
    if colored:
        resources.append('<basematerials id="1">\n' + "\n".join(
            f'<base name="{name}" displaycolor="{color}"/>' for name, color in colored) + "\n</basematerials>")
    pindex = 0
    for i, (name, model, color) in enumerate(parts):
        oid = i + 2 if colored else i + 1
        mesh = model.to_mesh()
        verts = np.asarray(mesh.vert_properties)[:, :3]
        tris = np.asarray(mesh.tri_verts)
        v = "\n".join(f'<vertex x="{a:.4f}" y="{b:.4f}" z="{c:.4f}"/>' for a, b, c in verts)
        t = "\n".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tris)
        mat = ""
        if color:
            mat = f' pid="1" pindex="{pindex}"'
            pindex += 1
        resources.append(f'''<object id="{oid}" type="model" name="{name}"{mat}>
<mesh><vertices>
{v}
</vertices><triangles>
{t}
</triangles></mesh>
</object>''')
        items.append(f'<item objectid="{oid}"/>')
    resources_xml = "\n".join(resources)
    model_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
<metadata name="Title">{title}</metadata>
<resources>
{resources_xml}
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
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model_xml)


if __name__ == "__main__":
    args = sys.argv[1:]
    filled = "--filled" in args
    args = [a for a in args if a != "--filled"]
    pose_name = "print"
    if "--pose" in args:
        i = args.index("--pose")
        pose_name = args[i + 1]
        del args[i:i + 2]
    name = "electrolux-4055512018-wheel-carrier"
    if filled:
        name += "-filled"
    fname = args[0] if args else f"{name}.3mf"
    model = build()
    parts = [(name, pose(model, pose_name), BODY_COLOR)]
    if filled:
        parts += [(f"wheel-{i + 1}", pose(wheel(x), pose_name), WHEEL_COLOR) for i, x in enumerate(AXLE_X)]
        parts += [(n, pose(m, pose_name), c) for n, m, c in basket()]
    elif pose_name == "print":
        parts += [(f"wheel-{i + 1}", wheel_on_bed(y), None) for i, y in enumerate((WHEEL_PRINT_Y, -WHEEL_PRINT_Y))]
    write_3mf(fname, parts, name)
    print(f"{fname}: объём {model.volume()/1000:.1f} см³, кусков {len(model.decompose())}, "
          f"genus {model.genus()}, статус {model.status()}")
