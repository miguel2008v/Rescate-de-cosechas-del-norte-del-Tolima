# Rescate de Cosechas del Norte del Tolima — listo para Render

Aplicación web académica con **HTML, CSS y JavaScript**, lógica algorítmica
en **Python** y servidor **Gunicorn (WSGI)** para su despliegue en Render.
No utiliza base de datos ni API de terceros.

## Cómo publicar en Render (desde GitHub)

1. Descomprime `Rescate_de_cosechas_listo_para_Render.zip`.
2. Crea un repositorio nuevo en GitHub y sube **el contenido de la carpeta**
   `rescate_cosechas_render` a la **raíz del repositorio**, incluido `render.yaml`.
   **No** subas el ZIP como único archivo; Render necesita leer el código.
3. Abre https://dashboard.render.com y conecta tu cuenta de GitHub.
4. Pulsa **New > Web Service**, selecciona el repositorio y configura:
   - **Language/Runtime:** Python 3
   - **Root Directory:** vacío (si subiste los archivos a la raíz)
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 30 app:app`
   - **Plan:** Free, si aparece disponible
   - **Health Check Path:** `/health`
5. Pulsa **Deploy Web Service**. Cuando el estado sea **Live**, abre
   la URL `https://<nombre-asignado>.onrender.com` que Render mostrará.
   También debe responder `https://<nombre-asignado>.onrender.com/health`
   con `{"status":"ok"}`.

**Alternativa:** `New > Blueprint` puede leer el archivo `render.yaml`
desde el repositorio y proponer el servicio automáticamente.

## Estructura

```text
app.py                 Servidor WSGI: API JSON + HTML/CSS/JS
logic/algorithms.py    Backtracking y poda, Greedy, DP, Merge Sort
templates/index.html  Interfaz
static/styles.css     Estilos
static/app.js         Interactividad, gráficos y cálculos solicitados
tests/                Pruebas automáticas
requirements.txt      Gunicorn
render.yaml           Configuración declarativa para Render
.python-version       Python 3.13
```

## Pruebas

Sin instalar paquetes, ejecuta en la carpeta del proyecto:

```bash
python -m unittest discover -s tests -v
python app.py
```

Visita http://127.0.0.1:5000/ en tu PC.

Para probar el mismo servidor de Render localmente tras instalar dependencias:

```bash
pip install -r requirements.txt
gunicorn --bind 0.0.0.0:10000 app:app
```

En Windows, el comando `gunicorn` debe ejecutarse en Linux/Render; para
desarrollo en Windows utiliza `py app.py`.

## API

- `GET /` — interfaz
- `GET /static/app.js` y `GET /static/styles.css` — recursos estáticos
- `GET /api/defaults` — seis productores y dos camiones de 100 kg
- `POST /api/solve` — solución exacta y comparación
- `POST /api/benchmark` — pruebas N=5 a N=8 (datos simulados)
- `GET /health` — comprobación del servicio

## Alcance

El sistema minimiza distancias euclidianas para posiciones **simuladas**;
no calcula distancias viales reales. La prioridad es informativa y no
condiciona matemáticamente las rutas. El máximo es ocho productores.
Es una **demostración académica**, sin autenticación y con un cálculo
exacto combinatorio limitado; no debe usarse como logística empresarial.

## Problemas frecuentes

- **No open ports detected:** usa el comando de inicio con
  `--bind 0.0.0.0:$PORT`, no el servidor local `python app.py`.
- **ModuleNotFoundError: gunicorn:** comprueba el comando de build.
- **ModuleNotFoundError: logic:** comprueba que la raíz del repositorio
  incluya directamente `app.py`, `logic/`, `templates/` y `static/`.
- **El servicio tarda al abrir:** un servicio Free puede suspenderse por
  inactividad y tardar en reactivarse.
- **CSS/JS no carga:** comprueba en Render los endpoints `/static/styles.css`
  y `/static/app.js`.
