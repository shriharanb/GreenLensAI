import re
from typing import List, Dict

class AgentService:
    def __init__(self):
        self.pipeline = None
        self.is_model_loaded = False
        self.model_id = "Qwen/Qwen2.5-0.5B-Instruct"
        
        self.lang_map = {
            'en': 'English',
            'fr': 'French',
            'es': 'Spanish',
            'it': 'Italian',
            'ru': 'Russian'
        }

    def load_model(self):
        """Loads the Qwen model for conversational AI and translation."""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
            import torch
            
            print(f"--- LLM LOAD START: {self.model_id} ---")
            print(f"Note: This may take several minutes if the model (~1GB) is not cached.")
            
            print(f"Loading tokenizer for {self.model_id}...")
            tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            
            print(f"Loading model weights for {self.model_id} (this is the big part)...")
            model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                device_map="auto",
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                low_cpu_mem_usage=True
            )
            
            print(f"Setting up generation pipeline...")
            self.pipeline = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=256
            )
            self.is_model_loaded = True
            print(f"✅ Model {self.model_id} loaded successfully.")
            print(f"--- LLM LOAD COMPLETE ---")
        except Exception as e:
            print(f"❌ Error loading LLM model: {e}")
            import traceback
            traceback.print_exc()

    def _chat(self, system_prompt: str, user_prompt: str) -> str:
        if not self.is_model_loaded:
            self.load_model()
            
        if not self.is_model_loaded:
            return ""
            
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        try:
            outputs = self.pipeline(messages, max_new_tokens=256, temperature=0.3)
            # Find the assistant's reply
            for msg in reversed(outputs[0]["generated_text"]):
                if msg["role"] == "assistant":
                    return msg["content"].strip()
            return ""
        except Exception as e:
            print(f"LLM Generation failed: {e}")
            return ""

    def _clean_translation(self, translated: str) -> str:
        if not translated:
            return ""
        # Strip potential prefixes from small models
        prefixes_to_strip = [
            "Here is the translation:", "Here's the translation:",
            "Translation:", "Translated text:", "Here is the translated text:",
            "Here is the text in English:", "In English:", "Translated:"
        ]
        text_lower = translated.lower()
        for prefix in prefixes_to_strip:
            if text_lower.startswith(prefix.lower()):
                return translated[len(prefix):].strip()
            # Also handle if they wrap in quotes
            if text_lower.startswith(f'"{prefix.lower()}'):
                stripped = translated[len(prefix)+1:].strip()
                if stripped.endswith('"'):
                    stripped = stripped[:-1]
                return stripped
        return translated.strip()

    def translate_message(self, text: str, target_lang: str) -> str:
        """Translates a message to the target language using the LLM."""
        if not text or target_lang == 'en':
            return text
            
        lang_name = self.lang_map.get(target_lang, 'English')
        system_prompt = f"You are a professional translator. Your task is to accurately translate the provided text into {lang_name}. Output ONLY the translated text. Do not include any explanations, greetings, or the original text."
        translated = self._chat(system_prompt, text)
        cleaned = self._clean_translation(translated)
        return cleaned if (cleaned and len(cleaned) > 1) else text

    def translate_to_english(self, text: str, source_lang: str) -> str:
        """Translates a message to English using the LLM."""
        if not text or source_lang == 'en':
            return text
            
        lang_name = self.lang_map.get(source_lang, 'English')
        system_prompt = f"You are a professional translator. Your task is to accurately translate the provided {lang_name} text into English. Output ONLY the English translation. Do not include any explanations, greetings, or the original text."
        translated = self._chat(system_prompt, text)
        cleaned = self._clean_translation(translated)
        return cleaned if (cleaned and len(cleaned) > 1) else text
        
    def generate_chat_response(self, user_message_english: str, rag_context: str, language: str) -> str:
        """Generates a conversational reply based on RAG context, always in English first, then translates."""
        system_prompt = (
            "You are GreenLensAI, an expert agricultural assistant. "
            "Always reply in English. "
            "Be conversational and helpful. "
            "If a disease is detected, ALWAYS clearly state the disease name first, "
            "then explain the treatment/solution step by step. "
            "If the crop is healthy, congratulate the farmer. "
        )
        
        if rag_context:
            system_prompt += f"Use the following expert guide to inform your answer:\n\n{rag_context}\n\nPresent the solution naturally with the disease name and treatment steps."
            
        english_reply = self._chat(system_prompt, user_message_english)
        if not english_reply:
            english_reply = "I encountered an issue. Please try again."
            
        if language and language != 'en':
            return self.translate_message(english_reply, language)
        return english_reply

    def parse_rag_solution_into_days(self, solution_text: str) -> List[str]:
        """
        Parses a solution string from RAG into a list of daily treatments.
        Assumes the text might have 'Day 1: ... Day 2: ...' patterns.
        """
        days = []
        # Try to find explicit Day X patterns
        day_splits = re.split(r'Day\s*\d+\s*[-:]', solution_text, flags=re.IGNORECASE)
        
        # If no explicit days, just break by sentences or return as single block
        if len(day_splits) <= 1:
            # Split by period for rough daily tasks if no "Day X" format found
            sentences = [s.strip() for s in solution_text.split('.') if s.strip()]
            return sentences if sentences else [solution_text]
            
        # First split might be introductory text, skip if empty
        for split in day_splits:
            if split.strip():
                days.append(split.strip())
                
        return days

    def generate_daily_prompt(self, disease_name: str, day_number: int, treatment_step: str, language: str, is_first_day: bool = False) -> str:
        """Generates the prompt string to send to the farmer."""
        if is_first_day:
            # Deterministic construction for exact wording requested by user
            english_reply = f"Hii I'm GreenLensAI  this is Day-1 Your crop have afftect by {disease_name} follow the give solution we will see on next day\n\nSolution: {treatment_step}"
        else:
            english_reply = f"Ok, {disease_name} is still not gone. Now this is day {day_number}.\n\nSolution: {treatment_step}"
            
        if language and language != 'en':
            return self.translate_message(english_reply, language)
        return english_reply

    def generate_photo_request(self, day_number: int, language: str) -> str:
        """Generates the prompt requesting the next day's photo."""
        # Deterministic construction for exact wording requested by user
        english_reply = f"This is day - {day_number} share the pic of your affected crop."
        
        if language and language != 'en':
            return self.translate_message(english_reply, language)
        return english_reply

agent_service = AgentService()
