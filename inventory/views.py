# ===================================================================
# Projeto: Inventory Management
# Autor: Henrique José Dias Pereira
# Data: 06/11/2024
# Direitos Autorais: © 2024 Henrique José Dias Pereira. Todos os direitos reservados.
# ===================================================================


from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from .utils import get_response, predict_class
from django.views.generic import TemplateView, View, CreateView, UpdateView, DeleteView, ListView
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import UserRegisterForm, InventoryItemForm, ItemFilterForm, DecreaseItemForm, IncreaseItemForm
from .models import InventoryItem, Category, MovementLog
from inventory_management.settings import LOW_QUANTITY
from django.contrib import messages
import json
from django.db.models import Sum, Q
from django.utils import timezone
import logging
from django.core.paginator import Paginator

logger = logging.getLogger(__name__)

class Index(TemplateView):
    template_name = 'inventory/index.html'

class Dashboard(LoginRequiredMixin, View):
    def get(self, request):
        # Obtém o valor do filtro 'filter' da query string
        filter_value = request.GET.get('filter', '')

        # Inicia o queryset dos itens
        items = InventoryItem.objects.filter(user=self.request.user.id).order_by('id')

        # Se houver valor de filtro, aplica a busca tanto no nome quanto na categoria
        if filter_value:
            # Filtro por nome ou categoria usando Q objects para criar uma consulta mais flexível
            items = items.filter(
                Q(name__icontains=filter_value) | Q(category__name__icontains=filter_value)
            )

        # Aplica a paginação (15 itens por página)
        paginator = Paginator(items, 15)  # 15 itens por página
        page_number = request.GET.get('page')  # Obtém o número da página
        page_obj = paginator.get_page(page_number)  # Obtém os itens da página atual

        # Filtra os itens com baixo estoque
        low_inventory = InventoryItem.objects.filter(
            user=self.request.user.id,
            quantity__lte=LOW_QUANTITY
        )
        
        if low_inventory.exists():  # Verifica se há itens com baixo estoque
            low_inventory_count = low_inventory.count()
            if low_inventory_count > 1:
                messages.error(request, f'{low_inventory_count} itens estão com baixo estoque')
            else:
                messages.error(request, f'{low_inventory_count} item está com baixo estoque')

        # Obtém os IDs dos itens com baixo estoque
        low_inventory_ids = low_inventory.values_list('id', flat=True)
    
        # Passa os itens paginados e o filtro para o template
        return render(request, 'inventory/dashboard.html', {
            'items': page_obj,  # Passando os itens paginados para o template
            'low_inventory_ids': low_inventory_ids,  # Passa os itens com baixo estoque
            'filter_value': filter_value,  # Passa o filtro para o template
        })
        
class AddItem(LoginRequiredMixin, CreateView):
    model = InventoryItem
    form_class = InventoryItemForm
    template_name = 'inventory/item_form.html'
    success_url = reverse_lazy('dashboard')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.name = form.instance.name.upper()
        response = super().form_valid(form)
        
        # Registrar movimentação
        MovementLog.objects.create(
            item=form.instance,
            change=form.instance.quantity,
            action_type='ADD',
            user=self.request.user
            )    

        return response


class SignUpView(View):
    def get(self, request):
        form = UserRegisterForm()
        return render(request, 'inventory/signup.html', {'form': form})
        
    def post(self, request):
        form = UserRegisterForm(request.POST)
        
        if form.is_valid():
            form.save()
            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1']
            )
            
            login(request, user)
            return redirect('index')
        
        return render(request, 'inventory/signup.html', {'form':form})


class EditItem(LoginRequiredMixin, UpdateView):
    model = InventoryItem
    form_class = InventoryItemForm
    template_name = 'inventory/item_form.html'
    success_url = reverse_lazy('dashboard')
    
    def form_valid(self, form):
        original_item = self.get_object()
        original_quantity = original_item.quantity
        response = super().form_valid(form)
        
        # Calcular a diferença de quantidade
        quantity_change = form.instance.quantity - original_quantity
        
        # Determinar o tipo de ação
        action_type = 'INCREASE' if quantity_change > 0 else 'DECREASE'
        
        # Registrar movimentação
        MovementLog.objects.create(
            item=form.instance,
            change=quantity_change,
            action_type='EDIT',
            user=self.request.user  # Garantir que o usuário está sendo atribuído aqui
        )
        
        return response

class DeleteItem(LoginRequiredMixin, DeleteView):
    model = InventoryItem
    template_name = 'inventory/delete_item.html'
    success_url = reverse_lazy('dashboard')
    context_object_name = 'item'
    
    def delete(self, request, *args, **kwargs):
        item = self.get_object()
        
        if item:  # Verifica se o item não é None
            with transaction.atomic():
                MovementLog.objects.create(
                    item=item,
                    change=-item.quantity,
                    action_type='REMOVE',
                    user=self.request.user,
                    observation='Item excluído'
                )
            
        response = super().delete(request, *args, **kwargs)
        
        return response
    
class IncreaseItemView(LoginRequiredMixin, View):
    def get(self, request, pk):
        item = get_object_or_404(InventoryItem, pk=pk)
        form = IncreaseItemForm(initial={'quantity': 1})
        return render(request, 'inventory/increase_item.html', {'item': item, 'form': form})

    def post(self, request, pk):
        item = get_object_or_404(InventoryItem, pk=pk)
        form = IncreaseItemForm(request.POST)
        
        if form.is_valid():
            increase_amount = form.cleaned_data['quantity']
            observation = form.cleaned_data['observation']

            if increase_amount > 0:
                item.quantity += increase_amount
                item.save()

                MovementLog.objects.create(
                    item=item,
                    change=increase_amount,
                    action_type='INCREASE',
                    observation=observation,
                    user=request.user
                )

            return redirect('dashboard')

        return render(request, 'inventory/increase_item.html', {'item': item, 'form': form})

class ClearLogsView(LoginRequiredMixin, View):
    def get(self, request):
        MovementLog.objects.all().delete()
        return redirect('movement_log')  


class MovementLogView(LoginRequiredMixin, View):
    def get(self, request):
        # Verifica se o usuário é superusuário
        if request.user.is_superuser:
            logs = MovementLog.objects.all().order_by('-timestamp')  # Admin vê todos os logs
        else:
            logs = MovementLog.objects.filter(user=request.user).order_by('-timestamp')  # Usuário vê apenas seus próprios logs


        return render(request, 'inventory/movement_log.html', {'logs': logs})


class DecreaseItemView(LoginRequiredMixin, View):
    def get(self, request, pk):
        item = get_object_or_404(InventoryItem, pk=pk)
        form = DecreaseItemForm(initial={'quantity': 1})
        return render(request, 'inventory/decrease_item.html', {'item': item, 'form': form})

    def post(self, request, pk):
        item = get_object_or_404(InventoryItem, pk=pk)
        form = DecreaseItemForm(request.POST)
        
        if form.is_valid():
            decrease_amount = form.cleaned_data['quantity']
            observation = form.cleaned_data['observation']

            if decrease_amount > 0:
                item.quantity -= decrease_amount
                item.save()

                MovementLog.objects.create(
                    item=item,
                    change=-decrease_amount,
                    action_type='DECREASE',
                    observation=observation,
                    user=request.user
                )

            return redirect('dashboard')

        return render(request, 'inventory/decrease_item.html', {'item': item, 'form': form})
    
class ItemFilter(LoginRequiredMixin, View):
    def get(self, request):
        # Captura o valor do parâmetro 'name' da URL
        name = request.GET.get('name', '')

        # Filtra os itens com base no usuário
        items = InventoryItem.objects.filter(user=request.user).order_by('id')

        # Aplica o filtro de nome, se o valor 'name' for fornecido
        if name:
            items = items.filter(name__icontains=name)

        # Obtém IDs de itens com baixo estoque
        low_inventory_ids = items.filter(quantity__lte=LOW_QUANTITY).values_list('id', flat=True)

        context = {
            'items': items,
            'low_inventory_ids': low_inventory_ids,
            'name': name,  # Passa o valor do campo de input para o template
        }
        
        return render(request, 'inventory/item_filter.html', context)

@csrf_exempt
def chatbot_response(request):
    if request.method == 'POST':
        message = request.POST.get('message')
        if message:
            response = get_response(message)
            return JsonResponse({'response': response})
        return JsonResponse({'error': 'No message provided'}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def index(request):
    return render(request, 'dashboard.html')

@csrf_exempt
def handle_message(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        message = data.get('message', '')

        if not message:
            return JsonResponse({'response': "Desculpe, não entendi sua mensagem."})

        response = get_response(message)
        return JsonResponse({'response': response})
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def update_intents_file(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        file_path = data.get('file_path')
        tag = data.get('tag')
        new_patterns = data.get('patterns')

        if not file_path or not tag or not new_patterns:
            return JsonResponse({'error': 'Parâmetros insuficientes.'}, status=400)

        try:
            with open(file_path, 'r+', encoding='utf-8') as file:
                data = json.load(file)
                intent_found = False
                for intent in data['intents']:
                    if intent['tag'] == tag:
                        intent['patterns'] = new_patterns
                        intent_found = True
                        break
                if not intent_found:
                    data['intents'].append({'tag': tag, 'patterns': new_patterns, 'responses': []})
                file.seek(0)
                json.dump(data, file, indent=4, ensure_ascii=False)
                file.truncate()
            return JsonResponse({'message': 'Intents atualizados com sucesso.'})
        except FileNotFoundError:
            return JsonResponse({'error': 'Arquivo não encontrado.'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Erro ao decodificar o arquivo JSON.'}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def chat(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        if 'message' not in data:
            return JsonResponse({"error": "A chave 'message' é obrigatória."}, status=400)

        message = data['message']
        intents = predict_class(message)
        response = get_response(message)
        
        return JsonResponse({
            'intents': intents,
            'response': response
        })
    return JsonResponse({'error': 'Invalid request method'}, status=405)

class MostSoldItemsReport(LoginRequiredMixin, View):
    def get(self, request):
        report = (MovementLog.objects
                  .filter(change__lt=0)  # Somente saídas
                  .values('item__name')
                  .annotate(total_sold=Sum('change'))
                  .order_by('total_sold')[:10])
        
        return render(request, 'inventory/most_sold_report.html', {'report': report})


