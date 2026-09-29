# -*- coding: utf-8 -*-
"""
生成 PNG 系列：指定大调的常用三和弦柱式总览图（钢琴大谱表，低音谱 + 高音谱）。
每个和弦从 A1（低音谱下方第 3 线）音域内的最低排列起，完整 4 轮循环 = 12 个
（原位 / 第一转位 / 第二转位各 4 个），自左向右、由低到高；最高音按需延伸。

用法：python -X utf8 make_chord_inversions.py <C|G|F>   # 不带参数则生成全部调
输出：Traid/<Key of X>/<key>_chord_inversions.png ×7
（绘图元件见 staff_lib.py；七和弦版见 make7_*.py）
"""
import os
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from staff_lib import (GRAY, didx, draw_grand_staff, draw_chord, ctext)

OUT_ROOT = "Traid"                    # 三和弦成品根目录

DPI = 200
X_MIN, X_MAX = 0.0, 95.0
Y_MIN, Y_MAX = 18.0, 66.0

TREBLE_BOTTOM_Y = 48.0              # 高音谱底线（线间距 = 1）
BASS_BOTTOM_Y = 34.0                # 低音谱底线
TREBLE_BOTTOM_NOTE = ("E", 4)
BASS_BOTTOM_NOTE = ("G", 2)
X_FIRST, X_LAST = 13.0, 88.5

# 音域与谱表分配阈值
LO = ("A", 1)                        # 最低音：低音谱下方第 3 线（A1）
HI = ("F", 6)                        # 枚举上限：取前 N_CHORDS 个
N_CHORDS = 12                        # 每个和弦固定 4 轮完整循环
TREBLE_FROM = ("B", 3)               # 最低音 >= B3 的和弦放高音谱，否则低音谱

INV_NAMES = ["原位", "第一转位", "第二转位"]
TONE_ROLES = ["根音", "三音", "五音"]

# ---------------- 调性数据 ----------------
KEYS = {
    "C": dict(
        key_name="C 大调", folder="Key of C", sharps=0, flats=0, sig="", disp={},
        book="C大调和弦练习册.pdf",
        motif=dict(bass=[("C", 2), ("E", 2), ("G", 2)],
                   treble=[("C", 4), ("E", 4), ("G", 4)]),
        chords=[
            dict(key="c",    name="C",    roman="I 级",   quality="大三和弦", tones=["C", "E", "G"],
                 sym=["C", "C/E", "C/G"]),
            dict(key="dm",   name="Dm",   roman="ii 级",  quality="小三和弦", tones=["D", "F", "A"],
                 sym=["Dm", "Dm/F", "Dm/A"]),
            dict(key="em",   name="Em",   roman="iii 级", quality="小三和弦", tones=["E", "G", "B"],
                 sym=["Em", "Em/G", "Em/B"]),
            dict(key="f",    name="F",    roman="IV 级",  quality="大三和弦", tones=["F", "A", "C"],
                 sym=["F", "F/A", "F/C"]),
            dict(key="g",    name="G",    roman="V 级",   quality="大三和弦", tones=["G", "B", "D"],
                 sym=["G", "G/B", "G/D"]),
            dict(key="am",   name="Am",   roman="vi 级",  quality="小三和弦", tones=["A", "C", "E"],
                 sym=["Am", "Am/C", "Am/E"]),
            dict(key="bdim", name="Bdim", roman="vii° 级", quality="减三和弦", tones=["B", "D", "F"],
                 sym=["Bdim", "Bdim/D", "Bdim/F"]),
        ],
    ),
    "G": dict(
        key_name="G 大调", folder="Key of G", sharps=1, flats=0,
        sig="调号：1 个升号（F♯）", disp={"F": "F♯"},
        book="G大调和弦练习册.pdf",
        motif=dict(bass=[("G", 2), ("B", 2), ("D", 3)],
                   treble=[("G", 4), ("B", 4), ("D", 5)]),
        chords=[
            dict(key="g",      name="G",     roman="I 级",   quality="大三和弦", tones=["G", "B", "D"],
                 sym=["G", "G/B", "G/D"]),
            dict(key="am",     name="Am",    roman="ii 级",  quality="小三和弦", tones=["A", "C", "E"],
                 sym=["Am", "Am/C", "Am/E"]),
            dict(key="bm",     name="Bm",    roman="iii 级", quality="小三和弦", tones=["B", "D", "F♯"],
                 sym=["Bm", "Bm/D", "Bm/F♯"]),
            dict(key="c",      name="C",     roman="IV 级",  quality="大三和弦", tones=["C", "E", "G"],
                 sym=["C", "C/E", "C/G"]),
            dict(key="d",      name="D",     roman="V 级",   quality="大三和弦", tones=["D", "F♯", "A"],
                 sym=["D", "D/F♯", "D/A"]),
            dict(key="em",     name="Em",    roman="vi 级",  quality="小三和弦", tones=["E", "G", "B"],
                 sym=["Em", "Em/G", "Em/B"]),
            dict(key="fsharp", name="F♯dim", roman="vii° 级", quality="减三和弦", tones=["F♯", "A", "C"],
                 sym=["F♯dim", "F♯dim/A", "F♯dim/C"]),
        ],
    ),
    "F": dict(
        key_name="F 大调", folder="Key of F", sharps=0, flats=1,
        sig="调号：1 个降号（B♭）", disp={"B": "B♭"},
        book="F大调和弦练习册.pdf",
        motif=dict(bass=[("F", 2), ("A", 2), ("C", 3)],
                   treble=[("F", 4), ("A", 4), ("C", 5)]),
        chords=[
            dict(key="f",    name="F",    roman="I 级",   quality="大三和弦", tones=["F", "A", "C"],
                 sym=["F", "F/A", "F/C"]),
            dict(key="gm",   name="Gm",   roman="ii 级",  quality="小三和弦", tones=["G", "B♭", "D"],
                 sym=["Gm", "Gm/B♭", "Gm/D"]),
            dict(key="am",   name="Am",   roman="iii 级", quality="小三和弦", tones=["A", "C", "E"],
                 sym=["Am", "Am/C", "Am/E"]),
            dict(key="bb",   name="B♭",   roman="IV 级",  quality="大三和弦", tones=["B♭", "D", "F"],
                 sym=["B♭", "B♭/D", "B♭/F"]),
            dict(key="c",    name="C",    roman="V 级",   quality="大三和弦", tones=["C", "E", "G"],
                 sym=["C", "C/E", "C/G"]),
            dict(key="dm",   name="Dm",   roman="vi 级",  quality="小三和弦", tones=["D", "F", "A"],
                 sym=["Dm", "Dm/F", "Dm/A"]),
            dict(key="edim", name="Edim", roman="vii° 级", quality="减三和弦", tones=["E", "G", "B♭"],
                 sym=["Edim", "Edim/G", "Edim/B♭"]),
        ],
    ),
}

def build_triads(tones):
    """音域 LO..HI 内该和弦全部密集三和弦，按最低音升序取前 N_CHORDS 个。
    音名可带 ♯（如 F♯），按其本位音字母定位。返回 [(notes, inv), ...]"""
    from staff_lib import idx_note, LETTERS
    ti = [LETTERS.index(t[0]) for t in tones]
    lo, hi = didx(LO), didx(HI)
    out = []
    for start in range(3):
        g1 = (ti[(start + 1) % 3] - ti[start]) % 7
        g2 = (ti[(start + 2) % 3] - ti[(start + 1) % 3]) % 7
        for octv in range(1, 7):
            base = octv * 7 + ti[start]
            idxs = [base, base + g1, base + g1 + g2]
            if idxs[0] >= lo and idxs[-1] <= hi:
                out.append(([idx_note(i) for i in idxs], start))
    out.sort(key=lambda c: didx(c[0][0]))
    return out[:N_CHORDS]

# ---------------- 生成 ----------------
def make_chart(spec, chord):
    triads = build_triads(chord["tones"])
    n = len(triads)
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
    first, last = triads[0][0][0], triads[-1][0][-1]
    lo_note = "%s%d" % (disp.get(first[0], first[0]), first[1])
    hi_note = "%s%d" % (disp.get(last[0], last[0]), last[1])
    ctext(ax, 47.5, 59.6,
          "低音谱 + 高音谱上下合并 ｜ 自 A1（低音谱下方第 3 线）音域内最低排列起，完整 4 轮 ×（原位+第一转位+第二转位）= %d 个 ｜ 实际跨度 %s – %s%s"
          % (n, lo_note, hi_note,
             (" ｜ " + spec["sig"]) if spec["sig"] else ""),
          10.5, color="#555555")

    draw_grand_staff(ax, TREBLE_BOTTOM_Y, BASS_BOTTOM_Y, final_barline=True,
                     key_sharps=spec.get("sharps", 0), key_flats=spec.get("flats", 0))

    thr = didx(TREBLE_FROM)
    for x, (notes, inv) in zip(xs, triads):
        if didx(notes[0]) < thr:      # 低音谱
            draw_chord(ax, x, notes, BASS_BOTTOM_Y, BASS_BOTTOM_NOTE)
        else:                          # 高音谱
            draw_chord(ax, x, notes, TREBLE_BOTTOM_Y, TREBLE_BOTTOM_NOTE)
            if notes[0] == ("C", 4):   # 最低音为中央C
                ctext(ax, x, 45.2, "中央C", 8.5, color=GRAY)
        ctext(ax, x, 26.8, chord["sym"][inv], 12, bold=True)
        ctext(ax, x, 24.3, INV_NAMES[inv], 10.5)
        ctext(ax, x, 22.1, "·".join(disp.get(nt[0], nt[0]) for nt in notes), 9, color=GRAY)

    t = chord["tones"]
    ctext(ax, 47.5, 19.2,
          "%s = %s（%s=%s，%s=%s，%s=%s）｜ 低音 = %s → 原位；%s → 第一转位；%s → 第二转位"
          % (chord["name"], " · ".join(t), TONE_ROLES[0], t[0], TONE_ROLES[1], t[1],
             TONE_ROLES[2], t[2], t[0], t[1], t[2]), 10, color=GRAY)

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
        for chord in spec["chords"]:
            out, n = make_chart(spec, chord)
            print("%-38s %2d 个和弦" % (out, n))
