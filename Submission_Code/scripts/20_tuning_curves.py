"""Learning curves for the LSTM before and after tuning.

Dr Talebi asked for a direct before/after comparison of the tuning, with learning
curves if possible. This trains the original (untuned) configuration and the one
the grid search picked, under an identical protocol, and records train/validation
loss every epoch so the difference is visible rather than just asserted.

Writes: processed/tuning_curves.csv, plots/final_tuning_curves.png
"""
import os, warnings, time
import numpy as np, pandas as pd, torch, torch.nn as nn
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from torch.utils.data import Dataset, DataLoader, Subset
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error

warnings.filterwarnings('ignore')
ROOT = r'D:\Final year project'; PROC = os.path.join(ROOT,'processed'); PLOTS = os.path.join(ROOT,'plots')

df = pd.read_csv(os.path.join(PROC,'master_all_cities.csv'), parse_dates=['time'], low_memory=False)
df = df.sort_values(['city','time']).reset_index(drop=True)
CITIES = ['Jena','London','New_York','Sydney','Tokyo']
CONT = ['temperature','humidity','dew_point','precipitation','wind_speed','wind_gusts','wind_u','wind_v',
        'pressure_msl','surface_pressure','cloud_cover','cloud_cover_low','cloud_cover_mid','cloud_cover_high',
        'shortwave_radiation','direct_radiation','vapour_pressure_deficit','wet_bulb_temp','water_vapour','soil_temperature']
CYC = ['hour_sin','hour_cos','month_sin','month_cos','dayofyear_sin','dayofyear_cos']
SEQ, H, TIDX = 168, 24, 0
onehot = pd.get_dummies(df['city']).astype(float)[CITIES]

tr,va,te = [],[],[]
for c in CITIES:
    ix = np.where((df['city']==c).values)[0]; n=len(ix); a,b=int(n*.70),int(n*.85)
    tr.append(ix[:a]); va.append(ix[a:b]); te.append((c, ix[b:]))
sc = StandardScaler().fit(df.iloc[np.concatenate(tr)][CONT].values)
mk = lambda r: np.concatenate([sc.transform(df.iloc[r][CONT].values), df.iloc[r][CYC].values,
                               onehot.iloc[r].values], axis=1).astype(np.float32)
TRAIN = np.concatenate([mk(r) for r in tr]); VAL = np.concatenate([mk(r) for r in va])
TEST = [(c, mk(r)) for c,r in te]
N_IN = len(CONT)+len(CYC)+len(CITIES)

class WD(Dataset):
    def __init__(s,d): s.d=torch.FloatTensor(d)
    def __len__(s): return len(s.d)-SEQ-H+1
    def __getitem__(s,i): return s.d[i:i+SEQ], s.d[i+SEQ:i+SEQ+H, TIDX]

class Net(nn.Module):
    def __init__(s, hidden):
        super().__init__()
        s.l = nn.LSTM(N_IN, hidden, 2, batch_first=True, dropout=0.2)
        s.n = nn.LayerNorm(hidden)
        s.h = nn.Sequential(nn.Linear(hidden,64), nn.ReLU(), nn.Dropout(0.2), nn.Linear(64,H))
    def forward(s,x):
        o,_ = s.l(x); return s.h(s.n(o[:,-1]))

STRIDE, EPOCHS = 8, 12

def run(lr, hidden, label):
    tr_ds = WD(TRAIN); va_ds = WD(VAL)
    tl = DataLoader(Subset(tr_ds, range(0,len(tr_ds),STRIDE)), batch_size=256, shuffle=True, drop_last=True)
    vl = DataLoader(Subset(va_ds, range(0,len(va_ds),STRIDE)), batch_size=256)
    torch.manual_seed(42)
    net = Net(hidden); opt = torch.optim.AdamW(net.parameters(), lr=lr, weight_decay=1e-4); lf = nn.HuberLoss()
    rows, best, state = [], 1e9, None
    for ep in range(1, EPOCHS+1):
        net.train(); tot=0; k=0
        for xb,yb in tl:
            opt.zero_grad(); loss=lf(net(xb),yb); loss.backward()
            nn.utils.clip_grad_norm_(net.parameters(),1.0); opt.step()
            tot+=loss.item(); k+=1
        net.eval(); v=0; m=0
        with torch.no_grad():
            for xb,yb in vl: v+=lf(net(xb),yb).item(); m+=1
        trl, vll = tot/max(k,1), v/max(m,1)
        rows.append({'config':label,'epoch':ep,'train_loss':round(trl,5),'val_loss':round(vll,5)})
        if vll<best: best, state = vll, {kk:t.clone() for kk,t in net.state_dict().items()}
        print(f'  {label} ep{ep:02d} train {trl:.4f} val {vll:.4f}', flush=True)
    net.load_state_dict(state); net.eval()
    tm, ts = sc.mean_[TIDX], sc.scale_[TIDX]; per={}
    for c, arr in TEST:
        dl = DataLoader(WD(arr), batch_size=256); ps,as_=[],[]
        with torch.no_grad():
            for xb,yb in dl: ps.append(net(xb).numpy()); as_.append(yb.numpy())
        p=np.concatenate(ps)*ts+tm; a=np.concatenate(as_)*ts+tm
        per[c]=mean_absolute_error(a.flatten(),p.flatten())
    return rows, float(np.mean(list(per.values()))), best

print('=== untuned configuration (lr=0.001, hidden=128) ===', flush=True)
r1, t1, v1 = run(0.001, 128, 'Untuned (lr=0.001)')
print('=== tuned configuration (lr=0.003, hidden=128) ===', flush=True)
r2, t2, v2 = run(0.003, 128, 'Tuned (lr=0.003)')

pd.DataFrame(r1+r2).to_csv(os.path.join(PROC,'tuning_curves.csv'), index=False)
print()
print(f'untuned: best val {v1:.5f}  test MAE {t1:.4f}')
print(f'tuned  : best val {v2:.5f}  test MAE {t2:.4f}')
print(f'improvement: {100*(t1-t2)/t1:.1f}%')

d1, d2 = pd.DataFrame(r1), pd.DataFrame(r2)
fig, ax = plt.subplots(1, 2, figsize=(13,4.5))
ax[0].plot(d1.epoch, d1.train_loss, 'o-', color='tab:gray', label='untuned, train')
ax[0].plot(d1.epoch, d1.val_loss, 's--', color='tab:gray', label='untuned, validation')
ax[0].plot(d2.epoch, d2.train_loss, 'o-', color='tab:blue', label='tuned, train')
ax[0].plot(d2.epoch, d2.val_loss, 's--', color='tab:blue', label='tuned, validation')
ax[0].set_xlabel('epoch'); ax[0].set_ylabel('Huber loss'); ax[0].set_title('LSTM learning curves')
ax[0].legend(fontsize=8); ax[0].grid(alpha=.3)

ax[1].bar(['Untuned','Tuned'], [t1,t2], color=['tab:gray','tab:blue'], width=.5)
for i,v in enumerate([t1,t2]): ax[1].text(i, v+.005, f'{v:.3f}', ha='center')
ax[1].set_ylabel('Test MAE (C)'); ax[1].set_title('LSTM before and after tuning')
ax[1].set_ylim(0, max(t1,t2)*1.25); ax[1].grid(axis='y', alpha=.3)
plt.tight_layout(); plt.savefig(os.path.join(PLOTS,'final_tuning_curves.png'), dpi=150)
print('saved plots/final_tuning_curves.png and processed/tuning_curves.csv')
