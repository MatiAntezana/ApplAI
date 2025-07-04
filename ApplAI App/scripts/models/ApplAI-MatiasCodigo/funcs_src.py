import ast
from typing import Any, Dict
import torch.nn as nn
from sentence_transformers import SentenceTransformer
import os
import re
import shutil
import joblib
import json
from pathlib import Path
import ast
from typing import Any, Dict
import torch

class STClassifier(nn.Module):
    def __init__(
        self,
        model_downloaded: bool,
        model_name: str,
        device: str = 'cpu',
        hidden_layer_sizes: tuple = (256, 64),
        dropout_rate: float = 0.3,
        activation: str = 'gelu'
    ):
        super().__init__()
        self.device = device
        # Carga el modelo de embeddings
        if model_downloaded:
            self.bert = SentenceTransformer(f'./{model_name}')
        else:
            self.bert = SentenceTransformer(model_name)

        # Dimension de entrada = embeddings_CV + embeddings_job (concatenados)
        in_dim = self.bert.get_sentence_embedding_dimension() * 2

        # Construye la MLP
        layers = []
        prev_dim = in_dim
        for h in hidden_layer_sizes:
            layers.append(nn.Linear(prev_dim, h))
            if activation.lower() == 'relu':
                layers.append(nn.ReLU())
            elif activation.lower() == 'gelu':
                layers.append(nn.GELU())
            else:
                raise ValueError(f"Unsupported activation: {activation}")
            layers.append(nn.Dropout(dropout_rate))
            prev_dim = h
        layers.append(nn.Linear(prev_dim, 1))

        self.mlp = nn.Sequential(*layers)
        self.to(self.device)

    def forward(self, x):
        # x: tensor (batch_size, 2 * embed_dim)
        return self.mlp(x).squeeze(1)


def getEmbbedings(model, dataset):
    cv_embeddings = model.encode(dataset['CV'].tolist(), convert_to_tensor=True)
    jd_embeddings = model.encode(dataset['JD'].tolist(), convert_to_tensor=True)

    X = torch.cat((cv_embeddings, jd_embeddings), dim=1)

    Y = torch.tensor(dataset['score'].tolist(), dtype=torch.float32)

    return X, Y

def getDatasetEmbeddings(model, dataset, typeEbbeddings):
    if typeEbbeddings == "NormalEmbbedings":
        return getEmbbedings(model, dataset)
    elif typeEbbeddings == "EmbbedingsSimilarity":
        return getEmbbedingsSimilarity(model, dataset)
    else:
        print("No especificado el tipo de Embbedings")
    
def load_config_with_exec(file_path: str) -> Dict[str, Any]:
    config = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        exec(f.read(), {}, config)
    return config

def save_final_model(gs, config_py_path, base_name="finalmodel", out_root="."):
    out_root_path = Path(out_root)
    out_root_path.mkdir(parents=True, exist_ok=True)

    existing = []
    pattern = re.compile(rf"^{re.escape(base_name)}(\d+)$")
    for entry in os.listdir(out_root_path):
        m = pattern.match(entry)
        if m:
            existing.append(int(m.group(1)))
    next_idx = max(existing, default=0) + 1

    folder_name = f"{base_name}{next_idx}"
    folder_path = out_root_path / folder_name
    folder_path.mkdir(parents=True, exist_ok=False)

    config_dest = folder_path / Path(config_py_path).name
    shutil.copy(config_py_path, config_dest)

    model_dest = folder_path / "best_model.pkl"
    joblib.dump(gs.best_estimator_, model_dest)

    params_dest = folder_path / "best_params.json"
    with open(params_dest, "w") as f:
        json.dump(gs.best_params_, f, indent=4)

def get_or_create_embeddings(model, df, type_embedding, prefix, folder="embeddings"):
    os.makedirs(folder, exist_ok=True)
    x_path = Path(folder) / f"{prefix}_X_{type_embedding}.pkl"
    y_path = Path(folder) / f"{prefix}_Y.pkl"

    if x_path.exists() and y_path.exists():
        print(f"📂 Cargando embeddings desde: {x_path}")
        X = joblib.load(x_path)
        Y = joblib.load(y_path)
    else:
        print(f"⚙️ Generando embeddings para {prefix}...")
        X, Y = getDatasetEmbeddings(model, df, type_embedding)
        joblib.dump(X, x_path)
        joblib.dump(Y, y_path)
        print(f"✅ Embeddings guardados en: {x_path}")

    return X, Y
