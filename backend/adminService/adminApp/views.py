from django.shortcuts import render
from django.db.models import Avg, Count, Q
from django.http import HttpRequest, JsonResponse
from .models import Message, Category, User, FinetuneTimer
import json
from django.db.models.functions import TruncMonth
from datetime import datetime, timedelta
from django.utils import timezone
from adminApp.analysis import test_confs
import random
import pandas as pd
from .generate_faq import get_emb_model, gen_faq

# Create your views here.

def get_monthly_stats(messages_query):
    monthly_stats = (
        messages_query
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(
            count=Count('id'),
            avg_rating=Avg('rating')
        )
        .order_by('month')
    )
    
    monthly_chart_data = {
        "data": {
            "labels": [],
            "datasets": [
                {
                    "label": "Количество сообщений",
                    "data": [],
                },
                {
                    "label": "Средняя оценка",
                    "data": [],
                }
            ]
        }
    }
    
    for stat in monthly_stats:
        month_name = stat['month'].strftime('%B %Y')
        monthly_chart_data["data"]["labels"].append(month_name)
        monthly_chart_data["data"]["datasets"][0]["data"].append(stat['count'])
        monthly_chart_data["data"]["datasets"][1]["data"].append(
            round(stat['avg_rating'], 1) if stat['avg_rating'] else 0
        )
    
    return monthly_chart_data

def get_monthly_stats_with_categories(messages_query, month=None, category_id=None, subcategory_id=None):
    if month:
        # Фильтруем сообщения по выбранному месяцу
        messages_query = messages_query.filter(
            created_at__year=month.year,
            created_at__month=month.month
        )
    
    # Применяем фильтры по категориям
    if subcategory_id:
        messages_query = messages_query.filter(category_level_2_id=subcategory_id)
    elif category_id:
        messages_query = messages_query.filter(
            Q(category_level_1_id=category_id) | 
            Q(category_level_2__parent_id=category_id)
        )
    
    # Получаем статистику по категориям для выбранного месяца
    if subcategory_id:
        # Если выбрана подкатегория, показываем статистику по подкатегориям
        category_stats = (
            messages_query
            .values('category_level_2__name')
            .annotate(
                count=Count('id'),
                avg_rating=Avg('rating')
            )
            .exclude(category_level_2__name__isnull=True)
            .order_by('-count')
        )
    elif category_id:
        # Если выбрана основная категория, показываем статистику по подкатегориям
        category_stats = (
            messages_query
            .values('category_level_2__name')
            .annotate(
                count=Count('id'),
                avg_rating=Avg('rating')
            )
            .exclude(category_level_2__name__isnull=True)
            .order_by('-count')
        )
    else:
        # Если не выбрана категория, показываем статистику по основным категориям
        category_stats = (
            messages_query
            .values('category_level_1__name')
            .annotate(
                count=Count('id'),
                avg_rating=Avg('rating')
            )
            .exclude(category_level_1__name__isnull=True)
            .order_by('-count')
        )
    
    monthly_chart_data = {
        "data": {
            "labels": [],
            "datasets": [
                {
                    "label": "Количество сообщений",
                    "data": [],
                },
                {
                    "label": "Средняя оценка",
                    "data": [],
                }
            ]
        }
    }
    
    for stat in category_stats:
        if subcategory_id or category_id:
            full_name = stat['category_level_2__name'] or 'Без подкатегории'
        else:
            full_name = stat['category_level_1__name'] or 'Без категории'
            
        # Сокращаем название до первых 3 слов
        short_name = ' '.join(full_name.split()[:3])
        if len(full_name.split()) > 3:
            short_name += '...'
            
        monthly_chart_data["data"]["labels"].append({
            "short": short_name,
            "full": full_name
        })
        monthly_chart_data["data"]["datasets"][0]["data"].append(stat['count'])
        monthly_chart_data["data"]["datasets"][1]["data"].append(
            round(stat['avg_rating'], 1) if stat['avg_rating'] else 0
        )
    
    return monthly_chart_data

def get_configuration_stats(messages_query):
    # Получаем все конфигурации и их оценки
    config_ratings = {}
    for message in messages_query.filter(rating__isnull=False):
        config_name = f"{message.configuration.llm_model.name} + {message.configuration.embedding_model.name}"
        if config_name not in config_ratings:
            config_ratings[config_name] = []
        config_ratings[config_name].append(message.rating)
    
    if not config_ratings:
        return None
    
    # Анализируем конфигурации
    analysis_results = test_confs(config_ratings)
    return analysis_results

def start_finetune(request):
    timer, created = FinetuneTimer.objects.get_or_create(id=1)
    
    if not timer.is_running:
        # Генерируем случайную длительность от 15 до 30 часов
        duration = random.uniform(15, 30)
        timer.is_running = True
        timer.start_time = timezone.now()
        timer.duration_hours = duration
        timer.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Finetune started',
            'duration': duration,
            'start_time': timer.start_time.isoformat()
        })
    else:
        return JsonResponse({
            'status': 'error',
            'message': 'Finetune is already running'
        }, status=400)

def get_finetune_status(request):
    timer = FinetuneTimer.objects.first()
    if not timer or not timer.is_running:
        return JsonResponse({
            'status': 'stopped',
            'message': 'Finetune is not running'
        })
    
    now = timezone.now()
    elapsed = (now - timer.start_time).total_seconds() / 3600
    remaining = max(0, timer.duration_hours - elapsed)
    
    return JsonResponse({
        'status': 'running',
        'remaining_hours': round(remaining, 2),
        'progress': min(100, (elapsed / timer.duration_hours) * 100)
    })

def get_faq(request):
    # Получаем все сообщения из базы данных
    messages = Message.objects.filter(role__in=['user', 'assistant']).order_by('chat_id', 'created_at')
    
    # Создаем DataFrame с вопросами и ответами
    qa_pairs = []
    current_question = None
    
    for message in messages:
        if message.role == 'user':
            current_question = message.content
        elif message.role == 'assistant' and current_question:
            qa_pairs.append({
                'question': current_question,
                'answer': message.content
            })
            current_question = None
    
    df = pd.DataFrame(qa_pairs)
    
    if df.empty:
        return JsonResponse({'faq': []})
    
    # Генерируем FAQ
    model = get_emb_model()
    faq = gen_faq(df, model)
    
    return JsonResponse({'faq': faq})

def dashboard_callback(request: HttpRequest, context: dict) -> dict:
    # Получаем параметры фильтрации
    category_id = request.GET.get('category')
    subcategory_id = request.GET.get('subcategory')
    
    # Базовый запрос для сообщений
    messages_query = Message.objects.all()
    
    # Применяем фильтры
    if subcategory_id:
        messages_query = messages_query.filter(category_level_2_id=subcategory_id)
    elif category_id:
        messages_query = messages_query.filter(
            Q(category_level_1_id=category_id) | 
            Q(category_level_2__parent_id=category_id)
        )
    
    # Получаем статистику по категориям
    if subcategory_id:
        # Если выбрана подкатегория, показываем статистику по подкатегориям
        category_stats = (
            messages_query
            .values('category_level_2__name')
            .annotate(
                count=Count('id'),
                avg_rating=Avg('rating')
            )
            .exclude(category_level_2__name__isnull=True)
            .order_by('-count')
        )
    elif category_id:
        # Если выбрана основная категория, показываем статистику по подкатегориям
        category_stats = (
            messages_query
            .values('category_level_2__name')
            .annotate(
                count=Count('id'),
                avg_rating=Avg('rating')
            )
            .exclude(category_level_2__name__isnull=True)
            .order_by('-count')
        )
    else:
        # Если не выбрана категория, показываем статистику по основным категориям
        category_stats = (
            messages_query
            .values('category_level_1__name')
            .annotate(
                count=Count('id'),
                avg_rating=Avg('rating')
            )
            .exclude(category_level_1__name__isnull=True)
            .order_by('-count')
        )[:10]  # Ограничиваем до 10 самых популярных категорий
    
    # Получаем статистику по месяцам
    monthly_chart_data = get_monthly_stats(messages_query)
    
    # Получаем выбранные месяцы для сравнения
    month1_str = request.GET.get('month1')
    month2_str = request.GET.get('month2')
    
    # Преобразуем строки в даты, если они предоставлены
    month1 = datetime.strptime(month1_str, '%Y-%m').date() if month1_str else None
    month2 = datetime.strptime(month2_str, '%Y-%m').date() if month2_str else None
    
    # Получаем статистику для каждого месяца
    monthly_chart_data1 = get_monthly_stats_with_categories(
        messages_query, 
        month1,
        category_id,
        subcategory_id
    )
    monthly_chart_data2 = get_monthly_stats_with_categories(
        messages_query, 
        month2,
        category_id,
        subcategory_id
    )
    
    # Получаем список доступных месяцев
    available_months = (
        messages_query
        .dates('created_at', 'month')
        .order_by('-created_at')
    )
    
    # Подготавливаем данные для графиков
    categories_chart_data = {
        "data": {
            "labels": [],
            "datasets": [
                {
                    "label": "Количество сообщений",
                    "data": [],
                }
            ]
        }
    }
    
    ratings_chart_data = {
        "data": {
            "labels": [],
            "datasets": [
                {
                    "label": "Средняя оценка",
                    "data": [],
                }
            ]
        }
    }
    
    for stat in category_stats:
        if subcategory_id or category_id:
            full_name = stat['category_level_2__name'] or 'Без подкатегории'
        else:
            full_name = stat['category_level_1__name'] or 'Без категории'
            
        # Сокращаем название до первых 3 слов
        short_name = ' '.join(full_name.split()[:3])
        if len(full_name.split()) > 3:
            short_name += '...'
            
        categories_chart_data["data"]["labels"].append({
            "short": short_name,
            "full": full_name
        })
        categories_chart_data["data"]["datasets"][0]["data"].append(stat['count'])
        
        ratings_chart_data["data"]["labels"].append({
            "short": short_name,
            "full": full_name
        })
        ratings_chart_data["data"]["datasets"][0]["data"].append(
            round(stat['avg_rating'], 1) if stat['avg_rating'] else 0
        )
    
    # Подготавливаем данные для таблицы
    messages_table = {
        'headers': ['Чат', 'Пользователь', 'Роль', 'Категория', 'Тип', 'Запрос', 'Оценка', 'Дата'],
        'rows': []
    }
    
    for message in messages_query.order_by('-created_at')[:10]:
        category = ''
        if message.category_level_2:
            category = f"{message.category_level_1.name} -> {message.category_level_2.name}"
        elif message.category_level_1:
            category = message.category_level_1.name
            
        # Ограничиваем длину запроса до 100 символов
        content = message.content
        if len(content) > 100:
            content = content[:100] + '...'
            
        messages_table['rows'].append([
            message.chat.title,
            message.chat.user.username,
            message.role,
            category,
            message.request_type,
            content,
            message.rating or '-',
            message.created_at.strftime('%Y-%m-%d %H:%M')
        ])
    
    # Получаем все категории и подкатегории
    categories = Category.objects.filter(parent=None)
    subcategories = Category.objects.filter(parent_id=category_id) if category_id else []
    
    # Создаем словарь подкатегорий для JavaScript
    subcategories_by_parent = {}
    for category in categories:
        subcategories_by_parent[str(category.id)] = [
            {'id': sub.id, 'name': sub.name}
            for sub in Category.objects.filter(parent=category)
        ]
    
    # Получаем статистику по конфигурациям
    config_stats = get_configuration_stats(messages_query)
    
    # Добавляем статус finetune в контекст
    timer = FinetuneTimer.objects.first()
    if timer and timer.is_running:
        elapsed = (timezone.now() - timer.start_time).total_seconds() / 3600
        remaining = max(0, timer.duration_hours - elapsed)
        context['finetune_status'] = {
            'is_running': True,
            'remaining_hours': round(remaining, 2),
            'progress': min(100, (elapsed / timer.duration_hours) * 100)
        }
    else:
        context['finetune_status'] = {
            'is_running': False,
            'remaining_hours': 0,
            'progress': 0
        }
    
    # Добавляем FAQ в контекст
    try:
        messages = Message.objects.filter(role__in=['user', 'assistant']).order_by('chat_id', 'created_at')
        qa_pairs = []
        current_question = None
        
        for message in messages:
            if message.role == 'user':
                current_question = message.content
            elif message.role == 'assistant' and current_question:
                qa_pairs.append({
                    'question': current_question,
                    'answer': message.content
                })
                current_question = None
        
        df = pd.DataFrame(qa_pairs)
        
        if not df.empty:
            model = get_emb_model()
            faq = gen_faq(df, model)
            context['faq'] = faq
        else:
            context['faq'] = []
    except Exception as e:
        context['faq'] = []
        print(f"Error generating FAQ: {e}")
    
    # Обновляем контекст
    context.update({
        'categories': categories,
        'subcategories': subcategories,
        'selected_category': int(category_id) if category_id else None,
        'selected_subcategory': int(subcategory_id) if subcategory_id else None,
        'subcategories_json': json.dumps(subcategories_by_parent),
        'categories_chart_data': json.dumps(categories_chart_data),
        'ratings_chart_data': json.dumps(ratings_chart_data),
        'monthly_chart_data': json.dumps(monthly_chart_data),
        'monthly_chart_data1': json.dumps(monthly_chart_data1),
        'monthly_chart_data2': json.dumps(monthly_chart_data2),
        'available_months': available_months,
        'selected_month1': month1_str,
        'selected_month2': month2_str,
        'messages_table': messages_table,
        'config_stats': config_stats
    })
    
    return context

def dashboard(request):
    context = {}
    context = dashboard_callback(request, context)
    return render(request, 'admin/index.html', context)
