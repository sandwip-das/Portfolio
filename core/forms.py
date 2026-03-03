from django import forms
from .models import ServiceBooking, ContactMessage, Review

TIME_CHOICES = [('', 'Select Time')] + [
    (f"{h % 24:02d}:{m:02d}", f"{12 if h % 12 == 0 else h % 12:d}:{m:02d} {'AM' if h < 12 or h == 24 else 'PM'}")
    for h in range(9, 25)
    for m in (0, 30)
    if not (h == 24 and m == 30)
]

class StyledFormMixin:
    """Mixin to apply common styling to form fields."""
    common_class = 'w-full bg-white/5 border border-white/20 rounded-lg px-4 py-1.5 text-white placeholder:text-gray-500 placeholder:text-xs placeholder:italic focus:outline-none focus:border-primary transition text-sm'
    
    def apply_styling(self):
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.EmailInput, forms.DateInput, forms.Textarea, forms.Select, forms.ChoiceField)):
                existing_class = field.widget.attrs.get('class', '')
                if not existing_class:
                    field.widget.attrs['class'] = self.common_class
                elif 'w-full' not in existing_class:
                     field.widget.attrs['class'] = f"{self.common_class} {existing_class}"

class ServiceBookingForm(StyledFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styling()
        # Specific overrides for HTML5 pickers
        picker_style = 'color-scheme: dark;'
        self.fields['date_from'].widget = forms.DateInput(attrs={'type': 'date', 'style': picker_style, 'class': self.common_class.replace('px-4', 'px-2')})
        self.fields['date_to'].widget = forms.DateInput(attrs={'type': 'date', 'style': picker_style, 'class': self.common_class.replace('px-4', 'px-2')})
        self.fields['time_from'].widget = forms.TimeInput(attrs={'type': 'time', 'style': picker_style, 'class': self.common_class.replace('px-4', 'px-2')})
        self.fields['time_to'].widget = forms.TimeInput(attrs={'type': 'time', 'style': picker_style, 'class': self.common_class.replace('px-4', 'px-2')})
        self.apply_styling()

    class Meta:
        model = ServiceBooking
        fields = ['name', 'phone', 'email', 'date_from', 'date_to', 'time_from', 'time_to', 'additional_message']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Your Full Name'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Your Phone Number'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Your Email Address'}),
            'additional_message': forms.Textarea(attrs={'placeholder': 'Additional Message', 'rows': 2}),
        }

class ContactForm(StyledFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styling()

    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Phone Number'}),
            'subject': forms.TextInput(attrs={'placeholder': 'Topic'}),
            'message': forms.Textarea(attrs={'placeholder': 'Message', 'rows': 4}),
        }

class ReviewForm(StyledFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styling()

    class Meta:
        model = Review
        fields = ['name', 'email', 'profession', 'location', 'picture', 'rating', 'comment']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Your Name', 'maxlength': '50'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Your Email'}),
            'profession': forms.TextInput(attrs={'placeholder': 'Profession/ Company Name', 'maxlength': '50'}),
            'location': forms.TextInput(attrs={'placeholder': 'Location/Address', 'maxlength': '50'}),
            'picture': forms.FileInput(attrs={'class': 'w-full bg-white/5 border border-white/20 rounded-lg px-4 py-1 text-white focus:outline-none focus:border-primary transition text-sm'}),
            'rating': forms.HiddenInput(),
            'comment': forms.Textarea(attrs={'placeholder': 'Short comment', 'rows': 2, 'maxlength': '70'}),
        }
