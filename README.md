# DeepWeather

Multi-city weather forecasting that runs a neural network in your browser.

**Live:** https://tharun2431.github.io/weather-forecasting-msc/

Pick one of five cities and it produces a 24-hour temperature forecast, with a
calibrated uncertainty band around it. The model runs on your device. Nothing is
sent to a server, there is no account, and once the page has loaded it works
offline.

Built as the artefact for an MSc Data Science project at the University of
Roehampton on multi-city temperature forecasting.

## What it does

- 24-hour hourly temperature forecast for Jena, London, New York, Sydney and Tokyo
- every forecast comes with a conformal prediction interval, so you can see how
  much to trust it rather than just a line on a chart
- a five-city comparison view, since the whole point of the project was that
  these five cities behave very differently on the same day
- climate range and background for why those five were chosen
- installable as a PWA and works offline after the first load

## How it works

The forecasting model is an LSTM trained in PyTorch on ten years of hourly
records, then exported to ONNX. In the browser it runs through ONNX Runtime Web,
which executes it via WebAssembly on the client device.

Live conditions come from the Open-Meteo forecast API. The derived features are
recomputed in JavaScript to match the training pipeline exactly, which is the
fiddly part: the thermodynamic terms, the cyclical hour and month encodings and
the standardisation all have to agree with what the model saw during training, or
it quietly receives inputs from the wrong distribution and the forecast degrades
without any obvious error. The fitted means and standard deviations are exported
alongside the model in `scaler.json` (14 features) so the two stay in step.

The uncertainty band is a split conformal prediction interval calibrated per
forecast horizon rather than globally. A single global interval looks fine on
average but drifts badly across the horizon, over-covering at hour 1 and
under-covering at hour 24. Calibrating each horizon separately holds coverage at
roughly 90 per cent all the way out.

## Files

| File | What it is |
|---|---|
| `index.html` | the page |
| `app.js` | fetches conditions, builds features, runs inference, draws the charts |
| `styles.css` | styling |
| `lstm_model.onnx` | the trained model, about 900 KB |
| `scaler.json` | fitted means and scales for the 14 input features |
| `sw.js` | service worker, caches assets so it runs offline |
| `manifest.json` | PWA manifest |

## Running it locally

No build step, no dependencies. It just needs to be served over HTTP rather than
opened as a file, because the service worker and the ONNX fetch will not work
from `file://`.

```
python -m http.server 8000
```

Then open http://localhost:8000

## Model results

Trained and evaluated on hourly records from the Open-Meteo historical API,
derived from ERA5 reanalysis, covering 2000 to 2009 for the five cities. That is
87,672 records per city and 438,360 in total, split chronologically 70/15/15 so
the model is never validated or tested on anything earlier than what it trained
on.

Test set mean absolute error at the 24-hour horizon, in degrees Celsius:

| Model | MAE |
|---|---|
| Temporal Fusion Transformer | 1.247 |
| Gradient boosting | 1.263 |
| LSTM (the one deployed here) | 1.266 |
| Linear regression | 1.575 |
| Seasonal naive | 2.091 |
| Climatology | 2.470 |
| Persistence | 2.935 |

The three learned models finish within 0.02 degrees of each other once each one
is given an equivalent hyperparameter search. The LSTM is deployed here rather
than the transformer because it is small enough to sit comfortably in a browser
and there is no meaningful accuracy difference between them.

Conformal intervals hold between 90 and 93 per cent empirical coverage at every
one of the 24 horizons, widening from about plus or minus 1.26 degrees at one
hour ahead to plus or minus 4.81 degrees at twenty-four.

## Dissertation code

The research code behind this artefact is in [`Submission_Code/`](Submission_Code/).
It is the code submission for the MSc dissertation and the notebooks are stored with
their cell outputs intact, so the results can be read without re-running anything.

| Folder | What is in it |
|---|---|
| `notebooks/` | 14 Jupyter notebooks, all executed, covering exploration, baselines, the deep models, the hyperparameter search, conformal prediction and explainability |
| `scripts/` | 4 supporting scripts, including the checkpoint evaluation and the converged LSTM comparison |
| `results/` | every results CSV the report's tables are built from |
| `figures/` | the figures used in the report |
| `best_model/` | the trained Temporal Fusion Transformer checkpoint, so `16_tft_evaluation.ipynb` reproduces the reported 1.247 without a GPU |
| `not_executed_remote/` | 2 notebooks that cannot be re-run, each explaining why in its own first cell |

`Submission_Code/README.md` describes what each notebook does and which result file
supports each claim in the report.

## Data

The full dataset is mirrored at
[kaggle.com/datasets/tharun2431/multi-city-weather-2000-2009](https://www.kaggle.com/datasets/tharun2431/multi-city-weather-2000-2009).
It was retrieved from the Open-Meteo historical API, described under Data and
attribution below.

## Data and attribution

Weather data from the [Open-Meteo](https://open-meteo.com/) API, derived from
ERA5 reanalysis (Hersbach et al., 2020). Open-Meteo permits free use for research.
The data describes atmospheric conditions and contains no personal information.

## Notes

This is a research demonstration, not an operational forecasting system. It
covers five cities over a fixed historical period, and the accuracy figures above
apply to that setting only. Do not use it for anything that matters.
