# -*- coding: utf-8 -*-
"""
合并成册：指定大调的七和弦练习册 PDF（12 页，打印省纸版）
  第 1 页   封面（标题 + Imaj7 谱表装饰 + 目录）
  第 2–5 页 第一章 · 顺阶七和弦柱式总览（每页上下排布 2 个和弦）
  第 6–12 页 第二章 · 七和弦分解（琶音）练习

用法：python -X utf8 make7_practice_book.py <C|G|F>   # 不带参数则生成全部调
输出：Seventh/<Key of X>/<调名>七和弦练习册.pdf
（依赖 make7_chord_inversions.py / make7_arpeggios.py 生成的 PNG；只装订，不改 PNG；
  拼页/页码元件复用 make_practice_book.py）
"""
import os
import sys
import tempfile
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import img2pdf
from PIL import Image

from staff_lib import GRAY, LETTERS, draw_grand_staff, draw_chord, ctext
from make_chord_inversions import KEYS
from make7_chord_inversions import SEVENTHS, OUT_ROOT
from make_practice_book import page_image, pair_page_image

# ---------------- 封面 ----------------
def stack_octaves(tones, base_oct):
    """音名列表放到以 base_oct 为根音八度的密集排列（跨 C 界自动进位）。"""
    out, prev, octv = [], -1, base_oct
    for t in tones:
        i = LETTERS.index(t[0])
        if i < prev:
            octv += 1
        out.append((t[0], octv))
        prev = i
    return out

def make_cover(k, spec, path):
    chords = SEVENTHS[k]
    fig = plt.figure(figsize=(12.5, 13.16))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 95)
    ax.set_ylim(0, 100)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    ctext(ax, 47.5, 88, "%s七和弦练习册" % spec["key_name"], 34, bold=True)
    ctext(ax, 47.5, 82.5,
          "钢琴大谱表 · %d 个顺阶七和弦 × 12 把位（3 轮 × 原位+第一+第二+第三转位）· 音域 A1 – F6%s"
          % (len(chords), (" · " + spec["sig"]) if spec["sig"] else ""),
          12, color="#555555")

    # 谱表装饰带：Imaj7（低音谱 + 高音谱各一个柱式和弦，含调号）
    draw_grand_staff(ax, treble_bottom=66.0, bass_bottom=56.0,
                     key_sharps=spec.get("sharps", 0),
                     key_flats=spec.get("flats", 0))
    imaj7 = chords[0]["tones"]
    draw_chord(ax, 47.5, stack_octaves(imaj7, 2), 56.0, ("G", 2))
    draw_chord(ax, 47.5, stack_octaves(imaj7, 4), 66.0, ("E", 4))

    # 目录（两章并排）；页码按“柱式每页 2 个和弦”的分页计算
    n = len(chords)
    n_ch1 = (n + 1) // 2
    ch2_start = 2 + n_ch1
    total = 1 + n_ch1 + n
    ch1_x, ch2_x = 26.0, 69.0
    ctext(ax, ch1_x, 44, "第一章 · 七和弦柱式总览", 15, bold=True, ha="center")
    ctext(ax, ch1_x, 40.3, "第 2 – %d 页（每页 2 个和弦）" % (1 + n_ch1), 11, color=GRAY, ha="center")
    ctext(ax, ch2_x, 44, "第二章 · 七和弦分解（琶音）练习", 15, bold=True, ha="center")
    ctext(ax, ch2_x, 40.3, "第 %d – %d 页" % (ch2_start, total), 11, color=GRAY, ha="center")
    for i, ch in enumerate(chords):
        y = 36.2 - i * 3.6
        pos = "·上" if i % 2 == 0 and i + 1 < n else ("·下" if i % 2 == 1 else "")
        ctext(ax, ch1_x, y, "%s（%s · %s）…… 第 %d 页%s"
              % (ch["name"], ch["roman"], ch["quality"], 2 + i // 2, pos), 11.5, ha="center")
        ctext(ax, ch2_x, y, "%s（%s · %s）…… 第 %d 页"
              % (ch["name"], ch["roman"], ch["quality"], ch2_start + i), 11.5, ha="center")

    ctext(ax, 47.5, 4.5,
          "%s：%s ｜ 每个和弦 12 个把位 = 3 轮 ×（原位+第一+第二+第三转位）｜ 低音决定转位（七音 = 第三转位）｜ 第一章每页上下排布 2 个和弦"
          % (spec["key_name"], " · ".join(c["name"] for c in chords)),
          10.5, color=GRAY)

    fig.savefig(path, dpi=200, facecolor="white")
    plt.close(fig)

# ---------------- 组装 ----------------
def build(k, spec):
    folder = os.path.join(OUT_ROOT, spec["folder"])
    chords = [os.path.join(folder, "%s_chord_inversions.png" % c["key"])
              for c in SEVENTHS[k]]
    arps = [os.path.join(folder, "%s_arpeggios.png" % c["key"])
            for c in SEVENTHS[k]]
    for f in chords + arps:
        if not os.path.exists(f):
            raise SystemExit("缺少 %s，请先运行 make7_chord_inversions.py 和 make7_arpeggios.py" % f)

    n = len(chords)
    total = 1 + (n + 1) // 2 + len(arps)
    with tempfile.TemporaryDirectory() as tmp:
        pages = []
        cover = os.path.join(tmp, "page_01.png")
        make_cover(k, spec, cover)
        im = Image.open(cover).convert("RGB")   # 去掉 alpha，避免 PDF 多余 SMask
        im.save(cover)
        pages.append(cover)
        page_no = 2
        for i in range(0, n, 2):                # 第一章：每页上下 2 个和弦
            pair = chords[i:i + 2]
            pages.append(pair_page_image(pair[0], pair[1] if len(pair) > 1 else None,
                                         page_no, total, tmp))
            page_no += 1
        for src in arps:                        # 第二章：琶音整页
            pages.append(page_image(src, page_no, total, tmp))
            page_no += 1
        out_pdf = os.path.join(folder, "%s七和弦练习册.pdf"
                               % spec["key_name"].replace(" ", ""))
        with open(out_pdf, "wb") as f:
            f.write(img2pdf.convert(pages,
                     layout_fun=img2pdf.get_fixed_dpi_layout_fun((200, 200))))
    print("saved: %s（%d 页）" % (out_pdf, total))

if __name__ == "__main__":
    want = sys.argv[1] if len(sys.argv) > 1 else None
    for k, spec in KEYS.items():
        if want and k != want:
            continue
        build(k, spec)
