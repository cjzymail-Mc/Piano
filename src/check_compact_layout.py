# -*- coding: utf-8 -*-
"""
紧凑琶音页几何校验：对全部调 x 全部和弦的每个把位（单行 12 列布局），
用包围盒断言以下五类零相交（余量 0.05 线距）：
  1) 和弦名称带（两谱表中间 bass+8.25）vs 本组符头/符干/加线
  2) 下方音名标签 vs 本组谱表下方墨迹
  3) 本块标签 vs 下一块伸出谱表上方的墨迹（含标题 vs 上一块标签）
  4) 标题（谱表上方左侧）vs 本块谱表上方墨迹
  5) 相邻标签互不串位
运行：python -X utf8 src/check_compact_layout.py
"""
from staff_lib import didx
from make_chord_inversions import (KEYS, build_triads, TREBLE_FROM,
                                   TREBLE_BOTTOM_NOTE, BASS_BOTTOM_NOTE,
                                   X_FIRST, X_LAST)
from make7_chord_inversions import SEVENTHS, build_sevenths
from make_compact_collection import (BLK_TR, AR_TITLE_DY, AR_G, AR_COLS,
                                     AR_NOTE_DX, AR_SYM_DY, AR_LBL_DY)

HEAD_HW, HEAD_HH = 0.55, 0.55        # 符头半宽/半高（略放大，保守）
STEM_HW = 0.16                       # 符干半宽（lw 2pt ≈ 0.21u）
LEDGER_HW, LEDGER_HH = 0.95, 0.10    # 加线半宽/半厚
MARGIN = 0.05

def text_box(cx, cy, s, pt, ha="center"):
    """文本包围盒：CJK 1.05em、ASCII 0.52em 估宽，高 1em。"""
    w = sum((1.05 if ord(c) > 0x2E80 else 0.52) for c in s) * pt / 9.474
    h = pt / 9.474 / 2
    x0 = cx - w + 0.12 if ha == "left" else cx - w / 2 - 0.12
    return (x0, x0 + w + 0.24, cy - h, cy + h)

def overlap(a, b, margin=MARGIN):
    return not (a[1] + margin <= b[0] or b[1] + margin <= a[0] or
                a[3] + margin <= b[2] or b[3] + margin <= a[2])

def title_str(spec, chord, n):
    return "%s 和弦分解（琶音）· %s %s %s · 每组 %d 音 · A1 – F6 ｜ 调号" % (
        chord["name"], spec["key_name"], chord["roman"], chord["quality"], n)

def group_geometry(spec, chord, notes, inv, gi):
    """返回 dict：标题/sym/lbl 包围盒 + 全部墨迹盒 + 块号。"""
    treble = BLK_TR[0]                       # 块间相对几何同构，用块 0 校验块内，
    bass = treble - AR_G                     # 块间纵向关系单独校验
    slot_w = (X_LAST - X_FIRST) / AR_COLS
    x0g = X_FIRST + slot_w * gi + 0.7
    center = x0g + AR_NOTE_DX * (len(notes) - 1) / 2.0
    thr = didx(TREBLE_FROM)
    by, bn = ((bass, BASS_BOTTOM_NOTE) if didx(notes[0]) < thr
              else (treble, TREBLE_BOTTOM_NOTE))
    ink = []
    for j, nt in enumerate(notes):
        x = x0g + AR_NOTE_DX * j
        y = by + (didx(nt) - didx(bn)) * 0.5
        ink.append((x - HEAD_HW, x + HEAD_HW, y - HEAD_HH, y + HEAD_HH))
        if y < by + 2.0:                                   # 上符干
            ink.append((x + 0.42 - STEM_HW, x + 0.42 + STEM_HW, y, y + 3.4))
        else:                                              # 下符干
            ink.append((x - 0.42 - STEM_HW, x - 0.42 + STEM_HW, y - 3.4, y))
        top, bot = by + 4, by                              # 加线
        if y > top:
            for k in range(1, int(y - top) + 1):
                ink.append((x - LEDGER_HW, x + LEDGER_HW,
                            top + k - LEDGER_HH, top + k + LEDGER_HH))
        elif y < bot:
            for k in range(1, int(bot - y) + 1):
                ink.append((x - LEDGER_HW, x + LEDGER_HW,
                            bot - k - LEDGER_HH, bot - k + LEDGER_HH))
    disp = spec["disp"]
    lbl = " ".join(disp.get(t[0], t[0]) + str(t[1]) for t in notes)
    return dict(tag="%s[%d] %s" % (chord["name"], gi, chord["sym"][inv]),
                treble=treble, bass=bass,
                ttl=text_box(4.0, treble + AR_TITLE_DY,
                             title_str(spec, chord, len(notes)), 11, ha="left"),
                sym=text_box(center, bass + AR_SYM_DY, chord["sym"][inv], 11),
                lbl=text_box(center, bass + AR_LBL_DY, lbl, 8.5),
                ink=ink)

def check(spec, chord, build_fn):
    bad = []
    gs = [group_geometry(spec, chord, notes, inv, gi)
          for gi, (notes, inv) in enumerate(build_fn(chord["tones"]))]
    for g in gs:
        for ib in g["ink"]:                                # 1) 名称带 vs 墨迹
            if overlap(g["sym"], ib):
                bad.append("名称x墨迹 %s %s" % (g["tag"], [round(v, 2) for v in ib]))
        for ib in g["ink"]:                                # 2) 标签 vs 谱表下方墨迹
            if ib[3] < g["bass"] and overlap(g["lbl"], ib):
                bad.append("标签x低音 %s %s" % (g["tag"], [round(v, 2) for v in ib]))
        for ib in g["ink"]:                                # 4) 标题 vs 谱表上方墨迹
            if ib[3] > g["treble"] + 4 and overlap(g["ttl"], ib):
                bad.append("标题x顶音 %s %s" % (g["tag"], [round(v, 2) for v in ib]))
    # 3) 块间纵向关系见 inter_block()
    # 5) 相邻标签串位
    for a, b in zip(gs, gs[1:]):
        if overlap(a["lbl"], b["lbl"]):
            bad.append("标签串位 %s / %s" % (a["tag"], b["tag"]))
    return bad

def inter_block():
    """块间纵向校验（对所有块对，用最大墨迹包络）。"""
    bad = []
    top_ink = BLK_TR[0] + 4 + 8.05 + 0.0   # F6 符头顶 = treble+8.05
    lbl_bot = BLK_TR[0] - AR_G + AR_LBL_DY - 0.45
    for hi_blk in BLK_TR[1:]:
        nxt_top_ink = hi_blk + 4 + 8.05
        if lbl_bot <= nxt_top_ink + MARGIN:
            bad.append("块距不足: 上块标签底 %.2f vs 下块顶墨迹 %.2f"
                       % (lbl_bot, nxt_top_ink))
        ttl_top = hi_blk + AR_TITLE_DY + 0.58
        if ttl_top >= lbl_bot - MARGIN:
            bad.append("标题x上块标签: %.2f / %.2f" % (ttl_top, lbl_bot))
        lbl_bot = hi_blk - AR_G + AR_LBL_DY - 0.45
    if BLK_TR[0] + 4 + 8.05 > 100 - MARGIN:
        bad.append("顶墨迹越界 %.2f" % (BLK_TR[0] + 4 + 8.05))
    if BLK_TR[-1] - AR_G + AR_LBL_DY - 0.45 < MARGIN:
        bad.append("底标签越界 %.2f" % (BLK_TR[-1] - AR_G + AR_LBL_DY - 0.45))
    return bad

def chord_ink(notes, bottom_y, bottom_note, x):
    """柱式和弦墨迹：符头纵叠 + 共用符干 + 二度错位（复刻 staff_lib.draw_chord）。"""
    pairs = sorted(((bottom_y + (didx(n) - didx(bottom_note)) * 0.5, n)
                    for n in notes), key=lambda p: p[0])
    ys = [p[0] for p in pairs]
    shift = [False] * len(ys)
    for i in range(1, len(ys)):
        if ys[i] - ys[i - 1] < 0.99:
            shift[i] = True
    y_mid = bottom_y + 2.0
    up = (y_mid - ys[0]) >= (ys[-1] - y_mid)
    dx = 1.08 if up else -1.08
    ink = []
    for (y, _n), sh in zip(pairs, shift):
        hx = x + (dx if sh else 0.0)
        ink.append((hx - HEAD_HW, hx + HEAD_HW, y - HEAD_HH, y + HEAD_HH))
        top, bot = bottom_y + 4, bottom_y
        if y > top:
            for k in range(1, int(y - top) + 1):
                ink.append((hx - LEDGER_HW, hx + LEDGER_HW,
                            top + k - LEDGER_HH, top + k + LEDGER_HH))
        elif y < bot:
            for k in range(1, int(bot - y) + 1):
                ink.append((hx - LEDGER_HW, hx + LEDGER_HW,
                            bot - k - LEDGER_HH, bot - k + LEDGER_HH))
    if up:
        yt = max(ys[0] + 3.4, ys[-1] + 0.65)
        ink.append((x + 0.42 - STEM_HW, x + 0.42 + STEM_HW, ys[0], yt))
    else:
        yb = min(ys[-1] - 3.4, ys[0] - 0.65)
        ink.append((x - 0.42 - STEM_HW, x - 0.42 + STEM_HW, yb, ys[-1]))
    return ink

def check_chart(spec, chord, build_fn):
    """柱式条带校验：名称带/标签/标题 vs 墨迹，条带上下越界。"""
    from make_compact_collection import CH_SPAN, CH_BASS, CH_TREBLE, CH_SYM_DY, CH_LBL_DY
    bad = []
    chords = build_fn(chord["tones"])
    n = len(chords)
    disp = spec["disp"]
    thr = didx(TREBLE_FROM)
    ttl = text_box(47.5, CH_TREBLE + 6.2,
                   "%s 和弦与全部转位（%s %s %s）· 跨度 A1 – F6 ｜ 调号：1 个降号（B♭）"
                   % (chord["name"], spec["key_name"], chord["roman"],
                      chord["quality"]), 11.5)
    for i, (notes, inv) in enumerate(chords):
        x = X_FIRST + i * (X_LAST - X_FIRST) / (n - 1)
        by, bn = ((CH_BASS, BASS_BOTTOM_NOTE) if didx(notes[0]) < thr
                  else (CH_TREBLE, TREBLE_BOTTOM_NOTE))
        ink = chord_ink(notes, by, bn, x)
        tag = "%s[%d] %s" % (chord["name"], i, chord["sym"][inv])
        sym = text_box(x, CH_BASS + CH_SYM_DY, chord["sym"][inv], 11)
        lbl = text_box(x, CH_BASS + CH_LBL_DY,
                       " ".join(disp.get(t[0], t[0]) + str(t[1]) for t in notes), 8.5)
        for ib in ink:
            if overlap(sym, ib):
                bad.append("柱式名称x墨迹 %s %s" % (tag, [round(v, 2) for v in ib]))
            if ib[3] < CH_BASS and overlap(lbl, ib):
                bad.append("柱式标签x低音 %s %s" % (tag, [round(v, 2) for v in ib]))
            if ib[3] > CH_TREBLE + 4 and overlap(ttl, ib):
                bad.append("柱式标题x顶音 %s %s" % (tag, [round(v, 2) for v in ib]))
            if ib[3] > CH_SPAN - MARGIN:
                bad.append("柱式顶越界 %s %s" % (tag, [round(v, 2) for v in ib]))
            if ib[2] < MARGIN:
                bad.append("柱式底越界 %s %s" % (tag, [round(v, 2) for v in ib]))
    return bad

def main():
    fails = 0
    for spec in KEYS.values():
        for c in spec["chords"]:
            fails += len(check(spec, c, build_triads))
            fails += len(check_chart(spec, c, build_triads))
    for k, chords7 in SEVENTHS.items():
        for c in chords7:
            fails += len(check(KEYS[k], c, build_sevenths))
            fails += len(check_chart(KEYS[k], c, build_sevenths))
    ib = inter_block()
    fails += len(ib)
    for b in ib:
        print(b)
    print("checked: 3 keys x (7 triads + 7 sevenths) x 12 positions x (琶音+柱式) + blocks")
    print("FAILURES:", fails)
    return fails

if __name__ == "__main__":
    raise SystemExit(1 if main() else 0)
