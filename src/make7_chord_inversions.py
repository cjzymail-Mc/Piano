# -*- coding: utf-8 -*-
"""
生成 PNG 系列：指定大调的顺阶七和弦柱式总览图（钢琴大谱表）。
每个七和弦从 A1 音域内最低排列起，完整 3 轮 ×（原位/第一/第二/第三转位）= 12 个。

七和弦体系：Imaj7 · iim7 · iiim7 · IVmaj7 · V7 · vim7 · viim7♭5
用法：python -X utf8 make7_chord_inversions.py <C|G|F>   # 不带参数则生成全部调
输出：Seventh/<Key of X>/<key>_chord_inversions.png ×7
（调性数据复用 make_chord_inversions.KEYS——加新调只改那一处；绘图元件见 staff_lib.py）
"""
import os
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from staff_lib import (GRAY, didx, idx_note, LETTERS, draw_grand_staff,
                       draw_chord, ctext)
from make_chord_inversions import (KEYS, LO, HI, TREBLE_FROM,
                                   TREBLE_BOTTOM_Y, BASS_BOTTOM_Y,
                                   TREBLE_BOTTOM_NOTE, BASS_BOTTOM_NOTE,
                                   X_FIRST, X_LAST)

OUT_ROOT = "Seventh"                  # 七和弦成品根目录
DPI = 200
X_MIN, X_MAX = 0.0, 95.0
Y_MIN, Y_MAX = 18.0, 66.0

N_CHORDS = 12                         # 3 轮 × 4 种转位
INV7_NAMES = ["原位", "第一转位", "第二转位", "第三转位"]
TONE_ROLES7 = ["根音", "三音", "五音", "七音"]

# ---------------- 各调七和弦数据（音名带 ♯/♭ 时按本位音字母定位） ----------------
SEVENTHS = {
    "C": [
        dict(key="cmaj7", name="Cmaj7", roman="I 级", quality="大七和弦",
             tones=["C", "E", "G", "B"], sym=["Cmaj7", "Cmaj7/E", "Cmaj7/G", "Cmaj7/B"]),
        dict(key="dm7", name="Dm7", roman="ii 级", quality="小七和弦",
             tones=["D", "F", "A", "C"], sym=["Dm7", "Dm7/F", "Dm7/A", "Dm7/C"]),
        dict(key="em7", name="Em7", roman="iii 级", quality="小七和弦",
             tones=["E", "G", "B", "D"], sym=["Em7", "Em7/G", "Em7/B", "Em7/D"]),
        dict(key="fmaj7", name="Fmaj7", roman="IV 级", quality="大七和弦",
             tones=["F", "A", "C", "E"], sym=["Fmaj7", "Fmaj7/A", "Fmaj7/C", "Fmaj7/E"]),
        dict(key="g7", name="G7", roman="V 级", quality="属七和弦",
             tones=["G", "B", "D", "F"], sym=["G7", "G7/B", "G7/D", "G7/F"]),
        dict(key="am7", name="Am7", roman="vi 级", quality="小七和弦",
             tones=["A", "C", "E", "G"], sym=["Am7", "Am7/C", "Am7/E", "Am7/G"]),
        dict(key="bm7b5", name="Bm7♭5", roman="vii 级", quality="半减七和弦",
             tones=["B", "D", "F", "A"], sym=["Bm7♭5", "Bm7♭5/D", "Bm7♭5/F", "Bm7♭5/A"]),
    ],
    "G": [
        dict(key="gmaj7", name="Gmaj7", roman="I 级", quality="大七和弦",
             tones=["G", "B", "D", "F♯"], sym=["Gmaj7", "Gmaj7/B", "Gmaj7/D", "Gmaj7/F♯"]),
        dict(key="am7", name="Am7", roman="ii 级", quality="小七和弦",
             tones=["A", "C", "E", "G"], sym=["Am7", "Am7/C", "Am7/E", "Am7/G"]),
        dict(key="bm7", name="Bm7", roman="iii 级", quality="小七和弦",
             tones=["B", "D", "F♯", "A"], sym=["Bm7", "Bm7/D", "Bm7/F♯", "Bm7/A"]),
        dict(key="cmaj7", name="Cmaj7", roman="IV 级", quality="大七和弦",
             tones=["C", "E", "G", "B"], sym=["Cmaj7", "Cmaj7/E", "Cmaj7/G", "Cmaj7/B"]),
        dict(key="d7", name="D7", roman="V 级", quality="属七和弦",
             tones=["D", "F♯", "A", "C"], sym=["D7", "D7/F♯", "D7/A", "D7/C"]),
        dict(key="em7", name="Em7", roman="vi 级", quality="小七和弦",
             tones=["E", "G", "B", "D"], sym=["Em7", "Em7/G", "Em7/B", "Em7/D"]),
        dict(key="fsharp_m7b5", name="F♯m7♭5", roman="vii 级", quality="半减七和弦",
             tones=["F♯", "A", "C", "E"], sym=["F♯m7♭5", "F♯m7♭5/A", "F♯m7♭5/C", "F♯m7♭5/E"]),
    ],
    "F": [
        dict(key="fmaj7", name="Fmaj7", roman="I 级", quality="大七和弦",
             tones=["F", "A", "C", "E"], sym=["Fmaj7", "Fmaj7/A", "Fmaj7/C", "Fmaj7/E"]),
        dict(key="gm7", name="Gm7", roman="ii 级", quality="小七和弦",
             tones=["G", "B♭", "D", "F"], sym=["Gm7", "Gm7/B♭", "Gm7/D", "Gm7/F"]),
        dict(key="am7", name="Am7", roman="iii 级", quality="小七和弦",
             tones=["A", "C", "E", "G"], sym=["Am7", "Am7/C", "Am7/E", "Am7/G"]),
        dict(key="bbmaj7", name="B♭maj7", roman="IV 级", quality="大七和弦",
             tones=["B♭", "D", "F", "A"], sym=["B♭maj7", "B♭maj7/D", "B♭maj7/F", "B♭maj7/A"]),
        dict(key="c7", name="C7", roman="V 级", quality="属七和弦",
             tones=["C", "E", "G", "B♭"], sym=["C7", "C7/E", "C7/G", "C7/B♭"]),
        dict(key="dm7", name="Dm7", roman="vi 级", quality="小七和弦",
             tones=["D", "F", "A", "C"], sym=["Dm7", "Dm7/F", "Dm7/A", "Dm7/C"]),
        dict(key="em7b5", name="Em7♭5", roman="vii 级", quality="半减七和弦",
             tones=["E", "G", "B♭", "D"], sym=["Em7♭5", "Em7♭5/G", "Em7♭5/B♭", "Em7♭5/D"]),
    ],
}

def build_sevenths(tones):
    """音域 LO..HI 内该七和弦全部密集排列，按最低音升序取前 N_CHORDS 个。
    与三和弦版同构：start=0..3 对应 原位/一/二/三转位。返回 [(notes, inv), ...]"""
    ti = [LETTERS.index(t[0]) for t in tones]
    lo, hi = didx(LO), didx(HI)
    out = []
    for start in range(4):
        gaps = [(ti[(start + k + 1) % 4] - ti[(start + k) % 4]) % 7 for k in range(3)]
        for octv in range(1, 7):
            base = octv * 7 + ti[start]
            idxs = [base]
            for g in gaps:
                idxs.append(idxs[-1] + g)
            if idxs[0] >= lo and idxs[-1] <= hi:
                out.append(([idx_note(i) for i in idxs], start))
    out.sort(key=lambda c: didx(c[0][0]))
    return out[:N_CHORDS]

# ---------------- 生成 ----------------
def make_chart(spec, chord):
    chords = build_sevenths(chord["tones"])
    n = len(chords)
    xs = [X_FIRST + i * (X_LAST - X_FIRST) / (n - 1) for i in range(n)]
    disp = spec["disp"]

    fig = plt.figure(figsize=(12.5, 6.32))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(X_MIN, X_MAX)
    ax.set_ylim(Y_MIN, Y_MAX)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    ctext(ax, 47.5, 63.2, "%s 和弦与全部转位（%s %s，%s）· 钢琴大谱表"
          % (chord["name"], spec["key_name"], chord["roman"], chord["quality"]), 19, bold=True)
    first, last = chords[0][0][0], chords[-1][0][-1]
    lo_note = "%s%d" % (disp.get(first[0], first[0]), first[1])
    hi_note = "%s%d" % (disp.get(last[0], last[0]), last[1])
    ctext(ax, 47.5, 59.6,
          "低音谱 + 高音谱上下合并 ｜ 自 A1（低音谱下方第 3 线）音域内最低排列起，完整 3 轮 ×（原位+第一+第二+第三转位）= %d 个 ｜ 实际跨度 %s – %s%s"
          % (n, lo_note, hi_note,
             (" ｜ " + spec["sig"]) if spec["sig"] else ""),
          10.5, color="#555555")

    draw_grand_staff(ax, TREBLE_BOTTOM_Y, BASS_BOTTOM_Y, final_barline=True,
                     key_sharps=spec.get("sharps", 0), key_flats=spec.get("flats", 0))

    thr = didx(TREBLE_FROM)
    for x, (notes, inv) in zip(xs, chords):
        if didx(notes[0]) < thr:      # 低音谱
            draw_chord(ax, x, notes, BASS_BOTTOM_Y, BASS_BOTTOM_NOTE)
        else:                          # 高音谱
            draw_chord(ax, x, notes, TREBLE_BOTTOM_Y, TREBLE_BOTTOM_NOTE)
            if notes[0] == ("C", 4):   # 最低音为中央C
                ctext(ax, x, 45.2, "中央C", 8.5, color=GRAY)
        ctext(ax, x, 26.8, chord["sym"][inv], 11.5, bold=True)
        ctext(ax, x, 24.3, INV7_NAMES[inv], 10.5)
        ctext(ax, x, 22.1, "·".join(disp.get(nt[0], nt[0]) for nt in notes), 9, color=GRAY)

    t = chord["tones"]
    ctext(ax, 47.5, 19.2,
          "%s = %s（%s=%s，%s=%s，%s=%s，%s=%s）｜ 低音 = %s → 原位；%s → 第一转位；%s → 第二转位；%s → 第三转位"
          % (chord["name"], " · ".join(t), TONE_ROLES7[0], t[0], TONE_ROLES7[1], t[1],
             TONE_ROLES7[2], t[2], TONE_ROLES7[3], t[3], t[0], t[1], t[2], t[3]),
          10, color=GRAY)

    os.makedirs(os.path.join(OUT_ROOT, spec["folder"]), exist_ok=True)
    out = os.path.join(OUT_ROOT, spec["folder"], "%s_chord_inversions.png" % chord["key"])
    fig.savefig(out, dpi=DPI, facecolor="white")
    plt.close(fig)
    return out, n

if __name__ == "__main__":
    want = sys.argv[1] if len(sys.argv) > 1 else None
    for k, spec in KEYS.items():
        if want and k != want:
            continue
        for chord in SEVENTHS[k]:
            out, n = make_chart(spec, chord)
            print("%-46s %2d 个和弦" % (out, n))
