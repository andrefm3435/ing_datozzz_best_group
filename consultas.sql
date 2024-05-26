-- Archivo con todas las consultas sql para responder a las preguntas del proyecto



-- ¿Cuáles son los ingresos de las personas las cuales han terminado sus estudios universitarios a comparación de aquellas personas que no la han completado?
SELECT ingreso_tot
FROM tipo_ingreso 
JOIN miembro ON tipo_ingreso.id2_miembro = miembro.id_miembro 
JOIN educacion ON miembro.id_miembro = educacion.id1_miembro 
WHERE educacion.nivel_actual = 'Universitario';

SELECT ingreso_tot
FROM tipo_ingreso 
JOIN miembro ON tipo_ingreso.id2_miembro = miembro.id_miembro 
JOIN educacion ON miembro.id_miembro = educacion.id1_miembro 
WHERE educacion.nivel_actual != 'Universitario';

-- ¿Cómo compara la situación laboral de la gente que vive con sus padres versus quienes no?


-- ¿En promedio cuantos ingresos de familias cuya cabeza de hogar sea mujer superan el salario mínimo en argentina durante el 2019?
SELECT mi.id_miembro, mi.parentesco, mi.sexo, ti.ingreso_tot
FROM miembro mi
JOIN Tipo_ingreso ti ON mi.id_miembro = ti.id2_miembro
WHERE mi.sexo = 'Mujer' AND mi.parentesco = 'Jefe';

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

-- ¿Como se comparan los ingresos familiares y el salario entre universidad privada y pública?


-- ¿Qué lugar de nacimiento (de los presentes en la encuesta) cuenta con los mayores salarios?


-- ¿Las familias más grandes tienden a tener una mejor, igual o peor educación que las familias más pequeñas?
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

-- ¿Las personas con ingresos familiares per cápita superiores a la media tienen salarios superiores a la media?

