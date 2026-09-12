from django.db import models
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import BaseUserManager



class CustomUserManager(BaseUserManager):
    
    def create_user(self, email, password = None, **extra_fields):
        
        if not email:
            raise ValueError('Email is required')
        
        email = self.normalize_email(email = email)
        user = self.model(email = email, **extra_fields)
        user.set_password(password)
        user.save(using = self.db)
        return user
    
    def create_superuser(self, email, password = None, **extra_fields):
        
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff',True)
        
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email=email, password=password, **extra_fields)     
    

class CustomUser(AbstractBaseUser,PermissionsMixin):
    
    email = models.EmailField(unique=True, max_length=255)
    username = models.CharField(max_length=255)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_staff = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    avatar = models.ImageField(null=True)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        
    def __str__(self):
        return self.username
    