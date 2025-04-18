from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ["username", "email", "categoria", "is_staff"]
    fieldsets = UserAdmin.fieldsets + (
        ("Categoria do Usuário", {"fields": ("categoria",)}),
    )


admin.site.register(CustomUser, CustomUserAdmin)
