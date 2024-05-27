import pandas as pd
import psycopg2 as psy2
import dash
from dash import dcc, html, Input, Output, callback
import plotly.express as px
import plotly.graph_objs as go

dbname = "datos_Argentina"
user = "javier"
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
-- Consulta dividiendo los ingresos familiares en 'superior a la media' e 'inferior a la media'
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

#Pregunta 7
sql_query7_1 = """
WITH ingreso_per_capita AS (
    SELECT 
        id_hogar,
        ingreso_fam,
        COUNT(*) AS num_miembros,
        (ingreso_fam / COUNT(*)) AS ingreso_per_capita
    FROM miembro m
    JOIN Tipo_ingreso t ON m.id_miembro = t.id2_miembro
    GROUP BY id_hogar, ingreso_fam
),
ingreso_per_capita_media AS (
    SELECT AVG(ingreso_per_capita) AS ingreso_per_capita_medio
    FROM ingreso_per_capita
),
salarios_comparacion AS (
    SELECT 
        m.id_miembro,
        t.ingreso_tot_lab,
        ipc.ingreso_per_capita,
        ipcm.ingreso_per_capita_medio,
        CASE 
            WHEN ipc.ingreso_per_capita > ipcm.ingreso_per_capita_medio THEN 'Superior'
            ELSE 'Inferior'
        END AS categoria_ingreso
    FROM miembro m
    JOIN Tipo_ingreso t ON m.id_miembro = t.id2_miembro
    JOIN ingreso_per_capita ipc ON m.id_hogar = ipc.id_hogar
    CROSS JOIN ingreso_per_capita_media ipcm
)
SELECT 
    categoria_ingreso,
    AVG(ingreso_tot_lab) AS promedio_salario
FROM salarios_comparacion
GROUP BY categoria_ingreso;
"""
sql_query7_2 = """
-- 'Consulta diviendo los ingresos familiares en cuartiles'
WITH ingreso_per_capita AS (
    SELECT 
        id_hogar,
        ingreso_fam,
        COUNT(*) AS num_miembros,
        (ingreso_fam / COUNT(*)) AS ingreso_per_capita
    FROM miembro m
    JOIN Tipo_ingreso t ON m.id_miembro = t.id2_miembro
    GROUP BY id_hogar, ingreso_fam
),
cuartiles AS (
    SELECT 
        ingreso_per_capita,
        NTILE(4) OVER (ORDER BY ingreso_per_capita) AS cuartil
    FROM ingreso_per_capita
),
salarios_comparacion AS (
    SELECT 
        m.id_miembro,
        t.ingreso_tot_lab,
        ipc.ingreso_per_capita,
        c.cuartil
    FROM miembro m
    JOIN Tipo_ingreso t ON m.id_miembro = t.id2_miembro
    JOIN ingreso_per_capita ipc ON m.id_hogar = ipc.id_hogar
    JOIN cuartiles c ON ipc.ingreso_per_capita = c.ingreso_per_capita
)
SELECT 
    cuartil,
    AVG(ingreso_tot_lab) AS promedio_salario
FROM salarios_comparacion
GROUP BY cuartil
ORDER BY cuartil;

"""
df7_1 =pd.read_sql(sql_query7_1, conn)
df7_2 =pd.read_sql(sql_query7_2, conn)



app = dash.Dash(__name__)

# Layout con botones de navegación y contenido dinámico
app.layout = html.Div([

    html.H1('Un análisis basado en datos de los salarios y la economía doméstica en Argentina en 2019', style={'text-align': 'center'}),
    dcc.Tabs(id='tabs', value='tab-1', children=[
        dcc.Tab(label='Información', value='info'),
        dcc.Tab(label='Pregunta 1', value='tab-1'),
        dcc.Tab(label='Pregunta 2', value='tab-2'),
        dcc.Tab(label='Pregunta 3', value='tab-3'),
        dcc.Tab(label='Pregunta 4', value='tab-4'),
        dcc.Tab(label='Pregunta 5', value='tab-5'),
        dcc.Tab(label='Pregunta 6', value='tab-6'),
        dcc.Tab(label='Pregunta 7', value='tab-7')
    ]),
    html.Div(id='content')
])

@app.callback(Output('content', 'children'), [Input('tabs', 'value')])
def render_content(tab):
    if tab == 'info':
        return html.Div([
            html.P("Se dispone de un conjunto de datos que contiene información demográfica y socioeconómica de Argentina en el 2019, sujeta a ciertas restricciones y reglas. El objetivo es realizar un análisis detallado de estos datos para responder a una serie de preguntas relacionadas con los ingresos, la educación, el estado conyugal, la situación laboral y otros aspectos relevantes de la población. El enfoque principal está orientado a entender los distintos factores que influyen en la obtención de salarios elevados, identificando así las variables determinantes en el panorama socioeconómico del país.", 
                   style={'fontSize': '25px'}
                   ),
            html.Div(html.P(['William Cabrera', html.Br(), 'Paola Cortés', html.Br(), 'Andrés Miranda Mendoza', html.Br(), 'Sofía Torres', html.Br(), 'Simón Vélez Castillo'], style={'fontSize': '25px'})),
            html.P("Universidad del Rosario 2024-I", style={'fontSize': '25px'})
        ])
    elif tab == 'tab-1':
        return html.Div([
            html.H3('Pregunta 1: Ingresos de Universitarios vs No Universitarios', style={'fontSize': '30px', 'fontWeight': 'bold'}),
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
            html.H4('Conclusión:', style={'fontSize': '30px', 'fontWeight': 'bold'}),
            html.P('Los ingresos de los no universitarios (rojo) son mucho más altos y presentan una mayor variabilidad en comparación con los ingresos de los universitarios (azul), los ingresos de los no universitarios muestran una alta variabilidad con algunos picos significativos que alcanzan ingresos muy altos, sin embargo la mayoría de los datos se agrupan en rangos bajos de ingresos, hay varios picos en los ingresos de los no universitarios, destacando uno muy alto cerca del índice 10k lo que podría indicar casos excepcionales.',
                   style={'fontSize': '25px'}
                   )
        ])
    elif tab == 'tab-2':
        return html.Div([
            html.H3('Pregunta 2: Situación laboral y salarios según convivencia con los padres', style={'fontSize': '30px', 'fontWeight': 'bold'}),
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
            ),
            html.H4('Conclusión:', style={'fontSize': '30px', 'fontWeight': 'bold'}),
            html.P('Tras revisar los datos presentes en la base del censo para comparar tanto los ingresos como la situación laboral de las personas que viven en un mismo hogar con sus padres con respecto a las personas que no viven con sus padres en casa; desde el primer momento se nota una clara y abismal diferencia entre ambos grupos, tanto en el estado laboral como en el promedio de los ingresos de cada uno,dando en ambos casos a entender que es el grupo de aquellos que no viven con sus padres los que trabajan, y por ende los que obtienen más ingresos en promedio,dando a entender que no es tan grande la cantidad de hogares donde sea necesario que los hijos comiencen a trabajar por dificultades del hogar, sino que pueden  disfrutar de su rol de hijos, mientras llegan a la adultez, para posteriormente hacerse cargo de si mismos.',
                   style={'fontSize': '25px'}
                   )
        ])
    elif tab == 'tab-3':
        return html.Div([
            html.H3('Pregunta 3: Salarios de Mujeres Jefas de Familia', style={'fontSize': '30px', 'fontWeight': 'bold'}),
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
            html.H4('Conclusión:', style={'fontSize': '30px', 'fontWeight': 'bold'}),
            html.P('El salario mínimo en Argentina en 2019 fue de 14,125 pesos argentinos. Según los datos de nuestra encuesta, el 73.9% de las mujeres jefas de familia ganan por encima de este salario. Sin embargo, aunque la mayoría supera el salario mínimo, los ingresos de estas mujeres no son significativamente altos, ya que los datos no presentan una gran dispersión. Se estima que para vivir bien en Argentina en 2019 se necesitarían alrededor de 50,000 pesos mensuales. Esto implica que aproximadamente la mitad de las mujeres jefas de familia encuestadas alcanzan este nivel de ingresos.',
                   style={'fontSize': '25px'}
                   )
        ])
    elif tab == 'tab-4':
        return html.Div([
            html.H3('Pregunta 4: Comparación de Ingresos Familiares y Salarios entre Universidad Privada y Pública', style={'fontSize': '30px', 'fontWeight': 'bold'}),
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
            html.H4('Conclusión:', style={'fontSize': '30px', 'fontWeight': 'bold'}),
            html.P('1. El gráfico muestra los ingresos familiares según el sector educativo al que pertenece la universidad (privada religiosa, estatal/pública, privada no religiosa, y una categoría adicional de "no corresponde"). Las familias cuyos estudiantes asisten a universidades privadas no religiosas tienen los ingresos familiares más altos, cercanos a los 100k. Esto sugiere que las universidades privadas religiosas están asociadas con familias de mayores ingresos. Similar a las universidades privadas no religiosas, las universidades privadas religiosas también muestran altos ingresos familiares, aunque ligeramente menores que los del sector privado no religioso. Esto indica que, en general, las universidades privadas (religiosas y no religiosas) están relacionadas con familias de mayor capacidad económica. Las familias cuyos estudiantes asisten a universidades estatales o públicas tienen ingresos significativamente menores en comparación con las familias de las universidades privadas. Este grupo tiene ingresos familiares alrededor de los 50k, lo que sugiere que las universidades públicas están más accesibles a familias con menores ingresos. La categoría no corresponde, que posiblemente agrupe otros casos no especificados, muestra ingresos familiares en un rango intermedio, aunque más cercanos a los ingresos de las familias de las universidades públicas. Esto sugiere que este grupo podría incluir una variedad de situaciones económicas no directamente relacionadas con el tipo de universidad.',
                   style={'fontSize': '25px'}
                   ),
            html.P('2.Los que estudian en universidad privadas no religiosas son los que obtienen un mayor salario, comparado con los que estudiaron en universidad estatales/públicas y el de estas dos mencionadas es mucho mayor que el de las universidades privadas religiosas, aunque el salario de la categoría "no corresponde" muestra los salarios más altos. Este análisis sugiere que, a pesar de que las universidades privadas religiosas tienen ingresos familiares más altos, los egresados de estas instituciones no necesariamente obtienen los salarios más altos. En contraste, los egresados de universidades privadas no religiosas tienen salarios más altos, lo que podría reflejar una mejor preparación para el mercado laboral o una mayor demanda por sus habilidades. La categoría "no corresponde" muestra los salarios más altos, lo cual podría indicar que agrupa diversos casos con mejores oportunidades salariales.',
                   style={'fontSize': '25px'}
                   )
        ])
    elif tab == 'tab-5':
        return html.Div([
            html.H3('Pregunta 5: Salarios según Lugar de Nacimiento', style={'fontSize': '30px', 'fontWeight': 'bold'}),
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
            html.H4('Conclusión:', style={'fontSize': '30px', 'fontWeight': 'bold'}),
            html.P('Aquellas personas que ganan menos son las que se encuentran en las afueras del país. Esto lo notamos gracias a que los países limítrofes y no limítrofes son los que menos ganan. De igual forma, Caba tampoco tiene un salario muy alto, siendo esta la zona central de Buenos Aires. Otras provincias tienen ganancias intermedias. Luego, podemos notar que las personas que tienen el salario promedio más alto son las que viven en la provincia de Buenos Aires. Entonces, aquellas personas que son de PBA, sin especificar, son las que ganan más, seguidas por las personas que viven en PBA, excepto GBA. Luego, en tercer lugar, vienen las personas que nacieron en GBA. Entonces, aquellas personas que ganan más son las que nacieron en las zonas que rodean la parte central de Buenos Aires.',
                   style={'fontSize': '25px'})
        ])
    elif tab == 'tab-6':
        return html.Div([
            html.H3('Pregunta 6: Salarios según Lugar de Nacimiento', style={'fontSize': '30px', 'fontWeight': 'bold'}),
            dcc.Graph(
                id = 'pregunta_6',
            figure=px.bar(df6, x='num_miembros', y='promedio_escolaridad', title='¿Las familias más grandes tienden a tener una mejor, igual o peor educación que las familias más pequeñas?').update_layout(            
            xaxis_title = 'Número de miembros de la familia',
            yaxis_title = 'Promedio de escolaridad')
            ),
            html.H4('Conclusión:', style={'fontSize': '30px', 'fontWeight': 'bold'}),
            html.P('El gráfico muestra una clara tendencia, donde la escolaridad promedio disminuye conforme aumenta el tamaño de las familias. Esto tiene sentido, considerando los altos costos de la educación superior, además de la presión en las familias más grandes de entrar a una edad más temprana al mundo laboral, perdiendo oportunidades importantes de empleo. Hay que tener en cuenta que pocas familias tienen un número enorme de miembros, entonces datos como la familia de 19 integrantes no deberían ser tenidos en cuenta en el análisis. A pesar de esto, se muestra una tendencia clara.',
                   style={'fontSize': '25px'}
                   )
        ])
    elif tab == 'tab-7':
        return html.Div([
            html.H3('Pregunta 7: ¿Las personas con ingresos familiares per cápita superiores a la media tienen salarios superiores a la media?', style={'fontSize': '30px', 'fontWeight': 'bold'}),
            dcc.Graph(
                id='pregunta_7_1',
                figure=px.bar(df7_1, x='categoria_ingreso', y='promedio_salario', title='Salario según los ingresos familiares (Ingresos familiares divididos en "superior" e "inferior" a la media)').update_layout(
                    xaxis_title='Categoría de ingresos familiares (superior e inferior a la media)',
                    yaxis_title='Promedio del salario'
                )
            ),
            dcc.Graph(
                id='pregunta_7_2',
                figure=px.bar(df7_2, x='cuartil', y='promedio_salario', title='Salario según los ingresos familiares (Ingresos familiares divididos en cuartiles)').update_layout(
                    xaxis_title='Cuartiles',
                    yaxis_title='Promedio del salario'
                )
            ),  
            html.H4('Conclusión:', style={'fontSize': '30px', 'fontWeight': 'bold'}),
            html.P('Hay una clara correlación entre los ingresos familiares y el salario. Aunque puede haber algunas excepciones, que una familia tenga altos ingresos hace fácil predecir que esto se traducirá en futuros altos salarios, ya sea por una mejor educación, mayores contactos o presión familiar a tener y mantener mejores empleos.',
                   style={'fontSize': '25px'}
                   )
        ])
    
    else:
        return html.Div([
            html.H3('Selecciona una pregunta para ver los resultados correspondientes.',
                    style={'fontSize': '25px'}
                    )
        ])

if __name__ == '__main__':
    app.run_server(port=8085)

