"""Power without accountability: a walled-city thought experiment.

A Streamlit demo on synthetic data. Run with: streamlit run app.py
"""
import altair as alt
import pandas as pd
import streamlit as st

from simulate import GOVERNANCE, Settings, ruler_summary, simulate, survival_curve

st.set_page_config(page_title="Power without accountability", layout="wide")

COLOR = {"Sole ruler": "#C25E00", "Accountable leader": "#0072B2", "Council": "#6B5CB8"}
SHAPE = {"Sole ruler": "square", "Accountable leader": "circle", "Council": "triangle-up"}
DASH = {"Sole ruler": [1, 0], "Accountable leader": [6, 3], "Council": [2, 2]}
INK, QUIET, RULE = "#1E2A33", "#5B6770", "#D5DBDF"

color = alt.Color("governance:N", title="Who holds power", scale=alt.Scale(domain=GOVERNANCE, range=[COLOR[g] for g in GOVERNANCE]), legend=alt.Legend(orient="top"))
shape = alt.Shape("governance:N", title="Who holds power", scale=alt.Scale(domain=GOVERNANCE, range=[SHAPE[g] for g in GOVERNANCE]))
dash = alt.StrokeDash("governance:N", title="Who holds power", scale=alt.Scale(domain=GOVERNANCE, range=[DASH[g] for g in GOVERNANCE]))


def styled(chart, height=280):
    return (chart.properties(height=height)
            .configure_axis(labelColor=QUIET, titleColor=QUIET, gridColor=RULE, domainColor=RULE, tickColor=RULE, labelFontSize=12, titleFontSize=12)
            .configure_legend(labelColor=INK, titleColor=QUIET, labelFontSize=12)
            .configure_view(strokeWidth=0))


@st.cache_data(show_spinner="Simulating 600 cities…")
def run(effect, escalation, harm_limit, seed):
    s = Settings(effect=effect, escalation=escalation, harm_limit=harm_limit, seed=seed)
    df = simulate(s)
    summary = ruler_summary(df, s.rounds)
    return df, summary, survival_curve(summary)


with st.sidebar:
    st.markdown("### Your assumptions")
    st.caption("The effect is built into this synthetic data. Change it and watch the results follow. Set both to 0 to see what no effect looks like.")
    effect = st.slider("How much having no one to answer to raises the urge to strike", 0.0, 2.0, 1.0, 0.1)
    escalation = st.slider("How much each successful strike emboldens an unchecked ruler", 0.0, 0.8, 0.35, 0.05)
    harm_limit = st.slider("Harm to outsiders that gets an accountable leader replaced", 20, 150, 60, 10)
    seed = st.number_input("Random seed", 0, 9999, 7)
    st.caption("Same settings and seed always give the same cities.")

df, summary, km = run(effect, escalation, harm_limit, int(seed))

st.title("Power without accountability")
st.markdown("**A walled-city thought experiment.** When power sits with one person who answers to no one, does it get used more recklessly, and who pays for it?")
st.info("Everything here is synthetic: 600 invented cities, not real people or events. The idea was sparked by a theme in *Attack on Titan*. The effect is an assumption you control in the sidebar, so these charts show how you'd look for it, not evidence that it exists.", icon="ℹ️")

means = summary.groupby("governance")[["strike_share", "outsider_harm", "had_catastrophe"]].mean()
cols = st.columns(3)
for col, gov in zip(cols, GOVERNANCE):
    m = means.loc[gov]
    col.metric(f"{gov}: moves that were strikes", f"{m.strike_share:.0%}", help="Share of all rounds in which the city chose to strike")
    col.caption(f"Average harm to outsiders: {m.outsider_harm:.0f} · Cities with a catastrophe: {m.had_catastrophe:.0%}")

st.subheader("1. How often each city chose to strike, round by round")
st.caption("The threat outside the walls rises every round. Unchecked rulers who win early tend to strike again.")
by_round = df.assign(strike=df["choice"].eq("strike")).groupby(["governance", "round"])["strike"].mean().rename("share").reset_index()
enc = dict(x=alt.X("round:Q", title="Round", axis=alt.Axis(tickMinStep=1)), y=alt.Y("share:Q", title="Share of cities striking", axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0, 1])), color=color)
lines = alt.Chart(by_round).mark_line(strokeWidth=2.5).encode(**enc, strokeDash=dash)
pts = alt.Chart(by_round).mark_point(filled=True, size=50, opacity=1).encode(**enc, shape=shape, tooltip=["governance:N", "round:Q", alt.Tooltip("share:Q", format=".0%")])
st.altair_chart(styled(alt.layer(lines, pts)), width="stretch", theme=None)

left, right = st.columns(2)
with left:
    st.subheader("2. Who pays")
    st.caption("Total harm to people outside the walls, one dot per city. The dark tick is the median.")
    dots = alt.Chart(summary).mark_point(filled=True, size=35, opacity=0.55).encode(
        y=alt.Y("governance:N", title=None, sort=GOVERNANCE), x=alt.X("outsider_harm:Q", title="Harm to outsiders over 20 rounds"),
        yOffset=alt.YOffset("jit:Q"), color=alt.Color("governance:N", scale=alt.Scale(domain=GOVERNANCE, range=[COLOR[g] for g in GOVERNANCE]), legend=None),
        shape=alt.Shape("governance:N", scale=alt.Scale(domain=GOVERNANCE, range=[SHAPE[g] for g in GOVERNANCE]), legend=None),
        tooltip=["ruler:N", "governance:N", alt.Tooltip("outsider_harm:Q", format=".0f")],
    ).transform_calculate(jit="(random() - 0.5) * 30")
    med = alt.Chart(summary).mark_tick(color=INK, thickness=3, size=40).encode(y=alt.Y("governance:N", sort=GOVERNANCE), x="median(outsider_harm):Q", tooltip=[alt.Tooltip("median(outsider_harm):Q", title="median", format=".0f")])
    st.altair_chart(styled(alt.layer(dots, med), 260), width="stretch", theme=None)
with right:
    st.subheader("3. How long until disaster")
    st.caption("Share of cities that haven't suffered a catastrophe yet. Cities that never did stay in to the end, as survival analysis does.")
    kenc = dict(x=alt.X("round:Q", title="Round"), y=alt.Y("share_without_catastrophe:Q", title="Share with no catastrophe yet", axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0, 1])), color=color)
    step = alt.Chart(km).mark_line(interpolate="step-after", strokeWidth=2.5).encode(**kenc, strokeDash=dash)
    kpts = alt.Chart(km).mark_point(filled=True, size=30, opacity=1).encode(**kenc, shape=shape, tooltip=["governance:N", "round:Q", alt.Tooltip("share_without_catastrophe:Q", format=".0%")])
    st.altair_chart(styled(alt.layer(step, kpts), 260), width="stretch", theme=None)

st.subheader("4. One city's story")
c1, c2 = st.columns([1, 3])
with c1:
    gov = st.selectbox("Who holds power", GOVERNANCE)
    pool = summary[summary["governance"] == gov].sort_values("outsider_harm", ascending=False)
    pick = st.selectbox("City", pool["ruler"], format_func=lambda r: f"{r} · harm {pool.set_index('ruler').loc[r, 'outsider_harm']:.0f}")
    row = pool.set_index("ruler").loc[pick]
    st.caption(f"Struck in {row.strike_share:.0%} of rounds. " + ("Leader replaced for harming outsiders. " if row.replaced else "") + (f"First catastrophe in round {int(row.first_catastrophe)}." if row.had_catastrophe else "No catastrophe."))
with c2:
    one = df[df["ruler"] == pick]
    base = alt.Chart(one).encode(x=alt.X("round:Q", title="Round", axis=alt.Axis(tickMinStep=1)))
    safety = base.mark_line(color=COLOR[gov], strokeWidth=2.5).encode(y=alt.Y("city_safety:Q", title="City safety", scale=alt.Scale(domain=[0, 100])))
    marks = base.mark_point(size=110, filled=True, opacity=1).encode(
        y="city_safety:Q",
        shape=alt.Shape("choice:N", title="Move", scale=alt.Scale(domain=["fortify", "negotiate", "strike"], range=["circle", "diamond", "triangle-up"])),
        color=alt.Color("choice:N", title="Move", scale=alt.Scale(domain=["fortify", "negotiate", "strike"], range=["#9AA7B0", "#5B6770", COLOR[gov]])),
        tooltip=["round:Q", "choice:N", "city_safety:Q", "outsider_harm:Q", "catastrophe:N"])
    st.altair_chart(styled(alt.layer(safety, marks), 240), width="stretch", theme=None)

with st.expander("How the simulation works"):
    st.markdown("""
Each round the threat outside the walls grows, and the city picks one move:

- **Fortify:** a small, sure gain in safety.
- **Negotiate:** a coin flip between a small gain and a small loss.
- **Strike:** usually a big gain, sometimes a catastrophe, and it always harms people outside the walls.

Three ways of holding power:

- **Sole ruler:** one person decides and answers to no one. The sidebar's first slider raises their urge to strike; the second makes each win embolden them further.
- **Accountable leader:** one person decides, but is replaced once their harm to outsiders passes a limit.
- **Council:** five members vote, and a strike needs three of them.

With both effect sliders at 0, the sole ruler and the accountable leader behave almost the same, and the council differs only because a majority vote is harder to win. That's the honest baseline: any gap you see beyond it is the assumption you set, not a discovery.
""")

with st.expander("The data"):
    st.dataframe(summary.round(2), hide_index=True, width="stretch")
    st.download_button("Download per-city data (CSV)", summary.to_csv(index=False), "walled_city_rulers.csv", "text/csv")
    st.download_button("Download round-by-round data (CSV)", df.to_csv(index=False), "walled_city_rounds.csv", "text/csv")

st.caption("Synthetic data · built with Streamlit · not affiliated with the creators of Attack on Titan")
