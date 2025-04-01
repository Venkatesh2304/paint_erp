from collections import defaultdict
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import path
import django_filters
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
# from .admin import admin_site

from app.serializers import * 
from rest_framework import permissions, viewsets
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.utils.cache import get_cache_key
from django.core.cache import cache
from django.utils.http import quote_etag
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import PermissionDenied

#Create a listview for the sales
from rest_framework import generics
from .models import * 
from django.db.models import Sum,F
from django.db.models.functions import Coalesce

class OutstandingListView(viewsets.ModelViewSet):
    class Filter(django_filters.FilterSet):
        class Meta:
            model = Outstanding
            fields = '__all__'
            
    filter_backends = (DjangoFilterBackend,)
    filterset_class = Filter
    queryset = Outstanding.objects.all()
    serializer_class = OutstandingSerializer
    pagination_class = None 

class CollectionListView(viewsets.ModelViewSet):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer

class SupplierListView(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer


class CustomerListView(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

class SupplierNameListView(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierNameSerializer
    pagination_class = None

class CustomerNameListView(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerNameSerializer
    pagination_class = None

class ProductNameListView(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductNameSerializer
    pagination_class = None
    


class ProductListView(viewsets.ModelViewSet):
    
    class Filter(django_filters.FilterSet):
        name = django_filters.CharFilter(lookup_expr='icontains')
        class Meta:
            model = Product
            fields = '__all__'
            
    filter_backends = (DjangoFilterBackend,)
    filterset_class = Filter


    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_value_regex = '[^/]+'
    

    def perform_destroy(self, instance):
        if not instance.can_delete():
            raise PermissionDenied("You Cannot Delete The Product as it is Billed.")
        instance.delete()
    

    # @method_decorator(cache_page(3600))
    # def list(self, request, *args, **kwargs):
    #     response = super().list(request, *args, **kwargs)
    #     response['ETag'] = self.get_etag(request)
    #     return response

    # def get_etag(self, request):
    #     queryset = self.get_queryset()
    #     etag = f"v1-{len(queryset)}"
    #     return quote_etag(etag)

class PurchaseListView(viewsets.ModelViewSet):
    class Filter(django_filters.FilterSet):
        bill_no = django_filters.CharFilter(lookup_expr='icontains')
        class Meta:
            model = Purchase
            fields = '__all__'
    filter_backends = (DjangoFilterBackend,)
    filterset_class = Filter

    queryset = Purchase.objects.all()
    serializer_class = PurchaseSerializer


class SalesListView(viewsets.ModelViewSet):
    class Filter(django_filters.FilterSet):
        bill_no = django_filters.CharFilter(lookup_expr='icontains')
        class Meta:
            model = Sale
            fields = '__all__'
    filter_backends = (DjangoFilterBackend,)
    filterset_class = Filter

    queryset = Sale.objects.all()
    serializer_class = SalesSerializer


def download_invoice(request,bill) :

    sale = Sale.objects.get(bill_no=bill)
    taxes = defaultdict(lambda : 0)
    total_amt = 0
    total_qty = 0
    total_gst = 0
    for sp in sale.products.all() :
        taxes[sp.product.rt] += sp.qty * sp.price 
        total_amt += sp.qty * sp.price * (1 + sp.product.rt/100)
        total_qty += sp.qty
        total_gst += sp.qty * sp.product.rt * sp.price / 100
    
    invoice_data = {
        "invoice_no": sale.bill_no,
        "date": sale.date.strftime("%d %b %Y"),
        "due_date": (sale.date + datetime.timedelta(days=28)).strftime("%d %b %Y"),
        "customer_name": sale.customer.name.upper(),
        "customer_address": sale.customer.address,
        "customer_pincode": sale.customer.pincode,
        "party_gstin" : sale.customer.gstin or "-" , 
        "items": [
            {"no" : idx+1 , "name": sp.product.name, "hsn": sp.product.hsn, "qty": sp.qty, 
             "price": "₹ " + str(round(sp.price,2)), "colour_code" :  sp.color or "" , 
             "amount": "₹ " + str(round(sp.qty * sp.price,2)) }
            for idx,sp in enumerate(sale.products.all()) 
        ] + [{"name":"","hsn":"","qty":"","price":"","gst":"","amount":""}] * 3 ,
        "taxes" : [
            {"taxable" : taxes[rt] , "rate" : rt , "cgst" : round(taxes[rt] * rt/200,2) , "sgst" : round(taxes[rt] * rt/200,2)}
            for rt in taxes
        ],
        "total":  round(total_amt) , 
        "total_gst" : round(total_gst,2) , 
        "total_cgst" : round(total_gst/2,2) , 
        "total_sgst" : round(total_gst/2,2) , 
        "total_amt" : round(total_amt) , 
        "round_off" : round(round(total_amt) - total_amt,2) ,
        "total_qty" : total_qty ,
    }
    
    env = Environment(loader=FileSystemLoader("."))
    template = env.get_template("invoice_template.html")
    html_out = template.render(invoice_data)
    HTML(string=html_out).write_pdf("invoice.pdf")
    return HttpResponse(open("invoice.pdf","rb"),content_type='application/pdf')

def report(request):
    
    def get_queryset(model):
        queryset = model.objects.all()
        filter_params = {}
        for key, value in request.GET.items():
            if '__' in key:  # Handle lookups like 'field__lookup'
                field_name, lookup_type = key.split('__', 1)
                if hasattr(model, field_name):
                    filter_params[f'{field_name}__{lookup_type}'] = value
            else:
                if hasattr(model, key):
                    filter_params[key] = value
        if filter_params:
            queryset = queryset.filter(**filter_params)
        return queryset

    type = request.GET.get('type')
    models = {"sales": Sale , "purchase": Purchase , "collection": Collection, "outstanding" : Outstanding ,
              "stock" : Product }
    queryset = get_queryset(models[type])

    if type in ['purchase','sales'] :
        bills = pd.DataFrame(list(queryset.order_by("bill_no").values()))
        day_wise = bills.groupby('date').agg({'amt':'sum'}).reset_index() if not bills.empty else pd.DataFrame()
        product_model = SaleProduct if type == 'sales' else PurchaseProduct
        bill_foriegn_key = 'sale' if type == 'sales' else 'purchase'
        products = product_model.objects.all().filter( **({ f"{bill_foriegn_key}_id__in" :  bills.bill_no.values}) )
        products = pd.DataFrame(list(products.values()))
        if not products.empty:
            products = products.groupby('product_id').agg({'qty':'sum','price':'mean'}).reset_index()
        with pd.ExcelWriter(f'{type}.xlsx') as writer:
            bills.round(2).to_excel(writer, sheet_name='bill_wise', index=False)
            day_wise.round(2).to_excel(writer, sheet_name='day_wise', index=False)
            products.round(2).to_excel(writer, sheet_name='products', index=False)

    if type == "collection" : 
        colls = pd.DataFrame(list(queryset.order_by("id").values()))
        day_wise = colls.pivot_table(index=["date"],columns=["mode"],values=["amt"]).reset_index() if not colls.empty else pd.DataFrame()
        day_wise.columns = [ col[len(col) - 1] if isinstance(col, tuple) else col for col in day_wise.columns.values]

        bill_wise = CollectionBillEntry.objects.all().filter( **({ f"collection_id__in" :  colls.id.values}) )
        bill_wise = pd.DataFrame(list(bill_wise.values()))
        if not bill_wise.empty:
            bill_wise = bill_wise.groupby('bill_id').agg({'amt':'sum'}).reset_index()
        with pd.ExcelWriter(f'{type}.xlsx') as writer:
            colls.round(2).to_excel(writer, sheet_name='Party wise', index=False)
            day_wise.round(2).to_excel(writer, sheet_name='Day wise', index=False)
            bill_wise.round(2).to_excel(writer, sheet_name='Bill wise', index=False)

    if type == "outstanding" :
        df = pd.DataFrame(list(queryset.filter(balance__lte = -1).order_by("date").values()))
        if not df.empty:
            df["balance"] = -df["balance"]
            df["days"] =  (pd.Timestamp.today().normalize() - pd.to_datetime(df["date"])).dt.days
        with pd.ExcelWriter(f'{type}.xlsx') as writer:
            df.round(2).to_excel(writer, sheet_name='Outstanding', index=False)

    if type == "stock" :
        queryset = queryset.annotate(closing_stock = 
                                     F("opening_stock") - Coalesce(Sum('sales__qty'),0) +   Coalesce(Sum('purchase__qty'),0) ) 
        df = pd.DataFrame(list(queryset.order_by("name").values()))
        df["total"] = df["closing_stock"] * df["dpl"]
        with pd.ExcelWriter(f'{type}.xlsx') as writer:
            df.round(2).to_excel(writer, sheet_name='Stock', index=False)

    return HttpResponse(open(f"{type}.xlsx","rb"),content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        headers={'Content-Disposition': f'attachment; filename="{type}.xlsx"'})
