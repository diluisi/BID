#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May  3 16:52:23 2021
O projeto de Indicador de Congestionamento foi financiado pelo 
Banco de Desenvolvimento Interamericano (BID) em parceria com a
Fundação Getúio Vargas e a companhia Waze.
O protótipo utiliza dados coletados do banco de dados na AWS e
dados em tempo real.
O resultado é um dashboard escrito em python em utilizando 
principalmente a biblioteca Dash da Plotly. Todas as bibliotecas
são Open Source o que possibilita as agências de trânsito
o modificarem livremente.
@author: diluisi
"""

# SELECT pub_utc_date, street, length, level, line_geojson FROM "cities"."br_saopaulo_waze_jams" WHERE month = 3 AND level IN (3,4,5) AND city = 'São Paulo';

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input
import plotly.express as px
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import geopandas as gpd
import json
from shapely.geometry import shape
from plotly import graph_objs as go
from plotly.graph_objs import *
import datetime as dt
import dash_daq as daq
from aws_query import query_transf

STATUS = {'st_date':None, 'ed_date':None, 'base345': None, 'base45':None}

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0'}]
                )

server = app.server

def cvt_linestring(lst):
    ls = gpd.GeoSeries(lst.apply(lambda x: shape(json.loads(x))), crs='EPSG:4326')
    return ls

def linestr(df):
    lats = []
    lons = []
    df['new_linestring'] = cvt_linestring(df.line_geojson)
    for index, row in df.iterrows():
        x, y = row.new_linestring.xy
        lats = np.append(lats, y)
        lons = np.append(lons, x)
        lats = np.append(lats, None)
        lons = np.append(lons, None)
    return lats, lons

#------------------------------------------------------------------------------
# LEITURA DO ARQUIVO
#------------------------------------------------------------------------------
# Arquivo > objeto dataframe

# Sao Paulo
sp_df_30min_345 = pd.read_csv('/home/diluisi/Documentos/BID_Project/Projeto_Final/sp_30min_345.csv',parse_dates=['30min'])
sp_df_30min_345['length'] = sp_df_30min_345['length']/1000
sp_df_30min_45 = pd.read_csv('/home/diluisi/Documentos/BID_Project/Projeto_Final/sp_30min_45.csv',parse_dates=['30min'])
sp_df_30min_45['length'] = sp_df_30min_45['length']/1000


# street option
option_list = pd.read_csv('/home/diluisi/Documentos/BID_Project/Projeto_Final/option_list')

coords = pd.DataFrame({"region": ["Sao Paulo - Brazil", "Quito - Ecuador", "Miraflores - Peru", "Montevideo - Uruguay"], 
                       "city_la":[-23.506226,-0.111780,-12.029391,-34.782417], 
                       "city_lo":[-46.6336332,-78.450622,-77.028059,-56.222555], 
                       "mpbx_center":[-23.550164466,-0.202431,-12.124605,-34.905283]})

def df_pick(region):
    if region == 'Sao Paulo - Brazil':
        city_df_30min_345 = sp_df_30min_345.copy()
        city_df_30min_45 = sp_df_30min_45.copy()
    else:
        city_df_30min_345 = sp_df_30min_345.copy()
        city_df_30min_45 = sp_df_30min_45.copy()
    
    return city_df_30min_345, city_df_30min_45


#------------------------------------------------------------------------------
# LAYOUT
#------------------------------------------------------------------------------

# Layout of Dash App
app.layout = html.Div(
    children=[
        html.Div(
            className="row",
            children=[
                # Column for user controls
                html.Div(
                    className="four columns div-user-controls",
                    children=[
                        html.Img(
                            className="logo", src=app.get_asset_url("logo.png"),style={'height':'9%', 'width':'95%'}
                        ),
                        html.H2("TRAFFIC CONGESTION DASHBOARD"),
                        html.P(
                            """Select different days using the date range picker."""
                        ),
                        html.Div(
                            className="div-for-dropdown",
                            children=[
                                dcc.DatePickerRange(
                                    id="date-picker",
                                    min_date_allowed=dt.datetime(2021, 7, 1),
                                    #max_date_allowed=dt.datetime(2019, 4, 30),
                                    initial_visible_month=dt.datetime(2021, 7, 1),
                                    start_date=dt.datetime(2021, 7, 1).date(),
                                    #end_date=dt.datetime(2019, 3, 5).date(),
                                    display_format="MMMM D, YYYY",
                                    style={"border": "0px solid black","width": "45rem"},
                                    end_date_placeholder_text='Select end date'
                                )
                            ],
                            
                        ),
                        
                        html.Div(
                                    className="div-for-dropdown",
                                    children=[
                                        # Dropdown for locations on map
                                        dcc.Dropdown(
                                            id="region-dropdown",
                                            options=[
                                                {"label": "Sao Paulo - Brazil", "value": "Sao Paulo - Brazil"},
                                                ],
                                            #placeholder="Select a category",
                                            value='Sao Paulo - Brazil',
                                            style={"width": "45rem"},
                                            clearable=False,
                                        )
                                    ],
                                ),
                        
                        # Categorias
                        html.Div(
                                    className="div-for-dropdown",
                                    children=[
                                        # Dropdown for locations on map
                                        dcc.Dropdown(
                                            id="category-dropdown",
                                            options=[
                                                {"label": "3-4-5", "value": "3-4-5"},
                                                 {"label": "4-5", "value":"4-5"}
                                                ],
                                            #placeholder="Select a category",
                                            value='3-4-5',
                                            style={"width": "45rem"},
                                            clearable=False,
                                        )
                                    ],
                                ),
                        # Locais no mapa    
                        html.Div(
                            className="div-for-dropdown",
                            children=[
                                # Dropdown for locations on map
                                dcc.Dropdown(
                                    id="location-dropdown",
                                    placeholder="Select a location",
                                    style={"width": "45rem"},
                                )
                            ],
                        ),
                        #html.Br(),
                        html.P(
                            """Select day type:"""
                        ),
                        #html.Br(),
                        dcc.RadioItems(
                                        id="check-day",
                                        options=[
                                            {'label': 'All', 'value': 'ALL'},
                                            {'label': 'Business day', 'value': 'BD'},
                                            {'label': 'Weekend', 'value': 'FD'},
                                        ],
                                        value='ALL',
                                        #labelStyle={'display': 'inline-block'}
                                    ),
                        html.Br(),
                        html.P(
                            """Select Historical data or Real Time data."""
                        ),
                        dcc.RadioItems(
                                        id="hist_rt",
                                        options=[
                                            {'label': 'Historical', 'value': 'HD'},
                                            {'label': 'Real time', 'value': 'RT'},
                                        ],
                                        value='HD',
                                        #labelStyle={'display': 'inline-block'}
                                    ),
                        #html.P(
                        #    """According to parameters selection, the traffic congestion indicator is shown below."""
                        #),
                        html.Br(),
                       dcc.Graph(id="indicator-graph"),
                       # atualização automática
                       dcc.Interval(id='interval-component',interval=300*1000, n_intervals=0), #300000 millisecond == 5min
                    ],
                ),
                # Column for app graphs and plots
                html.Div(
                    className="eight columns div-for-charts bg-grey",
                    children=[
                        dcc.Graph(id="map-graph"),
                        html.Div(
                            className="text-padding",
                            children=[
                                "The barplot shows the traffic congestion every 30 minutes for historical data and 5 minutes for real time data."
                            ],
                        ),
                        dcc.Graph(id="histogram1"),
                    ],
                ),
            ],
        )
    ]
)


#------------------------------------------------------------------------------
# CALL BACKS
#------------------------------------------------------------------------------
# Update Map Graph based on date-picker, selected data on histogram and location dropdown
#@app.callback(
#    Output('map-graph', 'figure'),
#    Input('date-picker', 'start_date'),
#    Input('date-picker', 'end_date'),
#    Input("category-dropdown", "value"),
#    Input("location-dropdown", "value"),
#    Input("region-dropdown", "value"),
#    Input("check-day", "value"),
#    Input("hist_rt", "value"),
#    Input('interval-component', 'n_intervals')
#)
#def update_map(s_date, e_date, category, location,region,chk_day,hist_rt,n):
#    
#    city_df_30min_345, city_df_30min_45 = df_pick(region)
#    
#
#    return fig

# Histogram
@app.callback(
    Output('histogram1', 'figure'),
    Output("indicator-graph", "figure"),
    Output('map-graph', 'figure'),
    Input('date-picker', 'start_date'),
    Input('date-picker', 'end_date'),
    Input("category-dropdown", "value"),
    Input("location-dropdown", "value"),
    Input("region-dropdown", "value"),
    Input("check-day", "value"),
    Input("hist_rt", "value"),
    Input('interval-component', 'n_intervals')
)
def update_graph(s_date, e_date, category, location, region,chk_day,hist_rt,n):
    
    start_date = dt.datetime.strptime(s_date, "%Y-%m-%d")
    if e_date == None:
        finish_date = dt.datetime.strptime(s_date, "%Y-%m-%d") + dt.timedelta(days=1) - dt.timedelta(seconds=1)
    else:
        finish_date = dt.datetime.strptime(e_date, "%Y-%m-%d")
    
    if (STATUS['st_date'] != start_date) or (STATUS['ed_date'] != finish_date):
        #city_df_30min_345, city_df_30min_45 = df_pick(region)
        city_df_30min_345, city_df_30min_45 = query_transf(start_date.day,finish_date.day,start_date.month,start_date.year)
        # atualiza o contorle de parâmetros 
        STATUS['st_date'] = start_date
        STATUS['ed_date'] = finish_date
        STATUS['base345'] = city_df_30min_345 
        STATUS['base45'] = city_df_30min_45
    else:
        city_df_30min_345 = STATUS['base345']
        city_df_30min_45 = STATUS['base45']
    
    # ATUALIZA MAPA
    if hist_rt == "HD":
        if category == '3-4-5':
            #-23.550164466 -46.633664132 > -0.103127
            if location == None:        
                figb = px.scatter_mapbox(lat=[coords[coords['region']==region].city_la.iloc[0]], lon=[coords[coords['region']==region].city_lo.iloc[0]], zoom=3,height=500)
                figb.update_layout(mapbox_style="carto-positron", mapbox_zoom=12, mapbox_center_lat = coords[coords['region']==region].mpbx_center.iloc[0], 
                                  margin={"r":0,"t":0,"l":0,"b":0})     
            else:
#                start_date = dt.datetime.strptime(s_date, "%Y-%m-%d")
#                if e_date == None:
#                    finish_date = dt.datetime.strptime(s_date, "%Y-%m-%d") + dt.timedelta(days=1) - dt.timedelta(seconds=1)
#                else:
#                    finish_date = e_date
                
                if chk_day == 'ALL':
                    df55 = city_df_30min_345[(city_df_30min_345['30min'].between(start_date,finish_date)) & (city_df_30min_345['new_street']==location)].drop_duplicates(subset=['line_geojson'], keep='first').copy()
                elif chk_day == 'BD':
                    df55 = city_df_30min_345[(city_df_30min_345['30min'].between(start_date,finish_date)) & (city_df_30min_345['new_street']==location) & (city_df_30min_345['weekday']=='BD')].drop_duplicates(subset=['line_geojson'], keep='first').copy()
                else:
                    df55 = city_df_30min_345[(city_df_30min_345['30min'].between(start_date,finish_date)) & (city_df_30min_345['new_street']==location) & (city_df_30min_345['weekday']=='FD')].drop_duplicates(subset=['line_geojson'], keep='first').copy()
         
                lats, lons = linestr(df55)
                dff = pd.DataFrame({'lat': lats, 'lon': lons})
                
                figb = px.line_mapbox(dff, lat='lat', lon='lon',color_discrete_sequence=['red'],zoom=3,height=500)
                figb.update_layout(mapbox_style="carto-positron", mapbox_zoom=12, mapbox_center_lat = dff['lat'].mean(), 
                                  margin={"r":0,"t":0,"l":0,"b":0})
        else:
            if location == None:        
                figb = px.scatter_mapbox(lat=[coords[coords['region']==region].city_la.iloc[0]], lon=[coords[coords['region']==region].city_lo.iloc[0]], zoom=3,height=500)
                figb.update_layout(mapbox_style="carto-positron", mapbox_zoom=12, mapbox_center_lat = coords[coords['region']==region].mpbx_center.iloc[0], 
                                  margin={"r":0,"t":0,"l":0,"b":0})     
            else:
#                start_date = dt.datetime.strptime(s_date, "%Y-%m-%d")
#                if e_date == None:
#                    finish_date = dt.datetime.strptime(s_date, "%Y-%m-%d") + dt.timedelta(days=1) - dt.timedelta(seconds=1)
#                else:
#                    finish_date = e_date
                                   
                if chk_day == 'ALL':
                    df55 = city_df_30min_45[(city_df_30min_45['30min'].between(start_date,finish_date)) & (city_df_30min_45['new_street']==location)].drop_duplicates(subset=['line_geojson'], keep='first').copy()
                elif chk_day == 'BD':
                    df55 = city_df_30min_45[(city_df_30min_45['30min'].between(start_date,finish_date)) & (city_df_30min_45['new_street']==location) & (city_df_30min_45['weekday']=='BD')].drop_duplicates(subset=['line_geojson'], keep='first').copy()
                else:
                    df55 = city_df_30min_45[(city_df_30min_45['30min'].between(start_date,finish_date)) & (city_df_30min_45['new_street']==location) & (city_df_30min_45['weekday']=='FD')].drop_duplicates(subset=['line_geojson'], keep='first').copy()
    
                #df5 = city_df_30min_45[(city_df_30min_45['30min'].between(start_date,finish_date)) & (city_df_30min_45['new_street']==location)].drop_duplicates(subset=['line_geojson'], keep='first').copy()
    
                lats, lons = linestr(df55)
                dff = pd.DataFrame({'lat': lats, 'lon': lons})
                
                figb = px.line_mapbox(dff, lat='lat', lon='lon',color_discrete_sequence=['red'],zoom=3,height=500)
                figb.update_layout(mapbox_style="carto-positron", mapbox_zoom=12, mapbox_center_lat = dff['lat'].mean(), 
                                  margin={"r":0,"t":0,"l":0,"b":0})
    else:
        map_live = pd.read_csv('/home/diluisi/Documentos/BID_Project/Projeto_Final/map.csv')
        if category == '3-4-5':
            figb = px.line_mapbox(map_live, lat='latitude', lon='longitude',color_discrete_sequence=['red'],zoom=2,height=500)
            figb.update_layout(mapbox_style="carto-positron",margin={"r":0,"t":0,"l":0,"b":0},  mapbox_zoom=12,mapbox_center_lat = map_live['latitude'].mean(),uirevision=True)
        elif category == '4-5':
            figb = px.line_mapbox(map_live[map_live['level']!=3], lat='latitude', lon='longitude',color_discrete_sequence=['red'],zoom=2,height=500)
            figb.update_layout(mapbox_style="carto-positron",margin={"r":0,"t":0,"l":0,"b":0},  mapbox_zoom=12,mapbox_center_lat = map_live[map_live['level']!=3].latitude.mean(),uirevision=True)    
    
    
    
    # ATUALIZA HISTOGRAMA
    if hist_rt == "HD":
        if category == '3-4-5':
            if location == None:
                
                if chk_day == 'ALL':
                    # base filtrada pela data
                    df1 = city_df_30min_345[city_df_30min_345['30min'].between(start_date,finish_date)].dropna().copy()
                    # obtendo a soma de congestionamento por segmento
                    df2 = df1[['30min','new_street','length','time_hm']].groupby(['30min','new_street','time_hm']).sum().reset_index()
                    df3 = df2[['time_hm','new_street','length']].groupby(['time_hm','new_street']).mean().reset_index()
                    df4 = df3[['time_hm','length']].groupby(['time_hm']).sum().reset_index()
                    
                    # obtendo a soma de congestionamento por segmento
                    df6 = city_df_30min_345[['30min','new_street','length','time_hm']].groupby(['30min','new_street','time_hm']).sum().reset_index()
                    df7 = df6[['time_hm','new_street','length']].groupby(['time_hm','new_street']).mean().reset_index()
                    df8 = df7[['time_hm','length']].groupby(['time_hm']).sum().reset_index()                        
                    
                elif chk_day == 'BD':
                    # base filtrada pela data
                    df1 = city_df_30min_345[(city_df_30min_345['30min'].between(start_date,finish_date)) & (city_df_30min_345['weekday']=='BD')].dropna().copy()
                    # obtendo a soma de congestionamento por segmento
                    df2 = df1[['30min','new_street','length','time_hm']].groupby(['30min','new_street','time_hm']).sum().reset_index()
                    df3 = df2[['time_hm','new_street','length']].groupby(['time_hm','new_street']).mean().reset_index()
                    df4 = df3[['time_hm','length']].groupby(['time_hm']).sum().reset_index()
                    
                    # obtendo a soma de congestionamento por segmento
                    df6 = city_df_30min_345[['30min','new_street','length','time_hm']][city_df_30min_345['weekday']=='BD'].groupby(['30min','new_street','time_hm']).sum().reset_index()
                    df7 = df6[['time_hm','new_street','length']].groupby(['time_hm','new_street']).mean().reset_index()
                    df8 = df7[['time_hm','length']].groupby(['time_hm']).sum().reset_index()
                    
                else:
                    # base filtrada pela data
                    df1 = city_df_30min_345[(city_df_30min_345['30min'].between(start_date,finish_date)) & (city_df_30min_345['weekday']=='FD')].dropna().copy()
                    # obtendo a soma de congestionamento por segmento
                    df2 = df1[['30min','new_street','length','time_hm']].groupby(['30min','new_street','time_hm']).sum().reset_index()
                    df3 = df2[['time_hm','new_street','length']].groupby(['time_hm','new_street']).mean().reset_index()
                    df4 = df3[['time_hm','length']].groupby(['time_hm']).sum().reset_index()
    
                    # obtendo a soma de congestionamento por segmento
                    df6 = city_df_30min_345[['30min','new_street','length','time_hm']][city_df_30min_345['weekday']=='FD'].groupby(['30min','new_street','time_hm']).sum().reset_index()
                    df7 = df6[['time_hm','new_street','length']].groupby(['time_hm','new_street']).mean().reset_index()
                    df8 = df7[['time_hm','length']].groupby(['time_hm']).sum().reset_index()                           
                
                fig = px.bar(df4,
                             x='time_hm', y="length",title="Traffic Congestion @{}".format(region),
                             labels={
                             "time_hm": "Time interval [30 minutes]",
                             "length": "Traffic congestion [km]",
                             "level": "Waze category"
                         })
                fig.update_layout({'plot_bgcolor': 'rgba(0, 0, 0, 0)','paper_bgcolor': 'rgba(0, 0, 0, 0)',},template="plotly_dark")
                fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgb(102,102,102)')
                fig.update_traces(marker_line_color="#636EFA")
                            
            else:
                
                if chk_day == 'ALL':
                    # base filtrada pela data
                    df1 = city_df_30min_345[city_df_30min_345['30min'].between(start_date,finish_date)& (city_df_30min_345['new_street']==location)].dropna().copy()
                    # obtendo a soma de congestionamento por segmento
                    df2 = df1[['30min','new_street','length','time_hm']].groupby(['30min','new_street','time_hm']).sum().reset_index()
                    df3 = df2[['time_hm','new_street','length']].groupby(['time_hm','new_street']).mean().reset_index()
                    df4 = df3[['time_hm','length']].groupby(['time_hm']).sum().reset_index()
                    
                    # obtendo a soma de congestionamento por segmento
                    df6 = city_df_30min_345[['30min','new_street','length','time_hm']][city_df_30min_345['new_street']==location].groupby(['30min','new_street','time_hm']).sum().reset_index()
                    df7 = df6[['time_hm','new_street','length']].groupby(['time_hm','new_street']).mean().reset_index()
                    df8 = df7[['time_hm','length']].groupby(['time_hm']).sum().reset_index()                                            
                    
                elif chk_day == 'BD':
                    # base filtrada pela data
                    df1 = city_df_30min_345[(city_df_30min_345['30min'].between(start_date,finish_date)) & (city_df_30min_345['weekday']=='BD')& (city_df_30min_345['new_street']==location)].dropna().copy()
                    # obtendo a soma de congestionamento por segmento
                    df2 = df1[['30min','new_street','length','time_hm']].groupby(['30min','new_street','time_hm']).sum().reset_index()
                    df3 = df2[['time_hm','new_street','length']].groupby(['time_hm','new_street']).mean().reset_index()
                    df4 = df3[['time_hm','length']].groupby(['time_hm']).sum().reset_index()
                    #df5 = city_df_30min_345[['30min','new_street','length']].groupby(['30min']).sum().reset_index()
                    
                    # obtendo a soma de congestionamento por segmento
                    df6 = city_df_30min_345[['30min','new_street','length','time_hm']][(city_df_30min_345['new_street']==location) & (city_df_30min_345['weekday']=='BD')].groupby(['30min','new_street','time_hm']).sum().reset_index()
                    df7 = df6[['time_hm','new_street','length']].groupby(['time_hm','new_street']).mean().reset_index()
                    df8 = df7[['time_hm','length']].groupby(['time_hm']).sum().reset_index()                        
    
                else:
                    # base filtrada pela data
                    df1 = city_df_30min_345[(city_df_30min_345['30min'].between(start_date,finish_date)) & (city_df_30min_345['weekday']=='FD')& (city_df_30min_345['new_street']==location)].dropna().copy()
                    # obtendo a soma de congestionamento por segmento
                    df2 = df1[['30min','new_street','length','time_hm']].groupby(['30min','new_street','time_hm']).sum().reset_index()
                    df3 = df2[['time_hm','new_street','length']].groupby(['time_hm','new_street']).mean().reset_index()
                    df4 = df3[['time_hm','length']].groupby(['time_hm']).sum().reset_index()
    
                    # obtendo a soma de congestionamento por segmento
                    df6 = city_df_30min_345[['30min','new_street','length','time_hm']][(city_df_30min_345['new_street']==location) & (city_df_30min_345['weekday']=='FD')].groupby(['30min','new_street','time_hm']).sum().reset_index()
                    df7 = df6[['time_hm','new_street','length']].groupby(['time_hm','new_street']).mean().reset_index()
                    df8 = df7[['time_hm','length']].groupby(['time_hm']).sum().reset_index()                                                 
                
                fig = px.bar(df4,
                             x='time_hm', y="length",title="Traffic Congestion @{}".format(region),
                             labels={
                             "time_hm": "Time interval [30 minutes]",
                             "length": "Traffic congestion [km]",
                             "level": "Waze category"
                         })
                fig.update_layout({'plot_bgcolor': 'rgba(0, 0, 0, 0)','paper_bgcolor': 'rgba(0, 0, 0, 0)',},template="plotly_dark")
                fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgb(102,102,102)')    
        else:
            if location == None:
                if chk_day == 'ALL':
                    # base filtrada pela data
                    df1 = city_df_30min_45[city_df_30min_45['30min'].between(start_date,finish_date)].dropna().copy()
                    # obtendo a soma de congestionamento por segmento
                    df2 = df1[['30min','new_street','length','time_hm']].groupby(['30min','new_street','time_hm']).sum().reset_index()
                    df3 = df2[['time_hm','new_street','length']].groupby(['time_hm','new_street']).mean().reset_index()
                    df4 = df3[['time_hm','length']].groupby(['time_hm']).sum().reset_index()
                    
                    # obtendo a soma de congestionamento por segmento
                    df6 = city_df_30min_45[['30min','new_street','length','time_hm']].groupby(['30min','new_street','time_hm']).sum().reset_index()
                    df7 = df6[['time_hm','new_street','length']].groupby(['time_hm','new_street']).mean().reset_index()
                    df8 = df7[['time_hm','length']].groupby(['time_hm']).sum().reset_index()                        
                    
                    
                elif chk_day == 'BD':
                    # base filtrada pela data
                    df1 = city_df_30min_45[(city_df_30min_45['30min'].between(start_date,finish_date)) & (city_df_30min_45['weekday']=='BD')].dropna().copy()
                    # obtendo a soma de congestionamento por segmento
                    df2 = df1[['30min','new_street','length','time_hm']].groupby(['30min','new_street','time_hm']).sum().reset_index()
                    df3 = df2[['time_hm','new_street','length']].groupby(['time_hm','new_street']).mean().reset_index()
                    df4 = df3[['time_hm','length']].groupby(['time_hm']).sum().reset_index()
                    
                    # obtendo a soma de congestionamento por segmento
                    df6 = city_df_30min_45[['30min','new_street','length','time_hm']][city_df_30min_45['weekday']=='BD'].groupby(['30min','new_street','time_hm']).sum().reset_index()
                    df7 = df6[['time_hm','new_street','length']].groupby(['time_hm','new_street']).mean().reset_index()
                    df8 = df7[['time_hm','length']].groupby(['time_hm']).sum().reset_index()
    
                else:
                    # base filtrada pela data
                    df1 = city_df_30min_45[(city_df_30min_45['30min'].between(start_date,finish_date)) & (city_df_30min_45['weekday']=='FD')].dropna().copy()
                    # obtendo a soma de congestionamento por segmento
                    df2 = df1[['30min','new_street','length','time_hm']].groupby(['30min','new_street','time_hm']).sum().reset_index()
                    df3 = df2[['time_hm','new_street','length']].groupby(['time_hm','new_street']).mean().reset_index()
                    df4 = df3[['time_hm','length']].groupby(['time_hm']).sum().reset_index()
    
                    # obtendo a soma de congestionamento por segmento
                    df6 = city_df_30min_45[['30min','new_street','length','time_hm']][city_df_30min_45['weekday']=='FD'].groupby(['30min','new_street','time_hm']).sum().reset_index()
                    df7 = df6[['time_hm','new_street','length']].groupby(['time_hm','new_street']).mean().reset_index()
                    df8 = df7[['time_hm','length']].groupby(['time_hm']).sum().reset_index()                           
                               
                fig = px.bar(df4,
                             x='time_hm', y="length",title="Traffic Congestion @{}".format(region),
                             labels={
                             "time_hm": "Time interval [30 minutes]",
                             "length": "Traffic congestion [km]",
                             "level": "Waze category"
                         })
                fig.update_layout({'plot_bgcolor': 'rgba(0, 0, 0, 0)','paper_bgcolor': 'rgba(0, 0, 0, 0)',},template="plotly_dark")
                fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgb(102,102,102)')
            else:
    
                if chk_day == 'ALL':
                    # base filtrada pela data
                    df1 = city_df_30min_45[city_df_30min_45['30min'].between(start_date,finish_date)& (city_df_30min_45['new_street']==location)].dropna().copy()
                    # obtendo a soma de congestionamento por segmento
                    df2 = df1[['30min','new_street','length','time_hm']].groupby(['30min','new_street','time_hm']).sum().reset_index()
                    df3 = df2[['time_hm','new_street','length']].groupby(['time_hm','new_street']).mean().reset_index()
                    df4 = df3[['time_hm','length']].groupby(['time_hm']).sum().reset_index()
                    
                    # obtendo a soma de congestionamento por segmento
                    df6 = city_df_30min_45[['30min','new_street','length','time_hm']][city_df_30min_45['new_street']==location].groupby(['30min','new_street','time_hm']).sum().reset_index()
                    df7 = df6[['time_hm','new_street','length']].groupby(['time_hm','new_street']).mean().reset_index()
                    df8 = df7[['time_hm','length']].groupby(['time_hm']).sum().reset_index()                        
                    
                elif chk_day == 'BD':
                    # base filtrada pela data
                    df1 = city_df_30min_45[(city_df_30min_45['30min'].between(start_date,finish_date)) & (city_df_30min_45['weekday']=='BD')& (city_df_30min_45['new_street']==location)].dropna().copy()
                    # obtendo a soma de congestionamento por segmento
                    df2 = df1[['30min','new_street','length','time_hm']].groupby(['30min','new_street','time_hm']).sum().reset_index()
                    df3 = df2[['time_hm','new_street','length']].groupby(['time_hm','new_street']).mean().reset_index()
                    df4 = df3[['time_hm','length']].groupby(['time_hm']).sum().reset_index()
                    
                    # obtendo a soma de congestionamento por segmento
                    df6 = city_df_30min_45[['30min','new_street','length','time_hm']][(city_df_30min_45['new_street']==location) & (city_df_30min_45['weekday']=='BD')].groupby(['30min','new_street','time_hm']).sum().reset_index()
                    df7 = df6[['time_hm','new_street','length']].groupby(['time_hm','new_street']).mean().reset_index()
                    df8 = df7[['time_hm','length']].groupby(['time_hm']).sum().reset_index()                                  
                    
                else:
                    # base filtrada pela data
                    df1 = city_df_30min_45[(city_df_30min_45['30min'].between(start_date,finish_date)) & (city_df_30min_45['weekday']=='FD')& (city_df_30min_45['new_street']==location)].dropna().copy()
                    # obtendo a soma de congestionamento por segmento
                    df2 = df1[['30min','new_street','length','time_hm']].groupby(['30min','new_street','time_hm']).sum().reset_index()
                    df3 = df2[['time_hm','new_street','length']].groupby(['time_hm','new_street']).mean().reset_index()
                    df4 = df3[['time_hm','length']].groupby(['time_hm']).sum().reset_index()
    
                    # obtendo a soma de congestionamento por segmento
                    df6 = city_df_30min_45[['30min','new_street','length','time_hm']][(city_df_30min_45['new_street']==location) & (city_df_30min_45['weekday']=='FD')].groupby(['30min','new_street','time_hm']).sum().reset_index()
                    df7 = df6[['time_hm','new_street','length']].groupby(['time_hm','new_street']).mean().reset_index()
                    df8 = df7[['time_hm','length']].groupby(['time_hm']).sum().reset_index()                                                 
                                               
                fig = px.bar(df4,
                             x='time_hm', y="length",title="Traffic Congestion @{}".format(region),
                             labels={
                             "time_hm": "Time interval [30 minutes]",
                             "length": "Traffic congestion [km]",
                             "level": "Waze category"
                         })
                fig.update_layout({'plot_bgcolor': 'rgba(0, 0, 0, 0)','paper_bgcolor': 'rgba(0, 0, 0, 0)',},template="plotly_dark",uirevision=True)
                fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgb(102,102,102)')
        
        # linhas de referência do histograma
        mean_local = round(df4['length'].mean(),2)
        mean_global = round(df8['length'].mean(),2)
        std_global = round(df8['length'].std(),2)
        
        # adicionando as linhas no gráfico - visualização
        fig.add_hline(y=mean_global,line_width=2, line_color="white",annotation_text="Mean baseline",annotation_position="bottom right")
        fig.add_hline(y=mean_global + std_global,line_width=1, line_dash="dash", line_color="white",annotation_text="Mean + 1 std",annotation_position="bottom right",annotation_font_color="white")
        fig.add_hline(y=mean_global - std_global,line_width=1, line_dash="dash", line_color="white",annotation_text="Mean - 1 std",annotation_position="bottom right",annotation_font_color="white")
        fig.add_hline(y=mean_local,line_width=3, line_color="yellow",annotation_text="Mean",annotation_position="top right",annotation_font_color="yellow")
        
        # ajustando o indicador
        fig_a = go.Figure()
        fig_a.add_trace(go.Indicator(
        mode = "number+delta",
        value = mean_local,
        title = {"text": "Traffic Congestion Indicator<br><span style='font-size:0.8em;color:gray'>Traffic congestion in km</span><br><span style='font-size:0.8em;color:gray'>% Last update vs Baseline</span>"},
        delta = {'reference': mean_global, 'relative': True},
        domain = {'x': [0, 1], 'y': [0, 1]}))
        fig_a.update_layout(paper_bgcolor = "#1e1e1e",width=450, height=310)
        fig_a.update_traces(title_font_color="white", delta_increasing_color="#FB0D0D",delta_decreasing_color="#00FE35",number_font_color="white")
        
    else:
        sp_df_5min = pd.read_csv('/home/diluisi/Documentos/BID_Project/Projeto_Final/traffic_now.csv',parse_dates=['5min'])
        sp_df_5min['length'] = sp_df_5min['length']/1000
        if category == '3-4-5':
            # base filtrada pela data
            df1 = sp_df_5min[sp_df_5min['5min']>=dt.date.today()].dropna().copy()
            # obtendo a soma de congestionamento por segmento
            df2 = df1[['5min','new_street','length','time_hm']].groupby(['5min','new_street','time_hm']).sum().reset_index()
            df3 = df2[['time_hm','new_street','length']].groupby(['time_hm','new_street']).mean().reset_index()
            df4 = df3[['time_hm','length']].groupby(['time_hm']).sum().reset_index()

            # obtendo a soma de congestionamento por segmento
            df6 = city_df_30min_45[['30min','new_street','length','time_hm']].groupby(['30min','new_street','time_hm']).sum().reset_index()
            df7 = df6[['time_hm','new_street','length']].groupby(['time_hm','new_street']).mean().reset_index()
            df8 = df7[['time_hm','length']].groupby(['time_hm']).sum().reset_index()
            
            hist_45 = pd.read_csv('/home/diluisi/Documentos/BID_Project/Projeto_Final/historico_345.csv',parse_dates=['time_hm'])
            hist_45['time_hm'] = hist_45['time_hm'].dt.strftime('%H:%M')
            
            # Figura
            hist_345 = pd.read_csv('/home/diluisi/Documentos/BID_Project/Projeto_Final/historico_345.csv',parse_dates=['time_hm'])
            hist_345['time_hm'] = hist_345['time_hm'].dt.strftime('%H:%M')

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hist_345['time_hm'], y=hist_345['mean'], name='Baseline',line=dict(color='white', width=2)))
            fig.add_trace(go.Scatter(x=hist_345['time_hm'], y=hist_345['mean_p10'], name='Baseline + 10%',line=dict(color='#19D3F3', width=2, dash='dash')))
            fig.add_trace(go.Scatter(x=hist_345['time_hm'], y=hist_345['mean_m10'], name='Baseline - 10%',line=dict(color='#0099C6', width=2, dash='dash')))
            fig.add_bar(x=df4['time_hm'], y=df4['length'],name='Last 5 min')
            # Add shape regions
            fig.add_vrect(
                    x0="06:00", x1="10:00",
                    fillcolor="rgb(242,242,242)", opacity=0.3,
                    layer="below", line_width=0,
                    ),
            fig.add_vrect(
                    x0="15:00", x1="20:00",
                    fillcolor="rgb(242,242,242)", opacity=0.3,
                    layer="below", line_width=0,
                    ),
            
            fig.update_layout({'plot_bgcolor': 'rgba(0, 0, 0, 0)','paper_bgcolor': 'rgba(0, 0, 0, 0)',},template="plotly_dark",uirevision=True,xaxis_title="Time interval [5 min]",yaxis_title="Traffic congestion [km]")
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgb(102,102,102)')
            
            fig_a = go.Figure()
            fig_a.add_trace(go.Indicator(
            mode = "number+delta",
            value = np.float(df4[df4['time_hm']==np.max(df4['time_hm'])].length),
            title = {"text": "Traffic Congestion Indicator<br><span style='font-size:0.8em;color:gray'>Traffic congestion in km</span><br><span style='font-size:0.8em;color:gray'>% variation Last update vs Baseline</span>"},
            delta = {'reference': np.float(hist_345[hist_45['time_hm']==np.max(df4['time_hm'])]['mean']), 'relative': True},
            domain = {'x': [0, 1], 'y': [0, 1]}))
            fig_a.update_layout(paper_bgcolor = "#1e1e1e",width=450, height=310)
            fig_a.update_traces(title_font_color="white", delta_increasing_color="#FB0D0D",delta_decreasing_color="#00FE35",number_font_color="white")
            
        else:
            # base filtrada pela data
            df1 = sp_df_5min[(sp_df_5min['5min']>=dt.date.today()) & (sp_df_5min['level']>=4)].dropna().copy()
            # obtendo a soma de congestionamento por segmento
            df2 = df1[['5min','new_street','length','time_hm']].groupby(['5min','new_street','time_hm']).sum().reset_index()
            df3 = df2[['time_hm','new_street','length']].groupby(['time_hm','new_street']).mean().reset_index()
            df4 = df3[['time_hm','length']].groupby(['time_hm']).sum().reset_index()

            # obtendo a soma de congestionamento por segmento
            df6 = city_df_30min_45[['30min','new_street','length','time_hm']].groupby(['30min','new_street','time_hm']).sum().reset_index()
            df7 = df6[['time_hm','new_street','length']].groupby(['time_hm','new_street']).mean().reset_index()
            df8 = df7[['time_hm','length']].groupby(['time_hm']).sum().reset_index()
            
            hist_45 = pd.read_csv('/home/diluisi/Documentos/BID_Project/Projeto_Final/historico_45.csv',parse_dates=['time_hm'])
            hist_45['time_hm'] = hist_45['time_hm'].dt.strftime('%H:%M')
            
            # Figura
            hist_45 = pd.read_csv('/home/diluisi/Documentos/BID_Project/Projeto_Final/historico_45.csv',parse_dates=['time_hm'])
            hist_45['time_hm'] = hist_45['time_hm'].dt.strftime('%H:%M')

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hist_45['time_hm'], y=hist_45['mean'], name='Baseline',line=dict(color='white', width=2)))
            fig.add_trace(go.Scatter(x=hist_45['time_hm'], y=hist_45['mean_p10'], name='Baseline + 10%',line=dict(color='#19D3F3', width=2, dash='dash')))
            fig.add_trace(go.Scatter(x=hist_45['time_hm'], y=hist_45['mean_m10'], name='Baseline - 10%',line=dict(color='#0099C6', width=2, dash='dash')))
            fig.add_bar(x=df4['time_hm'], y=df4['length'],name='Last 5 min')
            # Add shape regions
            fig.add_vrect(
                    x0="06:00", x1="10:00",
                    fillcolor="rgb(242,242,242)", opacity=0.3,
                    layer="below", line_width=0,
                    ),
            fig.add_vrect(
                    x0="15:00", x1="20:00",
                    fillcolor="rgb(242,242,242)", opacity=0.3,
                    layer="below", line_width=0,
                    ),

            fig.update_layout({'plot_bgcolor': 'rgba(0, 0, 0, 0)','paper_bgcolor': 'rgba(0, 0, 0, 0)',},template="plotly_dark",uirevision=True, xaxis_title="Time interval [5 min]",yaxis_title="Traffic congestion [km]")
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgb(102,102,102)')
                
            fig_a = go.Figure()
            fig_a.add_trace(go.Indicator(
            mode = "number+delta",
            value = np.float(df4[df4['time_hm']==np.max(df4['time_hm'])].length),
            title = {"text": "Traffic Congestion Indicator<br><span style='font-size:0.8em;color:gray'>Traffic congestion in km</span><br><span style='font-size:0.8em;color:gray'>% variation Mean vs Mean baseline</span>"},
            delta = {'reference': np.float(hist_45[hist_45['time_hm']==np.max(df4['time_hm'])]['mean']), 'relative': True},
            domain = {'x': [0, 1], 'y': [0, 1]}))
            fig_a.update_layout(paper_bgcolor = "#1e1e1e",width=450, height=310)
            fig_a.update_traces(title_font_color="white", delta_increasing_color="#FB0D0D",delta_decreasing_color="#00FE35",number_font_color="white")
                        
    return fig, fig_a, figb

@app.callback(
    Output("location-dropdown", "options"),
    Input("region-dropdown", "value")
    )
def update_options(region):
    return [{"label": i, "value": i} for i in sorted(option_list[option_list['city']==region].street.unique())]
    
if __name__=='__main__':
    
    app.run_server(debug=True, port=8886)    