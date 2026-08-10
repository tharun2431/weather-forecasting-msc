# The two notebooks that cannot be re-executed

Everything else in this submission carries saved cell outputs. The two notebooks
here do not, and cannot be made to, for reasons that are specific to each. Both
say the same thing in their own first cell.

Five notebooks were originally written for Kaggle or Google Colab GPU sessions,
which are not persistent, so none of them came back with outputs. Three have
since been re-run and now live in `notebooks/` with their outputs intact:
`02_lstm_baseline.ipynb`, `11_per_city_vs_pooled_colab.ipynb` and
`15_tft_retrain_colab.ipynb`. These two are what is left.

| Notebook | Why it cannot be re-executed | Where the result is reproduced |
|---|---|---|
| `03_tft_model_kaggle.ipynb` | It evaluates a checkpoint and never trains one. That checkpoint was lost with the Kaggle session. Its code also specifies lr 0.001 while the 1.53 MAE it reported came from lr 0.0003, so retraining would not reproduce the reported figure, and loading the later tuned checkpoint would report the tuned model under an untuned heading. | Superseded by `notebooks/17_hyperparameter_search.ipynb`, which tunes every model on the same protocol |
| `10_tft_retrain_kaggle.ipynb` | 40 epochs at lr 0.0003 is roughly 18 hours, beyond any single session. lr 0.0003 is also the learning rate later identified as the cause of the TFT underperforming, so the run would only reproduce a known fault. | Superseded by `15_tft_retrain_colab.ipynb`, which uses the corrected lr 0.03 |

The trained checkpoint from `15` is included in `best_model/`, so the final TFT
result can be verified locally without a GPU. `notebooks/16_tft_evaluation.ipynb`
loads it and reproduces the reported test MAE of 1.247 from scratch.
