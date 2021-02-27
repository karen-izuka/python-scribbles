import io
import json
import pandas as pd
import requests

#get df
url = 'https://raw.githubusercontent.com/karen-izuka/python-scribbles/main/animal-crossing-sankey/villagers.csv'
data_string = requests.get(url).content
df = (pd.read_csv(io.StringIO(data_string.decode('utf-8')))
        .groupby(['Gender','Personality','Hobby'], as_index=False).agg({'Unique_Entry_ID': 'count'})
        .rename(columns={'Unique_Entry_ID': 'value'}))
nodes = ['Gender', 'Personality', 'Hobby']

#turn into json
for i, node in enumerate(nodes):
  df[node] = '{0} '.format(i) + df[node]

#create nodes
node_dict = {}
node_list = []
node_name = []
for i, node in enumerate(nodes):
  node_dict['node{0}'.format(i)] = list(df[node].drop_duplicates())
for node in node_dict:
  for item in node_dict[node]:
    node_list.append({'name': item})
for node in node_dict:
  for item in node_dict[node]:
    node_name.append(item)

#create links
df_dict = {}
link_dict = {}
#create edges
i = 0
while i < len(nodes)-1:
  df_dict['df{0}'.format(i)] = df.groupby([nodes[i], nodes[i+1]], as_index=False).agg({'value': 'sum'})
  df_dict['df{0}'.format(i)]['source'] = df_dict['df{0}'.format(i)][nodes[i]].apply(lambda x: node_name.index(x))
  df_dict['df{0}'.format(i)]['target'] = df_dict['df{0}'.format(i)][nodes[i+1]].apply(lambda x: node_name.index(x))
  df_dict['df{0}'.format(i)] = df_dict['df{0}'.format(i)][['source', 'target', 'value']]
  link_dict['link{0}'.format(i)] = df_dict['df{0}'.format(i)].to_dict('records')
  i += 1

link_list = []
for i in link_dict:
  for j in link_dict[i]:
    link_list.append(j)
        
data = {'nodes': node_list, 'links': link_list}
data = json.dumps(data)
load = json.loads(data)
with open('/Users/karenizuka/Projects/python-scribbles/animal-crossing-sankey/data.json', 'w') as f:
  json.dump(load, f)