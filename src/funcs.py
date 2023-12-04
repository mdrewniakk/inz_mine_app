import ee
import streamlit as st
import geemap.foliumap as geemap
import plotly.express as px
import plotly.graph_objects as go
import numpy as np


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
    return nmdi.rename("NMDI").set('year', date)


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


def best_image(year, roi):
    start_date = ee.Date.fromYMD(year, 1, 1)
    end_date = start_date.advance(1, 'year')
    image = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterBounds(roi) \
        .filterDate(start_date, end_date) \
        .sort("CLOUDY_PIXEL_PERCENTAGE") \
        .first()
    return image


def calc_indices(images, bound):
    count = images.size().getInfo()
    return ee.ImageCollection.fromImages(
        [calculate_indices(ee.Image(images.get(index)).clipToCollection(bound)) for index in range(count)]
    )


def calculate_indices(image):
    return (
        calculate_ndvi(image)
        .addBands(calculate_ndwi1(image))
        .addBands(calculate_ndwi2(image))
        .addBands(calculate_nmdi(image))
        .addBands(calculate_evi(image))
        .addBands(calculate_msi(image).addBands(calculate_msavi(image)))
    )


years_fun = [2018, 2019, 2020, 2021, 2022, 2023]
reducer = ee.Reducer.mean().combine(
    ee.Reducer.median(), sharedInputs=True).combine(ee.Reducer.mode(), sharedInputs=True)


def lineplot(index, bound, data):
    stats_data = data.select(index).toBands().reduceRegion(
        reducer=reducer,
        geometry=bound,
        scale=30
    ).getInfo()

    means = [stats_data[f"{i}_{index}_mean"] for i in range(6)]
    medians = [stats_data[f"{i}_{index}_median"] for i in range(6)]
    modes = [stats_data[f"{i}_{index}_mode"] for i in range(6)]

    fig = go.Figure()

    for name, values in [('Średnia', means), ('Mediana', medians), ('Moda', modes)]:
        fig.add_trace(go.Scatter(x=years_fun, y=values, mode='lines+markers', name=name))

    fig.update_layout(
        title=f'Zmiana statystyk indeksu {index} na przestrzeni lat',
        xaxis_title="Rok",
        yaxis_title='Wartość',
        showlegend=True,
        height=300,
    )

    st.plotly_chart(fig, use_container_width=True)


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
text2 = {"NDWI1": '<div style="text-align: justify;">Wartości poniżej zera wskazują obszary bez wód, między 0 a 0,'
                  '2 oznaczają obszary o niskiej zawartości wód, między 0,2 a 0,5 wskazują na obszary o umiarkowanej '
                  'zawartości wód, a wartości powyżej 0,5 sugerują obszary o wysokiej zawartości wód. Analiza NDWI '
                  'umożliwia monitorowanie zmian wody, identyfikację obszarów podatnych na powodzie i ocenę zasobów '
                  'wodnych, przy uwzględnieniu kontekstu danego obszaru badawczego.</div>',
         "NDVI": '<div style="text-align: justify;">Wartości bliskie -1 wskazują na obszary bez roślinności lub pokryte '
                 'śniegiem, a zakresy między -1 a 0 oraz 0 a 0,2 charakteryzują się niską do umiarkowaną roślinnością, '
                 'obejmując obszary zurbanizowane, pustynie, a także tereny rolnicze. Wartości między 0,2 a 0,'
                 '5 reprezentują obszary o umiarkowanej roślinności, takie jak obszary leśne czy pastwiska, '
                 'natomiast wartości powyżej 0,5 wskazują na obszary o wysokiej roślinności, takie jak gęste lasy '
                 'deszczowe.</div>',
         "NMDI": '<div style="text-align: justify;">Obszary o wartościach NMDI zbliżonych do 1 sygnalizują brak suszy, '
                 'co oznacza dostateczny dostęp do wody dla roślinności. Wartości między -1 a 0 wskazują na umiarkowaną '
                 'suszę, gdzie obszar doświadcza pewnego stopnia deficytu wody, wpływając na zdrowie roślin. W przypadku '
                 'wartości NMDI poniżej -2 można wnioskować, że obszar ten dotknięty jest poważną suszą, co może prowadzić '
                 'do znaczącego stresu wodnego dla roślinności.</div>',
         "MSI": '<div style="text-align: justify;">Wartości powyżej 0 sygnalizują obfitość wilgoci w glebie, '
                'co może wynikać z intensywnych opadów deszczu lub innych warunków sprzyjających wilgotności. Wartości '
                'między 0 a -0,5 wskazują na umiarkowany poziom wilgotności, co może być korzystne dla roślinności. '
                'Obszary o wartościach między -0,5 a -1 doświadczają umiarkowanego do znacznego stresu wilgotnościowego '
                'roślin, co może wpływać na ich zdrowie.</div>',
         "MSAVI2": '<div style="text-align: justify;">Wartości poniżej zera sygnalizują obszary o niskiej roślinności lub '
                   'obszary, gdzie odbicie światła z roślin jest maskowane przez tło glebowe. Zakres między 0 a 0,'
                   '2 może wskazywać na umiarkowaną roślinność, lecz jednocześnie sugerować, że tło glebowe wpływa na '
                   'odbicie światła. Obszary o wartościach między 0,2 a 0,5 charakteryzują się umiarkowaną do wysoką '
                   'roślinnością, gdzie wpływ tła glebowego staje się mniej istotny. Wartości powyżej 0,5 wskazują na '
                   'obszary o dużej gęstości roślinności, gdzie wpływ tła glebowego jest minimalny.</div>',
         "EVI": '<div style="text-align: justify;">Zakres między 0 a 0,2 oznacza obszary o niskiej roślinności lub te '
                'poddane wpływom środowiskowym, takim jak susza czy zanieczyszczenie. Obszary o wartościach między 0,'
                '2 a 0,5 sugerują umiarkowaną gęstość roślinności, obejmując obszary rolnicze lub lasy o umiarkowanej '
                'gęstości drzew. Wartości między 0,5 a 0,8 charakteryzują obszary o dużej gęstości roślinności, '
                'takie jak bujne lasy deszczowe, ogrody czy obszary intensywnego rolnictwa.</div>',
         "NDWI2": '<div style="text-align: justify;">Wartości poniżej zera wskazują obszary bez wód, między 0 a 0,'
                  '2 oznaczają obszary o niskiej zawartości wód, między 0,2 a 0,5 wskazują na obszary o umiarkowanej '
                  'zawartości wód, a wartości powyżej 0,5 sugerują obszary o wysokiej zawartości wód. Analiza NDWI '
                  'umożliwia monitorowanie zmian wody, identyfikację obszarów podatnych na powodzie i ocenę zasobów '
                  'wodnych, przy uwzględnieniu kontekstu danego obszaru badawczego.</div>'}


def get_vis_params(year, index, data):
    nlcd = data.filter(ee.Filter.eq("year", year)).first()
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


def get_index(year, index, data):
    nlcd = data.filter(ee.Filter.eq("year", year)).first()
    return nlcd.select(index)


def latest_image(roi):
    image = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterBounds(roi) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10)) \
        .sort('system:time_start', False) \
        .first()
    return image


def plot_hist(year, index, data):
    values = get_index(year, index, data).reduceRegion(
        reducer=ee.Reducer.toList(),
        geometry=get_index(year, index, data).geometry(),
        scale=40
    ).getInfo()[index]

    BINS = 20
    y, x = np.histogram(values, bins=BINS)
    x = [(a + b) / 2 for a, b in zip(x, x[1:])]
    fig = px.bar(x=x, y=y, color=x, color_continuous_scale=palettes_hist[index]
                 ).update_layout(title=f'Histogram rozkładu wartości {index}', xaxis_title='Wartość',
                                 yaxis_title='Ilość wystąpień', height=500)
    st.plotly_chart(fig, use_container_width=True)
