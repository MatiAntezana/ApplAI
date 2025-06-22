import pandas as pd

##### ESTE ARCHIVO ES SOLO PARA VER QUE SALIÓ BIEN EL CSV. BORRARRRRR #######

def leer_csv(ruta_archivo: str) -> pd.DataFrame:
    """
    Lee un archivo CSV y lo convierte en un DataFrame de pandas.

    Args:
        ruta_archivo (str): Ruta al archivo CSV.

    Returns:
        pd.DataFrame: DataFrame con los datos del archivo CSV.
    """
    try:
        df = pd.read_csv(ruta_archivo)
        return df
    except FileNotFoundError:
        print(f"El archivo {ruta_archivo} no se encontró.")
        return pd.DataFrame()
    except pd.errors.EmptyDataError:
        print(f"El archivo {ruta_archivo} está vacío.")
        return pd.DataFrame()
    except Exception as e:
        print(f"Ocurrió un error al leer el archivo {ruta_archivo}: {e}")
        return pd.DataFrame()
    

# Ejemplo de uso
if __name__ == "__main__":
    ruta = "cv_vector_db/reviews_of_candidates.csv"  # Cambia esto por la ruta de tu archivo CSV
    df = leer_csv(ruta)
    if not df.empty:
        print("Datos leídos correctamente:")
        print(df.columns)
        for col in df.columns:
            print(f"\nCOLUMNA: {col}: \n{df[col]}\n")