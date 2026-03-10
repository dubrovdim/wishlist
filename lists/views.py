from django.shortcuts import render, redirect, get_object_or_404
from .forms import SimpleRegistrationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .models import Wishlist, Item
from .forms import WishlistForm, ItemForm
import requests
from bs4 import BeautifulSoup
from django.core.files.base import ContentFile
from io import BytesIO
from PIL import Image

# Головна сторінка
def home(request):
    return render(request, 'home.html')

# Реєстрація
def register(request):
    if request.method == 'POST':
        form = SimpleRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home') # Повертаємо на головну сторінку
    else:
        form = SimpleRegistrationForm()
    
    return render(request, 'register.html', {'form': form})

@login_required
def dashboard(request):
    user_wishlists = Wishlist.objects.filter(owner=request.user).order_by('-created_at')
    
    return render(request, 'dashboard.html', {'wishlists': user_wishlists})

@login_required
def create_wishlist(request):
    if request.method == 'POST':
        form = WishlistForm(request.POST)
        if form.is_valid():
            wishlist = form.save(commit=False)
            wishlist.owner = request.user
            wishlist.save()
            return redirect('dashboard')
    else:
        form = WishlistForm()    
    
    return render(request, 'create_wishlist.html', {'form': form})

def wishlist_detail(request, pk):
    wishlist = get_object_or_404(Wishlist, pk=pk)
    return render(request, 'wishlist_detail.html', {'wishlist': wishlist})

@login_required
def add_item(request, pk):
    wishlist = get_object_or_404(Wishlist, pk=pk)
    if wishlist.owner != request.user:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.wishlist = wishlist
            
            if item.shop_url:
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                        'Accept-Language': 'uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7',
                    }
                    response = requests.get(item.shop_url, headers=headers, timeout=5)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        og_image = soup.find('meta', property='og:image')
                        if og_image and og_image.get('content'):
                            img_url = og_image['content']
                            img_response = requests.get(img_url, headers=headers, timeout=5)
                            
                            if img_response.status_code == 200:
                                img = Image.open(BytesIO(img_response.content))
                                
                                if img.mode != 'RGB':
                                    img = img.convert('RGB')
                                    
                                img.thumbnail((600, 600))
                                
                        
                                buffer = BytesIO()
                                img.save(buffer, format="JPEG", quality=80)
                                    
                                item.image.save('product.jpg', ContentFile(buffer.getvalue()), save=False)
                except Exception:
                    pass
            
            item.save()
            return redirect('wishlist_detail', pk=pk)
    else:
        form = ItemForm()
    
    return render(request, 'add_item.html', {'form': form, 'wishlist': wishlist})

def reserve_item(request, item_id):
    # Знаходимо конкретний подарунок
    item = get_object_or_404(Item, id=item_id)
    
    # Якщо його вже хтось забронював раніше, просто повертаємо назад у список
    if item.is_reserved:
        return redirect('wishlist_detail', pk=item.wishlist.pk)

    if request.method == 'POST':
        # Отримуємо ім'я з форми (яку ми зараз створимо)
        reserver_name = request.POST.get('reserver_name')
        
        if reserver_name:
            item.is_reserved = True
            item.reserved_by = reserver_name
            item.save()
            return redirect('wishlist_detail', pk=item.wishlist.pk)

    return render(request, 'reserve_item.html', {'item': item})

@login_required
def delete_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    wishlist_pk = item.wishlist.pk

    if item.wishlist.owner == request.user:
        if request.method == 'POST':
            item.delete()
            
    return redirect('wishlist_detail', pk=wishlist_pk)