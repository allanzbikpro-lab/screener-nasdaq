"""
Screener Nasdaq 100 - Moteur d'analyse technique
================================================
Détecte zones d'achat/vente via patterns de chandeliers, volumes,
divergences, croisements MM et niveaux de survente/surachat.

Usage:
    python screener.py --horizon swing
    python screener.py --horizon position
    python screener.py --horizon all         # génère les 3 fichiers
"""

import argparse
import json
import shutil
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Configuration par horizon
# ---------------------------------------------------------------------------
HORIZON_CONFIG = {
    "day": {
        "interval": "5m", "period": "5d",
        "ema_fast": 9, "ema_slow": 20, "ema_trend": 50,
        "rsi_period": 14, "lookback_pattern": 5, "volume_ma": 20,
        "label": "Day Trading (5min)",
    },
    "swing": {
        "interval": "1d", "period": "6mo",
        "ema_fast": 20, "ema_slow": 50, "ema_trend": 100,
        "rsi_period": 14, "lookback_pattern": 5, "volume_ma": 20,
        "label": "Swing Trading (journalier)",
    },
    "position": {
        "interval": "1d", "period": "2y",
        "ema_fast": 50, "ema_slow": 100, "ema_trend": 200,
        "rsi_period": 14, "lookback_pattern": 10, "volume_ma": 50,
        "label": "Position Trading (LT)",
    },
}

NASDAQ100 = [
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "TSLA", "AVGO", "COST",
    "NFLX", "ADBE", "PEP", "ASML", "TMUS", "CSCO", "AZN", "LIN", "INTU", "AMD",
    "QCOM", "TXN", "ISRG", "CMCSA", "AMGN", "HON", "AMAT", "BKNG", "PANW", "ADP",
    "GILD", "VRTX", "ADI", "MU", "LRCX", "MELI", "SBUX", "PYPL", "MDLZ", "REGN",
    "KLAC", "SNPS", "CDNS", "PLTR", "CRWD", "MAR", "CEG", "ORLY", "CTAS", "FTNT",
    "CHTR", "MNST", "WDAY", "ABNB", "ADSK", "NXPI", "PCAR", "ROP", "DASH", "FANG",
    "ROST", "MRVL", "AEP", "KDP", "FAST", "PAYX", "CPRT", "ODFL", "EA", "KHC",
    "BKR", "IDXX", "CHKP", "VRSK", "CSGP", "EXC", "CTSH", "XEL", "CCEP", "GEHC",
    "LULU", "TTD", "ANSS", "DDOG", "ZS", "TEAM", "BIIB", "ON", "CDW", "WBD",
    "MDB", "GFS", "DXCM", "ARM", "MRNA", "ILMN", "SMCI", "TTWO", "WBA", "SIRI",
]


# ---------------------------------------------------------------------------
# Indicateurs
# ---------------------------------------------------------------------------
def ema(s, p): return s.ewm(span=p, adjust=False).mean()
def sma(s, p): return s.rolling(p).mean()


def rsi(s, p=14):
    d = s.diff()
    g = d.where(d > 0, 0.0)
    l = -d.where(d < 0, 0.0)
    ag = g.ewm(alpha=1 / p, adjust=False).mean()
    al = l.ewm(alpha=1 / p, adjust=False).mean()
    rs = ag / al.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd(s, f=12, sl=26, sg=9):
    m = ema(s, f) - ema(s, sl)
    sig = ema(m, sg)
    return m, sig, m - sig


def bollinger(s, p=20, sd=2.0):
    m = sma(s, p)
    d = s.rolling(p).std()
    return m + sd * d, m, m - sd * d


def atr(h, l, c, p=14):
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / p, adjust=False).mean()


# ---------------------------------------------------------------------------
# Patterns de chandeliers
# ---------------------------------------------------------------------------
def candle_anatomy(df):
    o = df.copy()
    o["body"] = (o["Close"] - o["Open"]).abs()
    o["range"] = o["High"] - o["Low"]
    o["upper_wick"] = o["High"] - o[["Open", "Close"]].max(axis=1)
    o["lower_wick"] = o[["Open", "Close"]].min(axis=1) - o["Low"]
    o["bullish"] = o["Close"] > o["Open"]
    rng = o["range"].replace(0, np.nan)
    o["body_ratio"] = o["body"] / rng
    o["upper_ratio"] = o["upper_wick"] / rng
    o["lower_ratio"] = o["lower_wick"] / rng
    return o


def detect_patterns(df):
    if len(df) < 3:
        return {}
    d = candle_anatomy(df)
    last, prev = d.iloc[-1], d.iloc[-2]
    p = {}

    if last["lower_ratio"] >= 0.6 and last["upper_ratio"] <= 0.15 and last["body_ratio"] <= 0.3:
        p["hammer"] = {"signal": "bullish", "strength": 70}
    if last["upper_ratio"] >= 0.6 and last["lower_ratio"] <= 0.15 and last["body_ratio"] <= 0.3:
        p["shooting_star"] = {"signal": "bearish", "strength": 70}
    if last["body_ratio"] <= 0.1 and last["range"] > 0:
        p["doji"] = {"signal": "neutral", "strength": 40}

    if (not prev["bullish"] and last["bullish"] and last["Open"] < prev["Close"]
            and last["Close"] > prev["Open"] and last["body"] > prev["body"]):
        p["bullish_engulfing"] = {"signal": "bullish", "strength": 80}
    if (prev["bullish"] and not last["bullish"] and last["Open"] > prev["Close"]
            and last["Close"] < prev["Open"] and last["body"] > prev["body"]):
        p["bearish_engulfing"] = {"signal": "bearish", "strength": 80}

    if len(d) >= 3:
        p2 = d.iloc[-3]
        if (not p2["bullish"] and p2["body_ratio"] > 0.5 and prev["body_ratio"] < 0.3
                and last["bullish"] and last["Close"] > (p2["Open"] + p2["Close"]) / 2):
            p["morning_star"] = {"signal": "bullish", "strength": 85}
        if (p2["bullish"] and p2["body_ratio"] > 0.5 and prev["body_ratio"] < 0.3
                and not last["bullish"] and last["Close"] < (p2["Open"] + p2["Close"]) / 2):
            p["evening_star"] = {"signal": "bearish", "strength": 85}
    return p


def detect_divergence(price, indicator, lookback=20):
    if len(price) < lookback:
        return None
    p = price.iloc[-lookback:]
    i = indicator.iloc[-lookback:]
    recent_high_idx = price.iloc[-5:].idxmax()
    recent_low_idx = price.iloc[-5:].idxmin()

    if recent_high_idx == price.iloc[-5:].index[-1] and p.iloc[-1] >= p.max() * 0.98:
        if len(p) > 5:
            ph = p.iloc[:-5].max()
            phi = p.iloc[:-5].idxmax()
            if p.iloc[-1] > ph and i.iloc[-1] < indicator.loc[phi]:
                return "bearish"

    if recent_low_idx == price.iloc[-5:].index[-1] and p.iloc[-1] <= p.min() * 1.02:
        if len(p) > 5:
            pl = p.iloc[:-5].min()
            pli = p.iloc[:-5].idxmin()
            if p.iloc[-1] < pl and i.iloc[-1] > indicator.loc[pli]:
                return "bullish"
    return None


# ---------------------------------------------------------------------------
# Analyse d'un ticker
# ---------------------------------------------------------------------------
def analyze_ticker(ticker, config):
    try:
        df = yf.download(ticker, period=config["period"], interval=config["interval"],
                         progress=False, auto_adjust=True)
        if df.empty or len(df) < 50:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        close, high, low, volume = df["Close"], df["High"], df["Low"], df["Volume"]

        df["ema_fast"] = ema(close, config["ema_fast"])
        df["ema_slow"] = ema(close, config["ema_slow"])
        df["ema_trend"] = ema(close, config["ema_trend"])
        df["rsi"] = rsi(close, config["rsi_period"])
        m, sig, hist = macd(close)
        df["macd"], df["macd_signal"], df["macd_hist"] = m, sig, hist
        u, mid, lo = bollinger(close)
        df["bb_upper"], df["bb_mid"], df["bb_lower"] = u, mid, lo
        df["atr"] = atr(high, low, close)
        df["vol_ma"] = volume.rolling(config["volume_ma"]).mean()
        df["vol_ratio"] = volume / df["vol_ma"]

        last, prev = df.iloc[-1], df.iloc[-2]
        signals, score = [], 0.0

        # Patterns
        patterns = detect_patterns(df.tail(10))
        ps = 0
        for n, pt in patterns.items():
            if pt["signal"] == "bullish":
                ps += pt["strength"] * 0.25
                signals.append({"type": "pattern", "name": n, "dir": "bull", "weight": pt["strength"]})
            elif pt["signal"] == "bearish":
                ps -= pt["strength"] * 0.25
                signals.append({"type": "pattern", "name": n, "dir": "bear", "weight": pt["strength"]})
        ps = max(-20, min(20, ps))

        # Volume + breakout
        vs = 0
        vr = float(last["vol_ratio"]) if pd.notna(last["vol_ratio"]) else 1.0
        rh20 = high.iloc[-21:-1].max()
        rl20 = low.iloc[-21:-1].min()
        if vr > 1.5:
            if last["Close"] > rh20:
                vs = 25; signals.append({"type": "breakout", "name": "breakout_haussier_volume", "dir": "bull", "weight": 90})
            elif last["Close"] < rl20:
                vs = -25; signals.append({"type": "breakout", "name": "breakout_baissier_volume", "dir": "bear", "weight": 90})
            elif last["Close"] > last["Open"]:
                vs = 10; signals.append({"type": "volume", "name": "volume_achat_anormal", "dir": "bull", "weight": 60})
            else:
                vs = -10; signals.append({"type": "volume", "name": "volume_vente_anormal", "dir": "bear", "weight": 60})

        # Divergences
        ds = 0
        dv = detect_divergence(close, df["rsi"], 20)
        if dv == "bullish":
            ds = 20; signals.append({"type": "divergence", "name": "divergence_haussiere_rsi", "dir": "bull", "weight": 75})
        elif dv == "bearish":
            ds = -20; signals.append({"type": "divergence", "name": "divergence_baissiere_rsi", "dir": "bear", "weight": 75})

        # Croisements MM
        ms = 0
        cu = (prev["ema_fast"] <= prev["ema_slow"]) and (last["ema_fast"] > last["ema_slow"])
        cd = (prev["ema_fast"] >= prev["ema_slow"]) and (last["ema_fast"] < last["ema_slow"])
        if cu:
            ms = 15; signals.append({"type": "ma_cross", "name": "golden_cross_court", "dir": "bull", "weight": 70})
        elif cd:
            ms = -15; signals.append({"type": "ma_cross", "name": "death_cross_court", "dir": "bear", "weight": 70})
        elif last["Close"] > last["ema_trend"]:
            ms = 5
        else:
            ms = -5

        # Survente/surachat
        rv = float(last["rsi"]) if pd.notna(last["rsi"]) else 50
        os_ = 0
        if rv < 30:
            os_ = 20; signals.append({"type": "oversold", "name": f"rsi_survente_{rv:.0f}", "dir": "bull", "weight": 65})
        elif rv > 70:
            os_ = -20; signals.append({"type": "overbought", "name": f"rsi_surachat_{rv:.0f}", "dir": "bear", "weight": 65})
        if last["Close"] < last["bb_lower"]:
            os_ += 5; signals.append({"type": "bollinger", "name": "sous_bb_inf", "dir": "bull", "weight": 50})
        elif last["Close"] > last["bb_upper"]:
            os_ -= 5; signals.append({"type": "bollinger", "name": "au_dessus_bb_sup", "dir": "bear", "weight": 50})

        score = max(-100, min(100, ps + vs + ds + ms + os_))

        if score >= 40:
            zone = "ACHAT_FORT"
        elif score >= 20:
            zone = "ACHAT"
        elif score <= -40:
            zone = "VENTE_FORT"
        elif score <= -20:
            zone = "VENTE"
        else:
            zone = "NEUTRE"

        chart_df = df.tail(60).reset_index()
        date_col = "Datetime" if "Datetime" in chart_df.columns else "Date"
        history = [{
            "date": str(row[date_col])[:16],
            "open": round(float(row["Open"]), 2),
            "high": round(float(row["High"]), 2),
            "low": round(float(row["Low"]), 2),
            "close": round(float(row["Close"]), 2),
            "volume": int(row["Volume"]),
        } for _, row in chart_df.iterrows()]

        return {
            "ticker": ticker,
            "price": round(float(last["Close"]), 2),
            "change_pct": round(float((last["Close"] / prev["Close"] - 1) * 100), 2),
            "volume_ratio": round(vr, 2),
            "rsi": round(rv, 1),
            "macd_hist": round(float(last["macd_hist"]), 3),
            "ema_fast": round(float(last["ema_fast"]), 2),
            "ema_slow": round(float(last["ema_slow"]), 2),
            "ema_trend": round(float(last["ema_trend"]), 2),
            "atr": round(float(last["atr"]), 2),
            "score": round(score, 1),
            "zone": zone,
            "signals": signals,
            "history": history,
        }
    except Exception as e:
        print(f"  [!] Erreur {ticker}: {e}")
        return None


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
def run_horizon(horizon, tickers, output_path):
    config = HORIZON_CONFIG[horizon]
    print(f"\n{'='*60}\n  {config['label']} — {len(tickers)} tickers\n{'='*60}")

    results = []
    for i, t in enumerate(tickers, 1):
        print(f"[{i:3}/{len(tickers)}] {t:6} ", end="", flush=True)
        r = analyze_ticker(t, config)
        if r:
            results.append(r)
            e = {"ACHAT_FORT": "🟢🟢", "ACHAT": "🟢", "NEUTRE": "⚪",
                 "VENTE": "🔴", "VENTE_FORT": "🔴🔴"}[r["zone"]]
            print(f"{e} score={r['score']:+6.1f}  {r['zone']}")
        else:
            print("—")

    results.sort(key=lambda x: abs(x["score"]), reverse=True)
    output = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "horizon": horizon,
        "horizon_label": config["label"],
        "count": len(results),
        "results": results,
    }
    Path(output_path).write_text(json.dumps(output, indent=2, ensure_ascii=False))
    bs = sum(1 for r in results if r["zone"] == "ACHAT_FORT")
    ss = sum(1 for r in results if r["zone"] == "VENTE_FORT")
    print(f"\n  ✓ {output_path} — 🟢🟢 {bs}  |  🔴🔴 {ss}")
    return output


def main():
    parser = argparse.ArgumentParser(description="Screener Nasdaq 100")
    parser.add_argument("--horizon", choices=["day", "swing", "position", "all"],
                        default="swing", help="Horizon (ou 'all' pour tous)")
    parser.add_argument("--limit", type=int, default=None, help="Limiter tickers (debug)")
    parser.add_argument("--output-dir", default=".", help="Dossier de sortie")
    args = parser.parse_args()

    tickers = NASDAQ100[: args.limit] if args.limit else NASDAQ100
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.horizon == "all":
        for h in ["swing", "position"]:
            run_horizon(h, tickers, str(out_dir / f"results_{h}.json"))
        shutil.copy(out_dir / "results_swing.json", out_dir / "results.json")
        print(f"\n  ✓ Tous horizons générés dans {out_dir.absolute()}\n")
    else:
        run_horizon(args.horizon, tickers, str(out_dir / "results.json"))


if __name__ == "__main__":
    main()
