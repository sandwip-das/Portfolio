from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.contrib import messages
from allauth.exceptions import ImmediateHttpResponse

User = get_user_model()


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom account adapter — no custom behaviour needed for standard accounts.
    """
    pass


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    For social (e.g. Google) logins:
    - Uses the Google account's username/local part of email as the Django username.
    - The user can edit their username later from the profile page.
    """

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)

        # Try to get a good username from Google profile info
        extra_data = sociallogin.account.extra_data
        # Google provides 'given_name', 'family_name', and 'email'
        given_name = extra_data.get('given_name', '')
        family_name = extra_data.get('family_name', '')
        email = extra_data.get('email', '')

        if given_name:
            base_username = given_name
            if family_name:
                base_username = f"{given_name}{family_name}"
        elif extra_data.get('name'):
            base_username = extra_data.get('name')
        elif email:
            # Fall back to using the part before @
            base_username = email.split('@')[0]
        else:
            base_username = 'user'

        # Remove spaces to keep username clean
        base_username = base_username.replace(' ', '')

        # Ensure uniqueness
        final_username = base_username
        counter = 1
        while User.objects.filter(username=final_username).exists():
            final_username = f"{base_username}{counter}"
            counter += 1

        user.username = final_username
        # Clear first/last name so only username is used (as per requirement)
        user.first_name = ''
        user.last_name = ''
        return user

    def pre_social_login(self, request, sociallogin):
        # Email from social account profile
        email = sociallogin.user.email
        if not email:
            return

        # Check if the social account is already linked to an existing user
        # is_existing means 'is this specific social account already in the SocialAccount table?'
        if not sociallogin.is_existing:
            user_exists = User.objects.filter(email=email).exists()
            # Determine if this originates from the signup or login page
            is_signup = 'signup' in request.path
            is_login = 'login' in request.path

            if is_signup and user_exists:
                # Signup: Block if email already taken
                messages.error(request, "The email ID already exists. Please try with another email ID.")
                raise ImmediateHttpResponse(redirect('account_signup'))
            
            elif is_login and not user_exists:
                # Login: Block if no account exists for this browser's email
                messages.error(request, "Login to the browser with your provided gmail account. Or sign up by creating an account.")
                raise ImmediateHttpResponse(redirect('account_login'))

    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        """
        Invoked when a social login fails or is cancelled by the user.
        Redirects back to the signup page with a message instead of showing a white error page.
        """
        messages.error(request, "Registration Not Completed")
        raise ImmediateHttpResponse(redirect('account_signup'))
