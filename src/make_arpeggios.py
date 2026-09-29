# -*- coding: utf-8 -*-
"""
生成 PNG 系列：指定大调各和弦的分解和弦（琶音）练习页。
每个和弦 12 个把位，每把位 = 3 个独立四分音符（单音、无束杠）自低到高；
3 行钢琴大谱表，每行 4 组。

用法：python -X utf8 make_arpeggios.py <C|G|F>   # 不带参数则生成全部调
输出：Traid/<Key of X>/<key>_arpeggios.png ×7
（和弦枚举与调性数据复用 make_chord_inversions.py，绘图元件见 staff_lib.py）
"""
import os
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from staff_lib import GRAY, didx, pitch_y, draw_grand_staff, draw_note, ctext
from make_chord_inversions import (build_triads, KEYS, INV_NAMES, TREBLE_FROM, OUT_ROOT)

DPI = 200
X_MIN, X_MAX = 0.0, 95.0
Y_MIN, Y_MAX = 0.0, 100.0

N_PER_ROW = 4                          # 每行 4 组
ROW_TREBLE_BOTTOM = [84.0, 54.0, 24.0]  # 各行高音谱底线（行距 30）
GAP_STAFF = 10.0                       # 高音谱底线到低音谱底线的距离

NOTE_DX = 2.0                          # 组内相邻音符间距
TREBLE_BOTTOM_NOTE = ("E", 4)
BASS_BOTTOM_NOTE = ("G", 2)

def make_sheet(spec, chord):
    triads = build_triads(chord["tones"])
    n = len(triads)
    slot_w = (88.5 - 13.0) / N_PER_ROW
    disp = spec["disp"]

    fig = plt.figure(figsize=(12.5, 13.16))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(X_MIN, X_MAX)
    ax.set_ylim(Y_MIN, Y_MAX)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    ctext(ax, 47.5, 96.6, "%s 和弦分解（琶音）练习 · 12 个把位 · 钢琴大谱表"
          % chord["name"], 20, bold=True)
    first, last = triads[0][0][0], triads[-1][0][-1]
    lo_note = "%s%d" % (disp.get(first[0], first[0]), first[1])
    hi_note = "%s%d" % (disp.get(last[0], last[0]), last[1])
    ctext(ax, 47.5, 93.0,
          "%s ｜ 每个把位 3 个四分音符自低到高依次弹奏（单音，无连音）｜ A1（低音谱下方第 3 线）音域内最低排列起，4 轮 ×（原位+第一转位+第二转位）= %d 组，分 3 行，实际跨度 %s – %s%s"
          % (spec["key_name"], n, lo_note, hi_note,
             (" ｜ " + spec["sig"]) if spec["sig"] else ""),
          10.5, color="#555555")

    thr = didx(TREBLE_FROM)
    for row, treble_bottom in enumerate(ROW_TREBLE_BOTTOM):
        bass_bottom = treble_bottom - GAP_STAFF
        draw_grand_staff(ax, treble_bottom, bass_bottom,
                         final_barline=(row == len(ROW_TREBLE_BOTTOM) - 1),
                         key_sharps=spec.get("sharps", 0),
                         key_flats=spec.get("flats", 0))

        # 组间浅色分隔虚线
        for i in range(N_PER_ROW - 1):
            ax.vlines(13.0 + slot_w * (i + 0.5), bass_bottom - 10.6, treble_bottom + 8.6,
                      color="#dddddd", lw=0.9, linestyles=(0, (4, 3)), zorder=1)

        chunk = triads[row * N_PER_ROW:(row + 1) * N_PER_ROW]
        for i, (notes, inv) in enumerate(chunk):
            x0 = 13.0 + slot_w * i + 2.0
            center = x0 + NOTE_DX
            if didx(notes[0]) < thr:
                bottom_y, bottom_note = bass_bottom, BASS_BOTTOM_NOTE
            else:
                bottom_y, bottom_note = treble_bottom, TREBLE_BOTTOM_NOTE
            for j, nt in enumerate(notes):
                x = x0 + NOTE_DX * j
                y = pitch_y(nt, bottom_note, bottom_y)
                draw_note(ax, x, y, bottom_y)
                if nt == ("C", 4) and j == 0:      # 最低音为中央C
                    ctext(ax, x, treble_bottom - 2.6, "中央C", 8.5, color=GRAY)
            ctext(ax, center, bass_bottom - 5.4, chord["sym"][inv], 12, bold=True)
            ctext(ax, center, bass_bottom - 7.6, INV_NAMES[inv], 10.5)
            ctext(ax, center, bass_bottom - 9.7,
                  "·".join(disp.get(nt[0], nt[0]) for nt in notes), 9, color=GRAY)

    t = chord["tones"]
    ctext(ax, 47.5, 1.8,
          "%s = %s · %s · %s ｜ 低音 = %s → 原位；%s → 第一转位；%s → 第二转位 ｜ 练习建议：先分手慢练、时值均匀；熟练后可来回弹（如 %s–%s–%s–%s）或将整行连奏"
          % (chord["name"], t[0], t[1], t[2], t[0], t[1], t[2], t[0], t[1], t[2], t[1]),
          10, color=GRAY)

    os.makedirs(os.path.join(OUT_ROOT, spec["folder"]), exist_ok=True)
    out = os.path.join(OUT_ROOT, spec["folder"], "%s_arpeggios.png" % chord["key"])
    fig.savefig(out, dpi=DPI, facecolor="white")
    plt.close(fig)
    return out, n

if __name__ == "__main__":
    want = sys.argv[1] if len(sys.argv) > 1 else None
    for k, spec in KEYS.items():
        if want and k != want:
            continue
        for chord in spec["chords"]:
            out, n = make_sheet(spec, chord)
            print("%-36s %2d 组" % (out, n))
