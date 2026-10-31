"""Связная надпись для кейса-микрофона: каждое слово получается одним куском, точки присоединены к буквам.

Шрифт Satisfy (Apache 2.0) в репозиторий не положен: скачайте Satisfy-Regular.ttf с Google Fonts
в папку fonts/ рядом со скриптом или укажите путь в переменной окружения MIC_FONT.
"""
import os
from functools import lru_cache
from pathlib import Path

import numpy as np
from fontTools.ttLib import TTFont
from manifold3d import CrossSection, FillRule, JoinType
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties

FONT_FILE = os.environ.get('MIC_FONT') or str(Path(__file__).parent / 'fonts' / 'Satisfy-Regular.ttf')
BOLD = 0.34          # утолщение на сторону, мм: без него буквы не связаны и слишком тонкие
TRACK = -0.012       # разрядка в долях кегля
WORD_W = 43.5        # ширина нижнего слова, мм
MAX_SIZE = 11.0      # короткое нижнее слово не раздуваем
GAP = 1.6            # просвет между строками, мм
TOP_SCALE = 1.5      # верхнее слово крупнее, иначе надпись теряется в панели
DOT_AREA = 6.0       # что мельче, считаем точкой


def rnd(cs, d):
    return cs.offset(d, JoinType.Round, 6, 16)


def raw_word(s, size):
    """Слово из отдельных глифов: шаг считаем сами, чтобы управлять разрядкой."""
    font = TTFont(FONT_FILE, fontNumber=0)
    cmap = font.getBestCmap()
    hmtx = font['hmtx']
    upem = font['head'].unitsPerEm
    prop = FontProperties(fname=FONT_FILE)
    x = 0.0
    parts = []
    for ch in s:
        polys = [np.asarray(p, float)[:-1] / 10.0 for p in TextPath((x * 10.0, 0), ch, size=size * 10.0, prop=prop).to_polygons() if len(p) > 3]
        parts.append(CrossSection(polys, FillRule.EvenOdd))
        x += hmtx[cmap[ord(ch)]][0] / upem * size + TRACK * size
    out = parts[0]
    for p in parts[1:]:
        out = out + p
    return out


def merge_dots(cs):
    """Точки двигает до касания с буквой: над i вниз, у восклицательного знака вверх."""
    comps = sorted(cs.decompose(), key=lambda c: -c.area())
    main = comps[0]
    for dot in comps[1:]:
        if dot.area() < 0.3:
            continue
        if dot.area() > DOT_AREA:
            main = main + dot
            continue
        for k in range(60):
            hit = None
            for sign in (-1, 1):
                moved = dot.translate([0, sign * 0.1 * k])
                if (moved ^ main).area() > 1.0:
                    hit = moved
                    break
            if hit is not None:
                main = main + hit
                break
        else:
            main = main + dot
    return main


def word(s, size):
    w = rnd(raw_word(s, size), BOLD)
    w = rnd(rnd(w, 0.22), -0.22)        # закрыть щели тоньше 0,44 мм
    return merge_dots(w)


def fit_size(s):
    """Кегль, при котором слово занимает ширину WORD_W, но не больше MAX_SIZE."""
    size = 10.0
    for _ in range(4):
        b = word(s, size).bounds()
        size *= WORD_W / (b[2] - b[0])
    return min(size, MAX_SIZE)


def thinnest(cs):
    """Толщина самого тонкого места, на котором слово ещё держится одним куском."""
    best = 0.0
    a = cs.area()
    for r in np.arange(0.2, 1.2, 0.05):
        o = rnd(rnd(cs, -r), r)
        c = [p for p in o.decompose() if p.area() > 0.4]
        if len(c) == 1 and o.area() > 0.75 * a:
            best = 2 * r
    return best


@lru_cache(maxsize=None)
def lines(top, bottom, zc):
    """Две строки по центру панели. Возвращает (слова с окнами, контур без окон для выемки, кегль)."""
    size = fit_size(bottom)
    a = word(top, size * TOP_SCALE)
    b = word(bottom, size)
    ba, bb = a.bounds(), b.bounds()
    a = a.translate([-(ba[0] + ba[2]) / 2, -ba[1] + GAP / 2])
    b = b.translate([-(bb[0] + bb[2]) / 2, -bb[3] - GAP / 2])
    all_ = a + b
    t = all_.bounds()
    all_ = all_.translate([0, zc - (t[1] + t[3]) / 2])

    def area(p):
        p = np.asarray(p)
        return 0.5 * np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1])
    outers = [p for p in all_.to_polygons() if area(p) > 0]
    return all_, CrossSection(outers, FillRule.NonZero), size


def stats(top, bottom):
    """Число деталей надписи и самое тонкое место, для подписи на картинке."""
    size = fit_size(bottom)
    a, b = word(top, size * TOP_SCALE), word(bottom, size)
    return len(a.decompose()) + len(b.decompose()), min(thinnest(a), thinnest(b))
