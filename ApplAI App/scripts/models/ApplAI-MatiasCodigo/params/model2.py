model = "all-MiniLM-L6-v2"


param_grid = {
    'lr': [1e-4],
    'max_epochs': [2],
    'batch_size': [32],
}

cv = 3

typeEmbedding = "NormalEmbbedings"