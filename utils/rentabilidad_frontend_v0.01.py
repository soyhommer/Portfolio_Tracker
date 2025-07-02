import pandas as pd
import streamlit as st
import plotly.express as px
from utils import rentabilidad_backend as rb

def mostrar_rentabilidad(portfolio_name: str):
    st.title(f"📈 Rentabilidad de la cartera: {portfolio_name}")

    # Load transactions
    df_tx = rb.load_transactions_clean(portfolio_name)
    if df_tx.empty:
        st.warning("⚠️ No hay transacciones para esta cartera.")
        return

    # Build holdings
    df_holdings = rb.build_holdings_over_time(df_tx)
    isin_list = df_holdings["ISIN"].unique()

    # Load NAVs with forward fill
    df_navs = rb.load_all_navs(isin_list, df_tx)

    # Portfolio valuation
    df_portfolio = rb.compute_portfolio_valuation(df_holdings, df_navs)
    if df_portfolio.empty:
        st.error("❌ No se pudo calcular el valor de la cartera. Verifica históricos NAV.")
        return

    # Cash flows for IRR
    df_cash_flows = rb.extract_cash_flows(df_tx)

    # Investment flows for cumulative invested capital
    df_investment_flows = rb.extract_investment_flows(df_tx)
    start_date = df_tx["Fecha"].min()
    end_date = pd.Timestamp.today()
    df_cumulative_investment = rb.compute_cumulative_investment(df_investment_flows, start_date, end_date)

    # Build full date range from first transaction to today
    full_range = pd.date_range(df_tx["Fecha"].min(), pd.Timestamp.today(), freq="D")

    # Extend PortfolioValue series to today
    df_portfolio = df_portfolio.set_index("Fecha").reindex(full_range).fillna(method="ffill").reset_index().rename(columns={"index":"Fecha"})

    # Extend CumulativeInvestment series to today
    df_cumulative_investment = df_cumulative_investment.set_index("Fecha").reindex(full_range).fillna(method="ffill").reset_index().rename(columns={"index":"Fecha"})

    # Merge for dual-line plot
    df_merged = pd.merge(df_portfolio, df_cumulative_investment, on="Fecha", how="outer").sort_values("Fecha").fillna(method="ffill")

    # 1️⃣ Portfolio Value vs Cumulative Invested
    st.header("📈 Evolución del valor de la cartera (€) y de la inversión acumulada (€)")
    
    # 🔹 Selección de frecuencia
    freq = st.selectbox(
        "Frecuencia de cálculo:",
        ["W", "M"],
        format_func=lambda x: "Semanal" if x == "W" else "Mensual"
    )
    
    
    fig_value = px.line(
        df_merged,
        x="Fecha",
        y=["PortfolioValue", "CumulativeInvestment"],
        title="Valor de la cartera vs Inversión acumulada",
        labels={"value": "€", "variable": "Serie"}
    )
    fig_value.update_traces(hovertemplate="%{y:.2f} €")
    st.plotly_chart(fig_value, use_container_width=True)

    # 2️⃣ TWR vs MWR Chart
    st.header("📈 Rentabilidad TWR vs MWR")

    

    # TWR Series
    # df_twr = rb.calculate_twr(df_portfolio, df_cash_flows)
    # df_twr_weekly = df_twr.set_index("Fecha").resample("W").last().dropna().reset_index()
    df_twr = rb.calculate_twr(df_portfolio, df_cash_flows)
    df_twr_periodic = rb.resample_twr_series(df_twr, freq=freq)


    # MWR Series (dynamic)
    #df_mwr_series = rb.calculate_mwr_series_weekly(df_portfolio, df_cash_flows)
    #df_mwr_periodic = rb.calculate_mwr_accumulated_series(df_portfolio, df_cash_flows, freq="W")
    #df_mwr_cum = rb.accumulate_returns(df_mwr_periodic)
    df_weighted_return = rb.calculate_weighted_return_series(df_portfolio, df_cumulative_investment, freq=freq)

    # Combine for Plotly long format
    df_plot = pd.concat([
        df_twr_periodic.assign(Tipo="TWR").rename(columns={"TWR": "Rentabilidad"}),
        df_weighted_return.assign(Tipo="Rentabilidad Ponderada").rename(columns={"WeightedReturn": "Rentabilidad"})
    ])


    fig_twr = px.line(
        df_plot,
        x="Fecha",
        y="Rentabilidad",
        color="Tipo",
        title=f"Rentabilidad {('semanal' if freq == 'W' else 'mensual')}: TWR vs Rentabilidad Ponderada por Activos",
        labels={"Rentabilidad": "%", "Tipo": "Serie"}
    )
    fig_twr.update_traces(hovertemplate="%{y:.2f}%")
    st.plotly_chart(fig_twr, use_container_width=True)


    # 3️⃣ MWR Metric
    st.header("💰 Rentabilidad MWR")
    mwr_result = rb.calculate_mwr(df_portfolio, df_cash_flows)
    st.metric(label="MWR estimado (%)", value=f"{mwr_result:.2f}%")

    # 4️⃣ Rolling Returns Table
    st.header("📊 Rentabilidades Rolling")
    windows = ["7D", "30D", "90D", "180D", "365D"]
    df_rolling = rb.compute_rolling_returns(df_portfolio, windows)
    st.dataframe(df_rolling)

    # 5️⃣ Benchmark Comparison
    st.header("📈 Comparativa con Benchmark")
    df_benchmark = rb.load_portfolio_benchmark(portfolio_name)
    if df_benchmark.empty:
        st.info("ℹ️ No hay benchmark definido para esta cartera.")
    else:
        df_aligned = rb.align_portfolio_and_benchmark(df_portfolio, df_benchmark)
        if df_aligned.empty:
            st.warning("⚠️ No hay fechas comunes entre cartera y benchmark.")
        else:
            df_comparison = rb.compute_relative_performance(df_aligned)
            fig_comp = px.line(
                df_comparison,
                x="Fecha",
                y=["PortfolioValue", "BenchmarkValue"],
                title="Evolución cartera vs Benchmark",
                labels={"value": "€", "variable": "Serie"}
            )
            st.plotly_chart(fig_comp, use_container_width=True)

            st.header("Diferencial de Rentabilidad")
            fig_diff = px.line(
                df_comparison,
                x="Fecha",
                y="RelativeReturn",
                title="Over/Under Performance (€)",
                labels={"RelativeReturn": "€"}
            )
            st.plotly_chart(fig_diff, use_container_width=True)

