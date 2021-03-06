import click
import lxml
import pandas as pd
import requests
import time
from datetime import datetime, timedelta
from lxml import html

#helper functions
def format_date(date):
  #returns a date formatted as a string to pass to the header
  date_string = str(int(time.mktime(date.timetuple())))
  return date_string

def subdomain(symbol, start, end, filter):
  #returns a subdomain to pass to the header
  subdomain = f'/quote/{symbol}/history?period1={start}&period2={end}&interval=1d&filter={filter}&frequency=1d'
  return subdomain

def header(subdomain):
  #returns a header to pass to the requests.get() method
  header = {'authority': 'finance.yahoo.com',
            'method': 'GET',
            'path': subdomain,
            'scheme': 'https',
            'accept': 'text/html',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'no-cache',
            'dnt': '1',
            'pragma': 'no-cache',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64)'}
  return header

def time_chunker(start_date, end_date):
  #chunks date requests as yahoo finance only returns 100 rows at a time :(
  start_int = int(start_date)
  end_int = int(end_date)
  start_dates = []
  end_dates = []
  if (end_int - start_int) <= 8640000:
    start_dates.append(str(start_int))
    end_dates.append(str(end_int))
  else:
    while start_int < end_int:
      #print('start time ' + str(time.asctime(time.localtime(start_int))))
      #print('end time ' + str(time.asctime(time.localtime(min(start_int + (8640000), end_int)))))
      start_dates.append(str(start_int))
      end_dates.append(str(min(start_int + (8640000), end_int)))
      start_int += (8640000)
  return start_dates, end_dates

def main():
  try:
    #parameters
    symbol = 'STX' 
    start_date = format_date(datetime(2017, 1, 1))
    end_date = format_date(datetime(2021, 3, 1))
    stock_filter = 'history'

    #helper variables
    start_dates, end_dates = time_chunker(start_date, end_date)
    final_df = pd.DataFrame()

    for index, item in enumerate(start_dates):
      #get stock prices
      sub = subdomain(symbol, start_dates[index], end_dates[index], stock_filter)
      headers = header(sub)
      url = f'https://finance.yahoo.com{sub}'

      page = requests.get(url, headers=headers)

      element_html = html.fromstring(page.content)
      table = element_html.xpath('//table')
      table_tree = lxml.etree.tostring(table[0], method='xml')

      df = (pd.read_html(table_tree)[0].iloc[:-1]
              .drop(columns=['Open', 'High', 'Low', 'Close*', 'Volume'])
              .rename(columns={'Date': 'date', 'Adj Close**': 'stock_price'})
              .assign(date = lambda x: x['date'].apply(lambda y: datetime.strptime(y, '%b %d, %Y').strftime('%Y-%m-%d')))
              .query('~stock_price.str.contains("Dividend")')
              .sort_values(by=['date']))
      final_df = final_df.append(df, ignore_index=True)

    final_df.to_csv(f'/Users/karenizuka/Projects/python-scribbles/stock-price-scraper/data.csv', index=False)
    
    click.echo(f'Success! CSV file created!')
    input('Press enter to continue')
  except Exception as e:
    click.echo(f'Process failed because {e}')
    input('Press enter to continue')

if __name__ == '__main__':
  main()