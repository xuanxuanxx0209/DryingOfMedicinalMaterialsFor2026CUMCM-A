"""Q4: material-coordinate effective diffusion; see 题目分析报告.md.

Reproduce: python -X utf8 问题4_复现.py
Inputs are read-only. Numba is optional (plain Python uses the same functions).
"""
from __future__ import annotations
import sys, json, argparse, time, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import openpyxl
from scipy.linalg import eigvalsh_tridiagonal

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'build/q4_runtime'))
try:
    from numba import njit
    ACCELERATED=True
except ImportError:
    ACCELERATED=False
    def njit(*args,**kwargs):
        return lambda f:f
import 全程干燥求解 as old

@njit(cache=True)
def geometry(x,xf,R,a):
    g=(1-R/.02)/(1-.01198/.02)
    r=R*(x+a*g*x*(1-x))
    rf=R*(xf+a*g*xf*(1-xf))
    w=(rf[1:]**2-rf[:-1]**2)/2
    geom=rf[1:-1]/(r[1:]-r[:-1])
    return r,w,geom

@njit(cache=True)
def props(c,t):
    rho=760+90*c
    cp=1850+2150*c/(1+c)
    k=.12+.20*c/(1+c)
    d=4.2e-4*np.exp(-.30/c)*np.exp(-3850/(t+273.15))
    return rho*cp,k,d

@njit(cache=True)
def linear_solve(history,b,gamma,w,geom,R,beta,ambient,dt):
    st=b*w/dt
    conduct=geom*(gamma[:-1]+gamma[1:])/2
    diag=st.copy()
    diag[:-1]+=conduct
    diag[1:]+=conduct
    diag[-1]+=R*beta
    rhs=st*history
    rhs[-1]+=R*beta*ambient
    dd=diag.copy(); yy=rhs.copy()
    for i in range(1,len(dd)):
        factor=-conduct[i-1]/dd[i-1]
        dd[i]+=factor*conduct[i-1]
        yy[i]-=factor*yy[i-1]
    u=yy.copy();u[-1]/=dd[-1]
    for i in range(len(u)-2,-1,-1):
        u[i]=(yy[i]+conduct[i]*u[i+1])/dd[i]
    residual=diag*u-rhs
    residual[:-1]-=conduct*u[1:]
    residual[1:]-=conduct*u[:-1]
    relative=np.max(np.abs(residual))/max(np.max(np.abs(rhs)),1e-30)
    return u,relative

@njit(cache=True,nogil=True)
def kernel(N,dt,end,ta,ca,rt,rv,airtime,stableT,stableC,a,fixed,stop,initT=28.,initC=2.55):
    x=np.linspace(0.,1.,N+1)
    xf=np.empty(N+2);xf[0]=0.;xf[-1]=1.;xf[1:-1]=(x[:-1]+x[1:])/2
    t=np.full(N+1,initT);c=np.full(N+1,initC);tp=t.copy();cp=c.copy()
    count=int(round(end/dt));stride=int(round(60/dt))
    capacity=count//stride+3
    times=np.zeros(capacity);radii=np.zeros(capacity)
    ts=np.zeros((capacity,N+1));cs=np.zeros((capacity,N+1))
    ts[0]=t;cs[0]=c;radii[0]=.02;rec=1
    iters=np.zeros(count,dtype=np.int16)
    # residualT,residualC,balanceC,balanceT_abs,balanceT_scaled,
    # minC,minT,maxT,max radial C increase,max(Cmax-Ccenter),minJac,
    # previous Cmax,final Cmax,drytime,max temporal Cmax increase
    stats=np.array([0.,0.,0.,0.,0.,initC,initT,initT,0.,0.,.02,initC,initC,-1.,0.])
    lastmax=initC
    for step in range(1,count+1):
        now=step*dt
        R=.02 if fixed else np.interp(now,rt,rv)
        ambT=np.interp(now,airtime,ta) if now<=airtime[-1] else stableT
        ambC=np.interp(now,airtime,ca) if now<=airtime[-1] else stableC
        r,w,geom=geometry(x,xf,R,a)
        g=(1-R/.02)/(1-.01198/.02)
        stats[10]=min(stats[10],R*(1-abs(a*g)))
        effective=dt if step==1 else 2*dt/3
        th=t.copy() if step==1 else (4*t-tp)/3
        ch=c.copy() if step==1 else (4*c-cp)/3
        tg=t.copy();cg=c.copy();converged=False
        for iteration in range(1,41):
            b,k,_=props(cg,tg)
            tn,errT=linear_solve(th,b,k,w,geom,R,25.,ambT,effective)
            _,_,d=props(cg,tn)
            cn,errC=linear_solve(ch,np.ones(N+1),d,w,geom,R,8e-7,ambC,effective)
            stats[0]=max(stats[0],errT);stats[1]=max(stats[1],errC)
            et=np.max(np.abs(tn-tg));ec=np.max(np.abs(cn-cg))
            tg=tn;cg=cn
            if et<=1e-8 and ec<=1e-10:
                converged=True;break
        if not converged:raise RuntimeError('Picard did not converge')
        if not np.all(np.isfinite(cg)) or not np.all(np.isfinite(tg)) or np.min(cg)<0:
            raise RuntimeError('invalid field')
        deltaC=(cg-ch)/effective
        lhs=np.sum(w*deltaC);flux=R*8e-7*(cg[-1]-ambC)
        # Roundoff floor only for synthetic zero-flux constant-state test.
        if max(abs(lhs),abs(flux))>1e-20:
            stats[2]=max(stats[2],abs(lhs+flux)/max(abs(lhs),abs(flux)))
        deltaT=(tg-th)/effective
        heatlhs=np.sum(b*w*deltaT);heatflux=R*25.*(tg[-1]-ambT)
        habs=abs(heatlhs+heatflux)
        hscale=np.sum(b*w*(np.abs(tg)+np.abs(th))/effective)+R*25.*(abs(tg[-1])+abs(ambT))
        stats[3]=max(stats[3],habs);stats[4]=max(stats[4],habs/max(hscale,1e-30))
        stats[5]=min(stats[5],np.min(cg));stats[6]=min(stats[6],np.min(tg));stats[7]=max(stats[7],np.max(tg))
        stats[8]=max(stats[8],np.max(cg[1:]-cg[:-1]))
        cmax=np.max(cg);stats[9]=max(stats[9],cmax-cg[0])
        stats[11]=lastmax;stats[12]=cmax;stats[14]=max(stats[14],cmax-lastmax)
        lastmax=cmax
        tp=t;t=tg;cp=c;c=cg
        iters[step-1]=iteration
        dry=stop and cmax<.15
        if step%stride==0 or dry or step==count:
            times[rec]=now;radii[rec]=R;ts[rec]=t;cs[rec]=c;rec+=1
        if dry:
            stats[13]=now;break
    if stop and stats[13]<0:raise RuntimeError('dryness not reached by horizon')
    return times[:rec],radii[:rec],ts[:rec],cs[:rec],iters[:step],stats

def input_data():
    air=old.core.read_air_boundary();rad=old.read_radius_history();ss=old.stable_air_statistics()
    assert np.all(np.isfinite(rad.radius_m))
    return air,rad,ss

def solve(*,N=320,dt=1.,a=0.,fixed=False,end=604800.,stop=True,Tshift=0.,Cshift=0.,last_air=False):
    air,rad,ss=input_data()
    st=ss['last_temperature_c'] if last_air else ss['temperature_mean_c']+Tshift
    sc=ss['last_moisture_kg_per_kg'] if last_air else ss['moisture_mean_kg_per_kg']+Cshift
    start=time.perf_counter()
    values=kernel(N,dt,end,air.temperature_c,air.moisture,rad.time_s,rad.radius_m,air.time_s,st,sc,a,fixed,stop)
    t,r,T,C,it,stats=values
    keys=['heat_linear_residual','moisture_linear_residual','moisture_balance_relative','heat_balance_absolute','heat_balance_scaled','min_moisture','min_temperature_c','max_temperature_c','max_radial_moisture_increase','max_Cmax_minus_center','min_mapping_Jacobian_m','previous_Cmax','final_Cmax','dry_time_s','max_step_Cmax_increase']
    meta=dict(zip(keys,map(float,stats)))
    meta.update(N=N,dt_s=dt,a=a,fixed=fixed,Tshift=Tshift,Cshift=Cshift,last_air=last_air,runtime_s=time.perf_counter()-start,max_picard_iterations=int(it.max()),stable_air=ss)
    meta['dry_time_h']=meta['dry_time_s']/3600
    meta['radius_end_cm']=float(r[-1]*100)
    meta['beyond_radius_observation']=bool(t[-1]>rad.time_s[-1])
    meta['final_matrix_conditions']=conditions(N,dt,r[-1],a,T[-1],C[-1])
    return dict(time_s=t,radius_m=r,temperature_c=T,moisture=C,iterations=it,meta=meta)

def conditions(N,dt,R,a,T,C):
    x=np.linspace(0,1,N+1);xf=np.r_[0,(x[:-1]+x[1:])/2,1]
    _,w,geom=geometry(x,xf,R,a);b,k,d=props(C,T)
    out={}
    for name,B,G,beta in [('heat',b,k,25.),('moisture',np.ones(N+1),d,8e-7)]:
        f=geom*(G[:-1]+G[1:])/2;diag=1.5*B*w/dt
        diag[:-1]+=f;diag[1:]+=f;diag[-1]+=R*beta
        ev=eigvalsh_tridiagonal(diag,-f)
        out[name]=float(ev[-1]/ev[0])
    return out

def sample(sol,spacing=.005):
    fixed=np.arange(0,.02-1e-10,spacing)
    c=sol['moisture'];R=sol['radius_m'];a=sol['meta']['a']
    x=np.linspace(0,1,c.shape[1]);out=np.full((len(R),len(fixed)+1),np.nan)
    for j,rad in enumerate(R):
        g=(1-rad/.02)/(1-.01198/.02);r=rad*(x+a*g*x*(1-x))
        mask=fixed<=rad+1e-12
        out[j,:len(fixed)][mask]=np.interp(fixed[mask],r,c[j])
        out[j,-1]=c[j,-1]
    return out

def save_run(sol,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(path,**{k:v for k,v in sol.items() if k!='meta'})
    path.with_suffix('.json').write_text(json.dumps(sol['meta'],indent=2,ensure_ascii=False),encoding='utf-8')

def load_run(path):
    with np.load(path) as z:out={k:z[k] for k in z.files}
    out['meta']=json.loads(path.with_suffix('.json').read_text(encoding='utf-8'))
    return out

def smoke(output):
    s=solve(N=32,dt=1,end=600,stop=False)
    ss=s['meta']['stable_air']
    ref=old.simulate_variable_model(model='q4',end_time_s=600,time_step_s=1,intervals=32,record_interval_s=60,temporal_scheme='bdf2',post_observation_temperature_c=ss['temperature_mean_c'],post_observation_moisture=ss['moisture_mean_kg_per_kg'])
    errT=float(np.max(np.abs(ref.temperature_c-s['temperature_c'])))
    errC=float(np.max(np.abs(ref.moisture-s['moisture'])))
    assert errT<1e-9 and errC<1e-10,(errT,errC)
    pert=solve(N=32,dt=1,end=1800,a=.2,stop=False)
    air,rad,_=input_data()
    const=kernel(16,1.,600.,np.full_like(air.temperature_c,28.),np.full_like(air.moisture,2.55),rad.time_s,rad.radius_m,air.time_s,28.,2.55,.2,False,False)
    constant_error=max(float(np.max(np.abs(const[2]-28))),float(np.max(np.abs(const[3]-2.55))))
    assert constant_error<1e-9
    fixed=solve(N=32,dt=1,end=1800,fixed=True,stop=False)
    assert np.all(fixed['radius_m']==.02)
    for z in [s,pert,fixed]:
        m=z['meta'];assert m['moisture_balance_relative']<1e-8 and m['min_mapping_Jacobian_m']>0
        assert max(m['heat_linear_residual'],m['moisture_linear_residual'])<1e-12
    output.parent.mkdir(parents=True,exist_ok=True)
    report={'status':'PASS','uniform_regression_temperature_error':errT,'uniform_regression_moisture_error':errC,'moving_constant_state_error':constant_error,'base':s['meta'],'shape_02':pert['meta'],'fixed':fixed['meta']}
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--smoke',action='store_true');p.add_argument('--output',default='results/P1_q4_smoke.json');args=p.parse_args()
    if args.smoke:smoke(ROOT/args.output)
    else:p.error('Use 问题4_复现.py for full computation, or --smoke')
