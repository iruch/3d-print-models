# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "manifold3d"]
# ///
"""Накладка на нижнюю кромку зеркала Evoform Ledline-S 60 × 75 (BY 2162) с полкой: закрывает сколы и трещины.

Схема автора. Три одинаковые по длине детали лежат вплотную к стеклу по всей ширине зеркала. В крайних деталях
есть окна под держатели полки. Во всех трёх деталях идёт разрез под полку. Штатная стеклянная полка ставится
обратно, поверх накладки: через разрез в свои держатели, до упора.

Как держится. Деталь лежит верхней кромкой разреза на полке: полка заходит в разрез на 2 мм. За задним краем
полки остаётся перемычка, она соединяет верх и низ детали и не даёт ей уйти вперёд. Назад деталь не пускает
стекло, вбок крайние детали держатся окнами на держателях. Клей, шпонки и винты не нужны. На стекло деталь не
давит, к треснувшему стеклу только прилегает. Внизу у детали дно, оно уходит под кромку стекла: если кусок
треснувшего стекла выпадет, дно его поймает.

Все размеры в мм. Откуда они:
  - автор, рулеткой и линейкой, 2026-11-05: ширина стекла 600; держатели 21 × 18 (ширина × высота), от бокового
    края стекла до ближнего края держателя 65, от нижней кромки до держателя 20; полка 8 × 596 × 130; полка
    до упора в держателе стоит в 5 мм от зеркала; за стеклом у кромки до коробки подсветки 3–4;
  - автор задал толщину: в разрезе 4–5, над полкой и под ней сначала 10, потом решил, что жирно, и попросил 7;
  - карточка товара: стекло 4, глубина зеркала 30, низ полос подсветки ≈113 над кромкой (чертёж похожей модели);
  - ОЦЕНКА: губки держателя по 5 мм (18 = 5 + 8 + 5), вылет держателя ≈21 (кадры видео, масштаб — рулетка).

Система координат сборки: X — вдоль зеркала (0 = левый край стекла), Y — к стене (лицо стекла Y = 0, комната
при Y < 0), Z — вверх (0 = нижняя кромка стекла). Для печати деталь кладётся лицом на стол.

uv run mirror_trim.py --part right|middle|left   -> evoform-ledline-s-mirror-trim-v1-<деталь>.3mf: деталь с подложкой
uv run mirror_trim.py --pose use                 -> три детали в сборе, без подложек: для картинок видов
uv run mirror_trim.py --filled                   -> сцена: стекло, держатели, полка, накладка; для filled.png
"""
import sys
import zipfile

import numpy as np
from manifold3d import CrossSection, JoinType, Manifold

# ---------- зеркало (замеры автора и карточка товара) ----------
СТЕКЛО_Ш = 600.0          # ширина стекла
СТЕКЛО_Т = 4.0            # толщина стекла (карточка)
ДО_СТЕНЫ = 30.0           # от лица стекла до стены: глубина изделия (карточка)
ПОДСВЕТКА_Z = 113.0       # низ полос подсветки над кромкой (чертёж похожей модели); накладка до них не доходит
ПОДСВЕТКА_X = (43.0, 63.0)  # полоса подсветки от бокового края

ДЕРЖ_Ш, ДЕРЖ_В = 21.0, 18.0   # держатель полки спереди: ширина × высота
ДЕРЖ_ОТ_КРАЯ = 65.0       # от бокового края стекла до ближнего края держателя
ДЕРЖ_Z = 20.0             # от нижней кромки до низа держателя
ДЕРЖ_ГУБКА = 5.0          # ОЦЕНКА: нижняя губка, на ней стоит полка
ДЕРЖ_ВЫЛЕТ = 21.0         # ОЦЕНКА по видео: насколько держатель торчит от стекла

ПОЛКА_Т, ПОЛКА_Д, ПОЛКА_Г = 8.0, 596.0, 130.0   # полка: толщина, длина, глубина
ПОЛКА_ОТ_СТЕКЛА = 5.0     # полка до упора в держателях стоит в 5 мм от зеркала
ПОЛКА_Z = ДЕРЖ_Z + ДЕРЖ_ГУБКА  # низ полки над кромкой

# ---------- накладка ----------
ТОЛЩИНА = 7.0             # над полкой и под ней (автор): полка заходит в разрез на ТОЛЩИНА − ПОЛКА_ОТ_СТЕКЛА = 2
ПЕРЕМЫЧКА = 4.5           # в разрезе (автор: 4–5): за краем полки остаётся 0,5 мм
РАЗРЕЗ_НИЗ = 1.0          # зазор под полкой; сверху зазора нет: деталь лежит на полке
ВЕРХ = 85.0               # верх накладки над кромкой: трещины на фото поднимаются примерно до 55
СКОС = ТОЛЩИНА            # верх скошен под 45° на всю толщину: вода и пыль скатываются, на столе печатается без поддержек
ДНО_ЗАЗОР = 3.0           # дно ниже кромки стекла: запас на неточность высоты полки, дно не упрётся в кромку
ДНО_Т = 2.5               # толщина дна
ДНО_ЗА_СТЕКЛО = 2.0       # дно выходит за стекло назад: ловит выпавший кусок по всей толщине стекла
ВЫХОД_ВБОК = 3.0          # за боковой край стекла: закрыть торцы; до стен ниши 1–2 см
ОКНО_ЗАЗОР = 1.5          # окно под держатель больше него на столько с каждой стороны
ПАЗ_Ш, ПАЗ_Г = 8.0, 3.0   # паз под отвёртку к стопорному винту снизу держателя: ширина, глубина от лица.
                          # Винт примерно посередине губки (≈10 от стекла), паз даёт запас, если он ближе к стеклу

# ---------- подложки (только в файлах для печати) ----------
ПОДЛОЖКА_Ш = 8.0          # ширина кольца вокруг пятна детали на столе
ПОДЛОЖКА_Н = 0.25         # толщина: только первый слой
ПОДЛОЖКА_ОТСТУП = 1.5     # от граней разреза и окон: верх разреза ложится на полку, остаток подложки помешает

СТОЛ = 220.0              # стол K1C, деталь кладётся по центру

ДЛИНА = (СТЕКЛО_Ш + 2 * ВЫХОД_ВБОК) / 3   # три детали одной длины
РАЗРЕЗ_Z0 = ПОЛКА_Z - РАЗРЕЗ_НИЗ
РАЗРЕЗ_Z1 = ПОЛКА_Z + ПОЛКА_Т
НИЗ = -ДНО_ЗАЗОР - ДНО_Т
ДЕРЖ_X = (ДЕРЖ_ОТ_КРАЯ, ДЕРЖ_ОТ_КРАЯ + ДЕРЖ_Ш)   # левый держатель; правый — зеркально


def box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))


def profile():
    """Сечение детали в плоскости YZ: лицо, скос сверху, дно под кромкой стекла."""
    t = ТОЛЩИНА
    pts = [(-t, НИЗ), (СТЕКЛО_Т + ДНО_ЗА_СТЕКЛО, НИЗ), (СТЕКЛО_Т + ДНО_ЗА_СТЕКЛО, НИЗ + ДНО_Т), (0.0, НИЗ + ДНО_Т),
           (0.0, ВЕРХ), (-t, ВЕРХ - СКОС)]
    return CrossSection([pts])


def extrude_x(cs, x0, x1):
    """Сечение (Y, Z) вытягивается вдоль X от x0 до x1. Extrude тянет по Z, поворот (90, 0, 90) переводит
    оси (u, v, w) сечения в (Y, Z, X)."""
    return Manifold.extrude(cs, x1 - x0).rotate((90, 0, 90)).translate((x0, 0, 0))


def holder_cut(x0, x1):
    """Окно под держатель и паз под отвёртку снизу (к стопорному винту на нижней губке)."""
    c = ОКНО_ЗАЗОР
    w = box(x0 - c, x1 + c, -ТОЛЩИНА - 1, 1, ДЕРЖ_Z - c, ДЕРЖ_Z + ДЕРЖ_В + c)
    xm = (x0 + x1) / 2
    g = box(xm - ПАЗ_Ш / 2, xm + ПАЗ_Ш / 2, -ТОЛЩИНА - 1, -ТОЛЩИНА + ПАЗ_Г, НИЗ - 1, ДЕРЖ_Z)
    return w + g


def piece(k):
    """k = 0 левая, 1 средняя, 2 правая."""
    x0 = -ВЫХОД_ВБОК + k * ДЛИНА
    x1 = x0 + ДЛИНА
    m = extrude_x(profile(), x0, x1)
    m -= box(x0 - 1, x1 + 1, -ТОЛЩИНА - 1, -ПЕРЕМЫЧКА, РАЗРЕЗ_Z0, РАЗРЕЗ_Z1)   # разрез под полку
    if k == 0:
        m -= holder_cut(*ДЕРЖ_X)
    if k == 2:
        m -= holder_cut(СТЕКЛО_Ш - ДЕРЖ_X[1], СТЕКЛО_Ш - ДЕРЖ_X[0])
    return m


ИМЕНА = {"left": (0, "левая"), "middle": (1, "средняя"), "right": (2, "правая")}


# ---------- печать: лицом на стол, с подложкой ----------

def to_bed(m):
    """Лицо (Y = −ТОЛЩИНА) — на стол. X остаётся вдоль стола, высота детали Z ложится в −Y стола."""
    return m.rotate((90, 0, 0)).translate((0, 0, ТОЛЩИНА))


def footprint(m):
    outer = [p for p in m.slice(0.1).to_polygons()
             if 0.5 * np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1]) > 0]
    return CrossSection(outer)


def keepout(k):
    """Куда подложке нельзя (в координатах стола до сдвига): полоса разреза и окна с пазами, с отступом.
    Верхняя грань разреза ложится на полку, в окна входят держатели."""
    o = ПОДЛОЖКА_ОТСТУП
    x0 = -ВЫХОД_ВБОК + k * ДЛИНА
    ko = CrossSection.square((ДЛИНА + 40, РАЗРЕЗ_Z1 - РАЗРЕЗ_Z0 + 2 * o)).translate((x0 - 20, -РАЗРЕЗ_Z1 - o))
    holders = []
    if k == 0:
        holders.append(ДЕРЖ_X)
    if k == 2:
        holders.append((СТЕКЛО_Ш - ДЕРЖ_X[1], СТЕКЛО_Ш - ДЕРЖ_X[0]))
    for a, b in holders:
        c = ОКНО_ЗАЗОР + o
        ko += CrossSection.square((b - a + 2 * c, ДЕРЖ_В + 2 * c)).translate((a - c, -(ДЕРЖ_Z + ДЕРЖ_В) - c))
        xm = (a + b) / 2
        ko += CrossSection.square((ПАЗ_Ш + 2 * o, ДЕРЖ_Z - НИЗ + 2 * o)).translate((xm - ПАЗ_Ш / 2 - o, -ДЕРЖ_Z - o))
    return ko


def with_pad(m, ko):
    fp = footprint(m)
    ring = fp.offset(ПОДЛОЖКА_Ш, JoinType.Round) - fp.offset(-0.05, JoinType.Round) - ko
    return m + Manifold.extrude(ring, ПОДЛОЖКА_Н)


def plate(k):
    m = to_bed(piece(k))
    ko = keepout(k)
    # Длинной стороной вдоль Y стола: с подложкой деталь занимает 218 из 220, а у левого края стола (X ≈ −1,
    # Y 20…145) прошивка K1 перед печатью чертит линию прочистки. Это по памяти о прошивке, через API принтера
    # не проверено. Вдоль Y деталь стоит по центру, до левого края больше 60 мм.
    m = with_pad(m, ko).rotate((0, 0, 90))
    bb = m.bounding_box()
    dx = (СТОЛ - (bb[3] - bb[0])) / 2 - bb[0]
    dy = (СТОЛ - (bb[4] - bb[1])) / 2 - bb[1]
    m = m.translate((dx, dy, 0))
    bb = m.bounding_box()
    if bb[0] < 0 or bb[1] < 0 or bb[3] > СТОЛ or bb[4] > СТОЛ:
        raise SystemExit(f"деталь с подложкой не помещается на стол {СТОЛ} × {СТОЛ}: {bb}")
    return m


# ---------- сцена для картинки с содержимым ----------

def glass():
    """Стекло со сколом слева и ступенькой справа (по фото, грубо: только для картинки)."""
    w = СТЕКЛО_Ш
    pts = [(0, 200), (0, 6), (12, 4), (22, 8), (30, 3), (36, 0), (w - 100, 0), (w - 80, 6), (w - 52, 6),
           (w - 30, 8), (w - 30, 20), (w - 6, 20), (w, 26), (w, 200)]
    cs = CrossSection([pts[::-1]])
    if cs.area() <= 0:
        cs = CrossSection([pts])
    return Manifold.extrude(cs, СТЕКЛО_Т).rotate((90, 0, 0)).translate((0, СТЕКЛО_Т, 0))


def holder(x0):
    x1 = x0 + ДЕРЖ_Ш
    z0, g, s = ДЕРЖ_Z, ДЕРЖ_ГУБКА, ПОЛКА_Т
    return (box(x0, x1, -ПОЛКА_ОТ_СТЕКЛА, 0, z0, z0 + ДЕРЖ_В) + box(x0, x1, -ДЕРЖ_ВЫЛЕТ, 0, z0, z0 + g)
            + box(x0, x1, -ДЕРЖ_ВЫЛЕТ, 0, z0 + g + s, z0 + ДЕРЖ_В))


def scene():
    xs = (СТЕКЛО_Ш - ПОЛКА_Д) / 2
    parts = [("стена", box(-40, СТЕКЛО_Ш + 40, ДО_СТЕНЫ, ДО_СТЕНЫ + 8, -90, 230), "#f4ece1"),
             ("зеркало", glass(), "#e2f0f4"),
             ("подсветка", box(ПОДСВЕТКА_X[0], ПОДСВЕТКА_X[1], -0.4, 0, ПОДСВЕТКА_Z, 200)
              + box(СТЕКЛО_Ш - ПОДСВЕТКА_X[1], СТЕКЛО_Ш - ПОДСВЕТКА_X[0], -0.4, 0, ПОДСВЕТКА_Z, 200), "#fffbe8"),
             ("держатели", holder(ДЕРЖ_X[0]) + holder(СТЕКЛО_Ш - ДЕРЖ_X[1]), "#cfd5da"),
             ("полка", box(xs, xs + ПОЛКА_Д, -ПОЛКА_ОТ_СТЕКЛА - ПОЛКА_Г, -ПОЛКА_ОТ_СТЕКЛА, ПОЛКА_Z, ПОЛКА_Z + ПОЛКА_Т),
              "#c6dcd6")]
    parts += [(f"накладка, {ИМЕНА[n][1]}", piece(ИМЕНА[n][0]), None) for n in ("left", "middle", "right")]
    # камера картинки смотрит сверху под ~44°: наклоняем сцену, чтобы зеркало было видно почти в лоб
    return [(n, m.rotate((-30, 0, 0)).rotate((0, 0, -20)), c) for n, m, c in parts]


# ---------- 3mf ----------

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
        resources.append(f'<object id="{oid}" type="model" name="{name}"{mat}>\n<mesh><vertices>\n{v}\n'
                         f'</vertices><triangles>\n{t}\n</triangles></mesh>\n</object>')
        items.append(f'<item objectid="{oid}"/>')
    model_xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
                 'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">\n'
                 f'<metadata name="Title">{title}</metadata>\n<resources>\n' + "\n".join(resources)
                 + f'\n</resources>\n<build>{"".join(items)}</build>\n</model>')
    ct = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/'
          'content-types">\n<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.'
          'relationships+xml"/>\n<Default Extension="model" ContentType="application/vnd.ms-package.'
          '3dmanufacturing-3dmodel+xml"/>\n</Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/'
            'package/2006/relationships">\n<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://'
            'schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n</Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model_xml)


def report(parts, plate=False):
    for name, m, _ in parts:
        bb = m.bounding_box()
        line = (f"  {name}: объём {m.volume() / 1000:.1f} см³, кусков {len(m.decompose())}, genus {m.genus()}, "
                f"габарит {bb[3] - bb[0]:.1f} × {bb[4] - bb[1]:.1f} × {bb[5] - bb[2]:.1f}, статус {m.status()}")
        if plate:
            extra = m.slice(0.1).area() - m.slice(ПОДЛОЖКА_Н + 0.1).area()
            line += f", подложка {'есть' if extra > 1 else 'НЕТ'} ({extra / 100:.1f} см²)"
            line += f", на столе x {bb[0]:.1f}…{bb[3]:.1f}, y {bb[1]:.1f}…{bb[4]:.1f}"
        print(line)


if __name__ == "__main__":
    args = sys.argv[1:]
    base = "evoform-ledline-s-mirror-trim-v1"
    plate_mode = False
    if "--part" in args:
        i = args.index("--part")
        key = args[i + 1]
        del args[i:i + 2]
        k, ru = ИМЕНА[key]
        parts = [(f"накладка, {ru}", plate(k), None)]
        name = f"{base}-{key}"
        plate_mode = True
    elif "--pose" in args:
        i = args.index("--pose")
        del args[i:i + 2]
        parts = [(f"накладка, {ИМЕНА[n][1]}", piece(ИМЕНА[n][0]), None) for n in ("left", "middle", "right")]
        name = f"{base}-use"
    elif "--filled" in args:
        args.remove("--filled")
        parts = scene()
        name = f"{base}-filled"
    else:
        raise SystemExit("укажите --part right|middle|left, --pose use или --filled")
    fname = args[0] if args else f"{name}.3mf"
    write_3mf(fname, parts, name)
    print(fname)
    report(parts, plate_mode)
