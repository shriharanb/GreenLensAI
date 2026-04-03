from django.core.management.base import BaseCommand
from api.models import TreatmentPlan, TreatmentDay
from api.services.agent_service import agent_service
from api.services.twilio_service import twilio_service
from django.utils import timezone
import datetime

class Command(BaseCommand):
    help = 'Sends daily progress check SMS to farmers engaged in an active treatment plan'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Checking active Treatment Plans..."))
        
        # agent_service.load_model() should be called instead if needed, or rely on lazy loading
        # agent_service.load_translation_model does not exist.
        
        active_plans = TreatmentPlan.objects.filter(is_active=True)
        count = 0
        
        for plan in active_plans:
            # Move to next day if it wasn't just created today.
            # Simplified for MVP: Increment day every time this runs (assuming it runs once every 24h via Cron)
            # Find the treatment for the *next* day
            next_day_num = plan.current_day + 1
            treatment_day = TreatmentDay.objects.filter(plan=plan, day_number=next_day_num).first()
            
            if not treatment_day:
                # If there are no more days in the plan, mark it inactive
                plan.is_active = False
                plan.save()
                
                # Send completion SMS
                if plan.farmer.phone:
                    completion_msg = "Your crop treatment plan from GreenLensAI is complete. Please upload a new image if issues persist."
                    translated = agent_service.translate_message(completion_msg, plan.farmer.language_preference)
                    twilio_service.send_sms(plan.farmer.phone, translated)
                continue
                
            # We have a treatment for the next day
            plan.current_day = next_day_num
            plan.save()
            
            if plan.farmer.phone:
                # 1) Send the photo request for tomorrow/today
                # Pass language preference to generate_photo_request
                photo_req = agent_service.generate_photo_request(next_day_num, plan.farmer.language_preference)
                twilio_service.send_sms(plan.farmer.phone, photo_req)
                
                # 2) Note: In the user flow, the farmer then uploads a photo, 
                # which triggers the Day X treatment logic in PredictImageView.
                pass
            
            count += 1
            
        self.stdout.write(self.style.SUCCESS(f"Finished processing {count} active plans."))
