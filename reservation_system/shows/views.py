from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.utils import timezone
from .models import User, Show, Reservation
from .forms import UserForm, ShowForm
import stripe
from django.conf import settings
from django.core.mail import send_mail

stripe.api_key = settings.STRIPE_SECRET_KEY

# Create your views here.

class UserListView(View):
    def get(self, request):
        users = User.objects.all()
        return render(request, 'shows/user_list.html', {'users': users})

class UserCreateView(View):
    def get(self, request):
        form = UserForm()
        return render(request, 'shows/user_form.html', {'form': form})

    def post(self, request):
        form = UserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('user_list')
        return render(request, 'shows/user_form.html', {'form': form})

class ShowListView(View):
    def get(self, request):
        shows = Show.objects.all()  # Temporarily show all shows
        return render(request, 'shows/show_list.html', {'shows': shows})

class ShowDetailView(View):
    def get(self, request, pk):
        show = get_object_or_404(Show, pk=pk)
        return render(request, 'shows/show_detail.html', {'show': show})

class ShowCreateView(View):
    def get(self, request):
        form = ShowForm()
        return render(request, 'shows/show_form.html', {'form': form})

    def post(self, request):
        form = ShowForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('show_list')
        return render(request, 'shows/show_form.html', {'form': form})

class ReservationCreateView(View):
    def get(self, request, pk):
        show = get_object_or_404(Show, pk=pk)
        return render(request, 'shows/reservation_form.html', {'show': show})

    def post(self, request, pk):
        show = get_object_or_404(Show, pk=pk)
        seat_number = request.POST.get('seat_number')
        # Logic for creating a reservation
        # Send confirmation email
        send_mail(
            'Reservation Confirmation',
            f'Your reservation for {show.title} on {show.date} has been confirmed. Seat number: {seat_number}.',
            'webmaster@example.com',
            [request.user.email],
            fail_silently=False,
        )
        return redirect('show_list')

class PaymentPageView(View):
    def get(self, request, pk):
        show = get_object_or_404(Show, pk=pk)
        return render(request, 'shows/payment_page.html', {'show': show, 'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY})

class PaymentView(View):
    def post(self, request, pk):
        show = get_object_or_404(Show, pk=pk)
        token = request.POST.get('stripeToken')
        try:
            charge = stripe.Charge.create(
                amount=int(show.price * 100),  # Stripe amount is in cents
                currency='usd',
                description=f'Reservation for {show.title}',
                source=token,
            )
            # Logic to mark reservation as paid
            return redirect('show_list')
        except stripe.error.StripeError as e:
            # Instead of redirecting to payment_error, render the payment page with an error message
            return render(request, 'shows/payment_page.html', {
                'show': show,
                'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY,
                'error_message': str(e)
            })

class PaymentErrorView(View):
    def get(self, request):
        return render(request, 'shows/payment_error.html')
