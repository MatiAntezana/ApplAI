import matplotlib.pyplot as plt
import pandas as pd

csv_o3 = pd.read_csv("predicted_scores_o3_mini.csv")
csv_4o = pd.read_csv("predicted_scores_4o_mini.csv")

# Calcular RMSE para ambos modelos
rmse_o3 = ((csv_o3["Real Score"] - csv_o3["Predicted Score"]) ** 2).mean() ** 0.5
rmse_4o = ((csv_4o["Real Score"] - csv_4o["Predicted Score"]) ** 2).mean() ** 0.5

# Graficar ambos resultados en una sola figura (y_pres vs y_true) distinguiendo cada caso por colores.
plt.figure(figsize=(10, 10))
plt.scatter(csv_o3["Real Score"], csv_o3["Predicted Score"], color='blue', label='o3-Mini. RMSE: {:.3f}'.format(rmse_o3), alpha=0.6)
plt.scatter(csv_4o["Real Score"], csv_4o["Predicted Score"], color='orange', label='GPT-4o-Mini. RMSE: {:.3f}'.format(rmse_4o), alpha=0.6)
plt.plot([0, 1], [0, 1], color='red', linestyle='--', label='y = x (Ideal)')
plt.title('Comparación de Predicciones: GPT-3.5 O3 Mini vs GPT-4 O3 Mini')
plt.xlabel('Real Score')
plt.ylabel('Predicted Score')
plt.legend()
plt.grid()
plt.savefig("comparison of GPTs.png")
plt.show()
