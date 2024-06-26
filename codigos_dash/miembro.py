import pandas as pd
import psycopg2 as psy2
import dash
from dash import dcc,Input,Output,callback
from dash import html
import plotly.express as px
from dash import dash_table as tbl
import dash_bootstrap_components as dbc



dbname = "Base argentina"
user = "javier"
password = "123456"
host = "localhost"


conn = psy2.connect(dbname =dbname, user = user, password = password, host = host)

sql_query = "Select * from miembro;"

df =pd.read_sql(sql_query, conn)


app = dash.Dash(__name__)

app.layout = html.Div([
    html.Div([
        html.H1('A data-driven analysis of Argentinian wages and household economics in 2019'),
        html.Img(src='complementos/cat.png')
        ], className = 'banner'),
    dbc.Container([
        dbc.Label('Miembro'),
        tbl.DataTable(
        id='table',
        columns=[{"id":i} for i in df.columns],
        data=df.to_dict('records'),
        page_size=15000,
        style_table={'height': '500px', 'overflowY': 'auto'}
        ),
        dbc.Alert(id='tbl_out')
    ]),
])

@callback(Output('tbl_out','children'),Input('tbl','active_cell'))
def update_graphs(active_cell):
    return str(active_cell) if active_cell else "Click the table"

if __name__ == '__main__':
    app.run(port=8085)
