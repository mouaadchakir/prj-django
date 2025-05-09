from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Show, Reservation

# Define a new User admin
class UserAdmin(BaseUserAdmin):
    # Add user_type to the fieldsets for the add/change forms
    # UserAdmin.fieldsets is a tuple of tuples (section_name, {fields_dict})
    # We need to add 'user_type' to the 'Personal info' section or create a new one.
    # Let's add it to the section with 'email'.
    # We copy the existing fieldsets and add our field.
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'user_type')}), # Added user_type
        (
            'Permissions',
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                ),
            },
        ),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    # Add user_type to the list display for a quick overview
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'user_type')
    # Add user_type to the search fields
    search_fields = BaseUserAdmin.search_fields + ('user_type',)
    # Add user_type to the filter options
    list_filter = BaseUserAdmin.list_filter + ('user_type',)

# Register your models here.
admin.site.register(User, UserAdmin)
admin.site.register(Show) # Assuming a simple registration for Show is fine
admin.site.register(Reservation) # Assuming a simple registration for Reservation is fine
