""
Screener Qualité v4 - Scoring strict sur 8 indicateurs fondamentaux
====================================================================
Approche stricte basée sur les seuils Buffett/Munger/value investing :
chaque indicateur = vert (1pt) / jaune (0.5pt) / rouge (0pt).

Indicateurs évalués :
1. Marge nette (>15% / 5-15% / <5%)
2. Croissance CA 5 ans (>7% / 3-7% / <3%)
3. Payout ratio (30-60% / 0-30% ou 60-80% / >80%)
4. PER (<18 ou <40 si qualité / 18-25 / >40)
5. ROE (>20% / 10-20% / <10%)
6. Dette nette / EBITDA (<0 ou ≤2 / 2-4 / >4)
7. ROIC moyen 5 ans (>15% / 10-15% / <10%)
8. FCF / Résultat net (≥80% / 50-80% / <50%)

Usage:
    python quality_screener.py --universe nasdaq100
    python quality_screener.py --universe stoxx600 --delay 0.3
"""

import argparse
import json
import math
import time
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")

from universes import get_universe, ticker_to_flag

# Paramètres économiques par défaut pour DCF
DEFAULT_RISK_FREE = 0.045
DEFAULT_EQUITY_PREMIUM = 0.055
DEFAULT_TERMINAL_GROWTH = 0.025


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


def to_float(v, default=None):
    """Convertit en float de façon robuste. Gère les strings, None, NaN, valeurs étranges."""
    if v is None:
        return default
    if isinstance(v, (int, float)):
        if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
            return default
        return float(v)
    # String ou autre : tenter conversion
    try:
        s = str(v).strip().replace(',', '.').replace('%', '')
        if s == '' or s.lower() in ('nan', 'none', 'null', 'n/a', '-'):
            return default
        return float(s)
    except (ValueError, TypeError):
        return default


def normalize_fundamentals(f):
    """Convertit en float toutes les clés numériques susceptibles de contenir des strings."""
    numeric_keys = [
        "market_cap", "price", "shares_outstanding", "beta",
        "roe", "roa", "gross_margin", "operating_margin", "net_margin",
        "debt_to_equity", "current_ratio", "total_debt", "total_cash", "ebitda",
        "free_cashflow", "pe_ratio", "forward_pe", "price_to_book",
        "book_value", "eps_ttm", "eps_forward",
        "dividend_yield", "payout_ratio",
    ]
    for k in numeric_keys:
        if k in f:
            f[k] = to_float(f[k])
    return f


def safe_get(d, *keys, default=None):
    for k in keys:
        v = d.get(k)
        if v is not None and not (isinstance(v, float) and np.isnan(v)):
            return v
    return default


def cagr(series):
    if series is None:
        return None
    s = pd.Series(series).dropna() if not isinstance(series, pd.Series) else series.dropna()
    if len(s) < 2:
        return None
    # yfinance retourne du plus récent au plus ancien
    start, end = s.iloc[-1], s.iloc[0]
    years = len(s) - 1
    if start is None or end is None or start <= 0 or end <= 0 or years < 1:
        return None
    try:
        return (end / start) ** (1 / years) - 1
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Extraction des fondamentaux
# ---------------------------------------------------------------------------
def extract_fundamentals(ticker):
    try:
        t = yf.Ticker(ticker)
        info = t.info
        if not info or info.get("symbol") is None:
            return None

        f = {
            "ticker": ticker,
            "name": info.get("shortName") or info.get("longName") or ticker,
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "market_cap": info.get("marketCap"),
            "price": safe_get(info, "currentPrice", "regularMarketPrice"),
            "currency": info.get("currency", "USD"),
            "shares_outstanding": info.get("sharesOutstanding"),
            "beta": info.get("beta") or 1.0,
        }

        # Rentabilité
        f["roe"] = info.get("returnOnEquity")
        f["roa"] = info.get("returnOnAssets")
        f["gross_margin"] = info.get("grossMargins")
        f["operating_margin"] = info.get("operatingMargins")
        f["net_margin"] = info.get("profitMargins")

        # Santé financière
        f["debt_to_equity"] = info.get("debtToEquity")
        f["current_ratio"] = info.get("currentRatio")
        f["total_debt"] = info.get("totalDebt") or 0
        f["total_cash"] = info.get("totalCash") or 0
        f["ebitda"] = info.get("ebitda")
        f["free_cashflow"] = info.get("freeCashflow")

        # Valorisation
        f["pe_ratio"] = info.get("trailingPE")
        f["forward_pe"] = info.get("forwardPE")
        f["price_to_book"] = info.get("priceToBook")
        f["book_value"] = info.get("bookValue")
        f["eps_ttm"] = info.get("trailingEps")
        f["eps_forward"] = info.get("forwardEps")

        # Dividendes
        f["dividend_yield"] = info.get("dividendYield") or 0
        f["payout_ratio"] = info.get("payoutRatio")

        # Historiques 5 ans
        try:
            fin = t.financials
            if fin is not None and not fin.empty:
                if "Total Revenue" in fin.index:
                    f["revenue_history"] = fin.loc["Total Revenue"].dropna().tolist()
                if "Net Income" in fin.index:
                    f["net_income_history"] = fin.loc["Net Income"].dropna().tolist()
                if "Operating Income" in fin.index:
                    f["op_income_history"] = fin.loc["Operating Income"].dropna().tolist()
                if "EBIT" in fin.index:
                    f["ebit_history"] = fin.loc["EBIT"].dropna().tolist()

            cf = t.cashflow
            if cf is not None and not cf.empty:
                if "Free Cash Flow" in cf.index:
                    f["fcf_history"] = cf.loc["Free Cash Flow"].dropna().tolist()
                elif "Operating Cash Flow" in cf.index:
                    f["fcf_history"] = cf.loc["Operating Cash Flow"].dropna().tolist()

            bs = t.balance_sheet
            if bs is not None and not bs.empty:
                eq = None
                for k in ["Total Equity Gross Minority Interest", "Stockholders Equity", "Total Stockholder Equity"]:
                    if k in bs.index:
                        eq = bs.loc[k].dropna()
                        break
                if eq is not None:
                    f["equity_history"] = eq.tolist()

                # Total assets pour calcul ROIC plus robuste
                ta = None
                for k in ["Total Assets"]:
                    if k in bs.index:
                        ta = bs.loc[k].dropna()
                        break
                if ta is not None:
                    f["assets_history"] = ta.tolist()

                # Total dette historique
                td = None
                for k in ["Total Debt", "Long Term Debt"]:
                    if k in bs.index:
                        td = bs.loc[k].dropna()
                        break
                if td is not None:
                    f["debt_history"] = td.tolist()

                # Cash historique
                cash_h = None
                for k in ["Cash And Cash Equivalents", "Cash"]:
                    if k in bs.index:
                        cash_h = bs.loc[k].dropna()
                        break
                if cash_h is not None:
                    f["cash_history"] = cash_h.tolist()
        except Exception:
            pass

        # Calcul ROIC année par année (5 ans)
        # ROIC = NOPAT / Capital Investi
        # NOPAT ≈ EBIT * (1 - taux d'imposition effectif), on prend 21% (US fédéral, conservateur)
        # Capital Investi = Equity + Total Debt - Cash
        roic_history = []
        ebits = f.get("ebit_history") or f.get("op_income_history") or []
        equities = f.get("equity_history", [])
        debts = f.get("debt_history", [])
        cashes = f.get("cash_history", [])
        years = min(len(ebits), len(equities), 5)
        for i in range(years):
            try:
                nopat = ebits[i] * (1 - 0.25)  # taux moyen
                eq = equities[i] if i < len(equities) else 0
                dt = debts[i] if i < len(debts) else (f.get("total_debt") or 0)
                ch = cashes[i] if i < len(cashes) else (f.get("total_cash") or 0)
                cap = (eq or 0) + (dt or 0) - (ch or 0)
                if cap and cap > 0:
                    roic_history.append(nopat / cap)
            except Exception:
                pass
        f["roic_history"] = roic_history
        f["roic_avg_5y"] = sum(roic_history) / len(roic_history) if roic_history else None
        f["roic_min_5y"] = min(roic_history) if roic_history else None

        # FCF / Net Income ratio sur 5 ans (moyenne)
        fcfs = f.get("fcf_history", [])
        nis = f.get("net_income_history", [])
        ratios = []
        for fcf, ni in zip(fcfs[:5], nis[:5]):
            if ni and ni > 0 and fcf is not None:
                ratios.append(fcf / ni)
        f["fcf_to_ni_avg"] = sum(ratios) / len(ratios) if ratios else None

        # CAGR revenus 5 ans
        f["revenue_cagr_5y"] = cagr(f.get("revenue_history", []))

        # Dette nette
        f["net_debt"] = (f.get("total_debt") or 0) - (f.get("total_cash") or 0)
        f["net_debt_to_ebitda"] = safe_div(f["net_debt"], f.get("ebitda"))

        # Détection contexte "Qualité/Luxe" pour PER
        # Critères : marge nette > 15% ET ROE > 20% ET ROIC moyen > 15%
        is_premium = (
            (to_float(f.get("net_margin")) or 0) > 0.15 and
            (to_float(f.get("roe")) or 0) > 0.20 and
            (f.get("roic_avg_5y") or 0) > 0.15
        )
        f["is_premium_quality"] = is_premium

        # Normaliser tous les types numériques (yfinance renvoie parfois des strings sur les marchés EU)
        f = normalize_fundamentals(f)

        return f
    except Exception as e:
        print(f"  [!] Erreur {ticker}: {e}")
        return None


# ---------------------------------------------------------------------------
# Évaluation des 8 indicateurs (scoring strict vert/jaune/rouge)
# ---------------------------------------------------------------------------
def evaluate_indicators(f):
    """
    Retourne une liste de dicts, un par indicateur, avec :
    - id, label, description, value, status (green/yellow/red), points (1/0.5/0),
      thresholds (texte), interpretation
    """
    indicators = []

    # 1. Marge nette
    nm = f.get("net_margin")
    if nm is None:
        status, pts, interp = "gray", 0, "Donnée indisponible"
    elif nm > 0.15:
        status, pts, interp = "green", 1, f"Marge nette de {nm*100:.1f}% — l'entreprise possède un fossé économique solide (pricing power)."
    elif nm >= 0.05:
        status, pts, interp = "yellow", 0.5, f"Marge nette de {nm*100:.1f}% — dans la moyenne, pas de signal fort de moat."
    else:
        status, pts, interp = "red", 0, f"Marge nette de {nm*100:.1f}% — faible, l'entreprise lutte sur les prix."
    indicators.append({
        "id": "net_margin",
        "label": "Marge nette",
        "description": "Ce qu'il reste après TOUTES les charges. Plus elle est haute, plus l'entreprise possède un MOAT (avantage concurrentiel) qui lui permet de vendre cher.",
        "value": nm,
        "value_fmt": f"{nm*100:.1f}%" if nm is not None else "—",
        "status": status, "points": pts,
        "thresholds": "🟢 >15%   🟡 5–15%   🔴 <5%",
        "interpretation": interp,
    })

    # 2. Croissance CA 5 ans
    rg = f.get("revenue_cagr_5y")
    if rg is None:
        status, pts, interp = "gray", 0, "Historique insuffisant"
    elif rg > 0.07:
        status, pts, interp = "green", 1, f"Croissance CAGR de {rg*100:.1f}%/an — l'entreprise séduit de nouveaux clients ou augmente ses prix."
    elif rg >= 0.03:
        status, pts, interp = "yellow", 0.5, f"Croissance CAGR de {rg*100:.1f}%/an — modeste, à peine au-dessus de l'inflation."
    else:
        status, pts, interp = "red", 0, f"Croissance CAGR de {rg*100:.1f}%/an — l'entreprise stagne ou décline."
    indicators.append({
        "id": "revenue_growth",
        "label": "Croissance CA (5 ans)",
        "description": "Indique si les produits séduisent de nouveaux clients ou si l'entreprise augmente ses prix. Une croissance régulière est préférable à une explosion suivie d'une chute.",
        "value": rg,
        "value_fmt": f"{rg*100:.1f}%" if rg is not None else "—",
        "status": status, "points": pts,
        "thresholds": "🟢 >7% (PIB+inflation)   🟡 3–7%   🔴 <3%",
        "interpretation": interp,
    })

    # 3. Payout ratio
    pr = f.get("payout_ratio")
    if pr is None:
        status, pts, interp = "gray", 0, "Pas de dividende ou donnée indisponible"
    elif 0.30 <= pr <= 0.60:
        status, pts, interp = "green", 1, f"Payout de {pr*100:.0f}% — équilibre sain entre dividendes et réinvestissement."
    elif pr > 0.80:
        status, pts, interp = "red", 0, f"Payout de {pr*100:.0f}% — l'entreprise s'épuise pour ses actionnaires, peu de réinvestissement."
    elif pr < 0.30 and pr > 0:
        status, pts, interp = "yellow", 0.5, f"Payout de {pr*100:.0f}% — faible, l'entreprise privilégie le réinvestissement (peut être une bonne chose)."
    elif pr == 0:
        status, pts, interp = "yellow", 0.5, "Pas de dividende — entreprise en phase de croissance ou peu de cash redistribué."
    else:  # 60-80%
        status, pts, interp = "yellow", 0.5, f"Payout de {pr*100:.0f}% — élevé mais soutenable."
    indicators.append({
        "id": "payout_ratio",
        "label": "Payout Ratio",
        "description": "Pourcentage du bénéfice net versé en dividendes. Un ratio trop élevé (>80%) peut signifier que l'entreprise n'a plus de projets de croissance.",
        "value": pr,
        "value_fmt": f"{pr*100:.0f}%" if pr is not None else "—",
        "status": status, "points": pts,
        "thresholds": "🟢 30–60%   🟡 0–30% ou 60–80%   🔴 >80%",
        "interpretation": interp,
    })

    # 4. PER (avec contexte qualité/luxe)
    per = f.get("pe_ratio") or f.get("forward_pe")
    is_premium = f.get("is_premium_quality", False)
    if per is None or per <= 0:
        status, pts, interp = "gray", 0, "Bénéfices négatifs ou données indisponibles"
    elif is_premium:
        # Entreprise premium : seuils élargis
        if per <= 40:
            status, pts, interp = "green", 1, f"PER de {per:.1f}x — pour une entreprise de qualité/luxe, valorisation acceptable (jusqu'à 40x toléré)."
        elif per <= 50:
            status, pts, interp = "yellow", 0.5, f"PER de {per:.1f}x — élevé même pour une entreprise premium, attendre une correction."
        else:
            status, pts, interp = "red", 0, f"PER de {per:.1f}x — survalorisation manifeste."
    else:
        # Entreprise standard
        if per <= 18:
            status, pts, interp = "green", 1, f"PER de {per:.1f}x — dans la moyenne historique du marché ou sous-valorisé."
        elif per <= 25:
            status, pts, interp = "yellow", 0.5, f"PER de {per:.1f}x — au-dessus de la moyenne marché, le marché anticipe de la croissance."
        else:
            status, pts, interp = "red", 0, f"PER de {per:.1f}x — élevé sans justification de qualité premium, attention au piège."
    indicators.append({
        "id": "pe_ratio",
        "label": "PER (Price/Earnings)",
        "description": "Multiple que le marché paye pour 1€ de bénéfice. Un PER élevé = anticipation de croissance future. Pour les entreprises de qualité/luxe (marges hautes, ROE élevé), un PER jusqu'à 40x est acceptable.",
        "value": per,
        "value_fmt": f"{per:.1f}x" if per else "—",
        "status": status, "points": pts,
        "thresholds": ("🟢 <40x (qualité)   🟡 40–50x   🔴 >50x" if is_premium
                       else "🟢 <18x (marché)   🟡 18–25x   🔴 >25x"),
        "interpretation": interp + (" [Profil qualité/luxe détecté]" if is_premium else ""),
    })

    # 5. ROE
    roe = f.get("roe")
    if roe is None:
        status, pts, interp = "gray", 0, "Donnée indisponible"
    elif roe > 0.20:
        status, pts, interp = "green", 1, f"ROE de {roe*100:.1f}% — excellence du management, capital actionnaire utilisé efficacement."
    elif roe >= 0.10:
        status, pts, interp = "yellow", 0.5, f"ROE de {roe*100:.1f}% — correct, dans la moyenne."
    else:
        status, pts, interp = "red", 0, f"ROE de {roe*100:.1f}% — faible, capital mal employé ou secteur peu rentable."
    indicators.append({
        "id": "roe",
        "label": "Return on Equity (ROE)",
        "description": "Mesure l'efficacité avec laquelle l'entreprise utilise l'argent des actionnaires pour générer du profit. Indicateur roi pour juger la qualité du management.",
        "value": roe,
        "value_fmt": f"{roe*100:.1f}%" if roe is not None else "—",
        "status": status, "points": pts,
        "thresholds": "🟢 >20%   🟡 10–20%   🔴 <10%",
        "interpretation": interp,
    })

    # 6. Dette nette / EBITDA
    nde = f.get("net_debt_to_ebitda")
    if nde is None:
        status, pts, interp = "gray", 0, "EBITDA indisponible ou nul"
    elif nde < 0:
        status, pts, interp = "green", 1, f"Trésorerie nette positive ({nde:.1f}x) — forteresse financière, peut traverser n'importe quelle crise."
    elif nde <= 2:
        status, pts, interp = "green", 1, f"Dette nette {nde:.1f}x EBITDA — saine, dans la zone de confort des entreprises de qualité."
    elif nde <= 4:
        status, pts, interp = "yellow", 0.5, f"Dette nette {nde:.1f}x EBITDA — endettement modéré à élevé, surveillance nécessaire."
    else:
        status, pts, interp = "red", 0, f"Dette nette {nde:.1f}x EBITDA — endettement excessif, risque en cas de retournement."
    indicators.append({
        "id": "net_debt_ebitda",
        "label": "Dette nette / EBITDA",
        "description": "Combien d'années de profits (EBITDA) il faudrait pour rembourser toute la dette nette. <0 = trésorerie positive (idéal), 0–2 = sain, >4 = risqué.",
        "value": nde,
        "value_fmt": f"{nde:.2f}x" if nde is not None else "—",
        "status": status, "points": pts,
        "thresholds": "🟢 <0 ou ≤2x   🟡 2–4x   🔴 >4x",
        "interpretation": interp,
    })

    # 7. ROIC moyen 5 ans
    roic = f.get("roic_avg_5y")
    roic_min = f.get("roic_min_5y")
    if roic is None:
        status, pts, interp = "gray", 0, "Historique insuffisant pour calculer le ROIC sur 5 ans"
    elif roic > 0.15:
        # Vérifier la constance
        if roic_min is not None and roic_min > 0.10:
            status, pts, interp = "green", 1, f"ROIC moyen de {roic*100:.1f}% (min {roic_min*100:.1f}%) — création de valeur constante, MOAT confirmé."
        else:
            status, pts, interp = "yellow", 0.5, f"ROIC moyen de {roic*100:.1f}% mais creux à {roic_min*100:.1f}% — création de valeur volatile."
    elif roic >= 0.10:
        status, pts, interp = "yellow", 0.5, f"ROIC moyen de {roic*100:.1f}% — couvre tout juste le coût du capital, pas de moat évident."
    else:
        status, pts, interp = "red", 0, f"ROIC moyen de {roic*100:.1f}% — destruction de valeur ou dépendance forte à la dette."
    indicators.append({
        "id": "roic_5y",
        "label": "ROIC moyen 5 ans",
        "description": "Mesure la rentabilité de l'outil industriel/commercial, indépendamment du financement. Un ROIC >15% constant = MOAT empêchant les concurrents de capter cette rentabilité. Si le ROE est haut mais le ROIC bas, l'entreprise est juste levierisée à la dette.",
        "value": roic,
        "value_fmt": f"{roic*100:.1f}%" if roic is not None else "—",
        "status": status, "points": pts,
        "thresholds": "🟢 >15% constant   🟡 10–15%   🔴 <10%",
        "interpretation": interp,
    })

    # 8. FCF / Résultat net
    fcf_ratio = f.get("fcf_to_ni_avg")
    if fcf_ratio is None:
        status, pts, interp = "gray", 0, "Données FCF/Résultat net indisponibles"
    elif fcf_ratio >= 0.80:
        status, pts, interp = "green", 1, f"FCF/RN moyen de {fcf_ratio*100:.0f}% — bénéfices réels, conversion en cash excellente."
    elif fcf_ratio >= 0.50:
        status, pts, interp = "yellow", 0.5, f"FCF/RN moyen de {fcf_ratio*100:.0f}% — typique d'industries capital-intensives, à surveiller."
    else:
        status, pts, interp = "red", 0, f"FCF/RN moyen de {fcf_ratio*100:.0f}% — alerte : les bénéfices ne se transforment pas en cash réel."
    indicators.append({
        "id": "fcf_ni",
        "label": "FCF / Résultat net",
        "description": "Le 'détecteur de mensonges'. Le résultat net est comptable, le FCF est le cash réel. Un ratio >80% = bénéfices réels. Un ratio bas = méfiance, soit l'entreprise réinvestit massivement, soit la rentabilité est artificielle.",
        "value": fcf_ratio,
        "value_fmt": f"{fcf_ratio*100:.0f}%" if fcf_ratio is not None else "—",
        "status": status, "points": pts,
        "thresholds": "🟢 ≥80%   🟡 50–80%   🔴 <50%",
        "interpretation": interp,
    })

    return indicators


def compute_score_and_tier(indicators):
    """
    Score strict : nombre de 🟢 / 🟡 / 🔴.
    Tier basé sur la distribution.
    """
    n_green = sum(1 for i in indicators if i["status"] == "green")
    n_yellow = sum(1 for i in indicators if i["status"] == "yellow")
    n_red = sum(1 for i in indicators if i["status"] == "red")
    n_gray = sum(1 for i in indicators if i["status"] == "gray")
    total_points = sum(i["points"] for i in indicators)
    n_evaluated = 8 - n_gray
    score = round(total_points / 8 * 100, 1) if n_evaluated > 0 else 0

    # Tier basé sur la distribution stricte
    if n_green >= 6 and n_red == 0:
        tier = "EXCELLENTE"
    elif n_green >= 5 and n_red <= 1:
        tier = "BONNE"
    elif n_red >= 5:
        tier = "A_EVITER"
    elif n_red >= 3:
        tier = "FAIBLE"
    else:
        tier = "MOYENNE"

    return {
        "score": score,
        "tier": tier,
        "n_green": n_green,
        "n_yellow": n_yellow,
        "n_red": n_red,
        "n_gray": n_gray,
    }


# ---------------------------------------------------------------------------
# Valorisation
# ---------------------------------------------------------------------------
def dcf_valuation(f, growth_5y=None, wacc=None, terminal_growth=None):
    """DCF avec hypothèses ajustables. Retourne aussi les données pour DCF interactif côté client."""
    fcf = f.get("free_cashflow")
    if not fcf or fcf <= 0:
        fcf_hist = f.get("fcf_history", [])
        positives = [x for x in fcf_hist[:3] if x and x > 0]
        fcf = sum(positives) / len(positives) if positives else None

    if not fcf or fcf <= 0:
        return None

    # Growth par défaut : CAGR revenus borné à 15%
    if growth_5y is None:
        g = f.get("revenue_cagr_5y") or 0.05
        growth_5y = max(0.02, min(0.15, g))

    # WACC par défaut via CAPM
    if wacc is None:
        beta = f.get("beta") or 1.0
        wacc = DEFAULT_RISK_FREE + beta * DEFAULT_EQUITY_PREMIUM
        wacc = max(0.07, min(0.15, wacc))

    if terminal_growth is None:
        terminal_growth = DEFAULT_TERMINAL_GROWTH

    if wacc <= terminal_growth:
        return None

    # Projection FCF 5 ans
    fcf_proj = [fcf * ((1 + growth_5y) ** y) for y in range(1, 6)]
    pv_fcf = sum(cf / ((1 + wacc) ** (i + 1)) for i, cf in enumerate(fcf_proj))

    # Valeur terminale via Gordon
    terminal_fcf = fcf_proj[-1] * (1 + terminal_growth)
    terminal_value = terminal_fcf / (wacc - terminal_growth)
    pv_terminal = terminal_value / ((1 + wacc) ** 5)

    enterprise_value = pv_fcf + pv_terminal

    # Equity = EV - Net Debt
    net_debt = f.get("net_debt", 0)
    equity_value = enterprise_value - net_debt

    shares = f.get("shares_outstanding")
    if not shares:
        price = f.get("price")
        mcap = f.get("market_cap")
        if price and mcap:
            shares = mcap / price
    if not shares or shares <= 0:
        return None

    intrinsic = equity_value / shares
    return {
        "intrinsic_value": round(intrinsic, 2) if intrinsic > 0 else None,
        "fcf_base": round(fcf, 0),
        "growth_5y": round(growth_5y, 4),
        "wacc": round(wacc, 4),
        "terminal_growth": round(terminal_growth, 4),
        "shares_outstanding": int(shares),
        "net_debt": int(net_debt),
        "fcf_projection": [round(x, 0) for x in fcf_proj],
    }


def peg_valuation(f):
    """PER justifié Peter Lynch : PER fair = croissance + dividend yield."""
    eps = f.get("eps_forward") or f.get("eps_ttm")
    if not eps or eps <= 0:
        return None
    growth = cagr(f.get("net_income_history", [])) or cagr(f.get("revenue_history", [])) or 0.05
    if growth <= 0:
        growth = 0.05
    growth_pct = min(30, max(0, growth * 100))
    div_pct = (f.get("dividend_yield") or 0) * 100
    fair_pe = max(8, min(30, growth_pct + div_pct))
    return round(fair_pe * eps, 2)


def graham_valuation(f):
    """Graham Number : √(22.5 × EPS × BookValue)."""
    eps = f.get("eps_ttm")
    bv = f.get("book_value")
    if not eps or not bv or eps <= 0 or bv <= 0:
        return None
    try:
        return round(math.sqrt(22.5 * eps * bv), 2)
    except Exception:
        return None


def intrinsic_value(f):
    dcf = dcf_valuation(f)
    peg = peg_valuation(f)
    graham = graham_valuation(f)

    dcf_val = dcf["intrinsic_value"] if dcf and dcf.get("intrinsic_value") else None
    values = [v for v in [dcf_val, peg, graham] if v and v > 0]
    avg = round(sum(values) / len(values), 2) if values else None

    price = f.get("price")
    margin = (avg - price) / price if avg and price and price > 0 else None

    return {
        "dcf": dcf_val,
        "dcf_data": dcf,  # pour DCF interactif côté client
        "peg_lynch": peg,
        "graham": graham,
        "average": avg,
        "price": price,
        "margin_of_safety": round(margin, 3) if margin is not None else None,
    }


# ---------------------------------------------------------------------------
# Analyse complète
# ---------------------------------------------------------------------------
def analyze_ticker(ticker):
    f = extract_fundamentals(ticker)
    if not f:
        return None

    indicators = evaluate_indicators(f)
    score_data = compute_score_and_tier(indicators)
    valuation = intrinsic_value(f)

    mos = valuation.get("margin_of_safety")
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
        "flag": ticker_to_flag(ticker),
        "name": f.get("name"),
        "sector": f.get("sector"),
        "industry": f.get("industry"),
        "currency": f.get("currency"),
        "price": f.get("price"),
        "market_cap": f.get("market_cap"),
        "is_premium_quality": f.get("is_premium_quality", False),
        "score": score_data["score"],
        "total_score": score_data["score"],  # alias pour compat dashboard existant
        "tier": score_data["tier"],
        "n_green": score_data["n_green"],
        "n_yellow": score_data["n_yellow"],
        "n_red": score_data["n_red"],
        "n_gray": score_data["n_gray"],
        "verdict": verdict,
        "indicators": indicators,
        "valuation": valuation,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Screener Qualité v4")
    parser.add_argument("--universe", default="nasdaq100",
                        help="Slug univers (nasdaq100, stoxx600)")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--output-dir", default=".")
    parser.add_argument("--delay", type=float, default=0.0)
    args = parser.parse_args()

    universe = get_universe(args.universe)
    tickers = universe["tickers"][: args.limit] if args.limit else universe["tickers"]
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_name = args.output or f"results_quality_{args.universe}.json"

    print(f"\n{'='*60}")
    print(f"  Screener Qualité v4 — {universe['label']}")
    print(f"  Scoring strict sur 8 indicateurs fondamentaux")
    print(f"  {len(tickers)} tickers")
    print(f"{'='*60}\n")

    results = []
    for i, t in enumerate(tickers, 1):
        print(f"[{i:3}/{len(tickers)}] {t:12} ", end="", flush=True)
        r = analyze_ticker(t)
        if r:
            results.append(r)
            emoji = {"EXCELLENTE": "⭐⭐⭐", "BONNE": "⭐⭐", "MOYENNE": "⭐",
                     "FAIBLE": "⚠️", "A_EVITER": "❌"}[r["tier"]]
            mos = r["valuation"].get("margin_of_safety")
            mos_str = f"MoS={mos*100:+.0f}%" if mos is not None else "MoS=?"
            print(f"{emoji} {r['n_green']}🟢{r['n_yellow']}🟡{r['n_red']}🔴 score={r['score']:5.1f}  {mos_str}")
        else:
            print("—")
        if args.delay > 0:
            time.sleep(args.delay)

    results.sort(key=lambda x: x["score"], reverse=True)

    output = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "type": "quality",
        "version": "v4-strict",
        "universe": args.universe,
        "universe_label": universe["label"],
        "count": len(results),
        "results": results,
    }
    
    # Nettoyage JSON : remplacer NaN/Infinity (invalides en JSON standard) par null
    def clean_json(obj):
        if isinstance(obj, dict):
            return {k: clean_json(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [clean_json(v) for v in obj]
        if isinstance(obj, float):
            if obj != obj or obj == float('inf') or obj == float('-inf'):
                return None
        return obj
    output = clean_json(output)

    out_path = out_dir / out_name
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False, default=str))

    excellent = [r for r in results if r["tier"] == "EXCELLENTE"]
    print(f"\n  ⭐⭐⭐ Excellentes : {len(excellent):3}  {[r['ticker'] for r in excellent[:10]]}")
    print(f"  ✓ Écrit dans {out_path.absolute()}\n")


if __name__ == "__main__":
    main()