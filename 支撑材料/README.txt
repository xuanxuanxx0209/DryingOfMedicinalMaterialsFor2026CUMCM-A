2026 年全国大学生数学建模竞赛 A 题支撑材料说明

一、内容与目录

本目录包含四问完整求解程序、复现与绘图程序、必要辅助模块、赛题附件副本、正文引用图件、关键结果表以及 AI 工具使用详情。AI工具使用详情.pdf 为正式提交文件，AI使用报告.docx 为便于参赛队最终审核的可编辑同内容版本。全部路径均为相对路径，不依赖参赛者电脑上的 Codex 或其他个人目录。

二、建议环境

Python 3.12；依赖见 requirements.txt。Numba 为问题四的可选加速依赖，缺少时程序会采用同一算法的纯 Python 路径，但运行时间明显增加。

三、运行方式

在本目录打开命令行，依次执行：

1. 问题一快速检查：python -X utf8 药材烘干求解.py --mode smoke
2. 问题二至问题四公共框架快速检查：python -X utf8 全程干燥求解.py --mode smoke
3. 问题三长时逻辑快速检查：python -X utf8 全程干燥求解.py --mode q3-smoke
4. 问题四移动边界快速检查：python -X utf8 问题4_求解.py --smoke --output results/P1_q4_smoke.json

生成全量结果时执行：

1. 问题一：python -X utf8 药材烘干求解.py --mode q1
2. 问题二：python -X utf8 全程干燥求解.py --mode q2
3. 问题三：python -X utf8 全程干燥求解.py --mode q3
4. 问题四：python -X utf8 问题4_复现.py --output-root .

问题四全量复现会完成主模型、固定半径对照、时空加密及空气边界、传递系数和内部映射敏感性计算，耗时显著长于冒烟测试。四个绘图脚本可在相应结果存在后单独运行：python -X utf8 问题1_绘图.py、问题2_绘图.py、问题3_绘图.py、问题4_绘图.py。

四、输入与输出

输入位于 problem A/附件。主要输出位于 results；正文实际引用的 15 幅 PDF 图件位于 figures。result1.xlsx 至 result4.xlsx 分别对应四个子问题。results/复现清单.json 记录最终问题四复现参数、运行命令和输入文件哈希。

五、提交前核验

参赛队应至少重新执行四项快速检查，确认均无异常；如重新运行全量计算，应核对 result1.xlsx 至 result4.xlsx、各问题结果摘要、论文关键数值和 figures 中图件一致。AI工具使用详情.pdf 为依据现有留痕生成的审核稿，提交前须逐项确认工具名称、版本、时间、用途、提示方式与使用过程。
