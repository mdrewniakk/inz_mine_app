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
    ROI2 = ee.Geometry.Point(24.117110, 42.549279)
    images_bga = years.map(lambda year: best_image(ee.Number(year), ROI2)).flatten()
    assarel = mining.filter(ee.Filter.inList('AREA', [6.47028179, 9.57015368]))
    dataset2 = calc_indices(images_bga, assarel)
    ROI3 = ee.Geometry.Point(46.147651, 39.146828)
    images_arm = years.map(lambda year: best_image(ee.Number(year), ROI3)).flatten()
    kajaran = mining.filter(ee.Filter.inList('AREA', [4.46054124, 0.94310862, 0.9555462, 0.40513458]))
    dataset3 = calc_indices(images_arm, kajaran)
    data_list = [dataset1, dataset2, dataset3]
    return data_list


st.markdown("Aplikacja")

