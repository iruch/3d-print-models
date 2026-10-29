# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "manifold3d"]
# ///
"""Органайзер: N × lil SOLID 3.0 (стоят на ребре, индикатор вверх) + 4 пачки HEETS + чистилка.
Все размеры в мм. X — слева направо, Y — от себя (перед = 0), Z — вверх.

uv run organizer.py 4            -> вариант на 4 устройства: lil-solid-organizer-4-devices.3mf
uv run organizer.py 3 out.3mf    -> вариант на 3 устройства в указанный файл
uv run organizer.py test         -> пробник посадки на 2 ложа и пачку: lil-solid-organizer-fit-test.3mf
uv run organizer.py 4 --filled   -> сцена для картинки: органайзер с устройствами, пачками,
                                    чистилкой и кабелем, у каждой детали свой цвет.
                                    Не для печати! Файл: lil-solid-organizer-4-devices-filled.3mf
Без uv: pip install numpy manifold3d, дальше python вместо uv run.
"""
import sys
import zipfile
import numpy as np
from manifold3d import Manifold, CrossSection, JoinType

# ---------- параметры ----------
CLR = 0.4                      # зазор на сторону по ширине (проверено пробником)
CLR_L = 1.0                    # зазор на сторону по длине (было 0.4 — туго)
FLOOR = 2.0                    # толщина дна
N_DEV = 4                      # сколько устройств, если не задано в командной строке

DEV_L, DEV_W, DEV_T = 105.8, 30.8, 21.4          # lil SOLID: длина, ширина, толщина
# устройство на ребре: в плане занимает DEV_L × DEV_T, в высоту DEV_W
H = FLOOR + DEV_W + 0.2                          # бокс высотой с устройство

HEETS_W, HEETS_T = 75.0, 15.0                    # пачка стоит гранью 75×15 (проверено)
HEETS_DEPTH = 22.0                               # глубина кармана под пачку (проверено)
CLEAN_L, CLEAN_D = 80.0, 17.0                    # чистилка (проверено)

# Type-C на торце: ближе к грани с индикатором, по центру толщины
PORT_FROM_TOP = 7.5                              # центр порта от верхней (индикаторной) грани
PLUG_L, PLUG_W = 25.0, 14.0                      # карман под штекер: длина вдоль X, ширина по Y
PLUG_BELOW = 6.0                                 # карман уходит ниже центра порта на столько
CABLE_W, CABLE_BELOW = 6.0, 3.5                  # прорезь под кабель в торцевой стенке
WALL, PART = 3.0, 12.0                           # наружная стенка, перегородка между рядами
OUTER_R = 8.0                                    # скругление углов бокса
SLOT_R = 3.0                                     # скругление углов ложа в плане

slot_l, slot_w = DEV_L + 2 * CLR_L, DEV_T + 2 * CLR
HEETS_CLR = 1.4                                  # зазор на сторону под пачку (было 0.4 — туго)
heets_l, heets_w = HEETS_W + 2 * HEETS_CLR, HEETS_T + 2 * HEETS_CLR
clean_l, clean_w = CLEAN_L + 2 * 0.5, CLEAN_D + 2 * 0.5

port_zc = FLOOR + DEV_W - PORT_FROM_TOP

# ---------- раскладка ----------
x_plug0 = WALL
x_dev0 = x_plug0 + PLUG_L
x_dev1 = x_dev0 + slot_l
x_cl0 = x_dev1 + 6.4
x_cl1 = x_cl0 + clean_w
W = max(x_cl1 + 4.0, 2 * heets_l + WALL + 2 * 3.5)   # пачки не должны съедать боковые стенки

# ---------- содержимое: только для картинки «с содержимым», на печать не влияет ----------
DEV_R = 6.0                                      # скругление продольных рёбер устройства (на глаз)
DEV_CAP_L = 16.0                                 # торцевая крышка устройства справа
BUTTON_AT = 66.0                                 # кнопка-индикатор: расстояние от левого торца
HEETS_H = 52.0                                   # высота пачки (примерно)
HEETS_LID_H = 13.0                               # цветная крышка пачки
CLEAN_CAP_L = 22.0                               # цветной колпачок чистилки
CABLE_R = 2.0                                    # кабель зарядки
DEV_COLORS = ["#2f3a5a", "#7a5c66", "#2e3138", "#5d636e"]
DEV_CAP_COLOR, BUTTON_COLOR = "#a3a9b2", "#dfe3e8"
PACK_COLOR, PACK_LID_COLORS = "#eef1f3", ["#1d9fa3"]
CLEAN_COLOR, CLEAN_CAP_COLOR = "#2b2d31", "#f2701f"
CABLE_COLOR = "#e39ab0"


def rrect(x0, y0, w, h, r, z0, z1):
    """Скруглённый прямоугольник, выдавленный от z0 до z1."""
    r = min(r, w / 2 - 0.01, h / 2 - 0.01)
    cs = CrossSection.square([w - 2 * r, h - 2 * r]).translate([r, r])
    if r > 0:
        cs = cs.offset(r, JoinType.Round, circular_segments=48)
    return Manifold.extrude(cs, z1 - z0).translate([x0, y0, z0])


def box(x0, y0, z0, x1, y1, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def cyl_x(xc, yc, zc, r, length):
    return (Manifold.cylinder(length, r, circular_segments=96)
            .rotate([0, 90, 0]).translate([xc - length / 2, yc, zc]))


def cyl_y(xc, yc, zc, r, length):
    return (Manifold.cylinder(length, r, circular_segments=96)
            .rotate([-90, 0, 0]).translate([xc, yc - length / 2, zc]))


def cyl_z(xc, yc, z0, z1, r):
    return Manifold.cylinder(z1 - z0, r, circular_segments=48).translate([xc, yc, z0])


def bar_x(x0, x1, yc, zc, w, h, r):
    """Брусок вдоль X со скруглёнными продольными рёбрами: сечение w (по Y) × h (по Z)."""
    cs = (CrossSection.square([h - 2 * r, w - 2 * r]).translate([r - h / 2, r - w / 2])
          .offset(r, JoinType.Round, circular_segments=48))
    return Manifold.extrude(cs, x1 - x0).rotate([0, 90, 0]).translate([x0, yc, zc])


def u_scoop_y(xc, y0, y1, r, z_bottom):
    """U-образная выемка вдоль Y: скруглённое дно на z_bottom, открыта вверх."""
    zc = z_bottom + r
    length = y1 - y0
    return (cyl_y(xc, (y0 + y1) / 2, zc, r, length)
            + box(xc - r, y0, zc, xc + r, y1, H + 1))


def build(n=N_DEV, test=False):
    """n — сколько устройств; test — пробник на 2 ложа без задних пачек и чистилки."""
    if test:
        n = 2
    # передний ряд пачек HEETS
    y_f0 = WALL
    y_f1 = y_f0 + heets_w
    # на 2 устройства ряд лож короче чистилки — раздвигаем ряды пачек, чтобы она влезла
    rows_len = n * slot_w + (n - 1) * PART
    extra = 0.0 if test else max(0.0, clean_l + 2 * WALL - (rows_len + 2 * PART))
    rows_y0 = []
    y = y_f1 + PART + extra / 2
    for _ in range(n):
        rows_y0.append(y)
        y += slot_w + PART
    y_rows_end = rows_y0[-1] + slot_w

    if test:
        Wt = x_dev1 + WALL
        Dt = y_rows_end + WALL
        body = rrect(0, 0, Wt, Dt, OUTER_R, 0, H)
    else:
        y_h0 = y_rows_end + PART + extra / 2
        y_h1 = y_h0 + heets_w
        Dt = y_h1 + WALL
        Wt = W
        body = rrect(0, 0, Wt, Dt, OUTER_R, 0, H)

    cuts = []
    for y0 in rows_y0:
        yc = y0 + slot_w / 2
        cuts.append(rrect(x_dev0, y0, slot_l, slot_w, SLOT_R, FLOOR, H + 1))
        # карман под штекер: только верхняя часть, где порт
        cuts.append(rrect(x_plug0, yc - PLUG_W / 2, PLUG_L + 2, PLUG_W, 2.0,
                          port_zc - PLUG_BELOW, H + 1))
        # прорезь под кабель через торцевую стенку
        cuts.append(box(-1, yc - CABLE_W / 2, port_zc - CABLE_BELOW,
                        x_plug0 + 1, yc + CABLE_W / 2, H + 1))

    # выемка для пальцев поперёк всех рядов у правых концов устройств
    groove_x = x_dev1 - 20.0
    groove_end = (Dt + 1) if test else (y_rows_end + PART + extra / 2 - 3.0)
    cuts.append(u_scoop_y(groove_x, y_f1 + 3.0, groove_end, 15.0, FLOOR + 6.0))

    heets_total = 2 * heets_l + 3 * WALL
    hx0 = (W - heets_total) / 2 + WALL
    hxs = (hx0, hx0 + heets_l + WALL)
    # передние пачки (в пробнике одна — проверить подход к устройствам)
    for hx in (hxs[:1] if test else hxs):
        cuts.append(rrect(hx, y_f0, heets_l, heets_w, 3.0, H - HEETS_DEPTH, H + 1))

    if not test:
        for hx in hxs:
            cuts.append(rrect(hx, y_h0, heets_l, heets_w, 3.0, H - HEETS_DEPTH, H + 1))

        clean_y0 = (rows_y0[0] + y_rows_end) / 2 - clean_l / 2   # по центру между пачками
        clean_floor = H - (CLEAN_D + 1.5)
        cuts.append(rrect(x_cl0, clean_y0, clean_w, clean_l, clean_w / 2, clean_floor, H + 1))
        cuts.append(cyl_x((x_cl0 + x_cl1) / 2, clean_y0 + clean_l / 2,
                          clean_floor + 16.0, 16.0, clean_w + 14))

    model = body
    for c in cuts:
        model = model - c
    layout = {"rows_y0": rows_y0, "hxs": hxs[:1] if test else hxs, "packs_y0": (y_f0,) if test else (y_f0, y_h0),
              "clean_y0": None if test else clean_y0, "clean_floor": None if test else clean_floor}
    return model, (Wt, Dt, H), layout


def contents(layout):
    """Содержимое органайзера для картинки: список (имя, Manifold, цвет)."""
    parts = []
    for i, y0 in enumerate(layout["rows_y0"]):
        yc = y0 + slot_w / 2
        x0, x1 = x_dev0 + CLR_L, x_dev1 - CLR_L
        zc = FLOOR + DEV_W / 2
        parts.append((f"device-{i + 1}", bar_x(x0, x1 - DEV_CAP_L, yc, zc, DEV_T, DEV_W, DEV_R),
                      DEV_COLORS[i % len(DEV_COLORS)]))
        parts.append((f"device-{i + 1}-cap", bar_x(x1 - DEV_CAP_L, x1, yc, zc, DEV_T, DEV_W, DEV_R),
                      DEV_CAP_COLOR))
        top = FLOOR + DEV_W
        parts.append((f"device-{i + 1}-button",
                      rrect(x0 + BUTTON_AT - 3.25, yc - 3.25, 6.5, 6.5, 1.5, top - 0.3, top + 0.5),
                      BUTTON_COLOR))

    # кабель с штекером — в первом ложе, чтобы было видно, что устройство заряжается на месте
    yc = layout["rows_y0"][0] + slot_w / 2
    x_plug = x_dev0 + CLR_L
    x_out, x_end = -12.0, -40.0
    plug = bar_x(x_plug - 20.0, x_plug, yc, port_zc, 7.0, 11.5, 2.0)
    cable = (cyl_x((x_out + x_plug - 20.0) / 2, yc, port_zc, CABLE_R, x_plug - 20.0 - x_out)
             + Manifold.sphere(CABLE_R, 48).translate([x_out, yc, port_zc])
             + cyl_z(x_out, yc, CABLE_R, port_zc, CABLE_R)
             + Manifold.sphere(CABLE_R, 48).translate([x_out, yc, CABLE_R])
             + cyl_x((x_end + x_out) / 2, yc, CABLE_R, CABLE_R, x_out - x_end))
    parts += [("plug", plug, "#d8dbe0"), ("cable", cable, CABLE_COLOR)]

    z0 = H - HEETS_DEPTH
    k = 0
    for py in layout["packs_y0"]:
        for hx in layout["hxs"]:
            x0, y0 = hx + HEETS_CLR, py + HEETS_CLR
            parts.append((f"pack-{k + 1}",
                          rrect(x0, y0, HEETS_W, HEETS_T, 1.0, z0, z0 + HEETS_H - HEETS_LID_H),
                          PACK_COLOR))
            parts.append((f"pack-{k + 1}-lid",
                          rrect(x0, y0, HEETS_W, HEETS_T, 1.0, z0 + HEETS_H - HEETS_LID_H, z0 + HEETS_H),
                          PACK_LID_COLORS[k % len(PACK_LID_COLORS)]))
            k += 1

    if layout["clean_y0"] is not None:
        xc = (x_cl0 + x_cl1) / 2
        zc = layout["clean_floor"] + CLEAN_D / 2
        y0 = layout["clean_y0"] + 0.5
        body_l = CLEAN_L - CLEAN_CAP_L
        parts.append(("cleaner", cyl_y(xc, y0 + body_l / 2, zc, CLEAN_D / 2, body_l), CLEAN_COLOR))
        parts.append(("cleaner-cap", cyl_y(xc, y0 + body_l + CLEAN_CAP_L / 2, zc, CLEAN_D / 2, CLEAN_CAP_L),
                      CLEAN_CAP_COLOR))
    return parts


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
    arg = args[0] if args else str(N_DEV)
    test = arg == "test"
    n = 2 if test else int(arg)
    name = "lil-solid-organizer-fit-test" if test else f"lil-solid-organizer-{n}-devices"
    if filled:
        name += "-filled"
    fname = args[1] if len(args) > 1 else f"{name}.3mf"
    model, (w, d, h), layout = build(n, test)
    parts = [(name, model, None)]
    if filled:
        parts += contents(layout)
    write_3mf(fname, parts, name)
    print(f"{fname}: {w:.1f} × {d:.1f} × {h:.1f} мм, объём {model.volume()/1000:.1f} см³, "
          f"genus {model.genus()}, статус {model.status()}"
          + (f", деталей в сцене {len(parts)}" if filled else ""))
