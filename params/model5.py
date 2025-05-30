import torch
from skorch.callbacks import EarlyStopping

model = "mixedbread-ai/mxbai-embed-large-v1"

param_grid = {
    'lr': [1e-3, 1e-4],
    'max_epochs': [20],
    'batch_size': [16],
    'module__hidden_layer_sizes': [(128,), (256,), (128, 64)],
    'module__dropout_rate': [0.1, 0.3, 0.5],
    'module__activation': ['relu', 'gelu'],
    'optimizer': [torch_optim.Adam, torch_optim.SGD],
    'optimizer__weight_decay': [0.0, 1e-5, 1e-4],
}

cv = 3

typeEmbedding = "NormalEmbbedings"