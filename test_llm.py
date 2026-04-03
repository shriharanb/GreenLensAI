import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"

def test_llm():
    print(f"Loading tokenizer for {MODEL_ID}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    
    print(f"Loading model {MODEL_ID}...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        device_map="auto",
        torch_dtype="auto"
    )
    
    print("Model loaded successfully. Initializing pipeline...")
    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=256
    )
    
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant. Answer the user in the language they write to you."},
        {"role": "user", "content": "हाय, मुझे मदद चाहिए।"}
    ]
    
    print("Generating response...")
    outputs = pipe(messages)
    print("--- Output ---")
    print(outputs[0]["generated_text"][-1]["content"])

if __name__ == "__main__":
    test_llm()
