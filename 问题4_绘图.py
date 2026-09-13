"""Evidence plots for Q4. All values read from actual solver outputs."""
from pathlib import Path
import sys,json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
import 问题4_求解 as q

FIGURE_TOOLS=q.ROOT/'figure_tools'
sys.path.insert(0,str(FIGURE_TOOLS))
from export_figure import export_figure
from setup_style import setup_style
from utils.plot_style import publication_subplots

COLORS=['#0072B2','#D55E00','#009E73','#CC79A7','#666666']
STYLES=['-','--','-.',':','-']

def refinement_figure(verification):
    fig,ax=publication_subplots(1,1,width='report',aspect=.60)
    ys=np.arange(len(verification))
    ax.scatter(verification.table_max_abs_kg_kg,ys,s=38,color=COLORS[0],marker='D')
    for y,value in zip(ys,verification.table_max_abs_kg_kg):
        coefficient,exponent=f'{value:.4e}'.split('e')
        ax.annotate(rf'${coefficient}\times10^{{{int(exponent)}}}$ kg/kg',
                    (value,y),xytext=(10,0),textcoords='offset points',
                    va='center',ha='left',fontsize=9)
    ax.axvline(5e-5,color=COLORS[1],ls='--',lw=1,label='四位小数半单位')
    labels=[v.replace('space_','网格 ').replace('time_','时间步 ').replace('_',' / ') for v in verification.scenario]
    ax.set_yticks(ys,labels);ax.set_xlabel('共同表6位置的最大绝对差 / (kg/kg)');ax.set_ylim(-.6,len(ys)-.4)
    ax.ticklabel_format(axis='x',style='sci',scilimits=(0,0));ax.legend(loc='lower right',frameon=False)
    return fig

def figure16_only():
    setup_style(journal='general',lang='zh',serif_for_zh=True)
    plt.rcParams.update({'font.size':9,'axes.labelsize':9,'xtick.labelsize':8,'ytick.labelsize':8,'legend.fontsize':8,'svg.fonttype':'none','pdf.fonttype':42})
    verification=pd.read_csv(q.ROOT/'results/问题4_数值加密.csv')
    fig=refinement_figure(verification)
    stem=q.ROOT/'figures/q4/process_q4_refinement'
    export_figure(fig,str(stem),formats=['pdf','svg','png'],dpi=300,size_inches=tuple(fig.get_size_inches()),grayscale_preview=True)
    gp=stem.with_name(stem.name+'_grayscale.png')
    with Image.open(gp) as im:im.copy().save(stem.parent/'_qa'/gp.name,dpi=(300,300))
    gp.unlink()
    plt.close(fig)

def main(out=q.ROOT):
    out=Path(out);res=out/'results';figdir=out/'figures/q4';figdir.mkdir(parents=True,exist_ok=True)
    data=res/'q4_plot_data';data.mkdir(parents=True,exist_ok=True)
    setup_style(journal='general',lang='zh',serif_for_zh=True)
    plt.rcParams.update({'font.size':9,'axes.labelsize':9,'xtick.labelsize':8,'ytick.labelsize':8,'legend.fontsize':8,'svg.fonttype':'none','pdf.fonttype':42})
    air,rad,ss=q.input_data();base=q.load_run(res/'q4_runs/main.npz');fixed=q.load_run(res/'q4_runs/fixed.npz')
    summary=json.loads((res/'问题4_结果摘要.json').read_text(encoding='utf-8'))
    scenarios=pd.read_csv(res/'问题4_情景汇总.csv');verification=pd.read_csv(res/'问题4_数值加密.csv')
    contracts=[]
    def figax():
        return publication_subplots(1,1,width='report',aspect=.60)
    def finish(fig,name,claim,source,kind='折线',caption=''):
        size=tuple(fig.get_size_inches())
        contracts.append({'name':name,'question':'q4','claim':claim,'source':source,'chart':kind,'layout':'single primary quantitative panel; shared-variable panels only when needed','backend':'Python','size_inches':size,'dpi':300,'caption':caption or claim,'statistical_scope':'deterministic model scenarios; no statistical CI or significance claim'})
        export_figure(fig,str(figdir/name),formats=['pdf','svg','png'],dpi=300,size_inches=size,grayscale_preview=True)
        gp=figdir/(name+'_grayscale.png')
        qa=figdir/'_qa';qa.mkdir(exist_ok=True)
        with Image.open(gp) as im:im.copy().save(qa/gp.name,dpi=(300,300))
        gp.unlink()
        plt.close(fig)

    # Raw 1: measured radius and the exact interpolation.
    fig,ax=figax();hours=rad.time_s/3600
    ax.plot(hours,rad.radius_m*100,color=COLORS[0],lw=1.5)
    ax.scatter(hours[::4],rad.radius_m[::4]*100,s=12,facecolors='white',edgecolors=COLORS[0],zorder=3)
    ax.set(xlabel='时间 / h',ylabel='实测外半径 / cm',xlim=(0,72),ylim=(1.1,2.06))
    pd.DataFrame({'time_h':hours,'radius_cm':rad.radius_m*100}).to_csv(data/'radius.csv',index=False)
    finish(fig,'raw_q4_radius','附件2外半径早期快速减小，后期趋于平台。','problem A/附件/附件2.xlsx',caption='全部145点线性连接；空心标记每4点展示一次，未删去计算输入。')

    # Raw 2: actual stable-period fluctuations; separate units.
    mask=(air.time_s>=9000)&(air.time_s<=14400)
    fig,axes=plt.subplots(1,2,figsize=(6.3,3.5),layout='constrained')
    axes[0].hist(air.temperature_c[mask],bins=8,color=COLORS[0],edgecolor='white')
    axes[1].hist(air.moisture[mask],bins=8,color=COLORS[1],edgecolor='white')
    for ax in axes:ax.set_ylabel('观测点数');ax.spines[['top','right']].set_visible(False)
    axes[0].set_xlabel('稳定段空气温度 / ℃');axes[1].set_xlabel('稳定段空气水分浓度 / (kg/kg)')
    axes[1].ticklabel_format(axis='x',style='sci',scilimits=(0,0),useOffset=False)
    pd.DataFrame({'temperature_C':air.temperature_c[mask],'air_C':air.moisture[mask]}).to_csv(data/'stable_air.csv',index=False)
    finish(fig,'raw_q4_air_distribution','91个稳定段样本在平台值附近波动。','problem A/附件/附件1.xlsx','直方图','9000–14400 s的91点；图示观测分布，不是参数置信区间。')

    # Raw 3: radius-loss rate calculated directly from adjacent measurements.
    speed=-np.diff(rad.radius_m*100)/np.diff(hours)
    midR=(rad.radius_m[1:]+rad.radius_m[:-1])*50
    fig,ax=figax();ax.scatter(midR,speed,s=14,color=COLORS[0],alpha=.8)
    ax.set(xlabel='相邻时段平均半径 / cm',ylabel='分段收缩速率 / (cm/h)',ylim=(-.01,max(speed)*1.08))
    pd.DataFrame({'mean_radius_cm':midR,'shrink_rate_cm_h':speed}).to_csv(data/'shrink_rate.csv',index=False)
    finish(fig,'raw_q4_shrink_rate','原始半径记录对应的收缩速率随尺寸减小趋近零。','results/q4_plot_data/shrink_rate.csv','散点图','144个相邻观测区间的差商；零速率保留，不拟合相关性。')

    # Process 1: admissible material mappings, final g=1; not measured displacements.
    fig,ax=figax();xi=np.linspace(0,1,101)
    mapping={'xi':xi}
    for j,a in enumerate([0,.1,.2]):
        y=xi+a*xi*(1-xi);mapping[str(a)]=y
        ax.plot(xi,y,color=COLORS[j],ls=STYLES[j],label=f'a* = {a:g}')
    ax.set(xlabel='初始材料坐标 ξ',ylabel='当前位置 r/R',xlim=(0,1),ylim=(0,1));ax.legend(loc='upper left',frameon=False)
    pd.DataFrame(mapping).to_csv(data/'mapping.csv',index=False)
    finish(fig,'process_q4_mapping','三种映射共享中心和表面端点，改变内部位置分配。','题目分析报告.md Q4映射','折线','显示g=1情形；映射是确定性假设，未被内部位移观测标定。')

    # Process 2: counts represent actual iteration frequencies, not means.
    hist=pd.read_csv(res/'问题4_迭代统计.csv');fig,ax=figax()
    ax.bar(hist.iterations.astype(str),hist.step_count,color=COLORS[0],width=.55)
    ax.set(xlabel='每个时间步的 Picard 迭代次数',ylabel='时间步数',ylim=(0,hist.step_count.max()*1.12))
    finish(fig,'process_q4_iterations','每秒耦合迭代在规定的40次上限内收敛。','results/问题4_迭代统计.csv','频数柱状图','频数统计覆盖主模型全部时间步，非采样频数。')

    # Process 3: numerical errors compared on common six-hour table locations.
    fig=refinement_figure(verification)
    finish(fig,'process_q4_refinement','时空加密误差按预先冻结的表值门槛核验。','results/问题4_数值加密.csv','点图','共同6h时刻与固定实际距离/表面值比较；终点时间差另外列在CSV中。')

    # Result 1: full threshold trajectories, semilog makes the endpoint visible.
    fig,ax=figax()
    for j,(label,s) in enumerate([('移动域主模型',base),('同物性固定半径',fixed)]):
        ax.plot(s['time_s']/3600,s['moisture'].max(axis=1),color=COLORS[j],ls=STYLES[j],label=label)
    ax.axhline(.15,color=COLORS[4],ls=':',lw=1,label='干燥阈值 0.15')
    ax.set(xlabel='时间 / h',ylabel='全域最大含水率 / (kg/kg)',yscale='log',ylim=(.12,3.0))
    ax.legend(frameon=False,loc='upper right')
    finish(fig,'result_q4_threshold','同附录4物性下，主模型与固定半径对照在不同时刻达到阈值。','results/q4_runs/main.npz; fixed.npz','半对数折线','最大值在全部计算节点上取值；精确首次跨越按1s步检测，图中为每60s记录及终点。')

    # Result 2: actual physical coordinates; gaps outside R are left white.
    times=base['time_s'];Tidx=np.unique(np.r_[np.linspace(0,len(times)-1,241).astype(int),len(times)-1])
    phys=np.linspace(0,.02,101);z=np.full((len(Tidx),len(phys)),np.nan)
    for ii,j in enumerate(Tidx):
        R=base['radius_m'][j];valid=phys<=R
        z[ii,valid]=np.interp(phys[valid],np.linspace(0,R,base['moisture'].shape[1]),base['moisture'][j])
    fig,ax=figax();mesh=ax.pcolormesh(times[Tidx]/3600,phys*100,z.T,cmap='viridis',shading='nearest',rasterized=False,vmin=0,vmax=2.55)
    mesh.set_edgecolor('face')
    ax.plot(times[Tidx]/3600,base['radius_m'][Tidx]*100,color='black',lw=.9)
    ax.set(xlabel='时间 / h',ylabel='到轴线的实际距离 / cm',ylim=(0,2))
    cb=fig.colorbar(mesh,ax=ax,pad=.03);cb.set_label('含水率 / (kg/kg)');cb.solids.set_rasterized(False)
    np.savez_compressed(data/'physical_field.npz',time_h=times[Tidx]/3600,radius_cm=phys*100,moisture=z)
    finish(fig,'result_q4_moving_field','药材内部区域随表面收缩而减小，内部含水率逐渐降低。','results/q4_plot_data/physical_field.npz','热力图','显示241个时间索引（含终点）、101个物理距离；白色区域为药材域外，非计算缺失。')

    # Result 3: paired counterfactual estimates (no fabricated uncertainty bars).
    fig,ax=figax();vals=[summary['dry_time_h'],summary['fixed_radius_dry_time_h']]
    for j,v in enumerate(vals):
        ax.plot([0,v],[j,j],color=COLORS[j],lw=1.4);ax.scatter([v],[j],color=COLORS[j],marker=['o','s'][j],s=38)
        ax.annotate(f'{v:.4f} h',(v,j),xytext=(6,0),textcoords='offset points',va='center',fontsize=9)
    ax.set_yticks([0,1],['移动域主模型','同物性固定半径']);ax.set(xlabel='干燥时间 / h',xlim=(0,max(vals)*1.22),ylim=(-.6,1.6))
    finish(fig,'result_q4_geometry_effect','仅更改是否收缩，分离附录4体系内的净几何效应。','results/问题4_结果摘要.json','配对点图','两点均来自确定性计算，所有物性、初边值与数值设置相同。')

    # Result 4: mapping uncertainty is distinct from geometric effect.
    fig,ax=figax();es=[0,summary['eta_shape_percent']['0.1'],summary['eta_shape_percent']['0.2']]
    ax.scatter(es,[0,1,2],s=40,color=COLORS[0],marker='D');ax.axvline(0,color=COLORS[4],lw=.8)
    ax.set_yticks([0,1,2],['a* = 0','a* = 0.1','a* = 0.2']);ax.set_xlabel('相对主模型的干燥时长变化 / %');ax.set_ylim(-.5,2.5)
    finish(fig,'result_q4_shape_sensitivity','相同实测外半径下，内部映射假设引起可量化的时长变化。','results/问题4_结果摘要.json','点图','三个未校准的确定性映射情景；点间差异不是置信区间。')

    # Result 5: genuine profiles at selected recorded instants.
    fig,ax=figax();target=[6*3600,24*3600,48*3600,times[-1]]
    for j,tt in enumerate(sorted(set(v for v in target if v<=times[-1]))):
        i=int(np.searchsorted(times,tt));R=base['radius_m'][i]
        ax.plot(np.linspace(0,R*100,base['moisture'].shape[1]),base['moisture'][i],color=COLORS[j],ls=STYLES[j],label=f'{tt/3600:.2f} h')
    ax.set(xlabel='到轴线的实际距离 / cm',ylabel='含水率 / (kg/kg)',xlim=(0,2),ylim=(0,2.7));ax.legend(frameon=False)
    finish(fig,'result_q4_profiles','径向梯度与表面内移共同决定固定距离处的水分变化。','results/q4_runs/main.npz','折线','各条曲线止于当时真实表面，不延长到初始2cm。')

    # Additional boundary sensitivity, with signed perturbations.
    names=['air_T_minus','air_T_plus','air_C_minus','air_C_plus','last_air'];labels=['温度 -1 SD','温度 +1 SD','空气水分 -1 SD','空气水分 +1 SD','末条边界替代']
    sub=scenarios.set_index('scenario').loc[names];fig,ax=figax()
    ax.scatter(sub.relative_to_main_percent,np.arange(5),color=COLORS[0],s=35)
    ax.axvline(0,color=COLORS[4],ls=':',lw=1);ax.set_yticks(np.arange(5),labels);ax.set(xlabel='相对主模型的时长变化 / %',ylim=(-.5,4.5))
    finish(fig,'process_q4_air_sensitivity','长期空气延拓不确定性与内部收缩假设分别评估。','results/问题4_情景汇总.csv','点图','单因素扰动，SD为91点总体标准差；不是随机置信区间。')

    (figdir/'图表契约.json').write_text(json.dumps(contracts,ensure_ascii=False,indent=2),encoding='utf-8')
    text=['# 问题四图表索引','', '仅q4范围：3张原始图、4张过程图、5张结果图。每幅均有PDF、SVG、300DPI PNG和灰度预览。','']
    for c in contracts:text += [f"## {c['name']}",c['claim'],f"图注：{c['caption']}",f"证据：{c['source']}",'']
    (figdir/'图表说明.md').write_text('\n'.join(text),encoding='utf-8')

if __name__=='__main__':
    if '--figure16-only' in sys.argv:figure16_only()
    else:main()
