import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import json
from urllib.request import urlopen

# Configuração da página
st.set_page_config(
    page_title="População Brasileira",
    page_icon="🌎",
    layout="wide",
    initial_sidebar_state="expanded"
)

alt.themes.enable("dark")

# Função para formatar números
def format_number(num):
    if num > 1000000:
        if not num % 1000000:
            return f'{num // 1000000} M'
        return f'{round(num / 1000000, 1)} M'
    return f'{num // 1000} K'

# Estilização CSS aprimorada
st.markdown("""
<style>
[data-testid="block-container"] {
    padding-left: 2rem;
    padding-right: 2rem;
    padding-top: 1rem;
    padding-bottom: 0rem;
    margin-bottom: -7rem;
}

[data-testid="stVerticalBlock"] {
    padding-left: 0rem;
    padding-right: 0rem;
}

[data-testid="stMetric"] {
    background-color: #393939;
    text-align: center;
    padding: 15px 0;
    border-radius: 10px;
    margin-bottom: 1rem;
}

[data-testid="stMetricLabel"] {
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 1.2rem;
    font-weight: bold;
}

[data-testid="stMetricDeltaIcon-Up"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}

[data-testid="stMetricDeltaIcon-Down"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}

h1, h2, h3, h4, h5, h6 {
    color: #FFFFFF;
}

/* Estilo do Slider */
.stSlider > div {
    padding: 0 1rem;
}
""", unsafe_allow_html=True)

# Carregar os dados
try:
    df_reshaped = pd.read_csv('./data/br-population-2015-2024-cleaned.csv')
except FileNotFoundError:
    st.error("Arquivo CSV não encontrado. Verifique o caminho do arquivo.")
    st.stop()

# Carregar o GeoJSON do Brasil
try:
    with urlopen('https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson') as response:
        Brazil = json.load(response)
except Exception as e:
    st.error(f"Erro ao carregar o GeoJSON: {e}")
    st.stop()

# Mapear siglas dos estados para nomes completos
state_id_map = {}
for feature in Brazil['features']:
    feature['id'] = feature['properties']['name']
    state_id_map[feature['properties']['sigla']] = feature['id']

# Sidebar
with st.sidebar:
    st.title('🌎 Dashboard Populacional')
    
    # Scrollbar horizontal para seleção de ano
    ano_list = list(df_reshaped.ano.unique())
    selected_ano = st.slider(
        'Selecione um ano',
        min_value=min(ano_list),
        max_value=max(ano_list),
        value=max(ano_list),
        key='ano_slider'
    )
    st.write(f"Ano selecionado: {selected_ano}")

    df_selected_ano = df_reshaped[df_reshaped.ano == selected_ano]
    df_selected_ano_sorted = df_selected_ano.sort_values(by="populacao", ascending=False)

    color_theme_list = ['blues', 'cividis', 'greens', 'inferno', 'magma', 'plasma', 'reds', 'rainbow', 'turbo', 'viridis']
    selected_color_theme = st.selectbox('Selecione um tema de cores', color_theme_list)

# Funções

# Heatmap
def make_heatmap(input_df, input_y, input_x, input_color, input_color_theme):
    heatmap = alt.Chart(input_df).mark_rect().encode(
        y=alt.Y(f'{input_y}:O', axis=alt.Axis(title="Ano", titleFontSize=18, titlePadding=15, titleFontWeight=900, labelAngle=0)),
        x=alt.X(f'{input_x}:O', axis=alt.Axis(title="", titleFontSize=18, titlePadding=15, titleFontWeight=900)),
        color=alt.Color(f'max({input_color}):Q',
                        legend=None,
                        scale=alt.Scale(scheme=input_color_theme)),
        stroke=alt.value('black'),
        strokeWidth=alt.value(0.25),
    ).properties(width=900).configure_axis(labelFontSize=12, titleFontSize=12)
    return heatmap

# Mapa Coroplético
def make_choropleth(input_df, input_id, input_column, input_color_theme):
    choropleth = px.choropleth(input_df, locations=input_id, color=input_column,
                                geojson=Brazil, locationmode="geojson-id",
                                color_continuous_scale=input_color_theme,
                                range_color=(0, max(df_selected_ano.populacao)),
                                labels={'populacao': 'População'})
    choropleth.update_layout(
        template='plotly_dark',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=350
    )
    choropleth.update_geos(fitbounds="locations", visible=False)
    return choropleth

# Gráfico de Barras (População por Estado)
def make_bar_chart(input_df, input_x, input_y, input_color_theme):
    bar_chart = alt.Chart(input_df).mark_bar().encode(
        x=alt.X(f'{input_x}:N', title="Estado", sort='-y'),
        y=alt.Y(f'{input_y}:Q', title="População"),
        color=alt.Color(f'{input_y}:Q', scale=alt.Scale(scheme=input_color_theme)),
        tooltip=[input_x, input_y]
    ).properties(width=800, height=400)
    return bar_chart

# Gráfico de Linha (Evolução da População por Estado)
def make_line_chart(input_df, input_x, input_y, input_color):
    line_chart = alt.Chart(input_df).mark_line().encode(
        x=alt.X(f'{input_x}:O', title="Ano"),
        y=alt.Y(f'{input_y}:Q', title="População"),
        color=alt.Color(f'{input_color}:N', legend=None),
        tooltip=[input_x, input_y]
    ).properties(width=800, height=400)
    return line_chart

# Layout principal
col = st.columns((1.5, 4.5, 2), gap='medium')

with col[0]:
    st.markdown('#### Crescimento/Declínio')

    df_population_difference_sorted = df_selected_ano_sorted.copy()

    if selected_ano > 2015:
        first_state_name = df_population_difference_sorted.Estado.iloc[0]
        first_state_population = format_number(df_population_difference_sorted.populacao.iloc[0])
        
        # Calcular a diferença de crescimento
        previous_year_population = df_reshaped[(df_reshaped.ano == selected_ano - 1) & (df_reshaped.Estado == first_state_name)].populacao.iloc[0]
        first_state_delta = df_population_difference_sorted.populacao.iloc[0] - previous_year_population
        first_state_delta_formatted = format_number(first_state_delta)
    else:
        first_state_name = '-'
        first_state_population = '-'
        first_state_delta_formatted = ''
    
    st.metric(label=first_state_name, value=first_state_population, delta=first_state_delta_formatted)

    if selected_ano > 2015:
        last_state_name = df_population_difference_sorted.Estado.iloc[-1]
        last_state_population = format_number(df_population_difference_sorted.populacao.iloc[-1])   
        last_state_delta = format_number(df_population_difference_sorted.populacao.iloc[-1] - df_reshaped[df_reshaped.ano == selected_ano - 1].populacao.iloc[-1])   
    else:
        last_state_name = '-'
        last_state_population = '-'
        last_state_delta = ''
    st.metric(label=last_state_name, value=last_state_population, delta=last_state_delta)

    st.markdown('#### Evolução da População por Estado')

    estado_selecionado = st.selectbox('Selecione um estado', df_reshaped.Estado.unique())
    df_estado_selecionado = df_reshaped[df_reshaped.Estado == estado_selecionado]

    line_chart = make_line_chart(df_estado_selecionado, 'ano', 'populacao', 'Estado')
    st.altair_chart(line_chart, use_container_width=True)

with col[1]:
    st.markdown('#### População Total')
    
    choropleth = make_choropleth(df_selected_ano, 'Estado', 'populacao', selected_color_theme)
    st.plotly_chart(choropleth, use_container_width=True)
    
    heatmap = make_heatmap(df_reshaped, 'ano', 'Estado', 'populacao', selected_color_theme)
    st.altair_chart(heatmap, use_container_width=True)

with col[2]:
    st.markdown('#### Estados Mais Populosos')

    st.dataframe(df_selected_ano_sorted,
                column_order=("Estado", "populacao"),
                hide_index=True,
                width=None,
                column_config={
                    "Estado": st.column_config.TextColumn("Estado"),
                    "populacao": st.column_config.ProgressColumn(
                        "População",
                        format="%f",
                        min_value=0,
                        max_value=max(df_selected_ano_sorted.populacao),
                    )}
                )
    
    with st.expander('Sobre', expanded=True):
        st.write('''
            - Dados: IBGE (População estimada de 2015 a 2024).
            - :orange[**Crescimento/Declínio**]: estados com maior crescimento ou declínio populacional no ano selecionado.
            - :orange[**Evolução da População**]: gráfico de linha mostrando a evolução da população de um estado ao longo dos anos.
            ''')