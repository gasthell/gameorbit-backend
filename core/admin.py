from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Game, Tariff, Feature, MainPageGame, Promocode, Room
from adminsortable2.admin import SortableAdminMixin
from django.utils.safestring import mark_safe
from django import forms

import os

class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ('email', 'name', 'subscription', 'is_verified', 'is_staff', 'is_superuser', 'active', 'role', 'linked_game_ids', 'sessions')
    list_filter = ('is_verified', 'is_staff', 'is_superuser', 'active', 'role')
    search_fields = ('email', 'name', 'phone')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('name', 'profile_picture', 'phone', 'subscription', 'free_trial', 'linked_game_ids', 'sessions', 'role', 'is_verified')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2', 'is_staff', 'is_superuser', 'active', 'role'),
        }),
    )

class FeatureInline(admin.TabularInline):
    model = Feature
    extra = 1

class TariffAdmin(admin.ModelAdmin):
    inlines = [FeatureInline]
    list_display = ('name', 'price', 'preview_html')

    def preview_html(self, obj):
        features = "<ul>" + "".join(f"<li>{f.name}</li>" for f in obj.features.all()) + "</ul>"
        return mark_safe(f"<div style='padding:8px;border:1px solid #ccc'><b>{obj.name}</b><br>Price: {obj.price}<br>Features:{features}</div>")
    preview_html.short_description = "Preview"

class MainPageGameAdmin(SortableAdminMixin, admin.ModelAdmin):
    model = MainPageGame
    list_display = ('name', 'author', 'author_link', 'preview_html')
    ordering = ('order',)
    
    fields = ('preview', 'order', 'name', 'author', 'author_link', 'description', 'picture')
    readonly_fields = ["preview"]

    class Media:
        js = ('core/js/mainpagegame_preview.js',)

    def preview(self, obj):
        template_path = os.path.join(os.path.dirname(__file__), 'html_templates', 'rt_preview_card.html')
        with open(template_path, encoding='utf-8') as f:
            html = f.read().format(
                image_url=obj.picture.url if obj.picture else '',
                name=obj.name,
                author_link=obj.author_link,
                author=obj.author,
                description=obj.description,
            )
        # Wrap the preview in a div for JS updates
        return mark_safe(html)
    
    def preview_html(self, obj):
        template_path = os.path.join(os.path.dirname(__file__), 'html_templates', 'preview_card.html')
        with open(template_path, encoding='utf-8') as f:
            html = f.read().format(
                image_url=obj.picture.url if obj.picture else '',
                name=obj.name,
                author_link=obj.author_link,
                author=obj.author,
                description=obj.description,
            )
        # Wrap the preview in a div for JS updates
        return mark_safe(html)

class PromocodeForm(forms.ModelForm):
    class Meta:
        model = Promocode
        fields = '__all__'

    class Media:
        js = ('core/js/promocode_type_toggle.js',)

class PromocodeAdmin(admin.ModelAdmin):
    form = PromocodeForm

admin.site.register(User, UserAdmin)
admin.site.register(Game)
admin.site.register(Room)
admin.site.register(Tariff, TariffAdmin)
admin.site.register(MainPageGame, MainPageGameAdmin)
admin.site.register(Promocode, PromocodeAdmin)