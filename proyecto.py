import pandas as pd
import psycopg2 as psy2
import dash
from dash import dcc, html, Input, Output, callback
import plotly.express as px
import plotly.graph_objs as go

dbname = "datos_Argentina"
user = "juan"
password = "123456"
host = "localhost"

# Connect to the database
conn = psy2.connect(dbname=dbname, user=user, password=password, host=host)

# Consultas SQL
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
sql_query2_1 = """
SELECT 
    (miembro.nmiembro_padre > 0 OR nmiembro_madre > 0) AS padres,
    AVG(ingreso_tot) AS avg_ingreso_tot
FROM 
    miembro 
INNER JOIN 
    tipo_ingreso 
ON 
    miembro.id_miembro = tipo_ingreso.id2_miembro 
GROUP BY 
    padres;
"""
sql_query2_2 = """
SELECT 
    (miembro.nmiembro_padre > 0 OR nmiembro_madre > 0) AS padres,
    estado_ocup 
FROM 
    miembro 
INNER JOIN 
    tipo_ingreso 
ON 
    miembro.id_miembro = tipo_ingreso.id2_miembro 
WHERE 
    ingreso_tot > 0;
"""
sql_query2_3 = """
SELECT 
    estado_ocup, 
    COUNT(tipo_ingreso.estado_ocup) AS count_estado_ocup 
FROM 
    miembro 
INNER JOIN 
    tipo_ingreso 
ON 
    miembro.id_miembro = tipo_ingreso.id2_miembro 
WHERE 
    tipo_ingreso.ingreso_tot > 0  
    AND (miembro.nmiembro_padre > 0 OR miembro.nmiembro_madre > 0) 
GROUP BY 
    tipo_ingreso.estado_ocup;
"""
sql_query2_4 = """
SELECT 
    estado_ocup,
    COUNT(tipo_ingreso.estado_ocup) AS count_estado_ocup 
FROM 
    miembro 
INNER JOIN 
    tipo_ingreso 
ON 
    miembro.id_miembro = tipo_ingreso.id2_miembro 
WHERE 
    tipo_ingreso.ingreso_tot > 0 
    AND NOT (miembro.nmiembro_padre > 0 OR miembro.nmiembro_madre > 0)  
GROUP BY 
    tipo_ingreso.estado_ocup;
"""
df2_1 = pd.read_sql(sql_query2_1, conn)
df2_2 = pd.read_sql(sql_query2_2, conn)
df2_3 = pd.read_sql(sql_query2_3, conn)
df2_4 = pd.read_sql(sql_query2_4, conn)

# Pregunta 3
query3i = """
SELECT mi.id_miembro, mi.parentesco, mi.sexo, ti.ingreso_tot
FROM miembro mi
JOIN Tipo_ingreso ti ON mi.id_miembro = ti.id2_miembro
WHERE mi.sexo = 'Mujer' AND mi.parentesco = 'Jefe';
"""
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
sql_query4 = """
SELECT educacion.sector_educativo, 
       AVG(tipo_ingreso.ingreso_fam) as ingresos_familiares, 
       AVG(tipo_ingreso.ingreso_tot_lab) as salario 
FROM educacion 
JOIN miembro ON educacion.id1_miembro = miembro.id_miembro 
JOIN tipo_ingreso ON educacion.id1_miembro = tipo_ingreso.id2_miembro 
WHERE sector_educativo != '' 
GROUP BY educacion.sector_educativo
"""
df4 = pd.read_sql(sql_query4, conn)

# Pregunta 5
sql_query5 = """
SELECT salud.lugar_nacimiento, 
       AVG(tipo_ingreso.ingreso_tot_lab) AS salario 
FROM salud 
JOIN miembro ON salud.id3_miembro = miembro.id_miembro 
JOIN tipo_ingreso ON salud.id3_miembro = tipo_ingreso.id2_miembro 
GROUP BY salud.lugar_nacimiento
"""
df5 = pd.read_sql(sql_query5, conn)

#Pregunta 6
sql_query6 = """
WITH tamanio_hogar AS (
    SELECT id_hogar, COUNT(*) AS num_miembros
    FROM miembro
    GROUP BY id_hogar
),

promedio_escolaridad_hogar AS (
    SELECT m.id_hogar, AVG(e.años_escolaridad) AS promedio_escolaridad
    FROM miembro m
    JOIN educacion e ON m.id_miembro = e.id1_miembro
    GROUP BY m.id_hogar
)

SELECT t.num_miembros, AVG(p.promedio_escolaridad) AS promedio_escolaridad
FROM tamanio_hogar t
JOIN promedio_escolaridad_hogar p ON t.id_hogar = p.id_hogar
GROUP BY t.num_miembros
ORDER BY t.num_miembros;
"""
df6 =pd.read_sql(sql_query6, conn)

app = dash.Dash(__name__)

# Layout con botones de navegación y contenido dinámico
app.layout = html.Div([
    html.H1('Análisis de Datos Socioeconómicos de Argentina 2019', style={'text-align': 'center'}),
    dcc.Tabs(id='tabs', value='tab-1', children=[
        dcc.Tab(label='Pregunta 1', value='tab-1'),
        dcc.Tab(label='Pregunta 2', value='tab-2'),
        dcc.Tab(label='Pregunta 3', value='tab-3'),
        dcc.Tab(label='Pregunta 4', value='tab-4'),
        dcc.Tab(label='Pregunta 5', value='tab-5'),
        dcc.Tab(label='Pregunta 6', value='tab-6')
    ]),
    html.Div(id='content')
])

@app.callback(Output('content', 'children'), [Input('tabs', 'value')])
def render_content(tab):
    if tab == 'tab-1':
        return html.Div([
            html.H3('Pregunta 1: Ingresos de Universitarios vs No Universitarios'),
            dcc.Graph(
                id='grafica1',
                figure=go.Figure(
                    data=[
                        go.Scatter(
                            x=R_uni.index,  
                            y=R_uni['ingreso_tot'],  
                            mode='lines',  
                            name='Ingresos de Universitarios'  
                        ),
                        go.Scatter(
                            x=R_no_uni.index, 
                            y=R_no_uni['ingreso_tot'], 
                            mode='lines',  
                            name='Ingresos de No Universitarios'  
                        )
                    ],
                    layout=go.Layout(
                        title='Ingresos Laborales',
                        xaxis_title='Índice',
                        yaxis_title='Ingresos Laborales',
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(family="Arial", size=14),
                        title_font=dict(size=20),
                        title_x=0.5
                    )
                )
            ),
            html.P('Conclusión:Los ingresos de los no universitarios (rojo) son mucho más altos y presentan una mayor variabilidad en comparación con los ingresos de los universitarios (azul), los ingresos de los no universitarios muestran una alta variabilidad con algunos picos significativos que alcanzan ingresos muy altos, sin embargo la mayoría de los datos se agrupan en rangos bajos de ingresos, hay varios picos en los ingresos de los no universitarios, destacando uno muy alto cerca del índice 10k lo que podría indicar casos excepcionales.')
        ])
    elif tab == 'tab-2':
        return html.Div([
            html.H3('Pregunta 2: Situación laboral y salarios según convivencia con los padres'),
            dcc.Graph(
                id='grafica1',
                figure=px.bar(df2_1, x='padres', y='avg_ingreso_tot', title='¿Cómo se compara la situación laboral de la gente que vive con sus padres versus quienes no?').update_layout(
                    xaxis_title='¿vive con padres?',
                    yaxis_title='Ingresos persona'
                )
            ),
            dcc.Graph(
                id='grafica2',
                figure=px.bar(df2_2, x='padres', y='estado_ocup', title='Situación laboral').update_layout(
                    xaxis_title='¿vive con padres?',
                    yaxis_title='Situación laboral'
                )
            ),
            dcc.Graph(
                id='grafica3_no_padres',
                figure=px.bar(df2_3, x='estado_ocup', y='count_estado_ocup', title='Distribución situación laboral - No vive con padres').update_layout(
                    xaxis_title='Situación laboral',
                    yaxis_title='Cantidad'
                )
            ),
            dcc.Graph(
                id='grafica3_con_padres',
                figure=px.bar(df2_4, x='estado_ocup', y='count_estado_ocup', title='Distribución situación laboral - Vive con padres').update_layout(
                    xaxis_title='Situación laboral',
                    yaxis_title='Cantidad'
                )
            )
        ])
    elif tab == 'tab-3':
        return html.Div([
            html.H3('Pregunta 3: Salarios de Mujeres Jefas de Familia'),
            dcc.Graph(
                id='salary-graph',
                figure=px.scatter(df3, x='id_miembro', y='ingreso_tot', title='Salarios de Mujeres Jefas de Familia',
                                  labels={'id_miembro': 'ID del Miembro', 'ingreso_tot': 'Salarios'},
                                  trendline='ols',  
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
            html.P('Conclusión: El salario mínimo en Argentina en 2019 fue de 14,125 pesos argentinos. Según los datos de nuestra encuesta, el 73.9% de las mujeres jefas de familia ganan por encima de este salario. Sin embargo, aunque la mayoría supera el salario mínimo, los ingresos de estas mujeres no son significativamente altos, ya que los datos no presentan una gran dispersión. Se estima que para vivir bien en Argentina en 2019 se necesitarían alrededor de 50,000 pesos mensuales. Esto implica que aproximadamente la mitad de las mujeres jefas de familia encuestadas alcanzan este nivel de ingresos.')
        ])
    elif tab == 'tab-4':
        return html.Div([
            html.H3('Pregunta 4: Comparación de Ingresos Familiares y Salarios entre Universidad Privada y Pública'),
            dcc.Graph(
                id='grafica1',
                figure=px.bar(df4, x='sector_educativo', y='ingresos_familiares', title='¿Cómo se comparan los ingresos familiares y el salario entre universidad privada y pública?').update_layout(            
                    xaxis_title='Sector Educativo',
                    yaxis_title='Ingresos Familiares',
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family="Arial", size=14),
                    title_font=dict(size=20),
                    title_x=0.5
                ).update_traces(marker_color='#636EFA', marker_line_color='rgb(8,48,107)', marker_line_width=1.5)
            ),
            dcc.Graph(
                id='grafica2',
                figure=px.bar(df4, x='sector_educativo', y='salario', title='¿Cómo se comparan los ingresos familiares y el salario entre universidad privada y pública?').update_layout(            
                    xaxis_title='Sector Educativo',
                    yaxis_title='Salario',
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family="Arial", size=14),
                    title_font=dict(size=20
                    ),
                    title_x=0.5
                ).update_traces(marker_color='#EF553B', marker_line_color='rgb(8,48,107)', marker_line_width=1.5)
            ),
            html.P('Conclusión:1. El gráfico muestra los ingresos familiares según el sector educativo al que pertenece la universidad (privada religiosa, estatal/pública, privada no religiosa, y una categoría adicional de "no corresponde"). Las familias cuyos estudiantes asisten a universidades privadas no religiosas tienen los ingresos familiares más altos, cercanos a los 100k. Esto sugiere que las universidades privadas religiosas están asociadas con familias de mayores ingresos. Similar a las universidades privadas no religiosas, las universidades privadas religiosas también muestran altos ingresos familiares, aunque ligeramente menores que los del sector privado no religioso. Esto indica que, en general, las universidades privadas (religiosas y no religiosas) están relacionadas con familias de mayor capacidad económica. Las familias cuyos estudiantes asisten a universidades estatales o públicas tienen ingresos significativamente menores en comparación con las familias de las universidades privadas. Este grupo tiene ingresos familiares alrededor de los 50k, lo que sugiere que las universidades públicas están más accesibles a familias con menores ingresos. La categoría no corresponde, que posiblemente agrupe otros casos no especificados, muestra ingresos familiares en un rango intermedio, aunque más cercanos a los ingresos de las familias de las universidades públicas. Esto sugiere que este grupo podría incluir una variedad de situaciones económicas no directamente relacionadas con el tipo de universidad.'),
            html.P('2.Los que estudian en universidad privadas no religiosas son los que obtienen un mayor salario, comparado con los que estudiaron en universidad estatales/públicas y el de estas dos mencionadas es mucho mayor que el de las universidades privadas religiosas, aunque el salario de la categoría "no corresponde" muestra los salarios más altos. Este análisis sugiere que, a pesar de que las universidades privadas religiosas tienen ingresos familiares más altos, los egresados de estas instituciones no necesariamente obtienen los salarios más altos. En contraste, los egresados de universidades privadas no religiosas tienen salarios más altos, lo que podría reflejar una mejor preparación para el mercado laboral o una mayor demanda por sus habilidades. La categoría "no corresponde" muestra los salarios más altos, lo cual podría indicar que agrupa diversos casos con mejores oportunidades salariales.')
        ])
    elif tab == 'tab-5':
        return html.Div([
            html.H3('Pregunta 5: Salarios según Lugar de Nacimiento'),
            dcc.Graph(
                id='grafica3',
                figure=px.bar(df5, x='lugar_nacimiento', y='salario', title='¿Qué lugar de nacimiento (de los presentes en la encuesta) cuenta con los mayores salarios?').update_layout(            
                    xaxis_title='Lugar de Nacimiento',
                    yaxis_title='Salario',
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family="Arial", size=14),
                    title_font=dict(size=20),
                    title_x=0.5
                ).update_traces(marker_color='#00CC96', marker_line_color='rgb(8,48,107)', marker_line_width=1.5)
            ),
            html.P('Conclusión: La visualización muestra los lugares de nacimiento con los mayores salarios, destacando las diferencias geográficas en los ingresos.')
        ])
    elif tab == 'tab-6':
        return html.Div([
            html.H3('Pregunta 6: Salarios según Lugar de Nacimiento'),
            dcc.Graph(
                id = 'pregunta_6',
            figure=px.bar(df6, x='num_miembros', y='promedio_escolaridad', title='¿Las familias más grandes tienden a tener una mejor, igual o peor educación que las familias más pequeñas?').update_layout(            
            xaxis_title = 'Número de miembros de la familia',
            yaxis_title = 'Promedio de escolaridad')
            ),
            html.P('Conclusión:')
        ])
    else:
        return html.Div([
            html.H3('Selecciona una pregunta para ver los resultados correspondientes.')
        ])

if __name__ == '__main__':
    app.run_server(port=8085)

