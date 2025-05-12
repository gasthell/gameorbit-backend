from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.validators import RegexValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
import re

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        email = self.clean_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

    def clean_email(self, email):
        # Remove dots and +extension from the local part
        local, at, domain = email.partition('@')
        local = re.sub(r'\.', '', local)
        local = re.sub(r'\+.*', '', local)
        return f"{local}@{domain}"

class User(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=255)
    profile_picture = models.ImageField(upload_to='users/', blank=True, null=True)
    email = models.EmailField(unique=True, db_index=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    subscription = models.ForeignKey('Tariff', on_delete=models.SET_NULL, blank=True, null=True, help_text='Select a subscription tariff')
    end_date = models.DateTimeField(blank=True, null=True, help_text='Subscription end date')
    free_trial = models.BooleanField(default=False)
    linked_game_ids = ArrayField(models.IntegerField(), default=list, blank=True)
    sessions = models.JSONField(default=list, blank=True)
    active = models.BooleanField(default=True)
    role = models.CharField(max_length=50, default='user')
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, blank=True, null=True)
    verification_code_created = models.DateTimeField(blank=True, null=True)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    objects = UserManager()

    def save(self, *args, **kwargs):
        self.email = UserManager().clean_email(self.email)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email

class Game(models.Model):
    name = models.CharField(max_length=255)
    user_id = models.IntegerField(null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    max_users = models.IntegerField(null=True, blank=True)
    picture = models.ImageField(upload_to='games/', blank=True, null=True)
    map = models.ImageField(upload_to='games/', blank=True, null=True)
    chips = models.JSONField(default=dict, blank=True, null=True)
    cube = models.JSONField(default=dict, blank=True, null=True)
    decks = models.JSONField(default=dict, blank=True, null=True, help_text='Example: {"deck1": ["card1", "card2"]}')
    objects_json = models.JSONField(default=dict, blank=True, null=True, help_text='Example: {"photo": "url", "copies": 1}')
    rules = models.FileField(upload_to='rules/', null=True, blank=True)
    date_created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

class Room(models.Model):
    room_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    user_id = models.IntegerField(null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    max_users = models.IntegerField(null=True, blank=True)
    picture = models.ImageField(upload_to='games/', blank=True, null=True)
    map = models.ImageField(upload_to='games/', blank=True, null=True)
    chips = models.JSONField(default=dict, blank=True, null=True)
    cube = models.JSONField(default=dict, blank=True, null=True)
    decks = models.JSONField(default=dict, blank=True, null=True, help_text='Example: {"deck1": ["card1", "card2"]}')
    objects_json = models.JSONField(default=dict, blank=True, null=True, help_text='Example: {"photo": "url", "copies": 1}')
    rules = models.URLField(null=True)
    date_created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name
    
class Feature(models.Model):
    name = models.CharField(max_length=255)
    tariff = models.ForeignKey('Tariff', on_delete=models.CASCADE, related_name='features')

    def __str__(self):
        return self.name

class Tariff(models.Model):
    name = models.CharField(max_length=255)
    price = models.IntegerField()

    def __str__(self):
        return self.name

class MainPageGame(models.Model):
    order = models.IntegerField(default=0, help_text='Order of the game on the main page')
    name = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    author_link = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True)
    picture = models.ImageField(upload_to='main_page_games/', blank=True, null=True)
    
    def __str__(self):
        return self.name
    
class Promocode(models.Model):
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255, choices=[('option1', 'Subscription'), ('option2', 'Discount')])
    subscription = models.ForeignKey('Tariff', on_delete=models.SET_NULL, blank=True, null=True, help_text='Select a subscription tariff')
    discount_amount = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    max_users = models.IntegerField()
    end_date = models.DateTimeField()

    def clean(self):
        if self.type == 'option1' and not self.subscription:
            raise ValidationError("Subscription is required when type is Subscription.")
        if self.type == 'option2' and not self.discount_amount:
            raise ValidationError("Discount amount is required when type is Discount.")

    def __str__(self):
        return self.name