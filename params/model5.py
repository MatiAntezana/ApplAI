import torch
from skorch.callbacks import EarlyStopping

model = "mixedbread-ai/mxbai-embed-large-v1"

param_grid = {
    'lr': [1e-3, 1e-4],
    'max_epochs': [200],
    'batch_size': [16, 32],
}

cv = 3

typeEmbedding = "NormalEmbbedings"