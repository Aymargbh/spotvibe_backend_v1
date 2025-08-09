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
    
    # Gestion des médias
    path('<int:event_id>/medias/', views.EventMediaListView.as_view(), name='event-medias'),
    path('<int:event_id>/medias/upload/', views.EventMediaUploadView.as_view(), name='event-media-upload'),
    path('medias/<int:pk>/', views.EventMediaDetailView.as_view(), name='event-media-detail'),
    path('medias/<int:pk>/delete/', views.EventMediaDeleteView.as_view(), name='event-media-delete'),
    path('<int:event_id>/set-cover/<int:media_id>/', views.set_cover_image, name='event-set-cover'),
    path('<int:event_id>/set-post-cover/<int:media_id>/', views.set_post_cover_image, name='event-set-post-cover'),
    
    # Participations
    path('participate/', views.EventParticipationView.as_view(), name='event-participate'),
    path('<int:event_id>/cancel-participation/', views.cancel_participation_view, name='event-cancel-participation'),
    path('<int:event_id>/participants/', views.EventParticipantsView.as_view(), name='event-participants'),
    
    # Partages
    path('share/', views.EventShareView.as_view(), name='event-share'),
    path('shares/<int:pk>/click/', views.track_share_click, name='event-share-click'),
    
    # Billetterie
    path('tickets/purchase/', views.EventTicketPurchaseView.as_view(), name='event-ticket-purchase'),
    path('tickets/<uuid:uuid>/', views.EventTicketDetailView.as_view(), name='event-ticket-detail'),
    path('tickets/<uuid:uuid>/validate/', views.validate_ticket, name='event-ticket-validate'),
    path('<int:event_id>/tickets/', views.EventTicketListView.as_view(), name='event-tickets'),
    
    # Événements utilisateur
    path('my-events/', views.UserEventsView.as_view(), name='user-events'),
    path('my-participations/', views.UserParticipationsView.as_view(), name='user-participations'),
    path('my-tickets/', views.UserTicketsView.as_view(), name='user-tickets'),
    
    # Recherche et filtres avancés
    path('search/', views.EventSearchView.as_view(), name='event-search'),
    path('nearby/', views.NearbyEventsView.as_view(), name='nearby-events'),
    path('recommendations/', views.EventRecommendationsView.as_view(), name='event-recommendations'),
    
    # Statistiques et tendances
    path('stats/', views.event_stats_view, name='event-stats'),
    path('trending/', views.trending_events_view, name='trending-events'),
    path('<int:event_id>/analytics/', views.event_analytics, name='event-analytics'),
    
    # Actions administratives
    path('<int:event_id>/approve/', views.approve_event, name='event-approve'),
    path('<int:event_id>/reject/', views.reject_event, name='event-reject'),
    path('pending-approval/', views.PendingEventsView.as_view(), name='pending-events'),
    
    # Export et rapports
    path('<int:event_id>/export-participants/', views.export_participants, name='export-participants'),
    path('<int:event_id>/generate-report/', views.generate_event_report, name='generate-event-report'),
]

