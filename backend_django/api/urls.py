from django.urls import path
from .views import (
    RegisterView, VerifyRegistrationOTPView, LoginView, 
    ChatHistoryView, SaveMessageView, PredictImageView,
    RecoverIDView, RequestRecoveryOTPView, VerifyRecoveryOTPView, ResetPasswordView,
    HealthCheckView, ChatView, ConversationListView, ConversationDeleteView
)
from .admin_views import IndexPdfView, UserListView, UserDeleteView, IndexedPdfsView

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/verify-registration-otp/', VerifyRegistrationOTPView.as_view(), name='verify-registration-otp'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('auth/recover-id/', RecoverIDView.as_view(), name='recover-id'),
    path('auth/request-recovery-otp/', RequestRecoveryOTPView.as_view(), name='request-recovery-otp'),
    path('auth/verify-recovery-otp/', VerifyRecoveryOTPView.as_view(), name='verify-recovery-otp'),
    path('auth/reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('chat/conversations/<str:farmer_id>/', ConversationListView.as_view(), name='conversation-list'),
    path('chat/conversations/<int:conversation_id>/delete/', ConversationDeleteView.as_view(), name='conversation-delete'),
    path('chat/history/<str:farmer_id>/', ChatHistoryView.as_view(), name='chat-history'),
    path('chat/save/', SaveMessageView.as_view(), name='save-message'),
    path('chat/ask/', ChatView.as_view(), name='chat-ask'),
    path('image/predict/', PredictImageView.as_view(), name='predict-image'),
    
    # RAG Admin
    path('admin/index-pdf/', IndexPdfView.as_view(), name='index-pdf'),
    path('admin/indexed-pdfs/', IndexedPdfsView.as_view(), name='indexed-pdfs'),
    path('admin/indexed-pdfs/<str:filename>/', IndexedPdfsView.as_view(), name='delete-indexed-pdf'),
    path('admin/users/', UserListView.as_view(), name='admin-users'),
    path('admin/users/delete/<str:username>/', UserDeleteView.as_view(), name='admin-delete-user'),
]
