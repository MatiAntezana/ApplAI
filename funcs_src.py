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
    def __init__(self, model_downloaded, model_name, device='cpu'):
        super().__init__()
        self.device = device
        if model_downloaded:
            self.bert = SentenceTransformer(f'./{model_name}')
        else:
            self.bert = SentenceTransformer(model_name)
        self.linear = nn.Linear(self.bert.get_sentence_embedding_dimension()*2, 1)

    def forward(self, x):
        return self.linear(x).squeeze(1)

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
    
def extract_config_from_file(file_path: str) -> Dict[str, Any]:
    """
    Extrae todas las asignaciones simples (model, param_grid, cv, etc.)
    de un archivo Python, evaluando sus literales.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()
    tree = ast.parse(source, filename=file_path)
    config: Dict[str, Any] = {}

    for node in tree.body:
        if isinstance(node, ast.Assign):
            # Solo un target y que sea un nombre
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                name = node.targets[0].id
                # ast.literal_eval falla si no es literal (p.ej. función)
                try:
                    value = ast.literal_eval(node.value)
                except Exception:
                    continue
                config[name] = value

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