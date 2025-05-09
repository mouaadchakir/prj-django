from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
    USER_TYPES = [
        ('spectator', 'Spectator'),
        ('admin', 'Administrator'),
        ('organizer', 'Organizer'),
    ]
    # username, email, password, last_login are inherited from AbstractUser
    # first_name, last_name, is_staff, is_active, is_superuser, date_joined are also inherited
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='spectator') # Added a default

    # Add any other custom fields you need here

    def __str__(self):
        return self.username

class Show(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=500)
    image = models.ImageField(upload_to='show_images/', null=True, blank=True) # Added image field
    date = models.DateTimeField()
    location = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.title

class Seat(models.Model):
    show = models.ForeignKey(Show, on_delete=models.CASCADE)
    seat_number = models.CharField(max_length=10)
    is_reserved = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.show.title} - Seat {self.seat_number}"

class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    show = models.ForeignKey(Show, on_delete=models.CASCADE)
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    reservation_date = models.DateTimeField(auto_now_add=True)
    payment_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return f"Reservation for {self.user.username} at {self.show.title} - Seat {self.seat.seat_number}"
