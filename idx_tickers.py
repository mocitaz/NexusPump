# List of major liquid stocks in IDX (LQ45 / IDX80 proxy)
# Scanning thousands of stocks is not feasible with free yfinance due to rate limits.
# We focus on the top ~60-100 most active stocks.

IDX_WATCHLIST = [
    # Banking (Big Caps)
    "BBCA", "BBRI", "BMRI", "BBNI", "BRIS", "BBTN", "BDMN", "BNGA",
    
    # Telco & Tech
    "TLKM", "ISAT", "EXCL", "GOTO", "MTDL", "EMTK", "SCMA", "BUKA",
    
    # Consumer & Retail
    "ICBP", "INDF", "UNVR", "MYOR", "AMRT", "MAPI", "ACES", "ERAA", "KLBF", "TSPC", "SIDO",
    
    # Energy & Mining (Coal, Gold, Nickel)
    "ADRO", "PTBA", "ITMG", "HRUM", "INDY", "BUMI", "ADMR",
    "ANTM", "INCO", "MDKA", "MBMA", "TINS", "PSAB", "NCKL", "ARCHI",
    
    # Oil & Gas / Petro
    "AKRA", "MEDC", "PGAS", "BRPT", "TPIA", "ESSA",
    
    # Pulp & Paper
    "INKP", "TKIM",
    
    # Construction & Cement & Infra
    "SMGR", "INTP", "JSMR", "PTPP", "WIKA", "ADHI",
    
    # Property
    "BSDE", "CTRA", "PWON", "SMRA", "ASRI",
    
    # Automotive / Diversified
    "ASII", "AUTO", "IMAS",
    
    # Others / Commodities
    "CPIN", "JPFA", "TAPG", "DSNG", "LSIP", "AALI"
]

# Helper to get full ticker format
def get_all_tickers():
    return [f"{t}.JK" for t in IDX_WATCHLIST]
