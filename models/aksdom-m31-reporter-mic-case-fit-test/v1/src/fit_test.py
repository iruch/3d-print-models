# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "manifold3d", "matplotlib", "fonttools"]
# ///
"""Пробник кейса-микрофона: оба байонета, колодец с пластиной и выемка под надпись.
Детали вырезаны из самой модели (mic_case.py из папки модели), поэтому посадки те же и печатаются так же.
Все размеры в мм, оси как в mic_case.py: Z = 0 — низ бокса, Z = 82 — его верх.

uv run fit_test.py                 -> пробник для печати: ../aksdom-m31-reporter-mic-case-fit-test-v1.3mf
uv run fit_test.py --filled        -> сцена для картинки: пробник в сборке, не для печати
uv run fit_test.py --top слово --bottom слово -> другая надпись на плитке
Без uv: pip install numpy manifold3d matplotlib fonttools, дальше python вместо uv run.
"""
import argparse
import sys
from pathlib import Path

from manifold3d import Manifold

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / 'aksdom-m31-reporter-mic-case' / 'v1' / 'src'))
import mic_case as M

NAME = 'aksdom-m31-reporter-mic-case-fit-test'
LUG_HS = (3.6, 3.8, 4.0)        # кольца головы: высота лапки, зазор до плиты 0,4 / 0,2 / 0 мм
LUG_GAPS = (0.1, 0.2, 0.3)      # ручка: зазор лапки до конуса плиты
TOP_HALF = 22.0                 # верх колодца: половина стороны
WELL_WALL = 3.2                 # стенка вокруг колодца снизу
Z_LOW = M.PEDESTAL_Z - 3.0      # кусок бокса начинается под дном колодца
Z_STEP = 60.0                   # выше этой высоты он широкий, под гнездо головы
SOCKET_H = M.SPIGOT_L + 4.0     # кусок бокса с гнездом ручки
SOCKET_W = 38.0
TILE = (54.0, 32.0, 6.0)        # плитка с выемкой под надпись
STUB_L = 6.0                    # длина обрубка ручки под плечом


def block(hx, hy, r, z0, z1):
    return M.rrect(2 * hx, 2 * hy, r).extrude(z1 - z0).translate([0, 0, z0])


def well_outer():
    """Узкий низ вокруг колодца и широкий верх вокруг гнезда, между ними скос: вверх дном он печатается без поддержек."""
    wx, wy = M.well_half()
    lx, ly = wx + WELL_WALL, wy + WELL_WALL
    low = block(lx, ly, 3.0, Z_LOW, Z_STEP - (TOP_HALF - min(lx, ly)))
    top = block(TOP_HALF, TOP_HALF, 3.0, Z_STEP, M.BOX_H)
    neck = Manifold.batch_hull([block(lx, ly, 3.0, Z_STEP - (TOP_HALF - min(lx, ly)) - 0.01, Z_STEP - (TOP_HALF - min(lx, ly))), block(TOP_HALF, TOP_HALF, 3.0, Z_STEP, Z_STEP + 0.01)])
    return low + neck + top


def well_piece(bumps=True):
    out = well_outer() - M.well() - M.top_socket() + M.blade()
    return out + M.top_bumps() if bumps else out


def socket_piece():
    return M.rrect(SOCKET_W, SOCKET_W, 4.0).extrude(SOCKET_H) - M.bottom_socket()


def rim_marks(n):
    """Метка кольца: одна, две или три насечки на шейке."""
    cut = [M.prism([[17.4, -0.45], [18.6, -0.45], [18.6, 0.45], [17.4, 0.45]], M.BOX_H + 1.5, M.BOX_H + 6.0, M.BAYONET[0] + i * 7.0) for i in range(n)]
    return M.union(cut)


def head_ring(lug_h, n):
    """Шейка с юбкой и лапками, как у головы, без шара."""
    keep = M.LUG_H
    M.LUG_H = lug_h
    ring = M.collar(M.revolve(M.neck_prof())) - rim_marks(n)
    M.LUG_H = keep
    return ring


def end_marks(n):
    """Метка обрубка ручки: одна, две или три ямки на торце."""
    cut = [Manifold.cylinder(1.8, 1.0, 1.0, 24).translate([-3.5 + 3.5 * i, 0, -STUB_L - 1.0]) for i in range(n)]
    return M.union(cut)


def handle_stub(gap, n=0, bumps=True):
    """Хвостовик с плечом и коротким куском ручки."""
    keep = M.BOT_LUG_GAP
    M.BOT_LUG_GAP = gap
    prof = M.shoulder()
    stub = M.spigot(M.revolve(prof + [[prof[-1][0], -STUB_L], [0, -STUB_L]]), bumps)
    M.BOT_LUG_GAP = keep
    return stub - end_marks(n) if n else stub


def tile():
    """Плитка с выемкой и слова надписи. В боксе выемка стоит на боковой стенке, поэтому плитка печатается стоя, надписью вниз головой."""
    full, solid, _ = M.lettering.lines(M.TEXT[0], M.TEXT[1], 0.0)
    w, h, t = TILE
    pocket = solid.offset(M.POCKET_GAP, M.JoinType.Round, 6, 18).extrude(M.POCKET_D + 1).translate([0, 0, t - M.POCKET_D])
    plate = M.rrect(w, h, 3.0).extrude(t) - pocket
    return plate.rotate([-90, 0, 0]), full.extrude(M.LETTER_T).rotate([180, 0, 0])


def on_bed(m, x, y):
    """Ставит деталь на стол центром в точку (x, y)."""
    b = m.bounding_box()
    return m.translate([x - (b[0] + b[3]) / 2, y - (b[1] + b[4]) / 2, -b[2]])


def plate():
    parts = [('well', on_bed(well_piece().rotate([180, 0, 0]), 40, 165)),
             ('handle-socket', on_bed(socket_piece().rotate([180, 0, 0]), 100, 170))]
    for i, h in enumerate(LUG_HS):
        parts.append((f'head-ring-{i + 1}', on_bed(head_ring(h, i + 1), 32 + i * 42, 105)))
    for i, g in enumerate(LUG_GAPS):
        parts.append((f'handle-stub-{i + 1}', on_bed(handle_stub(g, i + 1).rotate([180, 0, 0]), 28 + i * 37, 55)))
    t, w = tile()
    parts.append(('letters-tile', on_bed(t, 170, 110)))
    parts.append(('letters', on_bed(w, 170, 60)))
    return parts


def scene():
    """Пробник в сборке: передатчик с кольцом головы в колодце, ручка в гнезде."""
    tb, tg, tc = M.transmitter()
    a = [0, 0, -Z_LOW]
    flip = lambda m: m.rotate([180, 0, 0]).translate([62, 0, SOCKET_H])     # кусок с гнездом ручкой вверх, иначе её не видно
    return [(f'{NAME}-filled', well_piece().translate(a) + flip(socket_piece()), None),
            ('head-ring', head_ring(LUG_HS[1], 2).translate(a), '#E9E4D8'),
            ('handle-stub', flip(handle_stub(LUG_GAPS[1], 2)), '#E9E4D8'),
            ('transmitter', (tb + tg + tc).translate(a), '#2B2F36')]


def check():
    top, free = well_piece(), well_piece(False)
    for i, h in enumerate(LUG_HS):
        r = head_ring(h, i + 1)
        M.joint(f'кольцо {i + 1}', r, r, top, free, M.TOP_SENSE, 1)
    sock = socket_piece()
    for i, g in enumerate(LUG_GAPS):
        M.joint(f'ручка {i + 1}', handle_stub(g), handle_stub(g, bumps=False), sock, sock, M.BOT_SENSE, -1)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--filled', action='store_true')
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--top', default=M.TEXT[0])
    ap.add_argument('--bottom', default=M.TEXT[1])
    ap.add_argument('--out')
    args = ap.parse_args()
    M.TEXT = (args.top, args.bottom)
    if args.check:
        check()
        sys.exit()
    if args.filled:
        parts, name = scene(), f'{NAME}-filled'
    else:
        parts, name = [(n, m, None) for n, m in plate()], f'{NAME}-v1'
    out = Path(args.out) if args.out else HERE.parent / f'{name}.3mf'
    M.write_3mf(out, parts, name)
    total = 0.0
    for n, m, _ in parts:
        b = m.bounding_box()
        total += m.volume()
        print(f'{n}: {b[3] - b[0]:.1f} × {b[4] - b[1]:.1f} × {b[5] - b[2]:.1f}, X {b[0]:.0f}–{b[3]:.0f}, Y {b[1]:.0f}–{b[4]:.0f}, объём {m.volume() / 1000:.1f} см³, кусков {len(m.decompose())}, {m.status().name}')
    print(f'{out.name}: сплошной объём {total / 1000:.1f} см³')
