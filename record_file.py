import pandas as pd
import numpy as np
import json
import datetime as dt
import requests
import time

# ps -ef | grep python
# kill -9 PID

# Classe para tratar os dados baixados da API
class Maplatlong():
    def __init__(self, lat, long, street, timestamp, level, length,timestamp_map,level_map):            
        self.lat = lat
        self.long = long
        self.street = street
        self.timestamp = timestamp
        self.level = level
        self.length = length
        self.timestamp_map= timestamp_map
        self.level_map = level_map

# client ID de acesso à API
client_id = 'Fundacao+Getulio+Vargas'

# lista de cidades
cities = ['Sao Paulo 1','Sao Paulo 2', 'Sao Paulo 3']

# arquivos de DE PARA
de_para_sp = pd.read_csv('sp_streets.txt')

# polígonos
WAZE_POLYGONS = {
    'Sao Paulo 1': {
        'city': 'São Paulo',
        'points': '-46.89388,-23.65469;-46.8972,-23.79037;-46.32591,-23.791;-46.32865,-23.64431;-46.89388,-23.65469',
    },
    'Sao Paulo 2': {
        'city': 'São Paulo',
        'points': '-46.9344,-23.4539;-46.91986,-23.55706;-46.27304,-23.52685;-46.30119,-23.35991;-46.9344,-23.4539',
    },
    'Sao Paulo 3': {
        'city': 'São Paulo',
        'points': '-46.2656,-23.52821;-46.92789,-23.5558;-46.90063,-23.65647;-46.31814,-23.64391;-46.2656,-23.52821',
    }
}

# atualização do arquivo
while True:
    latitude_map = []
    longitude_map = []
    street = []
    timestamp = []
    timestamp_map = []
    level_map= []
    level = []
    length = []
    for i in cities:
        polygon_city = WAZE_POLYGONS[i]['points']
        url = 'https://world-georss.waze.com/rtserver/web/TGeoRSS?format=JSON&types=traffic&tk=ccp_partner&ccp_partner_name={}&polygon={}'.format(client_id, polygon_city)
        response = requests.get(url)
        data = json.loads(response.text)

        for j in range(len(data['jams'])):
            try:
                if (data['jams'][j]['city'] == 'São Paulo') & (data['jams'][j]['level']>=3) & (data['jams'][j]['street'] in list(de_para_sp.street)):
                    print('***************************************')
                    level = np.append(level,data['jams'][j]['level'])
                    street = np.append(street,data['jams'][j]['street'])
                    length = np.append(length,data['jams'][j]['length'])
                    timestamp = np.append(timestamp,dt.datetime.strptime(data['endTime'][:-4], '%Y-%m-%d %H:%M:%S')- dt.timedelta(hours=3))
                    for k in range(len(data['jams'][j]['line'])):
                        latitude_map = np.append(latitude_map, data['jams'][j]['line'][k]['y'])
                        longitude_map = np.append(longitude_map, data['jams'][j]['line'][k]['x'])
                        timestamp_map = np.append(timestamp_map, dt.datetime.strptime(data['endTime'][:-4], '%Y-%m-%d %H:%M:%S')- dt.timedelta(hours=3))
                        level_map = np.append(level_map, data['jams'][j]['level'])
                    print('***************************************')
                    latitude_map = np.append(latitude_map,None)
                    longitude_map = np.append(longitude_map,None)
                    timestamp_map = np.append(timestamp_map,None)
                    level_map = np.append(level_map,None)
                    print(data['jams'][j]['street'])
            except:
                continue
        if i == 'Sao Paulo 1':
            sp1_data = Maplatlong(latitude_map, longitude_map, street, timestamp, level, length,timestamp_map, level_map)
        elif i == 'Sao Paulo 2':
            sp2_data = Maplatlong(latitude_map, longitude_map, street, timestamp, level, length,timestamp_map,level_map)
        elif i == 'Sao Paulo 3':
            sp3_data = Maplatlong(latitude_map, longitude_map, street, timestamp, level, length,timestamp_map,level_map)
            
    df1_map = pd.DataFrame({"latitude":sp1_data.lat, "longitude":sp1_data.long, "level":sp1_data.level_map})
    df2_map = pd.DataFrame({"latitude":sp2_data.lat, "longitude":sp2_data.long, "level":sp2_data.level_map})
    df3_map = pd.DataFrame({"latitude":sp3_data.lat, "longitude":sp3_data.long, "level":sp3_data.level_map})
    df_map = pd.concat([df1_map,df2_map,df3_map],ignore_index=True)
    df_map.to_csv('/home/diluisi/Documentos/BID_Project/Projeto_Final/map.csv', header=True, index=False)
    
    
    df1_hist = pd.DataFrame({"timestamp":sp1_data.timestamp, "new_street":sp1_data.street, "level":sp1_data.level, "length":sp1_data.length})
    df2_hist = pd.DataFrame({"timestamp":sp2_data.timestamp, "new_street":sp2_data.street, "level":sp2_data.level, "length":sp2_data.length})
    df3_hist = pd.DataFrame({"timestamp":sp3_data.timestamp, "new_street":sp3_data.street, "level":sp3_data.level, "length":sp3_data.length})
    df_hist = pd.concat([df1_hist,df2_hist,df3_hist],ignore_index=True)
    df_hist['5min'] = df_hist['timestamp'].dt.round('5min')
    df_hist['time_hm'] = df_hist['5min'].dt.strftime('%H:%M')
    
    df_hist.to_csv('traffic_now.csv', mode='a', header=False, index=False)
    
    time.sleep(300)
