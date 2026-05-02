from django import forms

from . import models
      
from .models import Contact


class BloodForm(forms.ModelForm):
    class Meta:
        model=models.Stock
        fields=['bloodgroup','unit']

class RequestForm(forms.ModelForm):
    class Meta:
        model=models.BloodRequest
        fields=['patient_name','patient_age','reason','bloodgroup','unit']




class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'email', 'phone', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class':'form-control', 'placeholder':'Enter your name'}),
            'email': forms.EmailInput(attrs={'class':'form-control', 'placeholder':'Enter your email'}),
            'phone': forms.TextInput(attrs={'class':'form-control', 'placeholder':'Enter phone number'}),
            'message': forms.Textarea(attrs={'class':'form-control', 'rows':4, 'placeholder':'Write your message'}),
        }
