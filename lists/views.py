from django.shortcuts import render, redirect, get_object_or_404
from lists.services.product_image import fetch_product_image_file
from .forms import SimpleRegistrationForm, WishlistForm, ItemForm, ReserveItemForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .models import Wishlist, Item
from django.db import transaction
from django.db.models import F



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
            return redirect('home')
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
    sort = request.GET.get('sort')
    items = wishlist.items.all()

    if sort == 'price_asc':
        items = items.order_by(F('price').asc(nulls_last=True), 'name')
    elif sort == 'price_desc':
        items = items.order_by(F('price').desc(nulls_last=True), 'name')

    return render(request, 'wishlist_detail.html', {
        'wishlist': wishlist,
        'items': items,
        'sort': sort,
    })

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
            
            image_file = fetch_product_image_file(item.shop_url)
            if image_file:
                item.image.save(image_file.name, image_file, save=False)

            item.save()
            return redirect('wishlist_detail', pk=pk)
    else:
        form = ItemForm()
    
    return render(request, 'add_item.html', {'form': form, 'wishlist': wishlist})

def reserve_item(request, item_id):
    item = get_object_or_404(Item.objects.select_related("wishlist"), id=item_id)

    if item.is_reserved:
        return redirect("wishlist_detail", pk=item.wishlist.pk)

    if request.method == "POST":
        form = ReserveItemForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                item = (
                    Item.objects
                    .select_related("wishlist")
                    .select_for_update()
                    .get(id=item_id)
                )

                if item.is_reserved:
                    form.add_error(None, "Цей подарунок уже заброньовано.")
                else:
                    item.is_reserved = True
                    item.reserved_by = form.cleaned_data["reserver_name"]
                    item.save(update_fields=["is_reserved", "reserved_by"])
                    return redirect("wishlist_detail", pk=item.wishlist.pk)
    else:
        form = ReserveItemForm()

    return render(request, "reserve_item.html", {
        "item": item,
        "form": form,
    })


@login_required
def delete_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    wishlist_pk = item.wishlist.pk

    if item.wishlist.owner == request.user:
        if request.method == 'POST':
            item.delete()
            
    return redirect('wishlist_detail', pk=wishlist_pk)

@login_required
def edit_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)

    if item.wishlist.owner != request.user:
        return redirect('dashboard')

    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            return redirect('wishlist_detail', pk=item.wishlist.pk)
    else:
        form = ItemForm(instance=item)

    return render(request, 'add_item.html', {
        'form': form,
        'wishlist': item.wishlist,
        'item': item,
        'is_edit': True,
    })

@login_required
def delete_wishlist(request, pk):
    wishlist = get_object_or_404(Wishlist, pk=pk)
    if wishlist.owner != request.user:
        return redirect('dashboard')
    
    if request.method == 'POST':
        wishlist.delete()
        return redirect('dashboard')

    return redirect('dashboard')
