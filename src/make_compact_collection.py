# -*- coding: utf-8 -*-
"""
紧凑打印版合集：柱式 4 合 1 页（紧凑重绘条带，谱表原尺寸）+ 琶音 1 页 3 和弦
（每和弦单行大谱表 x 12 列）。和弦名称统一在两谱表中缝（bass+8.25），
带八度音名统一在低音谱下方（bass-4.45）。

当前为样张模式：
  python -X utf8 src/make_compact_collection.py sample
确认版式后补全 full 模式，生成完整合集 PDF（预计 29 页）。
"""
import os
import sys
import tempfile
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont

from staff_lib import (GRAY, didx, pitch_y, draw_grand_staff, draw_chord,
                       draw_note, ctext)
from make_chord_inversions import (KEYS, build_triads, TREBLE_FROM,
                                   TREBLE_BOTTOM_NOTE, BASS_BOTTOM_NOTE,
                                   X_FIRST, X_LAST)
from make7_chord_inversions import SEVENTHS, build_sevenths

PAGE_W, PAGE_H = 2500, 2632
CJK_TTF = "C:/Windows/Fonts/msyh.ttc"

# ---------------- 紧凑柱式谱面（2500 x ~649，谱表原尺寸，4 合 1 页） ----------------
# 条带预算（CH_SPAN=24.65）：顶部余量 0.3 + 谱上墨迹 8.05（F6 头顶）+ 谱表 4 + 中缝 11
# + 谱表 4 + 下方墨迹 3.55（A1）+ 标签行至 -4.93。中缝名称带/音名标签与琶音页完全同位。
CH_SPAN = 24.65
CH_BASS = 5.3
CH_TREBLE = CH_BASS + 11.0
CH_SYM_DY = 8.25
CH_LBL_DY = -4.45

def compact_chart(spec, chord, build_fn):
    """单条带：标题（谱表上方）+ 大谱表 + 中缝和弦名称 + 下方一行带八度音名。
    与琶音页同名元素同位（bass+8.25 / bass-4.45），版式全书统一。"""
    chords = build_fn(chord["tones"])
    n = len(chords)
    xs = [X_FIRST + i * (X_LAST - X_FIRST) / (n - 1) for i in range(n)]
    disp = spec["disp"]

    fig = plt.figure(figsize=(12.5, CH_SPAN / 7.5994))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 95)
    ax.set_ylim(0, CH_SPAN)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    first, last = chords[0][0][0], chords[-1][0][-1]
    lo = "%s%d" % (disp.get(first[0], first[0]), first[1])
    hi = "%s%d" % (disp.get(last[0], last[0]), last[1])
    ctext(ax, 47.5, CH_TREBLE + 6.2,
          "%s 和弦与全部转位（%s %s，%s）· 跨度 %s – %s"
          % (chord["name"], spec["key_name"], chord["roman"], chord["quality"],
             lo, hi),
          11, bold=True)

    draw_grand_staff(ax, CH_TREBLE, CH_BASS, final_barline=True,
                     key_sharps=spec.get("sharps", 0),
                     key_flats=spec.get("flats", 0))

    thr = didx(TREBLE_FROM)
    for x, (notes, inv) in zip(xs, chords):
        if didx(notes[0]) < thr:
            draw_chord(ax, x, notes, CH_BASS, BASS_BOTTOM_NOTE)
        else:
            draw_chord(ax, x, notes, CH_TREBLE, TREBLE_BOTTOM_NOTE)
        ctext(ax, x, CH_BASS + CH_SYM_DY, chord["sym"][inv], 10, bold=True)
        ctext(ax, x, CH_BASS + CH_LBL_DY,
              " ".join(disp.get(t[0], t[0]) + str(t[1]) for t in notes),
              8, color=GRAY)

    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "c.png")
        fig.savefig(p, dpi=200, facecolor="white")
        plt.close(fig)
        return Image.open(p).convert("RGB")

# ---------------- 页面拼装 ----------------
def stack_n(imgs, out=None):
    """同宽图纵向堆满一页，上下/间隙均分；返回画布。"""
    canvas = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    slack = PAGE_H - sum(im.size[1] for im in imgs)
    gap = max(slack // (len(imgs) + 1), 0)
    y = gap // 2
    for im in imgs:
        canvas.paste(im, (0, y))
        y += im.size[1] + gap
    if out:
        canvas.save(out)
        print("saved:", out)
    return canvas

# ---------------- 紧凑琶音页（原尺寸重绘：1 页 3 和弦，每和弦单行大谱表 x 12 列） ----------------
# 垂直预算（0-100，每块 ~33）：谱表上墨迹至 treble+8.05（F6 符头顶）→ 谱表 4 + 中缝 11 +
# 谱表 4 → 下方墨迹至 bass-3.55（A1）→ 标签行 bass-4.45。名称带在两谱表中间 bass+8.25：
# 下清低音组最高音（G4，头顶 bass+7.55），上清高音组最低音（B3，头底 bass+8.95）。
# 12 列 = 左半低音组（0-5）、右半高音组（6-11）；标题放谱表上方左侧（左半无谱上墨迹）。
BLK_TR = [87.7, 54.8, 21.9]          # 3 块高音谱底线（块 0 顶墨迹 F6 头 99.75 < 100）
AR_TITLE_DY = 6.2                    # 标题中心相对本块 treble 底线
AR_G = 11.0                          # 高/低音谱表间距（容纳中间的和弦名称带）
AR_COLS = 12                         # 每和弦 12 把位排一行 12 列
AR_NOTE_DX = 1.6                     # 组内相邻音符间距（4 音组占 4.8 < 列宽 6.29）
AR_SYM_DY = 8.25                     # 和弦名称带位置（相对 bass 底线）
AR_LBL_DY = -4.45                    # 音名标签行位置（相对 bass 底线）

def compact_arps_page(blocks):
    """一页最多 3 个和弦的琶音练习：blocks = [(spec, chord, build_fn), ...]，
    每和弦一块独立大谱表（12 把位单行 12 列），谱表原尺寸，调号随块。
    和弦名称放两行谱表中间；带八度的音名一行放低音谱下方（斜杠和弦名已含转位）。"""
    fig = plt.figure(figsize=(12.5, 13.16))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 95)
    ax.set_ylim(0, 100)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    slot_w = (X_LAST - X_FIRST) / AR_COLS
    thr = didx(TREBLE_FROM)

    for bi, (spec, chord, build_fn) in enumerate(blocks):
        treble_bottom = BLK_TR[bi]
        bass_bottom = treble_bottom - AR_G
        disp = spec["disp"]
        chords = build_fn(chord["tones"])
        first, last = chords[0][0][0], chords[-1][0][-1]
        lo = "%s%d" % (disp.get(first[0], first[0]), first[1])
        hi = "%s%d" % (disp.get(last[0], last[0]), last[1])
        ctext(ax, 4.0, treble_bottom + AR_TITLE_DY,
              "%s 和弦分解（琶音）· %s %s %s · 每组 %d 音 · %s – %s"
              % (chord["name"], spec["key_name"], chord["roman"],
                 chord["quality"], len(chord["tones"]), lo, hi),
              11, bold=True, ha="left")

        draw_grand_staff(ax, treble_bottom, bass_bottom,
                         final_barline=(bi == len(blocks) - 1),
                         key_sharps=spec.get("sharps", 0),
                         key_flats=spec.get("flats", 0))
        for i in range(AR_COLS - 1):
            ax.vlines(X_FIRST + slot_w * (i + 0.5),
                      bass_bottom, treble_bottom + 4.0,
                      color="#dddddd", lw=0.9, linestyles=(0, (4, 3)), zorder=1)

        for i, (notes, inv) in enumerate(chords):
            x0 = X_FIRST + slot_w * i + 0.7
            center = x0 + AR_NOTE_DX * (len(notes) - 1) / 2.0
            if didx(notes[0]) < thr:
                bottom_y, bottom_note = bass_bottom, BASS_BOTTOM_NOTE
            else:
                bottom_y, bottom_note = treble_bottom, TREBLE_BOTTOM_NOTE
            for j, nt in enumerate(notes):
                draw_note(ax, x0 + AR_NOTE_DX * j,
                          pitch_y(nt, bottom_note, bottom_y), bottom_y)
            # 和弦名称放两行谱表中间；带八度音名一行放低音谱下方
            ctext(ax, center, bass_bottom + AR_SYM_DY, chord["sym"][inv],
                  10, bold=True)
            ctext(ax, center, bass_bottom + AR_LBL_DY,
                  " ".join(disp.get(t[0], t[0]) + str(t[1]) for t in notes),
                  8, color=GRAY)

    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "a.png")
        fig.savefig(p, dpi=200, facecolor="white")
        plt.close(fig)
        return Image.open(p).convert("RGB")

# ---------------- 样张 ----------------
def sample():
    spec = KEYS["C"]
    charts = [compact_chart(spec, c, build_triads)
              for c in spec["chords"][:4]]            # C / Dm / Em / F
    stack_n(charts, "样张_紧凑柱式4合1.png")

    compact_arps_page([(spec, c, build_triads)
                       for c in spec["chords"][:3]]).save("样张_紧凑琶音重绘.png")
    print("saved: 样张_紧凑琶音重绘.png")

# ---------------- 完整合集 ----------------
def _all_items():
    """全书 42 和弦统一顺序：三和弦 C/G/F → 七和弦 C/G/F。"""
    items = [(spec, c, build_triads) for spec in KEYS.values()
             for c in spec["chords"]]
    for k, chords7 in SEVENTHS.items():
        items += [(KEYS[k], c, build_sevenths) for c in chords7]
    return items

def _key_sections():
    """[(调名, 类型, 和弦名列表, 全书起始索引)]，起始索引按 _all_items 顺序。"""
    secs, idx = [], 0
    for spec in KEYS.values():
        secs.append((spec["key_name"], "三和弦",
                     [c["name"] for c in spec["chords"]], idx))
        idx += 7
    for k, chords7 in SEVENTHS.items():
        secs.append((KEYS[k]["key_name"], "七和弦",
                     [c["name"] for c in chords7], idx))
        idx += 7
    return secs

def _range_txt(first, last):
    return ("第 %d 页" % first) if first == last else ("第 %d – %d 页" % (first, last))

def toc_page(total, n_chart_pages):
    """目录页（PIL 绘制）：两部分 + 六个调的页码范围。"""
    canvas = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    d = ImageDraw.Draw(canvas)
    bold = lambda s: ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", s)
    reg = lambda s: ImageFont.truetype(CJK_TTF, s)
    MX = 190
    gray, ink = (110, 110, 110), (20, 20, 20)

    y = 250
    d.text((MX, y), "和弦练习册合集 · 紧凑打印版", font=bold(104), fill=ink)
    y += 190
    d.text((MX, y), "三和弦与七和弦 · C / G / F 大调 · 柱式 + 琶音 · 每和弦 12 把位",
           font=reg(48), fill=gray)
    y += 210

    parts = [
        ("第一部分 · 柱式和弦与全部转位",
         2, 1 + n_chart_pages, lambda i: 2 + i // 4),
        ("第二部分 · 和弦分解（琶音）练习",
         2 + n_chart_pages, total, lambda i: 2 + n_chart_pages + i // 3),
    ]
    for title, p_first, p_last, page_of in parts:
        d.text((MX, y), title, font=bold(62), fill=ink)
        rng = _range_txt(p_first, p_last)
        d.text((PAGE_W - MX - d.textlength(rng, font=bold(62)), y),
               rng, font=bold(62), fill=gray)
        y += 130
        d.line([(MX, y), (PAGE_W - MX, y)], fill=(210, 210, 210), width=3)
        y += 60
        for key, typ, names, start in _key_sections():
            p0, p1 = page_of(start), page_of(start + len(names) - 1)
            d.text((MX + 30, y), "%s · %s" % (key, typ), font=reg(52), fill=ink)
            d.text((MX + 660, y), "  ".join(names), font=reg(44), fill=gray)
            rng = _range_txt(p0, p1)
            d.text((PAGE_W - MX - d.textlength(rng, font=reg(46)), y + 4),
                   rng, font=reg(46), fill=ink)
            y += 120
        y += 90

    d.text((MX, PAGE_H - 180),
           "版式说明：和弦名称统一在两谱表中缝；音名（含八度）在低音谱下方。原 72 页压缩为 %d 页。"
           % total, font=reg(40), fill=gray)
    return canvas

def full():
    from make_practice_book import _stamp
    items = _all_items()
    chunks4 = [items[i:i + 4] for i in range(0, len(items), 4)]
    chunks3 = [items[i:i + 3] for i in range(0, len(items), 3)]
    total = 1 + len(chunks4) + len(chunks3)
    build_dir = "build_紧凑版"
    os.makedirs(build_dir, exist_ok=True)
    paths = []

    def emit(im, page_no):
        _stamp(im, page_no, total)
        p = os.path.join(build_dir, "p%02d.png" % page_no)
        im.save(p)
        paths.append(p)
        print("page %d / %d" % (page_no, total))

    emit(toc_page(total, len(chunks4)), 1)
    for gi, grp in enumerate(chunks4):
        print("柱式 %d-%d / %d" % (gi * 4 + 1, gi * 4 + len(grp), len(items)))
        emit(stack_n([compact_chart(spec, c, bf) for spec, c, bf in grp]), 2 + gi)
    for gi, grp in enumerate(chunks3):
        print("琶音 %d-%d / %d" % (gi * 3 + 1, gi * 3 + len(grp), len(items)))
        emit(compact_arps_page(grp), 2 + len(chunks4) + gi)

    import img2pdf
    out = "和弦练习册合集.pdf"
    with open(out, "wb") as f:
        f.write(img2pdf.convert(paths,
                                layout_fun=img2pdf.get_fixed_dpi_layout_fun((200, 200))))
    print("saved: %s（%d 页）" % (out, total))

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "sample"
    if mode == "sample":
        sample()
    elif mode == "full":
        full()
    else:
        raise SystemExit("用法: %s [sample|full]" % sys.argv[0])
