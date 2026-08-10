"""Full-data TFT retrain on local CPU (the LR-fix version). Runs unattended.
Checkpoints the best model every epoch to models/tft_v2_full_best.ckpt, so even
if it does not finish we can evaluate whatever it reached. Writes progress to
tft_full_progress.txt and final metrics to processed/tft_v2_final_results.csv.
"""
import os, warnings, time, numpy as np, pandas as pd, torch
import lightning.pytorch as pl
from lightning.pytorch.callbacks import EarlyStopping, ModelCheckpoint, Callback
from pytorch_forecasting import TimeSeriesDataSet, TemporalFusionTransformer
from pytorch_forecasting.data import GroupNormalizer
from pytorch_forecasting.metrics import QuantileLoss
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
warnings.filterwarnings('ignore'); torch.serialization.add_safe_globals([GroupNormalizer]); pl.seed_everything(42)

ROOT = r'D:\Final year project'; PROC = os.path.join(ROOT, 'processed'); MODELS = os.path.join(ROOT, 'models')
os.makedirs(MODELS, exist_ok=True)
PROG = os.path.join(ROOT, 'tft_full_progress.txt')
def log(m):
    with open(PROG, 'a') as f:
        f.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")}  {m}\n')
    print(m, flush=True)

log('=== full-data local TFT retrain started ===')

df = pd.read_csv(os.path.join(PROC, 'master_all_cities.csv'), parse_dates=['time'], low_memory=False)
df = df.sort_values(['city', 'time']).reset_index(drop=True); df['time_idx'] = df.groupby('city').cumcount()
kn = ['time_idx','hour_sin','hour_cos','month_sin','month_cos','dayofyear_sin','dayofyear_cos']
cu = ['temperature','humidity','dew_point','precipitation','rain','wind_speed','wind_direction','wind_gusts',
      'wind_u','wind_v','pressure_msl','surface_pressure','cloud_cover','cloud_cover_low','cloud_cover_mid',
      'cloud_cover_high','shortwave_radiation','direct_radiation','vapour_pressure_deficit','wet_bulb_temp',
      'water_vapour','soil_temperature']
cu = [c for c in cu if c in df.columns]
MT = df['time_idx'].max(); TRAIN_END = int(MT*0.70); VAL_END = int(MT*0.85); ENC, DEC = 168, 24

training = TimeSeriesDataSet(
    df[df['time_idx'] <= TRAIN_END], time_idx='time_idx', target='temperature', group_ids=['city'],
    min_encoder_length=ENC//2, max_encoder_length=ENC, min_prediction_length=1, max_prediction_length=DEC,
    static_categoricals=['city'], static_reals=['lat','lon'],
    time_varying_known_reals=kn, time_varying_unknown_reals=cu,
    target_normalizer=GroupNormalizer(groups=['city']),
    add_relative_time_idx=True, add_target_scales=True, add_encoder_length=True, allow_missing_timesteps=True)
validation = TimeSeriesDataSet.from_dataset(training, df[df['time_idx'] <= VAL_END], predict=False, stop_randomization=True)
train_loader = training.to_dataloader(train=True, batch_size=128, num_workers=0)
val_loader = validation.to_dataloader(train=False, batch_size=128, num_workers=0)
log(f'full data. train batches {len(train_loader)} (expect ~2.5h/epoch on CPU)')

model = TemporalFusionTransformer.from_dataset(
    training, learning_rate=0.03, hidden_size=64, attention_head_size=4, dropout=0.2,
    hidden_continuous_size=32, output_size=7, loss=QuantileLoss(), optimizer='adamw', reduce_on_plateau_patience=3)

class EpochLog(Callback):
    def on_validation_epoch_end(self, trainer, pl_module):
        vl = trainer.callback_metrics.get('val_loss')
        log(f'epoch {trainer.current_epoch} done. val_loss={float(vl):.4f}' if vl is not None else f'epoch {trainer.current_epoch} done')

ckpt = ModelCheckpoint(dirpath=MODELS, filename='tft_v2_full_best', monitor='val_loss', mode='min', save_top_k=1)
early = EarlyStopping(monitor='val_loss', patience=5, mode='min', min_delta=1e-4)
trainer = pl.Trainer(max_epochs=20, accelerator='cpu', gradient_clip_val=0.1,
                     callbacks=[early, ckpt, EpochLog()], enable_progress_bar=False, log_every_n_steps=100)
try:
    trainer.fit(model, train_dataloaders=train_loader, val_dataloaders=val_loader)
    log('training finished. best ckpt: ' + str(ckpt.best_model_path))
except Exception as e:
    log('training stopped early with: ' + repr(e)[:200])

# evaluate whatever best checkpoint exists, on the TEST SLICE (memory safe)
cpath = ckpt.best_model_path or os.path.join(MODELS, 'tft_v2_full_best.ckpt')
if os.path.exists(cpath):
    log('evaluating ' + cpath)
    best = TemporalFusionTransformer.load_from_checkpoint(cpath, map_location='cpu'); best.eval()
    test_df = df[df['time_idx'] > (VAL_END - ENC)].reset_index(drop=True)
    testing = TimeSeriesDataSet.from_dataset(training, test_df, predict=False, stop_randomization=True)
    tl = testing.to_dataloader(train=False, batch_size=256, num_workers=0)
    pr = best.predict(tl, return_y=True, return_x=True, mode='prediction')
    p = pr.output.cpu().numpy(); a = pr.y[0].cpu().numpy()
    pf, af = p.flatten(), a.flatten(); m = np.isfinite(pf) & np.isfinite(af)
    mae = mean_absolute_error(af[m], pf[m]); rmse = float(np.sqrt(mean_squared_error(af[m], pf[m]))); r2 = r2_score(af[m], pf[m])
    log(f'RESULT  MAE {mae:.4f}  RMSE {rmse:.4f}  R2 {r2:.4f}')
    gi = pr.x['groups'].cpu().numpy().flatten(); clist = sorted(df['city'].unique()); rows = []
    for i, c in enumerate(clist):
        mk = gi == i
        if not mk.any(): continue
        ac, pc = a[mk].flatten(), p[mk].flatten(); ff = np.isfinite(ac) & np.isfinite(pc)
        rows.append({'City': c, 'MAE': round(mean_absolute_error(ac[ff], pc[ff]),4),
                     'RMSE': round(float(np.sqrt(mean_squared_error(ac[ff], pc[ff]))),4), 'R2': round(r2_score(ac[ff], pc[ff]),4)})
    pd.DataFrame(rows).to_csv(os.path.join(PROC, 'tft_v2_final_per_city.csv'), index=False)
    pd.DataFrame([{'model':'TFT-v2-full-local','MAE':round(mae,4),'RMSE':round(rmse,4),'R2':round(r2,4),
                   'lr':0.03,'hidden':64,'full_data':True}]).to_csv(os.path.join(PROC, 'tft_v2_final_results.csv'), index=False)
    log('SAVED processed/tft_v2_final_results.csv')
else:
    log('no checkpoint found to evaluate')
log('=== done ===')
