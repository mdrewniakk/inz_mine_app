import streamlit as st
import geemap.foliumap as geemap


st.set_page_config(layout="wide")
@st.cache_data
def ee_authenticate(token_name="EARTHENGINE_TOKEN"):
    geemap.ee_initialize(token_name=token_name)


ee_authenticate(token_name="EARTHENGINE_TOKEN")

st.markdown("Aplikacja")

st.image("https://i.imgur.com/VvBuFkR.jpg")