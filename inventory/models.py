# ===================================================================
# Projeto: Inventory Management
# Autor: Henrique José Dias Pereira
# Data: 06/11/2024
# Direitos Autorais: © 2024 Henrique José Dias Pereira. Todos os direitos reservados.
# ===================================================================

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class InventoryItem(models.Model):
    name = models.CharField(max_length=200)
    quantity = models.IntegerField()
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, blank = True, null = True)
    date_created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null = True)
    
    def __str__(self):
        return self.name
    

class Category(models.Model):
    name = models.CharField(max_length=200)
    
    class Meta:
        verbose_name_plural = 'categories'
    
    def __str__(self):
        return self.name
    
class MovementLog(models.Model):
    ACTION_CHOICES = [
        ('ADD', 'Adicionado'),
        ('REMOVE', 'Removido'),
        ('EDIT', 'Editado'),
        ('INCREASE', 'Aumentado'),
        ('DECREASE', 'Diminuído'),
    ]

    item = models.ForeignKey('InventoryItem', on_delete=models.SET_NULL, null=True)
    change = models.IntegerField()  
    action_type = models.CharField(max_length=10, choices=ACTION_CHOICES, default='ADD')  
    timestamp = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)  
    observation = models.TextField(blank=True, null=True)  

    def __str__(self):
        item_name = self.item.name
        return f"{item_name} - {self.get_action_type_display()} - Observação: {self.observation} - {self.change} units on {self.timestamp} by {self.user}"
