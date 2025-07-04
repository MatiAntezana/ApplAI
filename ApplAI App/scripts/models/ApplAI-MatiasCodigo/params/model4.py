import torch
from skorch.callbacks import EarlyStopping

model = "intfloat/e5-base-v2"

param_grid = {
    'lr': [1e-3, 1e-4],
    'max_epochs': [150],
    'batch_size': [16, 32],
    'optimizer': [torch.optim.Adam, torch.optim.SGD],
    'iterator_train__shuffle': [True],
}

cv = 3

typeEmbedding = "NormalEmbbedings"