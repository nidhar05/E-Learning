from django.urls import path
from .views import (
    EnrollView,
    EnrollDetailView,
    SubscriptionPaymentOrderCreateView,
    SubscriptionPaymentVerifyView,
)

urlpatterns = [
    path('enroll/<int:course_id>/', EnrollView.as_view(), name='enroll'),
    path('payments/create-order/<int:course_id>/', SubscriptionPaymentOrderCreateView.as_view(), name='subscription-payment-create-order'),
    path('payments/verify/<int:course_id>/', SubscriptionPaymentVerifyView.as_view(), name='subscription-payment-verify'),
    path('', EnrollDetailView.as_view(), name='enrollment-detail'),
]
