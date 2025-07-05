model = "all-MiniLM-L6-v2"

param_grid = {
    'lr': [1e-2, 1e-3, 1e-4],
    'max_epochs': [100],
    'batch_size': [16, 32, 64],
}

cv = 3

typeEmbedding = "NormalEmbbedings"