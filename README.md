# Power without accountability

A walled-city thought experiment in Streamlit, on synthetic data.

When power sits with one person who answers to no one, does it get used more recklessly, and who pays for it? Six hundred invented cities face a rising threat for 20 seasons under three ways of holding power: a sole ruler, an accountable leader who is replaced after harming outsiders too much, and a five-member council that needs a majority to strike.

The idea was sparked by a theme in *Attack on Titan*. Nothing here is real data, and the effect is an assumption you set with the sidebar sliders. Set both effect sliders to 0 to see the honest baseline.

## Run it

```
pip install -r requirements.txt
streamlit run app.py
```

`python simulate.py` regenerates the CSVs in `data/`.

## What's inside

- `simulate.py`: the simulation, the per-city summary and a Kaplan-Meier curve, all in plain NumPy and pandas.
- `app.py`: the Streamlit app.
- `data/`: the default synthetic dataset (seed 7).
- `.streamlit/config.toml`: light theme, usage statistics off.

Not affiliated with the creators of Attack on Titan.
