"""Цветовые наборы кейса-микрофона: цвета головы, бокса, ручки и надписи.
Из них строятся листы с цветами (sheets.py) и раскладки по цветам для печати одной нитью (mic_case.py --plates).
"""
K, Wh, Yl, Bl, Rd, Tl, Pa = 'black', 'white', 'yellow', 'blue', 'red', 'teal', 'pastel'

# названия как в FILAMENTS.md
NAMES = {K: 'чёрный', Wh: 'белый', Yl: 'жёлтый шёлковый', Bl: 'синий', Rd: 'красный',
         Tl: 'сине-зелёный шёлковый', Pa: 'многоцветный пастельный'}
PARTS = ('head', 'box', 'handle', 'words')   # в таком порядке идут цвета в наборе
PART_NAMES = dict(head='голова', box='бокс', handle='ручка', words='надпись')

COMBOS = [
    ('Белый бокс', [(K, Wh, K, Rd), (K, Wh, K, Bl), (Wh, Wh, Yl, Yl), (Tl, Wh, Tl, Tl), (Rd, Wh, Rd, Rd), (Bl, Wh, Bl, Bl)]),
    ('Чёрный бокс', [(K, K, K, Yl), (Yl, K, Yl, Yl), (Wh, K, Wh, Wh), (Rd, K, Rd, Rd), (Tl, K, Tl, Tl), (Bl, K, Bl, Wh)]),
    ('Красный бокс', [(K, Rd, K, Wh), (K, Rd, K, Yl), (Wh, Rd, Wh, Wh), (Wh, Rd, K, Wh), (Yl, Rd, K, Yl), (Bl, Rd, Bl, Wh)]),
    ('Синий бокс', [(Wh, Bl, Wh, Wh), (Wh, Bl, Wh, Yl), (K, Bl, K, Wh), (Yl, Bl, Yl, Yl), (Rd, Bl, Rd, Wh), (Tl, Bl, Tl, Wh)]),
    ('Жёлтый шёлковый бокс', [(K, Yl, K, K), (Wh, Yl, Wh, K), (Bl, Yl, Bl, Bl), (Rd, Yl, Rd, Rd), (K, Yl, K, Rd), (Tl, Yl, Tl, Tl)]),
    ('Сине-зелёный шёлковый бокс', [(K, Tl, K, Wh), (Wh, Tl, Wh, Wh), (Yl, Tl, Yl, Yl), (K, Tl, K, Yl), (Wh, Tl, K, Wh), (Bl, Tl, Bl, Wh)]),
    ('Пастельный бокс', [(Wh, Pa, Wh, K), (Wh, Pa, Wh, Bl), (K, Pa, K, K), (K, Pa, K, Wh), (Rd, Pa, Rd, Rd), (Tl, Pa, Tl, Tl)]),
    ('Смелые сочетания', [(Pa, Wh, Pa, K), (Pa, K, Pa, Wh), (Pa, Bl, Pa, Wh), (Pa, Rd, Pa, Wh), (Rd, Yl, Bl, K), (Tl, Rd, Yl, Wh)]),
]


def sets():
    """Наборы с номерами, как на листах цветов: [(номер, ряд, (голова, бокс, ручка, надпись))]."""
    out = []
    for label, row in COMBOS:
        for cc in row:
            out.append((len(out) + 1, label, cc))
    return out


def prints(cc):
    """Печати одного набора: на каждый цвет одна печать со всеми деталями этого цвета. [(цвет, (детали))]."""
    groups = {}
    for part, c in zip(PARTS, cc):
        groups.setdefault(c, []).append(part)
    return [(c, tuple(p)) for c, p in groups.items()]
