from django.db import models
import uuid
from django.contrib.auth.models import User

class Wishlist(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlists')
    title = models.CharField(max_length=200, verbose_name='title')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title}, owned by {self.owner.username}"
    
class Item(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')

    name = models.CharField(max_length=200, verbose_name='name')
    description = models.TextField(blank=True, null=True ,verbose_name='description')
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name='price')
    shop_url = models.URLField(max_length=500, blank=True, null=True, verbose_name='shop url')
    image = models.ImageField(upload_to='wishlist_images/', blank=True, null=True, verbose_name="image")
    is_reserved = models.BooleanField(default=False, verbose_name="is reserved")
    reserved_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="reserved by")

    def __str__(self):
        return self.name

