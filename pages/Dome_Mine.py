import ee
import streamlit as st
import geemap.foliumap as geemap
from src.funcs import best_image, latest_image, calc_indices, lineplot, get_index, get_vis_params, plot_hist, text, \
    equations, years_fun, text2


@st.cache_data
def ee_authenticate(token_name="EARTHENGINE_TOKEN"):
    geemap.ee_initialize(token_name=token_name)


ee_authenticate(token_name="EARTHENGINE_TOKEN")

ee.Initialize()


@st.cache_data
def ee_authenticate(token_name="EARTHENGINE_TOKEN"):
    geemap.ee_initialize(token_name=token_name)


@st.cache_data
def get_data():
    ROI = ee.Geometry.Point(-81.240261, 48.458284)
    start_year = 2018
    end_year = 2022
    years = ee.List.sequence(start_year, end_year)
    images_canada = years.map(lambda year: best_image(ee.Number(year), ROI))
    images_canada = images_canada.add(latest_image(ROI))
    dataset = calc_indices(images_canada, get_bound())
    return dataset


@st.cache_data
def get_bound():
    mining = ee.FeatureCollection("projects/sat-io/open-datasets/global-mining/global_mining_polygons")
    return mining.filter(ee.Filter.inList('AREA', [8.93758181, 3.93418783]))


ee_authenticate(token_name="EARTHENGINE_TOKEN")

ee.Initialize()

st.header("Dome Mine - Timmins, Ontario, Kanada")

row1_col1, row1_col2, row1_col3 = st.columns([1, 2, 1])

Map = geemap.Map(center=(48.458284, -81.240261), zoom=13)
Map.addLayer(get_bound())

indices = ['NDVI', 'EVI', 'NDWI1', 'NDWI2', 'NMDI', 'MSI', 'MSAVI2']
with row1_col3:
    year = st.selectbox("Wybierz rok", years_fun)
    index = st.selectbox("Wybierz wskaźnik", indices)
    lineplot(index, get_bound(), get_data())
    st.markdown(text2[index], unsafe_allow_html=True)

if year:
    if index:
        Map.addLayer(get_index(year, index, get_data()), get_vis_params(year, index, get_data()), index + str(year))
        with (row1_col1):
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
            plot_hist(year, index, get_data())
            Map.add_colorbar(get_vis_params(year, index, get_data()), label=f"Wartość {index}",
                             layer_name=index + str(year))

            with row1_col2:
                st.markdown("<style>padding-top: 10px</style>", unsafe_allow_html=True)
                Map.to_streamlit(height=700)

else:
    with row1_col2:
        Map.to_streamlit(height=700)
