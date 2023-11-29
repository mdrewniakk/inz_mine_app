import ee
import streamlit as st
import geemap.foliumap as geemap
import plotly.express as px
import plotly.graph_objects as go
import numpy as np


# Get an NLCD image by year.
@st.cache_data
def ee_authenticate(token_name="EARTHENGINE_TOKEN"):
    geemap.ee_initialize(token_name=token_name)


ee_authenticate(token_name="EARTHENGINE_TOKEN")

ee.Initialize()


def calculate_ndvi(image):
    date = ee.Date(image.get('system:time_start')).get('year')
    image = image.divide(10000)
    return (image.select('B8').subtract(image.select('B4'))).divide(image.select('B8').add(image.select('B4'))).rename(
        'NDVI').set('year', date)


def calculate_ndwi1(image):
    date = ee.Date(image.get('system:time_start')).get('year')
    image = image.divide(10000)
    return (image.select('B8A').subtract(image.select('B12'))).divide(
        image.select('B8A').add(image.select('B12'))).rename('NDWI1').set('year', date)


def calculate_ndwi2(image):
    date = ee.Date(image.get('system:time_start')).get('year')
    image = image.divide(10000)
    return (image.select('B3').subtract(image.select('B8'))).divide(image.select('B8').add(image.select('B3'))).rename(
        'NDWI2').set('year', date)


def calculate_evi(image):
    date = ee.Date(image.get('system:time_start')).get('year')
    image = image.divide(10000)
    evi = image.expression(
        '2.5 * (NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1)', {
            'NIR': image.select('B8'),
            'RED': image.select('B4'),
            'BLUE': image.select('B2')
        })
    return evi.rename('EVI').set('year', date)


def calculate_nmdi(image):
    date = ee.Date(image.get('system:time_start')).get('year')
    image = image.divide(10000)
    nmdi = image.expression(
        '(NIR - (SWIR1-SWIR2)) / (NIR + (SWIR1 - SWIR2))', {
            'NIR': image.select('B8A'),
            'SWIR1': image.select('B11'),
            'SWIR2': image.select('B12')})
    mask = nmdi.lt(2).And(nmdi.gt(0))
    return nmdi.rename("NMDI").set('year', date).updateMask(mask)


def calculate_msavi(image):
    date = ee.Date(image.get('system:time_start')).get('year')
    image = image.divide(10000)
    msavi = image.expression(
        '(2*NIR + 1 - sqrt((2*NIR+1)**2-8*(NIR-RED)))/2', {
            'NIR': image.select('B8'),
            'RED': image.select('B4')})
    return msavi.rename('MSAVI2').set('year', date)


def calculate_msi(image):
    date = ee.Date(image.get('system:time_start')).get('year')
    image = image.divide(10000)
    msi = image.select('B11').divide(image.select('B8A'))
    return msi.rename('MSI').set('year', date)


def best_image(year):
    start_date = ee.Date.fromYMD(year, 1, 1)
    end_date = start_date.advance(1, 'year')
    image_collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterBounds(ROI) \
        .filterDate(start_date, end_date) \
        .sort("CLOUDY_PIXEL_PERCENTAGE")
    image = ee.Image(image_collection.toList(image_collection.size()).get(1))
    return image


def calc_indices(images, bound):
    bandlist = []
    for index in range(0, count):
        image = ee.Image(images.get(index)).clipToCollection(bound)
        im = calculate_ndvi(image).addBands(calculate_ndwi1(image)).addBands(calculate_ndwi2(image)).addBands(
            calculate_nmdi(image)).addBands(calculate_evi(image)).addBands(
            calculate_msi(image).addBands(calculate_msavi(image)))
        bandlist.append(im)
    col = ee.ImageCollection.fromImages(bandlist)
    return col


def lineplot(index, bound):
    # Retrieve data in a single call
    stats_data = dataset.select(index).toBands().reduceRegion(
        reducer=reducer,
        geometry=bound,
        scale=30  # Adjust the scale as needed
    ).getInfo()

    # Extract mean, median, and mode values using list comprehension
    means = [stats_data[f"{i}_{index}_mean"] for i in range(6)]
    medians = [stats_data[f"{i}_{index}_median"] for i in range(6)]
    modes = [stats_data[f"{i}_{index}_mode"] for i in range(6)]

    # Create the plot
    fig = go.Figure()

    # Add traces for means, medians, and modes
    for name, values in [('Średnia', means), ('Mediana', medians), ('Moda', modes)]:
        fig.add_trace(go.Scatter(x=years, y=values, mode='lines+markers', name=name))

    # Update layout
    fig.update_layout(
        title=f'Zmiana statystyk indeksu {index} na przestrzeni lat',
        xaxis_title="Rok",
        yaxis_title='Wartość',
        showlegend=True
    )

    st.plotly_chart(fig, use_container_width=True)

    # Show the Plotly chart


palettes_gee = {"NDWI1": 'RdBu', "NDVI": 'RdYlGn', "NMDI": 'YlGnBu', "EVI": 'Greens', 'MSAVI2': 'YlGn', "NDWI2": "gray",
                "MSI": "RdBu_r"}
palettes_hist = {"NDWI1": px.colors.diverging.RdBu, "NDVI": px.colors.diverging.RdYlGn,
                 "NMDI": px.colors.sequential.YlGnBu, "EVI": px.colors.sequential.Greens,
                 "MSAVI2": px.colors.sequential.YlGn, "NDWI2": px.colors.sequential.gray,
                 "MSI": px.colors.diverging.RdBu_r}
text = {
    "NDWI1": '<div style="text-align: justify;">Indeks NDWI (Normalized Difference Water Index) to wskaźnik '
             'teledetekcyjny wykorzystywany do identyfikowania obszarów wody na podstawie danych obrazów '
             'satelitarnych. Oba warianty NDWI mają na celu wykorzystanie różnic wchłaniania i odbicia światła przez '
             'wodę oraz inne powierzchnie, takie jak ląd, co umożliwia ich skuteczną identyfikację na obrazach '
             'satelitarnych. Wartości indeksu są niższe w obszarach wodnych i wyższe na obszarach lądowych, '
             'co ułatwia wykrywanie ciał wodnych, takich jak jeziora, rzeki czy zbiorniki wodne.</div>',
    "NDVI": '<div style="text-align: justify;">Normalized Difference Vegetation Index (NDVI) to indeks wegetacyjny '
            'używany w zdalnym odczycie do oceny zdrowia roślin i ilości roślinności na powierzchni ziemi. Jest to '
            'jedno z najczęściej stosowanych narzędzi do monitorowania zmian w pokrywie roślinnej na podstawie '
            'obrazów satelitarnych lub lotniczych.</div>',
    "NMDI": '<div style="text-align: justify;">Normalizowany Wielopasmowy Indeks Suszy (NMDI) to indeks zdalnego '
            'odczytu używany do oceny warunków suszy na podstawie obrazów satelitarnych. Zaprojektowany jest, '
            'aby uchwycić zmiany w zdrowiu roślin związane z dostępnością wody. NMDI zazwyczaj wykorzystuje dane z '
            'pasm bliskiej podczerwieni (NIR) i krótkofalowej podczerwieni (SWIR) z multispektralnych danych '
            'satelitarnych.</div>',
    "MSI": '<div style="text-align: justify;">Moisture Stress Index (MSI) to indeks stresu wilgotności, który jest '
           'używany w teledetekcji i badaniach ekologicznych do oceny stopnia stresu wilgotności roślinności. Ten '
           'indeks jest szczególnie przydatny w monitorowaniu obszarów rolniczych i naturalnych środowisk, '
           'aby ocenić wpływ warunków wilgotności na rośliny.</div>',
    "MSAVI2": '<div style="text-align: justify;">Indeks MSAVI2 (Modified Soil-Adjusted Vegetation Index 2) jest '
              'używany głównie do monitorowania zdrowia roślinności i oceny warunków środowiskowych, takich jak '
              'wilgotność gleby. Jest stosowany w różnych obszarach, takich jak rolnictwo, leśnictwo, czy ekologia, '
              'aby badać zmiany w roślinności związane z warunkami środowiskowymi, takimi jak susza, choroby roślin, '
              'czy zmiany w składzie gleby.</div>',
    "EVI": '<div style="text-align: justify;">Indeks EVI (Enhanced Vegetation Index) to wskaźnik teledetekcyjny '
           'wykorzystywany do oceny zdrowia roślinności na podstawie danych obrazów satelitarnych. Podobnie jak NDVI, '
           'indeks EVI mierzy różnice wchłaniania światła w obszarze czerwonym i bliskiego podczerwonego przez '
           'rośliny. Jednak EVI wprowadza dodatkowe korekty, które poprawiają jego wydajność w warunkach, gdzie NDVI '
           'może być mniej dokładny, np. w obszarach o gęstej roślinności lub w przypadku obrazów o niskiej '
           'jakości.</div>',
    "NDWI2": '<div style="text-align: justify;">Indeks NDWI (Normalized Difference Water Index) to wskaźnik '
             'teledetekcyjny wykorzystywany do identyfikowania obszarów wody na podstawie danych obrazów '
             'satelitarnych. Oba warianty NDWI mają na celu wykorzystanie różnic wchłaniania i odbicia światła przez '
             'wodę oraz inne powierzchnie, takie jak ląd, co umożliwia ich skuteczną identyfikację na obrazach '
             'satelitarnych. Wartości indeksu są niższe w obszarach wodnych i wyższe na obszarach lądowych, '
             'co ułatwia wykrywanie ciał wodnych, takich jak jeziora, rzeki czy zbiorniki wodne.</div>'
}
equations = {"NDVI": r'''NDVI\:=\:\frac{NIR-RED}{NIR+RED}''',
             "EVI": r'''EVI\:=\frac{2.5\left(NIR-RED\right)}{\left(\left(NIR+6RED-7.5BLUE\right)+1\right)}''',
             "NDWI1": r'''NDWI\left(I\right)\:=\:\frac{NIR\:-\:SWIR2}{NIR+SWIR2}''',
             "NDWI2": r'''NDWI\left(II\right)\:=\:\frac{GREEN\:-\:NIR}{GREEN\:+\:NIR}''',
             "NMDI": r'''NMDI\:=\frac{\left(NIR-SWIR\right)}{\left(NIR\:+\:SWIR\right)}''',
             "MSI": r'''MSI\:=\:\frac{SWIR1}{NIR}''',
             "MSAVI2": r'''MSAVI2\:=\:\frac{2NIR+1-\sqrt{\left(2NIR+1\right)^2-8\left(NIR-RED\right)}}{2}'''}


def get_vis_params(year, index):
    nlcd = dataset.filter(ee.Filter.eq("year", year)).first()
    im = nlcd.select(index)
    mean = im.reduceRegion(
        ee.Reducer.mean(), scale=40).getInfo()[index]
    sd = im.reduceRegion(
        ee.Reducer.stdDev(), scale=40).getInfo()[index]
    vis_param = {
        'min': mean - (sd * 3),
        'max': mean + (sd * 3),
        'palette': palettes_gee[index],
    }
    return vis_param


def get_index(year, index):
    nlcd = dataset.filter(ee.Filter.eq("year", year)).first()
    return nlcd.select(index)


def latest_image():
    image = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterBounds(ROI) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10)) \
        .sort('system:time_start', False) \
        .first()
    return image


def plot_hist(year, index):
    values = get_index(year, index).reduceRegion(
        reducer=ee.Reducer.toList(),
        geometry=get_index(year, index).geometry(),
        scale=40  # Adjust scale as needed
    ).getInfo()[index]

    # use numpy to generate histogram
    BINS = 60
    y, x = np.histogram(values, bins=BINS)
    # bin edges to midpoint
    x = [(a + b) / 2 for a, b in zip(x, x[1:])]
    fig = px.bar(x=x, y=y, color=x, color_continuous_scale=palettes_hist[index]
                 ).update_layout(title='Histogram rozkładu wartości indeksu', xaxis_title='Wartość',
                                 yaxis_title='Ilość wystąpień')
    st.plotly_chart(fig, use_container_width=True)

    if add_legend:
        Map.add_colorbar(get_vis_params(year, index), label=f"Wartość {index}", layer_name=index + str(year))


mining = ee.FeatureCollection("projects/sat-io/open-datasets/global-mining/global_mining_polygons")
Map = geemap.Map(center=(39.146828, 46.147651), zoom=13)
ROI = ee.Geometry.Point(46.147651, 39.146828)
start_year = 2018
end_year = 2022
kajaran = mining.filter(ee.Filter.inList('AREA', [4.46054124, 0.94310862, 0.9555462, 0.40513458]))
Map.addLayer(kajaran)
years = ee.List.sequence(start_year, end_year)
year_list = years.getInfo()
images_arm = years.map(best_image)
images_arm = images_arm.add(latest_image())
count = images_arm.size().getInfo()
dataset = calc_indices(images_arm, kajaran)
st.header("Kajaran Mine - Armenia")

# Create a layout containing two columns, one for the map and one for the layer dropdown list.
row1_col1, row1_col2, row1_col3 = st.columns([1, 2, 1])

# Create an interactive map
reducer = ee.Reducer.mean().combine(
    ee.Reducer.median(), sharedInputs=True).combine(ee.Reducer.mode(), sharedInputs=True)

# Convert the reduced collection to a FeatureCollection


# Select the seven NLCD epochs after 2000.
years = [2018, 2019, 2020, 2021, 2022, 2023]
indices = ['NDVI', 'EVI', 'NDWI1', 'NDWI2', 'NMDI', 'MSI', 'MSAVI2']
with row1_col3:
    year = st.selectbox("Wybierz rok", years)
    index = st.selectbox("Wybierz wskaźnik", indices)
    add_legend = st.checkbox("Pokaż legendę")
    lineplot(index, kajaran)

if year:
    if index:
        Map.addLayer(get_index(year, index), get_vis_params(year, index), index + str(year))

        with (row1_col1):
            st.markdown(text[index], unsafe_allow_html=True)
            st.latex(equations[index])
            plot_hist(year, index)
            with row1_col2:
                Map.to_streamlit(height=600)

else:
    with row1_col2:
        Map.to_streamlit(height=600)
