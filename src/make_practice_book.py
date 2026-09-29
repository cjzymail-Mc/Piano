# -*- coding: utf-8 -*-
"""
合并成册：指定大调的和弦练习册 PDF（12 页，打印省纸版）
  第 1 页   封面（标题 + 谱表装饰 + 目录）
  第 2–5 页 第一章 · 柱式和弦总览（每页上下排布 2 个和弦，谱面原尺寸不缩放）
  第 6–12 页 第二章 · 分解和弦（琶音）练习

用法：python -X utf8 make_practice_book.py <C|G|F>   # 不带参数则生成全部调
输出：Traid/<Key of X>/<调名>和弦练习册.pdf
（依赖 make_chord_inversions.py / make_arpeggios.py 生成的 PNG；只装订，不改 PNG）
"""
import os
import sys
import tempfile
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import img2pdf
from PIL import Image, ImageDraw, ImageFont

from staff_lib import GRAY, draw_grand_staff, draw_chord, ctext
from make_chord_inversions import KEYS, OUT_ROOT

PAGE_W, PAGE_H = 2500, 2632          # 所有页统一尺寸（12.5 x 13.16 in @ 200dpi）
CJK_TTF = "C:/Windows/Fonts/msyh.ttc"

# ---------------- 封面 ----------------
def make_cover(spec, path):
    fig = plt.figure(figsize=(12.5, 13.16))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 95)
    ax.set_ylim(0, 100)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    ctext(ax, 47.5, 88, "%s和弦练习册" % spec["key_name"], 34, bold=True)
    ctext(ax, 47.5, 82.5,
          "钢琴大谱表 · %d 个常用和弦 × 12 把位（原位 + 第一转位 + 第二转位 ×4）· 音域 A1 – F6%s"
          % (len(spec["chords"]),
             (" · " + spec["sig"]) if spec["sig"] else ""),
          12, color="#555555")

    # 谱表装饰带：主和弦（低音谱 + 高音谱各一个柱式和弦，含调号）
    draw_grand_staff(ax, treble_bottom=66.0, bass_bottom=56.0,
                     key_sharps=spec.get("sharps", 0),
                     key_flats=spec.get("flats", 0))
    draw_chord(ax, 47.5, spec["motif"]["bass"], 56.0, ("G", 2))
    draw_chord(ax, 47.5, spec["motif"]["treble"], 66.0, ("E", 4))

    # 目录（两章并排）；页码按“柱式每页 2 个和弦”的分页计算
    n = len(spec["chords"])
    n_ch1 = (n + 1) // 2                     # 第一章页数（7 个和弦 -> 4 页）
    ch2_start = 2 + n_ch1
    total = 1 + n_ch1 + n
    ch1_x, ch2_x = 26.0, 69.0
    ctext(ax, ch1_x, 44, "第一章 · 柱式和弦总览", 15, bold=True, ha="center")
    ctext(ax, ch1_x, 40.3, "第 2 – %d 页（每页 2 个和弦）" % (1 + n_ch1), 11, color=GRAY, ha="center")
    ctext(ax, ch2_x, 44, "第二章 · 分解和弦（琶音）练习", 15, bold=True, ha="center")
    ctext(ax, ch2_x, 40.3, "第 %d – %d 页" % (ch2_start, total), 11, color=GRAY, ha="center")
    for i, ch in enumerate(spec["chords"]):
        y = 36.2 - i * 3.6
        pos = "·上" if i % 2 == 0 and i + 1 < n else ("·下" if i % 2 == 1 else "")
        ctext(ax, ch1_x, y, "%s（%s · %s）…… 第 %d 页%s"
              % (ch["name"], ch["roman"], ch["quality"], 2 + i // 2, pos), 11.5, ha="center")
        ctext(ax, ch2_x, y, "%s（%s · %s）…… 第 %d 页"
              % (ch["name"], ch["roman"], ch["quality"], ch2_start + i), 11.5, ha="center")

    ctext(ax, 47.5, 4.5,
          "%s：%s ｜ 每个和弦 12 个把位 = 4 轮完整转位循环 ｜ 低音决定转位 ｜ 第一章每页上下排布 2 个和弦"
          % (spec["key_name"], " · ".join(c["name"] for c in spec["chords"])),
          10.5, color=GRAY)

    fig.savefig(path, dpi=200, facecolor="white")
    plt.close(fig)

# ---------------- 内容页：统一尺寸 + 页码 ----------------
def _stamp(im, page_no, total):
    """右下角页码"""
    d = ImageDraw.Draw(im)
    font = ImageFont.truetype(CJK_TTF, 34)
    txt = "%d / %d" % (page_no, total)
    tb = d.textbbox((0, 0), txt, font=font)
    d.text((PAGE_W - 36 - (tb[2] - tb[0]), PAGE_H - 26 - (tb[3] - tb[1])),
           txt, font=font, fill=(170, 170, 170))

def page_image(src, page_no, total, tmpdir):
    im = Image.open(src).convert("RGB")
    if im.size != (PAGE_W, PAGE_H):
        canvas = Image.new("RGB", (PAGE_W, PAGE_H), "white")
        canvas.paste(im, (0, (PAGE_H - im.size[1]) // 2))
        im = canvas
    _stamp(im, page_no, total)
    out = os.path.join(tmpdir, "page_%02d.png" % page_no)
    im.save(out)
    return out

def pair_page_image(src_top, src_bottom, page_no, total, tmpdir):
    """第一章页：两张柱式谱面（2500x1264）原尺寸上下拼入一页。
    布局：上边距 40 + 图1 + 间隙 24 + 图2 + 下边距 40 = 2632px。"""
    canvas = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    a = Image.open(src_top).convert("RGB")
    assert a.size == (PAGE_W, 1264), a.size
    canvas.paste(a, (0, 40))
    if src_bottom:
        b = Image.open(src_bottom).convert("RGB")
        assert b.size == (PAGE_W, 1264), b.size
        canvas.paste(b, (0, PAGE_H - 40 - b.size[1]))   # 顶部对齐成对版式
    _stamp(canvas, page_no, total)
    out = os.path.join(tmpdir, "page_%02d.png" % page_no)
    canvas.save(out)
    return out

# ---------------- 组装 ----------------
def build(spec):
    folder = os.path.join(OUT_ROOT, spec["folder"])
    chords = [os.path.join(folder, "%s_chord_inversions.png" % c["key"])
              for c in spec["chords"]]
    arps = [os.path.join(folder, "%s_arpeggios.png" % c["key"])
            for c in spec["chords"]]
    for f in chords + arps:
        if not os.path.exists(f):
            raise SystemExit("缺少 %s，请先运行 make_chord_inversions.py 和 make_arpeggios.py" % f)

    n = len(chords)
    total = 1 + (n + 1) // 2 + len(arps)
    with tempfile.TemporaryDirectory() as tmp:
        pages = []
        cover = os.path.join(tmp, "page_01.png")
        make_cover(spec, cover)
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
        out_pdf = os.path.join(folder, spec["book"])
        with open(out_pdf, "wb") as f:
            f.write(img2pdf.convert(pages,
                     layout_fun=img2pdf.get_fixed_dpi_layout_fun((200, 200))))
    print("saved: %s（%d 页）" % (out_pdf, total))

if __name__ == "__main__":
    want = sys.argv[1] if len(sys.argv) > 1 else None
    for k, spec in KEYS.items():
        if want and k != want:
            continue
        build(spec)
