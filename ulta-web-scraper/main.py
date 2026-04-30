import click
import json
import time
import requests
import pandas as pd
from pathlib import Path


BASE_DIR       = Path('/Users/karencantrell/Documents/Projects/python-scribbles/ulta-web-scraper')
OUTPUT_PATH    = BASE_DIR / 'data_tools.csv'
CHECKPOINT_PATH = BASE_DIR / 'checkpoint.json'

CATEGORIES = [
    #('Makeup',    '/shop/makeup/all'),
    #('Skincare',  '/shop/skin-care/all'),
    #('Hair Care', '/shop/hair/all'),
    #('Fragrance', '/shop/fragrance/all'),
    #('Body Care', '/shop/body-care/all'),
    #('Wellness',  '/shop/wellness-by-ulta-beauty/all'),
    ('Tools',     '/shop/tools-brushes/all'),
]

GRAPHQL_URL = 'https://www.ulta.com/v1/client/dxl/graphql'
GRAPHQL_PARAMS = {'ultasite': 'en-us', 'User-Agent': 'gomez'}
GRAPHQL_QUERY = """
query Page($url: JSON, $moduleParams: JSON) {
  Page(url: $url, moduleParams: $moduleParams) {
    content
  }
}
"""

DELAY_SECONDS     = 2
BREAK_EVERY_PAGES = 25
BREAK_SECONDS     = 45
CATEGORY_PAUSE    = 90
MAX_RETRIES       = 8
RETRY_BACKOFF     = 60

session = requests.Session()
session.headers.update({
    'User-Agent':   'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer':      'https://www.ulta.com/',
    'Origin':       'https://www.ulta.com',
    'Content-Type': 'application/json',
    'Accept':       'application/json',
})


def fetch_page(path, page):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = session.post(
                GRAPHQL_URL,
                params=GRAPHQL_PARAMS,
                json={
                    'operationName': 'Page',
                    'query':         GRAPHQL_QUERY,
                    'variables':     {'url': {'path': path}, 'moduleParams': {'page': page}},
                },
                timeout=30,
            )
            response.raise_for_status()
            content = response.json().get('data', {}).get('Page', {}).get('content')
            if not content:
                return None
            for mod in content.get('modules', []):
                if mod.get('moduleName') == 'ProductListingResults':
                    return mod
            return None
        except requests.HTTPError as e:
            if response.status_code == 408 and attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF * attempt
                click.echo(f'  Rate limited (408), retrying in {wait}s (attempt {attempt}/{MAX_RETRIES})...')
                time.sleep(wait)
            else:
                raise
        except requests.RequestException as e:
            if attempt < MAX_RETRIES:
                click.echo(f'  Request error: {e}, retrying in {RETRY_BACKOFF}s...')
                time.sleep(RETRY_BACKOFF)
            else:
                raise


def extract_products(plr_module, category_name):
    products = []
    for item in plr_module.get('items', []):
        price = item.get('salePrice') or item.get('listPrice')
        products.append({
            'category':    category_name,
            'brand':       item.get('brandName'),
            'name':        item.get('productName'),
            'price':       price,
            'avg_rating':  item.get('rating'),
            'num_ratings': item.get('reviewCount'),
        })
    return products


def load_checkpoint():
    if CHECKPOINT_PATH.exists():
        return set(json.loads(CHECKPOINT_PATH.read_text()).get('completed', []))
    return set()


def save_checkpoint(completed):
    CHECKPOINT_PATH.write_text(json.dumps({'completed': list(completed)}))


def save_products(all_products):
    df = (pd.DataFrame(all_products)
            .reindex(columns=['category', 'brand', 'name', 'price', 'avg_rating', 'num_ratings'])
            .drop_duplicates(subset=['name', 'brand'])
            .reset_index(drop=True))
    df.to_csv(OUTPUT_PATH, index=False)
    return df


@click.command()
@click.option('--resume', is_flag=True, default=False, help='Skip already-completed categories.')
def main(resume):
    completed = set()
    all_products = []

    if resume:
        completed = load_checkpoint()
        if completed and OUTPUT_PATH.exists():
            existing = pd.read_csv(OUTPUT_PATH)
            all_products = existing.to_dict('records')
            click.echo(f'Resuming: loaded {len(all_products)} existing products, skipping {completed}')

    try:
        first_active = True
        for category_name, path in CATEGORIES:
            if category_name in completed:
                click.echo(f'Skipping {category_name} (already scraped)')
                continue

            if not first_active:
                click.echo(f'  Pausing {CATEGORY_PAUSE}s between categories...')
                time.sleep(CATEGORY_PAUSE)
            first_active = False

            click.echo(f'Scraping {category_name}...')
            page = 1

            while True:
                plr = fetch_page(path, page)
                if not plr or not plr.get('items'):
                    click.echo(f'  No products on page {page}, stopping.')
                    break

                products = extract_products(plr, category_name)
                all_products.extend(products)
                click.echo(f'  Page {page}: +{len(products)} products (total so far: {plr["resultCount"]})')

                page_size    = plr.get('pageSize', 64)
                result_count = plr.get('resultCount', 0)
                if page * page_size >= result_count:
                    break

                page += 1
                if page % BREAK_EVERY_PAGES == 0:
                    click.echo(f'  Taking a {BREAK_SECONDS}s break at page {page}...')
                    time.sleep(BREAK_SECONDS)
                else:
                    time.sleep(DELAY_SECONDS)

            completed.add(category_name)
            save_checkpoint(completed)
            df = save_products(all_products)
            click.echo(f'  {category_name} done. {len(df)} unique products saved so far.')

        df = save_products(all_products)
        click.echo(f'Success! {len(df)} products saved to {OUTPUT_PATH}')

    except Exception as e:
        click.echo(f'Process failed: {e}')
        if all_products:
            df = save_products(all_products)
            click.echo(f'Saved {len(df)} products collected before failure to {OUTPUT_PATH}')


if __name__ == '__main__':
    main()
