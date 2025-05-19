from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.utils import timezone
from .models import User, Show, Reservation, Seat
from .forms import CustomUserCreationForm, ShowForm, UserProfileForm
import stripe
import random
import string
import datetime
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponseNotAllowed, HttpResponse
from functools import wraps
from django.db.models import Q
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.hashers import make_password, check_password

# Pour la génération des PDF
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO

stripe.api_key = settings.STRIPE_SECRET_KEY

# Decorator to check if user is staff
def staff_required(view_func):
    decorated_view_func = login_required(user_passes_test(lambda u: u.is_staff)(view_func))
    return decorated_view_func

def staff_required_debug(view_func):
    @wraps(view_func) # Important for preserving view metadata
    def _wrapped_view(request, *args, **kwargs):
        print(f"[staff_required_debug] Attempting to access: {request.path}")
        print(f"[staff_required_debug] Checking user: {request.user}")
        if not request.user.is_authenticated:
            print(f"[staff_required_debug] User not authenticated. LOGIN_URL is no longer available. Returning 403.")
            # Previously: return redirect(settings.LOGIN_URL)
            return HttpResponseForbidden("Access Denied: You must be authenticated to view this page.")
        if not request.user.is_staff:
            print(f"[staff_required_debug] User {request.user} is AUTHENTICATED but NOT staff. Permission denied.")
            return HttpResponseForbidden("Access Denied: You must be a staff member to view this page.")
        print(f"[staff_required_debug] User {request.user} is staff. Access granted.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# Create your views here.

class UserListView(View):
    def get(self, request):
        users = User.objects.all()
        return render(request, 'shows/user_list.html', {'users': users})

class UserCreateView(View):
    def get(self, request):
        form = CustomUserCreationForm()
        return render(request, 'registration/register.html', {'form': form})

    def post(self, request):
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login') # Assurez-vous que l'URL 'login' est définie
        return render(request, 'registration/register.html', {'form': form})

# Remove login_required decorator to make ShowListView public
from django.views.generic import ListView, DetailView, CreateView, UpdateView

class LoginView(View):
    def get(self, request):
        return render(request, 'registration/login.html')

    def post(self, request):
        username_or_email = request.POST.get('username_or_email')
        password = request.POST.get('password')
        error_message = None

        try:
            user = None
            if '@' in username_or_email:
                user = User.objects.get(email=username_or_email)
            else:
                user = User.objects.get(username=username_or_email)

            if user and check_password(password, user.password):
                auth_login(request, user) # Gère la session pour l'utilisateur
                
                # Redirection basée sur user_type
                if user.user_type == 'admin' or user.user_type == 'organizer':
                    return redirect('admin_show_list') 
                else: # 'spectator'
                    return redirect('show_list') 
            else:
                error_message = "Nom d'utilisateur/email ou mot de passe incorrect."
        except User.DoesNotExist:
            error_message = "Nom d'utilisateur/email ou mot de passe incorrect."
        
        return render(request, 'registration/login.html', {'error_message': error_message, 'username_or_email': username_or_email})

@method_decorator(login_required, name='dispatch')
class ShowListView(ListView):
    model = Show
    template_name = 'shows/show_list.html'
    context_object_name = 'shows'

    def get_queryset(self):
        queryset = super().get_queryset().order_by('date') # Get the original queryset
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(location__icontains=query)
            ).distinct() # Use distinct() if your OR conditions might lead to duplicates
        return queryset

@method_decorator(staff_required, name='dispatch')
class AdminShowListView(ListView):
    model = Show
    template_name = 'shows/admin_show_list.html'
    context_object_name = 'shows'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().order_by('-date')
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(location__icontains=query)
            ).distinct()
        return queryset

class ShowDetailView(DetailView):
    model = Show
    template_name = 'shows/show_detail.html'
    context_object_name = 'show'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        show = self.get_object()  # Récupère l'objet Show actuel

        # Compter le nombre total de sièges pour ce spectacle
        total_seats_count = Seat.objects.filter(show=show).count()
        
        # Compter le nombre de sièges disponibles (non réservés) pour ce spectacle
        available_seats_count = Seat.objects.filter(show=show, is_reserved=False).count()
        
        context['total_seats_count'] = total_seats_count
        context['available_seats_count'] = available_seats_count
        return context

@method_decorator(staff_required, name='dispatch')
class ShowCreateView(View):
    def get(self, request):
        form = ShowForm()
        print(f"[ShowCreateView] GET request. User: {request.user}") # Basic log
        return render(request, 'shows/show_form.html', {'form': form})

    def post(self, request):
        form = ShowForm(request.POST, request.FILES)
        print(f"[ShowCreateView] POST request. User: {request.user}") # Basic log
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

@method_decorator(staff_required, name='dispatch')
class ShowUpdateView(UpdateView): 
    model = Show
    form_class = ShowForm 
    template_name = 'shows/show_form.html' 
    success_url = reverse_lazy('admin_show_list')

@method_decorator(staff_required, name='dispatch')
class ShowDeleteView(DeleteView): 
    model = Show
    template_name = 'shows/show_confirm_delete.html' 
    success_url = reverse_lazy('admin_show_list')

# User Profile View
@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    # Get user's reservations
    user_reservations = Reservation.objects.filter(user=request.user).order_by('-reservation_date')
    
    # Get upcoming and past reservations
    now = timezone.now()
    upcoming_reservations = user_reservations.filter(show__date__gt=now)
    past_reservations = user_reservations.filter(show__date__lte=now)
    
    # Count statistics
    stats = {
        'total_reservations': user_reservations.count(),
        'upcoming_reservations': upcoming_reservations.count(),
        'past_reservations': past_reservations.count(),
        'total_spent': sum(r.show.price for r in user_reservations if hasattr(r, 'show') and r.show),
    }
    
    context = {
        'form': form,
        'user_reservations': user_reservations,
        'upcoming_reservations': upcoming_reservations,
        'past_reservations': past_reservations,
        'stats': stats,
        'active_tab': request.GET.get('tab', 'profile')
    }
    
    return render(request, 'shows/profile.html', context)

# Password Change View
@login_required
def password_change_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            # Update the session to prevent the user from being logged out
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, form.user)
            messages.success(request, 'Your password has been changed successfully!')
            return redirect('profile')
    else:
        form = PasswordChangeForm(user=request.user)
    
    return render(request, 'shows/password_change.html', {'form': form})


# Ticket Views
@login_required
def ticket_view(request, reservation_id):
    """
    Affiche le ticket pour une réservation spécifique
    """
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    return render(request, 'shows/ticket.html', {'reservation': reservation})


@login_required
def generate_demo_tickets(request):
    """
    Génère 10 tickets de démonstration avec différentes catégories
    """
    if not request.user.is_authenticated:
        messages.error(request, "Vous devez être connecté pour générer des tickets.")
        return redirect('login')
    
    # Récupérer tous les spectacles
    shows = Show.objects.all()
    if not shows.exists():
        messages.error(request, "Aucun spectacle n'est disponible pour générer des tickets.")
        return redirect('show_list')
    
    # Liste des catégories pour les démonstrations
    categories = ['concert', 'theatre', 'cinema', 'comedy', 'dance']
    
    # Générer 10 tickets de démonstration
    created_reservations = []
    for i in range(10):
        # Sélectionner un spectacle aléatoire
        show = random.choice(shows)
        
        # S'assurer que le spectacle a une catégorie définie
        if not hasattr(show, 'category') or not show.category:
            # Si la catégorie n'existe pas, en assigner une aléatoire
            category = random.choice(categories)
            show.category = category
            show.save()
        
        # Créer ou récupérer un siège disponible
        seat_row = random.choice(['A', 'B', 'C', 'D', 'E'])
        seat_number = random.randint(1, 30)
        seat_category = random.choice(['Standard', 'Premium', 'VIP'])
        
        # Créer un siège s'il n'existe pas déjà
        seat, created = Seat.objects.get_or_create(
            show=show,
            seat_number=f"{seat_row}-{seat_number}",
            defaults={'is_reserved': False}
        )
        
        # Ajouter des attributs supplémentaires au siège
        if not hasattr(seat, 'row'):
            seat.row = seat_row
        if not hasattr(seat, 'number'):
            seat.number = seat_number
        if not hasattr(seat, 'category'):
            seat.category = seat_category
        
        # Marquer le siège comme réservé
        seat.is_reserved = True
        seat.save()
        
        # Créer la réservation
        reservation_date = timezone.now() - datetime.timedelta(days=random.randint(0, 30))
        
        reservation = Reservation.objects.create(
            user=request.user,
            show=show,
            seat=seat,
            reservation_date=reservation_date,
            payment_confirmed=True
        )
        
        created_reservations.append(reservation)
    
    messages.success(request, f"10 tickets de démonstration ont été générés avec succès!")
    
    # Rediriger vers la page des réservations (my_bookings)
    return redirect('my_bookings')


@login_required
def my_bookings(request):
    """
    Affiche toutes les réservations de l'utilisateur connecté
    """
    reservations = Reservation.objects.filter(user=request.user).order_by('-reservation_date')
    return render(request, 'shows/my_bookings.html', {'reservations': reservations})


@login_required
def download_ticket_pdf(request, reservation_id):
    """
    Génère et télécharge un ticket au format PDF
    """
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    
    # Rendu du template HTML en chaîne
    template = get_template('shows/ticket_pdf.html')
    context = {'reservation': reservation, 'MEDIA_URL': settings.MEDIA_URL}
    html = template.render(context)
    
    # Création du PDF à partir du HTML
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        filename = f"ticket_{reservation.id}_{reservation.show.title}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    return HttpResponse('Erreur lors de la génération du PDF', status=400)
