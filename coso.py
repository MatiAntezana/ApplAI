import csv
import random

# Ruta al archivo CSV
csv_file = 'archivo.csv'

# Leer el CSV (por ejemplo, imprimir cuántas filas tiene)
with open(csv_file, newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    rows = list(reader)
    print(f'El CSV tiene {len(rows)} filas.')

# Generar un número aleatorio entre 0 y 1
random_value = random.uniform(0, 1)

print(f'Valor aleatorio generado: {random_value}')
