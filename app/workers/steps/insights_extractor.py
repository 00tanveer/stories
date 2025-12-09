import json
import requests
from tqdm import tqdm
import os
from pydantic import BaseModel
from typing import List
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

OLLAMA_BASE = "https://ovb1wujcy8gupy-11434.proxy.runpod.net"
load_dotenv()
class Insight(BaseModel):
    insight: str
    type: str

class InsightsResponse(BaseModel):
    question: str
    insights: List[Insight]
schema = InsightsResponse.model_json_schema()
# for Huggingface Inference API
response_format = {
    "type": "json_schema",
    "json_schema": {
        "name": "InsightsResponse",   
        "schema": schema              
    }
}

OLLAMA_MODEL_NAME = 'llama3.1:8b'
SEMANTIC_TYPES = [
    "career_reflection",
    "decision_making",
    "philosophy",
    "learning",
    "leadership",
    "technical",
    "personal_growth",
    "industry_trend"
]

def generate_insight(block, model=OLLAMA_MODEL_NAME, huggingface=False, huggingface_model="openai/gpt-oss-20b"):
    """
    Given a Q&A dict with 'topic', 'question_text', and 'answer_text',
    use a local Ollama model to generate concise labeled insights.
    """
    prompt = f"""
    You are analyzing a podcast interview between {block['question_speaker']} and {block['answer_speaker']}.
    You are an expert interviewer and insight extractor.
    Given the topic, question, and the guest's answer — write 2 to 4 short insights.

    Each insight should include:
    - A clear phrasing of the idea or takeaway
    - A type label, chosen from this list:
    {', '.join(SEMANTIC_TYPES)}

    Return the result as a JSON array like this:

    Return strictly in this JSON format:
    {{
    "question": "{block['question_text']}",
    "insights": [
        {{"insight": "...", "type": "..."}},
        {{"insight": "...", "type": "..."}}
    ]
    }}

    ---
    Topic: {block['topic']}
    Question: {block['question_text']}
    Answer: {block['answer_text']}
    ---
    """
    if not huggingface:
        data = {
            "model": model,
            "prompt": prompt,
            "format": schema,
            "stream": False,
        }

        response = requests.post(f"{OLLAMA_BASE}/api/generate", json=data, timeout=300)
        print(type(response.json()))
        print(json.loads(response.json()['response']))
        insights_response = json.loads(response.json()['response'])
        # response = ollama.chat(
        #     model=model,
        #     messages=[{'role': 'user', 'content': prompt}],
        #     options={'temperature': 0.4},
        #     format=schema
        # )

        # text = response['message']['content'].strip()
        # print(text)
        insights_response = InsightsResponse.model_validate(insights_response)
    else: 
        hf_token = os.getenv("HF_TOKEN")
        client = InferenceClient(
            provider="auto",  # or use "auto" for automatic selection
            api_key=hf_token,
        )
        messages = [{'role': 'user', 'content': prompt}]
        response = client.chat_completion(
            model=huggingface_model,
            messages=messages,
            response_format=response_format,
            temperature=0.4,
        )
        insights_response = json.loads(response.choices[0].message.content)
        print(insights_response)
        insights_response = InsightsResponse.model_validate(insights_response)
        print(insights_response)
    return insights_response.model_dump()

def process_all_qa(qa_pairs, output_path, model='llama3.1:8b'):
    """
    Processes all Q&A pairs in a JSON file and writes out labeled insights.
    """

    all_insights = []
    # print(type(qa_pairs))
    # print(qa_pairs[:3])
    for qa in tqdm(qa_pairs, desc=f"Generating insights with {model}"):
        print("\n", qa["question_text"])
        insights = generate_insight(qa, model=model, huggingface=False)
        print(insights)
        all_insights.append(insights)

    with open(output_path, 'w') as f:
        json.dump(all_insights, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Done. Insights written to {output_path}")


# Example usage:
# process_all_qa("data/episode_01_qa.json", "data/episode_01_insights.json", model="gemma3:4b")


# Load JSON files from content-json directory
folder_path = "content-json/"
filepaths = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
for path in filepaths:
    with open(path, 'r') as f:
        data = json.load(f)
# Extract insights
    output_path = path.replace("content-json", "insights-json").replace(".json", "_insights.json")
    process_all_qa(data["blocks"], output_path, model='llama3.1:8b')
    

# curl -X POST https://r9iewp2pk4kfcg-11434.proxy.runpod.net/api/generate -H "Content-Type: application/json" -d '{
#   "model": "gemma2:9b",
#   "prompt": "Ollama is 22 years old and is busy saving the world. Respond using JSON",
#   "stream": false,
#   "format": {
#     "type": "object",
#     "properties": {
#       "age": {
#         "type": "integer"
#       },
#       "available": {
#         "type": "boolean"
#       }
#     },
#     "required": [
#       "age",
#       "available"
#     ]
#   }
# }'