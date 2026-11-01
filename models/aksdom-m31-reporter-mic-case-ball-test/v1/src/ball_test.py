# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "manifold3d", "matplotlib", "fonttools"]
# ///
"""Пробник верха шара кейса-микрофона: верхняя половина шара, два варианта полости внутри.
Детали вырезаны из самой модели (mic_case.py из папки модели), поэтому отверстия и поясок те же.
Все размеры в мм.

uv run ball_test.py              -> пробник для печати: ../aksdom-m31-reporter-mic-case-ball-test-v1.3mf
uv run ball_test.py --check      -> нависания каждого варианта
Без uv: pip install numpy manifold3d matplotlib fonttools, дальше python вместо uv run.
"""
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / 'aksdom-m31-reporter-mic-case' / 'v1' / 'src'))
import mic_case as M

NAME = 'aksdom-m31-reporter-mic-case-ball-test'
ROOFS = (60.0, 52.0)        # нависание конуса внутри шара, градусов от вертикали


def marks(n):
    """Метка варианта: насечки на пояске, одна или две."""
    cz = M.BALL_CZ
    return M.union([M.prism([[26.6, -0.6], [28.0, -0.6], [28.0, 0.6], [26.6, 0.6]], cz - 1, cz + 3, 90.0 + i * 8.0) for i in range(n)])


def cap(roof, n):
    """Верхняя половина шара: лежит на столе срезом по экватору, внизу половина пояска."""
    keep = M.BALL_ROOF
    M.BALL_ROOF = roof
    half = M.head().trim_by_plane([0, 0, 1], M.BALL_CZ) - marks(n)
    M.BALL_ROOF = keep
    return half.translate([0, 0, -M.BALL_CZ])


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    caps = [cap(r, i + 1) for i, r in enumerate(ROOFS)]
    if args.check:
        for r, c in zip(ROOFS, caps):
            M.overhangs(f'конус {r:.0f}°', c, r + 1.0)
        sys.exit()
    parts = [(f'ball-{i + 1}', c.translate([68 + i * 84, 110, 0]), None) for i, c in enumerate(caps)]
    out = HERE.parent / f'{NAME}-v1.3mf'
    M.write_3mf(out, parts, NAME)
    for (n, m, _), r in zip(parts, ROOFS):
        b = m.bounding_box()
        print(f'{n}: конус {r:.0f}°, {b[3] - b[0]:.1f} × {b[4] - b[1]:.1f} × {b[5] - b[2]:.1f}, X {b[0]:.0f}–{b[3]:.0f}, объём {m.volume() / 1000:.1f} см³, кусков {len(m.decompose())}, {m.status().name}')
