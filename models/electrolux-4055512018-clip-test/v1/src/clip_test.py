# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "manifold3d"]
# ///
"""Пробник клипс для каретки Electrolux 4055512018: три рабочие пары с разным зазором и пара от крючка.
Пробник вырезан из самой каретки (carrier.py рядом), поэтому клипсы те же и печатаются так же, стоя.
Канал под проволоку здесь сквозной: пробник проверяет только клипсы, поэтому поперечные рёбра срезаны до дна ячеек.
Все размеры в мм, оси как в carrier.py: X — вдоль детали, Y — поперёк, Z — по толщине.

uv run clip_test.py            -> пробник для печати: electrolux-4055512018-clip-test.3mf
uv run clip_test.py --filled   -> сцена для картинки: пробник с проволокой, не для печати
Без uv: pip install numpy manifold3d, дальше python вместо uv run.
"""
import sys
from manifold3d import Manifold
import carrier as c

GAPS = (2.2, 2.5, 2.8)         # зазор между зацепами у рабочих пар; проволока толще него и разводит стенки
HOOK_GAP = 2.8                 # зазор у пары от крючка
X_LOW, X_TOP = 10.0, 31.0      # какой кусок каретки берём у рабочей пары
X_TOP_HOOK = 85.0              # где кончается кусок у крючка
HOOK_SHIFT = 56.0              # на столько сдвигаем кусок у крючка, чтобы он встал вровень
Y_IN = 11.4                    # внутренний край куска; наружный — край каретки
PITCH = 11.2                   # шаг пар поперёк пробника
SLAB_TOP = c.T_RIM + c.PLATEAU_T
MARK_W, MARK_D, MARK_L, MARK_STEP = 0.7, 0.5, 8.0, 1.2   # насечки: одна, две, три — номер рабочей пары
TIE_LOW, TIE_TOP = (X_LOW, 14.5), (29.2, X_TOP)   # перемычки между кусками: вне наружной стенки, чтобы не мешать ей пружинить


def channel(x0, x1):
    """Паз под проволоку между стенками, до дна ячеек."""
    return c.box(x0, c.RIB_Y[1], -8, x1, c.OUTER_Y, c.FLOOR_Z)


def piece(gap, hook=False):
    """Кусок каретки с одной парой клипс и сквозным каналом под проволоку."""
    c.BARB_SNAP = c.WIRE_NOM - gap
    c.FLAP_SNAP = c.WIRE_NOM - gap
    model = c.build()
    shift = HOOK_SHIFT if hook else 0.0
    top = X_TOP_HOOK if hook else X_TOP
    part = model ^ c.box(X_LOW + shift, Y_IN, -10, top, c.W / 2 + 1, SLAB_TOP + 1)
    # окно вокруг зацепов уже есть, здесь паз продлевается до краёв куска
    x0, x1 = c.FLAP_X if hook else c.CLIP_X
    part = part - channel(X_LOW + shift - 1, x0) - channel(x1, top + 1)
    if hook:   # остаток низкой поперечной стенки: к клипсам не относится
        part = part - c.box(c.STUB_X[0], c.RIB_Y[1], -6, c.STUB_X[1], c.W / 2 - c.RIM, 0)
    return part.translate([-shift, 0, 0])


def marks(n, dy):
    """Насечки на лицевой стороне: сверху открыты, поэтому печатаются без поддержек."""
    mid = (Y_IN + c.RIB_Y[1]) / 2 + dy
    y0 = mid - (n - 1) * MARK_STEP / 2
    cut = None
    for i in range(n):
        y = y0 + i * MARK_STEP
        m = c.box(X_TOP - MARK_L, y - MARK_W / 2, SLAB_TOP - MARK_D, X_TOP + 1, y + MARK_W / 2, SLAB_TOP + 1)
        cut = m if cut is None else cut + m
    return cut


def build():
    model = None
    for i, gap in enumerate(GAPS):
        dy = i * PITCH
        part = piece(gap).translate([0, dy, 0]) - marks(i + 1, dy)
        model = part if model is None else model + part
    last = len(GAPS)
    model = model + piece(HOOK_GAP, hook=True).translate([0, last * PITCH, 0])
    # перемычки между кусками стоят вне наружной стенки; кусок у крючка короче, он держится на нижней
    for i in range(last):
        for x0, x1 in (TIE_LOW, TIE_TOP) if i < last - 1 else (TIE_LOW,):
            model = model + c.box(x0, 19.4 + i * PITCH, c.FLOOR_Z, x1, Y_IN + (i + 1) * PITCH, SLAB_TOP)
    return model


def wires():
    """Проволока в каждой паре, только для картинки."""
    z = -c.BARB_GAP + c.WIRE_NOM / 2
    y = (c.RIB_Y[1] + c.OUTER_Y) / 2
    w = None
    for i in range(len(GAPS) + 1):
        one = (Manifold.cylinder(X_TOP - X_LOW + 12, c.WIRE_NOM / 2, circular_segments=32).rotate([0, 90, 0])
               .translate([X_LOW - 6, y + i * PITCH, z]))
        w = one if w is None else w + one
    return w


if __name__ == "__main__":
    args = sys.argv[1:]
    filled = "--filled" in args
    args = [a for a in args if a != "--filled"]
    name = "electrolux-4055512018-clip-test"
    if filled:
        name += "-filled"
    fname = args[0] if args else f"{name}.3mf"
    model = build()
    if filled:
        back = lambda m: m.rotate([180, 0, 0]).translate([0, 0, 12])
        parts = [(name, back(model), None), ("wire", back(wires()), c.WIRE_COLOR)]
    else:
        parts = [(name, model.translate([-X_LOW, 0, 0]).rotate([0, -90, 0]), None)]
    c.write_3mf(fname, parts, name)
    print(f"{fname}: объём {model.volume()/1000:.1f} см³, кусков {len(model.decompose())}, "
          f"genus {model.genus()}, статус {model.status()}")
