import os, warnings, numpy as np, pandas as pd, torch
import lightning.pytorch as pl
from pytorch_forecasting import TimeSeriesDataSet, TemporalFusionTransformer
from pytorch_forecasting.data import GroupNormalizer
from pytorch_forecasting.metrics import QuantileLoss
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
warnings.filterwarnings('ignore'); pl.seed_everything(42)
torch.serialization.add_safe_globals([GroupNormalizer])

ROOT = r'D:\Final year project'; PROC = os.path.join(ROOT, 'processed')
df = pd.read_csv(os.path.join(PROC, 'master_all_cities.csv'), parse_dates=['time'], low_memory=False)
df = df.sort_values(['city', 'time']).reset_index(drop=True)
# the colab run named the city 'New York'; local master has 'New_York'. match them
# so the checkpoint's category encoder recognises it.
df['city'] = df['city'].replace('New_York', 'New York')
df['time_idx'] = df.groupby('city').cumcount()
MT = df['time_idx'].max(); TRAIN_END = int(MT*0.70); VAL_END = int(MT*0.85)

# the checkpoint was trained on the A100, so load_from_checkpoint hits a CUDA
# assertion on this CPU box. load the raw checkpoint and rebuild the model by hand,
# using the checkpoint's own dataset_parameters so the encoders line up exactly.
CKPT = os.path.join(ROOT, 'best_model', 'tft_v2_best.ckpt')
raw = torch.load(CKPT, map_location='cpu', weights_only=False)
hp = raw['hyper_parameters']; dsp = hp['dataset_parameters']
print('checkpoint hparams: hidden=%s heads=%s lr=%s' % (hp.get('hidden_size'), hp.get('attention_head_size'), hp.get('learning_rate')), flush=True)

train_ds = TimeSeriesDataSet.from_parameters(dsp, df[df['time_idx'] <= TRAIN_END])
best = TemporalFusionTransformer.from_dataset(
    train_ds,
    learning_rate=hp.get('learning_rate', 0.03),
    hidden_size=hp.get('hidden_size', 32),
    attention_head_size=hp.get('attention_head_size', 4),
    dropout=hp.get('dropout', 0.2),
    hidden_continuous_size=hp.get('hidden_continuous_size', 16),
    output_size=hp.get('output_size', 7),
    loss=QuantileLoss(),
)
best.load_state_dict(raw['state_dict'])
best.eval()
print('model rebuilt and weights loaded', flush=True)

# evaluate on the TEST slice only (last 15%)
test_df = df[df['time_idx'] > (VAL_END - 168)].reset_index(drop=True)
testing = TimeSeriesDataSet.from_parameters(dsp, test_df, predict=False, stop_randomization=True)
test_loader = testing.to_dataloader(train=False, batch_size=256, num_workers=0)
print('test batches:', len(test_loader), '- predicting...', flush=True)
pred = best.predict(test_loader, return_y=True, return_x=True, mode='prediction')
p = pred.output.cpu().numpy(); a = pred.y[0].cpu().numpy()

pf, af = p.flatten(), a.flatten(); m = np.isfinite(pf) & np.isfinite(af)
mae = mean_absolute_error(af[m], pf[m]); rmse = float(np.sqrt(mean_squared_error(af[m], pf[m]))); r2 = r2_score(af[m], pf[m])
print(f'TFT v2 FINAL  MAE {mae:.4f}  RMSE {rmse:.4f}  R2 {r2:.4f}', flush=True)
print('LSTM 1.39 | old TFT 1.53 | gradient boosting 1.26', flush=True)

gi = pred.x['groups'].cpu().numpy().flatten(); clist = sorted(df['city'].unique()); rows = []
for i, city in enumerate(clist):
    mk = gi == i
    if not mk.any(): continue
    ac, pc = a[mk].flatten(), p[mk].flatten(); f = np.isfinite(ac) & np.isfinite(pc)
    rows.append({'City': city, 'MAE': round(mean_absolute_error(ac[f], pc[f]),4),
                 'RMSE': round(float(np.sqrt(mean_squared_error(ac[f], pc[f]))),4), 'R2': round(r2_score(ac[f], pc[f]),4)})
city_df = pd.DataFrame(rows); print(city_df.to_string(index=False), flush=True)
city_df.to_csv(os.path.join(PROC, 'tft_v2_final_per_city.csv'), index=False)
pd.DataFrame([{'model':'TFT-v2-final','MAE':round(mae,4),'RMSE':round(rmse,4),'R2':round(r2,4),
               'lr':round(float(hp.get('learning_rate',0.03)),4),'hidden':hp.get('hidden_size',32),'full_data':True}]).to_csv(
    os.path.join(PROC, 'tft_v2_final_results.csv'), index=False)
print('SAVED tft_v2_final_results.csv + tft_v2_final_per_city.csv', flush=True)
