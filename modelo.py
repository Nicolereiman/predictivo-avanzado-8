# -*- coding: utf-8 -*-
"""Modelo Deploy Final.ipynb

##### Trabajo practico II - Analisis predictivo avanzado
### PASO 1: Importar librerias
"""
import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import warnings
import datetime
import pytz
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from collections import defaultdict
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split, KFold, GridSearchCV, cross_val_score, StratifiedKFold
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, auc, RocCurveDisplay
from sklearn.preprocessing import FunctionTransformer, StandardScaler, MinMaxScaler
from sklearn.pipeline import FeatureUnion, Pipeline
import xgboost as xgb
import matplotlib.colors as mcolors
from pandas.plotting import scatter_matrix
import geopy
import geopy.distance as distance
import shapely.wkt
from shapely.geometry import LineString, Point
from PIL import Image




### PASO 2: Preparación de la base

# CARGAMOS EL DATASET #
df = pd.read_csv('ClimateChange.csv')

# ESTANDARIZAMOS LAS FECHAS #
import pandas as pd
from datetime import datetime

from datetime import datetime

def separar_fecha(df, columna):
    # Itera sobre las filas del DataFrame
    for index, fila in df.iterrows():
        fecha = fila[columna]

        if "-" in fecha:
            # Convierte la cadena de fecha al objeto datetime
            fecha_obj = datetime.strptime(fecha, '%Y-%d-%m')
        else:
            # Convierte la cadena de fecha al objeto datetime para el caso sin "-"
            fecha_obj = datetime.strptime(fecha, '%d/%m/%Y')

        # Agrega columnas al DataFrame para día, mes, año y fecha formateada
        df.at[index, "dia"] = int(fecha_obj.day)
        df.at[index, "mes"] = int(fecha_obj.month)
        df.at[index, "anio"] = int(fecha_obj.year)
        df.at[index, "dt"] = fecha_obj.strftime('%d/%m/%Y')

    return df


# CONVERTIR LAS COORDENADAS #
def convertir_coordenadas(coordenada):
    deg = float(coordenada[:-1])
    direction = coordenada[-1]
    decimal_coord = deg if direction.upper() in ['N', 'E'] else -deg if direction.upper() in ['S', 'W'] else None
    return decimal_coord

df = separar_fecha(df, "dt")
df['Latitude'] = df['Latitude'].apply(convertir_coordenadas)
df['Longitude'] = df['Longitude'].apply(convertir_coordenadas)

df['dt'] = pd.to_datetime(df['dt'])

df = df[df['dt'].dt.year >= 2000]

##### Imputacion de missings

df['dt'] = pd.to_datetime(df['dt'])
city_monthly_mean = df.groupby(['City', df['dt'].dt.month])['AverageTemperature'].mean()
city_monthly_mean1 = df.groupby(['City', df['dt'].dt.month])['AverageTemperatureUncertainty'].mean()

for index, row in df.iterrows():
    city = row['City']
    month = row['dt'].month
    if pd.isnull(row['AverageTemperature']):
        mean_value = city_monthly_mean.get((city, month))
        df.at[index, 'AverageTemperature'] = mean_value
    if pd.isnull(row['AverageTemperatureUncertainty']):
        mean_value1 = city_monthly_mean1.get((city, month))
        df.at[index, 'AverageTemperatureUncertainty'] = mean_value1

from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.arima.model import ARIMA
from skopt import gp_minimize
from skopt.space import Integer
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_squared_error
from math import sqrt
from sklearn.metrics import mean_squared_error
from math import sqrt
import matplotlib.pyplot as plt
from functools import partial
from pmdarima import auto_arima


def esEstacionaria(series):
    result = adfuller(series)
    return result[1] < 0.05


def prediccionTemperaturaPromedioARIMA(pais, cantmeses):
  #Transformaciones de la base
  dfnuevo = df[df['Country'] == pais]
  dfnuevo['anio_mes'] = dfnuevo['dt'].dt.strftime('%Y-%m')
  dfmundo = dfnuevo.groupby('anio_mes')['AverageTemperature'].mean().reset_index()
  dfmundo['anio_mes'] = pd.to_datetime(dfmundo['anio_mes'])
  dfmundo = dfmundo.set_index('anio_mes')
  y = dfmundo['AverageTemperature'].resample('MS').mean()
  #Hacemos particion del dataset para obtener los mejores hiperparametros
  dfmundoSERIES = dfmundo.iloc[:, 0]
  X = dfmundoSERIES.values
  d = 0 if esEstacionaria(dfmundoSERIES) else 1
  history = [x for x in dfmundoSERIES.values]
  predictions = []
  order = (3,d,10)
  print(order)
  model = ARIMA(history, order=order)
  model_fit = model.fit()
  predictions = model_fit.forecast(steps=cantmeses)
  fecha_inicio = dfmundoSERIES.index[-1]
  fechas = pd.date_range(start=fecha_inicio, periods=cantmeses + 1, freq='MS')[1:]
  df_predicciones = pd.DataFrame({'Fecha': fechas, 'Prediccion_Temperatura': predictions})
  return df_predicciones


st.title('App de predicción de temperatura')

### Por último: Preparación de la app
#Insert a picture
# First, read it with PIL
image = Image.open('foto.jpg')
# Load Image in the App
st.image(image)

#st.title("Ejemplo" )
#st.write(f"Predicciones de temperatura los próximos 10 meses en india:")
#predictions_df=prediccionTemperaturaPromedioARIMA('India', 10)


countries = [
    "Côte D'Ivoire", "Ethiopia", "India", "Syria", "Egypt", "Turkey",
    "Iraq", "Thailand", "Brazil", "Germany", "Colombia", "South Africa", "Morocco",
    "China", "United States", "Senegal", "Tanzania", "Bangladesh", "Pakistan",
    "Zimbabwe", "Vietnam", "Nigeria", "Indonesia", "Saudi Arabia", "Afghanistan",
    "Ukraine", "Congo (Democratic Republic Of The)", "Peru", "United Kingdom",
    "Angola", "Spain", "Philippines", "Iran", "Australia", "Mexico", "Somalia",
    "Canada", "Russia", "Japan", "Kenya", "France", "Burma", "Italy", "Chile",
    "Dominican Republic", "South Korea", "Singapore", "Taiwan", "Sudan"
]
# Dropdown for selecting a country
selected_country = st.selectbox("Elegí un país:", countries)


    
# Slider
st.text("")
st.text('Mes')
selected_months=st.slider('<-- Deslizá a los costados -->', min_value=0, max_value=12, value=6, step=1)



st.title("Resultado" )
st.write(f"Predicciones de temperatura los próximos {selected_months} meses en {selected_country}:")
predictions_df=prediccionTemperaturaPromedioARIMA(selected_country, selected_months)
st.dataframe(predictions_df, height=300)
