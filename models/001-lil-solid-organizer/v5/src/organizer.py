"""Органайзер v4: 4 × lil SOLID 3.0 (стоят на ребре, индикатор вверх) + 2 пачки HEETS + чистилка.
Все размеры в мм. X — слева направо, Y — от себя (перед = 0), Z — вверх.

python3 organizer.py          -> полная деталь  lil_solid_organizer_v4.3mf
python3 organizer.py test     -> пробник на 2 ложа lil_solid_test_v4.3mf
"""
import sys
import zipfile
import numpy as np
from manifold3d import Manifold, CrossSection, JoinType

# ---------- параметры ----------
CLR = 0.4                      # зазор на сторону по ширине (проверено пробником)
CLR_L = 1.0                    # зазор на сторону по длине (было 0.4 — туго)
FLOOR = 2.0                    # толщина дна
N_DEV = 4                      # сколько устройств

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


def u_scoop_y(xc, y0, y1, r, z_bottom):
    """U-образная выемка вдоль Y: скруглённое дно на z_bottom, открыта вверх."""
    zc = z_bottom + r
    length = y1 - y0
    return (cyl_y(xc, (y0 + y1) / 2, zc, r, length)
            + box(xc - r, y0, zc, xc + r, y1, H + 1))


def build(test=False):
    n = 2 if test else N_DEV
    # передний ряд пачек HEETS
    y_f0 = WALL
    y_f1 = y_f0 + heets_w
    rows_y0 = []
    y = y_f1 + PART
    for _ in range(n):
        rows_y0.append(y)
        y += slot_w + PART
    y_rows_end = rows_y0[-1] + slot_w

    if test:
        Wt = x_dev1 + WALL
        Dt = y_rows_end + WALL
        body = rrect(0, 0, Wt, Dt, OUTER_R, 0, H)
    else:
        y_h0 = y_rows_end + PART
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
    groove_end = (Dt + 1) if test else (y_rows_end + PART - 3.0)
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
    return model, (Wt, Dt, H)


def write_3mf(path, model, name):
    mesh = model.to_mesh()
    verts = np.asarray(mesh.vert_properties)[:, :3]
    tris = np.asarray(mesh.tri_verts)
    v = "\n".join(f'<vertex x="{a:.4f}" y="{b:.4f}" z="{c:.4f}"/>' for a, b, c in verts)
    t = "\n".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tris)
    model_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
<metadata name="Title">{name}</metadata>
<resources>
<object id="1" type="model" name="{name}">
<mesh><vertices>
{v}
</vertices><triangles>
{t}
</triangles></mesh>
</object>
</resources>
<build><item objectid="1"/></build>
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
    return verts, tris


if __name__ == "__main__":
    test = len(sys.argv) > 1 and sys.argv[1] == "test"
    model, (w, d, h) = build(test)
    fname = "lil_solid_test_v4.3mf" if test else "lil_solid_organizer_v4.3mf"
    verts, tris = write_3mf(fname, model, "lil SOLID test v4" if test else "lil SOLID organizer v4")
    np.savez("mesh_test.npz" if test else "mesh.npz", verts=verts, tris=tris)
    print(f"{fname}: {w:.1f} × {d:.1f} × {h:.1f} мм, объём {model.volume()/1000:.1f} см³, "
          f"genus {model.genus()}, статус {model.status()}")
