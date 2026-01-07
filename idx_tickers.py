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
    "ANTM", "INCO", "MDKA", "MBMA", "TINS", "PSAB", "NCKL",
    
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

def get_all_tickers():
    return [f"{t}.JK" for t in IDX_WATCHLIST]

# V26: Sector Mapping
SECTOR_MAP = {
    "FINANCE": ["BBCA", "BBRI", "BMRI", "BBNI", "BRIS", "BBTN", "BDMN", "BNGA"],
    "TECHNOLOGY": ["GOTO", "EMTK", "SCMA", "BUKA", "MTDL"],
    "INFRA & TELCO": ["TLKM", "ISAT", "EXCL", "JSMR", "PGAS"],
    "ENERGY": ["ADRO", "PTBA", "ITMG", "HRUM", "INDY", "BUMI", "ADMR", "AKRA", "MEDC"],
    "BASIC MAT": ["ANTM", "INCO", "MDKA", "MBMA", "TINS", "PSAB", "NCKL", "INKP", "TKIM", "BRPT", "TPIA", "ESSA"],
    "CONSUMER": ["ICBP", "INDF", "UNVR", "MYOR", "AMRT", "MAPI", "ACES", "KLBF", "SIDO", "CPIN", "JPFA"],
    "PROPERTY": ["BSDE", "CTRA", "PWON", "SMRA", "ASRI"],
    "AUTO & IND": ["ASII", "AUTO", "IMAS", "SMGR", "INTP", "UNTR"]
}
