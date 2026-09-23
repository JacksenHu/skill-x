#!/usr/bin/env python3
"""零依赖 SVG 思维导图渲染器。

输入 YAML(受限子集,手写解析):
  root: 根节点文本
  children:
    - label: 分支文本
      children:
        - label: 子分支文本

布局:左根右树;叶子纵向均分,父节点取子节点纵向均值。
输出:独立 SVG 文件(可外部 <img> 引用)。
"""
import re
import sys
from pathlib import Path

NODE_H = 30
V_GAP = 14
H_GAP = 64
PAD_X = 14
FONT = "font-family='Microsoft YaHei,Segoe UI,sans-serif'"
PALETTE = ["#0ea5e9", "#8b5cf6", "#10b981", "#f59e0b", "#ef4444", "#06b6d4", "#ec4899", "#84cc16"]


def parse_map(text: str):
    """解析受限 YAML -> {'label':..., 'children':[...]}。"""
    lines = [ln for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    root = {"label": "", "children": []}
    # stack: (indent, node_children_list)
    stack = [(-1, root["children"])]
    for ln in lines:
        indent = len(ln) - len(ln.lstrip())
        s = ln.strip()
        if s.startswith("root:"):
            root["label"] = s[5:].strip().strip('"').strip("'")
            continue
        if s == "children:":
            continue
        m = re.match(r"^-\s*label\s*:\s*(.*)$", s)
        if m:
            node = {"label": m.group(1).strip().strip('"').strip("'"), "children": []}
            while stack and indent <= stack[-1][0]:
                stack.pop()
            stack[-1][1].append(node)
            stack.append((indent, node["children"]))
            continue
        if s.startswith("-"):
            node = {"label": s[1:].strip().strip('"').strip("'"), "children": []}
            while stack and indent <= stack[-1][0]:
                stack.pop()
            stack[-1][1].append(node)
            stack.append((indent, node["children"]))
    return root


def text_width(s: str) -> int:
    units = sum(2 if ord(c) > 0x2E7F else 1 for c in s)
    return units * 8 + PAD_X * 2


def layout(node, depth, y0):
    """返回 (nodes, links, next_y)。nodes: (x,y,w,label,color_depth)"""
    my_w = text_width(node["label"])
    nodes, links = [], []
    children = node.get("children") or []
    if not children:
        y = y0 + NODE_H / 2
        nodes.append((depth, y, my_w, node["label"]))
        return nodes, links, y0 + NODE_H + V_GAP, y
    child_ys = []
    cur = y0
    for ch in children:
        cn, cl, cur, cy = layout(ch, depth + 1, cur)
        nodes.extend(cn)
        links.extend(cl)
        child_ys.append(cy)
    my_y = (child_ys[0] + child_ys[-1]) / 2
    nodes.append((depth, my_y, my_w, node["label"]))
    for cy in child_ys:
        links.append((my_y, cy))
    return nodes, links, cur, my_y


def render_svg(root, title=""):
    nodes, links, total_h, _ = layout(root, 0, V_GAP)
    # 计算每列 x 偏移(按列最大宽度)
    col_w = {}
    for depth, y, w, label in nodes:
        col_w[depth] = max(col_w.get(depth, 0), w)
    col_x, acc = {}, 20
    for d in sorted(col_w):
        col_x[d] = acc
        acc += col_w[d] + H_GAP
    width = acc - H_GAP + 20
    height = int(total_h + V_GAP)

    placed = {}
    for depth, y, w, label in nodes:
        placed[(depth, y)] = (col_x[depth], w)

    def find_node(depth, y):
        return placed.get((depth, y), (0, 0))

    # 连线:按 (depth, y) 找父子——用 (parent_y, child_y) 链接记录,但需重建父子关系
    parts = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>",
             "<rect width='100%' height='100%' fill='#ffffff' rx='8'/>"]
    # 重建父子:layout 时 links 只有 y 对,改为在 layout 中记录 (parent_key, child_key)
    # 简化:二次遍历建立连接(按深度差与 y 序)
    by_depth = {}
    for depth, y, w, label in sorted(nodes, key=lambda n: (n[0], n[1])):
        by_depth.setdefault(depth, []).append((y, w, label))

    def draw_node(depth, y, w, label, root_node=None):
        x = col_x[depth]
        cy = y - NODE_H / 2
        color = PALETTE[(root_node if root_node is not None else depth) % len(PALETTE)]
        if depth == 0:
            color = "#1a1d24"
        parts.append(f"<rect x='{x}' y='{cy}' width='{w}' height='{NODE_H}' rx='8' fill='{color}22' stroke='{color}' stroke-width='1.5'/>")
        parts.append(f"<text x='{x + w/2}' y='{y + 5}' text-anchor='middle' font-size='13' fill='#1a1d24' {FONT}>{_esc(label)}</text>")

    def link(parent, child, color_idx):
        pd, py = parent
        cd, cy = child
        x1 = col_x[pd] + col_w[pd]
        x2 = col_x[cd]
        color = PALETTE[color_idx % len(PALETTE)]
        mx = (x1 + x2) / 2
        parts.append(f"<path d='M{x1},{py} C{mx},{py} {mx},{cy} {x2},{cy}' fill='none' stroke='{color}' stroke-width='1.5' opacity='0.75'/>")

    # 递归绘制(重新走树,携带父信息)
    def draw(node, depth, y, color_idx):
        # 找自身节点坐标
        my = None
        for d, yy, w, label in nodes:
            if d == depth and abs(yy - y) < 0.01 and label == node["label"]:
                my = (d, yy, w, label)
                break
        if not my:
            return
        draw_node(*my, color_idx if depth else None)
        children = node.get("children") or []
        if not children:
            return
        # 子节点坐标:按 layout 的同序匹配
        ys = []
        for d, yy, w, label in nodes:
            if d == depth + 1 and any(c["label"] == label for c in children):
                ys.append((yy, label))
        ys.sort()
        for yy, label in ys:
            child_color = color_idx if depth else [c["label"] for c in children].index(label)
            link((depth, my[1]), (depth + 1, yy), child_color)
        for ch in children:
            for yy, label in ys:
                if label == ch["label"]:
                    draw(ch, depth + 1, yy, color_idx if depth else (children.index(ch)))
                    break

    root_y = None
    for d, yy, w, label in nodes:
        if d == 0 and label == root["label"]:
            root_y = yy
    draw(root, 0, root_y if root_y is not None else 0, 0)
    if title:
        parts.append(f"<text x='20' y='{height - 8}' font-size='11' fill='#9ca3af' {FONT}>{_esc(title)}</text>")
    parts.append("</svg>")
    return "".join(parts)


def _esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def render_file(yaml_path, out_path, title=""):
    root = parse_map(Path(yaml_path).read_text(encoding="utf-8"))
    svg = render_svg(root, title)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(svg, encoding="utf-8")
    return out_path


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        render_file(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")
        print(f"rendered -> {sys.argv[2]}")
    else:
        demo = """root: 示例技能
children:
  - label: 核心能力
    children:
      - label: 能力 A
      - label: 能力 B
  - label: 适用场景
    children:
      - label: 场景 X
"""
        print(render_svg(parse_map(demo), "demo")[:300])
