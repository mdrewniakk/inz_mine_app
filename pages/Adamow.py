import ee
import streamlit as st
import geemap.foliumap as geemap
from src.funcs import best_image, latest_image, calc_indices, lineplot, get_index, get_vis_params, plot_hist, text, \
    equations, years_fun, text2, get_dates
from Strona_glowna import get_data


@st.cache_data
def ee_authenticate(token_name="EARTHENGINE_TOKEN"):
    geemap.ee_initialize(token_name=token_name)


ee_authenticate(token_name="EARTHENGINE_TOKEN")

ee.Initialize()


@st.cache_data
def ee_authenticate(token_name="EARTHENGINE_TOKEN"):
    geemap.ee_initialize(token_name=token_name)



@st.cache_data
def get_dates_cache():
    return get_dates(index, get_data()[0])


    
mining = ee.FeatureCollection("projects/sat-io/open-datasets/global-mining/global_mining_polygons")
adamow = mining.filter(ee.Filter.eq("system:index", "000000000000000016ed"))

Map = geemap.Map(center=(52.010558, 18.629901), zoom=13)
Map.addLayer(adamow, name="Poligon Kopalni")

st.header("KWB Adamów")

row1_col1, row1_col2, row1_col3 = st.columns([1, 2, 1])

indices = ['NDVI', 'EVI', 'NDWI1', 'NDWI2', 'NMDI', 'MSI', 'MSAVI2']
with row1_col3, st.container(border=True):
    year = st.selectbox("Wybierz rok", years_fun)
    index = st.selectbox("Wybierz wskaźnik", indices)
    lineplot(index, adamow, get_data()[0], get_dates_cache())
    st.markdown(text2[index], unsafe_allow_html=True)

if year:
    if index:
        Map.addLayer(ee.Image(get_index(year, index, get_data()[0]).toList(2).get(0)), get_vis_params(index), f"{index} Maj {year}")
        Map.addLayer(ee.Image(get_index(year, index, get_data()[0]).toList(2).get(1)), get_vis_params(index), f"{index} Sierpień {year}")
        with row1_col1, st.container(border=True):
            st.markdown(text[index], unsafe_allow_html=True)
            st.markdown('''
            <style>
            .katex-html {
                font-size: 0.7em;
            }
            </style>''',
                        unsafe_allow_html=True
                        )
            st.latex(equations[index])
            with st.expander("Histogram dla maja", True):
                plot_hist(year, index, get_data()[0], 0)
            with st.expander("Histogram dla sierpnia"):
                plot_hist(year, index, get_data()[0], 1)
            Map.add_colorbar(get_vis_params(index), label=f"Wartość {index}",
                             layer_name=index + str(year))

            with row1_col2, st.container(border=True):
                st.markdown("<style>padding-top: 10px</style>", unsafe_allow_html=True)
                Map.to_streamlit(height=700)

else:
    with row1_col2, st.container(border=True):
        Map.to_streamlit(height=700)
