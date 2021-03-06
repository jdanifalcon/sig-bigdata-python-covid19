# -*- coding: utf-8 -*-
"""Visualizacion-COVID-Tabasco.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1KmkAiqyiG53uHLAr5v9Zbyc0tFJ4-R3z

# Visualización de datos abiertos de COVID-19 en México

* Jessica Daniela O. Falcón (Estudiante, Twitter: [@jdanielafalcon](https://twitter.com/jdanielafalcon)
)

En esta actividad de capacitación, se manejo Python junto con [la base de datos abiertos](https://www.gob.mx/salud/documentos/datos-abiertos-152127) que publica diariamente la Dirección General de Epidemiología de la Secretaría de Salud.

La base de datos es grande y tiene varias complejidades que se fueron revisando. El objetivo es utilizar este recurso de información y que, al hacerlo, se desarrollen gráficas y mapas utilizando librerías de Python.

Los pasos estan organizados de la siguiente forma:

* Instalación de dependencias
* Descarga de datos y exploración del contenido
* *Aplanado* de los datos
* Agregados diarios (casos, defunciones)
* Gráficas
* Mapas

Realizado durante la semana de capacitación "Escuela de Verano CentroGeo 2021"
Impartido por el:
[Laboratorio Nacional de Geointeligencia](http://www.geoint.mx/)

* Pablo López-Ramírez (CentroGeo, Twitter: [@oskrsasi](https://twitter.com/oskrsasi)
)
* Oscar Sánchez-Siordia (CentroGeo, Twitter: [@plablo09](https://twitter.com/plablo09))

## Instalación de dependencias

La mayor parte del taller utilizaremos principalmente la librería [Pandas](https://pandas.pydata.org/) para el análisis de datos, esta librería viene incluida en el stack que nos provee automáticamente COlab. Sin embargo, para poder leer datos geográficos y hacer mapas, vamos a necesitar instalar [Geopandas](https://geopandas.org/), que es una extensión de Pandas para el manejo de datos geográficos, y un par de librerías más para hacer mapas interactivos. 

La instalación de dependencias en Colab es relativamente sencilla, el caso de Geopandas tiene elguna complicación porque requiere de la instalación de un par de librerías del sistema (es decir, librerías que no son sólo de Python). La siguiente celda contiene las instrucciones (al sistema operativo debajo de Colab, noten el símbolo `!` al inicio de cada instrucción) para instalar todas las dependencias que necesitamos.
"""

# Commented out IPython magic to ensure Python compatibility.
# %%time 
# 
# # Important library for many geopython libraries
# !apt install gdal-bin python-gdal python3-gdal 
# # Install rtree - Geopandas requirment
# !apt install python3-rtree 
# # Install Geopandas
# !pip install git+git://github.com/geopandas/geopandas.git
# # Install descartes - Geopandas requirment
# !pip install descartes 
# # Install Folium for Geographic data visualization
# !pip install folium
# # Install plotlyExpress
# !pip install plotly_express
# !pip install mapclassify

"""Ahora vamos a importar de una vez todas las dependencias que vamos a usar en el resto del notebook"""

import os
import glob
import itertools
from pathlib import Path
import zipfile
import numpy as np
import pandas as pd
import geopandas as gpd
from datetime import timedelta, date, datetime
import csv
import openpyxl
import requests
import plotly.express as px
import mapclassify
import folium

import logging

"""## Descargar datos

El primer paso es, evidentemente, descargar los datos. Es claro que podríamos ir a la [página](https://www.gob.mx/salud/documentos/datos-abiertos-152127) de la Dirección General de Epidemiología (DGE) y descargarlos, sin embargo, lo vamos a hacer por el camino difícil de bajarlos usando Python.

Para eso, vamos a definir una función que tome como argumento la fecha para la que queremos descargar los datos y el *path* en donde los vamos a guardar. La función es relativamente simple, sólo hace un *request* al archivo histórico de la DGE y guarda los datos en la ruta configurada.

Para trabajar vamos siempre a descargar tres archivos:

* Los datos COVID-19 
* El catálogo de campos
* El archivo de descripción

El primer archivo contiene la serie de tiempo de seguimiento de casos hasta la fecha configurada, los dos archivos restantes sirven para entender la información contenida en los datos.

Entonces, primero definimos la función
"""

def bajar_datos_salud(directorio_datos='/content/', fecha='05-05-2021'):
    '''
        Descarga el archivo de datos y los diccionarios para la fecha solicitada.
    '''
    fecha = datetime.strptime(fecha, "%d-%m-%Y")
    url_salud_historicos = 'http://datosabiertos.salud.gob.mx/gobmx/salud/datos_abiertos/historicos/'    
    archivo_nombre = f'{fecha.strftime("%y%m%d")}COVID19MEXICO.csv.zip'
    archivo_ruta = os.path.join(directorio_datos, archivo_nombre)
    url_diccionario = 'http://datosabiertos.salud.gob.mx/gobmx/salud/datos_abiertos/diccionario_datos_covid19.zip'
    diccionario_ruta = os.path.join(directorio_datos, 'diccionario.zip')
    if os.path.exists(archivo_ruta):
        logging.debug(f'Ya existe {archivo_nombre}')
    else:
        print(f'Bajando datos {fecha.strftime("%d.%m.%Y")}')
        url_dia = "{}/{}/datos_abiertos_covid19_{}.zip".format(fecha.strftime('%Y'),
                                                                fecha.strftime('%m'),
                                                                fecha.strftime('%d.%m.%Y'))
        url = url_salud_historicos + url_dia
        r = requests.get(url, allow_redirects=True)
        open(archivo_ruta, 'wb').write(r.content)
        r = requests.get(url_diccionario, allow_redirects=True)
        open(diccionario_ruta, 'wb').write(r.content)
        with zipfile.ZipFile(diccionario_ruta, 'r') as zip_ref:
          zip_ref.extractall(directorio_datos)

"""Con la función que acabamos de definir, podemos bajar los datos hasta la última fecha disponible"""

ayer = datetime.now() - timedelta(1)
bajar_datos_salud(fecha=ayer.strftime('%d-%m-%Y'))

"""## Exploración del contenido

Antes de empezar a manipular los datos, lo primero que tenemos que hacer es explorarlos brevemente y entender cómo están guardados. Leamos los datos en un DataFrame.

Fíjense en la ruta en donde la función de arriba descarga los datos, con la barra exploradora del lado izquierdo pueden navegar hasta esa ruta y copiar el *path*
"""

df = pd.read_csv('/content/210713COVID19MEXICO.csv.zip', dtype=object, encoding='latin-1')
df

"""Cada renglón en la base de datos corresponde a un caso en *seguimiento*, el resultado de cada caso se puede actualizar en sucesivas publicaciones de la base de datos. Las columnas describen un conjunto de variables asociadas al seguimiento de cada uno de los casos. Las dos primeras columnas corresponden a la fecha en la que se actualizó el caso y a un id único para cada caso respectivamente, en este taller no vamos a usar esas dos columnas.

Luego vienen un conjunto de columnas que describen la unidad médica de reporte y, después, las columnas que nos interesan más, que son las que describen al paciente.

Para entender un poco mejor los datos, conviene leer el archívo de catálogo. Pueden descargarlo en el explorador de archivos del lado izquierdo, pero aquí vamos a abrirlo y explorarlo un poco con Pandas. Como el catálogo es un archivo de excel con varias hojas, lo vamos a leer usando [openpyxl]() que nos va a devolver un diccionario de DataFrames que relacionan el nombre de la hoja con los datos que contiene.
"""

catalogos = '/content/201128 Catalogos.xlsx'
nombres_catalogos = ['Catálogo de ENTIDADES', # Acá están los nombres de las hojas del excel
                      'Catálogo MUNICIPIOS',
                      'Catálogo SI_NO',
                      'Catálogo TIPO_PACIENTE',
                      'Catálogo CLASIFICACION_FINAL',
                      'Catálogo RESULTADO_LAB'
                     ]
dict_catalogos = pd.read_excel(catalogos,
                          nombres_catalogos,
                          dtype=str,
                          engine='openpyxl')
clasificacion_final = dict_catalogos['Catálogo CLASIFICACION_FINAL']
clasificacion_final.columns = ["CLAVE", "CLASIFICACIÓN", "DESCRIPCIÓN"] # Aquí le damos nombre a las columnas porque en el excel se saltan dos líneas
clasificacion_final

"""Lo que estamos viendo aquí es el catálogo de datos de la columna `CLASIFICACION_FINAL`. Este catálogo relaciona el valor de la `CLAVE` con su significado. En particular, la columna `CLASIFICACION_FINAL` es la que nos permite identificar los casos positivos como veremos más adelante.

El resto de los catálogos funciona de la misma forma, aunque en este taller sólo trabajaremos con los datos de la clasificación de los pacientes

## *Aplanado* de los datos

Como ya vimos, la información viene codificada, entonces para utilizarla con más facilidad, nos conviene *aplanar* la codificación utilizando los valores que vienen en los catálogos y descriptores de datos.

Para eso vamos a utilizar dos funciones, una que carga los datos que acabamos de bajar y llena los campos a partir de la información que viene en los catálogos y descriptores y otra que simplemente procesa las fechas para tenerlas en un formato más amistoso.

La función también toma un argumento opcional para seleccionar una entidad en específico. En este caso siempre vamos a seleccionar alguna entidad, ya que la base completa es demasiado grande para procesarla en Colab. Noten cómo la selección de la entidad se hace sobre la entidad de residencia del paciente (campo `ENTIDAD_RES`), esto quiere decir que, para cada estado sólo estamos tomando los pacientes que residen en el.
"""

def carga_datos_covid19_MX(fecha='210505', resolver_claves='si_no_binarias', entidad='27'):
    """
        Lee en un DataFrame el CSV con el reporte de casos de la Secretaría de Salud de México publicado en una fecha dada. Esta función
        también lee el diccionario de datos que acompaña a estas publicaciones para preparar algunos campos, en particular permite la funcionalidad
        de generar columnas binarias para datos con valores 'SI', 'No'.

        **Nota**: En esta versión la ruta esta y nombre de los archivos es fija. Asumimos que existe un directorio '/content/'
        donde se encuentran todos los archivos.

        **Nota 2**: Por las actualizaciones a los formatos de datos, esta función sólo va a servir para archivos posteriores a 20-11-28

        resolver_claves: 'sustitucion', 'agregar', 'si_no_binarias', 'solo_localidades'. Resuelve los valores del conjunto de datos usando el
        diccionario de datos y los catálogos. 'sustitucion' remplaza los valores en las columnas, 'agregar'
        crea nuevas columnas. 'si_no_binarias' cambia valores SI, NO, No Aplica, SE IGNORA, NO ESPECIFICADO por 1, 0, 0, 0, 0 respectivamente.

    """
    fecha_formato = '201128'
    nuevo_formato = True
    fecha_carga = pd.to_datetime(fecha, yearfirst=True)
    if fecha_carga < datetime.strptime('20-11-28', "%y-%m-%d"):
      raise ValueError('La fecha debe ser posterior a 20-11-28.')
    
    catalogos=f'/content/{fecha_formato} Catalogos.xlsx'
    descriptores=f'/content/{fecha_formato} Descriptores.xlsx'    
    data_file = os.path.join('/content/', f'{fecha}COVID19MEXICO.csv.zip')
    df = pd.read_csv(data_file, dtype=object, encoding='latin-1')
    if entidad is not None:
      df = df[df['ENTIDAD_RES'] == entidad]
    # Hay un error y el campo OTRA_COMP es OTRAS_COMP según los descriptores
    df.rename(columns={'OTRA_COM': 'OTRAS_COM'}, inplace=True)
    # Asignar clave única a municipios
    df['MUNICIPIO_RES'] = df['ENTIDAD_RES'] + df['MUNICIPIO_RES']
    df['CLAVE_MUNICIPIO_RES'] = df['MUNICIPIO_RES']
    # Leer catalogos
    nombres_catalogos = ['Catálogo de ENTIDADES',
                         'Catálogo MUNICIPIOS',
                         'Catálogo RESULTADO',
                         'Catálogo SI_NO',
                         'Catálogo TIPO_PACIENTE']
    if nuevo_formato:
        nombres_catalogos.append('Catálogo CLASIFICACION_FINAL')
        nombres_catalogos[2] = 'Catálogo RESULTADO_LAB'

    dict_catalogos = pd.read_excel(catalogos,
                              nombres_catalogos,
                              dtype=str,
                              engine='openpyxl')

    entidades = dict_catalogos[nombres_catalogos[0]]
    municipios = dict_catalogos[nombres_catalogos[1]]
    tipo_resultado = dict_catalogos[nombres_catalogos[2]]
    cat_si_no = dict_catalogos[nombres_catalogos[3]]
    cat_tipo_pac = dict_catalogos[nombres_catalogos[4]]
    # Arreglar los catálogos que tienen mal las primeras líneas
    dict_catalogos[nombres_catalogos[2]].columns = ["CLAVE", "DESCRIPCIÓN"]
    dict_catalogos[nombres_catalogos[5]].columns = ["CLAVE", "CLASIFICACIÓN", "DESCRIPCIÓN"]

    if nuevo_formato:
        clasificacion_final = dict_catalogos[nombres_catalogos[5]]


    # Resolver códigos de entidad federal
    cols_entidad = ['ENTIDAD_RES', 'ENTIDAD_UM', 'ENTIDAD_NAC']
    df['CLAVE_ENTIDAD_RES'] = df['ENTIDAD_RES']
    df[cols_entidad] = df[cols_entidad].replace(to_replace=entidades['CLAVE_ENTIDAD'].values,
                                               value=entidades['ENTIDAD_FEDERATIVA'].values)

    # Construye clave unica de municipios de catálogo para resolver nombres de municipio
    municipios['CLAVE_MUNICIPIO'] = municipios['CLAVE_ENTIDAD'] + municipios['CLAVE_MUNICIPIO']

    # Resolver códigos de municipio
    municipios_dict = dict(zip(municipios['CLAVE_MUNICIPIO'], municipios['MUNICIPIO']))
    df['MUNICIPIO_RES'] = df['MUNICIPIO_RES'].map(municipios_dict.get)

    # Resolver resultados
    if nuevo_formato:
        df.rename(columns={'RESULTADO_LAB': 'RESULTADO'}, inplace=True)
        tipo_resultado['DESCRIPCIÓN'].replace({'POSITIVO A SARS-COV-2': 'Positivo SARS-CoV-2'}, inplace=True)

    tipo_resultado = dict(zip(tipo_resultado['CLAVE'], tipo_resultado['DESCRIPCIÓN']))
    df['RESULTADO'] = df['RESULTADO'].map(tipo_resultado.get)
    clasificacion_final = dict(zip(clasificacion_final['CLAVE'], clasificacion_final['CLASIFICACIÓN']))
    df['CLASIFICACION_FINAL'] = df['CLASIFICACION_FINAL'].map(clasificacion_final.get)
    # Resolver datos SI - NO

    # Necesitamos encontrar todos los campos que tienen este tipo de dato y eso
    # viene en los descriptores, en el campo FORMATO_O_FUENTE
    descriptores = pd.read_excel('/content/201128 Descriptores_.xlsx',
                                 index_col='Nº',
                                 engine='openpyxl')
    descriptores.columns = list(map(lambda col: col.replace(' ', '_'), descriptores.columns))
    descriptores['FORMATO_O_FUENTE'] = descriptores.FORMATO_O_FUENTE.str.strip()

    datos_si_no = descriptores.query('FORMATO_O_FUENTE == "CATÁLOGO: SI_ NO"')
    cat_si_no['DESCRIPCIÓN'] = cat_si_no['DESCRIPCIÓN'].str.strip()

    campos_si_no = datos_si_no.NOMBRE_DE_VARIABLE
    nuevos_campos_si_no = campos_si_no

    if resolver_claves == 'agregar':
        nuevos_campos_si_no = [nombre_var + '_NOM' for nombre_var in campos_si_no]
    elif resolver_claves == 'si_no_binarias':
        nuevos_campos_si_no = [nombre_var + '_BIN' for nombre_var in campos_si_no]
        cat_si_no['DESCRIPCIÓN'] = list(map(lambda val: 1 if val == 'SI' else 0, cat_si_no['DESCRIPCIÓN']))

    df[nuevos_campos_si_no] = df[datos_si_no.NOMBRE_DE_VARIABLE].replace(
                                                to_replace=cat_si_no['CLAVE'].values,
                                                value=cat_si_no['DESCRIPCIÓN'].values)

    # Resolver tipos de paciente
    cat_tipo_pac = dict(zip(cat_tipo_pac['CLAVE'], cat_tipo_pac['DESCRIPCIÓN']))
    df['TIPO_PACIENTE'] = df['TIPO_PACIENTE'].map(cat_tipo_pac.get)

    df = procesa_fechas(df)

    return df

def procesa_fechas(covid_df):
    df = covid_df.copy()

    df['FECHA_INGRESO'] = pd.to_datetime(df['FECHA_INGRESO'])
    df['FECHA_SINTOMAS'] = pd.to_datetime(df['FECHA_SINTOMAS'])
    df['FECHA_DEF'] = pd.to_datetime(df['FECHA_DEF'], 'coerce')
    df['DEFUNCION'] = (df['FECHA_DEF'].notna()).astype(int)
    df['EDAD'] = df['EDAD'].astype(int)

    df.set_index('FECHA_INGRESO', drop=False, inplace=True)
    df['AÑO_INGRESO'] = df.index.year
    df['MES_INGRESO'] = df.index.month
    df['DIA_SEMANA_INGRESO'] = df.index.weekday
    df['SEMANA_AÑO_INGRESO'] = df.index.week
    df['DIA_MES_INGRESO'] = df.index.day
    df['DIA_AÑO_INGRESO'] = df.index.dayofyear

    return df

aplanados = carga_datos_covid19_MX(fecha=ayer.strftime('%y%m%d'), entidad='27')
aplanados

"""Como pueden ver, lo que tenemos ahora es la misma base de datos que antes, pero con los valores de los campos obtenidos de los diccionarios y descriptores, lo que hace mucha más fácil utilizarlos.

Con esta base podemos empezar a hacer algunas visualizaciones en la siguiente sección.

## Curvas epidémicas

Las primeras visualizaciones que vamos a hacer son las *curvas epidémicas*, es decir, la evolución temporal de los casos confirmados y las defunciones. Si consultamos los diccionarios de datos, podemos ver que los casos confirmados para COVID-19 corresponden a 3 categorías de la columna clasificación final:

1. CASO DE COVID-19 CONFIRMADO POR ASOCIACIÓN CLÍNICA EPIDEMIOLÓGICA
2. CASO DE COVID-19 CONFIRMADO POR COMITÉ DE  DICTAMINACIÓN
3. CASO DE SARS-COV-2  CONFIRMADO

mientras que las defunciones corresponden a todos aquellos registros que tengan una fecha de defunción válida, es decir, distinta del valor `'9999-99-99'`.

Entonces, primero vamos a obtener los casos confirmados a partir de la base aplanada.

### Curva de casos confirmados
"""

valores_confirmados = ['CASO DE COVID-19 CONFIRMADO POR ASOCIACIÓN CLÍNICA EPIDEMIOLÓGICA',
                       'CASO DE COVID-19 CONFIRMADO POR COMITÉ DE DICTAMINACIÓN',
                       'CASO DE SARS-COV-2 CONFIRMADO']
confirmados = aplanados.loc[aplanados['CLASIFICACION_FINAL'].isin(valores_confirmados)]
confirmados.head()

"""Ahora tenemos una tabla con todos los casos confirmados, para hacer una curva epidémica, tenemos que agregar en una escala temporal. Lo más sencillo es primero agragar por día y a partir de ahí podemos construir agregados para cualquier intervalo que queramos.

Para poder construir las curvas epidémicas necesitamos decidir cuáál fecha de todas las disponibles vamos a utilizar para agregar los casos. En este caso, la DGE sugiere utilizar la fecha de inicio de síntomas (`FECHA_SINTOMAS`) para construir la curva de casos confirmados y la de defunción (`FECHA_DEF`) para la curva de defunciones.

Entonces, para construir la curva de confirmados lo primero que tenemos que hacer es indexar el DataFrame por la fecha de inicio de síntomas
"""

confirmados = confirmados.set_index('FECHA_SINTOMAS')
confirmados.index

"""Entonces es fácil construir agregados diarios, sólo tenemos que seleccionar qué columnas queremos agregar. Por lo pronto hagamos un conteo sólo de casos confirmados. Para eso sólo tenemos que agrupár el ídice usando una frecuencia diaría y tomar el tamaño de los grupos (de alguna columna, realmente no importa cual). """

confirmados_diarios = (confirmados
                       .groupby(pd.Grouper(freq='D'))[['ID_REGISTRO']] # grupos por dia y seleccionamos 'ID_REGISTRO'
                       .size() # Calculamos el tamaño de cada grupo
                       .reset_index() # Convertimos el resultado (que es una serie) en DataFrame
                       .rename({0:'Confirmados'}, axis=1) # Le damos nombre a la columna que obtenemos
                       )
confirmados_diarios

"""Con estos datos podemos usar [Plotly](https://plotly.com/) para hacer una gráfica interactiva de forma muy sencilla."""

fig = px.line(confirmados_diarios, x='FECHA_SINTOMAS', y="Confirmados")
fig.show()

"""Para ver con más claridad las tendencia y eliminar un poco el ruido, podemos incluir en la gráfica el promedio móvil. Para eso tenemos que calcularlo y agregarlo a la base de datos, en este caso vamos a usar una ventana móvil de 7 días para tratar de quitar los valles que corresponden a los fines de semana."""

confirmados_diarios['Media Móvil'] = confirmados_diarios.rolling(window=7).mean()
confirmados_diarios.head(10)

"""Y podemos graficarlos de la misma manera que arriba"""

fig = px.line(confirmados_diarios, x='FECHA_SINTOMAS', y='Media Móvil')
fig.show()

"""Para graficar las dos series en la misma gráfica lo más sencillo es pasar los datos de el formato ancho (en columnas) al formato largo (en filas con una columna que los distinga)"""

confirmados_diarios = confirmados_diarios.melt(id_vars=['FECHA_SINTOMAS'], value_vars=['Confirmados', 'Media Móvil'])
 confirmados_diarios

fig = px.line(confirmados_diarios, x='FECHA_SINTOMAS', y='value', color='variable')
fig.show(renderer="colab")

"""### Curva de defunciones

Ya que construimos la curva de casos confirmados, la de defunciones es exáctamente igual, sólo necesitamos seleccionar al inicio del proceso los renglones que tengan una fecha de defunción válida e indexar por fecha de defunción
"""

defunciones = confirmados.loc[confirmados['FECHA_DEF'].notnull()] # Seleccionamos los casos con fecha de defunción
defunciones = defunciones.set_index('FECHA_DEF') # indexamos por fecha de defuncióón
defunciones_diarios = (defunciones
                       .groupby(pd.Grouper(freq='D'))[['ID_REGISTRO']] # grupos por dia y seleccionamos 'ID_REGISTRO'
                       .size() # Calculamos el tamaño de cada grupo
                       .reset_index() # Convertimos el resultado (que es una serie) en DataFrame
                       .rename({0:'Defunciones'}, axis=1) # Le damos nombre a la columna que obtenemos
                       )
defunciones_diarios['Media Móvil'] = defunciones_diarios.rolling(window=7).mean()
defunciones_diarios = defunciones_diarios.melt(id_vars=['FECHA_DEF'], value_vars=['Defunciones', 'Media Móvil'])
fig = px.line(defunciones_diarios, x='FECHA_DEF', y='value', color='variable')
fig.show()

"""### Combinando las dos

La forma más sencilla de combinar ambas gráficas es hacer un Facet Plot, es decir, prodcir dos gráficas ligadas a partir de una sóla base de datos. Para lograr esto necesitamos una estructura un poco diferente, seguimos necesitando una columna que nos distinga los conteos de sus medias móviles, pero además vamos a necesitar otra columna que nos distina el tipo de caso: casos confirmados o defunciones.

Podemos partir de las bases que ya tenemos y simplemente cambiar algunas cosas:

* Agregar una columna que distinga si es Caso o defunción
* Cambiar los valores en las columnas `variable` para que coincidan en ambas series
* Cambiar los nombres de las fechas para que coincidan
* Hacer una base con las dos fuentes 
"""

defunciones_diarios

defunciones_diarios['Tipo'] = 'Defunciones'
defunciones_diarios.loc[defunciones_diarios['variable'] == 'Defunciones', 'variable'] = 'Conteo'
defunciones_diarios = defunciones_diarios.rename({'FECHA_DEF': 'Fecha'}, axis=1)
confirmados_diarios['Tipo'] = 'Casos Confirmados'
confirmados_diarios.loc[confirmados_diarios['variable'] == 'Confirmados', 'variable'] = 'Conteo'
confirmados_diarios = confirmados_diarios.rename({'FECHA_SINTOMAS': 'Fecha'}, axis=1)
casos_defunciones = defunciones_diarios.append(confirmados_diarios)
casos_defunciones

"""Ya con la nueva serie como la queremos, podemos hacer un Facet, la parte importante es decirle que no queremos que compartan el eje $y$ porque las escalas son muy diferentes"""

fig = px.line(casos_defunciones, x='Fecha', y='value', color='variable', facet_col='Tipo', facet_col_wrap=1)
fig.update_yaxes(matches=None)
fig.show()

"""### Hospitalizaciones

Otra grááfica muy interesante para comprender la evolucióón de la epidemia es la de hospitalizaciones. Para obtener esta grááfica primero tenemos que seleccionar los pacientes confirmados como positivos a COVID-19 y que además fueron hospitalizados.

Los caos confirmados ya los tenemos calculados en la variable `confirmados`, entonces falta ver cómo obtener los pacientes hospitalizados 
"""

confirmados.TIPO_PACIENTE.unique()

"""Gracias a nuentra base *aplanada* es muy fácil distinguirlos, entonces sólo los tenemos que seleccionar, agregar por día y podemos hacer una gráfica como las anteriores (incluyendo la media móvil). Recordemos que `confirmados` estáá indexado por fecha de inicio de sííntomas, entonces nuestra curva de hospitalización estará indexada por la misma fecha"""

hospitalizados = confirmados[confirmados.TIPO_PACIENTE == 'HOSPITALIZADO']
hospitalizados_diarios = (hospitalizados
                          .groupby(pd.Grouper(freq='D'))[['ID_REGISTRO']] # grupos por dia y seleccionamos 'ID_REGISTRO'
                          .size() # Calculamos el tamaño de cada grupo
                          .reset_index() # Convertimos el resultado (que es una serie) en DataFrame
                          .rename({0:'Hospitalizaciones'}, axis=1) # Le damos nombre a la columna que obtenemos
                        )
hospitalizados_diarios['Media Móvil'] = hospitalizados_diarios.rolling(window=7).mean()
hospitalizados_diarios = hospitalizados_diarios.melt(id_vars=['FECHA_SINTOMAS'], value_vars=['Hospitalizaciones', 'Media Móvil'])
fig = px.line(hospitalizados_diarios, x='FECHA_SINTOMAS', y='value', color='variable')
fig.show()

"""Y, una vez más, para comparar vamos a poner las tres gráficas (casos confirmados, defunciones y hospitalizacones) en un Facet"""

hospitalizados_diarios['Tipo'] = 'Hospitalizaciones'
hospitalizados_diarios.loc[hospitalizados_diarios['variable'] == 'Hospitalizaciones', 'variable'] = 'Conteo'
hospitalizados_diarios = hospitalizados_diarios.rename({'FECHA_SINTOMAS': 'Fecha'}, axis=1)
casos_defunciones_hospitalizaciones = casos_defunciones.append(hospitalizados_diarios)
casos_defunciones_hospitalizaciones

"""La ventaja de la estructura de datos que estamos usando es que la nueva gráfica se hace exactamente igual que antes"""

fig = px.line(casos_defunciones_hospitalizaciones, x='Fecha', y='value', color='variable', facet_col='Tipo', facet_col_wrap=1)
fig.update_yaxes(matches=None)
fig.show()

"""## Mapas

En esta sección del taller vamos a hacer algunos mapas sencillos a partir de los datos que ya tenemos. El primer paso es bajar los datos con la geometría de los municipios del país y su población total
"""

url = "https://www.dropbox.com/s/2zw0fh3vdl0rxh4/municipios_pob_2020_simple.json?dl=1"
r = requests.get(url, allow_redirects=True)
open('/content/municipios_pob_2020_simple.json', 'wb').write(r.content)

"""El archivo que acabamos de bajar es un GeoJson con las geometrías de los municipios y algunos otros datos. Para manipularlos en Python usamos la librería [GeoPandas](https://geopandas.org/) que es una extensión espacial de Panda. Para empezar, simplemente vamos a cargar los datos y hacer un mapa muy sencillo"""

municipios = gpd.read_file('/content/municipios_pob_2020_simple.json')
municipios

"""Geopandas provee un método `plot` para hacer mapas facilmente, sólo es necesario pasar la columna que se quiere usar para colorear el mapa, el esquema de colores y la clasificación a utilizar"""

municipios.plot(column='pob2020', cmap='OrRd',figsize=(15, 10), scheme="quantiles")

"""La columna `municipio_cvegeo` nos permite unir los datos de COVID-19 a las geometrías (y los datos) de esta tabla de municipios. Pero recordemos que los datos de COVID en realidad son series de tiempo, entonces podemos empezar por hacer un mapa para una fecha específica, digamos la más reciente disponible.

Lo primero que vamos a hacer es extraer sólo la última fecha de los datos que ya tenemos aplanados (recuerden que estos sólo van a ser para algún estado). Esto quiere decir un mapa con los casos que reportaron en el último día, no los casos acumulados.
"""

ultima_fecha = aplanados.loc[aplanados['FECHA_INGRESO'] == aplanados['FECHA_INGRESO'].max()]
ultima_fecha.head()

"""Ya con esta tabla, podemos hacer un agregado por municipio para ver el total de casos en cada uno."""

por_municipio = (ultima_fecha
                 .groupby(['CLAVE_MUNICIPIO_RES', 'MUNICIPIO_RES'])['ID_REGISTRO']
                 .size()
                 .reset_index()
                 .rename({"ID_REGISTRO": "Nuevos Casos"}, axis=1)
                 )
por_municipio

"""Tenemos la lista de los municipios *que tuvieron* casos en la fecha que estamos analizando, para hacer un mapa necesitamos unir estos datos a la geometría de los municipios.

Primero vamos a seleccionar, a partir del GeoDataFrame que ya tenemos sólo los municipios de la entidad que estamos analizando. A partir de eso podemos realizar una unión via la clave del municipio, sólo tenemos que tener cuiaddo de utilizar el tipo de unión adecuada para no dejar fuera los municipios sin casos.
"""

tabasco = municipios[municipios.entidad_cvegeo == '27']
casos_municipio = (tabasco
                   .merge(por_municipio, left_on='municipio_cvegeo', right_on='CLAVE_MUNICIPIO_RES', how='left') # Unimos con los municipios
                   .drop(columns=['CLAVE_MUNICIPIO_RES', 'MUNICIPIO_RES']) # eliminamos dos columnas que ya no vamosd a usar
                   .fillna(0) # Los municipios sin casos deben tener 0 en lugar de NaN
                   )
casos_municipio

"""Con esta base ya podemos hacer un mapa, para havcerlo más interesante en este caso vamos a usar [folium](http://python-visualization.github.io/folium/) para hacer un mapa interactivo."""

m = folium.Map(location=[17.8917015, -92.8174020], zoom_start=9) # Creamos la instancia de folium
folium.Choropleth( # Instanciamos un mapa de coropletas
    geo_data=casos_municipio, # Pasamos la geometría de los municipios
    data=casos_municipio[["municipio_cvegeo", "Nuevos Casos"]], # Las variables que vamos a usar en el mapa
    columns=["municipio_cvegeo", "Nuevos Casos"], # La primera columna une geometrías y datos, la segunda es la variable que vamos a mapear
    key_on="feature.properties.municipio_cvegeo", # Cómo se unen los datos
    bins=4, # Cuántos intervalos iguales queremos en la clasificación 
    fill_color="OrRd", # La escala de colores
    fill_opacity=0.7, # Opacidad del relleno
    line_opacity=0.2, # opacidad de la línea
    legend_name="Nuevos Casos",
).add_to(m)
m

"""Ya hicimos un mapa para una fecha específica, ahora podemos hacer un mapa igual pero del total de casos acumulados. Lo primero que tenemos que hacer es calcular los acumulados totales para cada municipio, esto se hace agrpando los datos por municipio y calculando el tamaño de cada grupo."""

acumulados_municipio = (aplanados
                        .groupby(['CLAVE_MUNICIPIO_RES', 'MUNICIPIO_RES'])['ID_REGISTRO']
                        .size()
                        .reset_index()
                        .rename({'ID_REGISTRO': 'Casos Acumulados'}, axis=1)
                        )
acumulados_municipio

"""Unimos a las geometrías de municipios y hacemos un mapa"""

acumulados_municipio = (tabasco
                        .merge(acumulados_municipio, left_on='municipio_cvegeo', right_on='CLAVE_MUNICIPIO_RES', how='left')
                        .drop(columns=['CLAVE_MUNICIPIO_RES', 'MUNICIPIO_RES'])
                        .fillna(0)
                        )
m = folium.Map(location=[17.8917015, -92.8174020], zoom_start=10) # Creamos la instancia de folium
folium.Choropleth( # Instanciamos un mapa de coropletas
    geo_data=acumulados_municipio, # Pasamos la geometría de los municipios
    data=acumulados_municipio[["municipio_cvegeo", "Casos Acumulados"]], # Las variables que vamos a usar en el mapa
    columns=["municipio_cvegeo", "Casos Acumulados"], # La primera columna une geometrías y datos, la segunda es la variable que vamos a mapear
    key_on="feature.properties.municipio_cvegeo", # Cómo se unen los datos
    bins=6, # Cuántos intervalos iguales queremos en la clasificación 
    fill_color="OrRd", # La escala de colores
    fill_opacity=0.7, # Opacidad del relleno
    line_opacity=0.2, # opacidad de la línea
    legend_name="Casos Acumulados",
).add_to(m)
m

"""Una forma más adecuada de representar estos mismos datos es utilizando la cantidad de casos por cada 100,000 habitantes, para no sesgar el mapa por la población que vive en cada municipio. Los datos de población vienen en la capa de municipios, entonces calcular la tasa es muy sencillo"""

acumulados_municipio['Tasa x 100,000 habitantes'] = (acumulados_municipio['Casos Acumulados']/acumulados_municipio['pob2020']) * 100000
m = folium.Map(location=[17.8917015, -92.8174020], zoom_start=10) # Creamos la instancia de folium
folium.Choropleth( # Instanciamos un mapa de coropletas
    geo_data=acumulados_municipio, # Pasamos la geometría de los municipios
    data=acumulados_municipio[["municipio_cvegeo", "Tasa x 100,000 habitantes"]], # Las variables que vamos a usar en el mapa
    columns=["municipio_cvegeo", "Tasa x 100,000 habitantes"], # La primera columna une geometrías y datos, la segunda es la variable que vamos a mapear
    key_on="feature.properties.municipio_cvegeo", # Cómo se unen los datos
    bins=6, # Cuántos intervalos iguales queremos en la clasificación 
    fill_color="OrRd", # La escala de colores
    fill_opacity=0.7, # Opacidad del relleno
    line_opacity=0.2, # opacidad de la línea
    legend_name="Tasa x 100,000 habitantes",
).add_to(m)
m

"""Es muy claro que son dos mapas diferentes. Para apreciarlo mejor, podemos ponerlos juntos como capas de un mismo mapa de folium y agragar un *control* para cambiar las capas"""

m = folium.Map(location=[17.8917015, -92.8174020], zoom_start=11) # Creamos la instancia de folium
# Agregamos la primera capa
folium.Choropleth( # Instanciamos un mapa de coropletas
    geo_data=acumulados_municipio, # Pasamos la geometría de los municipios
    name="Tasa x 100,000 habitantes", # Un nombre para distinguirlas en el control
    data=acumulados_municipio[["municipio_cvegeo", "Tasa x 100,000 habitantes"]], # Las variables que vamos a usar en el mapa
    columns=["municipio_cvegeo", "Tasa x 100,000 habitantes"], # La primera columna une geometrías y datos, la segunda es la variable que vamos a mapear
    key_on="feature.properties.municipio_cvegeo", # Cómo se unen los datos
    bins=6, # Cuántos intervalos iguales queremos en la clasificación 
    fill_color="OrRd", # La escala de colores
    fill_opacity=0.7, # Opacidad del relleno
    line_opacity=0.2, # opacidad de la línea
    legend_name="Tasa x 100,000 habitantes",
).add_to(m)
# Agregamos la segunda
folium.Choropleth( # Instanciamos un mapa de coropletas
    geo_data=acumulados_municipio, # Pasamos la geometría de los municipios
    name="Casos Acumulados", # Un nombre para distinguirlas en el control
    data=acumulados_municipio[["municipio_cvegeo", "Casos Acumulados"]], # Las variables que vamos a usar en el mapa
    columns=["municipio_cvegeo", "Casos Acumulados"], # La primera columna une geometrías y datos, la segunda es la variable que vamos a mapear
    key_on="feature.properties.municipio_cvegeo", # Cómo se unen los datos
    bins=6, # Cuántos intervalos iguales queremos en la clasificación 
    fill_color="OrRd", # La escala de colores
    fill_opacity=0.7, # Opacidad del relleno
    line_opacity=0.2, # opacidad de la línea
    legend_name="Casos Acumulados",
).add_to(m)
# Agregamos un control para cambiar de capas
folium.LayerControl().add_to(m)
m

