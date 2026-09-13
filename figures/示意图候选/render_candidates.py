from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont, ImageOps
from reportlab.graphics import renderPDF
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from svglib.svglib import svg2rlg


ROOT = Path(__file__).resolve().parent
FONT = Path(r"C:\Windows\Fonts\simhei.ttf")


def register_fonts() -> None:
    pdfmetrics.registerFont(TTFont("SimHei", str(FONT)))


def render_svg(svg_path: Path) -> Path:
    pdf_path = svg_path.with_suffix(".pdf")
    png_path = svg_path.with_suffix(".png")
    drawing = svg2rlg(str(svg_path))
    if drawing is None:
        raise RuntimeError(f"无法解析 SVG：{svg_path}")
    renderPDF.drawToFile(drawing, str(pdf_path))
    with fitz.open(pdf_path) as doc:
        pix = doc[0].get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        pix.save(str(png_path))
    with Image.open(png_path) as image:
        image.convert("RGB").save(png_path, dpi=(300, 300), quality=95)
    return png_path


def make_gallery(images: list[Path]) -> Path:
    canvas_w, canvas_h = 2200, 2760
    canvas = Image.new("RGB", (canvas_w, canvas_h), "#edf3f7")
    draw = ImageDraw.Draw(canvas)
    title_font = ImageFont.truetype(str(FONT), 58)
    label_font = ImageFont.truetype(str(FONT), 31)
    small_font = ImageFont.truetype(str(FONT), 25)
    draw.text((70, 48), "药材烘干论文非数据型配图候选", fill="#18324b", font=title_font)
    draw.text((70, 122), "当前仅供筛选，尚未插入论文", fill="#617487", font=small_font)

    cell_w, cell_h = 1020, 610
    x_positions = (60, 1120)
    y0 = 190
    labels = {
        "00_热风烘干概念场景候选.png": "00  热风烘干概念场景（AI 生成，非真实设备）",
        "01_四问递进关系.png": "01  四问递进关系与统一证据链",
        "02_烘干过程与径向简化.png": "02  热质传递过程与一维径向简化",
        "03_热质耦合与物性反馈.png": "03  温度—含水率—物性反馈",
        "04_径向有限体积离散.png": "04  径向有限体积离散",
        "05_收缩域材料坐标映射.png": "05  收缩域材料坐标映射",
        "06_任务时间轴与数据边界.png": "06  任务时间轴与数据边界",
    }
    for idx, image_path in enumerate(images):
        row, col = divmod(idx, 2)
        x, y = x_positions[col], y0 + row * 635
        draw.rounded_rectangle((x, y, x + cell_w, y + cell_h), radius=24, fill="white", outline="#c7d5df", width=3)
        with Image.open(image_path) as source:
            preview = ImageOps.contain(source.convert("RGB"), (cell_w - 36, cell_h - 98), Image.Resampling.LANCZOS)
        px = x + (cell_w - preview.width) // 2
        py = y + 18
        canvas.paste(preview, (px, py))
        draw.line((x + 18, y + cell_h - 70, x + cell_w - 18, y + cell_h - 70), fill="#e1e8ed", width=2)
        draw.text((x + 26, y + cell_h - 57), labels[image_path.name], fill="#18324b", font=label_font)

    path = ROOT / "候选图总览.png"
    canvas.save(path, dpi=(180, 180), quality=95)
    return path


def main() -> None:
    register_fonts()
    rendered = [render_svg(path) for path in sorted(ROOT.glob("0[1-6]_*.svg"))]
    scene = ROOT / "00_热风烘干概念场景候选.png"
    with Image.open(scene) as image:
        if image.info.get("dpi") is None:
            normalized = ROOT / "_scene_dpi.png"
            image.convert("RGB").save(normalized, dpi=(300, 300), quality=95)
            normalized.replace(scene)
    gallery = make_gallery([scene, *rendered])
    print(f"rendered={len(rendered)}")
    print(f"gallery={gallery}")


if __name__ == "__main__":
    main()
