# Overleaf 上传与编译说明

## 上传项目

打开 Overleaf 并登录，在项目首页选择 New Project，再选择 Upload Project。上传项目根目录中的 `完整论文-Overleaf.zip`。压缩包解压后，`example.tex`、`cumcmthesis.cls`、`cumcm2026.sty` 和 `figures` 文件夹应位于项目顶层。

不要只上传 `example.tex`。文档类、2026 年样式文件和图片目录缺失都会导致编译失败。

## 设置编译器

进入项目后打开左上角 Menu。在 Compiler 中选择 XeLaTeX，在 TeX Live version 中选择 2026 或界面提供的最新版本。Main document 选择 `example.tex`。保存设置后点击 Recompile。

Overleaf 会自动调用编译流程，不需要手工输入 `xelatex` 命令。项目没有启用 shell escape，也没有外部 BibTeX 文件。

## 继续编辑

正文入口是 `example.tex`。图片统一放在 `figures` 文件夹，并在正文中使用相对路径引用。新增图片建议采用英文文件名，优先使用 PDF 或 PNG 格式。

摘要和关键词目前整页留空，待四问结果完成后再填写。问题二至问题四的计算结果位置仍是 LaTeX 注释，占位注释不会显示在 PDF 中。当前可核验的正式数值仅来自问题一。

## 常见问题

若出现找不到 `cumcmthesis.cls` 或 `cumcm2026.sty`，说明压缩包目录层级被改变，应确认这两个文件与 `example.tex` 位于同一级。若出现找不到图片，应检查 `figures` 文件夹名称和正文路径是否一致。

导言区已设置字体回退。本机存在宋体等 Windows 字体时使用本机字体，Overleaf 未安装这些字体时自动使用 TeX Live 自带的 Fandol 字体。不要删除 `fontset=none` 选项或字体回退代码。

本地编译使用 XeLaTeX 并已通过。若 Overleaf 仍提示宏包版本问题，可把 TeX Live version 改为 2026 或当前最新版本后重新编译。
