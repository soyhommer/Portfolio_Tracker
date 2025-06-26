import streamlit as st

def mostrar_dataframe_formateado(df):
    if df.empty:
        st.info("No hay datos disponibles.")
        return

    def formatear_negativos(val):
        try:
            return f"color: red;" if float(val) < 0 else ""
        except:
            return ""

    def formatear_columna(col, decimales):
        return df[col].apply(lambda x: round(x, decimales) if isinstance(x, (int, float)) else x)

    # Copia para preservar formato
    df_formateado = df.copy()

    if "1 d%" in df_formateado.columns:
        df_formateado["1 d%"] = formatear_columna("1 d%", 2)

    if "#Participaciones" in df_formateado.columns:
        df_formateado["#Participaciones"] = formatear_columna("#Participaciones", 2)

    if "Último NAV (EUR)" in df_formateado.columns:
        df_formateado["Último NAV (EUR)"] = formatear_columna("Último NAV (EUR)", 2)

    styled = df_formateado.style

    if "1 d%" in df_formateado.columns:
        styled = styled.applymap(formatear_negativos, subset=["1 d%"])

    st.dataframe(styled, use_container_width=True, height=600)