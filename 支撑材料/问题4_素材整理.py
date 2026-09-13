"""Generate auditable paper materials from frozen numerical output, without writing paper prose."""
from pathlib import Path
import json,sys,re
import numpy as np
import pandas as pd
import 问题4_求解 as q

def main(out=q.ROOT):
    out=Path(out);folder=out/'Q4';folder.mkdir(exist_ok=True);res=out/'results'
    s=json.loads((res/'问题4_结果摘要.json').read_text(encoding='utf-8'))
    table=pd.read_csv(res/'问题4_表6含水率.csv');cases=pd.read_csv(res/'问题4_情景汇总.csv')
    a=cases.set_index('scenario')
    latex=[r'% 自动读取高精度结果生成；片段内容已同步入正文，但正文未通过\input直接引用本文件；需要booktabs。',r'\begin{table}[htbp]',r'\centering',r'\caption{考虑尺寸收缩的药材含水率（kg/kg）}',r'\label{tab:q4-moisture}',r'\begin{tabular}{rrrrrrr}',r'\toprule',r'时间/h & 半径/cm & 0 cm & 0.5 cm & 1.0 cm & 1.5 cm & 药材表面\\',r'\midrule']
    rows=[]
    for _,r in table.iterrows():
        vals=['---' if pd.isna(v) else f'{v:.4f}' for v in r[['time_h','radius_cm','r0_cm','r0.5_cm','r1_cm','r1.5_cm','surface']]]
        latex.append(' & '.join(vals)+r'\\')
        rows.append('| '+' | '.join(vals)+' |')
    latex += [r'\bottomrule',r'\end{tabular}',r'\par\smallskip{\footnotesize 横线表示固定位置已位于药材域外；末列独立记录当前表面。终点中心四位显示为0.1500，未舍入值严格小于0.15。}',r'\end{table}']
    (folder/'表6_可插入.tex').write_text('\n'.join(latex),encoding='utf-8')
    macros={'QFourDryHours':s['dry_time_h'],'QFourFixedHours':s['fixed_radius_dry_time_h'],
            'QFourGeometryPercent':s['eta_geometry_percent'],'QFourShapePercent':s['E_shape_percent'],
            'QFourHeatSensitivityPercent':s['E_h_percent'],
            'QFourMassSensitivityPercent':s['E_hm_percent']}
    bs=chr(92)
    (folder/'关键数值_可引用.tex').write_text('% 自动生成；数值已同步入正文，但正文未通过\\input直接引用本文件\n'+'\n'.join(f'{bs}newcommand{{{bs}{k}}}{{{v:.4f}}}' for k,v in macros.items()),encoding='utf-8')
    evidence=[
        ('附录4物性','题面第4页；问题4_求解.py props','existing eq:q4-properties','ρ,cp,k,D系数一致，Arrhenius温度用K'),
        ('相似收缩与表面条件','题目分析报告.md Q4；geometry/kernel','existing eq:moving-heat / moving-moisture / moving-boundaries','保留既有正确公式'),
        ('一般非均匀映射','题目分析报告.md Q4；geometry','eq:q4-nonuniform-map','rξ>0；同外半径a*=0,±0.1,±0.2'),
        ('固定半径反事实','results/q4_runs/fixed.json','eq:q4-geometry-result','模型内对照；必须同附录4，不得替用Q3'),
        ('正式干燥时间','results/问题4_结果摘要.json dry_time_s/h','tab:q4-moisture','全部节点每1秒检验严格<0.15'),
        ('表6','results/问题4_表6含水率.csv；Q4/表6_可插入.tex','tab:q4-moisture','浮点结果生成，结构性空值保留'),
        ('完整结果Excel','results/result4.xlsx','待下一轮附录清单','60s间隔加终点；22列、四位显示'),
        ('ηR','results/问题4_结果摘要.json eta_geometry_percent','eq:q4-geometry-result','分母为同物性固定半径时长；不作真实因果解释'),
        ('ηa及Eshape','results/问题4_结果摘要.json eta_shape_percent/E_shape_percent','eq:q4-shape-error','双侧确定性结构扰动，不是置信区间'),
        ('h、hm终点敏感性','results/问题4_边界参数敏感性.csv','tab:q4-transfer-sensitivity','分别±20%单因素完整复算'),
        ('数值误差','results/问题4_数值加密.csv','eq:q4-refinement-error','空间与时间分别检验，同6h表格位置'),
        ('离散平衡','results/q4_runs/main.json','existing eq:global-moisture-balance','有效方程残差，不是物理质量守恒证明'),
        ('12幅候选图','figures/q4/图表契约.json 与图表说明.md','已选图入正文，其余保留为候选','各图PDF/SVG/PNG，灰度在_qa'),
    ]
    pd.DataFrame(evidence,columns=['claim','evidence','paper_location','check']).to_csv(res/'问题4_论文核对.csv',index=False,encoding='utf-8-sig')
    md=['# 问题四主张—证据与论文核对','', '本轮已把固定半径反事实、双侧结构扰动及边界传递系数敏感性并入论文源文件。','', '| 主张 | 权威证据 | 论文落点/状态 | 核验口径 |','|---|---|---|---|']
    md += ['| '+' | '.join(row)+' |' for row in evidence]
    md += ['', '## 本轮论文修正', '', '入口为完整论文-LaTeX/example.tex，根目录example.tex是模板。本轮把固定半径结果改写为模型内反事实，不再表述为真实独立因果效应；把a*扩展为±0.1、±0.2双侧结构扰动；新增h、hm分别±20%的终点时长敏感性。旧PDF和压缩包未重新编译或导出，不能当作当前源码版本。', '', '## 口径限制', '', '1. ρ只用于题设热容量，不由ρ/(1+C)反演真实干固体运动；不声称完整多相质量守恒。', '2. 热平衡使用合并历史状态的绝对量作为归一分母，比逐项历史绝对值和更严格；记录中同时给出绝对残差。', '3. 结构情景a*=±0.1、±0.2不是材料参数估计；h、hm的±20%是确定性单因素情景，不是置信区间。固定半径反事实是第四题物性下人为关闭收缩的解释实验，不是正式答案，也不作真实因果解释。', '4. N=320/640事件相差13s，主步长1s只是事件分辨率，不是物理或空间误差界。', '5. 长期空气边界延拓仍是假设；有效模型未验证端面通量和显式蒸发潜热。', '', '## 文献素材', '', 'Adrover A, Brasiello A, Ponso G. A moving boundary model for food isothermal drying and shrinkage: General setting. Journal of Food Engineering, 2019, 244:178–191. DOI:10.1016/j.jfoodeng.2018.09.018。作者机构原始记录：https://iris.uniroma1.it/handle/11573/1156871 。只用于方法背景，不冒称本题映射已获实验验证。', 'Adrover A, Brasiello A. A moving boundary model for food isothermal drying and shrinkage: One-dimensional versus two-dimensional approaches. Journal of Food Process Engineering, 2019, 42(6):e13178. DOI:10.1111/jfpe.13178。https://onlinelibrary.wiley.com/doi/10.1111/jfpe.13178 。提示一维近似局限，不能把几何面积比当严格误差证明。', '', '双引擎原始日志位于build/q4_audit/literature_search.json。limit=5截取展示数组，stats保留截取前数量；General setting采用原始机构记录核验，未称双引擎交叉命中。']
    (folder/'问题四证据映射.md').write_text('\n'.join(md),encoding='utf-8')
    v=s['verification']
    guide=f'''# 问题四计算交付说明

本轮交付模型、可复现代码、真实数值结果及已更新的论文源文件。

## 可核验核心结果

| 项目 | 计算结果 |
|---|---:|
| 主模型干燥时长 | {s['dry_time_s']:.0f} s = {s['dry_time_h']:.4f} h |
| 同附录4固定半径对照 | {s['fixed_radius_dry_time_s']:.0f} s = {s['fixed_radius_dry_time_h']:.4f} h |
| 净几何效应ηR | {s['eta_geometry_percent']:.6f}% |
| a*=-0.2时长 | {a.loc['shape_-0.2','dry_time_h']:.6f} h |
| a*=-0.1时长 | {a.loc['shape_-0.1','dry_time_h']:.6f} h |
| a*=0.1时长 | {a.loc['shape_0.1','dry_time_h']:.6f} h |
| a*=0.2时长 | {a.loc['shape_0.2','dry_time_h']:.6f} h |
| 最大结构偏差 | {s['E_shape_percent']:.6f}% |
| h的±20%最大时长变化 | {s['E_h_percent']:.6f}% |
| hm的±20%最大时长变化 | {s['E_hm_percent']:.6f}% |
| 结束时半径 | {s['radius_end_cm']:.4f} cm |
| 前一秒全域最大含水率 | {s['previous_Cmax']:.12f} kg/kg |
| 终点全域最大含水率 | {s['final_Cmax']:.12f} kg/kg |

主模型约51.08h达到阈值，早于附件2的72h观测终点，未用到半径末值延拓。四种双侧结构扰动仅检验当前映射族，不能推断所有内部收缩模型均不敏感。净几何差异须以同附录4对照为基准，Q3不能替代该对照；该比较是模型内反事实，不作真实独立因果解释。

## 数值验证

主网格{int(s['N'])}个径向区间、1s时间步，首步BE、后续BDF2。最终网格上0.5s复算终点差{v['time_1_0.5']['event_difference_s']:.1f}s，共同表6点最大差{v['time_1_0.5']['table_max_abs_kg_kg']:.8g} kg/kg。320/640网格终点差{abs(v['space_320_640']['event_difference_s']):.0f}s（{v['space_320_640']['event_relative_percent']:.8f}%），表6最大差{v['space_320_640']['table_max_abs_kg_kg']:.8g} kg/kg，均通过事前门槛。

最大Picard次数{s['max_picard_iterations']}；水方程离散平衡相对残差{s['moisture_balance_relative']:.5g}；热方程归一残差{s['heat_balance_scaled']:.5g}；热、水线性残差分别{s['heat_linear_residual']:.5g}和{s['moisture_linear_residual']:.5g}。这些数字验证有效方程的计算，不证明真实干固体质量闭合。

## 表6素材

所有含水率单位为kg/kg；“---”表示该固定位置在当前药材外。表面单独给出。

| 时间/h | 半径/cm | 0 cm | 0.5 cm | 1.0 cm | 1.5 cm | 药材表面 |
|---|---|---|---|---|---|---|
'''+ '\n'.join(rows)+f'''

四位显示的终点中心0.1500是舍入，判断使用未舍入值。result4.xlsx有{s['excel_rows']}条数据、{s['excel_columns']}列，固定位置0–1.9cm每0.1cm加表面。起始60s，最后{s['dry_time_s']:.0f}s；域外结构空值{s['structural_empty_cells']}个，每个已逐项核对。

## 使用与复现

从项目根目录执行：`python -X utf8 问题4_复现.py`。完整入口重新计算所有情景、表格、12幅图、素材和复现清单。隔离复算：`python -X utf8 问题4_复现.py --output-root build/q4_reproduction`。

本轮数值复算使用Python3.12、NumPy、SciPy、pandas、openpyxl；图表使用Matplotlib和Pillow；本机加速依赖Numba0.67.0/llvmlite0.49.0安装在build/q4_runtime，亦可用标准pip安装。无Numba时同算法退回Python，速度明显下降。绘图及清单调用本机math-modeling技能脚本，技能位置与输入哈希见复现清单。`全程干燥求解.py --mode q4`是历史未完成入口，本轮不要使用。

| 文件/目录 | 用途 |
|---|---|
| 题目分析报告.md、术语表格.md | 冻结模型、补齐公式、单位、假设、验证门槛 |
| 问题4_求解.py、问题4_复现.py、问题4_绘图.py、问题4_素材整理.py | 核心、完整入口、绘图、素材自动生成 |
| results/result4.xlsx | 题定完整输出 |
| results/问题4_表6含水率.csv | 高精度表6 |
| results/q4_runs | 各情景高精度场与诊断；main.npz为主模型 |
| results/问题4_情景汇总.csv、问题4_边界参数敏感性.csv、问题4_数值加密.csv | 几何、结构、边界和数值证据 |
| figures/q4 | 3张原始、4张过程、5张结果图，PDF/SVG/300DPI PNG |
| figures/q4/_qa | 12张灰度预览 |
| Q4/表6_可插入.tex、关键数值_可引用.tex | 内容已同步入正文的LaTeX备用片段；正文未通过input直接引用 |
| Q4/问题四证据映射.md、results/问题4_论文核对.csv | 主张与证据、正文核对、图表落点 |
| results/复现清单.json | 输入SHA256、依赖、种子、参数、唯一命令 |
| build/q4_audit | M1/P1/P2与脚本门禁证据、构建记录 |

题面附件、Q4原始思路稿及Q1–Q3权威结果未改动。论文源文件已并入本轮Q4修改并通过静态校验；按用户要求没有调用LaTeX编译，因此旧PDF不是当前源码的渲染结果。

## 数据剖析与写作边界

附件1的241条及附件2的145条均无缺失。半径分布IQR规则标记早期28点，这些是时间演化形成的真实大半径，不删除、不缩尾。空气稳定段91点只用于均值与总体标准差，图中不是置信区间。12幅图契约见figures/q4/图表契约.json。

主模型仍依赖一维径向有效扩散、表面对流参数沿用和长期空气均值假设；没有内部形变观测及完整多相质量闭合。稿件最终需由队伍阅读、核对和改写，不应把素材原样视作已完成参赛论文。
'''
    (folder/'问题四交付说明.md').write_text(guide,encoding='utf-8')

if __name__=='__main__':main()
