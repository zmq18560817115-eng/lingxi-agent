"""版式模板 —— D3 视觉识别落地前的轻量替代。

内置几种常见版式，需求方在录入时选一个，parse() 按选择返回对应布局树。
纯参数化生成，无需视觉模型/API Key。D3 接真识别后，可由 parse() 在有参考图时
覆盖这里的模板输出。

布局树用一套小词汇（render.py 能画）：
  title_bar 标题栏 / group 分组 / product_card 产品卡 / price_bar 价格条 /
  cell 网格格 / hero 主图区 / text_block 文本块 / list_row 列表行 / category 分类头
"""

from __future__ import annotations

W, H = 1080, 1440
M = 40                      # 页边距
TITLE_H = 200               # 标题栏高
PALETTE = {"primary": "#F5B841", "bg": "#FFF9EF", "text": "#3A3226"}

TEMPLATES = {
    "two_col": "双栏对照",
    "grid": "均分网格",
    "hero_top": "上图下文",
    "list": "分类列表",
}
DEFAULT = "two_col"


def _base(regions: list) -> dict:
    return {"canvas": {"width": W, "height": H, "bg": PALETTE["bg"]},
            "regions": [{"role": "title_bar", "box": [0, 0, W, TITLE_H]}] + regions,
            "palette": dict(PALETTE), "margins_pct": 10}


def _cards_column(x0: int, x1: int, rows: int, label: str = "") -> dict:
    top, bottom = TITLE_H + 40, H - M
    gap = 32
    ch = (bottom - top - gap * (rows - 1)) // rows
    cards = []
    for i in range(rows):
        y0 = top + i * (ch + gap)
        y1 = y0 + ch
        cards.append({"role": "product_card", "box": [x0, y0, x1, y1],
                      "children": [{"role": "price_bar", "box": [x0, y1 - 60, x1, y1]}]})
    return {"role": "group", "label": label, "box": [x0, top, x1, bottom], "children": cards}


def _two_col(rows: int = 3) -> dict:
    return _base([_cards_column(M, 500, rows), _cards_column(540, W - M, rows)])


def _grid(cols: int = 3, rows: int = 2) -> dict:
    top, bottom = TITLE_H + 40, H - M
    gapx = gapy = 32
    cw = (W - 2 * M - gapx * (cols - 1)) // cols
    ch = (bottom - top - gapy * (rows - 1)) // rows
    cells = []
    for r in range(rows):
        for c in range(cols):
            x0 = M + c * (cw + gapx)
            y0 = top + r * (ch + gapy)
            cells.append({"role": "cell", "box": [x0, y0, x0 + cw, y0 + ch],
                          "children": [{"role": "price_bar", "box": [x0, y0 + ch - 56, x0 + cw, y0 + ch]}]})
    return _base(cells)


def _hero_top() -> dict:
    top = TITLE_H + 40
    hero_bottom = top + int((H - top - M) * 0.58)
    tb1 = hero_bottom + 32
    tb2 = (tb1 + H - M) // 2 + 16
    return _base([
        {"role": "hero", "box": [M, top, W - M, hero_bottom]},
        {"role": "text_block", "box": [M, tb1, W - M, tb2 - 16]},
        {"role": "text_block", "box": [M, tb2, W - M, H - M]},
    ])


def _list(categories: int = 2, rows: int = 3) -> dict:
    regions: list = []
    top = TITLE_H + 40
    y = top
    row_h, gap, cat_h, cat_gap = 96, 20, 40, 24
    for _ in range(categories):
        regions.append({"role": "category", "box": [M, y, W - M, y + cat_h]})
        y += cat_h + 8
        for _ in range(rows):
            regions.append({"role": "list_row", "box": [M, y, W - M, y + row_h]})
            y += row_h + gap
        y += cat_gap
    return _base(regions)


def layout_tree(template: str = DEFAULT) -> dict:
    """按模板名返回布局树；未知名回落默认。"""
    return {
        "two_col": _two_col,
        "grid": _grid,
        "hero_top": _hero_top,
        "list": _list,
    }.get(template, _two_col)()
