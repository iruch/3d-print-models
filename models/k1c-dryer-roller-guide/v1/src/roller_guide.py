# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "manifold3d"]
# ///
"""Направляющие ролики для нити из сушилки, которая стоит справа от Creality K1C. Пока только узел 1.

Узел 1: клипса на правом бортике принтера, стойка вниз снаружи по боковине, плечо наружу и ролик на конце.
Нить из сушилки поднимается к ролику, переходит через него и уходит назад, к ролику 2 у нитеприёмника (узел 2,
будет позже). Клипса держится только за бортик сверху и за боковину: внутрь рамы ничего не заходит,
там кабель-канал головы.

Как держит клипса. Плита лежит на верху бортика, выступ цепляется за его внутреннюю кромку, изнутри клипса
лежит на наружной фаске, стойка идёт вплотную по боковине. Барашковый винт проходит через стойку
и упирается в боковину ниже фаски: если его закрутить, выступ прижимается к кромке, и бортик зажат
по горизонтали. Винт давит не в фаску: она смотрит наружу и вверх под 45°, и прижим к ней
выталкивал бы клипсу с бортика.

Все размеры в мм. Профиль бортика замерен пользователем рулеткой: от внутренней кромки до боковины 22–23 мм,
наружная фаска 15 × 15 мм под 45°. Клипса садится на верх, фаску и кромку без зазора: во втором пробнике
у фаски была щель около 2 мм, и клипса качалась. Стойка в 1 мм от боковины, винт только поджимает.

Система координат кронштейна, она же положение для печати: профиль лежит на столе.
  X — наружу от боковины принтера (0 = ровная боковина ниже фаски), Y — вверх (0 = верх бортика),
  Z — вдоль бортика, по толщине детали (0..ТОЛЩИНА).
На принтере: X мира = X, Y мира = −Z (вдоль бортика), Z мира = Y.

uv run roller_guide.py                  -> k1c-dryer-roller-guide-v1.3mf: узел 1 для печати, все детали на одном столе
uv run roller_guide.py --clip-test      -> k1c-dryer-roller-guide-v1-clip-test.3mf: верх клипсы с винтом и гайкой
uv run roller_guide.py --pose use       -> узел 1 в сборе, как стоит на принтере, для картинок видов
uv run roller_guide.py --filled         -> сцена: кусок бортика, узел 1, нить; для картинки filled.png, не для печати
Последним аргументом можно передать имя файла. Без uv: pip install numpy manifold3d, дальше python вместо uv run.
"""
import sys
import zipfile
import numpy as np
from manifold3d import Manifold, CrossSection, JoinType

# ---------- профиль бортика K1C (рулеткой и примеркой пробников) ----------
ПРОФИЛЬ_ПОЛОСА = 23.0      # от внутренней кромки верха (за неё цепляется выступ) до ровной боковины: 22–23 по рулетке
ПРОФИЛЬ_ФАСКА = 15.0       # наружная фаска бортика: 15 мм вбок и 15 мм вниз, 45°. Замерено рулеткой
ПРОФИЛЬ_СТУПЕНЬКА = 12.0   # внутренняя кромка вниз от верха (только для сцены)
ПРОФИЛЬ_ПОЛКА = 13.0       # (только для сцены)
ЗАЗОР_ФАСКИ = 0.0          # между клипсой и фаской. Во втором пробнике было 1 мм: с выступом щель ~2 мм, клипса качалась

# ---------- кронштейн узла 1 ----------
ТОЛЩИНА = 20.0             # толщина детали вдоль бортика
ПЛИТА = 4.0                # верхняя плита на бортике
ВЫСТУП_Т, ВЫСТУП_Н = 4.0, 5.0   # выступ на полке: толщина и высота. Ниже ступеньки, чтобы плита легла на верх
ВЫСТУП_ЗАЗОР = 0.0         # от выступа до внутренней кромки. Во втором пробнике 0,5: вместе с фаской давало щель
СТОЙКА_X0 = 1.0            # внутренняя грань стойки: от боковины. В первом пробнике было 6 мм, клипса болталась
СТОЙКА_Т = 11.0            # толщина стойки
РОЛИК_X = 70.0             # центр ролика от боковины: плечо 8 см до наружной щеки (по рисунку пользователя)
РОЛИК_Z = -100.0           # центр ролика ниже верха бортика (10 см по рисунку пользователя)
ПЛЕЧО_Н = 12.0             # высота плеча
УКОС = 18.0                # косынка между стойкой и плечом

# ---------- ролик и вилка ----------
РОЛИК_R = 19.0             # наружный радиус по щёчкам
РОЛИК_ДНО = 14.0           # радиус по дну канавки
РОЛИК_Ш = 12.0             # ширина ролика
КАНАВКА_ДНО = 1.2          # плоское дно канавки под нить 1.75
КАНАВКА_УГОЛ = 35.0        # наклон стенок канавки от радиуса, градусы
ОСЬ_D = 6.0                # ось ролика
РОЛИК_ОТВ = 6.8            # отверстие ролика: свободно на оси
ЩЕКА = 5.0                 # щёки вилки
ЗАЗОР_БОК = 0.8            # между роликом и щекой
ЗАЗОР_НИЗ = 2.0            # под роликом
ЗАЗОР_ВЕРХ = 1.0           # между щёчками ролика и скобой: меньше нити, она не выскочит
ПЕРЕМЫЧКА = 6.0            # скоба над роликом и перемычка под ним
ОСЬ_НАРУЖ = 6.4            # отверстие оси в наружной щеке: ось входит свободно
ОСЬ_ВНУТР = 6.0            # во внутренней щеке: ось сидит туго
ОСЬ_ШЛЯПКА_D, ОСЬ_ШЛЯПКА_Н = 10.0, 2.5

# ---------- прижимной винт и гайка (печатная резьба, шаг крупный под печать) ----------
ВИНТ_Z = -50.0             # высота винта: ниже фаски с запасом
ВИНТ_D = 8.0               # наружный диаметр резьбы
ВИНТ_ШАГ = 2.0
ВИНТ_ГЛУБИНА = 1.0         # глубина профиля
ВИНТ_L = 16.0              # длина резьбы: стойка 11 мм и ход до 5 мм; с барашком 24 мм. Боковина под винтом прогибается
БАРАШЕК_D, БАРАШЕК_Н = 22.0, 8.0
ЗАЗОР_РЕЗЬБЫ = 0.35        # по радиусу между винтом и гайкой
ГАЙКА_S, ГАЙКА_Н = 13.0, 7.0    # гайка: под ключ и высота
ОТВ_ВИНТА = 8.8            # отверстие под винт в стойке
КАРМАН_ЗАЗОР = 0.4         # карман под гайку больше её

ПРОБНИК_Y = -62.0          # пробник клипсы: кронштейн обрезан на этой высоте

SEG = 96

# ---------- производные ----------
ВЫСТУП_X1 = -ПРОФИЛЬ_ПОЛОСА - ВЫСТУП_ЗАЗОР
ВЫСТУП_X0 = ВЫСТУП_X1 - ВЫСТУП_Т
СТОЙКА_X1 = СТОЙКА_X0 + СТОЙКА_Т
ОКНО_X0 = РОЛИК_X - РОЛИК_Ш / 2 - ЗАЗОР_БОК
ОКНО_X1 = РОЛИК_X + РОЛИК_Ш / 2 + ЗАЗОР_БОК
ЩЕКА_ВН0 = ОКНО_X0 - ЩЕКА
ЩЕКА_НАР1 = ОКНО_X1 + ЩЕКА
ОКНО_Y0 = РОЛИК_Z - РОЛИК_R - ЗАЗОР_НИЗ
ОКНО_Y1 = РОЛИК_Z + РОЛИК_R + ЗАЗОР_ВЕРХ
ВИЛКА_Y0 = ОКНО_Y0 - ПЕРЕМЫЧКА
ВИЛКА_Y1 = ОКНО_Y1 + ПЕРЕМЫЧКА


def rect(x0, y0, x1, y1):
    return CrossSection.square((x1 - x0, y1 - y0)).translate((x0, y0))


def poly(pts):
    return CrossSection([pts])


def cyl_x(x0, x1, y, z, d):
    """Цилиндр вдоль X."""
    return Manifold.cylinder(x1 - x0, d / 2, d / 2, SEG).rotate((0, 90, 0)).translate((x0, y, z))


def hex_x(x0, x1, y, z, s):
    """Шестигранник вдоль X, под ключ s, вершиной вверх по печати (+Z): карман печатается без поддержек."""
    r = s / np.sqrt(3)
    pts = [(r * np.cos(np.radians(a)), r * np.sin(np.radians(a))) for a in range(0, 360, 60)]
    return Manifold.extrude(poly(pts), x1 - x0).rotate((0, 90, 0)).translate((x0, y, z))


def chamfer_pts():
    """Наружная фаска бортика: от верха (x = -ФАСКА, z = 0) до боковины (x = 0, z = -ФАСКА), 45°."""
    return [(0.0, -ПРОФИЛЬ_ФАСКА), (-ПРОФИЛЬ_ФАСКА, 0.0)]


def hug_chamfer():
    """Заполнение между плитой, стойкой и фаской: клипса повторяет фаску с зазором ЗАЗОР_ФАСКИ (по нормали)."""
    c = ПРОФИЛЬ_ФАСКА - ЗАЗОР_ФАСКИ * np.sqrt(2)      # линия фаски со сдвигом наружу: z = -x - c
    x_top = -c                                       # где она пересекает низ плиты (z = 0)
    z_post = -СТОЙКА_X0 - c                          # и внутреннюю грань стойки (x = СТОЙКА_X0)
    return poly([(x_top, 0.0), (СТОЙКА_X0, z_post), (СТОЙКА_X0 + 0.5, z_post), (СТОЙКА_X0 + 0.5, 0.0)])


def bracket_profile(y_cut=None):
    cs = rect(ВЫСТУП_X0, 0, СТОЙКА_X1, ПЛИТА)
    cs += rect(ВЫСТУП_X0, -ВЫСТУП_Н, ВЫСТУП_X1, 0)
    cs += hug_chamfer()
    cs += rect(СТОЙКА_X0, РОЛИК_Z - ПЛЕЧО_Н / 2, СТОЙКА_X1, ПЛИТА)
    cs += rect(СТОЙКА_X1 - 1, РОЛИК_Z - ПЛЕЧО_Н / 2, ЩЕКА_ВН0 + 0.5, РОЛИК_Z + ПЛЕЧО_Н / 2)
    # многоугольники против часовой стрелки: по часовой CrossSection считает дыркой
    cs += poly([(СТОЙКА_X1 - 0.5, РОЛИК_Z + ПЛЕЧО_Н / 2 - 0.5), (СТОЙКА_X1 + УКОС, РОЛИК_Z + ПЛЕЧО_Н / 2 - 0.5),
                (СТОЙКА_X1 - 0.5, РОЛИК_Z + ПЛЕЧО_Н / 2 + УКОС)])
    cs += rect(ЩЕКА_ВН0, ВИЛКА_Y0, ЩЕКА_НАР1, ВИЛКА_Y1) - rect(ОКНО_X0, ОКНО_Y0, ОКНО_X1, ОКНО_Y1)
    if y_cut is not None:
        cs = cs ^ rect(-100, y_cut, 200, 50)
    return cs


def bracket(y_cut=None):
    body = Manifold.extrude(bracket_profile(y_cut), ТОЛЩИНА)
    zc = ТОЛЩИНА / 2
    holes = cyl_x(СТОЙКА_X0 - 1, СТОЙКА_X1 + 1, ВИНТ_Z, zc, ОТВ_ВИНТА)
    holes += hex_x(СТОЙКА_X0 - 0.01, СТОЙКА_X0 + ГАЙКА_Н + КАРМАН_ЗАЗОР, ВИНТ_Z, zc, ГАЙКА_S + КАРМАН_ЗАЗОР)
    if y_cut is None:
        holes += cyl_x(ОКНО_X1 - 0.5, ЩЕКА_НАР1 + 1, РОЛИК_Z, zc, ОСЬ_НАРУЖ)
        holes += cyl_x(ЩЕКА_ВН0 - 1, ОКНО_X0 + 0.5, РОЛИК_Z, zc, ОСЬ_ВНУТР)
    return body - holes


def roller():
    """Ролик осью по Z, лежит на столе. Канавка с плоским дном, стенки под КАНАВКА_УГОЛ."""
    w, rb = РОЛИК_Ш, РОЛИК_ОТВ / 2
    half = КАНАВКА_ДНО / 2 + (РОЛИК_R - РОЛИК_ДНО) * np.tan(np.radians(КАНАВКА_УГОЛ))
    z1, z2 = w / 2 - half, w / 2 + half
    ch = 0.6
    pts = [(rb + ch, 0), (РОЛИК_R - ch, 0), (РОЛИК_R, ch), (РОЛИК_R, z1),
           (РОЛИК_ДНО, w / 2 - КАНАВКА_ДНО / 2), (РОЛИК_ДНО, w / 2 + КАНАВКА_ДНО / 2),
           (РОЛИК_R, z2), (РОЛИК_R, w - ch), (РОЛИК_R - ch, w), (rb + ch, w), (rb, w - ch), (rb, ch)]
    return Manifold.revolve(poly(pts), SEG)


def pin():
    """Ось ролика: шляпка на столе, стержень вверх."""
    L = ЩЕКА_НАР1 - ЩЕКА_ВН0
    head = Manifold.cylinder(ОСЬ_ШЛЯПКА_Н, ОСЬ_ШЛЯПКА_D / 2, ОСЬ_ШЛЯПКА_D / 2, SEG)
    shaft = Manifold.cylinder(L - 0.6, ОСЬ_D / 2, ОСЬ_D / 2, SEG).translate((0, 0, ОСЬ_ШЛЯПКА_Н))
    tip = Manifold.cylinder(0.6, ОСЬ_D / 2, ОСЬ_D / 2 - 0.6, SEG).translate((0, 0, ОСЬ_ШЛЯПКА_Н + L - 0.6))
    return head + shaft + tip


def thread_section(offset=0.0):
    """Сечение резьбы поперёк оси: радиус меняется по кругу треугольником, с площадками на вершине и во впадине.
    Если выдавить его с поворотом 360° на шаг, получится однозаходная резьба."""
    r_min = ВИНТ_D / 2 - ВИНТ_ГЛУБИНА
    pts = []
    for i in range(SEG):
        t = 2 * np.pi * i / SEG
        tri = 1 - abs(t / np.pi - 1)
        f = min(1.0, max(0.0, (tri - 0.12) / 0.76))
        r = r_min + ВИНТ_ГЛУБИНА * f + offset
        pts.append((r * np.cos(t), r * np.sin(t)))
    return poly(pts)


def threaded(h, offset=0.0):
    turns = h / ВИНТ_ШАГ
    return Manifold.extrude(thread_section(offset), h, int(turns * 24), 360.0 * turns)


def screw():
    """Барашковый винт: барашек на столе, резьба вверх, торец плоский."""
    knob = Manifold.cylinder(БАРАШЕК_Н, БАРАШЕК_D / 2, БАРАШЕК_D / 2, SEG)
    for k in range(8):
        a = np.radians(k * 45)
        knob -= Manifold.cylinder(БАРАШЕК_Н + 2, 2.6, 2.6, 32).translate(
            (БАРАШЕК_D / 2 * np.cos(a), БАРАШЕК_D / 2 * np.sin(a), -1))
    rod = threaded(ВИНТ_L).translate((0, 0, БАРАШЕК_Н))
    # заход резьбы и плоский торец под упор в боковину ниже фаски
    top = БАРАШЕК_Н + ВИНТ_L
    lead = Manifold.cylinder(1.5, ВИНТ_D / 2 + 1, ВИНТ_D / 2 - 1.5, SEG).translate((0, 0, top - 1.5))
    keep = Manifold.cylinder(top - 1.5, 20, 20, SEG) + lead
    return (knob + rod) ^ keep


def nut():
    r = ГАЙКА_S / np.sqrt(3)
    pts = [(r * np.cos(np.radians(a + 30)), r * np.sin(np.radians(a + 30))) for a in range(0, 360, 60)]
    body = Manifold.extrude(poly(pts), ГАЙКА_Н)
    hole = threaded(ГАЙКА_Н + 2, ЗАЗОР_РЕЗЬБЫ).translate((0, 0, -1))
    cham = Manifold.cylinder(1.0, ВИНТ_D / 2 + ЗАЗОР_РЕЗЬБЫ + 0.6, ВИНТ_D / 2 - 0.4, SEG).translate((0, 0, -0.01))
    cham += cham.mirror((0, 0, 1)).translate((0, 0, ГАЙКА_Н + 0.02))
    return body - hole - cham


# ---------- сборка на принтере ----------

def use(m):
    """Из координат кронштейна в мировые: X наружу, Y вдоль бортика, Z вверх."""
    return m.rotate((90, 0, 0))


def assembly():
    zc = ТОЛЩИНА / 2
    parts = [("кронштейн", bracket())]
    parts.append(("ролик", roller().translate((0, 0, -РОЛИК_Ш / 2)).rotate((0, 90, 0)).translate((РОЛИК_X, РОЛИК_Z, zc))))
    parts.append(("ось", pin().rotate((0, -90, 0)).translate((ЩЕКА_НАР1 + ОСЬ_ШЛЯПКА_Н, РОЛИК_Z, zc))))
    # винт: торец упирается в боковину (X = 0), барашек снаружи
    parts.append(("винт", screw().rotate((0, -90, 0)).translate((БАРАШЕК_Н + ВИНТ_L, ВИНТ_Z, zc))))
    # гайка повёрнута на 30°, чтобы грани совпали с карманом (у кармана вершина смотрит вверх по печати)
    parts.append(("гайка", nut().rotate((0, 0, 30)).rotate((0, 90, 0)).translate((СТОЙКА_X0 + КАРМАН_ЗАЗОР / 2, ВИНТ_Z, zc))))
    return [(n, use(m)) for n, m in parts]


def rim_piece(length=110.0):
    """Кусок бортика и боковины K1C по профилю ПРОФИЛЬ_*, для сцены."""
    x_in = -ПРОФИЛЬ_ПОЛОСА - ПРОФИЛЬ_ПОЛКА
    pts = [(x_in, -150), (0, -150)] + chamfer_pts() + [(-ПРОФИЛЬ_ПОЛОСА, 0),
           (-ПРОФИЛЬ_ПОЛОСА, -ПРОФИЛЬ_СТУПЕНЬКА), (x_in, -ПРОФИЛЬ_СТУПЕНЬКА)]
    m = Manifold.extrude(poly(pts), length).translate((0, 0, ТОЛЩИНА / 2 - length / 2))
    return use(m)


def filament():
    """Нить на ролике 1: от выхода сушилки (впереди внизу) и к ролику 2 (сзади, ниже, ближе к принтеру).
    Направления посчитаны для узла примерно в 15 см от переднего края принтера."""
    c = np.array([РОЛИК_X, -ТОЛЩИНА / 2, РОЛИК_Z])
    rho = РОЛИК_ДНО + 0.9
    d_front = np.array([0.0, -0.75, -0.66]); d_front /= np.linalg.norm(d_front)
    d_back = np.array([-0.21, 0.83, -0.51]); d_back /= np.linalg.norm(d_back)
    a0, a1 = np.arctan2(-0.66, 0.75), np.arctan2(0.51, 0.83)   # углы точек схода от вертикали в плоскости ролика

    def seg(p, q, d=1.75):
        v = q - p; L = np.linalg.norm(v)
        m = Manifold.cylinder(L, d / 2, d / 2, 16)
        z = np.array([0, 0, 1.0]); u = v / L
        ax = np.cross(z, u); s = np.linalg.norm(ax)
        if s > 1e-9:
            ang = np.degrees(np.arctan2(s, z @ u)); ax /= s
            # поворот вокруг произвольной оси через углы Эйлера неудобен — строим матрицу
            K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
            R = np.eye(3) + np.sin(np.radians(ang)) * K + (1 - np.cos(np.radians(ang))) * K @ K
            m = m.transform(np.hstack([R, p.reshape(3, 1)]))
        else:
            m = m.translate(tuple(p))
        return m

    pts = [c + rho * np.array([0, np.sin(t), np.cos(t)]) for t in np.linspace(a0, a1, 12)]
    m = Manifold()
    for p, q in zip(pts[:-1], pts[1:]):
        m += seg(p, q)
    m += seg(pts[0] + 140 * d_front, pts[0])
    m += seg(pts[-1], pts[-1] + 160 * d_back)
    return m


# ---------- столы для печати ----------

def plate_main():
    b = bracket()
    bb = b.bounding_box()
    parts = [("кронштейн", b.translate((8 - bb[0], 8 - bb[1], 0)))]
    parts.append(("ролик", roller().translate((165, 35, 0))))
    parts.append(("ось", pin().translate((150, 90, 0))))
    parts.append(("винт", screw().translate((185, 92, 0))))
    parts.append(("гайка", nut().translate((160, 135, 0))))
    return parts


def plate_clip_test():
    b = bracket(ПРОБНИК_Y)
    bb = b.bounding_box()
    return [("пробник клипсы", b.translate((8 - bb[0], 8 - bb[1], 0))),
            ("винт", screw().translate((90, 30, 0))),
            ("гайка", nut().translate((90, 62, 0)))]


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


def report(parts):
    for name, m, _ in parts:
        bb = m.bounding_box()
        print(f"  {name}: объём {m.volume() / 1000:.1f} см³, кусков {len(m.decompose())}, genus {m.genus()}, "
              f"габарит {bb[3] - bb[0]:.1f} × {bb[4] - bb[1]:.1f} × {bb[5] - bb[2]:.1f}, статус {m.status()}")


if __name__ == "__main__":
    args = sys.argv[1:]
    name = "k1c-dryer-roller-guide-v1"
    if "--clip-test" in args:
        args.remove("--clip-test")
        parts = [(n, m, None) for n, m in plate_clip_test()]
        name += "-clip-test"
    elif "--filled" in args:
        args.remove("--filled")
        parts = [(n, m, None) for n, m in assembly()]
        parts += [("бортик K1C", rim_piece(), "#5f656d"), ("нить", filament(), "#e6dfc8")]
        name += "-filled"
    elif "--pose" in args:
        i = args.index("--pose"); del args[i:i + 2]
        parts = [(n, m, None) for n, m in assembly()]
        name += "-use"
    else:
        parts = [(n, m, None) for n, m in plate_main()]
    fname = args[0] if args else f"{name}.3mf"
    write_3mf(fname, parts, name)
    print(fname)
    report(parts)
