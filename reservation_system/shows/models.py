from django.db import models

# Create your models here.

class User(models.Model):
    USER_TYPES = [
        ('spectator', 'Spectator'),
        ('admin', 'Administrator'),
        ('organizer', 'Organizer'),
    ]
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPES)
    password = models.CharField(max_length=128)  # In reality, use Django's built-in User model

class Show(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateTimeField()
    location = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)

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
