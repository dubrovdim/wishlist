from django import forms
from .models import Wishlist, Item

class WishlistForm(forms.ModelForm):
    class Meta:
        model = Wishlist
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'На день народження...'
            })
        }

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        # Додали поле 'image' в список
        fields = ['name', 'description', 'price', 'shop_url', 'image'] 
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Наприклад: Навушники Sony'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Колір чорний, бажано з цієї серії...'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Наприклад: 1500.50'}),
            'shop_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            # Додали віджет для файлу
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }