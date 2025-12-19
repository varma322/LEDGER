from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    path('add-partner/', views.add_partner, name='add_partner'),
    
    # Ledger
    path('ledger/', views.ledger, name='ledger'),
    
    # Procurement
    path('procurement/', views.procurement, name='procurement'),
    path('deal/<int:deal_id>/update/', views.update_deal, name='update_deal'),
    path('deal/<int:deal_id>/to-warehouse/', views.move_to_warehouse, name='move_to_warehouse'),
    
    # Logistics
    path('logistics/', views.logistics, name='logistics'),
    path('deal/<int:deal_id>/mark-shipped/', views.mark_shipped, name='mark_shipped'),
    path('deal/<int:deal_id>/mark-delivered/', views.mark_delivered, name='mark_delivered'),
    path('deal/<int:deal_id>/commission-invoice/', views.generate_commission_invoice, name='commission_invoice'),
]
