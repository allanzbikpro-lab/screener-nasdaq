"""
Univers d'actions - listes de tickers
======================================
Chaque univers associe un identifiant (slug) à une liste de tickers yfinance.
- US : tickers simples (AAPL, MSFT...)
- EU : tickers avec suffixe bourse (.PA Paris, .DE Xetra, .AS Amsterdam,
       .MI Milan, .MC Madrid, .SW Zurich, .L Londres, .ST Stockholm,
       .BR Bruxelles, .CO Copenhague, .HE Helsinki, .OL Oslo, .IR Irlande)
"""

# ---------------------------------------------------------------------------
# NASDAQ 100 (US)
# ---------------------------------------------------------------------------
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
# STOXX EUROPE 600 - Principales composantes
# ---------------------------------------------------------------------------
# Liste ~600 tickers des plus grandes caps européennes cotées sur leurs
# marchés principaux. La composition exacte du STOXX 600 change, mais cette
# liste couvre la grande majorité des constituants sur la durée.
STOXX600 = [
    # FRANCE (.PA) - 75 tickers
    "MC.PA", "OR.PA", "RMS.PA", "TTE.PA", "SAN.PA", "AIR.PA", "SU.PA", "CDI.PA",
    "BNP.PA", "DG.PA", "BN.PA", "CS.PA", "SAF.PA", "EL.PA", "ENGI.PA", "KER.PA",
    "VIE.PA", "RI.PA", "ACA.PA", "CA.PA", "GLE.PA", "STM.PA", "ML.PA", "ORA.PA",
    "PUB.PA", "HO.PA", "LR.PA", "VIV.PA", "RNO.PA", "ATO.PA", "ALO.PA", "FP.PA",
    "SGO.PA", "FR.PA", "LI.PA", "EN.PA", "PUB.PA", "UG.PA", "STLA.PA", "EDEN.PA",
    "EDF.PA", "GFC.PA", "DSY.PA", "TEP.PA", "SW.PA", "BVI.PA", "NK.PA", "GLE.PA",
    "BOL.PA", "IPN.PA", "URW.AS", "ERF.PA", "WLN.PA", "CAP.PA", "SOP.PA", "RXL.PA",
    "FDJ.PA", "AMUN.PA", "ICAD.PA", "EXE.PA", "FGR.PA", "COV.PA", "SEB.PA", "RCO.PA",
    "CNP.PA", "KOF.PA", "SOI.PA", "AKE.PA", "BIM.PA", "DBG.PA", "EO.PA", "SCR.PA",
    "ALD.PA", "CGG.PA", "TRI.PA", "VK.PA",

    # ALLEMAGNE (.DE) - 70 tickers
    "SAP.DE", "SIE.DE", "ALV.DE", "DTE.DE", "MBG.DE", "MUV2.DE", "BAS.DE", "BMW.DE",
    "IFX.DE", "BAYN.DE", "DBK.DE", "ADS.DE", "VOW3.DE", "DB1.DE", "DHL.DE", "RWE.DE",
    "EOAN.DE", "HEN3.DE", "DPW.DE", "BEI.DE", "FRE.DE", "HEI.DE", "CON.DE", "FME.DE",
    "PAH3.DE", "MRK.DE", "RHM.DE", "SHL.DE", "MTX.DE", "ENR.DE", "VNA.DE", "SY1.DE",
    "PUM.DE", "DWNI.DE", "BOSS.DE", "AIXA.DE", "SRT3.DE", "TKA.DE", "SZG.DE", "DUE.DE",
    "HOT.DE", "NEM.DE", "LEG.DE", "HNR1.DE", "EVK.DE", "LXS.DE", "UN01.DE", "KGX.DE",
    "G1A.DE", "GIL.DE", "PSM.DE", "AFX.DE", "KRN.DE", "QIA.DE", "TEG.DE", "LIN.DE",
    "NDA.DE", "WDI.DE", "SOW.DE", "COP.DE", "JUN3.DE", "CBK.DE", "GXI.DE", "TUI1.DE",
    "SDF.DE", "OSR.DE", "WAF.DE", "ZAL.DE", "HLAG.DE", "HYQ.DE",

    # PAYS-BAS (.AS) - 30 tickers
    "ASML.AS", "PRX.AS", "HEIA.AS", "UNA.AS", "ADYEN.AS", "INGA.AS", "WKL.AS",
    "PHIA.AS", "AD.AS", "DSM.AS", "KPN.AS", "AKZA.AS", "REN.AS", "NN.AS", "MT.AS",
    "ASRNL.AS", "ABN.AS", "IMCD.AS", "RAND.AS", "AGN.AS", "BESI.AS", "AALB.AS",
    "GLPG.AS", "AMG.AS", "LIGHT.AS", "BFIT.AS", "ASM.AS", "TKWY.AS", "FAGR.AS",
    "CTP.AS",

    # SUISSE (.SW) - 40 tickers
    "NESN.SW", "ROG.SW", "NOVN.SW", "ZURN.SW", "UBSG.SW", "ABBN.SW", "CFR.SW",
    "LONN.SW", "SIKA.SW", "GIVN.SW", "SREN.SW", "GEBN.SW", "HOLN.SW", "ALC.SW",
    "BAER.SW", "KNIN.SW", "SCMN.SW", "SLHN.SW", "STMN.SW", "LOGN.SW", "UHR.SW",
    "SGSN.SW", "PGHN.SW", "SCHN.SW", "SOON.SW", "SCHP.SW", "ADEN.SW", "EMSN.SW",
    "AMS.SW", "LISN.SW", "SUN.SW", "SQN.SW", "VACN.SW", "BALN.SW", "TEMN.SW",
    "GF.SW", "BCGE.SW", "FHZN.SW", "BCVN.SW", "PSPN.SW",

    # ROYAUME-UNI (.L) - 90 tickers
    "AZN.L", "SHEL.L", "HSBA.L", "ULVR.L", "BP.L", "GSK.L", "RIO.L", "BATS.L",
    "RELX.L", "LSEG.L", "DGE.L", "LLOY.L", "NWG.L", "BARC.L", "BA.L", "CPG.L",
    "NG.L", "TSCO.L", "PRU.L", "AAL.L", "GLEN.L", "VOD.L", "IMB.L", "III.L",
    "STAN.L", "HLN.L", "LGEN.L", "REL.L", "EXPN.L", "ABF.L", "FLTR.L", "CNA.L",
    "BKG.L", "ANTO.L", "ADM.L", "INF.L", "SMIN.L", "ENT.L", "JD.L", "PSON.L",
    "WTB.L", "BT-A.L", "NXT.L", "DCC.L", "UU.L", "SVT.L", "AV.L", "SGRO.L",
    "SSE.L", "MKS.L", "SPX.L", "WEIR.L", "IHG.L", "CRH.L", "KGF.L", "LAND.L",
    "FRES.L", "BNZL.L", "HL.L", "ICG.L", "IAG.L", "ITRK.L", "ITV.L", "PHNX.L",
    "RTO.L", "SBRY.L", "SDR.L", "SGE.L", "TW.L", "HIK.L", "BLND.L", "PSH.L",
    "BEZ.L", "OCDO.L", "WPP.L", "ABDN.L", "MNDI.L", "BME.L", "BT-A.L", "SMT.L",
    "AHT.L", "MGGT.L", "RR.L", "HWDN.L", "BRBY.L", "AUTO.L", "AV.L", "IMI.L",
    "HSX.L",

    # ITALIE (.MI) - 40 tickers
    "ENI.MI", "ISP.MI", "UCG.MI", "ENEL.MI", "G.MI", "RACE.MI", "STLAM.MI",
    "STM.MI", "TEN.MI", "LDO.MI", "CPR.MI", "MB.MI", "MONC.MI", "POST.MI",
    "TRN.MI", "ATL.MI", "A2A.MI", "DIA.MI", "SPM.MI", "BAMI.MI", "BPE.MI",
    "UBI.MI", "AZM.MI", "AMP.MI", "SRG.MI", "ERG.MI", "BMED.MI", "FBK.MI",
    "REC.MI", "TIT.MI", "IG.MI", "CNHI.MI", "PIRC.MI", "HER.MI", "SFER.MI",
    "ENAV.MI", "BC.MI", "WBD.MI", "MS.MI", "TOD.MI",

    # ESPAGNE (.MC) - 30 tickers
    "IBE.MC", "ITX.MC", "SAN.MC", "BBVA.MC", "TEF.MC", "ELE.MC", "CABK.MC",
    "AENA.MC", "FER.MC", "REP.MC", "ACS.MC", "AMS.MC", "MAP.MC", "IAG.MC",
    "NTGY.MC", "ANA.MC", "RED.MC", "GRF.MC", "ENG.MC", "VIS.MC", "BKT.MC",
    "ACX.MC", "CLNX.MC", "MEL.MC", "MRL.MC", "SCYR.MC", "COL.MC", "IDR.MC",
    "SLR.MC", "LOG.MC",

    # SUÈDE (.ST) - 35 tickers
    "ATCO-A.ST", "INVE-B.ST", "VOLV-B.ST", "ERIC-B.ST", "HM-B.ST", "SAND.ST",
    "ASSA-B.ST", "SEB-A.ST", "HEXA-B.ST", "ABB.ST", "EQT.ST", "SKF-B.ST",
    "SWED-A.ST", "TELIA.ST", "SCA-B.ST", "BOL.ST", "SHB-A.ST", "ESSITY-B.ST",
    "EVO.ST", "NDA-SE.ST", "ALFA.ST", "ALIV-SDB.ST", "AZN.ST", "EPI-A.ST",
    "GETI-B.ST", "HUSQ-B.ST", "ICA.ST", "KINV-B.ST", "LATO-B.ST", "LIFCO-B.ST",
    "LUMI.ST", "SAAB-B.ST", "TELIA.ST", "TIGO-SDB.ST", "NIBE-B.ST",

    # DANEMARK (.CO) - 20 tickers
    "NOVO-B.CO", "ORSTED.CO", "DSV.CO", "MAERSK-B.CO", "CARL-B.CO", "DANSKE.CO",
    "VWS.CO", "GN.CO", "COLO-B.CO", "PNDORA.CO", "ISS.CO", "DEMANT.CO",
    "TRYG.CO", "AMBU-B.CO", "GMAB.CO", "CHR.CO", "FLS.CO", "JYSK.CO",
    "NETC.CO", "BAVA.CO",

    # FINLANDE (.HE) - 18 tickers
    "NOKIA.HE", "KNEBV.HE", "SAMPO.HE", "FORTUM.HE", "NESTE.HE", "UPM.HE",
    "STERV.HE", "WRT1V.HE", "KESKOB.HE", "OUT1V.HE", "METSO.HE", "CGCBV.HE",
    "TIETO.HE", "ELISA.HE", "ORNBV.HE", "HUH1V.HE", "FSKRS.HE", "QTCOM.HE",

    # NORVÈGE (.OL) - 20 tickers
    "EQNR.OL", "DNB.OL", "TEL.OL", "MOWI.OL", "AKRBP.OL", "YAR.OL", "NHY.OL",
    "ORK.OL", "SUBC.OL", "KOG.OL", "SALM.OL", "AKER.OL", "GJF.OL", "STB.OL",
    "LSG.OL", "REC.OL", "TOM.OL", "SCHA.OL", "WALWIL.OL", "NEL.OL",

    # BELGIQUE (.BR) - 18 tickers
    "ABI.BR", "UCB.BR", "KBC.BR", "GBLB.BR", "SOLB.BR", "ACKB.BR", "UMI.BR",
    "PROX.BR", "COLR.BR", "AED.BR", "COFB.BR", "ONTEX.BR", "WDP.BR",
    "BPOST.BR", "ARGX.BR", "AGS.BR", "ELI.BR", "LOTB.BR",

    # IRLANDE (.IR) - 10 tickers
    "CRH.IR", "RYA.IR", "KRX.IR", "BIRG.IR", "KRZ.IR", "FBD.IR", "GL9.IR",
    "GRP.IR", "GVR.IR", "PPA.IR",

    # AUTRICHE (.VI) - 10 tickers
    "OMV.VI", "VOE.VI", "EBS.VI", "RBI.VI", "VIG.VI", "VER.VI", "ANDR.VI",
    "POST.VI", "UQA.VI", "MMK.VI",

    # PORTUGAL (.LS) - 5 tickers
    "GALP.LS", "EDP.LS", "JMT.LS", "NOS.LS", "SON.LS",
]

# Déduplication (certains tickers peuvent apparaître deux fois)
STOXX600 = list(dict.fromkeys(STOXX600))


# ---------------------------------------------------------------------------
# Dictionnaire des univers
# ---------------------------------------------------------------------------
UNIVERSES = {
    "nasdaq100": {
        "label": "Nasdaq 100 🇺🇸",
        "flag": "🇺🇸",
        "currency": "USD",
        "tickers": NASDAQ100,
    },
    "stoxx600": {
        "label": "STOXX Europe 600 🇪🇺",
        "flag": "🇪🇺",
        "currency": "EUR",  # Principale, mais certaines GBP/CHF/SEK etc.
        "tickers": STOXX600,
    },
}


def get_universe(slug):
    """Retourne la config d'un univers."""
    if slug not in UNIVERSES:
        raise ValueError(f"Univers inconnu : {slug}. Disponibles : {list(UNIVERSES.keys())}")
    return UNIVERSES[slug]


def ticker_to_flag(ticker):
    """Déduit le drapeau pays depuis le ticker."""
    if "." not in ticker:
        return "🇺🇸"  # US par défaut
    suffix = ticker.split(".")[-1].upper()
    mapping = {
        "PA": "🇫🇷", "DE": "🇩🇪", "AS": "🇳🇱", "SW": "🇨🇭", "L": "🇬🇧",
        "MI": "🇮🇹", "MC": "🇪🇸", "ST": "🇸🇪", "CO": "🇩🇰", "HE": "🇫🇮",
        "OL": "🇳🇴", "BR": "🇧🇪", "IR": "🇮🇪", "VI": "🇦🇹", "LS": "🇵🇹",
    }
    return mapping.get(suffix, "🇪🇺")
