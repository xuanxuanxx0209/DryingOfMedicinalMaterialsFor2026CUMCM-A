"""Reproduce four focused paper figures from existing, read-only solver outputs."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(Path(r'C:\Users\23572\.codex\skills\math-modeling\tools\figure\scripts')))
from setup_style import setup_style
from export_figure import export_figure
from visual_qa import audit_layout, render_preview

OUT = ROOT / 'figures/paper_review'
QA = ROOT / 'build/figure_review'
OUT.mkdir(exist_ok=True)
QA.mkdir(exist_ok=True)
setup_style(journal='general', lang='zh', serif_for_zh=True)
plt.rcParams.update({'font.size':9, 'axes.labelsize':9, 'axes.titlesize':9,
                     'xtick.labelsize':8, 'ytick.labelsize':8, 'legend.fontsize':8,
                     'pdf.fonttype':42, 'svg.fonttype':'none', 'axes.unicode_minus':False})
BLUE, ORANGE, GREEN = '#0072B2', '#D55E00', '#009E73'
contracts=[]

def finish(fig, name, claim, sources, caption):
    for ax in fig.axes:
        ax.spines[['top','right']].set_visible(False)
    render_preview(fig, str(QA / (name+'.png')), dpi=170)
    fig.canvas.draw()  # Restore renderer at figure DPI after the preview save.
    issues=audit_layout(fig)
    if any(level=='FAIL' for level, _ in issues):
        raise RuntimeError(issues)
    print(name, issues)
    export_figure(fig, str(OUT/name), formats=['pdf','svg','png'], dpi=300,
                  size_inches=tuple(fig.get_size_inches()), grayscale_preview=True)
    gp=OUT/(name+'_grayscale.png')
    with Image.open(gp) as im:
        gray=im.copy()
    gray.save(gp,dpi=(300,300))
    contracts.append({'name':name,'claim':claim,'sources':[
        {'path':s,'sha256':hashlib.sha256((ROOT/s).read_bytes()).hexdigest()} for s in sources],
        'caption':caption,'backend':'Python','layout':'quantitative panels',
        'size_inches':list(fig.get_size_inches()),'dpi':300,'qa':issues,
        'scope':'deterministic simulation outputs; no inferential confidence interval'})
    plt.close(fig)

# Q2: the two differences have different units and therefore separate axes.
t=pd.read_excel(ROOT/'results/result2.xlsx',sheet_name='温度',header=0)
c=pd.read_excel(ROOT/'results/result2.xlsx',sheet_name='水分浓度',header=0)
assert t.shape==c.shape==(10800,22)
assert np.array_equal(t.iloc[:,0],c.iloc[:,0])
assert t.iloc[0,0]==1 and t.iloc[-1,0]==10800
assert float(t.columns[1])==0 and float(t.columns[-1])==2
assert np.isfinite(t.to_numpy(float)).all() and np.isfinite(c.to_numpy(float)).all()
hours=t.iloc[:,0].to_numpy(float)/3600
dt=t.iloc[:,-1].to_numpy(float)-t.iloc[:,1].to_numpy(float)
dc=c.iloc[:,1].to_numpy(float)-c.iloc[:,-1].to_numpy(float)
assert abs(dt[-1]-.1169)<1e-9 and abs(dc[-1]-.7581)<1e-9
pd.DataFrame({'time_h':hours,'surface_minus_center_T_C':dt,'center_minus_surface_C_kg_kg':dc}).to_csv(QA/'q2_gap_data.csv',index=False)
fig,axs=plt.subplots(2,1,figsize=(5.8,3.3),sharex=True,layout='constrained')
for ax,v,color,style,marker,label,title in [
    (axs[0],dt,ORANGE,'-','o','表面－中心温差 / ℃','a  径向温差先增大后减小'),
    (axs[1],dc,BLUE,'--','s','中心－表面含水率差 / (kg/kg)','b  含水率差在 3 h 时仍然存在')]:
    ax.plot(hours,v,color=color,ls=style,lw=1.15)
    ii=np.searchsorted(hours,np.arange(.5,3.01,.5))
    ax.plot(hours[ii],v[ii],ls='none',marker=marker,ms=3.5,color=color)
    ax.set(ylabel=label,xlim=(0,3.1),ylim=(0,float(v.max())*1.22))
    ax.set_title(title,loc='left')
    unit='℃' if ax is axs[0] else 'kg/kg'
    ax.annotate(f'{v[-1]:.4f} {unit}',(3,v[-1]),xytext=(-6,14),textcoords='offset points',ha='right',fontsize=9)
axs[1].set_xlabel('时间 / h')
finish(fig,'result_q2_gap_review','温度场先趋于均匀，水分梯度持续存在。',
       ['results/result2.xlsx'],'全部10800条秒级输出；符号标注每0.5h的报告时刻；差值取自四位小数结果表。')

# Q2: preserve the original fields, colors and display sampling, but remove PDF mesh seams.
for frame,name,label,cmap in [
    (t,'result_q2_temperature_review','温度 / ℃','inferno'),
    (c,'result_q2_moisture_review','含水率 / (kg/kg)','cividis_r')]:
    idx=np.unique(np.r_[np.arange(0,len(frame),30),len(frame)-1])
    radii=np.array([float(x) for x in frame.columns[1:]])
    fig,ax=plt.subplots(figsize=(5.8,3.0),layout='constrained')
    mesh=ax.pcolormesh(hours[idx],radii,frame.iloc[idx,1:].to_numpy(float).T,
                       shading='auto',cmap=cmap,rasterized=False)
    mesh.set_edgecolor('face')
    ax.set(xlabel='时间 / h',ylabel='到轴线的实际距离 / cm',xlim=(0,3),ylim=(0,2))
    bar=fig.colorbar(mesh,ax=ax,pad=.025)
    bar.set_label(label)
    bar.solids.set_edgecolor('face')
    bar.solids.set_rasterized(False)
    finish(fig,name,'保留原径向场信息，修复矢量网格在PDF渲染时的白色细缝。',
           ['results/result2.xlsx'],'沿用原图每30条秒级输出显示一条并追加末条的规则；21个输出半径均保留；网格边缘填同色，不改变数值。')

# Q3: preserve the full trajectory and show actual saved records without invented one-second points.
p=pd.read_csv(ROOT/'results/问题3_关键过程.csv')
assert len(p)==3447 and p.time_s.is_monotonic_increasing
assert not p.isna().any().any()
last=p.tail(2); end=float(last.time_s.iloc[-1]); excess=(last.maximum_moisture-.15)*1e6
assert list(last.time_s)==[206700,206756] and excess.iloc[0]>0>excess.iloc[-1]
fig,axs=plt.subplots(1,2,figsize=(5.8,2.8),layout='constrained',width_ratios=[1.15,1])
ax=axs[0]
ax.plot(p.time_h,p.maximum_moisture,color=BLUE,lw=1.25)
ax.axhline(.15,color=ORANGE,ls='--',lw=.9)
ax.plot(end/3600,p.maximum_moisture.iloc[-1],'o',ms=4,color=BLUE)
ax.annotate(f'{end/3600:.4f} h',(end/3600,.15),xytext=(-5,32),textcoords='offset points',ha='right',arrowprops={'arrowstyle':'-','lw':.6})
ax.text(.97,.89,'阈值 0.15 kg/kg',ha='right',transform=ax.transAxes,color=ORANGE)
ax.set(xlabel='时间 / h',ylabel='全域最大含水率 / (kg/kg)',xlim=(0,60),ylim=(0,2.7))
ax.set_title('a  全程干燥轨迹',loc='left')
ax=axs[1]
for x,y,marker,color in zip(last.time_s-end,excess,['s','o'],[ORANGE,BLUE]):
    ax.scatter(x,y,s=26,marker=marker,color=color,zorder=3)
ax.axhline(0,color='#555555',ls='--',lw=.8)
ax.set(xlabel='相对终点时间 / s',ylabel=r'阈值偏差 / ($10^{-6}$ kg/kg)',xlim=(-70,12),ylim=(-4,21),xticks=[-60,-40,-20,0])
ax.set_title('b  已保存记录的阈值偏差',loc='left')
ax.annotate(f'前一常规记录\n+{excess.iloc[0]:.4f}',(-56,excess.iloc[0]),xytext=(7,-3),textcoords='offset points',va='top',fontsize=8)
ax.annotate(f'终点记录\n{excess.iloc[-1]:.4f}',(0,excess.iloc[-1]),xytext=(-10,24),textcoords='offset points',ha='right',fontsize=8,arrowprops={'arrowstyle':'-','lw':.6})
finish(fig,'result_q3_threshold_review','终点已保存值严格低于阈值，首次时刻由原求解器逐秒检测。',
       ['results/问题3_关键过程.csv','results/问题3_结果摘要.json'],
       '左图全程；右图仅前一60s常规记录及追加终点，没有逐秒补点、插值连线或重新估计交点。')

# Q4: explain the same deterministic mapping family alongside its endpoint effect.
s=json.loads((ROOT/'results/问题4_结果摘要.json').read_text(encoding='utf-8'))
r=pd.read_csv(ROOT/'results/q4_plot_data/radius.csv')
g=(1-s['radius_end_cm']/r.radius_cm.iloc[0])/(1-r.radius_cm.iloc[-1]/r.radius_cm.iloc[0])
xi=np.linspace(0,1,201)
fig,axs=plt.subplots(1,2,figsize=(5.8,2.65),layout='constrained')
for a,col,ls in [(0,BLUE,'-'),(.1,ORANGE,'--'),(.2,GREEN,'-.')]:
    axs[0].plot(xi,a*g*xi*(1-xi),color=col,ls=ls,lw=1.2,label=fr'$a_*={a:g}$')
axs[0].set(xlabel=r'初始材料坐标 $\xi$',ylabel=r'映射偏离 $r/R-\xi$',xlim=(0,1),ylim=(-.004,.075))
axs[0].set_title('a  主模型终点时刻的映射扰动',loc='left')
axs[0].legend(frameon=False,loc='upper center',ncol=3,fontsize=7,handlelength=1.6,columnspacing=.8)
values=[0,s['eta_shape_percent']['0.1'],s['eta_shape_percent']['0.2']]
for j,(v,col,marker) in enumerate(zip(values,[BLUE,ORANGE,GREEN],['o','s','D'])):
    axs[1].scatter(v,j,color=col,marker=marker,s=26,zorder=3)
    axs[1].annotate(f'{v:.4f}%',(v,j),xytext=(6,0),textcoords='offset points',va='center',fontsize=8)
axs[1].axvline(0,color='#777777',lw=.7)
axs[1].set(yticks=[0,1,2],yticklabels=[r'$a_*=0$',r'$a_*=0.1$',r'$a_*=0.2$'],
           xlabel='相对主模型的时长变化 / %',xlim=(-.03,.43),ylim=(-.45,2.45))
axs[1].set_title('b  同一外半径下的终点变化',loc='left')
pd.DataFrame({'xi':xi,**{f'a_{a}':a*g*xi*(1-xi) for a in [0,.1,.2]}}).to_csv(QA/'q4_mapping_data.csv',index=False)
finish(fig,'result_q4_shape_review','相同外半径下的内部映射扰动对应所检验情景中至多0.3143%的时长变化。',
       ['results/问题4_结果摘要.json','results/q4_plot_data/radius.csv','results/问题4_情景汇总.csv'],
       f'左幅按主模型终点t=51.0775h计算，g={g:.10f}，绘制的是假设映射而非实测位移；右幅为确定性情景，无置信区间。')

# Q4: preserve the physically matched counterfactual and label actual endpoint times.
fig,ax=plt.subplots(figsize=(5.8,2.85),layout='constrained')
for key,label,col,ls,offset in [
    ('main','收缩主模型',BLUE,'-',(-14,27)),
    ('fixed','同物性固定半径',ORANGE,'--',(-7,45))]:
    with np.load(ROOT/f'results/q4_runs/{key}.npz') as z:
        tt=z['time_s']/3600; mm=z['moisture'].max(axis=1)
    ax.plot(tt,mm,color=col,ls=ls,lw=1.25,label=label)
    ax.plot(tt[-1],mm[-1],marker='o' if key=='main' else 's',color=col,ms=4)
    ax.annotate(f'{tt[-1]:.4f} h',(tt[-1],mm[-1]),xytext=offset,textcoords='offset points',ha='right',color=col,fontsize=9,arrowprops={'arrowstyle':'-','lw':.7,'color':col})
ax.axhline(.15,color='#777777',ls=':',lw=1,label='干燥阈值 0.15 kg/kg')
ax.set(xlabel='时间 / h',ylabel='全域最大含水率 / (kg/kg)',yscale='log',ylim=(.12,3),xlim=(0,140))
ax.legend(frameon=False,loc='upper right')
finish(fig,'result_q4_threshold_review','同附录四物性的固定半径对照分离净几何效应。',
       ['results/q4_runs/main.npz','results/q4_runs/fixed.npz'],
       '全部60s记录及追加终点；终点时间直接读实际求解记录，半对数纵轴。')

(QA/'figure_contracts.json').write_text(json.dumps(contracts,ensure_ascii=False,indent=2),encoding='utf-8')
print('Six focused figures generated; original figures and solver outputs unchanged.')
