import click
import yfinance as yf

def main():
  try:
    symbol = 'STX'
    start_date = '2021-01-01'
    end_date = '2025-12-31'

    df = (yf.Ticker(symbol)
            .history(start=start_date, end=end_date, auto_adjust=True)
            .reset_index()[['Date', 'Close']]
            .rename(columns={'Date': 'date', 'Close': 'stock_price'})
            .assign(date=lambda x: x['date'].dt.strftime('%Y-%m-%d')))

    df.to_csv('/Users/karencantrell/Documents/Projects/python-scribbles/stock-price-scraper/data.csv', index=False)
    click.echo('Success! CSV file created!')
    input('Press enter to continue')
  except Exception as e:
    click.echo(f'Process failed because {e}')
    input('Press enter to continue')

if __name__ == '__main__':
  main()
