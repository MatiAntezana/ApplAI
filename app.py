from flask import Flask, request, render_template
import os

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)



@app.route('/')
def index():
    return render_template("index.html")

@app.route('/evaluar', methods=["POST"])
def evaluar():
    descripcion = request.form["descripcion"]
    archivos = request.files.getlist("cv_files")

    resultados = []
    for archivo in archivos:
        path = os.path.join(UPLOAD_FOLDER, archivo.filename)
        archivo.save(path)
        # 
        # Acá deberías extraer texto del CV y compararlo con `descripcion`
        # Simulación:
        score = len(descripcion) % 100  # solo de ejemplo
        resultados.append((archivo.filename, score))

    mejor = max(resultados, key=lambda x: x[1])
    return f"El mejor CV es: {mejor[0]} con score {mejor[1]}"
#