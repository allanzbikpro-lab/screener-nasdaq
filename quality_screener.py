"""
Screener Qualité Nasdaq 100 - Analyse fondamentale style Buffett/Munger
======================================================================
Évalue la qualité des entreprises selon 6 dimensions et calcule une
valeur intrinsèque via 3 méthodes (DCF, PER justifié, Graham).

Usage:
    python quality_screener.py
    python quality_screener.py --limit 10 --output results_quality.json
"""

import argparse
import json
import math
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")

# Liste Nasdaq 100 (mêmes tickers que le screener technique)
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

# Paramètres économiques (à ajuster selon contexte macro)
RISK_FREE_RATE = 0.045      # Rendement Treasury 10 ans ~4.5%
EQUITY_PREMIUM = 0.055      # Prime de risque actions ~5.5%
TERMINAL_GROWTH = 0.025     # Croissance à perpétuité ~PIB long terme
SAFETY_MARGIN = 0.25        # Marge de sécurité Buffett (achat si 25% sous juste valeur)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def safe_div(a, b, default=None):
    try:
        if a is None or b is None or b == 0:
            return default
        return a / b
    except Exception:
        return default


def safe_get(d, *keys, default=None):
    """Récupère la première clé existante avec valeur non-null."""
    for k in keys:
        v = d.get(k)
        if v is not None and not (isinstance(v, float) and np.isnan(v)):
            return v
    return default


def clamp_score(v, mn=0, mx=100):
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return 0
    return max(mn, min(mx, v))


def score_linear(value, bad, good, reverse=False):
    """Score 0-100 par interpolation linéaire entre deux bornes."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return 0
    if reverse:
        bad, good = good, bad
    if value <= bad:
        return 0
    if value >= good:
        return 100
    return (value - bad) / (good - bad) * 100


def cagr(series):
    """Taux de croissance annuel composé."""
    if series is None or len(series) < 2:
        return None
    s = series.dropna()
    if len(s) < 2:
        return None
    start, end = s.iloc[-1], s.iloc[0]  # yfinance retourne du plus récent au plus ancien
    years = len(s) - 1
    if start <= 0 or end <= 0 or years < 1:
        return None
    try:
        return (end / start) ** (1 / years) - 1
    except Exception:
        return None


def coef_variation(series):
    """Coefficient de variation (stabilité) - plus c'est bas, plus c'est stable."""
    if series is None or len(series) < 3:
        return None
    s = series.dropna()
    if len(s) < 3 or s.mean() == 0:
        return None
    return abs(s.std() / s.mean())


# ---------------------------------------------------------------------------
# Extraction des données fondamentales
# ---------------------------------------------------------------------------
def extract_fundamentals(ticker):
    """Récupère toutes les métriques nécessaires à l'analyse qualité."""
    try:
        t = yf.Ticker(ticker)
        info = t.info
        if not info or info.get("symbol") is None:
            return None

        fundamentals = {
            "ticker": ticker,
            "name": info.get("shortName") or info.get("longName") or ticker,
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "market_cap": info.get("marketCap"),
            "price": safe_get(info, "currentPrice", "regularMarketPrice"),
            "currency": info.get("currency", "USD"),
        }

        # Rentabilité
        fundamentals["roe"] = info.get("returnOnEquity")
        fundamentals["roa"] = info.get("returnOnAssets")
        fundamentals["gross_margin"] = info.get("grossMargins")
        fundamentals["operating_margin"] = info.get("operatingMargins")
        fundamentals["net_margin"] = info.get("profitMargins")
        fundamentals["ebitda_margin"] = info.get("ebitdaMargins")

        # Santé financière
        fundamentals["debt_to_equity"] = info.get("debtToEquity")
        fundamentals["current_ratio"] = info.get("currentRatio")
        fundamentals["quick_ratio"] = info.get("quickRatio")
        fundamentals["total_debt"] = info.get("totalDebt")
        fundamentals["total_cash"] = info.get("totalCash")
        fundamentals["ebitda"] = info.get("ebitda")
        fundamentals["free_cashflow"] = info.get("freeCashflow")
        fundamentals["operating_cashflow"] = info.get("operatingCashflow")

        # Valorisation
        fundamentals["pe_ratio"] = info.get("trailingPE")
        fundamentals["forward_pe"] = info.get("forwardPE")
        fundamentals["peg_ratio"] = info.get("trailingPegRatio") or info.get("pegRatio")
        fundamentals["price_to_book"] = info.get("priceToBook")
        fundamentals["price_to_sales"] = info.get("priceToSalesTrailing12Months")
        fundamentals["book_value"] = info.get("bookValue")
        fundamentals["eps_ttm"] = info.get("trailingEps")
        fundamentals["eps_forward"] = info.get("forwardEps")

        # Croissance
        fundamentals["revenue_growth"] = info.get("revenueGrowth")
        fundamentals["earnings_growth"] = info.get("earningsGrowth")
        fundamentals["earnings_quarterly_growth"] = info.get("earningsQuarterlyGrowth")

        # Dividende
        fundamentals["dividend_yield"] = info.get("dividendYield") or 0
        fundamentals["payout_ratio"] = info.get("payoutRatio")

        # Historique 5 ans pour CAGR / stabilité
        try:
            fin = t.financials  # Annuel, colonnes = années récentes en tête
            if fin is not None and not fin.empty:
                if "Total Revenue" in fin.index:
                    fundamentals["revenue_history"] = fin.loc["Total Revenue"].dropna().tolist()
                if "Net Income" in fin.index:
                    fundamentals["net_income_history"] = fin.loc["Net Income"].dropna().tolist()
                if "Operating Income" in fin.index:
                    fundamentals["op_income_history"] = fin.loc["Operating Income"].dropna().tolist()

            cf = t.cashflow
            if cf is not None and not cf.empty:
                if "Free Cash Flow" in cf.index:
                    fundamentals["fcf_history"] = cf.loc["Free Cash Flow"].dropna().tolist()
                elif "Operating Cash Flow" in cf.index:
                    # Approximation si FCF absent : CFO - CapEx (si dispo)
                    cfo = cf.loc["Operating Cash Flow"].dropna()
                    fundamentals["fcf_history"] = cfo.tolist()

            bs = t.balance_sheet
            if bs is not None and not bs.empty:
                if "Total Equity Gross Minority Interest" in bs.index:
                    eq = bs.loc["Total Equity Gross Minority Interest"].dropna()
                    fundamentals["equity_history"] = eq.tolist()
                elif "Stockholders Equity" in bs.index:
                    fundamentals["equity_history"] = bs.loc["Stockholders Equity"].dropna().tolist()
        except Exception:
            pass

        # Calcul ROIC approximatif si on a les données
        # ROIC = NOPAT / (Equity + Debt) ~ Op Income * (1-t) / Invested Capital
        op = fundamentals.get("op_income_history")
        equity = fundamentals.get("equity_history")
        debt = fundamentals.get("total_debt")
        if op and equity and debt and len(op) > 0 and len(equity) > 0:
            nopat = op[0] * (1 - 0.21)  # Taxe US fédérale ~21%
            invested_cap = equity[0] + (debt or 0)
            fundamentals["roic"] = safe_div(nopat, invested_cap)
        else:
            fundamentals["roic"] = None

        # Beta pour WACC
        fundamentals["beta"] = info.get("beta", 1.0)

        return fundamentals

    except Exception as e:
        print(f"  [!] Erreur {ticker}: {e}")
        return None


# ---------------------------------------------------------------------------
# Scoring Qualité (6 dimensions)
# ---------------------------------------------------------------------------
def compute_quality_score(f):
    """Retourne un dict avec tous les sous-scores et le score global."""
    scores = {}
    details = {}

    # ============ 1. MOAT (25 points) ============
    # ROIC élevé + marges brutes élevées + stabilité = avantage durable
    roic_score = score_linear(f.get("roic"), 0.05, 0.20) if f.get("roic") is not None else 50
    gm_score = score_linear(f.get("gross_margin"), 0.20, 0.60)
    om_score = score_linear(f.get("operating_margin"), 0.05, 0.30)
    # Stabilité marges via CV des revenus
    rev_hist = f.get("revenue_history", [])
    stability_score = 50
    if len(rev_hist) >= 3:
        cv = coef_variation(pd.Series(rev_hist))
        if cv is not None:
            stability_score = score_linear(cv, 0.30, 0.05, reverse=True)
    moat_raw = (roic_score * 0.35 + gm_score * 0.25 + om_score * 0.25 + stability_score * 0.15)
    scores["moat"] = round(moat_raw * 0.25, 1)  # Max 25 points
    details["moat"] = {
        "roic": f.get("roic"),
        "gross_margin": f.get("gross_margin"),
        "operating_margin": f.get("operating_margin"),
        "stability_score": round(stability_score, 1),
    }

    # ============ 2. RENTABILITÉ (20 points) ============
    roe_score = score_linear(f.get("roe"), 0.05, 0.25)
    roa_score = score_linear(f.get("roa"), 0.03, 0.12)
    nm_score = score_linear(f.get("net_margin"), 0.05, 0.25)
    profit_raw = (roe_score * 0.4 + roa_score * 0.3 + nm_score * 0.3)
    scores["profitability"] = round(profit_raw * 0.20, 1)
    details["profitability"] = {
        "roe": f.get("roe"),
        "roa": f.get("roa"),
        "net_margin": f.get("net_margin"),
    }

    # ============ 3. SANTÉ FINANCIÈRE (20 points) ============
    de = f.get("debt_to_equity")
    # yfinance renvoie parfois en pourcentage (ex 150 pour 1.5)
    if de and de > 10:
        de = de / 100
    de_score = score_linear(de, 2.0, 0.3, reverse=True) if de is not None else 50

    cr = f.get("current_ratio")
    cr_score = score_linear(cr, 1.0, 2.5) if cr is not None else 50

    # Dette / EBITDA
    debt = f.get("total_debt")
    ebitda = f.get("ebitda")
    dte = safe_div(debt, ebitda)
    dte_score = score_linear(dte, 5.0, 0.5, reverse=True) if dte is not None else 50

    # Cash / Dette (filet de sécurité)
    cash = f.get("total_cash")
    cash_debt = safe_div(cash, debt) if debt and debt > 0 else 2.0
    cash_score = score_linear(cash_debt, 0.1, 1.0)

    health_raw = (de_score * 0.3 + cr_score * 0.2 + dte_score * 0.3 + cash_score * 0.2)
    scores["financial_health"] = round(health_raw * 0.20, 1)
    details["financial_health"] = {
        "debt_to_equity": de,
        "current_ratio": cr,
        "debt_to_ebitda": round(dte, 2) if dte else None,
        "cash_to_debt": round(cash_debt, 2) if cash_debt else None,
    }

    # ============ 4. STABILITÉ / PRÉVISIBILITÉ (15 points) ============
    fcf_hist = f.get("fcf_history", [])
    ni_hist = f.get("net_income_history", [])

    fcf_stability = 50
    if len(fcf_hist) >= 3:
        # % années avec FCF positif
        pos_ratio = sum(1 for x in fcf_hist if x and x > 0) / len(fcf_hist)
        fcf_stability = pos_ratio * 100

    ni_stability = 50
    if len(ni_hist) >= 3:
        pos_ratio = sum(1 for x in ni_hist if x and x > 0) / len(ni_hist)
        ni_stability = pos_ratio * 100

    pred_raw = (fcf_stability * 0.5 + ni_stability * 0.5)
    scores["stability"] = round(pred_raw * 0.15, 1)
    details["stability"] = {
        "fcf_positive_years_pct": round(fcf_stability, 0),
        "ni_positive_years_pct": round(ni_stability, 0),
    }

    # ============ 5. CROISSANCE (10 points) ============
    rev_cagr = cagr(pd.Series(rev_hist)) if len(rev_hist) >= 3 else f.get("revenue_growth")
    ni_cagr = cagr(pd.Series(ni_hist)) if len(ni_hist) >= 3 else f.get("earnings_growth")

    rev_g_score = score_linear(rev_cagr, 0, 0.20) if rev_cagr is not None else 50
    ni_g_score = score_linear(ni_cagr, 0, 0.20) if ni_cagr is not None else 50

    growth_raw = (rev_g_score * 0.5 + ni_g_score * 0.5)
    scores["growth"] = round(growth_raw * 0.10, 1)
    details["growth"] = {
        "revenue_cagr_5y": rev_cagr,
        "earnings_cagr_5y": ni_cagr,
    }

    # Score total (sans marge de sécurité, ajoutée après valorisation)
    quality_score = sum(scores.values())

    return {
        "scores": scores,
        "details": details,
        "quality_score": round(quality_score, 1),
    }


# ---------------------------------------------------------------------------
# Valorisation intrinsèque - 3 méthodes
# ---------------------------------------------------------------------------
def dcf_valuation(f):
    """DCF simplifié sur 5 ans + valeur terminale."""
    fcf = f.get("free_cashflow")
    if not fcf or fcf <= 0:
        # Utiliser historique si dispo
        fcf_hist = f.get("fcf_history", [])
        if fcf_hist:
            fcf = np.mean([x for x in fcf_hist[:3] if x and x > 0]) if any(x and x > 0 for x in fcf_hist[:3]) else None
        if not fcf or fcf <= 0:
            return None

    # Taux de croissance 5 ans (borné à 15% pour être conservateur)
    growth = f.get("revenue_growth") or 0.05
    if growth > 0.15:
        growth = 0.15
    if growth < 0:
        growth = 0.02

    # WACC simplifié via CAPM : Rf + beta * ERP
    beta = f.get("beta", 1.0) or 1.0
    wacc = RISK_FREE_RATE + beta * EQUITY_PREMIUM
    wacc = max(0.07, min(0.15, wacc))  # Borner entre 7% et 15%

    if wacc <= TERMINAL_GROWTH:
        return None

    # Projection des FCF sur 5 ans
    fcf_proj = []
    for year in range(1, 6):
        fcf_proj.append(fcf * ((1 + growth) ** year))

    # Valeur terminale via modèle de Gordon
    terminal_fcf = fcf_proj[-1] * (1 + TERMINAL_GROWTH)
    terminal_value = terminal_fcf / (wacc - TERMINAL_GROWTH)

    # Actualisation
    pv_fcf = sum(cf / ((1 + wacc) ** (i + 1)) for i, cf in enumerate(fcf_proj))
    pv_terminal = terminal_value / ((1 + wacc) ** 5)
    enterprise_value = pv_fcf + pv_terminal

    # Equity = EV - Dette + Cash
    debt = f.get("total_debt") or 0
    cash = f.get("total_cash") or 0
    equity_value = enterprise_value - debt + cash

    # Approximation shares outstanding via market cap / prix
    price = f.get("price")
    mcap = f.get("market_cap")
    if not price or not mcap:
        return None
    shares = mcap / price
    if shares <= 0:
        return None

    intrinsic = equity_value / shares
    return round(intrinsic, 2) if intrinsic > 0 else None


def peg_valuation(f):
    """Valeur via PER justifié (Peter Lynch) : PER fair = g% + dividend yield."""
    eps = f.get("eps_forward") or f.get("eps_ttm")
    if not eps or eps <= 0:
        return None

    rev_hist = f.get("revenue_history", [])
    ni_hist = f.get("net_income_history", [])

    # Taux de croissance historique EPS (priorité) ou revenus
    growth = cagr(pd.Series(ni_hist)) if len(ni_hist) >= 3 else None
    if growth is None or growth <= 0:
        growth = cagr(pd.Series(rev_hist)) if len(rev_hist) >= 3 else None
    if growth is None or growth <= 0:
        growth = f.get("revenue_growth") or 0.05

    growth_pct = growth * 100
    if growth_pct > 30:
        growth_pct = 30  # Borne : Lynch considérait qu'au-delà c'est irréaliste

    div_yield_pct = (f.get("dividend_yield") or 0) * 100
    fair_pe = growth_pct + div_yield_pct
    if fair_pe < 8:
        fair_pe = 8   # Plancher raisonnable
    if fair_pe > 30:
        fair_pe = 30  # Plafond conservateur

    return round(fair_pe * eps, 2)


def graham_valuation(f):
    """Graham Number : √(22.5 × EPS × BookValue). Formule ultra-conservatrice."""
    eps = f.get("eps_ttm")
    bv = f.get("book_value")
    if not eps or not bv or eps <= 0 or bv <= 0:
        return None
    try:
        return round(math.sqrt(22.5 * eps * bv), 2)
    except Exception:
        return None


def intrinsic_value(f):
    """Retourne les 3 méthodes + moyenne + marge de sécurité."""
    dcf = dcf_valuation(f)
    peg = peg_valuation(f)
    graham = graham_valuation(f)

    values = [v for v in [dcf, peg, graham] if v is not None and v > 0]
    avg = round(sum(values) / len(values), 2) if values else None

    price = f.get("price")
    margin = None
    if avg and price and price > 0:
        margin = (avg - price) / price  # >0 = sous-évalué

    return {
        "dcf": dcf,
        "peg_lynch": peg,
        "graham": graham,
        "average": avg,
        "price": price,
        "margin_of_safety": round(margin, 3) if margin is not None else None,
    }


# ---------------------------------------------------------------------------
# Analyse complète d'un ticker
# ---------------------------------------------------------------------------
def analyze_ticker(ticker):
    f = extract_fundamentals(ticker)
    if not f:
        return None

    quality = compute_quality_score(f)
    valuation = intrinsic_value(f)

    # Bonus marge de sécurité (0 à 10 points)
    mos = valuation.get("margin_of_safety")
    if mos is not None:
        if mos >= 0.30:
            mos_score = 10
        elif mos >= 0:
            mos_score = 10 * mos / 0.30
        elif mos >= -0.30:
            mos_score = 10 * mos / 0.30  # Négatif si surévalué
        else:
            mos_score = -10
    else:
        mos_score = 0

    total_score = round(quality["quality_score"] + mos_score, 1)
    total_score = max(0, min(100, total_score))

    # Tier qualité
    if total_score >= 75:
        tier = "EXCELLENTE"
    elif total_score >= 60:
        tier = "BONNE"
    elif total_score >= 45:
        tier = "MOYENNE"
    elif total_score >= 30:
        tier = "FAIBLE"
    else:
        tier = "A_EVITER"

    # Verdict valorisation
    if mos is None:
        verdict = "INCONNU"
    elif mos >= 0.30:
        verdict = "TRES_SOUS_VALORISE"
    elif mos >= 0.10:
        verdict = "SOUS_VALORISE"
    elif mos >= -0.10:
        verdict = "JUSTE_PRIX"
    elif mos >= -0.25:
        verdict = "SURVALORISE"
    else:
        verdict = "TRES_SURVALORISE"

    return {
        "ticker": ticker,
        "name": f.get("name"),
        "sector": f.get("sector"),
        "industry": f.get("industry"),
        "price": f.get("price"),
        "market_cap": f.get("market_cap"),
        "currency": f.get("currency"),
        "quality_score": quality["quality_score"],
        "total_score": total_score,
        "tier": tier,
        "verdict": verdict,
        "sub_scores": quality["scores"],
        "mos_score": round(mos_score, 1),
        "details": quality["details"],
        "valuation": valuation,
        "key_metrics": {
            "pe_ratio": f.get("pe_ratio"),
            "forward_pe": f.get("forward_pe"),
            "peg_ratio": f.get("peg_ratio"),
            "price_to_book": f.get("price_to_book"),
            "dividend_yield": f.get("dividend_yield"),
            "roe": f.get("roe"),
            "roic": f.get("roic"),
            "gross_margin": f.get("gross_margin"),
            "operating_margin": f.get("operating_margin"),
            "net_margin": f.get("net_margin"),
            "debt_to_equity": f.get("debt_to_equity"),
        },
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Screener Qualité Nasdaq 100")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--output", default="results_quality.json")
    parser.add_argument("--output-dir", default=".")
    args = parser.parse_args()

    tickers = NASDAQ100[: args.limit] if args.limit else NASDAQ100
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  Screener Qualité Nasdaq 100 (Buffett/Munger)")
    print(f"  {len(tickers)} tickers à analyser")
    print(f"{'='*60}\n")

    results = []
    for i, t in enumerate(tickers, 1):
        print(f"[{i:3}/{len(tickers)}] {t:6} ", end="", flush=True)
        r = analyze_ticker(t)
        if r:
            results.append(r)
            emoji = {"EXCELLENTE": "⭐⭐⭐", "BONNE": "⭐⭐", "MOYENNE": "⭐",
                     "FAIBLE": "⚠️", "A_EVITER": "❌"}[r["tier"]]
            vm = r["valuation"].get("margin_of_safety")
            mos_str = f"MoS={vm*100:+.0f}%" if vm is not None else "MoS=?"
            print(f"{emoji} score={r['total_score']:5.1f}  {r['tier']:10}  {mos_str}")
        else:
            print("— (données indisponibles)")

    results.sort(key=lambda x: x["total_score"], reverse=True)

    output = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "type": "quality",
        "count": len(results),
        "results": results,
    }

    out_path = out_dir / args.output
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False, default=str))

    # Résumé
    excellent = [r for r in results if r["tier"] == "EXCELLENTE"]
    good = [r for r in results if r["tier"] == "BONNE"]
    sousval = [r for r in results if r["verdict"] in ["SOUS_VALORISE", "TRES_SOUS_VALORISE"]]

    print(f"\n{'='*60}")
    print(f"  RÉSUMÉ")
    print(f"{'='*60}")
    print(f"  ⭐⭐⭐ Excellentes : {len(excellent):3}  {[r['ticker'] for r in excellent[:10]]}")
    print(f"  ⭐⭐  Bonnes       : {len(good):3}  {[r['ticker'] for r in good[:10]]}")
    print(f"  💰 Sous-valorisées: {len(sousval):3}  {[r['ticker'] for r in sousval[:10]]}")
    print(f"\n  Résultats écrits dans : {out_path.absolute()}\n")


if __name__ == "__main__":
    main()
