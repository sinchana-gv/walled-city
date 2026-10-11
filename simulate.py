"""Synthetic data for "Power without accountability", a fan-inspired thought experiment.

A walled city faces a rising threat for 20 seasons. Each season its ruler picks one
of three moves:

  fortify    safe and slow: small, sure gain in safety
  negotiate  a gamble with low stakes
  strike     a big gamble: often a large gain, sometimes a catastrophe, and it
             always harms people outside the walls

Three ways of governing:

  Sole ruler          one person decides and answers to no one
  Accountable leader  one person decides, but is replaced if harm to outsiders
                      passes a limit
  Council             five members vote; a strike needs a majority

Everything here is invented. The "power without accountability" effect is BUILT IN
through `effect` (how much the lack of checks raises the odds of striking) and
`escalation` (how much each successful strike emboldens an unchecked ruler).
Set both to 0 and the three ways of governing differ only by the council vote.
"""
from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd

GOVERNANCE = ["Sole ruler", "Accountable leader", "Council"]
CHECKS = {"Sole ruler": 0.0, "Accountable leader": 1.0, "Council": 1.0}


@dataclass
class Settings:
    rulers: int = 200          # per way of governing
    seasons: int = 20
    effect: float = 1.0        # extra log-odds of striking with no checks
    escalation: float = 0.35   # extra log-odds per past successful strike, unchecked only
    harm_limit: float = 60.0   # outsider harm that gets an accountable leader replaced
    seed: int = 7


def _sigmoid(x):
    return 1 / (1 + np.exp(-x))


def _strike_logit(threat, trait, unchecked, wins, s):
    base = -2.2 + 2.0 * threat + trait
    return base + s.effect * unchecked + s.escalation * unchecked * wins


def simulate(settings: Settings = Settings()) -> pd.DataFrame:
    s = settings
    rng = np.random.default_rng(s.seed)
    rows = []
    for gov in GOVERNANCE:
        unchecked = 1.0 - CHECKS[gov]
        for r in range(s.rulers):
            ruler = f"{gov[:2].upper()}-{r + 1:03d}"
            trait = rng.normal(0, 0.6)
            council = rng.normal(0, 0.6, 5) if gov == "Council" else None
            safety, harm_total, wins = 50.0, 0.0, 0
            replaced = False
            first_catastrophe = None
            for t in range(1, s.seasons + 1):
                threat = min(1.0, 0.15 + 0.04 * t + rng.normal(0, 0.05))
                if gov == "Council":
                    p_member = _sigmoid(_strike_logit(threat, council, unchecked, wins, s))
                    strike = (rng.random(5) < p_member).sum() >= 3
                else:
                    strike = rng.random() < _sigmoid(_strike_logit(threat, trait, unchecked, wins, s))
                if strike:
                    choice = "strike"
                elif rng.random() < 0.5:
                    choice = "negotiate"
                else:
                    choice = "fortify"
                harm = 0.0
                catastrophe = False
                if choice == "strike":
                    roll = rng.random()
                    if roll < 0.15:
                        delta, catastrophe = -30.0, True
                    elif roll < 0.75:
                        delta = 10.0
                        wins += 1
                    else:
                        delta = -2.0
                    harm = rng.uniform(8, 20)
                elif choice == "negotiate":
                    delta = 5.0 if rng.random() < 0.5 else -2.0
                else:
                    delta = 3.0
                safety = float(np.clip(safety + delta - 4 * threat, 0, 100))
                harm_total += harm
                if catastrophe and first_catastrophe is None:
                    first_catastrophe = t
                rows.append({
                    "replaced_here": False,
                    "ruler": ruler, "governance": gov, "season": t, "threat": round(threat, 3),
                    "choice": choice, "catastrophe": catastrophe, "city_safety": round(safety, 1),
                    "outsider_harm": round(harm, 1), "outsider_harm_total": round(harm_total, 1),
                })
                # Accountability: a leader whose harm to outsiders passes the limit is
                # replaced by a fresh one with no record of wins.
                if gov == "Accountable leader" and harm_total > s.harm_limit and not replaced:
                    replaced = True
                    wins = 0
                    trait = rng.normal(0, 0.6)
                    rows[-1]["replaced_here"] = True
    df = pd.DataFrame(rows)
    df.attrs["settings"] = asdict(s)
    return df


def ruler_summary(df: pd.DataFrame, seasons: int) -> pd.DataFrame:
    g = df.groupby(["governance", "ruler"])
    out = g.agg(
        strike_share=("choice", lambda c: (c == "strike").mean()),
        outsider_harm=("outsider_harm", "sum"),
        final_safety=("city_safety", "last"),
        replaced=("replaced_here", "any"),
    ).reset_index()
    first = df[df["catastrophe"]].groupby("ruler")["season"].min()
    out["first_catastrophe"] = out["ruler"].map(first)
    out["had_catastrophe"] = out["first_catastrophe"].notna()
    out["seasons_to_catastrophe"] = out["first_catastrophe"].fillna(seasons).astype(int)
    return out


def survival_curve(summary: pd.DataFrame) -> pd.DataFrame:
    """Kaplan-Meier: share of cities with no catastrophe yet, by season.
    Cities that never had one are censored at the last season."""
    rows = []
    for gov, g in summary.groupby("governance"):
        at_risk = len(g)
        surv = 1.0
        rows.append({"governance": gov, "season": 0, "share_without_catastrophe": 1.0})
        for t in sorted(g["seasons_to_catastrophe"].unique()):
            events = int(((g["seasons_to_catastrophe"] == t) & g["had_catastrophe"]).sum())
            if at_risk > 0:
                surv *= 1 - events / at_risk
            rows.append({"governance": gov, "season": int(t), "share_without_catastrophe": surv})
            at_risk -= int((g["seasons_to_catastrophe"] == t).sum())
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = simulate()
    df.to_csv("data/walled_city_seasons.csv", index=False)
    summ = ruler_summary(df, Settings().seasons)
    summ.to_csv("data/walled_city_rulers.csv", index=False)
    print(summ.groupby("governance")[["strike_share", "outsider_harm", "final_safety", "had_catastrophe", "replaced"]].mean().round(3))
    null = ruler_summary(simulate(Settings(effect=0, escalation=0)), 20)
    print("effect switched off:")
    print(null.groupby("governance")[["strike_share", "outsider_harm", "had_catastrophe"]].mean().round(3))
