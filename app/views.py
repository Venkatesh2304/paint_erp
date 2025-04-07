from collections import defaultdict
from django.http import HttpResponse, JsonResponse
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
from rest_framework.filters import OrderingFilter

#Create a listview for the sales
from rest_framework import generics
from .models import * 
from django.db.models import Sum,F
from django.db.models.functions import Coalesce
from rest_framework.exceptions import ValidationError


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
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_value_regex = '[^/]+'
    filter_backends = (DjangoFilterBackend,OrderingFilter)
    filterset_fields = { "name" : ["icontains"] }
    order_by = "__all__"
    

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
    queryset = Purchase.objects.all()
    serializer_class = PurchaseSerializer
    filter_backends = (DjangoFilterBackend,OrderingFilter)
    filterset_fields = {"bill_no" : ["exact","icontains"],"supplier__name" : ["icontains"],"date":["exact","gte","lte"]}
    order_by = "__all__"
    ordering = ['-date','-bill_no']

class SalesListView(viewsets.ModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SalesSerializer
    filter_backends = (DjangoFilterBackend,OrderingFilter)
    filterset_fields = {"bill_no" : ["exact","icontains"],"customer__name" : ["icontains"],"date":["exact","gte","lte"]}
    order_by = "__all__"
    ordering = ['-date','-bill_no']

    def perform_create(self, serializer):
        res = super().perform_create(serializer)
        self.custom_validate(serializer)
        return res
    
    def perform_update(self, serializer):
        res = super().perform_update(serializer)
        self.custom_validate(serializer)
        return res
    
    def custom_validate(self,serializer) : 
        products = SaleProduct.objects.filter(sale_id=serializer.instance.bill_no)
        idx = 0
        errs = [{}] * len(products)
        for product in products.all():
            print(product.product.closing_stock() , product.qty,product.product.name)
            if (product.product.closing_stock() < 0): 
                Sale.objects.get(bill_no = serializer.instance.bill_no).delete()
                # errs[idx] = {"qty" : "Stock Not Available"}
                raise ValidationError({'detail': f"Stock Not Available {product.product.name}"})
            idx += 1

    
class OutstandingListView(viewsets.ModelViewSet):
    queryset = Outstanding.objects.all()
    serializer_class = OutstandingSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,OrderingFilter)
    filterset_fields = {"customer" : ["exact"],"date":["exact","gte","lte"]}
    order_by = "__all__"
    ordering = ['date']

class CollectionListView(viewsets.ModelViewSet):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer
    filter_backends = (DjangoFilterBackend,OrderingFilter)
    order_by = "__all__"
    ordering = ['-id']
    filterset_fields = {"date" : ["exact"],"mode" : ["exact"],"customer__name" : ["icontains"],"id":["exact"]}



def download_invoice(request) :
    bill = request.GET.get('bill', '')
    sale = Sale.objects.get(bill_no=bill)
    taxes = defaultdict(lambda : 0)
    total_amt = 0
    total_qty = 0
    total_gst = 0
    total_taxable = 0 
    for sp in sale.products.all() :
        taxes[sp.product.rt] += sp.qty * sp.price 
        total_taxable += sp.qty * sp.price
        total_amt += sp.qty * sp.price * (1 + sp.product.rt/100)
        total_qty += sp.qty
        total_gst += sp.qty * sp.product.rt * sp.price / 100
    total_amt -= sale.discount
    
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
            {"taxable" : round(taxes[rt],2) , "rate" : round(rt) , "cgst" : round(taxes[rt] * rt/200,2) , "sgst" : round(taxes[rt] * rt/200,2)}
            for rt in taxes
        ],
        "total":  round(total_amt) , 
        "total_gst" : round(total_gst,2) , 
        "total_cgst" : round(total_gst/2,2) , 
        "total_sgst" : round(total_gst/2,2) , 
        "total_taxable" : round(total_taxable,2) , 
        "total_discount" : round(sale.discount) ,
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
        if not bills.empty :
            products = product_model.objects.all().filter( **({ f"{bill_foriegn_key}_id__in" :  bills.bill_no.values}) )  
            products = pd.DataFrame(list(products.values()))
            products = products.groupby('product_id').agg({'qty':'sum','price':'mean'}).reset_index()
        else : 
            products = pd.DataFrame()
        with pd.ExcelWriter(f'{type}.xlsx') as writer:
            bills.round(2).to_excel(writer, sheet_name='bill_wise', index=False)
            day_wise.round(2).to_excel(writer, sheet_name='day_wise', index=False)
            products.round(2).to_excel(writer, sheet_name='products', index=False)

    if type == "collection" : 
        colls = pd.DataFrame(list(queryset.order_by("id").values()))
        day_wise = colls.pivot_table(index=["date"],columns=["mode"],values=["amt"]).reset_index() if not colls.empty else pd.DataFrame()
        day_wise.columns = [ col[len(col) - 1] if isinstance(col, tuple) else col for col in day_wise.columns.values]

        if not colls.empty:
            bill_wise = CollectionBillEntry.objects.all().filter( **({ f"collection_id__in" :  colls.id.values}) )
            bill_wise = pd.DataFrame(list(bill_wise.values()))
            bill_wise = bill_wise.groupby('bill_id').agg({'amt':'sum'}).reset_index()
        else : 
            bill_wise = pd.DataFrame()

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


def dashboard(request) : 
    
    data = {"totals" : {},"month_wise" : {},"day_wise" : {}}

    for [key,model] in [["sales",Sale],["purchase",Purchase]] :
        queryset = model.objects.all()
        queryset = queryset.filter(date__gte = datetime.datetime.now() - datetime.timedelta(days=150))
        queryset = queryset.annotate(month = models.functions.TruncMonth('date'))
        queryset = queryset.values('month').annotate(total = Sum('amt')).order_by('month')
        queryset = pd.DataFrame(list(queryset)).rename(columns={"total" : key}).round()
        queryset['month'] = pd.to_datetime(queryset['month'],format="%Y-%m-%d").dt.strftime('%b')
        data["month_wise"][key] = queryset.to_dict('records')

        #Get Day wise sales for the last 15 days 
        queryset = model.objects.all()
        queryset = queryset.filter(date__gte = datetime.datetime.now() - datetime.timedelta(days=15))
        queryset = queryset.annotate(day = models.functions.TruncDay('date'))
        queryset = queryset.values('day').annotate(total = Sum('amt')).order_by('day')
        queryset = pd.DataFrame(list(queryset)).rename(columns={"total" : key}).round()
        queryset['day'] = pd.to_datetime(queryset['day'],format="%Y-%m-%d").dt.strftime('%d')
        data["day_wise"][key] = queryset.to_dict('records') 

    def indian_format(number):
        num_str = str(number)[::-1]  # Reverse string for easier processing
        parts = [num_str[:3]] + [num_str[i:i+2] for i in range(3, len(num_str), 2)]
        return ','.join(parts)[::-1] 

    #Get the total sales for this month alone 
    for [key,model] in [["sales",Sale],["purchase",Purchase],["collection",Collection]] :
        queryset = model.objects.all()
        queryset = queryset.filter(date__gte = datetime.datetime.now().replace(day=1))
        queryset = queryset.aggregate(total = Sum('amt'))
        data['totals'][key] = indian_format(round(queryset['total'] or 0))
    
    data["month"] = datetime.datetime.now().strftime("%b")
    data['totals']['outstanding'] = round(-Outstanding.objects.all().filter(balance__lte = -1).aggregate(total = Sum('balance'))['total'] or 0)
    return JsonResponse(data)   

def product_helper(request) : 
    #Get the set of categoires , companies , sizes for the products
    categories = set()
    companies = set()
    sizes = set()
    sizes = defaultdict(set)
    products = Product.objects.all()
    bases = defaultdict(set)
    for product in products :
        categories.add(product.category)
        companies.add(product.company)
        sizes[product.category].add(product.base)
        bases[product.category].add(product.base)
    data = {
        "categories" : list(categories),
        "companies" : list(companies),
        # "sizes" : {cat : list(sizes[cat]) for cat in sizes.keys()}, 
        "bases" : {cat : list(bases[cat]) for cat in bases.keys()}, 
    }
    return JsonResponse(data)
        
