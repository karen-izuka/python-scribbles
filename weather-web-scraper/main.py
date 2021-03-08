import click
import json
import numpy as np
import pandas as pd
import requests
from datetime import datetime

def main():
  try:
    #---set parameters---#
    final_df = pd.DataFrame()
    start_date, end_date = '2020-01-01', '2020-12-31'

    #https://www.ncdc.noaa.gov/cdo-web/token
    token = 'QOfbQjpzVcCmENdSHcKHvzCpxFoRgytS'

    #https://www.ncdc.noaa.gov/cdo-web/datatools/findstation
    station_id = {'SF': 'GHCND:USW00023234',
                  'Concord': 'GHCND:USW00023254',
                  'LA': 'GHCND:USW00023174',
                  'NYC': 'GHCND:USW00014732',
                  'Seattle': 'GHCND:USW00024233',
                  'Bend': 'GHCND:USS0021F21S'}

    #loop through stations to generate weather df
    for i in station_id.keys():
      #instantiate empty lists
      dates = []
      temps = []

      #get data from noaa and load into json file
      r = requests.get(f'https://www.ncdc.noaa.gov/cdo-web/api/v2/data?datasetid=GHCND&datatypeid=TAVG&limit=1000&stationid={station_id[i]}&startdate={start_date}&enddate={end_date}', headers={'token':token})
      d = json.loads(r.text)

      #extract dates and temperatures from json file
      average_temps = [item for item in d['results'] if item['datatype']=='TAVG']
      dates += [item['date'] for item in average_temps]
      temps += [item['value'] for item in average_temps]

      #load dates and temperatures into df
      df = (pd.DataFrame()
              .assign(date = [datetime.strptime(d, "%Y-%m-%dT%H:%M:%S") for d in dates])
              .assign(temperature = [round(float(t)/10.0*1.8+32,2) for t in temps])
              .assign(index = lambda x: x.index)
              .assign(location = str(i))
              .reindex(columns=['index','location','date','temperature']))
      
      #append df to final_df
      final_df = final_df.append(df, ignore_index=True)

    #output final df to csv
    final_df.to_csv(f'/Users/karenizuka/Projects/python-scribbles/weather-web-scraper/data.csv', index=False)

    #message box
    click.echo('Success! Weather extracted!')
    input('Press enter to continue')
  
  except Exception as e:
    click.echo(f'Process failed because {e}')
    input('Press enter to continue')

if __name__ == '__main__':
  main()