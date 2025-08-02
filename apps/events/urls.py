"""
URLs pour l'application events.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Catégories
    path('categories/', views.EventCategoryListView.as_view(), name='event-categories'),
    
    # CRUD événements
    path('', views.EventListView.as_view(), name='event-list'),
    path('create/', views.EventCreateView.as_view(), name='event-create'),
    path('<int:pk>/', views.EventDetailView.as_view(), name='event-detail'),
    path('<int:pk>/update/', views.EventUpdateView.as_view(), name='event-update'),
    path('<int:pk>/delete/', views.EventDeleteView.as_view(), name='event-delete'),
    
    # Participations
    path('participate/', views.EventParticipationView.as_view(), name='event-participate'),
    path('<int:event_id>/cancel-participation/', views.cancel_participation_view, name='event-cancel-participation'),
    path('<int:event_id>/participants/', views.EventParticipantsView.as_view(), name='event-participants'),
    
    # Partages
    path('share/', views.EventShareView.as_view(), name='event-share'),
    
    # Billetterie
    path('tickets/purchase/', views.EventTicketPurchaseView.as_view(), name='event-ticket-purchase'),
    
    # Événements utilisateur
    path('my-events/', views.UserEventsView.as_view(), name='user-events'),
    path('my-participations/', views.UserParticipationsView.as_view(), name='user-participations'),
    path('my-tickets/', views.UserTicketsView.as_view(), name='user-tickets'),
    
    # Statistiques et tendances
    path('stats/', views.event_stats_view, name='event-stats'),
    path('trending/', views.trending_events_view, name='trending-events'),
]

