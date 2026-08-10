"""Train the LSTM to convergence at both candidate learning rates.

The grid search in notebook 17 used a short budget (6 epochs, stride 20) and on
that budget lr=0.003 looked best. Notebook 20 showed the ordering reverses with a
longer budget, and that neither configuration had converged. This settles it:
denser data, more epochs, and early stopping with real patience so training stops
because the model has stopped improving rather than because the budget ran out.

Writes processed/lstm_converged.csv and plots/final_lstm_converged.png
"""
import os, time, warnings
import numpy as np, pandas as pd, torch, torch.nn as nn
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from torch.utils.data import Dataset, DataLoader, Subset
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error

warnings.filterwarnings('ignore')
ROOT = r'D:\Final year project'; PROC = os.path.join(ROOT,'processed'); PLOTS = os.path.join(ROOT,'plots')
LOG = os.path.join(ROOT,'lstm_converged_progress.txt')
def log(m):
    with open(LOG,'a') as f: f.write(f'{time.strftime("%H:%M:%S")}  {m}\n')
    print(m, flush=True)

df = pd.read_csv(os.path.join(PROC,'master_all_cities.csv'), parse_dates=['time'], low_memory=False)
df = df.sort_values(['city','time']).reset_index(drop=True)
CITIES=['Jena','London','New_York','Sydney','Tokyo']
CONT=['temperature','humidity','dew_point','precipitation','wind_speed','wind_gusts','wind_u','wind_v',
 'pressure_msl','surface_pressure','cloud_cover','cloud_cover_low','cloud_cover_mid','cloud_cover_high',
 'shortwave_radiation','direct_radiation','vapour_pressure_deficit','wet_bulb_temp','water_vapour','soil_temperature']
CYC=['hour_sin','hour_cos','month_sin','month_cos','dayofyear_sin','dayofyear_cos']
SEQ,H,TIDX=168,24,0
onehot=pd.get_dummies(df['city']).astype(float)[CITIES]
tr,va,te=[],[],[]
for c in CITIES:
    ix=np.where((df['city']==c).values)[0]; n=len(ix); a,b=int(n*.70),int(n*.85)
    tr.append(ix[:a]); va.append(ix[a:b]); te.append((c,ix[b:]))
sc=StandardScaler().fit(df.iloc[np.concatenate(tr)][CONT].values)
mk=lambda r: np.concatenate([sc.transform(df.iloc[r][CONT].values), df.iloc[r][CYC].values,
                             onehot.iloc[r].values],axis=1).astype(np.float32)
TRAIN=np.concatenate([mk(r) for r in tr]); VAL=np.concatenate([mk(r) for r in va])
TEST=[(c,mk(r)) for c,r in te]
N_IN=len(CONT)+len(CYC)+len(CITIES)

class WD(Dataset):
    def __init__(s,d): s.d=torch.FloatTensor(d)
    def __len__(s): return len(s.d)-SEQ-H+1
    def __getitem__(s,i): return s.d[i:i+SEQ], s.d[i+SEQ:i+SEQ+H,TIDX]
class Net(nn.Module):
    def __init__(s,hidden=128):
        super().__init__()
        s.l=nn.LSTM(N_IN,hidden,2,batch_first=True,dropout=0.2); s.n=nn.LayerNorm(hidden)
        s.h=nn.Sequential(nn.Linear(hidden,64),nn.ReLU(),nn.Dropout(0.2),nn.Linear(64,H))
    def forward(s,x):
        o,_=s.l(x); return s.h(s.n(o[:,-1]))

STRIDE=3; MAXEP=40; PATIENCE=6

def run(lr,label):
    tr_ds,va_ds=WD(TRAIN),WD(VAL)
    tl=DataLoader(Subset(tr_ds,range(0,len(tr_ds),STRIDE)),batch_size=256,shuffle=True,drop_last=True)
    vl=DataLoader(Subset(va_ds,range(0,len(va_ds),STRIDE)),batch_size=256)
    torch.manual_seed(42)
    net=Net(); opt=torch.optim.AdamW(net.parameters(),lr=lr,weight_decay=1e-4)
    sch=torch.optim.lr_scheduler.ReduceLROnPlateau(opt,patience=3,factor=0.5)
    lf=nn.HuberLoss(); best,bad,state,rows=1e9,0,None,[]
    log(f'{label}: {len(range(0,len(tr_ds),STRIDE))} train windows, max {MAXEP} epochs')
    for ep in range(1,MAXEP+1):
        net.train(); tot=k=0
        for xb,yb in tl:
            opt.zero_grad(); loss=lf(net(xb),yb); loss.backward()
            nn.utils.clip_grad_norm_(net.parameters(),1.0); opt.step(); tot+=loss.item(); k+=1
        net.eval(); v=m=0
        with torch.no_grad():
            for xb,yb in vl: v+=lf(net(xb),yb).item(); m+=1
        trl,vll=tot/max(k,1),v/max(m,1); sch.step(vll)
        rows.append({'config':label,'epoch':ep,'train_loss':round(trl,5),'val_loss':round(vll,5)})
        log(f'  {label} ep{ep:02d} train {trl:.4f} val {vll:.4f}')
        if vll<best-1e-5: best,bad,state=vll,0,{a:b.clone() for a,b in net.state_dict().items()}
        else:
            bad+=1
            if bad>=PATIENCE: log(f'  {label} converged at epoch {ep}'); break
    net.load_state_dict(state); net.eval()
    tm,ts=sc.mean_[TIDX],sc.scale_[TIDX]; per={}
    for c,arr in TEST:
        dl=DataLoader(WD(arr),batch_size=256); ps,as_=[],[]
        with torch.no_grad():
            for xb,yb in dl: ps.append(net(xb).numpy()); as_.append(yb.numpy())
        p=np.concatenate(ps)*ts+tm; a=np.concatenate(as_)*ts+tm
        per[c]=mean_absolute_error(a.flatten(),p.flatten())
    mae=float(np.mean(list(per.values())))
    log(f'{label}: best val {best:.5f}, test MAE {mae:.4f}, per-city {{k: round(v,3) for k,v in per.items()}}')
    return rows,mae,best,per

log('=== converged LSTM comparison started ===')
r1,m1,v1,p1 = run(0.001,'lr=0.001')
r2,m2,v2,p2 = run(0.003,'lr=0.003')

pd.DataFrame(r1+r2).to_csv(os.path.join(PROC,'lstm_converged_curves.csv'),index=False)
out=pd.DataFrame([{'learning_rate':0.001,'best_val':round(v1,5),'test_MAE':round(m1,4),**{k:round(v,3) for k,v in p1.items()}},
                  {'learning_rate':0.003,'best_val':round(v2,5),'test_MAE':round(m2,4),**{k:round(v,3) for k,v in p2.items()}}])
out.to_csv(os.path.join(PROC,'lstm_converged.csv'),index=False)
log(out.to_string(index=False))

d1,d2=pd.DataFrame(r1),pd.DataFrame(r2)
plt.figure(figsize=(9,5))
plt.plot(d1.epoch,d1.val_loss,'o-',color='tab:gray',label='lr=0.001 validation')
plt.plot(d2.epoch,d2.val_loss,'s-',color='tab:blue',label='lr=0.003 validation')
plt.plot(d1.epoch,d1.train_loss,'--',color='tab:gray',alpha=.5,label='lr=0.001 train')
plt.plot(d2.epoch,d2.train_loss,'--',color='tab:blue',alpha=.5,label='lr=0.003 train')
plt.xlabel('epoch'); plt.ylabel('Huber loss'); plt.title('LSTM trained to convergence')
plt.legend(); plt.grid(alpha=.3); plt.tight_layout()
plt.savefig(os.path.join(PLOTS,'final_lstm_converged.png'),dpi=150)
log('=== done ===')
