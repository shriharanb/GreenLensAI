import PyPDF2
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny # Update to IsAdminUser if needed later
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .models import Farmer
from .serializers import FarmerSerializer
from .rag_service import rag_service
import logging

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class UserDeleteView(views.APIView):
    permission_classes = [AllowAny] # Using AllowAny for current development ease

    def delete(self, request, username):
        logger.info(f"Admin attempt to delete user: {username}")
        try:
            user = Farmer.objects.get(username=username)
            if user.is_staff:
                logger.warning(f"Prevented deletion of admin user: {username}")
                return Response({"error": "Cannot delete admin users"}, status=status.HTTP_403_FORBIDDEN)
            user_id = user.id
            user.delete()
            logger.info(f"Successfully deleted user: {username} (ID: {user_id})")
            return Response({"message": f"User {username} deleted successfully"}, status=status.HTTP_200_OK)
        except Farmer.DoesNotExist:
            logger.error(f"User not found for deletion: {username}")
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(f"Unexpected error deleting user {username}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserListView(views.APIView):
    permission_classes = [AllowAny] # Using AllowAny for current development ease

    def get(self, request):
        try:
            farmers = Farmer.objects.all().order_by('-date_joined')
            serializer = FarmerSerializer(farmers, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(csrf_exempt, name='dispatch')
class IndexPdfView(views.APIView):
    permission_classes = [AllowAny] # Using AllowAny for current development ease

    def post(self, request):
        pdf_file = request.FILES.get('pdf')
        if not pdf_file:
            return Response({"error": "No PDF file provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            reader = PyPDF2.PdfReader(pdf_file)
            chunks = []
            metadata_list = []
            
            # Improved chunking: split text into overlapping chunks
            CHUNK_SIZE = 1000
            CHUNK_OVERLAP = 200
            
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if not text or not text.strip():
                    continue
                
                # Split page text into smaller chunks
                page_text = text.strip()
                start = 0
                while start < len(page_text):
                    end = start + CHUNK_SIZE
                    chunk = page_text[start:end]
                    
                    chunks.append(chunk)
                    metadata_list.append({
                        "source": pdf_file.name,
                        "page": i + 1,
                        "chunk_index": len(chunks)
                    })
                    
                    # Move start forward by (size - overlap), but at least 1
                    start += (CHUNK_SIZE - CHUNK_OVERLAP)

            if not chunks:
                return Response({"error": "No text could be extracted from the PDF"}, status=status.HTTP_400_BAD_REQUEST)

            rag_service.upsert_chunks(chunks, metadata_list)
            
            logger.info(f"Successfully processed {pdf_file.name}: {len(chunks)} chunks from {len(reader.pages)} pages.")
            return Response({
                "message": f"Successfully processed {pdf_file.name}",
                "pages_count": len(reader.pages),
                "chunks_count": len(chunks)
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class IndexedPdfsView(views.APIView):
    permission_classes = [AllowAny] # Using AllowAny for current development ease

    def get(self, request):
        try:
            sources = rag_service.get_all_sources()
            return Response({"pdfs": sources}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    def delete(self, request, filename):
        try:
            success = rag_service.delete_by_source(filename)
            if success:
                return Response({"message": f"Successfully deleted {filename}"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": f"Failed to delete {filename}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
