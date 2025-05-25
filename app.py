from flask import Flask, request, render_template

app = Flask(__name__)

def seleccionar_mejor_cv(cvs, especificacion):
    # Aquí iría tu lógica real
    return cvs[0] if cvs else "No hay CVs disponibles"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        especificacion = request.form['especificacion']
        cvs = ["CV de Ana", "CV de Juan", "CV de Pedro"]  # Simulados
        mejor_cv = seleccionar_mejor_cv(cvs, especificacion)
        mejor_cv = "CV de Ana""
        return render_template('resultado.html', cv=mejor_cv)
    return render_template('index.html')
