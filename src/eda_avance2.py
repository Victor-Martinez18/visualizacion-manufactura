"""
Avance 2 – Exploración de datos (EDA) con visualizaciones
Dataset: Manufacturing Production Data (ziya07, Kaggle)
         https://www.kaggle.com/datasets/ziya07/manufacturing-production-data

Genera las 6 figuras del Avance 2 (f1.png a f6.png) en outputs/figures/avance2/:
  Figura 1  Univariada     – Histograma del retraso en el inicio
  Figura 2  Bivariada      – Barras apiladas 100 %: máquina × estado
  Figura 3  Multivariada   – Mapa de calor: máquina × operación × % incumplimiento
  Figura 4  Temporal       – Línea diaria de % retrasadas y fallidas
  Figura 5  Incertidumbre  – Puntos con intervalo de confianza 95 % (Wilson)
  Figura 6  Distribución   – Diagramas de caja por estado de la orden
Además imprime los porcentajes, intervalos y la prueba ji cuadrada.

Requisitos:  pip install pandas numpy matplotlib scipy
Uso (desde la raíz del proyecto):  python src/eda_avance2.py
"""
import sys, os, pandas as pd, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":9,"axes.spines.top":False,"axes.spines.right":False,"axes.edgecolor":"#888","xtick.color":"#444","ytick.color":"#444","axes.labelcolor":"#333"})
# Rutas relativas a la raíz del proyecto (este script vive en src/)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCHIVO = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "raw", "hybrid_manufacturing_raw.csv")
print("Leyendo:", ARCHIVO)
d=pd.read_csv(ARCHIVO,parse_dates=['Scheduled_Start','Scheduled_End','Actual_Start','Actual_End'])
# Variables derivadas: retraso en el inicio (min) e incumplimiento (retrasada o fallida)
d['delay']=(d.Actual_Start-d.Scheduled_Start).dt.total_seconds()/60
d['nc']=d.Job_Status!='Completed'
C={'Completed':"#3A6EA5",'Delayed':"#E09A2B",'Failed':"#B8322A"}
ES={'Completed':'Completada','Delayed':'Retrasada','Failed':'Fallida'}
OUT=os.path.join(ROOT, "outputs", "figures", "avance2") + os.sep
os.makedirs(OUT, exist_ok=True)
def src(fig): fig.text(0.01,0.01,"Fuente: elaboración propia con datos de ziya07 (s.f.), Kaggle. n = 1,000 órdenes de trabajo.",fontsize=7,color="#777")
def title(ax,t,s=None):
    ax.set_title(t,loc="left",fontweight="bold",fontsize=10.5,pad=22 if s else 8)
    if s: ax.text(0,1.02,s,transform=ax.transAxes,fontsize=8.5,color="#555")
# Intervalo de confianza de Wilson para una proporción
def wilson(k,n,z=1.96):
    p=k/n; den=1+z*z/n; c=(p+z*z/(2*n))/den; h=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den; return p,c-h,c+h

# ---------- Figura 1. Univariada: histograma del retraso ----------: histograma del retraso
e=d.dropna(subset=['delay'])
fig,ax=plt.subplots(figsize=(8,4))
bins=np.arange(-5.5,31.5,1)
for st in ['Completed','Delayed']:
    ax.hist(e.delay[e.Job_Status==st],bins=bins,color=C[st],edgecolor="white",linewidth=1,label=ES[st])
ax.axvspan(5.5,9.5,color="#eee",zorder=0); ax.text(7.5,52,"Hueco:\nningún retraso\nde 6 a 9 min",ha="center",fontsize=8,color="#555")
ax.axvline(0,color="#333",lw=1,ls="--"); ax.text(0.3,74,"Hora programada",fontsize=8,color="#333")
ax.set_xlabel("Retraso en el inicio (minutos, inicio real − inicio programado)"); ax.set_ylabel("Número de órdenes")
ax.set_ylim(0,80); ax.legend(frameon=False,loc="upper right")
title(ax,"Figura 1. Distribución del retraso en el inicio de las órdenes","Solo órdenes ejecutadas (n = 871); las 129 fallidas no tienen inicio real")
src(fig); fig.tight_layout(rect=[0,0.03,1,1]); fig.savefig(OUT+"f1.png",dpi=200); plt.close()

# ---------- Figura 2. Bivariada: máquina × estado ----------: máquina x estado (100% apiladas corregida)
ct=pd.crosstab(d.Machine_ID,d.Job_Status); n=ct.sum(axis=1); pc=ct.div(n,axis=0)
pc=pc.sort_values('Completed',ascending=True)
fig,ax=plt.subplots(figsize=(8,3.8)); left=np.zeros(len(pc))
for st in ['Completed','Delayed','Failed']:
    ax.barh(range(len(pc)),pc[st],left=left,color=C[st],edgecolor="white",linewidth=2,height=0.62,label=ES[st])
    for i,(l,v) in enumerate(zip(left,pc[st])): ax.text(l+v/2,i,f"{v:.0%}",ha="center",va="center",fontsize=8.5,color="white" if st!='Delayed' else "#222")
    left+=pc[st].values
ax.set_yticks(range(len(pc))); ax.set_yticklabels([f"{m}  (n={n[m]})" for m in pc.index])
ax.set_xlim(0,1); ax.xaxis.set_major_formatter(PercentFormatter(1,decimals=0)); ax.set_xlabel("Porcentaje de órdenes de la máquina")
ax.legend(ncol=3,frameon=False,loc="lower left",bbox_to_anchor=(0,1.0),fontsize=8.5)
ax.set_title("Figura 2. Estado de las órdenes por máquina",loc="left",fontweight="bold",fontsize=10.5,pad=26)
src(fig); fig.tight_layout(rect=[0,0.03,1,1]); fig.savefig(OUT+"f2.png",dpi=200); plt.close()

# ---------- Figura 3. Multivariada: mapa de calor ----------: heatmap máquina x operación x % incumplimiento
ops={'Additive':'Aditiva','Drilling':'Taladrado','Grinding':'Rectificado','Lathe':'Torno','Milling':'Fresado'}
pv=d.pivot_table(index='Machine_ID',columns='Operation_Type',values='nc',aggfunc='mean')
nn=d.pivot_table(index='Machine_ID',columns='Operation_Type',values='nc',aggfunc='size')
fig,ax=plt.subplots(figsize=(7.6,4.3))
im=ax.imshow(pv.values,cmap="Oranges",vmin=0,vmax=0.6,aspect="auto")
for i in range(5):
    for j in range(5):
        v=pv.values[i,j]; ax.text(j,i,f"{v:.0%}\nn={nn.values[i,j]}",ha="center",va="center",fontsize=8,color="white" if v>0.42 else "#222")
ax.set_xticks(range(5)); ax.set_xticklabels([ops[c] for c in pv.columns]); ax.set_yticks(range(5)); ax.set_yticklabels(pv.index)
ax.set_xticks(np.arange(-.5,5),minor=True); ax.set_yticks(np.arange(-.5,5),minor=True); ax.grid(which="minor",color="white",lw=2); ax.tick_params(which="minor",length=0)
for s in ax.spines.values(): s.set_visible(False)
cb=fig.colorbar(im,ax=ax,shrink=.85,format=PercentFormatter(1,decimals=0)); cb.set_label("Órdenes retrasadas o fallidas"); cb.outline.set_visible(False)
ax.set_title("Figura 3. Incumplimiento por máquina y tipo de operación",loc="left",fontweight="bold",fontsize=10.5)
src(fig); fig.tight_layout(rect=[0,0.03,1,1]); fig.savefig(OUT+"f3.png",dpi=200); plt.close()

# ---------- Figura 4. Temporal: % por día ----------: % por día
d['day']=d.Scheduled_Start.dt.normalize()
g=pd.crosstab(d.day,d.Job_Status); nd=g.sum(axis=1); gp=g.div(nd,axis=0)
fig,ax=plt.subplots(figsize=(8,4))
x=np.arange(len(gp))
for st,mk in [('Delayed','o'),('Failed','s')]:
    ax.plot(x,gp[st],color=C[st],lw=2,marker=mk,ms=7,label=ES[st]+"s")
    ax.text(x[-1]+0.15,gp[st].iloc[-1],ES[st]+"s",color="#333",va="center",fontsize=8.5)
for i in [0,len(x)-1]: ax.axvspan(i-0.4,i+0.4,color="#f0f0f0",zorder=0)
ax.text(0,0.36,"Día\nparcial",ha="center",fontsize=7.5,color="#666"); ax.text(len(x)-1,0.36,"Día\nparcial",ha="center",fontsize=7.5,color="#666")
ax.set_xticks(x); ax.set_xticklabels([f"{t:%a %d}\nn={nd.iloc[i]}".replace("Sat","Sáb").replace("Sun","Dom").replace("Mon","Lun").replace("Tue","Mar").replace("Wed","Mié").replace("Thu","Jue").replace("Fri","Vie") for i,t in enumerate(gp.index)],fontsize=8)
ax.set_ylim(0,0.4); ax.yaxis.set_major_formatter(PercentFormatter(1,decimals=0)); ax.set_ylabel("Porcentaje de órdenes del día")
ax.grid(axis="y",color="#e6e6e6",lw=0.8); ax.set_axisbelow(True); ax.set_xlim(-0.5,len(x)-0.2)

ax.set_title("Figura 4. Porcentaje diario de órdenes retrasadas y fallidas (18–25 de marzo de 2023)",loc="left",fontweight="bold",fontsize=10.5)
src(fig); fig.tight_layout(rect=[0,0.03,1,1]); fig.savefig(OUT+"f4.png",dpi=200); plt.close()

# ---------- Figura 5. Incertidumbre: IC 95 % por máquina ----------: IC 95% por máquina
tot=d.nc.mean()
rows=[(m,)+wilson(g.nc.sum(),len(g))+(len(g),) for m,g in d.groupby('Machine_ID')]
rows.sort(key=lambda r:r[1])
fig,ax=plt.subplots(figsize=(8,3.8))
for i,(m,p,lo,hi,nm) in enumerate(rows):
    ax.plot([lo,hi],[i,i],color="#555",lw=2,solid_capstyle="round")
    ax.plot(p,i,"o",color="#B8322A",ms=9,mec="white",mew=1.5)
    ax.text(hi+0.006,i,f"{p:.0%}  [{lo:.0%} – {hi:.0%}]",va="center",fontsize=8,color="#333")
ax.axvline(tot,color="#888",ls="--",lw=1); ax.text(tot,len(rows)-0.45,f"Promedio general {tot:.1%}",ha="center",fontsize=8,color="#555")
ax.set_yticks(range(len(rows))); ax.set_yticklabels([f"{r[0]}  (n={r[4]})" for r in rows])
ax.set_xlim(0.2,0.5); ax.xaxis.set_major_formatter(PercentFormatter(1,decimals=0)); ax.set_xlabel("Órdenes retrasadas o fallidas (punto = proporción; línea = IC 95 % de Wilson)")
ax.set_ylim(-0.6,len(rows)-0.2)
ax.set_title("Figura 5. Incumplimiento por máquina con intervalo de confianza al 95 %",loc="left",fontweight="bold",fontsize=10.5)
src(fig); fig.tight_layout(rect=[0,0.03,1,1]); fig.savefig(OUT+"f5.png",dpi=200); plt.close()

# ---------- Figura 6. Diagramas de caja por estado ---------- variables continuas por estado
vars_=[('Machine_Availability','Disponibilidad de la máquina (%)'),('Processing_Time','Tiempo de proceso (min)'),('Energy_Consumption','Consumo de energía')]
fig,axs=plt.subplots(1,3,figsize=(9,3.6))
for ax,(v,lab) in zip(axs,vars_):
    data=[d[v][d.Job_Status==s] for s in ['Completed','Delayed','Failed']]
    bp=ax.boxplot(data,patch_artist=True,widths=0.55,medianprops=dict(color="#111",lw=1.5),flierprops=dict(marker="o",ms=3,mfc="#999",mec="none"))
    for b,s in zip(bp['boxes'],['Completed','Delayed','Failed']): b.set_facecolor(C[s]); b.set_alpha(0.85); b.set_edgecolor("white")
    ax.set_xticks([1,2,3]); ax.set_xticklabels(["Compl.","Retras.","Fallida"],fontsize=8)
    ax.set_title(lab,fontsize=9,loc="left"); ax.grid(axis="y",color="#eee"); ax.set_axisbelow(True)
    meds=[np.median(x) for x in data]; ax.text(0.02,-0.2,"Medianas: "+" / ".join(f"{m:.0f}" if v!='Energy_Consumption' else f"{m:.1f}" for m in meds),transform=ax.transAxes,fontsize=7.5,color="#444")
fig.suptitle("Figura 6. Disponibilidad, tiempo de proceso y energía según el estado de la orden",x=0.01,ha="left",fontweight="bold",fontsize=10.5)
src(fig); fig.tight_layout(rect=[0,0.04,1,0.97]); fig.savefig(OUT+"f6.png",dpi=200); plt.close()

# ---------- Resumen numérico y prueba ji cuadrada ----------
from scipy.stats import chi2_contingency
print(f"Órdenes: {len(d)} | Incumplimiento total: {tot:.1%}")
print("\nIncumplimiento por máquina con IC 95 % (Wilson):")
for m,p,lo,hi,nm in rows: print(f"  {m} (n={nm}): {p:.1%}  [{lo:.1%} – {hi:.1%}]")
for col in ['Machine_ID','Operation_Type']:
    chi2,p=chi2_contingency(pd.crosstab(d[col],d.Job_Status))[:2]
    print(f"Ji cuadrada {col} × Job_Status: chi2 = {chi2:.1f}, p = {p:.2f}")
print("\nPorcentaje por día:"); print(gp.round(3))
print(f"\nGráficas guardadas en la carpeta '{OUT}'")
