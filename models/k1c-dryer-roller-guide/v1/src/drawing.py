# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "manifold3d", "matplotlib"]
# ///
"""Чертёж узла 1 со всеми размерами. Контур берётся из генератора roller_guide.py, размеры — из его параметров,
так что чертёж всегда совпадает с моделью.

uv run drawing.py ../img/dims.png
"""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle, Rectangle
import roller_guide as g

OUT = sys.argv[1] if len(sys.argv) > 1 else "dims.png"
INK, BLUE, RIM = "#2b3036", "#1d6fa5", "#9aa0a6"


def dim(ax, p, q, text, off=(0, 0), side=1, fs=9):
    """Размерная линия между p и q со смещением off (вынос) и подписью."""
    p, q = np.array(p, float), np.array(q, float)
    o = np.array(off, float)
    a, b = p + o, q + o
    for s, t in ((p, a), (q, b)):
        if np.linalg.norm(t - s) > 0.1:
            ax.plot([s[0], t[0]], [s[1], t[1]], color=BLUE, lw=0.6)
    ax.annotate("", xy=b, xytext=a, arrowprops=dict(arrowstyle="<|-|>", color=BLUE, lw=0.9, shrinkA=0, shrinkB=0,
                                                    mutation_scale=8))
    m = (a + b) / 2
    vert = abs(b[0] - a[0]) < abs(b[1] - a[1])
    ax.text(m[0] + (1.2 * side if vert else 0), m[1] + (0 if vert else 1.0 * side), text, color=BLUE, fontsize=fs,
            ha="left" if vert and side > 0 else ("right" if vert else "center"),
            va="center" if vert else ("bottom" if side > 0 else "top"), rotation=0)


def outline(ax, cs, **kw):
    """Контуры сечения; дырки (обход по часовой) закрашены белым."""
    for poly in cs.to_polygons():
        p = np.array(poly)
        area = 0.5 * np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1])
        ax.add_patch(Polygon(p, closed=True, **(kw | {"fc": "white"} if area < 0 else kw)))


fig = plt.figure(figsize=(21, 12))
ax = fig.add_axes([0.01, 0.06, 0.42, 0.9])
cx = fig.add_axes([0.43, 0.06, 0.27, 0.9])
bx = fig.add_axes([0.71, 0.06, 0.29, 0.9])
zc = g.ВИНТ_Z
X0, X1 = g.ВЫСТУП_X0, g.СТОЙКА_X1


def rim_and_bracket(a):
    """Бортик и боковина K1C по профилю ПРОФИЛЬ_* (тонко, для понимания), кронштейн, отверстие и карман винта."""
    x_in = -g.ПРОФИЛЬ_ПОЛОСА - 8
    rim = [(x_in, -140), (0, -140)] + g.chamfer_pts() + [
        (-g.ПРОФИЛЬ_ПОЛОСА, 0), (-g.ПРОФИЛЬ_ПОЛОСА, -g.ПРОФИЛЬ_СТУПЕНЬКА), (x_in, -g.ПРОФИЛЬ_СТУПЕНЬКА)]
    a.add_patch(Polygon(rim, closed=True, fc="#eceef0", ec=RIM, lw=0.8, ls="--"))
    outline(a, g.bracket_profile(), fc="#d6dbe0", ec=INK, lw=1.2)
    # отверстие и карман в разрезе по оси (пунктиром)
    a.add_patch(Rectangle((g.СТОЙКА_X0, zc - g.ОТВ_ВИНТА / 2), g.СТОЙКА_Т, g.ОТВ_ВИНТА, fc="none", ec=INK, ls=":", lw=0.9))
    a.add_patch(Rectangle((g.СТОЙКА_X0, zc - (g.ГАЙКА_S + g.КАРМАН_ЗАЗОР) / 2), g.ГАЙКА_Н + g.КАРМАН_ЗАЗОР,
                          g.ГАЙКА_S + g.КАРМАН_ЗАЗОР, fc="none", ec=INK, ls=":", lw=0.9))
    a.plot([-4, g.СТОЙКА_X1 + 4], [zc, zc], color=INK, lw=0.6, ls="-.")


def note(a, xy, xytext, text):
    """Подпись со стрелкой-выноской."""
    a.annotate(text, xy=xy, xytext=xytext, color=BLUE, fontsize=8.5, va="center",
               arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=0.7, mutation_scale=7))


# ---------- вид спереди: весь кронштейн ----------
rim_and_bracket(ax)
ax.text(-g.ПРОФИЛЬ_ПОЛОСА + 2, -100, "бортик\nи боковина\nK1C", fontsize=8, color="#777")
ax.add_patch(Circle((g.РОЛИК_X, g.РОЛИК_Z), g.РОЛИК_R, fc="none", ec="#888", lw=0.8, ls="--"))
ax.plot([g.ЩЕКА_ВН0, g.ЩЕКА_НАР1], [g.РОЛИК_Z, g.РОЛИК_Z], color=INK, lw=0.6, ls="-.")
ax.plot([g.РОЛИК_X, g.РОЛИК_X], [g.ВИЛКА_Y0 - 3, g.ВИЛКА_Y1 + 3], color=INK, lw=0.6, ls="-.")
# рамка: что показано крупно справа
ax.add_patch(Rectangle((X0 - 3, -64), X1 - X0 + 9, 64 + g.ПЛИТА + 3, fc="none", ec="#999", lw=0.8, ls="--"))
ax.text(X1 + 8, -62, "клипса крупно —\nсправа", fontsize=8, color="#777", va="bottom")
# общие
dim(ax, (X0, g.ПЛИТА), (g.ЩЕКА_НАР1, g.ПЛИТА), f"{g.ЩЕКА_НАР1 - X0:.1f}", off=(0, 14))
dim(ax, (g.ЩЕКА_НАР1, g.ПЛИТА), (g.ЩЕКА_НАР1, g.ВИЛКА_Y0), f"{g.ПЛИТА - g.ВИЛКА_Y0:.1f}", off=(10, 0))
dim(ax, (X0, g.ПЛИТА), (X1, g.ПЛИТА), f"{X1 - X0:.1f}", off=(0, 7))
# плечо и косынка
dim(ax, (X1, g.РОЛИК_Z - g.ПЛЕЧО_Н / 2 - 3), (g.ЩЕКА_ВН0, g.РОЛИК_Z - g.ПЛЕЧО_Н / 2 - 3),
    f"{g.ЩЕКА_ВН0 - X1:.1f}", off=(0, -3), side=-1)
dim(ax, (g.ЩЕКА_ВН0 - 3, g.РОЛИК_Z - g.ПЛЕЧО_Н / 2), (g.ЩЕКА_ВН0 - 3, g.РОЛИК_Z + g.ПЛЕЧО_Н / 2),
    f"{g.ПЛЕЧО_Н:.0f}", off=(0, 0), side=-1, fs=8)
ax.text(X1 + g.УКОС / 2 + 2, g.РОЛИК_Z + g.ПЛЕЧО_Н / 2 + g.УКОС / 2 + 1, f"косынка\n{g.УКОС:.0f}×{g.УКОС:.0f}", fontsize=8, color=BLUE)
# стойка по высоте и центр ролика
dim(ax, (X0 + 2, 0), (X0 + 2, g.РОЛИК_Z), f"{-g.РОЛИК_Z:.0f} от верха бортика\nдо оси ролика", off=(-14, 0), side=-1)
dim(ax, (0, g.ВИЛКА_Y0 - 6), (g.РОЛИК_X, g.ВИЛКА_Y0 - 6), f"{g.РОЛИК_X:.0f} от боковины до оси ролика", off=(0, -4), side=-1)
# вилка
dim(ax, (g.ЩЕКА_ВН0, g.ВИЛКА_Y1), (g.ЩЕКА_НАР1, g.ВИЛКА_Y1), f"{g.ЩЕКА_НАР1 - g.ЩЕКА_ВН0:.1f}", off=(0, 5))
dim(ax, (g.ОКНО_X0, g.ОКНО_Y0 + 3), (g.ОКНО_X1, g.ОКНО_Y0 + 3), f"окно {g.ОКНО_X1 - g.ОКНО_X0:.1f}", off=(0, 0), fs=8)
dim(ax, (g.ЩЕКА_НАР1 + 2, g.ВИЛКА_Y1), (g.ЩЕКА_НАР1 + 2, g.ВИЛКА_Y0), f"{g.ВИЛКА_Y1 - g.ВИЛКА_Y0:.0f}", off=(2, 0), fs=8)
dim(ax, (g.ОКНО_X1 - 1.5, g.ОКНО_Y0), (g.ОКНО_X1 - 1.5, g.ОКНО_Y1), f"окно\n{g.ОКНО_Y1 - g.ОКНО_Y0:.0f}", off=(0, 0), side=-1, fs=8)
ax.text(g.ЩЕКА_НАР1 + 13, g.РОЛИК_Z, f"щёки {g.ЩЕКА:.0f}\nось: наружная\nщека Ø{g.ОСЬ_НАРУЖ},\nвнутренняя Ø{g.ОСЬ_ВНУТР}\n"
        f"скоба над\nроликом {g.ЗАЗОР_ВЕРХ:.0f} мм,\nпод ним {g.ЗАЗОР_НИЗ:.0f} мм", fontsize=8, color=BLUE, va="center")
ax.text(X0 - 28, g.ВИЛКА_Y0 - 32, f"Толщина детали вдоль бортика {g.ТОЛЩИНА:.0f} мм. Окно вилки сквозное вдоль бортика:\n"
        "нить идёт по ролику вперёд-назад. Отсчёт по X — от ровной боковины ниже фаски,\nпо высоте — от верха бортика.",
        fontsize=9, color=INK, va="top")
ax.set_title("Кронштейн узла 1, вид спереди (как стоит на принтере). Размеры в мм", fontsize=12, loc="left")
ax.set_xlim(X0 - 48, g.ЩЕКА_НАР1 + 40); ax.set_ylim(g.ВИЛКА_Y0 - 50, g.ПЛИТА + 22)
ax.set_aspect("equal"); ax.axis("off")

# ---------- клипса крупно, винт закручен до боковины ----------
rim_and_bracket(cx)
tip = 0.0
cx.add_patch(Rectangle((tip, zc - g.ВИНТ_D / 2), g.ВИНТ_L, g.ВИНТ_D, fc="#e8ebee", ec=INK, hatch="////", lw=0.9))
cx.add_patch(Rectangle((tip + g.ВИНТ_L, zc - g.БАРАШЕК_D / 2), g.БАРАШЕК_Н, g.БАРАШЕК_D, fc="#d6dbe0", ec=INK, lw=0.9))
cx.text(-g.ПРОФИЛЬ_ПОЛОСА + 3, -74, "бортик\nи боковина\nK1C", fontsize=8, color="#777")
# плита и выступ
dim(cx, (X0, g.ПЛИТА), (X1, g.ПЛИТА), f"{X1 - X0:.1f}", off=(0, 5))
dim(cx, (X0, 0), (X0, g.ПЛИТА), f"{g.ПЛИТА:.0f}", off=(-3, 0), side=-1, fs=8)
dim(cx, (X0, 0), (X0, -g.ВЫСТУП_Н), f"{g.ВЫСТУП_Н:.0f}", off=(-3, 0), side=-1, fs=8)
dim(cx, (X0, -g.ВЫСТУП_Н), (g.ВЫСТУП_X1, -g.ВЫСТУП_Н), f"{g.ВЫСТУП_Т:.0f}", off=(0, -2.5), side=-1, fs=8)
dim(cx, (g.ВЫСТУП_X1, -g.ВЫСТУП_Н), (0, -g.ВЫСТУП_Н), f"{-g.ВЫСТУП_X1:.0f} от выступа до боковины",
    off=(0, -6), side=-1, fs=8)
# фаска, кромка, боковина
note(cx, (-g.ПРОФИЛЬ_ФАСКА / 2, -g.ПРОФИЛЬ_ФАСКА / 2), (-31, -22),
     f"фаска бортика {g.ПРОФИЛЬ_ФАСКА:.0f}×{g.ПРОФИЛЬ_ФАСКА:.0f}, 45°:\nклипса лежит на ней\nбез зазора")
note(cx, (g.ВЫСТУП_X1, -g.ВЫСТУП_Н / 2), (-31, -38), "выступ вплотную\nк внутренней кромке")
note(cx, (g.СТОЙКА_X0 / 2, -30), (-31, -52), f"стойка до боковины:\nзазор {g.СТОЙКА_X0:.0f}")
dim(cx, (g.СТОЙКА_X0, -34), (X1, -34), f"{g.СТОЙКА_Т:.0f}", off=(0, 0), fs=8)
# винт
dim(cx, (X1, 0), (X1, zc), f"{-zc:.0f} до оси\nвинта", off=(17, 0))
dim(cx, (X1, zc + g.БАРАШЕК_D / 2 + 1.5), (tip + g.ВИНТ_L, zc + g.БАРАШЕК_D / 2 + 1.5), f"запас {tip + g.ВИНТ_L - X1:.0f}",
    off=(0, 0), fs=8)
cx.text(X1 + 1, zc - g.БАРАШЕК_D / 2 - 2, f"винт упёрт в боковину;\nзапас — сколько ещё\nможно довернуть\n\n"
        f"отв. Ø{g.ОТВ_ВИНТА}, карман гайки\nS{g.ГАЙКА_S + g.КАРМАН_ЗАЗОР:.1f}, глубина {g.ГАЙКА_Н + g.КАРМАН_ЗАЗОР:.1f}",
        fontsize=8, color=BLUE, va="top")
cx.set_title("Клипса крупно, винт закручен до боковины", fontsize=12, loc="left")
cx.set_xlim(-36, 34); cx.set_ylim(-86, 14)
cx.set_aspect("equal"); cx.axis("off")

# ---------- детали ----------
bx.set_xlim(0, 100); bx.set_ylim(0, 140); bx.set_aspect("equal"); bx.axis("off")
bx.set_title("Остальные детали узла 1", fontsize=12, loc="left")
# ролик в разрезе
ox, oy = 8, 92
half = g.КАНАВКА_ДНО / 2 + (g.РОЛИК_R - g.РОЛИК_ДНО) * np.tan(np.radians(g.КАНАВКА_УГОЛ))
w = g.РОЛИК_Ш
prof = [(0, g.РОЛИК_ОТВ / 2), (0, g.РОЛИК_R), (w / 2 - half, g.РОЛИК_R), (w / 2 - g.КАНАВКА_ДНО / 2, g.РОЛИК_ДНО),
        (w / 2 + g.КАНАВКА_ДНО / 2, g.РОЛИК_ДНО), (w / 2 + half, g.РОЛИК_R), (w, g.РОЛИК_R), (w, g.РОЛИК_ОТВ / 2)]
for sgn in (1, -1):
    bx.add_patch(Polygon([(ox + x, oy + sgn * r) for x, r in prof], closed=True, fc="#d6dbe0", ec=INK, lw=1))
bx.plot([ox - 3, ox + w + 3], [oy, oy], color=INK, lw=0.6, ls="-.")
dim(bx, (ox, oy + g.РОЛИК_R), (ox + w, oy + g.РОЛИК_R), f"{w:.0f}", off=(0, 3))
dim(bx, (ox + w + 3, oy - g.РОЛИК_R), (ox + w + 3, oy + g.РОЛИК_R), f"Ø{2 * g.РОЛИК_R:.0f}", off=(2, 0))
dim(bx, (ox + w / 2, oy - g.РОЛИК_ДНО), (ox + w / 2, oy + g.РОЛИК_ДНО), f"Ø{2 * g.РОЛИК_ДНО:.0f}\nпо дну", off=(0, 0), side=-1, fs=8)
bx.text(ox + w + 14, oy - 2, f"Ролик, разрез.\nОтверстие Ø{g.РОЛИК_ОТВ}, свободно на оси Ø{g.ОСЬ_D:.0f}.\n"
        f"Канавка: дно {g.КАНАВКА_ДНО}, стенки {g.КАНАВКА_УГОЛ:.0f}° от радиуса.", fontsize=9, va="center")
# ось
L = g.ЩЕКА_НАР1 - g.ЩЕКА_ВН0
ox, oy = 8, 55
bx.add_patch(Rectangle((ox, oy - g.ОСЬ_ШЛЯПКА_D / 2), g.ОСЬ_ШЛЯПКА_Н, g.ОСЬ_ШЛЯПКА_D, fc="#d6dbe0", ec=INK))
bx.add_patch(Rectangle((ox + g.ОСЬ_ШЛЯПКА_Н, oy - g.ОСЬ_D / 2), L, g.ОСЬ_D, fc="#d6dbe0", ec=INK))
dim(bx, (ox + g.ОСЬ_ШЛЯПКА_Н, oy + g.ОСЬ_D / 2), (ox + g.ОСЬ_ШЛЯПКА_Н + L, oy + g.ОСЬ_D / 2), f"{L:.1f}", off=(0, 4))
dim(bx, (ox, oy - g.ОСЬ_ШЛЯПКА_D / 2), (ox + g.ОСЬ_ШЛЯПКА_Н, oy - g.ОСЬ_ШЛЯПКА_D / 2), f"{g.ОСЬ_ШЛЯПКА_Н}", off=(0, -3), side=-1, fs=8)
bx.text(ox + L + 8, oy, f"Ось Ø{g.ОСЬ_D:.0f}, шляпка Ø{g.ОСЬ_ШЛЯПКА_D:.0f}", fontsize=9, va="center")
# винт
ox, oy = 8, 28
bx.add_patch(Rectangle((ox, oy - g.БАРАШЕК_D / 2), g.БАРАШЕК_Н, g.БАРАШЕК_D, fc="#d6dbe0", ec=INK))
bx.add_patch(Rectangle((ox + g.БАРАШЕК_Н, oy - g.ВИНТ_D / 2), g.ВИНТ_L, g.ВИНТ_D, fc="#e8ebee", ec=INK, hatch="////"))
dim(bx, (ox + g.БАРАШЕК_Н, oy + g.ВИНТ_D / 2), (ox + g.БАРАШЕК_Н + g.ВИНТ_L, oy + g.ВИНТ_D / 2), f"{g.ВИНТ_L:.0f}", off=(0, 7))
dim(bx, (ox, oy + g.БАРАШЕК_D / 2), (ox + g.БАРАШЕК_Н, oy + g.БАРАШЕК_D / 2), f"{g.БАРАШЕК_Н:.0f}", off=(0, 2), fs=8)
bx.text(ox + g.БАРАШЕК_Н + g.ВИНТ_L + 6, oy, f"Винт: резьба Ø{g.ВИНТ_D:.0f}, шаг {g.ВИНТ_ШАГ:.0f}, глубина {g.ВИНТ_ГЛУБИНА:.0f};\n"
        f"барашек Ø{g.БАРАШЕК_D:.0f}", fontsize=9, va="center")
# гайка
ox, oy = 8, 8
r = g.ГАЙКА_S / np.sqrt(3)
bx.add_patch(Polygon([(ox + 7 + r * np.cos(np.radians(a + 30)), oy + r * np.sin(np.radians(a + 30))) for a in range(0, 360, 60)],
                     closed=True, fc="#d6dbe0", ec=INK))
bx.add_patch(Circle((ox + 7, oy), g.ВИНТ_D / 2 + g.ЗАЗОР_РЕЗЬБЫ, fc="white", ec=INK))
bx.text(ox + 18, oy, f"Гайка: под ключ {g.ГАЙКА_S:.0f}, высота {g.ГАЙКА_Н:.0f},\nзазор в резьбе {g.ЗАЗОР_РЕЗЬБЫ} по радиусу",
        fontsize=9, va="center")

fig.text(0.01, 0.015, "Профиль бортика по замеру рулеткой: от внутренней кромки до боковины 22–23 мм, фаска 15 × 15 мм (45°). "
         "Клипса садится на верх, фаску и кромку без зазора: во втором пробнике у фаски была щель ~2 мм.",
         fontsize=10, color="#555")
fig.savefig(OUT, dpi=120)
print(OUT)
