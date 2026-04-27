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
    start_date, end_date = '2025-01-01', '2025-12-31'

    #https://www.ncdc.noaa.gov/cdo-web/token
    token = 'QOfbQjpzVcCmENdSHcKHvzCpxFoRgytS'

    #https://www.ncdc.noaa.gov/cdo-web/datatools/findstation
    station_id = {
                  'Lafayette': 'USR0000CBRI',
                  'SF': 'USW00023234',
                  'LA': 'USW00093134',
                  'Phoenix': 'USW00023183',
                  'NYC': 'USW00094728',
                  'Orlando': 'USW00012815',
                }

    #loop through stations to generate weather df
    for i in station_id.keys():
      #instantiate empty lists
      dates = []
      max_temps = []
      min_temps = []

      #get data from noaa and load into json file
      # r = requests.get(f'https://www.ncei.noaa.gov/access/services/data/v1?dataset=daily-summaries&dataTypes=PRCP&stations=US1CACC0045&startDate=2025-01-01&endDate=2025-01-31&includeAttributes=true&format=json', headers={'token':token})
      r = requests.get(
        'https://www.ncei.noaa.gov/access/services/data/v1',
        params={
            'dataset': 'daily-summaries',
            'dataTypes': ['TMIN', 'TMAX'],
            'stations': station_id[i],
            'startDate': start_date,
            'endDate': end_date,
            'includeAttributes': 'true',
            'format': 'json',
            'units': 'metric'
        },
        headers={'token': token}
      )
      d = json.loads(r.text)

      #extract dates and temperatures from json file
      dates += [item['DATE'] for item in d if item.get('TMAX') is not None]
      max_temps += [item['TMAX'] for item in d if item.get('TMAX') is not None]
      min_temps += [item['TMIN'] for item in d if item.get('TMIN') is not None]

      #load dates and temperatures into df
      df = (pd.DataFrame()
              .assign(date = [datetime.strptime(d, "%Y-%m-%d") for d in dates])
              .assign(max_temp = [round(float(t)*9/5+32,2) for t in max_temps])
              .assign(min_temp = [round(float(t)*9/5+32,2) for t in min_temps])
              .assign(temperature = lambda x: round((x['max_temp'] + x['min_temp'])/2, 2))
              .assign(index = lambda x: x.index)
              .assign(location = str(i))
              .reindex(columns=['index','location','date','temperature']))
      print(df.head())
      # append df to final_df
      final_df = pd.concat([final_df, df], ignore_index=True)

    #output final df to csv
    final_df.to_csv(f'/Users/karencantrell/Documents/Projects/python-scribbles/weather-web-scraper/data.csv', index=False)

    #message box
    click.echo('Success! Weather extracted!')
    input('Press enter to continue')
  
  except Exception as e:
    click.echo(f'Process failed because {e}')
    input('Press enter to continue')

if __name__ == '__main__':
  main()