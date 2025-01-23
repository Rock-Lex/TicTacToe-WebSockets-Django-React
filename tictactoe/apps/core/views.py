from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Q
from django.template.loader import render_to_string
from apps.api.models import PlayedGame

MAX_GAMES_PER_PAGE = 10

def get_game_filter(user, game_filter):
    try:
        if game_filter == 'win':
            return PlayedGame.objects.filter(
                Q(player_x=user, winner=user) | Q(player_o=user, winner=user),
                is_finished=True
            )
        elif game_filter == 'lose':
            return PlayedGame.objects.filter(
                is_finished=True
            ).exclude(winner=user)
        else:
            return PlayedGame.objects.filter(
                Q(player_x=user) | Q(player_o=user),
                is_finished=True
            )
    except Exception as e:
        return JsonResponse({'error': f'Error fetching game filter: {str(e)}'}, status=500)

def get_sorted_games(games_query, date_sort):
    try:
        if date_sort == 'asc':
            return games_query.order_by('created_at')
        return games_query.order_by('-created_at')
    except Exception as e:
        return JsonResponse({'error': f'Error sorting games: {str(e)}'}, status=500)

def get_paginated_games(request, games_query):
    try:
        paginator = Paginator(games_query, MAX_GAMES_PER_PAGE)
        page_number = request.GET.get('page', 1)
        games_page = paginator.get_page(page_number)
        return games_page, paginator
    except Exception as e:
        return JsonResponse({'error': f'Error paginating games: {str(e)}'}, status=500)

def paginate_games(request):
    game_filter = request.GET.get('filter', 'all')
    date_sort = request.GET.get('sort', 'desc')

    valid_filters = ['all', 'win', 'lose']
    valid_sorts = ['asc', 'desc']

    if game_filter not in valid_filters:
        game_filter = 'all'
    if date_sort not in valid_sorts:
        date_sort = 'desc'

    try:
        games_query = get_game_filter(request.user, game_filter)
        games_query = get_sorted_games(games_query, date_sort)

        games_page, paginator = get_paginated_games(request, games_query)

        table_html = render_to_string('partials/games_table.html', {'games_played': games_page})

        context = {
            'table_html': table_html,
            'has_next': games_page.has_next(),
            'has_previous': games_page.has_previous(),
            'current_page': games_page.number,
            'total_pages': paginator.num_pages,
        }

        return JsonResponse(context)
    except Exception as e:
        return JsonResponse({'error': f'Error processing the games data: {str(e)}'}, status=500)

@login_required
def home(request):
    return render(request, 'home.html')
