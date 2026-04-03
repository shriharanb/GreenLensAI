import os
import sys

# Add the project directory to sys.path so we can import django settings if needed
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# We need to set up django environment to run this if it depends on django settings
# but agent_service doesn't seem to depend on django settings directly.
from api.services.agent_service import agent_service

def test_languages():
    languages = {
        'en': 'English', 
        'ta': 'Tamil', 
        'te': 'Telugu', 
        'hi': 'Hindi', 
        'bn': 'Bengali', 
        'fr': 'French', 
        'es': 'Spanish', 
        'pt': 'Portuguese', 
        'de': 'German', 
        'it': 'Italian', 
        'ru': 'Russian', 
        'ar': 'Arabic'
    }
    
    agent_service.lang_map = languages
    agent_service.load_model()
    
    test_sentence = "The crop in the photo appears to have late blight, a common fungal disease. Please apply fungicide immediately."
    
    print("--- Starting Translation Tests ---")
    results = {}
    for code, lang in languages.items():
        if code == 'en':
            continue
        print(f"\nTranslating to {lang} ({code})...")
        translated = agent_service.translate_message(test_sentence, code)
        print(f"[{lang}] Original:  {test_sentence}")
        print(f"[{lang}] Translated: {translated}")
        results[lang] = translated
        
    print("\n--- Summary of Translations ---")
    for lang, translated in results.items():
        print(f"{lang}: {translated}")

if __name__ == "__main__":
    test_languages()
