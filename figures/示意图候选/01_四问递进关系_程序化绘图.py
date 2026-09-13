# Academic Figure Skill Asset Confirmation (verified against assets/figures/)
# (a) 四问演进主链 → cross-type inherit: assets/figures/SankeyDiagram → param inherit
# (b) 几何单因素对照 → cross-type inherit → param inherit
# RULE: "native run" = load pre-rendered PNG via Image.open().ax.imshow().
#       "param inherit" = drawing function below that copies Class A/B/C values.
#       If a panel says "native run" and you write a drawing function, you broke the contract.

# Academic Figure Skill Typography Baseline — COPY VERBATIM, place at TOP of script
import matplotlib as mpl
mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "Liberation Sans"],
    "font.size": 8,
    "axes.titlesize": 8,
    "axes.labelsize": 8,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "legend.fontsize": 8,
    "figure.titlesize": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.6,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "legend.frameon": False,
})

# Academic Figure Skill Nature/Cell/Science Color Palette -- COPY VERBATIM
CATEGORICAL = ["#2166AC", "#B2182B", "#1B7837", "#F1A340", "#762A83", "#666666"]
CATEGORICAL_EXTENDED = [
    "#2166AC", "#B2182B", "#1B7837", "#F1A340", "#762A83", "#666666",
    "#4393C3", "#D6604D", "#5AAE61", "#B35806", "#9970AB", "#999999",
]
DIVERGING   = ["#2166AC", "#F7F7F7", "#B2182B"]
SEQUENTIAL  = ["#F7FBFF", "#6BAED6", "#08306B"]
ACCENT_RED  = "#B2182B"
GREY        = "#999999"
BLACK       = "#222222"

# Academic Figure Skill Export Baseline — COPY VERBATIM
mpl.rcParams.update({
    "pdf.fonttype": 42,         # TrueType font embedding
    "svg.fonttype": "none",     # editable text in SVG
    "savefig.bbox": "tight",    # trim whitespace
    "savefig.dpi": 300,
})

def save_cns_figure(fig, filename):
    """Standard Academic Figure Skill export: vector PDF + 300dpi PNG preview."""
    fig.savefig(f"{filename}.pdf", bbox_inches="tight", dpi=300)
    fig.savefig(f"{filename}.png", bbox_inches="tight", dpi=300)


from pathlib import Path
import sys

mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle
from PIL import Image


ROOT = Path(__file__).resolve().parent
MM = 1 / 25.4
FIGURE_SIZE = (183 * MM, 106 * MM)
OUT_BASENAME = ROOT / "01_四问递进关系"

# 中文正文使用统一的 Noto Sans SC；英文字母和数字同样保持无衬线风格。
FONT_FILE = Path(r"C:\Windows\Fonts\NotoSansSC-VF.ttf")
ZH = FontProperties(fname=str(FONT_FILE), size=8.2)
ZH_SMALL = FontProperties(fname=str(FONT_FILE), size=8.0)
ZH_TINY = FontProperties(fname=str(FONT_FILE), size=7.5)
ZH_BOLD = FontProperties(fname=str(FONT_FILE), size=9.0, weight="bold")
ZH_PANEL = FontProperties(fname=str(FONT_FILE), size=9.5, weight="bold")
ZH_HERO = FontProperties(fname=str(FONT_FILE), size=10.0, weight="bold")

NAVY = "#18324B"
INK = "#24384A"
MUTED = "#617487"
LINE = "#8EA2B2"
PALE = "#F4F7F9"
Q_COLORS = [CATEGORICAL[0], CATEGORICAL_EXTENDED[6], CATEGORICAL[4], CATEGORICAL[2]]
Q_FILLS = ["#EDF4FA", "#EDF7FA", "#F3F0F8", "#EEF7F1"]


def add_text(ax, x, y, text, *, fp=ZH, color=INK, ha="left", va="center", zorder=5):
    return ax.text(
        x, y, text, transform=ax.transAxes, fontproperties=fp,
        color=color, ha=ha, va=va, zorder=zorder,
    )


def round_box(ax, x, y, w, h, *, face, edge, lw=0.9, radius=0.018, zorder=1):
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0.006,rounding_size={radius}",
        transform=ax.transAxes, facecolor=face, edgecolor=edge,
        linewidth=lw, zorder=zorder,
    )
    ax.add_patch(patch)
    return patch


def connector(ax, x0, y0, x1, y1, *, color=LINE, lw=1.2, style="-|>", ls="-"):
    arrow = FancyArrowPatch(
        (x0, y0), (x1, y1), transform=ax.transAxes,
        arrowstyle=style, mutation_scale=10, linewidth=lw,
        linestyle=ls, color=color, shrinkA=1, shrinkB=1, zorder=3,
    )
    ax.add_patch(arrow)
    return arrow


def pill(ax, x, y, w, text, color):
    round_box(ax, x, y, w, 0.048, face="white", edge=color, lw=0.7, radius=0.017, zorder=3)
    add_text(ax, x + w / 2, y + 0.024, text, fp=ZH_TINY, color=color, ha="center")


def stage_card(ax, x, y, w, h, stage):
    color = stage["color"]
    round_box(ax, x, y, w, h, face=stage["fill"], edge=color, lw=1.25, radius=0.022)

    # 顶部编号条同时承担颜色编码，主体保持低饱和以适应打印。
    header_h = 0.082
    head = FancyBboxPatch(
        (x, y + h - header_h), w, header_h,
        boxstyle="round,pad=0.006,rounding_size=0.022",
        transform=ax.transAxes, facecolor=color, edgecolor=color,
        linewidth=0, zorder=2,
    )
    ax.add_patch(head)
    ax.add_patch(Rectangle(
        (x, y + h - header_h), w, header_h / 2,
        transform=ax.transAxes, facecolor=color, edgecolor="none", zorder=2,
    ))
    add_text(ax, x + 0.014, y + h - header_h / 2, stage["label"], fp=ZH_BOLD, color="white")
    add_text(ax, x + w - 0.014, y + h - header_h / 2, stage["time"], fp=ZH_TINY,
             color="white", ha="right")

    top = y + h - header_h - 0.032
    add_text(ax, x + 0.016, top, stage["title"], fp=ZH_HERO, color=NAVY)
    add_text(ax, x + 0.016, top - 0.055, stage["model"], fp=ZH_SMALL, color=INK)

    # 新增或替换项用白底标签，不再另设重复的左侧输入栏。
    pill(ax, x + 0.016, top - 0.125, w - 0.032, stage["delta"], color)
    add_text(ax, x + 0.016, top - 0.158, stage["method"], fp=ZH_TINY, color=MUTED)

    # 结果行使用同色左边线，形成跨卡片一致的视觉语法。
    ax.plot([x + 0.018, x + 0.018], [y + 0.016, y + 0.056], transform=ax.transAxes,
            color=color, linewidth=2.4, solid_capstyle="round", zorder=4)
    add_text(ax, x + 0.030, y + 0.036, stage["result"], fp=ZH_SMALL, color=INK)


def draw_progression(ax):
    add_text(ax, 0.018, 0.953, "a", fp=ZH_PANEL, color=BLACK)
    add_text(ax, 0.048, 0.952, "四问沿同一热质传递主线逐层增加模型复杂度", fp=ZH_HERO, color=NAVY)

    round_box(ax, 0.048, 0.875, 0.904, 0.055, face=PALE, edge="#D4DEE5", lw=0.6, radius=0.015)
    add_text(
        ax, 0.500, 0.902,
        "共同结构：圆柱一维径向方程  ·  侧壁第三类换热/传质边界  ·  径向有限体积法  ·  箭头表示继承",
        fp=ZH_SMALL, color=MUTED, ha="center",
    )

    x_positions = [0.048, 0.282, 0.516, 0.750]
    y, w, h = 0.490, 0.202, 0.344
    stages = [
        {
            "label": "问题一", "time": "0–1800 s", "title": "预热场重构",
            "model": "常物性 · 固定半径 R0", "delta": "输入：附件 1 + 附录 2",
            "method": "边界插值；Fourier / Fick 扩散",
            "result": "输出  T(r,t)、C(r,t)", "color": Q_COLORS[0], "fill": Q_FILLS[0],
        },
        {
            "label": "问题二", "time": "0–3 h", "title": "全程变物性耦合",
            "model": "固定半径 · 顺序耦合", "delta": "替换：附录 3 物性经验式",
            "method": "物性反馈：C→ρ,c_p,k；T,C→D",
            "result": "输出  每 0.5 h 径向场", "color": Q_COLORS[1], "fill": Q_FILLS[1],
        },
        {
            "label": "问题三", "time": "固定 R0", "title": "固定域干燥终点",
            "model": "沿用问题二变物性模型", "delta": "新增：稳定边界延拓 + 阈值",
            "method": "逐秒判定：max C < 0.15",
            "result": "终点  57.4322 h", "color": Q_COLORS[2], "fill": Q_FILLS[2],
        },
        {
            "label": "问题四", "time": "移动 R(t)", "title": "收缩域干燥终点",
            "model": "材料坐标 x = r/R(t)", "delta": "替换：附件 2 + 附录 4",
            "method": "单位网格；终点 R=1.2000 cm",
            "result": "终点  51.0775 h", "color": Q_COLORS[3], "fill": Q_FILLS[3],
        },
    ]

    for x, stage in zip(x_positions, stages):
        stage_card(ax, x, y, w, h, stage)

    for i in range(3):
        x0 = x_positions[i] + w + 0.005
        x1 = x_positions[i + 1] - 0.005
        connector(ax, x0, y + h / 2, x1, y + h / 2, color=LINE, lw=1.25)


def draw_comparison(ax):
    add_text(ax, 0.018, 0.426, "b", fp=ZH_PANEL, color=BLACK)
    add_text(ax, 0.048, 0.425, "收缩效应必须在同一物性口径下比较", fp=ZH_HERO, color=NAVY)

    # 左：标出常见但无效的直接比较，强调“物性 + 几何”同时发生变化。
    round_box(ax, 0.048, 0.075, 0.400, 0.306, face="#FFF7F5", edge="#E5A08F", lw=0.9, radius=0.020)
    add_text(ax, 0.068, 0.342, "不可用于分离收缩效应", fp=ZH_BOLD, color=ACCENT_RED)

    add_text(ax, 0.076, 0.281, "问题三", fp=ZH_SMALL, color=Q_COLORS[2])
    add_text(ax, 0.076, 0.242, "附录 3 物性 · 固定 R0", fp=ZH_TINY, color=INK)
    add_text(ax, 0.076, 0.199, "57.4322 h", fp=ZH_BOLD, color=Q_COLORS[2])

    connector(ax, 0.202, 0.226, 0.302, 0.226, color=ACCENT_RED, lw=1.1, style="-|>", ls="--")
    add_text(ax, 0.252, 0.270, "物性与几何同时改变", fp=ZH_TINY, color=ACCENT_RED, ha="center")
    ax.plot([0.237, 0.267], [0.199, 0.251], transform=ax.transAxes,
            color=ACCENT_RED, linewidth=1.8, zorder=6)
    ax.plot([0.237, 0.267], [0.251, 0.199], transform=ax.transAxes,
            color=ACCENT_RED, linewidth=1.8, zorder=6)

    add_text(ax, 0.324, 0.281, "问题四", fp=ZH_SMALL, color=Q_COLORS[3])
    add_text(ax, 0.324, 0.242, "附录 4 物性 · 收缩 R(t)", fp=ZH_TINY, color=INK)
    add_text(ax, 0.324, 0.199, "51.0775 h", fp=ZH_BOLD, color=Q_COLORS[3])
    add_text(ax, 0.068, 0.119, "结论：两题时长差不能全部归因于半径收缩。", fp=ZH_SMALL, color=INK)

    # 右：准确按时长比例绘制同口径对照条，不把数值关系仅写成文字。
    round_box(ax, 0.478, 0.075, 0.474, 0.306, face="#F6FAFC", edge="#AFC2D0", lw=0.9, radius=0.020)
    add_text(ax, 0.498, 0.342, "有效对照：两情景均采用附录 4 物性", fp=ZH_BOLD, color=NAVY)
    add_text(ax, 0.498, 0.306, "空气边界、初值与数值算法相同；仅半径边界不同", fp=ZH_TINY, color=MUTED)

    bar_x, bar_w = 0.650, 0.255
    base_y, shrink_y = 0.235, 0.169
    base_t, shrink_t = 129.7964, 51.0775
    ratio = shrink_t / base_t

    add_text(ax, 0.500, base_y + 0.019, "固定 R0", fp=ZH_SMALL, color=INK)
    add_text(ax, 0.500, shrink_y + 0.019, "收缩 R(t)", fp=ZH_SMALL, color=INK)
    round_box(ax, bar_x, base_y, bar_w, 0.038, face="#D9E2E8", edge="#A7B6C1", lw=0.5, radius=0.010)
    round_box(ax, bar_x, shrink_y, bar_w * ratio, 0.038, face="#63A979", edge=Q_COLORS[3], lw=0.6, radius=0.010)
    add_text(ax, bar_x + bar_w + 0.012, base_y + 0.019, "129.7964 h", fp=ZH_SMALL, color=INK)
    add_text(ax, bar_x + bar_w * ratio + 0.012, shrink_y + 0.019, "51.0775 h", fp=ZH_SMALL, color=Q_COLORS[3])

    add_text(ax, 0.500, 0.112, "Δt = −78.7189 h", fp=ZH_BOLD, color=INK)
    add_text(ax, 0.690, 0.112, "终点缩短 60.6480%", fp=ZH_BOLD, color=Q_COLORS[3])


def build_figure():
    fig = plt.figure(figsize=FIGURE_SIZE, facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    draw_progression(ax)
    draw_comparison(ax)
    return fig


def main():
    # 使用 math-modeling 科研绘图工具的统一导出器，生成矢量主文件和 600 DPI 预览。
    figure_tools = Path(r"C:\Users\23572\.codex\skills\math-modeling\tools\figure\scripts")
    sys.path.insert(0, str(figure_tools))
    from export_figure import export_figure
    from visual_qa import audit_layout, print_report

    fig = build_figure()
    verdict = print_report(audit_layout(fig))
    if verdict != "PASS":
        raise RuntimeError(f"程序化版面自检未通过：{verdict}")
    # 基线保留自动裁边默认值；正式导出用局部上下文锁定精确物理画布。
    with mpl.rc_context({"savefig.bbox": None}):
        written = export_figure(
            fig,
            basename=str(OUT_BASENAME),
            formats=["pdf", "svg", "png"],
            size_inches=FIGURE_SIZE,
            dpi=600,
            grayscale_preview=True,
            tight=False,
            pad_inches=0.0,
            transparent=False,
        )

    # export_figure 的灰度辅助文件默认不保留 DPI 元数据，这里补写为线稿规格。
    gray_path = OUT_BASENAME.with_name(OUT_BASENAME.name + "_grayscale").with_suffix(".png")
    with Image.open(gray_path) as gray_source:
        gray = gray_source.copy()
    gray.save(gray_path, dpi=(600, 600))
    plt.close(fig)
    for path in written:
        print(path)


if __name__ == "__main__":
    main()
