# Contexto del proyecto (extraído de 01_alcance)

Generado: 2026-10-31T07:20:05 · Hash del alcance: `45cad2dc5277f49a`

Archivo generado automáticamente. No editar: se regenera en cada /practicaspre.

---

## Archivo: `01_alcance/examen parcial word.docx`

UNIVERSIDAD NACIONAL MAYOR DE SAN MARCOS

FACULTAD DE INGENIERIA DE SISTEMAS

EXAMEN PARCIAL

PARTE I:

Planteamiento del Problema

Descripción del problema

Formulación del Problema (Problema General Problemas Específicos)

Antecedentes (a nivel global y local)

Justificación de la investigación

Limitaciones de la investigación

Objetivos (Objetivo general Objetivos específicos)

Hipótesis

Tipo de investigación

Ejemplo aplicado (a tu proyecto de detección de estrés en plantas):

Tipo de investigación:

Este proyecto se enmarca dentro de una investigación aplicada, ya que busca ofrecer una solución tecnológica para el diagnóstico del estrés en plantas mediante inteligencia artificial. El enfoque es cuantitativo, pues se trabajará con datos visuales y métricas extraídas mediante redes neuronales convolucionales (CNN). El diseño es no experimental y transversal, ya que no se manipularán las variables y el análisis se realizará en un solo punto del tiempo.

Población y muestra

Ejemplo:

Qué planta estás usando

Cuántas observaciones tienes (o imágenes)

En qué lugar se realizó el muestreo

Instrumentos

Ejemplo:

Cámara digital o dron para capturar imágenes de las plantas.

Software de procesamiento de imágenes (por ejemplo, Python con OpenCV).

Red neuronal convolucional (CNN) implementada en PyTorch.

Computadora o servidor con capacidad de procesamiento gráfico.

Finalmente se presenta el diseño del modelo o arquitectura (si estás aplicando o desarrollando un modelo de aprendizaje automático (ML) o deep learning; si quieres demostrar cómo funciona tu sistema internamente o si es necesario explicar la lógica de la solución y su implementación).



---

## Archivo: `01_alcance/incidencias_seguridad_sjm_20260610.xlsx`

**Hoja `incidencias_seguridad_sjm_20260`** — 2 592 filas × 22 columnas

| Columna | Tipo | Nulos | Únicos | Ejemplo |
|---|---|---|---|---|
| FECHA_CORTE | int64 | 0 | 1 | 20260610 |
| UBIGEO | int64 | 0 | 1 | 150141 |
| ID_INCIDENCIA | object | 0 | 2591 | 9b52d6ed |
| FECHA_REGISTRO | int64 | 0 | 26 | 20260516 |
| HORA_REGISTRO | object | 0 | 1128 | 08:43:00 |
| TURNO | object | 0 | 3 | Mañana |
| TIPO | object | 0 | 7 | EMISION DE ALERTAS TEMPRANAS EN APOYO A LA PNP EN  PRESUNTAS |
| SUBTIPO | object | 0 | 23 | PRESUNTA ACTIV. CONTRA LAS BUENAS COSTUMBRES |
| MODALIDAD | object | 0 | 79 | PRESUNTO CONSUMO DE ALCOHOL O DROGAS PERTURBANDO LA TRANQUIL |
| ZONA | object | 312 | 6 | SAN JUAN |
| SECTOR | object | 543 | 4 | SECTOR III |
| DIRECCION | object | 0 | 1469 | Jesús Morales 221, San Juan de Miraflores 15801, Perú |
| LATITUD | float64 | 0 | 1820 | -12.169979 |
| LONGITUD | float64 | 0 | 1804 | -76.973507 |
| FUENTE | object | 0 | 7 | WHATSAPP |
| TIPO_REPORTANTE | object | 0 | 7 | CONTRIBUYENTE |
| NIVEL | object | 1687 | 3 | Relevante |
| ESTADO_FINAL | object | 0 | 3 | No atendida |
| FECHA_CIERRE | int64 | 0 | 25 | 20260517 |
| HORA_CIERRE | object | 0 | 1042 | 08:51:00 |
| TIEMPO_RESPUESTA_MIN | int64 | 0 | 460 | 1448 |
| AMBIENTAL | object | 0 | 1 | NO |

Rango `FECHA_CORTE`: 20260610 → 20260610

Rango `FECHA_REGISTRO`: 20260516 → 20260610

Rango `FECHA_CIERRE`: 20260517 → 20260610

**Hoja `Calc_Dashboard`** — 34 filas × 12 columnas

| Columna | Tipo | Nulos | Únicos | Ejemplo |
|---|---|---|---|---|
| Fecha | object | 2 | 32 | 05-16 |
| Incidencias | object | 2 | 29 | 4 |
| Unnamed: 2 | float64 | 34 | 0 |  |
| Zona | object | 28 | 6 | SAN JUAN |
| Incidencias.1 | float64 | 28 | 6 | 1060.0 |
| Unnamed: 5 | float64 | 34 | 0 |  |
| Turno | object | 31 | 3 | Mañana |
| Incidencias.2 | float64 | 31 | 3 | 1222.0 |
| Unnamed: 8 | float64 | 34 | 0 |  |
| Métrica | object | 29 | 5 | Total Incidencias |
| Valor | object | 29 | 5 | 2592 |
| Detalle | object | 29 | 5 | Registros totales |

Rango `Fecha`: 05-16 → PRESUNTO CONSUMO DE ALCOHOL O DROGAS PERTURBANDO LA TRANQUILIDAD O SEGURIDAD DE LAS PERSONAS O SUMINISTRARLO A MENORES DE EDAD

**Hoja `Dashboard`** — 32 filas × 11 columnas

| Columna | Tipo | Nulos | Únicos | Ejemplo |
|---|---|---|---|---|
| Unnamed: 0 | float64 | 32 | 0 |  |
| Unnamed: 1 | object | 18 | 14 | PANEL DE CONTROL DE SEGURIDAD CIUDADANA — SAN JUAN DE MIRAFL |
| Unnamed: 2 | float64 | 32 | 0 |  |
| Unnamed: 3 | float64 | 32 | 0 |  |
| Unnamed: 4 | object | 29 | 3 | TASA DE ATENCIÓN |
| Unnamed: 5 | object | 25 | 7 | Total |
| Unnamed: 6 | object | 25 | 7 | % Part. |
| Unnamed: 7 | object | 29 | 3 | TIEMPO PROM. RESPUESTA |
| Unnamed: 8 | float64 | 32 | 0 |  |
| Unnamed: 9 | float64 | 32 | 0 |  |
| Unnamed: 10 | object | 29 | 3 | TURNO MAYOR DEMANDA |


---

## Archivo: `01_alcance/Parte_I_Proyecto_SJM.docx`

Universidad Nacional Mayor de San Marcos

Facultad de Ingeniería de Sistemas e Informática

Sistema web basado en aprendizaje automático para la predicción espaciotemporal de puntos críticos y priorización de recursos de patrullaje para el apoyo a la gestión de seguridad ciudadana en San Juan de Miraflores, Lima

PARTE I

Planteamiento y diseño metodológico de la investigación

Curso: [completar]

Docente: [completar]

Integrantes: [completar]

Lima, 2026

## 1. Planteamiento del problema

La inseguridad ciudadana es un problema persistente en Lima Metropolitana, y los delitos contra el patrimonio, como el hurto y el robo, se cuentan entre los más extendidos (Zevallos Trigoso et al., s. f.; Escobedo Neyra y Tapia Aquino, 2024). San Juan de Miraflores ha sido mencionado por la prensa entre los distritos de la capital donde se concentran denuncias por hurto y robo (OJO, 2022). En este contexto, la Ley N.° 27933 organiza el Sistema Nacional de Seguridad Ciudadana y asigna un rol a los comités distritales y a las municipalidades en la gestión local de la seguridad (Congreso de la República del Perú, 2003).

La Municipalidad Distrital de San Juan de Miraflores, mediante su Centro de Control de Operaciones (CCO), registra las incidencias de seguridad ciudadana, serenazgo y emergencias que atiende y las publica como dato abierto, con fecha, hora, turno, tipo, sector y coordenadas (Municipalidad Distrital de San Juan de Miraflores [MDSJM], 2026). Esa información puede orientar dónde y cuándo conviene reforzar la presencia preventiva. Sin embargo, tal como se publica, es una tabla de eventos individuales: no existe un instrumento que la convierta en estimaciones de nivel de incidencias por zona y turno ni en un orden de prioridad explícito y revisable. En la revisión de fuentes realizada para este trabajo no se encontró un sistema público de ese tipo para el distrito.

Frente a ello se plantea un prototipo web que use aprendizaje automático sobre el historial georreferenciado del CCO para estimar un nivel de incidencias por microzona y turno, y que ordene los puntos de mayor prioridad para apoyar la decisión de un operador. El sistema no pretende predecir dónde ocurrirá un delito concreto ni sustituir el criterio de la autoridad.

## 2. Descripción del problema

### 2.1 Situación de los datos

El extracto del CCO disponible para este trabajo contiene 2 592 registros entre el 16 de mayo y el 10 de junio de 2026 (26 días; fecha de corte: 10 de junio de 2026). Todos los registros tienen latitud y longitud, y se distribuyen en tres turnos (mañana, tarde y noche) y en cuatro sectores del distrito. En promedio se registran cerca de 100 incidencias por día.

La mayor parte de los registros no corresponde a delitos. Predominan las alertas por presuntas infracciones (52,2 %) y por presuntas faltas (24,0 %), y solo 53 registros (2,0 %) se clasifican como actividades presuntamente delictivas. Por esta razón el objeto de estudio se define como incidencias de seguridad ciudadana y no como riesgo delictivo en sentido estricto, decisión que debe mantenerse en todo el documento y en las etiquetas del modelo.

Como fuente complementaria se identificó el conjunto de denuncias policiales del SIDPOL (Ministerio del Interior, 2026), que reúne conteos por año, mes, distrito y modalidad desde enero de 2018 hasta julio de 2026. Al no incluir ubicación fina ni turno, no permite construir microzonas; se usará únicamente como contexto histórico del distrito.

### 2.2 Brechas identificadas

Brecha de uso: los registros del CCO se publican como eventos aislados, sin una síntesis espacial ni temporal que apoye decisiones de patrullaje.

Brecha de priorización: no hay un criterio explícito y reproducible para ordenar los puntos que merecen atención en un turno determinado.

Brecha de visualización: los datos abiertos no vienen acompañados de un mapa, un ranking ni un tablero que un operador pueda consultar sin procesar archivos.

Brecha de evidencia: el volumen de datos disponible es reducido y cubre pocas semanas, por lo que cualquier modelo debe evaluarse con cautela y de forma temporal, no aleatoria.

## 3. Formulación del problema

### 3.1 Problema general

¿En qué medida un sistema web basado en modelos de aprendizaje automático, entrenado con incidencias georreferenciadas del CCO de San Juan de Miraflores, puede estimar el nivel de incidencias por microzona y turno y ordenar puntos críticos para apoyar la priorización de recursos de patrullaje?

### 3.2 Problemas específicos

¿Qué calidad y cobertura tienen los datos del CCO y del SIDPOL, y qué tratamiento requieren para un análisis espaciotemporal?

¿Qué tamaño de microzona y qué variables históricas son adecuados dado el volumen y la cobertura temporal disponibles?

¿Cuál de los modelos comparados (regresión logística, Random Forest y Gradient Boosting) obtiene mejor Macro F1 en una validación temporal, frente a una línea base simple?

¿Cómo combinar el nivel estimado, la gravedad histórica y la frecuencia reciente en un ranking de prioridad explicable?

¿Cómo presentar los resultados en una aplicación web (mapa, ranking, ficha de detalle y tablero) que un operador pueda consultar con facilidad?

## 4. Antecedentes

### 4.1 Antecedentes a nivel global

Mapeo de hotspots como predicción. Chainey et al. (2008) usaron datos de un periodo pasado para generar mapas de concentración con cuatro técnicas (áreas censales, elipses espaciales, grillas y estimación de densidad por kernel) y comprobaron qué tan bien anticipaban dónde ocurrirían los delitos después. La densidad por kernel fue la técnica más precisa de forma consistente, y los delitos callejeros fueron los mejor anticipados. Este trabajo respalda el principio de usar el historial para anticipar patrones espaciales y de evaluar sobre un periodo posterior.

Pronóstico y patrullaje dinámico. Mohler et al. (2015) realizaron dos ensayos controlados aleatorizados en el Departamento de Policía de Los Ángeles y en la policía de Kent (Reino Unido). Los pronósticos del modelo ETAS anticiparon entre 1,4 y 2,2 veces más delitos que un analista con las prácticas habituales, y el patrullaje guiado por esos pronósticos se asoció con una reducción promedio de 7,4 % del volumen delictivo en función del tiempo de patrulla, mientras que el guiado por analistas no mostró efecto significativo. La experiencia documenta que predecir áreas pequeñas por turno es una práctica viable; este proyecto no replica ese tipo de ensayo ni afirma resultados similares.

Marco y límites de la predicción policial. Perry et al. (2013), en una guía de RAND para agencias de seguridad, definen la predicción policial como el uso de técnicas analíticas para identificar objetivos de intervención, advierten que estas herramientas no sustituyen los enfoques integrales y no son una bola de cristal, y revisan mitos y errores frecuentes. Aportan el marco conceptual y la justificación de que el sistema solo apoye, y no reemplace, la decisión humana.

Aprendizaje automático en microlugares. Wheeler y Steenbeek (2021) emplearon Random Forest para pronosticar robos en Dallas sobre celdas pequeñas y encontraron que superaba a los modelos de terreno de riesgo y a la densidad por kernel, pero solo ligeramente a un modelo basado en el conteo previo de delitos. De ahí que este proyecto incluya una línea base de persistencia y reporte si la complejidad adicional de los modelos aporta una mejora real.

### 4.2 Antecedentes a nivel local

Predicción de delitos patrimoniales en Lima. Escobedo Neyra y Tapia Aquino (2024), en una tesis de Ingeniería de Sistemas de la Universidad de Lima, compararon modelos de regresión (Extra Trees, XGBoost, Bagging, AdaBoost, máquinas de vectores de soporte y Random Forest) con optimización de hiperparámetros para predecir delitos contra la propiedad en zonas de alto riesgo de Lima; el mejor resultado correspondió a Extra Trees, con un coeficiente de determinación de 0,79. Las autoras señalan además la escasez de estudios que predigan estos delitos en la ciudad. A diferencia de ese trabajo, el presente proyecto parte de datos municipales del CCO de un solo distrito, plantea una clasificación en niveles por microzona y turno, y añade priorización y una aplicación web.

Limitaciones del registro policial. Zevallos Trigoso et al. (s. f.) realizaron mapas participativos de hurto y robo en la jurisdicción de la comisaría de Canto Rey, en San Juan de Lurigancho, partiendo de que los mapas del delito basados en denuncias policiales están limitados por las condiciones operativas y metodológicas del registro. Este antecedente sustenta la prudencia con la que deben interpretarse los datos de registro y la decisión de no presentar los resultados como una medición del delito real.

### 4.3 Síntesis

En la búsqueda realizada no se identificó un antecedente que combine datos de un CCO municipal, microzonas, evaluación temporal y priorización con interfaz web para San Juan de Miraflores. Esto no demuestra que no exista: la revisión fue acotada y debería ampliarse con bases académicas antes de la versión final.

## 5. Justificación de la investigación

Justificación práctica. El operador de seguridad ciudadana necesita decidir en qué zonas y turnos reforzar la presencia preventiva con recursos limitados. Un mapa de niveles estimados y un ranking explicable ofrecen un apoyo ordenado a esa decisión, que sigue siendo humana.

Justificación social. Orientar mejor los recursos de patrullaje puede contribuir, a largo plazo, a una gestión más eficiente de la seguridad ciudadana. El prototipo no pretende demostrar una reducción de la delincuencia, sino preparar información útil para decidir.

Justificación técnica. Los datos del CCO son abiertos y están georreferenciados, y el problema puede resolverse con modelos clásicos de aprendizaje automático sobre datos tabulares, sin hardware especializado, lo que lo hace reproducible en un equipo de cómputo convencional.

Justificación académica y metodológica. El trabajo aplica un flujo completo de ciencia de datos (limpieza, asignación espacial, construcción de variables sin fuga de información, validación temporal, comparación con una línea base y presentación de resultados) a un problema real de gestión pública local.

## 6. Limitaciones de la investigación

Cobertura temporal reducida. El extracto cubre solo 26 días (16 de mayo a 10 de junio de 2026). No es posible observar estacionalidad mensual o anual, y la partición temporal en entrenamiento, validación y prueba dispone de pocos días. Los resultados deben considerarse exploratorios.

Posible cambio de cobertura entre meses. El promedio diario es de unos 84 registros en la parte de mayo incluida (16 días) y de unos 125 en junio (10 días). La diferencia debe revisarse porque podría reflejar un cambio en el registro y no un cambio real en las incidencias.

Naturaleza del registro. Los datos son incidencias atendidas por el CCO, no delitos. Solo el 2,0 % se clasifica como actividad presuntamente delictiva. Además, lo que se registra depende de dónde hay patrullaje y cámaras, lo que puede sesgar la distribución espacial.

Calidad de campos. El 20,9 % de los registros (543) no tiene sector asignado, por lo que el sector se usará solo como referencia y la ubicación se tomará de las coordenadas. El código de ubigeo del CCO (150141) no coincide con el que el SIDPOL usa para San Juan de Miraflores (150133), aunque las direcciones y coordenadas corresponden al distrito; se tratará como una inconsistencia de codificación y se validará la ubicación contra el límite distrital.

Variables posteriores al evento. Campos como el estado final, la fecha de cierre y el tiempo de respuesta se conocen después de la incidencia y no se usarán como predictores. En algunos registros revisados aparecen incidencias "no atendidas" con tiempos cercanos a 24 horas, lo que sugiere un cierre automático.

Fuente complementaria limitada. El SIDPOL solo aporta conteos mensuales por distrito y modalidad, sin ubicación ni turno, por lo que no entra al entrenamiento espacial.

Sin datos de exposición. No se dispone de población, flujo de personas ni superficie por microzona, de modo que los conteos no son tasas y las comparaciones entre zonas deben leerse con cuidado.

Recursos de patrullaje ilustrativos. La disponibilidad de camionetas, motocicletas y otros recursos se ingresa de forma manual como ejemplo; no proviene de datos reales de la municipalidad y el módulo de recursos pertenece a un segundo nivel de desarrollo.

Alcance del sistema. El prototipo no predice delitos individuales ni garantiza que una zona sea segura o insegura, no calcula rutas, no hace seguimiento en tiempo real, no evalúa impacto sobre la delincuencia y se ejecuta de forma local, sin despliegue en producción.

Riesgo de estigmatización. Mostrar zonas con nivel alto puede dar una imagen negativa de un sector. Los resultados deben presentarse como apoyo a la decisión y con la aclaración de que reflejan registros, no una condición permanente del lugar.

## 7. Objetivos

### 7.1 Objetivo general

Desarrollar un prototipo web basado en aprendizaje automático que estime niveles de incidencias de seguridad ciudadana por microzona y turno en San Juan de Miraflores a partir de datos georreferenciados del CCO, y que genere un ranking de puntos críticos para apoyar la priorización de recursos de patrullaje.

### 7.2 Objetivos específicos

Recopilar, depurar y validar los datos del CCO, usando el SIDPOL como contexto, y documentar su calidad y cobertura.

Definir las microzonas y construir observaciones por microzona, fecha y turno, con variables históricas que no incorporen información posterior al periodo que se estima.

Entrenar y comparar regresión logística, Random Forest y Gradient Boosting mediante validación temporal, usando Macro F1 como métrica principal y una línea base de persistencia como referencia.

Implementar un mecanismo de priorización explicable que combine el nivel estimado, la gravedad histórica y la frecuencia reciente, con pesos ajustables y justificados.

Desarrollar una aplicación web local con mapa de microzonas, ranking, ficha de detalle y tablero analítico.

Como segundo nivel, registrar disponibilidad de recursos y permitir su asignación manual sin superar las cantidades declaradas.

## 8. Hipótesis

Dado el periodo corto de datos, las hipótesis se contrastarán de forma descriptiva y exploratoria; no se busca generalización estadística.

### 8.1 Hipótesis general

H1: En el periodo de prueba reservado, al menos un modelo de ensamble (Random Forest o Gradient Boosting) obtiene un Macro F1 mayor que el de la regresión logística y que el de la línea base de persistencia, que repite el nivel del periodo anterior.

H0: Ningún modelo de ensamble supera a la regresión logística ni a la línea base de persistencia en Macro F1 sobre el periodo de prueba.

### 8.2 Hipótesis específicas

HE1: Las variables de historial reciente (conteos previos y promedios móviles) tienen mayor importancia en el modelo que las variables de calendario (día de la semana y turno).

HE2: Las incidencias registradas por el CCO se concentran espacialmente: una fracción reducida de las microzonas acumula la mayor parte de los registros.

## 9. Tipo de investigación

El proyecto se enmarca en una investigación aplicada, porque busca ofrecer una solución tecnológica concreta, un prototipo web con modelos de aprendizaje automático, a un problema de gestión de la seguridad ciudadana. El enfoque es cuantitativo, ya que se trabaja con conteos, variables numéricas y métricas de desempeño de modelos.

El diseño es no experimental, pues no se manipulan las variables ni se interviene en el patrullaje, y longitudinal retrospectivo, porque se analiza una serie histórica de incidencias registradas en 26 días consecutivos y se evalúa el modelo sobre los días finales del periodo. El alcance es descriptivo y predictivo: primero se describe la distribución espacial y temporal de las incidencias y luego se estima su nivel por microzona y turno.

## 10. Población y muestra

### 10.1 Población

La población está formada por todas las incidencias de seguridad ciudadana, serenazgo y emergencias atendidas por el Centro de Control de Operaciones de la Municipalidad Distrital de San Juan de Miraflores. Como referencia contextual se considera también el conjunto de denuncias policiales del SIDPOL registradas en el distrito.

### 10.2 Muestra

La muestra es el extracto publicado del CCO: 2 592 registros del 16 de mayo al 10 de junio de 2026, todos con coordenadas (WGS84). El muestreo es no probabilístico, por disponibilidad: se utiliza la totalidad del extracto obtenido. La unidad de análisis es la incidencia, y la unidad de modelado es la combinación de microzona, fecha y turno. Con 26 días y tres turnos se dispone de 78 periodos fecha-turno por microzona; el número total de observaciones dependerá del tamaño de microzona que se defina tras el análisis exploratorio.

Como partición temporal inicial se propone usar los primeros días para entrenamiento, unos cuatro para validación y los cuatro últimos para prueba, ajustándola según el análisis de los datos. A continuación se resume la composición de la muestra.

Tabla 1. Registros de la muestra según turno

| Turno | Registros | % |
|---|---|---|
| Mañana | 1 222 | 47,1 |
| Noche | 754 | 29,1 |
| Tarde | 616 | 23,8 |
| Total | 2 592 | 100,0 |

Fuente: elaboración propia a partir del extracto del CCO (MDSJM, 2026).

Tabla 2. Registros de la muestra según tipo de incidencia

| Tipo de incidencia (CCO) | Registros | % |
|---|---|---|
| Alertas tempranas en apoyo a la PNP y otras gerencias, en presuntas infracciones | 1 353 | 52,2 |
| Alertas tempranas en apoyo a la PNP en presuntas faltas | 622 | 24,0 |
| Alertas tempranas en desastres, infraestructura, servicios y espacios públicos afectados y en riesgo | 265 | 10,2 |
| Operativos | 176 | 6,8 |
| Ayuda y apoyo a personas y entidades | 113 | 4,4 |
| Alertas tempranas en apoyo a la PNP, en actividades presuntamente delictivas | 53 | 2,0 |
| Acontecimientos especiales | 10 | 0,4 |
| Total | 2 592 | 100,0 |

Fuente: elaboración propia a partir del extracto del CCO (MDSJM, 2026).

Tabla 3. Registros de la muestra según sector

| Sector | Registros | % del total |
|---|---|---|
| Sector I | 839 | 32,4 |
| Sector II | 660 | 25,5 |
| Sector III | 452 | 17,4 |
| Sector IV | 98 | 3,8 |
| Sin sector asignado | 543 | 20,9 |
| Total | 2 592 | 100,0 |

Fuente: elaboración propia a partir del extracto del CCO (MDSJM, 2026). La suma de los porcentajes puede diferir en una décima por redondeo.

### 10.3 Fuente complementaria

El conjunto de denuncias policiales del SIDPOL (Ministerio del Interior, 2026) cubre de enero de 2018 a julio de 2026 con conteos por año, mes, distrito y modalidad. Se usará para describir la tendencia y la composición histórica de las denuncias en San Juan de Miraflores y no forma parte del conjunto de entrenamiento.

## 11. Instrumentos

### 11.1 Fuentes de datos

Extracto de incidencias atendidas por el CCO de la MDSJM, en formato de hoja de cálculo o CSV.

Denuncias policiales del SIDPOL (conteos mensuales por distrito y modalidad).

Cartografía base de OpenStreetMap, con la atribución correspondiente (OpenStreetMap Foundation, s. f.), y límite distrital de una fuente oficial por definir.

### 11.2 Software

Python con Pandas y NumPy para limpieza y análisis, y GeoPandas y Shapely para coordenadas, microzonas y operaciones espaciales.

Scikit-learn para regresión logística, Random Forest y Gradient Boosting, y para el cálculo de métricas (Scikit-learn developers, s. f.-a); Joblib para guardar el modelo.

Jupyter Notebook para el análisis exploratorio y los experimentos.

Streamlit para la aplicación web, con Folium o PyDeck para el mapa y Plotly para los gráficos.

SQLite para registrar recursos y asignaciones (segundo nivel).

Git y GitHub para el control de versiones; Power BI como herramienta opcional para un tablero histórico a partir de archivos exportados.

### 11.3 Hardware

Computadora personal convencional, sin tarjeta gráfica dedicada; los modelos empleados trabajan con datos tabulares de tamaño reducido y se entrenan en poco tiempo.

### 11.4 Técnicas e indicadores de evaluación

Partición temporal de los datos en entrenamiento, validación y prueba, evitando mezclar aleatoriamente observaciones relacionadas en el tiempo (Scikit-learn developers, s. f.-b).

Macro F1 como métrica principal, acompañada de precisión y recall por clase, exactitud y matriz de confusión, con el número de observaciones por clase (Scikit-learn developers, s. f.-a).

Comparación contra una línea base de persistencia y contra la regresión logística.

Ranking de prioridad P = w1·R + w2·G + w3·F, donde R es el nivel estimado, G la gravedad histórica y F la frecuencia reciente, con valores normalizados entre 0 y 1 y pesos ajustables por el usuario.

## Referencias

Chainey, S., Tompson, L., & Uhlig, S. (2008). The utility of hotspot mapping for predicting spatial patterns of crime. Security Journal, 21(1-2), 4-28. https://doi.org/10.1057/palgrave.sj.8350066

Congreso de la República del Perú. (2003). Ley N.° 27933, Ley del Sistema Nacional de Seguridad Ciudadana.

Escobedo Neyra, M. C., & Tapia Aquino, C. L. (2024). Comparativa de modelos de regresión a fin de predecir el crimen en zonas de alto riesgo de la ciudad de Lima [Tesis de pregrado, Universidad de Lima]. Repositorio Institucional de la Universidad de Lima. https://hdl.handle.net/20.500.12724/21714

Ministerio del Interior. (2026). DataSet Denuncias Policiales de enero de 2018 a julio de 2026 [Conjunto de datos]. Plataforma Nacional de Datos Abiertos. https://www.datosabiertos.gob.pe/dataset/denuncias-policiales

Mohler, G. O., Short, M. B., Malinowski, S., Johnson, M., Tita, G. E., Bertozzi, A. L., & Brantingham, P. J. (2015). Randomized controlled field trials of predictive policing. Journal of the American Statistical Association, 110(512), 1399-1411. https://doi.org/10.1080/01621459.2015.1077710

Municipalidad Distrital de San Juan de Miraflores. (2026). Relación de incidencias atendidas por el Centro de Control de Operaciones (CCO) [Conjunto de datos]. Plataforma Nacional de Datos Abiertos. https://www.datosabiertos.gob.pe/SEARCH/field_tags/intervenciones-ciudadanas-1527

OJO. (2022). Mapa del delito: 30 puntos con más concentración de robos y hurtos en la capital. https://ojo.pe/actualidad/mapa-del-delito-30-puntos-con-mas-concentracion-de-robos-y-hurtos-en-la-capital-web-ojo-print-noticia/

OpenStreetMap Foundation. (s. f.). Copyright and license. https://www.openstreetmap.org/copyright

Perry, W. L., McInnis, B., Price, C. C., Smith, S. C., & Hollywood, J. S. (2013). Predictive policing: The role of crime forecasting in law enforcement operations. RAND Corporation. https://doi.org/10.7249/j.ctt4cgdcz

Scikit-learn developers. (s. f.-a). Metrics and scoring: quantifying the quality of predictions. Documentación técnica oficial.

Scikit-learn developers. (s. f.-b). Cross-validation: evaluating estimator performance. Documentación técnica oficial.

Wheeler, A. P., & Steenbeek, W. (2021). Mapping the risk terrain for crime using machine learning. Journal of Quantitative Criminology. https://doi.org/10.1007/s10940-020-09457-7

Zevallos Trigoso, N., Mujica, J., & Peñaloza, Á. (s. f.). Mapas participativos: Instrumentos para la geolocalización de zonas de alta incidencia de delitos patrimoniales a nivel local (en Lima, Perú). Dialnet. https://dialnet.unirioja.es/servlet/articulo?codigo=6509041


