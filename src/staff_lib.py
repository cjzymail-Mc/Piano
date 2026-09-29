# -*- coding: utf-8 -*-
"""
共享五线谱绘图库。
单位约定：1 数据单位 = 1 个谱线间距（各图均为 xlim 95 ↔ 12.5in，即 1 单位 ≈ 9.47pt）。
符头与谱号使用 Segoe UI Symbol 音乐字形，尺寸/摆位按 200pt 字形探测校准：
  - 黑符头 U+1D157：bbox 高 0.627in、宽 0.647in、中心低于锚点 0.430in（@200pt）
  - 谱内 1 线距 = 0.604in @200pt（由低音谱号双点间距标定）
"""
import numpy as np
import matplotlib.patches as mpatches
from matplotlib.path import Path
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
from matplotlib.transforms import Affine2D

MUSIC_FONT = "Segoe UI Symbol"
CJK_FONT = "Microsoft YaHei"
INK = "#111111"
GRAY = "#888888"
LINE_LW, LEDGER_LW, STEM_LW = 1.05, 1.2, 2.0

PT_PER_UNIT = 9.474                  # 1 数据单位 = 9.474pt（各图均为 xlim 95 ↔ 12.5in）
CLEF_TREBLE = dict(dy=1.13, size=64)               # 螺旋对准 G 线
CLEF_BASS = dict(dy=2.11, size=44)                 # 双点夹住 F 线

# 升号 ♯（U+266F）：@200pt 高 3.22 线距、宽 1.78、墨迹中心高于锚点 0.447 线距。
# 取 32.5pt（高约 2.4 线距的调号比例）；锚点 = 目标线 y - dy。
SHARP = dict(size=32.5, dy=0.333, x=9.2)
# 降号 ♭（U+266D）：@200pt 高 3.22 线距、宽 1.34；对齐基准是碗肚中心
# （宽墨迹区中心），位于锚点下方 0.233 线距 -> @32.5pt 为 -0.174。锚点 = 目标线 y - dy。
FLAT = dict(size=32.5, dy=-0.174, x=9.2)

LETTERS = "CDEFGAB"

def didx(note):
    letter, octave = note
    return octave * 7 + LETTERS.index(letter)

def idx_note(i):
    return (LETTERS[i % 7], i // 7)

def pitch_y(note, bottom_note, bottom_y):
    return bottom_y + (didx(note) - didx(bottom_note)) * 0.5

# ---------------- 基础元件 ----------------
def ctext(ax, x, y, s, size, color=INK, bold=False, ha="center"):
    # 字体回退列表：中文取 YaHei，♯ 等音乐符号取 Segoe UI Symbol
    ax.text(x, y, s, fontsize=size, color=color, ha=ha, va="center",
            fontfamily=[CJK_FONT, MUSIC_FONT],
            fontweight="bold" if bold else "normal", zorder=5)

def draw_staff(ax, bottom_y, x0=3.2, x1=92.6):
    for i in range(5):
        ax.hlines(bottom_y + i, x0, x1, color=INK, lw=LINE_LW, zorder=2)

def draw_ledgers(ax, x, y, bottom_y):
    """谱表外加线。上方：整线画到音符所在线；下方：只画到音符上方那条线为止。"""
    top_y = bottom_y + 4
    if y > top_y:
        ys = range(int(top_y) + 1, int(y) + 1)
    elif y < bottom_y:
        start = int(y) if float(y).is_integer() else int(y) + 1
        ys = range(start, int(bottom_y))
    else:
        ys = []
    for yy in ys:
        ax.hlines(yy, x - 0.9, x + 0.9, color=INK, lw=LEDGER_LW, zorder=3)

def _build_solid_notehead():
    """实心符头：Segoe U+1D157 直接渲染为空心环，故取其外轮廓矢量路径纯填充。
    路径单位为 pt（size=42），实测外形 1.02 x 1.00 个谱线间距。"""
    tp = TextPath((0, 0), "\U0001D157", size=42,
                  prop=FontProperties(family=MUSIC_FONT))
    verts, codes = tp.vertices, tp.codes
    segs, start = [], None
    for i, c in enumerate(codes):
        if c == Path.MOVETO:
            if start is not None:
                segs.append((start, i))
            start = i
    segs.append((start, len(codes)))

    def seg_area(se):
        v = verts[se[0]:se[1]]
        return np.ptp(v[:, 0]) * np.ptp(v[:, 1])

    s, e = max(segs, key=seg_area)
    path = Path(verts[s:e], codes[s:e])
    ext = path.get_extents()
    return path, (ext.x0 + ext.width / 2, ext.y0 + ext.height / 2)

_NOTE_PATH, _NOTE_CENTER = _build_solid_notehead()

def draw_notehead(ax, x, y):
    """实心黑色符头，中心对准 (x, y)"""
    tr = (Affine2D()
          .translate(-_NOTE_CENTER[0], -_NOTE_CENTER[1])
          .scale(1.0 / PT_PER_UNIT)
          .translate(x, y)) + ax.transData
    ax.add_patch(mpatches.PathPatch(_NOTE_PATH, transform=tr,
                                    facecolor=INK, edgecolor="none", lw=0, zorder=4))

def draw_stem(ax, x, y, up, length=3.4):
    """单个符干；符头稍后绘制盖住接缝"""
    if up:
        ax.vlines(x + 0.42, y, y + length, color=INK, lw=STEM_LW, zorder=3)
    else:
        ax.vlines(x - 0.42, y - length, y, color=INK, lw=STEM_LW, zorder=3)

def draw_note(ax, x, y, bottom_y):
    """单音符（四分音符）：符干方向按中线规则（中线及以下朝上，以上朝下）"""
    draw_ledgers(ax, x, y, bottom_y)
    draw_stem(ax, x, y, up=(y < bottom_y + 2.0))
    draw_notehead(ax, x, y)

NOTE_SHIFT = 1.08     # 二度音横向错位量（约一个符头宽）

def draw_chord(ax, x, notes, bottom_y, bottom_note):
    """柱式和弦：符头纵向叠置，整组共用一根符干（离中线最远的音符决定方向）。
    相邻音为二度（<1 线距）时，较高音向符干一侧横向错开，符干从两符头间穿过。
    （三和弦全是三度叠置，不触发错位，输出与旧版一致）"""
    pairs = sorted(((pitch_y(n, bottom_note, bottom_y), n) for n in notes),
                   key=lambda p: p[0])
    ys = [p[0] for p in pairs]
    shift = [False] * len(ys)
    for i in range(1, len(ys)):
        if ys[i] - ys[i - 1] < 0.99:      # 二度：较高音错位
            shift[i] = True
    y_mid = bottom_y + 2.0
    up = (y_mid - ys[0]) >= (ys[-1] - y_mid)
    dx = NOTE_SHIFT if up else -NOTE_SHIFT
    for (y, n), sh in zip(pairs, shift):
        draw_ledgers(ax, x + (dx if sh else 0.0), y, bottom_y)
    if up:
        ax.vlines(x + 0.42, ys[0], max(ys[0] + 3.4, ys[-1] + 0.65),
                  color=INK, lw=STEM_LW, zorder=3)
    else:
        ax.vlines(x - 0.42, min(ys[-1] - 3.4, ys[0] - 0.65), ys[-1],
                  color=INK, lw=STEM_LW, zorder=3)
    for (y, n), sh in zip(pairs, shift):
        draw_notehead(ax, x + (dx if sh else 0.0), y)

def draw_brace(ax, x, y_bot, y_top):
    """钢琴谱表左侧的花括号（贝塞尔）"""
    w = 1.0
    ym = (y_bot + y_top) / 2.0
    drop = (y_top - y_bot) * 0.19
    verts = [
        (x, y_top - 0.3), (x, y_top - 0.3 - drop * 0.4),
        (x - w * 0.35, ym + drop), (x - w, ym),
        (x - w * 0.35, ym - drop), (x, y_bot + 0.3 + drop * 0.4),
        (x, y_bot + 0.3),
    ]
    path = Path(verts, [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4,
                        Path.CURVE4, Path.CURVE4, Path.CURVE4])
    ax.add_patch(mpatches.PathPatch(path, facecolor="none", edgecolor=INK,
                                    lw=3.0, capstyle="round", zorder=3))

def draw_key_signature(ax, treble_bottom, bass_bottom, n_sharps=0, n_flats=0):
    """调号（支持 1 个升号 = G 大调 F♯；1 个降号 = F 大调 B♭）。
    F♯：高音谱顶线（F5）、低音谱第 4 线（F3）。
    B♭：高音谱中线（B4）、低音谱第 2 线（B2，自下而上）。"""
    if n_sharps >= 1:
        for y in (treble_bottom + 4, bass_bottom + 3):
            ax.text(SHARP["x"], y - SHARP["dy"], "♯",
                    fontsize=SHARP["size"], fontfamily=MUSIC_FONT,
                    ha="center", va="center", color=INK, zorder=4)
    if n_flats >= 1:
        for y in (treble_bottom + 2, bass_bottom + 1):
            ax.text(FLAT["x"], y - FLAT["dy"], "♭",
                    fontsize=FLAT["size"], fontfamily=MUSIC_FONT,
                    ha="center", va="center", color=INK, zorder=4)

def draw_grand_staff(ax, treble_bottom, bass_bottom, final_barline=False,
                     x0=3.2, x1=92.6, key_sharps=0, key_flats=0):
    """大谱表：两行五线谱 + 花括号 + 起始纵线 + 行尾纵线（可选终止双纵线）+ 调号"""
    top = treble_bottom + 4
    draw_staff(ax, treble_bottom, x0, x1)
    draw_staff(ax, bass_bottom, x0, x1)
    draw_brace(ax, 2.3, bass_bottom, top)
    ax.vlines(x0, bass_bottom, top, color=INK, lw=1.4, zorder=2)
    ax.vlines(x1, bass_bottom, top, color=INK, lw=1.2, zorder=2)
    if final_barline:
        ax.vlines(x1 - 0.9, bass_bottom, top, color=INK, lw=1.2, zorder=2)
        ax.vlines(x1, bass_bottom, top, color=INK, lw=4.2, zorder=2)
    ax.text(6.2, treble_bottom + CLEF_TREBLE["dy"], "\U0001D11E",
            fontsize=CLEF_TREBLE["size"], fontfamily=MUSIC_FONT,
            ha="center", va="center", color=INK, zorder=4)
    ax.text(6.6, bass_bottom + CLEF_BASS["dy"], "\U0001D122",
            fontsize=CLEF_BASS["size"], fontfamily=MUSIC_FONT,
            ha="center", va="center", color=INK, zorder=4)
    draw_key_signature(ax, treble_bottom, bass_bottom, key_sharps, key_flats)
