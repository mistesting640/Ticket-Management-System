from django import forms
from .models import Ticket


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = [
            'ticket_type',
            'raised_by_name',
            'shop_no',
            'department',
            'sub_category',
            'priority',
            'title',
            'description'
        ]

        widgets = {
            'ticket_type': forms.Select(
                attrs={'class': 'form-select'}
            ),
            'department': forms.Select(
                attrs={'class': 'form-select'}
            ),
            'sub_category': forms.Select(
                attrs={'class': 'form-select'}
            ),
            'priority': forms.Select(
                attrs={'class': 'form-select'}
            ),
            'raised_by_name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter person name'
                }
            ),
            'shop_no': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter shop number'
                }
            ),
            'title': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter ticket title'
                }
            ),
            'description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Describe the issue in detail'
                }
            ),
        }
