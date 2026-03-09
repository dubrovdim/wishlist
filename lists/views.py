from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .models import Wishlist, Item
from .forms import WishlistForm, ItemForm

# Головна сторінка
def home(request):
    return render(request, 'home.html')

# Реєстрація
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home') # Повертаємо на головну сторінку
    else:
        form = UserCreationForm()
    
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
        form = ItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.wishlist = wishlist
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