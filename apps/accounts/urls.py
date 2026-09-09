from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import StyledAuthenticationForm, StyledPasswordResetForm, StyledSetPasswordForm

app_name = 'accounts'

urlpatterns = [
    path('inscription/', views.SignUpView.as_view(), name='signup'),
    path('connexion/', auth_views.LoginView.as_view(
        template_name='accounts/login.html', authentication_form=StyledAuthenticationForm
    ), name='login'),
    path('deconnexion/', auth_views.LogoutView.as_view(), name='logout'),
    path('profil/', views.profile_view, name='profile'),

    path('mot-de-passe/reinitialiser/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset.html',
        email_template_name='accounts/password_reset_email.html',
        subject_template_name='accounts/password_reset_subject.txt',
        form_class=StyledPasswordResetForm,
    ), name='password_reset'),
    path('mot-de-passe/envoye/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    ), name='password_reset_done'),
    path('mot-de-passe/confirmer/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
        form_class=StyledSetPasswordForm,
    ), name='password_reset_confirm'),
    path('mot-de-passe/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ), name='password_reset_complete'),
]
