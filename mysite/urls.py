"""
URL configuration for mysite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from rest_framework import routers
from app.views import *
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.urls import re_path, include

router = routers.DefaultRouter()
router.register(r'sale', SalesListView)
router.register(r'purchase', PurchaseListView)
router.register(r'product', ProductListView)
router.register(r'customer', CustomerListView)
router.register(r'supplier', SupplierListView)
router.register(r'outstanding', OutstandingListView)
router.register(r'collection', CollectionListView)
router.register(r'productname', ProductNameListView, basename='product-list')
router.register(r'customername', CustomerNameListView, basename='customer-list')
router.register(r'suppliername', SupplierNameListView, basename='supplier-list')

urlpatterns = [
        re_path(
        r'^sale/(?P<bill_no>.+)/$',
        SalesListView.as_view({
            'get': 'retrieve',
            'put': 'update',
            'patch': 'partial_update',
            'delete': 'destroy',
        }),
        name='sale'
        ),
        path('', include(router.urls)),
        path('invoice/', download_invoice),
        path('report/', report),
        path('dashboard/', dashboard),
        path('product_helper/', product_helper),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
