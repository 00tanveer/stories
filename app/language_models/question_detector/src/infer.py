import os
import tarfile
from pathlib import Path
from app.services.storage import Storage
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from dotenv import load_dotenv

ENV = os.getenv("APP_ENV", "development")  # default to development
if ENV == 'development':
    load_dotenv(".env.development")
MODEL_NAME = "distilbert_question_detector"
MODEL_CACHE = Path(os.getenv("QUESTION_MODEL_CACHE", "/opt/stories/models"))
MODEL_DIR = MODEL_CACHE / MODEL_NAME
MODEL_OBJECT = os.getenv("QUESTION_MODEL_OBJECT", f"models/{MODEL_NAME}.tar.gz")

class InferenceModel:
    def __init__(self):
        MODEL_CACHE.mkdir(parents=True, exist_ok=True)
        if not MODEL_DIR.exists():
            storage = Storage(bucket_name=os.getenv("R2_BUCKET_NAME", "stories-prod"))
            archive = MODEL_CACHE / f"{MODEL_NAME}.tar.gz"
            storage.download_file(MODEL_OBJECT, str(archive))
            with tarfile.open(archive) as tf:
                tf.extractall(MODEL_CACHE)
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
        self.model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
        self.pipe = pipeline("text-classification", model=self.model, tokenizer=self.tokenizer)

    def predict(self, text: str):
        return self.pipe(text)
# # Example usage
infer_model = InferenceModel()
print(infer_model.predict("What inspired you to start your company?"))
print(infer_model.predict("Hogar baal"))

