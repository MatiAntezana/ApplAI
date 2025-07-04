import matplotlib.pyplot as plt
import pandas as pd

csv = pd.read_csv("predicted_scores_FT_LLM.csv")

# Calcular RMSE
rmse = ((csv["Real Score"] - csv["Predicted Score"]) ** 2).mean() ** 0.5
print(f"RMSE: {rmse}")

# Graficar ambos resultados en una sola figura (y_pres vs y_true) distinguiendo cada caso por colores.
plt.figure(figsize=(10, 10))
plt.scatter(csv["Real Score"], csv["Predicted Score"], color='green', label='Fine Tuned LLM. RMSE: {:.3f}'.format(rmse), alpha=0.6)
plt.plot([0, 1], [0, 1], color='red', linestyle='--', label='y = x (Ideal)')
plt.title('Fine Tuned LLM Predictions')
plt.xlabel('Real Score')
plt.ylabel('Predicted Score')
plt.legend()
plt.grid()
plt.savefig("fine tuned result.png")
plt.show()

