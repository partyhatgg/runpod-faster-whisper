from concurrent.futures import ThreadPoolExecutor, as_completed

from faster_whisper import WhisperModel

model_names = ["medium", "large-v3"]

def load_model(selected_model):
    '''
    Download model
    '''
    try:
        loaded_model = WhisperModel(selected_model, device="cpu", compute_type="int8", download_root="./.models")
        return loaded_model
    except Exception as e:
        print(f"Error downloading model '{model_name}': {e}")
        pass


models = {}


with ThreadPoolExecutor() as executor:
    model_futures = {executor.submit(load_model, model): model for model in model_names}
    for future in as_completed(model_futures):
        model_name = model_futures[future]
        try:
            models[model_name] = future.result()
        except Exception as e:
            print(f"Error loading model '{model_name}': {e}")

