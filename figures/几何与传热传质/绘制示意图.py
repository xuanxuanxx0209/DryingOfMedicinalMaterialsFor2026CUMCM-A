from pathlib import Path
import json
import hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Circle, Arc, Rectangle, FancyArrowPatch
from matplotlib.font_manager import FontProperties

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
FONT = FontProperties(fname='C:/Windows/Fonts/simsun.ttc')
FONT.set_math_fontfamily('stix')
plt.rcParams.update({'font.family': 'SimSun', 'mathtext.fontset':'stix',
                     'pdf.fonttype':42, 'ps.fonttype':42, 'svg.fonttype':'none',
                     'font.size':9, 'axes.unicode_minus':False})
L, R, T0, C0, h, hm = .25, .02, 28., 2.55, 25., 8e-7
assert np.isclose(R/L, .08) and np.isclose(L/(2*R), 6.25)

def draw(mono=False):
    ink='#262626'; light='#999999'
    heat=ink if mono else '#A64B36'
    mass=ink if mono else '#315B78'
    fig=plt.figure(figsize=(180/25.4,110/25.4),facecolor='white')
    ax=fig.add_axes([0,0,1,1]); ax.set(xlim=(0,180),ylim=(0,110),aspect='equal'); ax.axis('off')
    texts=[]
    def txt(x,y,s,sz=9,ha='center',color=ink,**kw):
        t=ax.text(x,y,s,fontproperties=FONT,fontsize=sz,ha=ha,va='center',color=color,**kw)
        texts.append(t); return t
    def line(x,y,**kw): ax.plot(x,y,color=kw.pop('color',ink),lw=kw.pop('lw',.8),**kw)
    def arrow(p,q,color=ink,style='-|>',ls='-',lw=1.1,ms=9):
        ax.add_patch(FancyArrowPatch(p,q,arrowstyle=style,mutation_scale=ms,
                     linewidth=lw,color=color,linestyle=ls,shrinkA=0,shrinkB=0))
    txt(43,104,'(a)  圆柱几何与径向简化',10)
    txt(132,104,'(b)  横截面与传递方向',10)
    # Cylinder side view: projected axial length / diameter is exactly 6.25.
    x0,x1,y,b,a=12,74.5,75,5,2.4
    ax.add_patch(Rectangle((x0,y-b),x1-x0,2*b,facecolor='#F3F3F3',edgecolor='none'))
    ax.add_patch(Arc((x0,y),2*a,2*b,theta1=90,theta2=270,color=ink,lw=.85))
    ax.add_patch(Arc((x0,y),2*a,2*b,theta1=-90,theta2=90,color=light,lw=.65,ls=(0,(3,3))))
    line([x0,x1],[y+b,y+b]); line([x0,x1],[y-b,y-b])
    ax.add_patch(Ellipse((x1,y),2*a,2*b,facecolor='white',edgecolor=ink,lw=.85))
    line([7,81],[y,y],ls=(0,(5,2,1,2)),lw=.65,color=light)
    txt(80,77.5,'$z$',9)
    for x in (x0,x1): line([x,x],[81.5,89],lw=.55,color=light)
    arrow((x0,87),(x1,87),style='<->',lw=.65,ms=7)
    txt(43,91,r'$L=25\,\mathrm{cm}$',9)
    arrow((x1,y),(x1,y+b),lw=.7,ms=6)
    line([76,80,80],[78,82,84],lw=.6)
    txt(80,87,r'$R=2\,\mathrm{cm}$',8,ha='left')
    # Section indicator, kept distinct from the heat/mass arrows.
    line([55,55],[67,83],ls=(0,(4,2)),lw=.65,color=light)
    txt(55,64,'横截面',8)
    txt(43,57,r'$T=T(r,t),\quad C=C(r,t)$',10)
    txt(43,50,'轴对称；忽略轴向梯度和端面传递',8.5)
    txt(43,42,'初始状态',8.5)
    txt(43,35,r'$T_0=301.15\,\mathrm{K}\ (28\,{}^{\circ}\mathrm{C})$，$C_0=2.55\,\mathrm{kg/kg}$',8.5)
    # Enlarged cross-section; rings only show geometry, never invented fields.
    cx,cy,rad=132,73,18
    ax.add_patch(Circle((cx,cy),rad,facecolor='#F7F7F7',edgecolor=ink,lw=1))
    line([cx-rad,cx+rad],[cy,cy],ls=(0,(5,2,1,2)),lw=.6,color=light)
    line([cx,cx],[cy-rad,cy+rad],ls=(0,(5,2,1,2)),lw=.6,color=light)
    ax.plot(cx,cy,'o',ms=2.6,color=ink)
    txt(cx-3,cy-3,'$O$',9)
    arrow((cx,cy),(cx+rad+6,cy),lw=.8,ms=7)
    txt(cx+rad+8,cy,'$r$',9)
    txt(cx+9,cy-3.8,'$R$',9)
    txt(cx,97,r'烘房空气：$T_a(t),\ C_a(t)$',9)
    # Heat inward on upper left, moisture outward on upper right.
    for angle in (125,165,205):
        v=np.array([np.cos(np.deg2rad(angle)),np.sin(np.deg2rad(angle))])
        arrow(np.array([cx,cy])+v*(rad+7),np.array([cx,cy])+v*(rad-6),color=heat)
    for angle in (50,20,-35):
        v=np.array([np.cos(np.deg2rad(angle)),np.sin(np.deg2rad(angle))])
        arrow(np.array([cx,cy])+v*(rad-6),np.array([cx,cy])+v*(rad+7),color=mass,ls=(0,(4,2)))
    txt(104,48,'热量传入',8.5,color=heat)
    arrow((96,53),(111,53),color=heat)
    txt(158,48,'水分逸出',8.5,color=mass)
    arrow((150,53),(165,53),color=mass,ls=(0,(4,2)))
    txt(132,39,r'轴线对称：$\left.\partial_r T\right|_0=\left.\partial_r C\right|_0=0$',9)
    # Two concise boundary equations, with signed outward-normal convention.
    line([8,172],[28,28],lw=.6,color=light)
    txt(8,23,'侧壁边界（径向向外为正）',8.5,ha='left')
    txt(8,15,r'$-k\left.\dfrac{\partial T}{\partial r}\right|_R=h[T(R,t)-T_a(t)]$',10,ha='left',color=heat)
    txt(96,15,r'$-D\left.\dfrac{\partial C}{\partial r}\right|_R=h_m[C(R,t)-C_a(t)]$',10,ha='left',color=mass)
    txt(90,4.5,'箭头示升温失水工况；横截面放大绘制，传质边界采用题设经验口径。',8)
    fig.canvas.draw()
    renderer=fig.canvas.get_renderer()
    bounds=fig.bbox
    clipped=[]
    for t in texts:
        b=t.get_window_extent(renderer)
        if b.x0<bounds.x0 or b.y0<bounds.y0 or b.x1>bounds.x1 or b.y1>bounds.y1: clipped.append(t.get_text())
    assert not clipped, clipped
    stem='几何与传热传质示意图'+('_黑白' if mono else '')
    for ext in ('pdf','svg','png'):
        fig.savefig(OUT/f'{stem}.{ext}',dpi=600,facecolor='white')
    plt.close(fig)
    return {'version':stem,'text_count':len(texts),'clipped_text':clipped}

if __name__=='__main__':
    reports=[draw(False),draw(True)]
    source=ROOT/'problem A/A题.pdf'
    report={'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
       'geometry':{'L_m':L,'R_m':R,'diameter_cm':2*R*100,'end_to_side_area_ratio':R/L},
       'initial':{'T_C':T0,'C_dry_basis_kg_kg':C0},
       'scope':'固定半径的一维径向模型；不表示问题四半径恒定',
       'direction':'外法向为正；升温时 q_out<0，失水时 J_out>0',
       'size_mm':[180,110],'png_dpi':600,'qa':reports}
    (OUT/'核对记录.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
