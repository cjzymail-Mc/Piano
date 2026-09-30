# AGENTS.md — 钢琴和弦练习谱生成器

本仓库用 matplotlib 生成钢琴练习谱（PNG 谱面 + PDF 练习册），主题是 C/G/F 大调
顺阶三和弦与七和弦的全部把位（12 个密集排列/和弦，音域 A1–F6）。
用户是钢琴学习者，最终产物用于**打印**，一切排版决策以打印紧凑、可读为准。

## 运行环境

- Windows；Python 需带 `matplotlib (Agg)`、`Pillow`、`img2pdf`、`pypdf`
- **一律从仓库根目录运行**：`python -X utf8 src/<脚本>.py`
  （`-X utf8` 处理中文路径/文案；`sys.path[0]=src` 使同目录 import 生效；
  脚本内输出路径均相对 cwd）
- 字体硬依赖系统字体：音乐字形 = Segoe UI Symbol，中文 = Microsoft YaHei
  （`C:/Windows/Fonts/msyh.ttc`，粗体 `msyhbd.ttc`）。换机器需先确认。

## 代码架构（数据流）

```
KEYS (make_chord_inversions)      SEVENTHS (make7_chord_inversions)
  三和弦 3 调 x 7 和弦             七和弦 3 调 x 7 和弦
        │                                │
  build_triads / build_sevenths —— 枚举 12 把位（自最低音≥A1 起，按最低音升序取前 12）
        │                                │
        └───────────┬────────────────────┘
                    ▼
     staff_lib.py（共享绘图库：谱表/谱号/符头/符干/加线/调号/大谱表）
                    ▼
   单弦 PNG（Traid/、Seventh/ 各 Key of X/ 下，每和弦 2 张）
                    ▼
   各调练习册 PDF（12 页版）→ merge_all_books → make_compact_collection（紧凑合集 26 页）
```

- `src/make_compact_collection.py`：当前主力。柱式 4 合 1 条带 + 琶音 1 页 3 和弦
  （单行大谱表 x 12 列，调号随块、支持跨调同页）+ 目录页；`sample` 出样张、`full` 出 PDF。
- `src/check_compact_layout.py`：**几何校验器**，对全部 42 和弦 x 12 把位做包围盒
  碰撞断言（名称带/标签/标题 vs 符头/符干/加线，含共用符干与二度错位建模）。

## 关键约定（改版式前必读）

**单位系统与尺寸耦合**：1 数据单位 = 1 个谱线间距 = 9.474pt（各图 xlim 95 ↔ 12.5in）。
figure 高度必须 = ylim 跨度 / 7.5994（如跨度 24.65 → 3.2438in），否则符头 TextPath
变换与谱线错位。页面画布 2500 x 2632 px（12.5 x 13.16in @200dpi）；
PDF 统一 `img2pdf.get_fixed_dpi_layout_fun((200, 200))`，页面尺寸应为 900 x 947.5 pt。

**紧凑版坐标预算（两页型共用同一套）**：

| 元素 | 位置 | 依据 |
|---|---|---|
| 和弦名称带 | `bass底线 + 8.25`（10pt 粗体） | 下清低音组最高音 G4（头顶 +7.55），上清高音组最低音 B3（头底 +8.95） |
| 音名（含八度）行 | `bass底线 − 4.45`（8pt 灰） | 下让 A1 符头/加线（墨迹至 −3.55） |
| 高/低音谱底间距 | 11 | 中缝容得下名称带（详见下"已否决方案"） |
| 谱表上方墨迹预算 | treble底线 + 8.05 | 最高音 F6 符头顶 |
| 琶音页 3 块谱底线 | `[87.7, 54.8, 21.9]` | 块距 = 4.93(标签) + 12.05(顶墨迹) 的富余分配 |

**枚举规则**：把位 = 密集排列，从最低音 ≥ A1 的排法起按最低音升序取 12 个；
柱式与琶音共用同一 build 函数，转位由斜杠和弦名（C/E = 第一转位）表达。

**绘图细节**：`draw_chord` 对相邻二度音做横向错位（NOTE_SHIFT=1.08，符干从两符头间
穿过）；`draw_ledgers` 加线网格锚定 `bottom_y`（谱底线可为任意实数，勿改回整数取整）；
音符高低分配阈值 `TREBLE_FROM = B3`（最低音 < B3 上低音谱表）。

## 工作流规则

1. **样张先行**：任何版式改动先 `sample` 出样张（`样张_*.png`）给用户确认，
   确认后才批量。已确认版式不回改。
2. **几何校验兜底**：改布局常量后必须跑
   `python -X utf8 src/check_compact_layout.py` 且 **FAILURES: 0**；
   眼看不可靠（本会话两次"目测没问题"都被用户打回），以包围盒断言为准。
3. **不修改已交付产物**：Traid/ 下已确认的 PNG 内容不动（尤其 Key of C）；
   需要新版式时新开脚本（make7_* 与 make_compact_* 即此惯例）。
4. **用户手工 push**：只做 commit，不 push。commit 中文消息、分层提交
   （库修复 / 工具链 / 成品 分开），消息尾加
   `Co-Authored-By: Claude Code <noreply@anthropic.com>`。
5. 中间产物 `build_紧凑版/`、`__pycache__/` 已 gitignore，可随时删除重建。

## 已否决方案（勿重蹈）

- **琶音页 4 行 x 6 组**：下一行高把位音（C6/E6/F6，谱上 2–3 条加线，墨迹至
  treble+8.05）必然顶进上一行标签带，行高 ~32 x 4 = 128 > 100 页高，
  数学上放不下 → 改用"每和弦单行大谱表 x 12 列"。
- **50% 等比缩放拼版**：用户判定太小，谱表必须原尺寸重绘。
- **标签带放谱表中缝 bass+6.1 附近**：低音组顶音（E4/F4/G4 加线音）恰好占该带 →
  名称带唯一可行位是 bass+8.25（配谱底间距 11）。
- 转位文字行 / 中央C 标注：与带八度音名冗余，已删（八度号自带信息）。

## 常用命令

```bash
python -X utf8 src/make_compact_collection.py sample   # 两张样张
python -X utf8 src/make_compact_collection.py full     # 26 页合集 PDF（和弦练习册合集.pdf）
python -X utf8 src/check_compact_layout.py             # 几何校验（须 0 失败）
python -X utf8 src/make_chord_inversions.py            # 三和弦单弦 PNG（Traid/）
python -X utf8 src/make7_chord_inversions.py           # 七和弦单弦 PNG（Seventh/）
```
