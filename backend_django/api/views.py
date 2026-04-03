from rest_framework import status, views
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate, login as django_login
from .models import Farmer, ChatHistory, Conversation, PendingFarmer, OTPRecord
from .serializers import FarmerSerializer, ChatHistorySerializer, ConversationSerializer
from .vision_service import predict_image
import os
import uuid
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib.auth.hashers import make_password

class RegisterView(views.APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        print(f"\n[DEBUG] RegisterView POST data: {request.data}")
        try:
            username = request.data.get('username')
            phone = request.data.get('phone', '')
            password = request.data.get('password')
            recovery_answer = request.data.get('recovery_answer')
            
            # Sanitize phone: remove spaces and handle redundant + signs
            phone = phone.replace(' ', '')
            if phone.startswith('++'):
                phone = '+' + phone.lstrip('+')
            # If phone starts with +91+91, fix it
            if phone.startswith('+91+91'):
                phone = '+91' + phone[6:]
            
            if not all([username, phone, password, recovery_answer]):
                msg = f"Missing fields: {[k for k in ['username', 'phone', 'password', 'recovery_answer'] if not request.data.get(k)]}"
                print(f"[DEBUG] Registration failed: {msg}")
                return Response({"error": msg}, status=status.HTTP_400_BAD_REQUEST)
                
            if Farmer.objects.filter(username=username).exists():
                print(f"[DEBUG] Registration failed: Username '{username}' already exists in Farmer model")
                return Response({"error": "Farmer ID already exists"}, status=status.HTTP_400_BAD_REQUEST)
                
            if Farmer.objects.filter(phone=phone).exists():
                print(f"[DEBUG] Registration failed: Phone '{phone}' already registered in Farmer model")
                return Response({"error": "Phone number is already registered"}, status=status.HTTP_400_BAD_REQUEST)
                
            # Create or update PendingFarmer
            print(f"[DEBUG] Creating/Updating PendingFarmer for {username}")
            pending_farmer, created = PendingFarmer.objects.update_or_create(
                username=username,
                defaults={
                    'phone': phone,
                    'password': make_password(password),
                    'recovery_answer': recovery_answer
                }
            )
            print(f"[DEBUG] PendingFarmer {'created' if created else 'updated'}")
            
            # Generate 6-digit OTP
            import random
            otp_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            print(f"[DEBUG] Generated OTP: {otp_code}")
            
            # Save OTP Record
            OTPRecord.objects.create(
                pending_user=pending_farmer,
                otp_code=otp_code,
                otp_type='mobile'
            )
            print(f"[DEBUG] OTPRecord saved")
            
            # Send SMS via Twilio
            from .services.twilio_service import twilio_service
            message = f"Your GreenLensAI registration OTP is: {otp_code}. Valid for 10 minutes."
            
            print(f"[DEBUG] Attempting to send SMS to {phone}...")
            if twilio_service.send_sms(phone, message):
                print(f"[DEBUG] Twilio SMS sent successfully")
                masked_phone = phone[:4] + "*" * (len(phone) - 7) + phone[-3:]
                resp_data = {
                    "message": f"OTP sent to your registered phone number {masked_phone}",
                    "farmer_id": pending_farmer.username
                }
                print(f"[DEBUG] Returning 200 success response: {resp_data}")
                return Response(resp_data, status=status.HTTP_200_OK)
            else:
                print(f"[DEBUG] Twilio SMS failed to send")
                # Check if it was because Twilio is unconfigured
                if not twilio_service.is_configured():
                    print(f"[DEBUG] Twilio NOT CONFIGURED. Bypassing for dev-mode.")
                    resp_data = {
                        "message": f"OTP sent to your registered phone number (Dev Mode: {phone})",
                        "farmer_id": pending_farmer.username,
                        "debug_info": "SMS sending bypassed in dev mode"
                    }
                    print(f"[DEBUG] Returning 200 dev-success response: {resp_data}")
                    return Response(resp_data, status=status.HTTP_200_OK)
                return Response({"error": "Failed to send OTP. Please try again later."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            import traceback
            print(f"[ERROR] RegisterView Exception: {str(e)}")
            print(traceback.format_exc())
            return Response({"error": f"Internal server error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VerifyRegistrationOTPView(views.APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        print(f"\n[DEBUG] VerifyRegistrationOTPView POST data: {request.data}")
        farmer_id = request.data.get('farmer_id')
        otp_code = request.data.get('otp_code')
        
        if not farmer_id or not otp_code:
            print(f"[DEBUG] Verification failed: Missing farmer_id or otp_code")
            return Response({"error": "farmer_id and otp_code are required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            pending_farmer = PendingFarmer.objects.get(username=farmer_id)
            from django.utils import timezone
            import datetime
            
            ten_mins_ago = timezone.now() - datetime.timedelta(minutes=10)
            print(f"[DEBUG] Checking OTP for {farmer_id} after {ten_mins_ago}")
            
            otp_record = OTPRecord.objects.filter(
                pending_user=pending_farmer, 
                otp_code=otp_code, 
                is_verified=False,
                created_at__gte=ten_mins_ago
            ).order_by('-created_at').first()
            
            if otp_record:
                print(f"[DEBUG] Valid OTP found. Creating Farmer.")
                otp_record.is_verified = True
                otp_record.save()
                
                # Create actual Farmer
                farmer = Farmer.objects.create(
                    username=pending_farmer.username,
                    phone=pending_farmer.phone,
                    password=pending_farmer.password,
                    recovery_answer=pending_farmer.recovery_answer
                )
                print(f"[DEBUG] Farmer '{farmer.username}' created successfully")
                
                # Delete pending farmer
                pending_farmer.delete()
                print(f"[DEBUG] PendingFarmer deleted")
                
                resp_data = {
                    "message": "Registration successful!",
                    "farmer_id": farmer.username
                }
                print(f"[DEBUG] Returning 201 success response: {resp_data}")
                return Response(resp_data, status=status.HTTP_201_CREATED)
            else:
                print(f"[DEBUG] OTP verification failed: Invalid or expired OTP")
                return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)
                
        except PendingFarmer.DoesNotExist:
            print(f"[DEBUG] OTP verification failed: PendingFarmer '{farmer_id}' not found")
            return Response({"error": "Pending registration not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            import traceback
            print(f"[ERROR] VerifyRegistrationOTPView Exception: {str(e)}")
            print(traceback.format_exc())
            return Response({"error": f"Internal server error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LoginView(views.APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        username = request.data.get('farmer_id') # Mapping farmer_id to username
        password = request.data.get('password')
        
        user = authenticate(username=username, password=password)
        
        if user is not None:
            django_login(request, user)
            return Response({
                "message": "Login successful",
                "farmer_id": user.username
            }, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid Farmer ID or password"}, status=status.HTTP_401_UNAUTHORIZED)

class HealthCheckView(views.APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({"status": "healthy"}, status=status.HTTP_200_OK)

class RecoverIDView(views.APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        phone = request.data.get('phone')
        recovery_answer = request.data.get('recovery_answer')
        
        if not phone or not recovery_answer:
            return Response({"error": "Phone and recovery answer are required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            # Check for answer match (case-insensitive)
            # Using contains for phone to handle potential country code formatting differences
            user = Farmer.objects.get(phone__contains=phone, recovery_answer__iexact=recovery_answer)
            return Response({
                "message": "ID recovered successfully",
                "farmer_id": user.username
            }, status=status.HTTP_200_OK)
        except Farmer.DoesNotExist:
            return Response({"error": "No matching farmer found with those details"}, status=status.HTTP_404_NOT_FOUND)


class RequestRecoveryOTPView(views.APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        farmer_id = request.data.get('farmer_id')
        if not farmer_id:
            return Response({"error": "farmer_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            farmer = Farmer.objects.get(username=farmer_id)
            if not farmer.phone:
                return Response({"error": "No phone number associated with this account"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Generate 6-digit OTP
            import random
            otp_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            
            # Save OTP Record
            from .models import OTPRecord
            OTPRecord.objects.create(
                user=farmer,
                otp_code=otp_code,
                otp_type='mobile'
            )
            
            # Send SMS via Twilio
            from .services.twilio_service import twilio_service
            message = f"Your GreenLensAI password recovery OTP is: {otp_code}. Valid for 10 minutes."
            if twilio_service.send_sms(farmer.phone, message):
                # Mask phone for security in response
                masked_phone = farmer.phone[:4] + "*" * (len(farmer.phone) - 7) + farmer.phone[-3:]
                return Response({
                    "message": f"OTP sent to your registered phone number {masked_phone}",
                    "farmer_id": farmer.username
                }, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Failed to send SMS. Please try again later."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Farmer.DoesNotExist:
            return Response({"error": "Farmer ID not found"}, status=status.HTTP_404_NOT_FOUND)

class VerifyRecoveryOTPView(views.APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        farmer_id = request.data.get('farmer_id')
        otp_code = request.data.get('otp_code')
        
        if not farmer_id or not otp_code:
            return Response({"error": "farmer_id and otp_code are required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            farmer = Farmer.objects.get(username=farmer_id)
            from .models import OTPRecord
            from django.utils import timezone
            import datetime
            
            # Get latest unverified OTP for this user within last 10 mins
            ten_mins_ago = timezone.now() - datetime.timedelta(minutes=10)
            otp_record = OTPRecord.objects.filter(
                user=farmer, 
                otp_code=otp_code, 
                is_verified=False,
                created_at__gte=ten_mins_ago
            ).order_by('-created_at').first()
            
            if otp_record:
                otp_record.is_verified = True
                otp_record.save()
                return Response({
                    "message": "OTP verified successfully",
                    "farmer_id": farmer.username
                }, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)
                
        except Farmer.DoesNotExist:
            return Response({"error": "Farmer ID not found"}, status=status.HTTP_404_NOT_FOUND)

class ResetPasswordView(views.APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        farmer_id = request.data.get('farmer_id')
        new_password = request.data.get('new_password')
        otp_code = request.data.get('otp_code')  # Replacing recovery_answer with otp_code
        
        if not all([farmer_id, new_password, otp_code]):
            return Response({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            farmer = Farmer.objects.get(username=farmer_id)
            from .models import OTPRecord
            from django.utils import timezone
            import datetime
            
            # Verify OTP record exists and was verified within last 15 mins
            fifteen_mins_ago = timezone.now() - datetime.timedelta(minutes=15)
            otp_verified = OTPRecord.objects.filter(
                user=farmer,
                otp_code=otp_code,
                is_verified=True,
                created_at__gte=fifteen_mins_ago
            ).exists()
            
            if otp_verified:
                farmer.set_password(new_password)
                farmer.save()
                return Response({"message": "Password reset successful"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Identity verification failed or OTP expired"}, status=status.HTTP_403_FORBIDDEN)
        except Farmer.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

class ConversationListView(views.APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, farmer_id):
        try:
            farmer = Farmer.objects.get(username=farmer_id)
            conversations = Conversation.objects.filter(farmer=farmer)
            serializer = ConversationSerializer(conversations, many=True)
            return Response(serializer.data)
        except Farmer.DoesNotExist:
            return Response({"error": "Farmer not found"}, status=status.HTTP_404_NOT_FOUND)

class ConversationDeleteView(views.APIView):
    permission_classes = [AllowAny]

    def delete(self, request, conversation_id):
        farmer_id = request.query_params.get('farmer_id')
        if not farmer_id:
            return Response({"error": "farmer_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            farmer = Farmer.objects.get(username=farmer_id)
            conversation = Conversation.objects.get(id=conversation_id, farmer=farmer)
            conversation.delete()  # Cascade deletes all ChatHistory messages
            return Response({"message": "Conversation deleted successfully"}, status=status.HTTP_200_OK)
        except Farmer.DoesNotExist:
            return Response({"error": "Farmer not found"}, status=status.HTTP_404_NOT_FOUND)
        except Conversation.DoesNotExist:
            return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)

class ChatHistoryView(views.APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, farmer_id):
        conversation_id = request.query_params.get('conversation_id')
        if conversation_id in ["null", "undefined", "", None]:
            conversation_id = None
            
        try:
            farmer = Farmer.objects.get(username=farmer_id)
            chats = ChatHistory.objects.filter(farmer=farmer)
            if conversation_id:
                chats = chats.filter(conversation_id=conversation_id)
            else:
                # If no conversation_id, maybe we want to show messages that don't have a conversation?
                # Or just return empty for a "New Chat" experience.
                # For compatibility, let's return all if no ID is specified, 
                # but the frontend will ideally specify it.
                pass
                
            serializer = ChatHistorySerializer(chats, many=True)
            return Response(serializer.data)
        except Farmer.DoesNotExist:
            return Response({"error": "Farmer not found"}, status=status.HTTP_404_NOT_FOUND)

class SaveMessageView(views.APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        farmer_id = request.data.get('farmer_id')
        try:
            farmer = Farmer.objects.get(username=farmer_id)
            data = request.data.copy()
            data['farmer'] = farmer.id
            serializer = ChatHistorySerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "id": serializer.data['id'],
                    "message": "Message saved successfully"
                }, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Farmer.DoesNotExist:
            return Response({"error": "Farmer not found"}, status=status.HTTP_404_NOT_FOUND)

class ChatView(views.APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        farmer_id = request.data.get('farmer_id')
        user_message = request.data.get('message')
        language = request.data.get('language', 'en')
        
        if not farmer_id or not user_message:
            return Response({"error": "farmer_id and message are required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            from .rag_service import rag_service
            from .services.agent_service import agent_service
            
            farmer = Farmer.objects.get(username=farmer_id)
            
            # --- Conversation Logic ---
            conversation_id = request.data.get('conversation_id')
            if conversation_id in ["null", "undefined", "", None]:
                conversation_id = None

            conversation = None
            if conversation_id:
                try:
                    conversation = Conversation.objects.get(id=conversation_id, farmer=farmer)
                except (Conversation.DoesNotExist, ValueError):
                    pass
            
            if not conversation:
                # Create a new conversation
                # Use first 30 chars of message as title
                title = user_message[:30] + "..." if len(user_message) > 30 else user_message
                conversation = Conversation.objects.create(farmer=farmer, title=title)
            
            # 1. Save user message to history
            ChatHistory.objects.create(
                farmer=farmer,
                conversation=conversation,
                message_type='user',
                content=user_message
            )
            
            # 2. Query RAG
            query_text = user_message
            if language != 'en':
                try:
                    query_text = agent_service.translate_to_english(user_message, language)
                    print(f"[DEBUG] Translated user query from '{user_message}' to '{query_text}'")
                except Exception as e:
                    print(f"[ERROR] Query translation failed: {e}")
            
            print(f"[DEBUG] Querying RAG with: '{query_text}'")
            solutions = rag_service.query(query_text)
            
            rag_context = ""
            if solutions:
                rag_context = solutions[0]['text'][:1000]
                print(f"[DEBUG] RAG found solution (first 100 chars): {rag_context[:100]}...")
            else:
                print(f"[DEBUG] No RAG solutions found, using conversational bot logic.")

            # 3. Generate conversational response in user's preferred language
            print(f"[DEBUG] Generating chat response in language: {language}")
            translated_response = agent_service.generate_chat_response(query_text, rag_context, language)
            print(f"[DEBUG] Final translated response (first 100 chars): {translated_response[:100]}...")
            
            # 4. Save bot message to history
            ChatHistory.objects.create(
                farmer=farmer,
                conversation=conversation,
                message_type='bot',
                content=translated_response
            )
            
            return Response({
                "farmer_id": farmer_id,
                "conversation_id": conversation.id,
                "conversation_title": conversation.title,
                "response": translated_response
            }, status=status.HTTP_200_OK)
            
        except Farmer.DoesNotExist:
            return Response({"error": "Farmer not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            import traceback
            print(f"\n[ERROR] ChatView Exception: {str(e)}")
            print(traceback.format_exc())
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PredictImageView(views.APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        farmer_id = request.data.get('farmer_id')
        file = request.FILES.get('file')
        
        if not farmer_id or not file:
            return Response({"error": "farmer_id and file are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from .models import TreatmentPlan, TreatmentDay, Conversation
            from .services.agent_service import agent_service
            from .services.twilio_service import twilio_service
            
            farmer = Farmer.objects.get(username=farmer_id)
            
            # --- Conversation Logic ---
            conversation_id = request.data.get('conversation_id')
            if conversation_id in ["null", "undefined", "", None]:
                conversation_id = None

            conversation = None
            if conversation_id:
                try:
                    conversation = Conversation.objects.get(id=conversation_id, farmer=farmer)
                except (Conversation.DoesNotExist, ValueError):
                    pass
            
            if not conversation:
                title = f"Photo Diagnosis: {file.name[:20]}"
                conversation = Conversation.objects.create(farmer=farmer, title=title)

            # Save file
            file_name = f"{uuid.uuid4()}_{file.name}"
            file_path = default_storage.save(os.path.join('uploads', file_name), ContentFile(file.read()))
            full_file_path = os.path.join(settings.MEDIA_ROOT, file_path)
            
            # Predict
            result = predict_image(full_file_path)
            prediction = result['prediction']
            
            # Check for active TreatmentPlan
            active_plan = TreatmentPlan.objects.filter(farmer=farmer, is_active=True).first()
            
            # Integrate RAG for Disease Solution (needed for new plans or info)
            from .rag_service import rag_service
            solutions = rag_service.query(f"What is the treatment and solution for {prediction} in crops?")
            
            solution_text = "\n\n**Solution from Expert Guide:**\n"
            if solutions:
                solution_text += "\n".join([f"• {res['text'][:500]}..." for res in solutions[:2]])
            else:
                solution_text += "Consult an agriculture expert for detailed treatment."

            # ----- Agentic AI Logic Start -----
            if active_plan:
                if prediction.lower() == "healthy":
                    active_plan.is_active = False
                    active_plan.save()
                    msg = "Congratulations! Your crop leaf is now healthy. The treatment plan is complete."
                    translated = agent_service.translate_message(msg, farmer.language_preference)
                    twilio_service.send_sms(farmer.phone, translated)
                else:
                    # Increment day and send next treatment
                    # Verify the photo for the current day
                    current_day_step = TreatmentDay.objects.filter(plan=active_plan, day_number=active_plan.current_day).first()
                    if current_day_step:
                        current_day_step.farmer_photo_verified = True
                        current_day_step.save()
                    
                    # Move to next day
                    next_day_num = active_plan.current_day + 1
                    next_day_step = TreatmentDay.objects.filter(plan=active_plan, day_number=next_day_num).first()
                    
                    if next_day_step:
                        active_plan.current_day = next_day_num
                        active_plan.save()
                        
                        prompt = agent_service.generate_daily_prompt(
                            disease_name=prediction,
                            day_number=next_day_num,
                            treatment_step=next_day_step.treatment_text,
                            language=farmer.language_preference,
                            is_first_day=False
                        )
                        twilio_service.send_sms(farmer.phone, prompt)
                        
                        next_day_step.sent_to_farmer = True
                        next_day_step.save()
                    else:
                        # No more steps but still not healthy? 
                        # Ask for another check or restart/extend
                        msg = f"We have reached the end of the initial plan, but {prediction} is still detected. Please continue the previous treatment or consult an expert."
                        translated = agent_service.translate_message(msg, farmer.language_preference)
                        twilio_service.send_sms(farmer.phone, translated)
            
            elif prediction.lower() != "healthy":
                # Create a NEW TreatmentPlan
                plan = TreatmentPlan.objects.create(
                    farmer=farmer,
                    disease_name=prediction,
                    current_day=1
                )
                
                rag_output_for_plan = "\n".join([res['text'] for res in solutions]) if solutions else "Consult an agriculture expert."
                days_content = agent_service.parse_rag_solution_into_days(rag_output_for_plan)
                
                for i, content in enumerate(days_content):
                    TreatmentDay.objects.create(
                        plan=plan,
                        day_number=i+1,
                        treatment_text=content
                    )
                
                # Send Day 1 SMS
                day1_treatment = TreatmentDay.objects.filter(plan=plan, day_number=1).first()
                if day1_treatment and farmer.phone:
                    prompt = agent_service.generate_daily_prompt(
                        disease_name=prediction,
                        day_number=1,
                        treatment_step=day1_treatment.treatment_text,
                        language=farmer.language_preference,
                        is_first_day=True
                    )
                    twilio_service.send_sms(farmer.phone, prompt)
                    
                    day1_treatment.sent_to_farmer = True
                    day1_treatment.save()
            # ----- Agentic AI Logic End -----

            # Save to history
            ChatHistory.objects.create(
                farmer=farmer,
                conversation=conversation,
                message_type='user',
                content=f"Uploaded an image for diagnosis: {file.name}",
                image_path=file_path
            )
            
            # Generate a conversational LLM response with disease name + solution
            rag_context = ""
            if solutions:
                rag_context = "\n".join([res['text'][:500] for res in solutions[:2]])
            
            language = farmer.language_preference or 'en'
            diagnosis_prompt = (
                f"The CNN model detected: {prediction} with {result['confidence']:.2%} confidence.\n"
                f"RAG Solution:\n{rag_context}" if rag_context else 
                f"The CNN model detected: {prediction} with {result['confidence']:.2%} confidence."
            )
            bot_response = agent_service.generate_chat_response(
                diagnosis_prompt, rag_context, language
            )
            
            ChatHistory.objects.create(
                farmer=farmer,
                conversation=conversation,
                message_type='bot',
                content=bot_response
            )
            
            return Response({
                "farmer_id": farmer_id,
                "conversation_id": conversation.id,
                "prediction": prediction,
                "confidence": result["confidence"],
                "bot_response": bot_response,
                "image_url": file_path
            })
            
        except Farmer.DoesNotExist:
            return Response({"error": "Farmer not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            import traceback
            print(f"\n[ERROR] PredictImageView Exception: {str(e)}")
            print(traceback.format_exc())
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
