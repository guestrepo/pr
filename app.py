import streamlit as st
import pandas as pd
import pycountry_convert as pc
import plotly.express as px

def country_to_continent(country):
    try:
        country_code = pc.country_name_to_country_alpha2(country, cn_name_format="default")
        continent_code = pc.country_alpha2_to_continent_code(country_code)
        continent_name = pc.convert_continent_code_to_continent_name(continent_code)
        return continent_name
    except:
        if country == 'Kosovo':
            return 'Europe'  # Asignación manual
        return 'Other'
    
st.set_page_config(layout='wide')
st.title("Producción Mineral y Desarrollo")

df = pd.read_csv("datos/dataset_fusionado.csv", sep=';')

df['Country_Name'] = df['Country_Name'].replace({
    'Bosnia-Herzegovina': 'Bosnia and Herzegovina',
    'Congo D,R,': 'Democratic Republic of the Congo',
    'Congo Rep,': 'Congo',
    "Cote d'Ivoire": "Ivory Coast",
    'Kosovo': 'Kosovo'  # Kosovo no está oficialmente en pycountry, lo asignaremos luego
})

# Reemplazar comas por puntos y limpiar espacios
for col in df.columns:
    df[col] = df[col].astype(str).str.replace(',', '.').str.strip()

columnas_excluir = ['Country_Name', 'Country_Code', 'Year', 'Mineral', 'Unidad', 'Valor', 'Tipo', 'Continent']
columnas_numericas = [col for col in df.columns if col not in columnas_excluir]
# Corregir coma decimal


# Convertir solo esas columnas a numérico
for col in columnas_numericas:
    df[col] = pd.to_numeric(df[col], errors='coerce')


# También asegurarse que 'Valor' sea numérico
df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce')

# Agregar continente
df['Continent'] = df['Country_Name'].apply(country_to_continent)

df['Year'] = pd.to_numeric(df['Year'], errors='coerce').astype('Int64')
anio = st.slider("Selecciona un año", int(df['Year'].min()), int(df['Year'].max()), step=1)
tipos_validos = df['Tipo'].dropna().unique().tolist()
tipos_validos.sort()
tipo_seleccionado = st.multiselect(
    "Selecciona tipo(s) de mineral (excluyendo fósiles e industriales)",
    sorted(tipos_validos),
    default=list(tipos_validos)  # Por defecto todos seleccionados
)
# Filtro por año
df = df[df['Tipo'].isin(tipo_seleccionado)]
df_anio = df[df['Year'] == anio]

st.write(f"Todos los gráficos son para el año ({anio}) y el tipo ({tipo_seleccionado})")

# Producción por continente
prod_cont = df_anio.groupby('Continent')['Valor'].sum().reset_index()
fig1 = px.bar(prod_cont, x='Continent', y='Valor', title=f"Producción minera total por continente")
st.plotly_chart(fig1)

# Producción por país (top 10)
#top_paises = df_anio.groupby('Country_Name')['Valor'].sum().nlargest(10).reset_index()
#fig2 = px.bar(top_paises, x='Valor', y='Country_Name', orientation='h', title=f"Top 10 países por producción minera")
#st.plotly_chart(fig2)

# Selector de país o continente
opcion = st.selectbox("Agrupar por:", [ 'Continente', 'País'])

if opcion == 'País':
    grupo = 'Country_Name'
else:
    grupo = 'Continent'

prod_mineral = df_anio.groupby([grupo, 'Mineral'])['Valor'].sum().reset_index()
fig3 = px.sunburst(prod_mineral, path=[grupo, 'Mineral'], values='Valor', title="Distribución de minerales")
st.plotly_chart(fig3)


# Selección de un indicador de desarrollo
indicadores = {
    'PIB per cápita (USD PPP)': 'NY_GDP_PCAP_PP_CD',
    'Esperanza de vida': 'SP_DYN_LE00_IN',
    'Acceso a electricidad (%)': 'EG_ELC_ACCS_ZS',
    'Índice de pobreza': 'SI_POV_NAHC'
}

indicador_sel = st.selectbox("Selecciona un indicador:", list(indicadores.keys()))
columna = indicadores[indicador_sel]
# Obtener top 10 países por producción total en el año
top_10_paises = (
    df_anio.groupby('Country_Name')['Valor']
    .sum()
    .nlargest(10)
    .index
)

# Filtrar datos para esos países
df_top10 = df_anio[df_anio['Country_Name'].isin(top_10_paises)]

# Agrupar por país: suma de producción, y promedio del indicador
df_disp = (
    df_top10
    .groupby('Country_Name')
    .agg({
        'Valor': 'sum',
        columna: 'mean'
    })
    .reset_index()
    .dropna()
)
import plotly.graph_objects as go

fig4 = px.scatter(
    df_disp, x=columna, y='Valor', text='Country_Name',
    title=f"{indicador_sel} vs Producción Mineral Total (Top 10 productores)",
    labels={'Valor': 'Producción Mineral (t)', columna: indicador_sel}
)

# Aumentar tamaño de los puntos
fig4.update_traces(marker=dict(size=12, color='royalblue', opacity=0.8), textposition='top center')

# Mejorar los ejes: mostrar títulos y ajustar rango y ticks si quieres
fig4.update_layout(
    xaxis_title=indicador_sel,
    yaxis_title='Producción Mineral (t)',
    xaxis=dict(showgrid=True),
    yaxis=dict(showgrid=True),
    margin=dict(l=60, r=40, t=60, b=60)
)

fig4.update_traces(
    hoverinfo='text+x+y',  # muestra país y valores al pasar el mouse
    mode='markers+text',
)

st.plotly_chart(fig4)
