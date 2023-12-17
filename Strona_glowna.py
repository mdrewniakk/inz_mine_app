import streamlit as st
st.set_page_config(layout="wide")
import geemap.foliumap as geemap
import ee
from src.funcs import best_image, calc_indices


@st.cache_data
def ee_authenticate(token_name="EARTHENGINE_TOKEN"):
    geemap.ee_initialize(token_name=token_name)


ee_authenticate(token_name="EARTHENGINE_TOKEN")
@st.cache_data
def get_data():
    ROI = ee.Geometry.Point(18.629901, 52.010558)
    start_year = 2018
    end_year = 2023
    years = ee.List.sequence(start_year, end_year)
    images_pol = years.map(lambda year: best_image(ee.Number(year), ROI)).flatten()    #images_arm = images_arm.add(latest_image(ROI))
    mining = ee.FeatureCollection("projects/sat-io/open-datasets/global-mining/global_mining_polygons")
    adamow = mining.filter(ee.Filter.eq("system:index", "000000000000000016ed"))
    dataset1 = calc_indices(images_pol, adamow)
    ROI2 = ee.Geometry.Point(-63.384707, 7.454339)
    images_ven = years.map(lambda year: best_image(ee.Number(year), ROI2)).flatten()
    cerro = mining.filter(ee.Filter.eq("system:index", "0000000000000000354a"))
    dataset2 = calc_indices(images_ven, cerro)
    ROI3 = ee.Geometry.Point(-81.240261, 48.458284)
    images_can = years.map(lambda year: best_image(ee.Number(year), ROI3)).flatten()
    dome = mining.filter(ee.Filter.inList('AREA', [8.93758181, 3.93418783]))
    dataset3 = calc_indices(images_can, dome)
    ROI4 = ee.Geometry.Point(22.968868, -28.393550)
    images_rpa = years.map(lambda year: best_image(ee.Number(year), ROI4)).flatten()
    kolomela = mining.filter(ee.Filter.eq("system:index", "00000000000000002655"))
    dataset4 = calc_indices(images_rpa, kolomela)
    data_list = [dataset1, dataset2, dataset3, dataset4]
    return data_list


st.markdown("Aplikacja")

