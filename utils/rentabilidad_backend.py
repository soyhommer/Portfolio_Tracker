import pandas as pd
import numpy as np
from utils.config import (
    get_transactions_path,
    NAV_HISTORICO_DIR,
    get_benchmark_path,
)
from utils.historial_nav import cargar_historico_isin
# =========================================
#  DATA ACCESS LAYER
# =========================================
def load_transactions_raw(portfolio_name):
    """
    Loads raw transactions CSV for a specific portfolio.
    """
    path = get_transactions_path(portfolio_name)
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame(columns=[
        "Posición", "Tipo", "Participaciones",
        "Fecha", "Moneda", "Precio", "Gasto"
    ])

#Data Acces Layer
def load_transactions_clean(portfolio_name):
    """
    Loads and cleans transactions for analysis.
    """
    df = load_transactions_raw(portfolio_name)
    if df.empty:
        return df

    cols_needed = ["ISIN", "Tipo", "Participaciones", "Fecha", "Precio", "Gasto"]
    df = df[[col for col in cols_needed if col in df.columns]].copy()
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    df = df.dropna(subset=["Fecha", "ISIN", "Participaciones"])
    df = df.sort_values("Fecha").reset_index(drop=True)
    return df

#Data Access Layer
def load_all_navs(isin_list, df_transactions):
    """
    Loads NAV histories for given ISINs, fills gaps to cover entire date range.
    """
    nav_frames = []
    full_range = pd.date_range(df_transactions["Fecha"].min(), pd.Timestamp.today(), freq="D")

    for isin in isin_list:
        df_nav = cargar_historico_isin(isin)
        if df_nav.empty:
            continue
        df_nav["Fecha"] = pd.to_datetime(df_nav["Date"], errors="coerce")
        df_nav = df_nav.dropna(subset=["Fecha"])
        df_nav = df_nav[["Fecha", "Price"]].copy()
        df_nav["ISIN"] = isin

        # Fill to full date range
        df_nav = fill_nav_series(df_nav, pd.Timestamp.today())
        nav_frames.append(df_nav)

    if nav_frames:
        df_navs = pd.concat(nav_frames, ignore_index=True)
        return df_navs.dropna(subset=["Price"])
    return pd.DataFrame(columns=["Fecha", "ISIN", "Price"])

#Data Access Layer
def find_closest_nav_price(df, target_date, price_column="Price", tolerance_days=30):
    if df.empty:
        return None, None

    df = df.reset_index().rename(columns={"Fecha": "DateIndex"})
    df["Diff"] = (df["DateIndex"] - target_date).abs()

    df = df[df["Diff"] <= pd.Timedelta(days=tolerance_days)]
    if df.empty:
        return None, None

    closest_row = df.sort_values("Diff").iloc[0]
    return closest_row["DateIndex"], closest_row[price_column]


#Data Access Layer
def fill_nav_series(df_nav, today):
    """
    Forward-fills NAV only from first available NAV date to today.
    No extrapolation before first NAV.
    """
    if df_nav.empty:
        return pd.DataFrame(columns=["Fecha", "ISIN", "Price"])
    
    first_date = df_nav["Fecha"].min()
    date_range = pd.date_range(first_date, today, freq="D")
    
    isin = df_nav["ISIN"].iloc[0]
    df_nav = df_nav.set_index("Fecha").sort_index()
    df_nav = df_nav.reindex(date_range)
    df_nav["ISIN"] = isin
    df_nav["Price"] = df_nav["Price"].fillna(method="ffill")
    return df_nav.reset_index().rename(columns={"index": "Fecha"})


#Data Acces Layer
def load_portfolio_benchmark(portfolio_name: str) -> pd.DataFrame:
    """
    Loads benchmark time series CSV for a given portfolio.
    """
    path = get_benchmark_path(portfolio_name)
    if path.exists():
        df = pd.read_csv(path)
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
        return df.dropna(subset=["Fecha"])
    return pd.DataFrame(columns=["Fecha", "BenchmarkValue"])

# =========================================
#  POSITION AND VALUATION LAYER
# =========================================

def build_holdings_over_time(df_transactions):
    if df_transactions.empty:
        return pd.DataFrame(columns=["Fecha", "ISIN", "Participaciones"])

    holdings_list = []
    for isin in df_transactions["ISIN"].unique():
        df_isin = df_transactions[df_transactions["ISIN"] == isin].copy()
        df_isin["Delta"] = df_isin.apply(
            lambda row: row["Participaciones"] if row["Tipo"] == "Compra" else -row["Participaciones"],
            axis=1
        )
        df_isin = df_isin.groupby("Fecha")["Delta"].sum().cumsum().reset_index()
        df_isin["ISIN"] = isin

        # Extend to today
        date_range = pd.date_range(df_isin["Fecha"].min(), pd.Timestamp.today(), freq="D")
        df_all = pd.DataFrame({"Fecha": date_range})
        df_all = df_all.merge(df_isin, on="Fecha", how="left")
        df_all["Delta"] = df_all["Delta"].fillna(method="ffill").fillna(0)
        df_all["ISIN"] = isin
        df_all.rename(columns={"Delta": "Participaciones"}, inplace=True)

        holdings_list.append(df_all[["Fecha", "ISIN", "Participaciones"]])

    df_holdings = pd.concat(holdings_list, ignore_index=True)
    df_holdings["Fecha"] = pd.to_datetime(df_holdings["Fecha"])
    return df_holdings

    
#Position and Valuation Layer
def compute_portfolio_valuation(df_holdings: pd.DataFrame, df_navs: pd.DataFrame) -> pd.DataFrame:
    
    """
    Merges holdings with NAV data to produce daily total portfolio value.
    Returns DataFrame with Fecha, PortfolioValue.
    """
    
    
    if df_holdings.empty or df_navs.empty:
        return pd.DataFrame(columns=["Fecha", "PortfolioValue"])

    df = pd.merge(df_holdings, df_navs, on=["Fecha", "ISIN"], how="left")
    df = df.dropna(subset=["Price"])
    df["Valor"] = df["Participaciones"] * df["Price"]
    df_portfolio = df.groupby("Fecha")["Valor"].sum().reset_index()
    df_portfolio.rename(columns={"Valor": "PortfolioValue"}, inplace=True)
    return df_portfolio

# =========================================
#  CASHFLOW LAYER
# =========================================

def extract_cash_flows(df_transactions: pd.DataFrame) -> pd.DataFrame:
    """
    From transaction records, extract net external cash flows over time.
    Compra = negative cash flow.
    Venta = positive cash flow.
    Includes Gasto.
    Returns DataFrame with Fecha, CashFlowAmount.
    """
    if df_transactions.empty:
        return pd.DataFrame(columns=["Fecha", "CashFlowAmount"])

    df = df_transactions.copy()
    #df["Sign"] = df["Tipo"].apply(lambda x: 1 if "Venta" in x else -1)
    df["Sign"] = df["Tipo"].apply(lambda x: 1 if x.lower().startswith("venta") else -1)
    df["CashFlowAmount"] = df["Sign"] * (df["Participaciones"] * df["Precio"] + df.get("Gasto", 0))
    df = df[["Fecha", "CashFlowAmount"]]
    df = df.groupby("Fecha").sum().reset_index()
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    return df

# Cashflow layer   
def compute_cumulative_cash_flows(df_cash_flows):
    """
    Computes cumulative invested cash over time.
    """
    if df_cash_flows.empty:
        return pd.DataFrame(columns=["Fecha", "CumulativeInvestment"])
    
    df_cash_flows = df_cash_flows.sort_values("Fecha")
    df_cash_flows["CumulativeInvestment"] = df_cash_flows["CashFlowAmount"].cumsum()
    return df_cash_flows[["Fecha", "CumulativeInvestment"]]

# Cashflow layer  
def extract_investment_flows(df_transactions):
    """
    For cumulative invested capital: Compra = positive, Venta = negative.
    """
    if df_transactions.empty:
        return pd.DataFrame(columns=["Fecha", "InvestmentFlow"])
    
    df = df_transactions.copy()
    df["Sign"] = df["Tipo"].apply(lambda x: 1 if x.lower().startswith("compra") else -1)
    df["InvestmentFlow"] = df["Sign"] * (df["Participaciones"] * df["Precio"] + df.get("Gasto", 0))
    df = df[["Fecha", "InvestmentFlow"]]
    df = df.groupby("Fecha").sum().reset_index()
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    return df

# Cashflow layer  
def compute_cumulative_investment(df_investment_flows, start_date, end_date):
    """
    Expands investment flows to daily series and sums to get cumulative invested capital over time.
    """
    if df_investment_flows.empty:
        return pd.DataFrame(columns=["Fecha", "CumulativeInvestment"])
    
    # Build full daily index
    full_range = pd.date_range(start_date, end_date, freq="D")
    df_investment_flows = df_investment_flows.set_index("Fecha").reindex(full_range).fillna(0).reset_index()
    df_investment_flows = df_investment_flows.rename(columns={"index": "Fecha"})
    
    # Cumulative sum
    df_investment_flows["CumulativeInvestment"] = df_investment_flows["InvestmentFlow"].cumsum()
    return df_investment_flows[["Fecha", "CumulativeInvestment"]]

   
# =========================================
#  RENTABILIDAD CALCULATIONS LAYER
# =========================================

def calculate_twr(df_portfolio_value, df_cash_flows):
    """
    Calculates true TWR by removing effect of external cash flows.
    """
    if df_portfolio_value.empty:
        return pd.DataFrame(columns=["Fecha", "TWR"])
    
    df_pv = df_portfolio_value.copy().sort_values("Fecha")
    df_cf = df_cash_flows.copy().sort_values("Fecha")
    
    # Identify cash flow dates
    flow_dates = set(df_cf["Fecha"])
    
    # Initialize
    df_pv["TWR"] = np.nan
    cumulative_twr = 1.0
    last_value = None
    
    twr_series = []
    
    for idx, row in df_pv.iterrows():
        date = row["Fecha"]
        value = row["PortfolioValue"]
        
        if last_value is not None:
            if date in flow_dates:
                # Cash flow → reset sub-period
                last_value = value
            else:
                sub_return = (value - last_value) / last_value
                cumulative_twr *= (1 + sub_return)
                last_value = value
        else:
            last_value = value
        
        twr_series.append((date, cumulative_twr - 1))
    
    df_twr = pd.DataFrame(twr_series, columns=["Fecha", "TWR"])
    df_twr["TWR"] = df_twr["TWR"] * 100
    return df_twr

#Rentabilidad Calculations Layer
def resample_twr_series(df_twr, freq="W"):
    """
    Resamples TWR series to weekly or monthly frequency.
    """
    return df_twr.set_index("Fecha").resample(freq).last().dropna().reset_index()


#Rentabilidad Calculations Layer
import numpy as np

def calculate_mwr(df_portfolio_value: pd.DataFrame, df_cash_flows: pd.DataFrame) -> float:
    """
    Computes annualized Money-Weighted Return (IRR/XIRR) over period.
    Returns single float %.
    """
    if df_cash_flows.empty or df_portfolio_value.empty:
        return 0.0

    df = pd.merge(df_cash_flows, df_portfolio_value, on="Fecha", how="outer").fillna(0)
    df = df.sort_values("Fecha")

    # Add ending value as final cash flow in
    df.loc[df.index[-1], "CashFlowAmount"] += df["PortfolioValue"].iloc[-1]

    # Build cash flows series
    cash_flows = df["CashFlowAmount"].values
    days = (df["Fecha"] - df["Fecha"].min()).dt.days.values / 365.25

    def xnpv(rate, cashflows, times):
        return np.sum(cashflows / (1 + rate) ** times)

    def xirr(cashflows, times, guess=0.1):
        try:
            from scipy.optimize import newton
        except ImportError:
            raise ImportError("scipy is required for XIRR calculation. Please install it with 'pip install scipy'.")
        try:
            return newton(lambda r: xnpv(r, cashflows, times), guess)
        except Exception:
            return None

    irr = xirr(cash_flows, days)
    if irr is None:
        return 0.0

    return irr * 100  # percentage

#Rentabilidad Calculations Layer
def calculate_mwr_series(df_portfolio_value, df_cash_flows):
    """
    Computes Money-Weighted Return (IRR/XIRR) only on dates with cash flows.
    Returns step series with Fecha, MWR (%).
    """
    import numpy as np

    if df_cash_flows.empty or df_portfolio_value.empty:
        return pd.DataFrame(columns=["Fecha", "MWR"])

    df_pv = df_portfolio_value.copy().sort_values("Fecha")
    df_cf = df_cash_flows.copy().sort_values("Fecha")
    
    # Identify all dates with any cash flow
    flow_dates = sorted(set(df_cf["Fecha"]) | set([df_pv["Fecha"].max()]))

    results = []

    last_irr = None

    for today in flow_dates:
        # Select cash flows up to today
        df_cf_until = df_cf[df_cf["Fecha"] <= today].copy()
        if df_cf_until.empty:
            continue

        # Add portfolio value as final cash flow
        value_today = df_pv[df_pv["Fecha"] == today]["PortfolioValue"].values[0]
        df_cf_until = pd.concat([
            df_cf_until,
            pd.DataFrame({"Fecha": [today], "CashFlowAmount": [value_today]})
        ], ignore_index=True)
        
        df_cf_until = df_cf_until.sort_values("Fecha")
        times = (df_cf_until["Fecha"] - df_cf_until["Fecha"].min()).dt.days.values / 365.25
        cash_flows = df_cf_until["CashFlowAmount"].values

        def xnpv(rate, cashflows, times):
            return np.sum(cashflows / (1 + rate) ** times)
        
        def xirr(cashflows, times, guess=0.1):
            from scipy.optimize import newton
            try:
                return newton(lambda r: xnpv(r, cashflows, times), guess)
            except Exception:
                return None

        irr = xirr(cash_flows, times)
        if irr is not None:
            last_irr = irr * 100

        results.append({"Fecha": today, "MWR": last_irr})

    # Forward-fill to all dates
    df_result = pd.DataFrame(results).sort_values("Fecha")
    df_result = df_result.set_index("Fecha").reindex(df_pv["Fecha"]).fillna(method="ffill").reset_index()
    df_result.rename(columns={"index": "Fecha"}, inplace=True)

    return df_result

#Rentabilidad Calculations Layer
def calculate_mwr_series_weekly(df_portfolio_value, df_cash_flows):
    """
    Computes MWR (IRR/XIRR) on a weekly rolling basis.
    Returns DataFrame with Fecha, MWR (%).
    """
    import numpy as np

    if df_cash_flows.empty or df_portfolio_value.empty:
        return pd.DataFrame(columns=["Fecha", "MWR"])
    
    df_pv = df_portfolio_value.copy().sort_values("Fecha")
    df_cf = df_cash_flows.copy().sort_values("Fecha")
    
    # Resample portfolio value to weekly
    df_pv_weekly = df_pv.set_index("Fecha").resample("W").last().dropna().reset_index()
    
    results = []

    for today in df_pv_weekly["Fecha"]:
        # Select all cash flows up to this week
        df_cf_until = df_cf[df_cf["Fecha"] <= today].copy()
        if df_cf_until.empty:
            continue

        # Add portfolio value as cash flow
        value_today = df_pv[df_pv["Fecha"] == today]["PortfolioValue"]
        if value_today.empty:
            value_today = df_pv[df_pv["Fecha"] <= today]["PortfolioValue"].iloc[-1]
        
        df_cf_until = pd.concat([
            df_cf_until,
            pd.DataFrame({"Fecha": [today], "CashFlowAmount": [value_today]})
        ], ignore_index=True)
        
        df_cf_until = df_cf_until.sort_values("Fecha")
        times = (df_cf_until["Fecha"] - df_cf_until["Fecha"].min()).dt.days.values / 365.25
        cash_flows = df_cf_until["CashFlowAmount"].values

        def xnpv(rate, cashflows, times):
            return np.sum(cashflows / (1 + rate) ** times)
        
        def xirr(cashflows, times, guess=0.1):
            from scipy.optimize import newton
            try:
                return newton(lambda r: xnpv(r, cashflows, times), guess)
            except Exception:
                return None

        irr = xirr(cash_flows, times)
        if irr is not None:
            results.append({"Fecha": today, "MWR": irr * 100})

    return pd.DataFrame(results)

# def calculate_periodic_mwr_series(df_portfolio_value, df_cash_flows, freq="W"):
    # """
    # Computes periodic (weekly/monthly) Money-Weighted Return (IRR) series.
    # """
    # import numpy as np

    # if df_cash_flows.empty or df_portfolio_value.empty:
        # return pd.DataFrame(columns=["Fecha", "MWR"])

    # # Resample to period end
    # df_pv_period = df_portfolio_value.set_index("Fecha").resample(freq).last().dropna().reset_index()
    # df_cf_period = df_cash_flows.set_index("Fecha").resample(freq).sum().reset_index()

    # results = []

    # for i in range(1, len(df_pv_period)):
        # start_date = df_pv_period.loc[i-1, "Fecha"]
        # end_date = df_pv_period.loc[i, "Fecha"]
        # valor_inicial = df_pv_period.loc[i-1, "PortfolioValue"]
        # valor_final = df_pv_period.loc[i, "PortfolioValue"]

        # # Filter cash flows in the period
        # mask = (df_cf_period["Fecha"] > start_date) & (df_cf_period["Fecha"] <= end_date)
        # flujos = df_cf_period[mask]["CashFlowAmount"].sum() if not df_cf_period[mask].empty else 0.0

        # # Build cash flow series
        # cash_flows = [-valor_inicial]
        # if flujos != 0:
            # cash_flows.append(flujos)
        # cash_flows.append(valor_final)

        # times = np.linspace(0, 1, len(cash_flows))

        # def xnpv(rate, cashflows, times):
            # return np.sum(cashflows / (1 + rate) ** times)

        # def xirr(cashflows, times, guess=0.1):
            # from scipy.optimize import newton
            # try:
                # return newton(lambda r: xnpv(r, cashflows, times), guess)
            # except Exception:
                # return None

        # irr = xirr(cash_flows, times)
        # if irr is not None:
            # results.append({"Fecha": end_date, "MWR": irr * 100})

    # return pd.DataFrame(results)

#Rentabilidad Calculations Layer
def calculate_mwr_accumulated_series(df_portfolio_value, df_cash_flows, freq="W"):
    """
    Computes rolling accumulated MWR (IRR/XIRR) up to each week.
    """
    import numpy as np

    if df_cash_flows.empty or df_portfolio_value.empty:
        return pd.DataFrame(columns=["Fecha", "MWR"])

    df_pv_period = df_portfolio_value.set_index("Fecha").resample(freq).last().dropna().reset_index()
    df_cf = df_cash_flows.copy().sort_values("Fecha")

    results = []

    for today in df_pv_period["Fecha"]:
        df_cf_until = df_cf[df_cf["Fecha"] <= today].copy()
        if df_cf_until.empty:
            continue

        # Add current portfolio value as final inflow
        value_today = df_pv_period[df_pv_period["Fecha"] == today]["PortfolioValue"].values[0]
        df_cf_until = pd.concat([
            df_cf_until,
            pd.DataFrame({"Fecha": [today], "CashFlowAmount": [value_today]})
        ], ignore_index=True)

        df_cf_until = df_cf_until.sort_values("Fecha")
        times = (df_cf_until["Fecha"] - df_cf_until["Fecha"].min()).dt.days.values / 365.25
        cash_flows = df_cf_until["CashFlowAmount"].values

        def xnpv(rate, cashflows, times):
            return np.sum(cashflows / (1 + rate) ** times)

        def xirr(cashflows, times, guess=0.1):
            from scipy.optimize import newton
            try:
                return newton(lambda r: xnpv(r, cashflows, times), guess)
            except Exception:
                return None

        irr = xirr(cash_flows, times)
        if irr is not None:
            results.append({"Fecha": today, "MWR": irr * 100})

    return pd.DataFrame(results)

#Rentabilidad Calculations Layer
def calculate_weighted_return_series(df_portfolio_value, df_cumulative_investment, freq="W"):
    """
    Calculates the time series of accumulated weighted return
    as (PortfolioValue / CumulativeInvestment - 1) in %,
    resampled to weekly or monthly frequency.
    """
    # Resample both series to the desired frequency
    df_pv_periodic = df_portfolio_value.set_index("Fecha").resample(freq).last().dropna().reset_index()
    df_inv_periodic = df_cumulative_investment.set_index("Fecha").resample(freq).last().dropna().reset_index()

    # Merge
    df_merged = pd.merge(df_pv_periodic, df_inv_periodic, on="Fecha", how="inner")

    # Avoid division by zero
    df_merged = df_merged[df_merged["CumulativeInvestment"] != 0]

    # Compute return
    df_merged["WeightedReturn"] = (df_merged["PortfolioValue"] / df_merged["CumulativeInvestment"] - 1) * 100

    return df_merged[["Fecha", "WeightedReturn"]]

#Rentabilidad Calculations Layer
def accumulate_returns(df_mwr):
    """
    Chain-links period returns into cumulative return series.
    Expects MWR in %.
    """
    df = df_mwr.copy().sort_values("Fecha")
    df["MWR_cumulative"] = (1 + df["MWR"] / 100).cumprod() - 1
    df["MWR_cumulative"] = df["MWR_cumulative"] * 100
    return df[["Fecha", "MWR_cumulative"]]

#Rentabilidad Calculations Layer
def compute_rolling_returns(df_portfolio_value: pd.DataFrame, windows: list) -> pd.DataFrame:
    """
    Computes rolling returns for specified periods.
    windows = list of pandas offsets (e.g. "7D", "30D").
    Returns DataFrame with Period, Return.
    """
    if df_portfolio_value.empty:
        return pd.DataFrame(columns=["Period", "Return"])

    df = df_portfolio_value.set_index("Fecha").sort_index()
    results = []

    for window in windows:
        shifted = df["PortfolioValue"].shift(freq=window)
        returns = (df["PortfolioValue"] / shifted - 1).dropna()
        avg_return = returns.mean() * 100
        results.append({"Period": window, "Return": round(avg_return, 2)})

    return pd.DataFrame(results)

#Rentabilidad Calculations Layer
def compute_rolling_returns_breakdown(df_portfolio, df_holdings, df_navs, windows):
    """
    Computes rolling returns for the portfolio total and each ISIN in current holdings.
    Returns DataFrame with Nombre, Periodo, Return.
    """
    results = []

    # 1️⃣ Cartera total
    for w in windows:
        shifted = df_portfolio.set_index("Fecha")["PortfolioValue"].shift(freq=w)
        returns = (df_portfolio.set_index("Fecha")["PortfolioValue"] / shifted - 1).dropna()
        avg_return = returns.mean() * 100
        results.append({"Nombre": "Cartera Total", "Periodo": f"{w}", "Return": round(avg_return, 2)})

    # 2️⃣ Activos actualmente en cartera
    fecha_max = df_holdings["Fecha"].max()
    activos_actuales = df_holdings[df_holdings["Fecha"] == fecha_max]["ISIN"].unique()

    for isin in activos_actuales:
        df_isin = df_navs[df_navs["ISIN"] == isin].sort_values("Fecha")
        if df_isin.empty:
            continue

        df_isin = df_isin.set_index("Fecha")
        for w in windows:
            shifted = df_isin["Price"].shift(freq=w)
            returns = (df_isin["Price"] / shifted - 1).dropna()
            if not returns.empty:
                avg_return = returns.mean() * 100
                results.append({"Nombre": isin, "Periodo": f"{w}", "Return": round(avg_return, 2)})

    return pd.DataFrame(results)

#Rentabilidad Calculations Layer
def calculate_total_return_annualized(df_series):
    """
    Computes annualized total return from first to last value in the series.
    Expects DataFrame with Fecha and PortfolioValue (or Price).
    """
    if df_series.empty or len(df_series) < 2:
        return None

    df_series = df_series.sort_values("Fecha")
    start_value = df_series.iloc[0, 1]
    end_value = df_series.iloc[-1, 1]
    days = (df_series.iloc[-1, 0] - df_series.iloc[0, 0]).days

    if start_value <= 0 or end_value <= 0 or days < 30:
        return None

    years = days / 365.25
    total_return = (end_value / start_value) ** (1 / years) - 1
    
    print(f"[Desde Compra] start: {start_value}, end: {end_value}, years: {years:.2f}, CAGR: {total_return*100:.2f}%")
    
    return total_return * 100

#Rentabilidad Calculations Layer
def compute_enhanced_rolling_returns(df_portfolio, df_holdings, df_navs, df_cumulative_investment ,isin_metadata):
    """
    Computes enhanced rolling returns table with Name, ISIN, and multiple horizons including annualized returns.
    """
    from datetime import datetime

    results = []

    # Define periods
    windows_days = [7, 30, 90, 180]
    today = datetime.today()

    # YTD
    ytd_start = pd.Timestamp(year=today.year, month=1, day=1)

    # Activos actualmente en cartera
    fecha_max = df_holdings["Fecha"].max()
    activos_actuales = df_holdings[
        (df_holdings["Fecha"] == fecha_max) & (df_holdings["Participaciones"] > 0)
    ]["ISIN"].unique()

    # Add Cartera Total
    entries = {"Nombre": "Cartera Total", "ISIN": ""}
    df_pv = df_portfolio.set_index("Fecha")
    
      
    for w in windows_days:
        if w >= 365:
            continue  # skip annualized here

        target_date = today - pd.Timedelta(days=w)
        df_valid = df_pv[df_pv.index <= target_date]
        
        if not df_valid.empty:
            nav_past = df_valid.iloc[-1]["PortfolioValue"]
            nav_today = df_pv.iloc[-1]["PortfolioValue"]

            if nav_past > 0:
                rentabilidad = (nav_today / nav_past) - 1
                entries[f"{w}D"] = round(rentabilidad * 100, 2)
            else:
                entries[f"{w}D"] = None
        else:
            entries[f"{w}D"] = None
                             
    # for w in windows_days:
        # shifted = df_pv["PortfolioValue"].shift(freq=pd.Timedelta(days=w))
        # returns = (df_pv["PortfolioValue"] / shifted - 1).dropna()
        # entries[f"{w}D"] = round(returns.mean() * 100, 2) if not returns.empty else None

    # YTD
    ytd_df = df_pv[df_pv.index >= ytd_start]
    if not ytd_df.empty and len(ytd_df) > 1:
        entries["YTD"] = round((ytd_df["PortfolioValue"].iloc[-1] / ytd_df["PortfolioValue"].iloc[0] - 1) * 100, 2)
    else:
        entries["YTD"] = None

    # 1 year
    one_year_ago = today - pd.DateOffset(years=1)
    df_one_year = df_pv[df_pv.index >= one_year_ago]
    if not df_one_year.empty and len(df_one_year) > 1:
        entries["1 año"] = round((df_one_year["PortfolioValue"].iloc[-1] / df_one_year["PortfolioValue"].iloc[0] - 1) * 100, 2)
    else:
        entries["1 año"] = None

    # 📌 Desde Compra* para la Cartera Total usando WeightedReturn
    df_weighted_monthly = calculate_weighted_return_series(df_portfolio, df_cumulative_investment, freq="M")
    df_weighted_monthly = df_weighted_monthly.sort_values("Fecha")

    if df_weighted_monthly.empty or len(df_weighted_monthly) < 2:
        entries["Desde Compra*"] = None
    else:
        start_date = df_weighted_monthly.iloc[0]["Fecha"]
        end_date = df_weighted_monthly.iloc[-1]["Fecha"]
        years = (end_date - start_date).days / 365.25

        if years < 2:
            entries["Desde Compra*"] = None
        else:
            total_weighted_return = df_weighted_monthly.iloc[-1]["WeightedReturn"] / 100
            cagr = (1 + total_weighted_return) ** (1 / years) - 1
            entries["Desde Compra*"] = round(cagr * 100, 2)

    # Placeholder for multi-year annualized
    # 3 años*
    three_years_ago = today - pd.DateOffset(years=3)
    start_date, start_value = find_closest_nav_price(df_pv, three_years_ago, price_column="PortfolioValue")
    end_value = df_pv["PortfolioValue"].iloc[-1]
    end_date = df_pv.index[-1]

    if start_value is not None and end_value > 0:
        years = (end_date - start_date).days / 365.25
        if years >= 2.5:
            cagr = (end_value / start_value) ** (1 / years) - 1
            entries["3 años*"] = round(cagr * 100, 2)
        else:
            entries["3 años*"] = None
    else:
        entries["3 años*"] = None

    # 5 años*
    five_years_ago = today - pd.DateOffset(years=5)
    start_date, start_value = find_closest_nav_price(df_pv, five_years_ago, price_column="PortfolioValue")

    if start_value is not None and end_value > 0:
        years = (end_date - start_date).days / 365.25
        if years >= 4.5:
            cagr = (end_value / start_value) ** (1 / years) - 1
            entries["5 años*"] = round(cagr * 100, 2)
        else:
            entries["5 años*"] = None
    else:
        entries["5 años*"] = None

    # 10 años*
    ten_years_ago = today - pd.DateOffset(years=10)
    start_date, start_value = find_closest_nav_price(df_pv, ten_years_ago, price_column="PortfolioValue")

    if start_value is not None and end_value > 0:
        years = (end_date - start_date).days / 365.25
        if years >= 9.5:
            cagr = (end_value / start_value) ** (1 / years) - 1
            entries["10 años*"] = round(cagr * 100, 2)
        else:
            entries["10 años*"] = None
    else:
        entries["10 años*"] = None

    results.append(entries)

    # Para cada activo
    for isin in activos_actuales:
        df_isin = df_navs[df_navs["ISIN"] == isin].sort_values("Fecha")
        if df_isin.empty:
            continue

        df_isin = df_isin.set_index("Fecha")
        name = isin_metadata.get(isin, isin)

        entries = {"Nombre": name, "ISIN": isin}

        for w in windows_days:
            if w >= 365:
                continue

            target_date = today - pd.Timedelta(days=w)
            df_valid = df_isin[df_isin.index <= target_date]

            if not df_valid.empty:
                price_past = df_valid.iloc[-1]["Price"]
                price_today = df_isin.iloc[-1]["Price"]

                if price_past > 0:
                    rentabilidad = (price_today / price_past) - 1
                    entries[f"{w}D"] = round(rentabilidad * 100, 2)
                else:
                    entries[f"{w}D"] = None
            else:
                entries[f"{w}D"] = None                      
        
        # for w in windows_days:
            # shifted = df_isin["Price"].shift(freq=pd.Timedelta(days=w))
            # returns = (df_isin["Price"] / shifted - 1).dropna()
            # entries[f"{w}D"] = round(returns.mean() * 100, 2) if not returns.empty else None

        # YTD
        ytd_df = df_isin[df_isin.index >= ytd_start]
        if not ytd_df.empty and len(ytd_df) > 1:
            entries["YTD"] = round((ytd_df["Price"].iloc[-1] / ytd_df["Price"].iloc[0] - 1) * 100, 2)
        else:
            entries["YTD"] = None

        # 1 año
        one_year_ago = today - pd.DateOffset(years=1)
        df_one_year = df_isin[df_isin.index >= one_year_ago]
        if not df_one_year.empty and len(df_one_year) > 1:
            entries["1 año"] = round((df_one_year["Price"].iloc[-1] / df_one_year["Price"].iloc[0] - 1) * 100, 2)
        else:
            entries["1 año"] = None

        # 3 años
        three_years_ago = today - pd.DateOffset(years=3)
        valid_data = df_isin[df_isin.index <= today]
        start_date, start_price = find_closest_nav_price(valid_data, three_years_ago)

        end_price = valid_data.iloc[-1]["Price"]
        end_date = valid_data.index[-1]

        # print(f"🔍 [3 años] Target date: {three_years_ago}")
        # print(f"🔍 [3 años] Found start_date: {start_date}, start_price: {start_price}")
        # print(f"🔍 [3 años] end_date: {end_date}, end_price: {end_price}")

        if (
            start_price is not None
            and end_price > 0
        ):
            years = (end_date - start_date).days / 365.25
            print(f"🔍 [3 años] Years diff: {years}")
            if years >= 2.5:
                cagr = (end_price / start_price) ** (1 / years) - 1
                entries["3 años*"] = round(cagr * 100, 2)
            else:
                print(f"⚠️ [3 años] Not enough years ({years})")
                entries["3 años*"] = None
        else:
            print(f"⚠️ [3 años] Missing start or end price")
            entries["3 años*"] = None


        # 5 años
        five_years_ago = today - pd.DateOffset(years=5)
        valid_data = df_isin[df_isin.index <= today]
        start_date, start_price = find_closest_nav_price(valid_data, five_years_ago)

        end_price = valid_data.iloc[-1]["Price"]
        end_date = valid_data.index[-1]

        # print(f"🔍 [5 años] Target date: {five_years_ago}")
        # print(f"🔍 [5 años] Found start_date: {start_date}, start_price: {start_price}")
        # print(f"🔍 [5 años] end_date: {end_date}, end_price: {end_price}")

        if (
            start_price is not None
            and end_price > 0
        ):
            years = (end_date - start_date).days / 365.25
            print(f"🔍 [5 años] Years diff: {years}")
            if years >= 4.5:
                cagr = (end_price / start_price) ** (1 / years) - 1
                entries["5 años*"] = round(cagr * 100, 2)
            else:
                print(f"⚠️ [5 años] Not enough years ({years})")
                entries["5 años*"] = None
        else:
            print(f"⚠️ [5 años] Missing start or end price")
            entries["5 años*"] = None


        # 10 años
        ten_years_ago = today - pd.DateOffset(years=10)
        valid_data = df_isin[df_isin.index <= today]
        start_date, start_price = find_closest_nav_price(valid_data, ten_years_ago)

        end_price = valid_data.iloc[-1]["Price"]
        end_date = valid_data.index[-1]

        # print(f"🔍 [10 años] Target date: {ten_years_ago}")
        # print(f"🔍 [10 años] Found start_date: {start_date}, start_price: {start_price}")
        # print(f"🔍 [10 años] end_date: {end_date}, end_price: {end_price}")

        if (
            start_price is not None
            and end_price > 0
        ):
            years = (end_date - start_date).days / 365.25
            print(f"🔍 [10 años] Years diff: {years}")
            if years >= 9.5:
                cagr = (end_price / start_price) ** (1 / years) - 1
                entries["10 años*"] = round(cagr * 100, 2)
            else:
                print(f"⚠️ [10 años] Not enough years ({years})")
                entries["10 años*"] = None
        else:
            print(f"⚠️ [10 años] Missing start or end price")
            entries["10 años*"] = None


                
        # Desde Compra
        entries["Desde Compra*"] = round(calculate_total_return_annualized(df_isin.reset_index()), 2)

        # # Placeholder for multi-year annualized
        # entries["3 años"] = None
        # entries["5 años"] = None
        # entries["10 años"] = None

        results.append(entries)

    return pd.DataFrame(results)

# =========================================
#  BENCHMARK COMPARISSON LAYER
# =========================================
def align_portfolio_and_benchmark(df_portfolio: pd.DataFrame, df_benchmark: pd.DataFrame) -> pd.DataFrame:
    """
    Aligns portfolio and benchmark series by date.
    """
    df_portfolio = df_portfolio.copy()
    df_benchmark = df_benchmark.copy()
    df = pd.merge(df_portfolio, df_benchmark, on="Fecha", how="inner")
    return df

#Benchmark Comparison Layer
def compute_relative_performance(df_aligned: pd.DataFrame) -> pd.DataFrame:
    """
    Computes over/under-performance vs benchmark.
    """
    df = df_aligned.copy()
    df["RelativeReturn"] = df["PortfolioValue"] - df["BenchmarkValue"]
    return df[["Fecha", "PortfolioValue", "BenchmarkValue", "RelativeReturn"]]



