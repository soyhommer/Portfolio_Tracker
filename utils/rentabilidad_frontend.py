import json
import pandas as pd
import streamlit as st
import plotly.express as px
from utils import rentabilidad_backend as rb
from utils.config import CACHE_NOMBRE_PATH

with open(CACHE_NOMBRE_PATH, "r", encoding="utf-8") as f:
    isin_metadata = json.load(f)

def mostrar_rentabilidad(portfolio_name: str):
    st.title(f"📈 Rentabilidad de la cartera: {portfolio_name}")

    # 🔹 Selección de frecuencia global
    
    # freq = st.selectbox(
        # "Frecuencia de cálculo:",
        # ["W", "M"],
        # format_func=lambda x: "Semanal" if x == "W" else "Mensual"
    # )
    freq = "M"
    
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

    # Cash flows
    df_cash_flows = rb.extract_cash_flows(df_tx)

    # Investment flows and cumulative invested capital
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

    # 📌 1️⃣ Gráfica: Valor de Cartera vs Inversión Acumulada (con frecuencia seleccionada)
    st.header("📈 Evolución del valor de la cartera (€) y de la inversión acumulada (€)")

    # Resamplear ambas series con frecuencia seleccionada
    df_portfolio_resampled = df_portfolio.set_index("Fecha").resample(freq).last().dropna().reset_index()
    df_investment_resampled = df_cumulative_investment.set_index("Fecha").resample(freq).last().dropna().reset_index()

    df_merged_value = pd.merge(df_portfolio_resampled, df_investment_resampled, on="Fecha", how="inner")

    fig_value = px.line(
        df_merged_value,
        x="Fecha",
        y=["PortfolioValue", "CumulativeInvestment"],
        title=f"Valor de la cartera vs Inversión acumulada - Frecuencia: {'Semanal' if freq == 'W' else 'Mensual'}",
        labels={"value": "€", "variable": "Serie"}
    )
    fig_value.update_traces(hovertemplate="%{y:.2f} €")
    st.plotly_chart(fig_value, use_container_width=True)

    # 📌 2️⃣ Gráfica: TWR vs Rentabilidad Ponderada por Activos (misma frecuencia)
    st.header("📈 Rentabilidad TWR vs Rentabilidad Ponderada por Activos")

    # TWR Series
    df_twr = rb.calculate_twr(df_portfolio, df_cash_flows)
    df_twr_periodic = rb.resample_twr_series(df_twr, freq=freq)

    # Rentabilidad Ponderada Series
    df_weighted_return = rb.calculate_weighted_return_series(df_portfolio, df_cumulative_investment, freq=freq)

    # Combinar para gráfico
    df_plot = pd.concat([
        df_twr_periodic.assign(Tipo="TWR").rename(columns={"TWR": "Rentabilidad"}),
        df_weighted_return.assign(Tipo="Rentabilidad Ponderada").rename(columns={"WeightedReturn": "Rentabilidad"})
    ])

    fig_twr = px.line(
        df_plot,
        x="Fecha",
        y="Rentabilidad",
        color="Tipo",
        title=f"Rentabilidad {'semanal' if freq == 'W' else 'mensual'}: TWR vs Rentabilidad Ponderada por Activos",
        labels={"Rentabilidad": "%", "Tipo": "Serie"}
    )
    fig_twr.update_traces(hovertemplate="%{y:.2f}%")
    st.plotly_chart(fig_twr, use_container_width=True)

    # 📌 3️⃣ MWR Metric
    st.header("💰 Rentabilidad MWR")
    mwr_result = rb.calculate_mwr(df_portfolio, df_cash_flows)
    st.metric(label="MWR estimado (%)", value=f"{mwr_result:.2f}%")
    
    # 🔹 Rentabilidad Ponderada Mensual por Año
    st.header("📊 Rentabilidad Ponderada Mensual por Año")

    # Calcular serie mensual acumulada
    df_weighted_monthly = rb.calculate_weighted_return_series(df_portfolio, df_cumulative_investment, freq="M")

    # Transformar en variación mensual
    df_weighted_monthly = df_weighted_monthly.sort_values("Fecha")
    df_weighted_monthly["RentabilidadMensual"] = (1 + df_weighted_monthly["WeightedReturn"]/100).pct_change() * 100
    df_weighted_monthly["RentabilidadMensual"] = df_weighted_monthly["RentabilidadMensual"].round(2)

    # Extraer año y mes
    df_weighted_monthly["Año"] = df_weighted_monthly["Fecha"].dt.year
    df_weighted_monthly["Mes"] = df_weighted_monthly["Fecha"].dt.month

    # Pivot a Año x Mes
    pivot_table = df_weighted_monthly.pivot_table(
        index="Año",
        columns="Mes",
        values="RentabilidadMensual",
        aggfunc="first"
    )

    # Calcular Total compuesto por año
    pivot_table["Total"] = (1 + pivot_table/100).prod(axis=1) - 1
    pivot_table["Total"] = (pivot_table["Total"] * 100).round(2)

    # Ordenar años descendente
    pivot_table = pivot_table.sort_index(ascending=False)

    # Redondear celdas en %
    pivot_table = pivot_table.applymap(lambda x: round(x, 2) if pd.notnull(x) else x)

    # Identificar máximos
    max_gain = pivot_table.drop(columns=["Total"], errors='ignore').max().max()
    max_loss = pivot_table.drop(columns=["Total"], errors='ignore').min().min()

    # Formato personalizado
    def highlight_cells(val):
        if pd.isna(val):
            return ""

        # Comparación directa para máximos y mínimos
        if val == max_gain:
            return "font-weight: bold;"
        if val == max_loss:
            return "color: red; font-weight: bold;"

        # Solo intentamos detectar negativos numéricos
        try:
            if float(val) < 0:
                return "color: red;"
        except (ValueError, TypeError):
            pass

        return ""



    def safe_percent_format(val):
        try:
            return "{:.2f}%".format(float(val))
        except (ValueError, TypeError):
            return val



    styled_table = pivot_table.style.format("{:,.2f}%").applymap(highlight_cells)

    # Mostrar
    st.dataframe(styled_table, use_container_width=True)
    
   # 📌 4️⃣ Rolling Returns Breakdown
    st.header("📊 Rentabilidades Rolling Detalladas")

    # Crear mapping ISIN ➜ Nombre
    import json
    from utils.config import CACHE_NOMBRE_PATH

    with open(CACHE_NOMBRE_PATH, "r", encoding="utf-8") as f:
        isin_metadata = json.load(f)

    # Llamada al backend
    df_rolling_detailed = rb.compute_enhanced_rolling_returns(
        df_portfolio,
        df_holdings,
        df_navs,
        df_cumulative_investment,
        isin_metadata
    )

    # Definir orden de columnas con anualizadas marcadas
    ordered_cols = [
        "Nombre", "ISIN", "7D", "30D", "90D", "180D",
        "YTD", "1 año", "3 años*", "5 años*", "10 años*", "Desde Compra*"
    ]
    df_rolling_detailed = df_rolling_detailed.reindex(columns=ordered_cols)

    # Formateo
    format_dict = {col: "{:,.2f}%" for col in ordered_cols if col not in ["Nombre", "ISIN"]}

    # Nota explicativa
    st.caption("* Las columnas marcadas con asterisco representan rentabilidades anualizadas")

    df_rolling_detailed = df_rolling_detailed.fillna("")
    
    # Mostrar tabla
    st.dataframe(
        df_rolling_detailed.style
            .format(safe_percent_format)
            .applymap(
                highlight_cells,
                subset=[col for col in df_rolling_detailed.columns if col not in ["Nombre", "ISIN"]]
            ),
        use_container_width=True
    )

    
    # 📌 5️⃣ Benchmark Comparison
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
