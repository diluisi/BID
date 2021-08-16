#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul  9 12:57:12 2021

@author: diluisi
"""
#import pprint
import io
import boto3
import pandas as pd
from retrying import retry
import datetime as dt

@retry(stop_max_delay=900*1000,
        wait_fixed=15 *1000)
def poll_status(_id,athena):
    '''
    poll query status
    '''
    result = athena.get_query_execution(
        QueryExecutionId = _id
    )

    # logging.info(pprint.pformat(result['QueryExecution']))
    state = result['QueryExecution']['Status']['State']
    print(state)
    if state == 'SUCCEEDED':
        return result
    elif state == 'FAILED':
        return result
    else:
        raise Exception
        
@retry(stop_max_attempt_number=10)
def download_s3(s3,S3BUCKET_NAME,s3_key):
    try:
        obj = s3.Object(bucket_name=S3BUCKET_NAME, key=s3_key).get()
        df = pd.read_csv(io.BytesIO(obj['Body'].read()), encoding='utf8')
        return df
    except:
        raise Exception

def query_execution(start_date, end_date, month , year):
    
    S3BUCKET_NAME = 'aws-athena-query-results-east-2'
    DATABASE_NAME = 'cities'
    
    #filename
    sql = (("SELECT \"pub_utc_date\",\"street\", \"level\", \"length\", \"line_geojson\"" +" FROM \"cities\".\"br_saopaulo_waze_jams\""+" WHERE day BETWEEN {} AND {} AND year={} AND month = {} AND level IN (3,4,5) AND city='São Paulo' ").format(start_date, end_date, year, month))

    
    athena = boto3.client('athena')
    s3 = boto3.resource('s3')
    result = athena.start_query_execution(
        QueryString = sql,
        QueryExecutionContext = {
            'Database': DATABASE_NAME
        },
        ResultConfiguration = {
            'OutputLocation': 's3://' + S3BUCKET_NAME,
        },
        WorkGroup='EquipeCiro'
    )
    
    # logging.info(pprint.pformat(result))
    QueryExecutionId = result['QueryExecutionId']
    result = poll_status(QueryExecutionId,athena)
        
    # save query result from S3
    if result['QueryExecution']['Status']['State'] == 'SUCCEEDED':
        s3_key = QueryExecutionId + '.csv'
        df = download_s3(s3,S3BUCKET_NAME,s3_key)
        df['pub_utc_date'] = pd.to_datetime(df['pub_utc_date'])
    
    return df

def query_transf(start_date, end_date, month , year):
    
    # busca na AWS
    df = query_execution(start_date, end_date, month , year)
        
    # arquivos de DE PARA
    de_para = pd.read_csv('sp_streets.txt')
    
    # conversão para lista
    wl1 = de_para['street'].to_list()
    
    # Por ora estamos descartando as vias que estão como null
    df.dropna(subset=['street'],inplace=True)
    
    # Filtro no Dataframe somente com as vias/segmentos que constam no DE PARA
    df2 = df[df['street'].isin(wl1)]
    
    # Ajuste do fuso horário
    df2['timestamp'] = df2.pub_utc_date - dt.timedelta(hours=3)
    df2['minute'] = df2['timestamp'].dt.minute
    df2['hour'] = df2['timestamp'].dt.hour
    df2['day'] = df2['timestamp'].dt.day
    
    # Cópia do df
    df3 = df2[['timestamp','day','hour','minute','street','length','level','line_geojson']].copy()
    
    # janela temporal de observação
    df3['30min'] = df3['timestamp'].dt.round('30min')
    
    # Converte os nomes dos segmentos do Waze para um nome mais legível
    df4 = pd.merge(df3,de_para,on='street')

    # construção das bases por janela temporal (5min, 15min,30min,60min)
    df4.sort_values(by=['timestamp', 'street','level'],ascending=False, inplace=True)
    df4.drop_duplicates(subset=['timestamp','line_geojson'], keep='first', inplace=True)
    
    df5 = df4.groupby(['30min','new_street', 'street','line_geojson']).mean().reset_index()[['30min','new_street','line_geojson','length']]
    df6 = df4[df4['level'].isin([4,5])].groupby(['30min','new_street', 'street','line_geojson']).mean().reset_index()[['30min','new_street','line_geojson','length']]
    
    df5['week'] = df5['30min'].dt.dayofweek
    df6['week'] = df6['30min'].dt.dayofweek
    
    # inclusão da classificação DIA ÚTIL = BD  e FINAIS DE SEMANA = FD
    daw345 = []
    for index, row in df5.iterrows():
        if row['week'] == 5 or row['week'] == 6:
            daw345.append('FD')
        else:
            daw345.append('BD')
    df5['weekday'] = daw345
    
    daw45 = []
    for index, row in df6.iterrows():
        if row['week'] == 5 or row['week'] == 6:
            daw45.append('FD')
        else:
            daw45.append('BD')
    df6['weekday'] = daw45
    
    df5['time_hm'] = df5['30min'].dt.strftime('%H:%M')
    df6['time_hm'] = df6['30min'].dt.strftime('%H:%M')
    
    df5['length'] = df5['length']/1000
    df6['length'] = df6['length']/1000
    
    return df5, df6
