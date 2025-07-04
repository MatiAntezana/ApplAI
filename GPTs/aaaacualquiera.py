import csv

# Rutas a tus archivos .txt
real_scores_path = 'y_val.txt'
pred_scores_path = 'y_pred.txt'
output_csv_path = 'predicted_scores_FT_LLM.csv'

# Leer las líneas de los archivos
with open(real_scores_path, 'r') as real_file:
    real_scores = [line.strip() for line in real_file.readlines()]

with open(pred_scores_path, 'r') as pred_file:
    pred_scores = [line.strip() for line in pred_file.readlines()]

# Verificar que tengan la misma cantidad de líneas
if len(real_scores) != len(pred_scores):
    raise ValueError("Los archivos no tienen la misma cantidad de líneas.")

# Escribir en CSV
with open(output_csv_path, 'w', newline='') as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(['Real Score', 'Predicted Score'])  # encabezado
    for real, pred in zip(real_scores, pred_scores):
        writer.writerow([real, pred])

print(f"CSV generado con éxito: {output_csv_path}")
