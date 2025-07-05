from sentence_transformers import SentenceTransformer, util


def leer_txt(path: str) -> str:
    """
    Lee un archivo .txt y devuelve su contenido como una cadena.
    """
    with open(path, 'r', encoding='utf-8') as f:
        contenido = f.read()
    return contenido

def predict(cv_desc, jb_desc, model):
    embedding1 = model.encode(cv_desc, convert_to_tensor=True)
    embedding2 = model.encode(jb_desc, convert_to_tensor=True)

    return util.cos_sim(embedding1, embedding2)

def main():
    model = SentenceTransformer("/Users/matias/4°AÑO/NLP/ApplAI/mxbai-embed-large-v1")

    cv = "Ingenieron en Sistemas de Información"
    jb = "Desarrollador Backend y experto en sistemas"

    cv_desc = leer_txt("cv.txt")
    jb_desc = leer_txt("job_description.txt")

    # Realizar la predicción
    similarity_score = predict(cv_desc, jb_desc, model)

    print(f"Similarity Score: {similarity_score.item()}")