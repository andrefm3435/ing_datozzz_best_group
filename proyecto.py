# Página del proyecto final de ingeniería de datos
# Universidad del Rosario 2024


import pandas as pd
import psycopg2 as psy2
import dash
from dash import dcc,Input,Output,callback
from dash import html
import plotly.express as px
import plotly.graph_objs as go
from dash import dash_table as tbl

dbname = "Base argentina"
user = "javier" 
password = "123456"
host = "localhost"

# Connect to the database
conn = psy2.connect(
    dbname=dbname,
    user=user,
    password=password,
    host=host
)


# Pregunta 1
consulta_ing_univer = """
SELECT ingreso_tot
FROM tipo_ingreso 
JOIN miembro ON tipo_ingreso.id2_miembro = miembro.id_miembro 
JOIN educacion ON miembro.id_miembro = educacion.id1_miembro 
WHERE educacion.nivel_actual = 'Universitario';
"""

consulta_ing_no_univer_laboral = """
SELECT ingreso_tot
FROM tipo_ingreso 
JOIN miembro ON tipo_ingreso.id2_miembro = miembro.id_miembro 
JOIN educacion ON miembro.id_miembro = educacion.id1_miembro 
WHERE educacion.nivel_actual != 'Universitario';
"""
R_uni = pd.read_sql(consulta_ing_univer, conn)
R_no_uni = pd.read_sql(consulta_ing_no_univer_laboral, conn)

# Pregunta 2

# Pregunta 3
query3i = """
SELECT mi.id_miembro, mi.parentesco, mi.sexo, ti.ingreso_tot
FROM miembro mi
JOIN Tipo_ingreso ti ON mi.id_miembro = ti.id2_miembro
WHERE mi.sexo = 'Mujer' AND mi.parentesco = 'Jefe';
"""
# Consulta SQL para obtener los conteos de salarios superiores e inferiores a 14125
query3ii = """
SELECT 
    CASE 
        WHEN ti.ingreso_tot > 14125 THEN 'Superiores a 14125'
        ELSE 'Inferiores a 14125'
    END AS salario_grupo,
    COUNT(*) AS count
FROM miembro mi
JOIN Tipo_ingreso ti ON mi.id_miembro = ti.id2_miembro
WHERE mi.sexo = 'Mujer' AND mi.parentesco = 'Jefe'
GROUP BY salario_grupo;
"""


# Consulta SQL para calcular los promedios de salarios por cuartil sin usar NTILE
query3iii = """ 
WITH quartiles AS (
    SELECT ingreso_tot,
        NTILE(4) OVER (ORDER BY ingreso_tot) AS quartile
    FROM (
        SELECT ti.ingreso_tot
        FROM miembro mi
        JOIN Tipo_ingreso ti ON mi.id_miembro = ti.id2_miembro
        WHERE mi.sexo = 'Mujer' AND mi.parentesco = 'Jefe'
    ) AS subquery
)
SELECT quartile,
    AVG(ingreso_tot) AS ingreso_promedio
FROM quartiles
GROUP BY quartile
ORDER BY quartile;
"""

df3 = pd.read_sql(query3i, conn)
grupo_counts = pd.read_sql(query3ii, conn)
quartile_avg = pd.read_sql(query3iii, conn)

# Pregunta 4
sql_query4 = "Select educacion.sector_educativo, avg(tipo_ingreso.ingreso_fam) as ingresos_familiares, avg(tipo_ingreso.ingreso_tot_lab) as salario from educacion join miembro on educacion.id1_miembro = miembro.id_miembro join tipo_ingreso on educacion.id1_miembro = tipo_ingreso.id2_miembro where sector_educativo != '' group by educacion.sector_educativo"
df4 =pd.read_sql(sql_query4, conn)

# Pregunta 5
sql_query5 = "select salud.lugar_nacimiento, AVG(tipo_ingreso.ingreso_tot_lab) AS salario from salud JOIN miembro ON salud.id3_miembro = miembro.id_miembro JOIN tipo_ingreso ON salud.id3_miembro = tipo_ingreso.id2_miembro group by salud.lugar_nacimiento"
df5 =pd.read_sql(sql_query5, conn)

# Pregunta 6

# Pregunta 7







app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1('A data-driven analysis of Argentinian wages and household economics in 2019', style={'text-align' : 'center'}),
    html.Div('Se dispone de un conjunto de datos que contiene información demográfica y socioeconómica de Argentina en el 2019, sujeta a ciertas restricciones y reglas. El objetivo es realizar un análisis detallado de estos datos para responder a una serie de preguntas relacionadas con los ingresos, la educación, el estado conyugal, la situación laboral y otros aspectos relevantes de la población. El enfoque principal está orientado a entender los distintos factores que influyen en la obtención de salario elevados, identificando así las variables determinantes en el panorama socioeconómico del país.'),
    
    # Pregunta 1
    html.Div('''¿Cuales son los ingresos de las personas las cuales han terminado sus estudios universitarios
            a comparación de aquellas personas que no los han completado '''),
    dcc.Graph(
        id='grafica1',
        figure=go.Figure(
            data=[
                go.Scatter(
                    x=R_uni.index,  
                    y=R_uni['ingreso_tot'],  
                    mode='lines',  
                    name='Ingresos, de Universitarios'  
                ),
                go.Scatter(
                    x=R_no_uni.index, 
                    y=R_no_uni['ingreso_tot'], 
                    mode='lines',  
                    name='Ingresos de,no Universitarios'  
                )
            ],
            layout=go.Layout(
                title='Ingresos Laborales',
                xaxis_title='Índice',
                yaxis_title='Ingresos Laborales'
            )
        )
    ),

    # Pregunta 3
    html.Div([
        html.H1('Salarios de mujeres jefas de familia', style={
            'text-align': 'center',
            'color': '#FFFFFF'
        })
    ]),
    html.Div('Datos de salarios de mujeres jefas de familia', style={
        'color': '#FFFFFF'
    }),
    dcc.Graph(
        id='salary-graph',
        figure=px.scatter(df3, x='id_miembro', y='ingreso_tot', title='Salarios de Mujeres Jefas de Familia',
                          labels={'id_miembro': 'ID del Miembro', 'ingreso_tot': 'Salarios'},
                          trendline='ols',  # Añade una línea de tendencia de regresión lineal
                          color='ingreso_tot',
                          color_continuous_scale=px.colors.sequential.Viridis)
    ),
    dcc.Graph(
        id='salary-bar-graph',
        figure=px.bar(df3, x='id_miembro', y='ingreso_tot', title='Salarios de Mujeres Jefas de Familia',
                      labels={'id_miembro': 'ID del Miembro', 'ingreso_tot': 'Salarios'},
                      color='ingreso_tot',
                      color_continuous_scale=px.colors.sequential.Viridis)
    ),
    dcc.Graph(
        id='salary-pie-graph',
        figure=px.pie(quartile_avg, values='ingreso_promedio', names='quartile',
                      title='Promedio de salarios por cuartil',
                      labels={'ingreso_promedio': 'Promedio de Salarios', 'quartile': 'Cuartil'},
                      color_discrete_sequence=px.colors.sequential.Viridis)
    ),
    dcc.Graph(
        id='salary-group-pie-graph',
        figure=px.pie(grupo_counts, values='count', names='salario_grupo',
                      title='Distribución de salarios superiores e inferiores a 14125',
                      labels={'count': 'Número de Personas', 'salario_grupo': 'Grupo de Salarios'},
                      color_discrete_sequence=px.colors.sequential.Viridis)
    ),

    # Preguntas 4 y 5
    dcc.Graph(
        id = 'grafica1',
            figure=px.bar(df4, x='sector_educativo', y='ingresos_familiares', title='¿Cómo se comparan los ingresos familiares y el salario entre universidad privada y pública?').update_layout(            
            xaxis_title = 'Sector Educativo',
            yaxis_title = 'Ingresos Familiares'
            )
        
        ),
    dcc.Graph(
        id = 'grafica2',
            figure=px.bar(df4, x='sector_educativo', y='salario', title='¿Cómo se comparan los ingresos familiares y el salario entre universidad privada y pública?').update_layout(            
            xaxis_title = 'Sector Educativo',
            yaxis_title = 'Salario'
            )
        
        ),
    dcc.Graph(
        id = 'grafica3',
            figure=px.bar(df5, x='lugar_nacimiento', y='salario', title='¿Qué lugar de nacimiento (de los presentes en la encuesta) cuenta con los mayores salarios?').update_layout(            
            xaxis_title = 'Lugar de nacimiento',
            yaxis_title = 'Salario'
            )
        
        )
])

@callback(Output('tbl_out','children'),Input('tbl','active_cell'))
def update_graphs(active_cell):
    return str(active_cell) if active_cell else "Click the table"

if __name__ == '__main__':
    app.run_server(port=8085)
