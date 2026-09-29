# -*- coding: utf-8 -*-
"""
合并全部练习册 PDF 为一册，便于整体打印。
顺序：三和弦（C→G→F）→ 七和弦（C→G→F），每本 12 页；每本加一条 PDF 书签。
各册页尺寸统一（12.5 x 13.16 in @200dpi），合并后可直接双面打印。

用法：python -X utf8 merge_all_books.py
输出：和弦练习册合集.pdf（根目录）
"""
import os
from pypdf import PdfWriter

BOOKS = [
    ("三和弦 · C 大调", os.path.join("Traid", "Key of C", "C大调和弦练习册.pdf")),
    ("三和弦 · G 大调", os.path.join("Traid", "Key of G", "G大调和弦练习册.pdf")),
    ("三和弦 · F 大调", os.path.join("Traid", "Key of F", "F大调和弦练习册.pdf")),
    ("七和弦 · C 大调", os.path.join("Seventh", "Key of C", "C大调七和弦练习册.pdf")),
    ("七和弦 · G 大调", os.path.join("Seventh", "Key of G", "G大调七和弦练习册.pdf")),
    ("七和弦 · F 大调", os.path.join("Seventh", "Key of F", "F大调七和弦练习册.pdf")),
]

def main():
    w = PdfWriter()
    for title, path in BOOKS:
        if not os.path.exists(path):
            raise SystemExit("缺少 %s" % path)
        w.append(path, outline_item=title)
        print("  + %-14s %s" % (title, path))
    out = "和弦练习册合集.pdf"
    with open(out, "wb") as f:
        w.write(f)
    print("saved: %s（%d 页）" % (out, len(w.pages)))

if __name__ == "__main__":
    main()
