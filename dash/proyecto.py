# Página del proyecto final de ingeniería de datos
# Universidad del Rosario 2024


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

sql_query2= "select * from hogar;"
dc=pd.read_sql(sql_query2,conn)

app = dash.Dash(__name__)

app.layout = html.Div([

])

@callback(Output('tbl_out','children'),Input('tbl','active_cell'))
def update_graphs(active_cell):
    return str(active_cell) if active_cell else "Click the table"

if __name__ == '__main__':
    app.run(port=8085)
