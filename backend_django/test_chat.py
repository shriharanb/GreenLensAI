import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api.models import Farmer
from api.rag_service import rag_service
from api.services.agent_service import agent_service

user_message = "हाय, मुझे मदद चाहिए।"
language = "hi"
farmer = Farmer.objects.first()

try:
    print("Translating query...")
    query_text = agent_service.translate_to_english(user_message, language)
    print(f"Query text: {query_text}")

    print("Querying RAG...")
    solutions = rag_service.query(query_text)
    
    if solutions:
        base_response = solutions[0]['text'][:1000]
    else:
        base_response = "I couldn't find specific information."
    print(f"Base response: {base_response}")

    print("Translating response...")
    translated_response = agent_service.translate_message(base_response, language)
    print(f"Translated response: {translated_response}")
except Exception as e:
    import traceback
    traceback.print_exc()
