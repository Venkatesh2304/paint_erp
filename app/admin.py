from collections import defaultdict
import datetime
from enum import Enum
from typing import Callable
import dal.autocomplete
from dal import autocomplete

from django import forms
from django.contrib import admin
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.template.response import TemplateResponse
from django.urls import path
from django.db.models import Q
from django.db import connection
from django.utils.safestring import mark_safe
from jinja2 import Environment, FileSystemLoader
import pandas as pd
from weasyprint import HTML
# Register your models here.
from app.models import Collection, Customer, Outstanding, Product, Sale, SaleProduct, Supplier , Purchase , PurchaseProduct, CollectionBillEntry

Permission = Enum("Permission","add delete change")

class NoDeleteAction(admin.ModelAdmin):
    def get_actions(self,request) : 
        actions = super().get_actions(request)
        if "delete_selected" in actions : actions.pop("delete_selected")
        return actions

class NoSelectActions(admin.ModelAdmin) : 
      empty_actions = []
      def changelist_view(self, request: HttpRequest, extra_context = None) -> TemplateResponse:
          if request.POST.get("action") in self.empty_actions :
             post = request.POST.copy()
             post.update({ "_selected_action" : [] })
             request._set_post(post)
             print("POst")
          return super().changelist_view(request, extra_context)
    
class ModelPermission() : 
    
    permissions = []
    
    def has_add_permission(self, request,obj = None):
        return (Permission.add in self.permissions) 

    def has_change_permission(self, request, obj=None):
        return Permission.change in self.permissions 
    
    def has_delete_permission(self, request, obj=None):
        return Permission.delete in self.permissions
    
class CustomAdminModel(admin.ModelAdmin) : 
    
    show_on_navbar = True
    custom_views:list[tuple[str,str|Callable]] = []
    hidden_fields = []
    allowed_path = None 

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.custom_admin_urls = []

    def save_changelist(self,request) :
        """Safe Work Around to Only save changelist forms (even works with actions, it doesnt trigger actions)""" 
        original_post = request.POST.copy()
        edited_post = request.POST.copy()
        edited_post["_save"] = "Save"
        request._set_post(edited_post)
        super().changelist_view( request )
        request._set_post(original_post)

    def get_urls(self) :
        urls =  super().get_urls()
        custom_urls = [ path(f'{view_name.rstrip("/")}/', 
                             self.admin_site.admin_view( getattr(self,view_fn) if isinstance(view_fn,str) else view_fn ), name=view_name.split("/")[0]) 
                             for view_name , view_fn in self.custom_views ] ## Supports viewname/<str:param>
        return custom_urls + urls 
    
    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if obj:  
            return [field for field in fields if field not in self.hidden_fields]
        return fields
    
    def has_delete_permission(self, request: HttpRequest, obj = None) -> bool:
        if self.allowed_path:
            return (self.allowed_path in request.path)
        return super().has_delete_permission(request, obj)
    
    def has_add_permission(self, request: HttpRequest, obj = None) -> bool:
        if self.allowed_path:
            return (self.allowed_path in request.path)
        return super().has_add_permission(request)
    
    def has_change_permission(self, request: HttpRequest, obj = None) -> bool:
        if self.allowed_path:
            return (self.allowed_path in request.path)
        return super().has_change_permission(request, obj)

class CustomerAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    show_change_link = False
    def has_delete_permission(self, request: HttpRequest, obj = None) -> bool:
        return False 


class SaleProductInline(admin.TabularInline):
    class SaleProductForm(forms.ModelForm):
        dpl = forms.FloatField(label="DPL",required=False,disabled=True)
        margin = forms.FloatField(label="Margin",required=False,disabled=False,initial=0)
        class Meta:
            fields = ["product","dpl","margin","price","qty","color"]
            widgets = {
                'product': dal.autocomplete.ModelSelect2(url='/app/product/product-autocomplete/') ,  
            }

    model = SaleProduct 
    show_change_link = False
    form = SaleProductForm
    extra = 1 
    class Media : 
        js = ('product.js',)

class PurchaseProductInline(admin.TabularInline):
    class PurchaseProductForm(forms.ModelForm):
        dpl = forms.FloatField(label="DPL",required=False,disabled=True)
        class Meta:
            fields = ["product","dpl","base_rate","discount","qty"]
            widgets = {
                'product': dal.autocomplete.ModelSelect2(url='/app/product/product-autocomplete/') ,  
            }

    model = PurchaseProduct
    show_change_link = False
    form = PurchaseProductForm
    extra = 1 
    class Media : 
        js = ('product.js',)


class ProductAdmin(CustomAdminModel,NoDeleteAction,NoSelectActions): 
    
    allowed_path = "product"
    search_fields = ["name","category"]
    list_display = ["name","dpl","closing_stock","value"]

    def closing_stock(self,obj):
        return obj.opening_stock - sum([ sale.qty for sale in obj.sales.all() ]) + sum([ pur.qty for pur in obj.purchase.all() ])

    @admin.display(description="Closing Value")
    def value(self,obj):
        return round(self.closing_stock(obj) * obj.dpl)
    
    def has_delete_permission(self, request: HttpRequest, obj = None) -> bool:
        if obj and ((obj.purchase.all().count() > 0) or (obj.sales.all().count() > 0)) :
            return False
        return super().has_delete_permission(request, obj)
    
    class ProductAutocomplete(autocomplete.Select2QuerySetView):
        def get_queryset(self):
            qs = Product.objects.all()
            qs = qs.filter(Q(name__icontains=self.q)) 
            return qs
    
    def get_info(self,request, name):
        obj = Product.objects.get(name=name)
        return JsonResponse({ 'dpl' : obj.dpl })
        
    custom_views = [ ("get-info/<str:name>","get_info") ,  ("product-autocomplete",ProductAutocomplete.as_view())]
    actions = ["download_closing_stock"]
    empty_actions = ["download_closing_stock"]

    @admin.action(description="Download Closing Stock")
    def download_closing_stock(self,request,queryset):
        df = pd.read_sql(f"""select * , 
                         (select coalesce(sum(qty),0) from app_saleproduct where product_id = name) as sale_qty , 
                         (select coalesce(sum(qty),0) from app_purchaseproduct where product_id = name) as pur_qty  from app_product""",connection)
        df["closing_stock"] = df["opening_stock"] + df["pur_qty"] - df["sale_qty"]
        df.to_csv("closing_stock.csv",index=False)
        response = HttpResponse(open("closing_stock.csv"),content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="closing_stock-{datetime.date.today()}.csv"'
        return response

class SaleAdmin(CustomAdminModel,NoDeleteAction,NoSelectActions):
    inlines = [SaleProductInline]
    fields = ['date','customer','amt']
    readonly_fields = ['amt']
    list_display = ["date","bill_no","customer","amt"]
    ordering = ["-bill_no"]
    allowed_path = "sale"
    list_filter = ["date"]
    actions = ["download_filtered_report"]
    empty_actions = ["download_filtered_report"]
    group = "Billing" 
    autocomplete_fields = ['customer']


    def download_invoice(self,request, bill_no):
        sale = Sale.objects.get(bill_no=bill_no)
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
        

    custom_views = [ ("download/<str:bill_no>","download_invoice") , ]

    def changeform_view(self, request: HttpRequest, object_id: str | None = ..., form_url: str = ..., extra_context: dict[str, bool] | None = ...) -> TemplateResponse:
        if object_id :
            extra_context = extra_context or {}
            extra_context["title"] = mark_safe(f"<a href='/app/sale/download/{object_id}' target='_blank'> Download Invoice </a>")
        return super().changeform_view(request, object_id, form_url, extra_context)
    
    def changelist_view(self, request: HttpRequest, extra_context=None) -> TemplateResponse:
        extra_context = extra_context or {}
        extra_context["title"] = mark_safe(f"<i> Month Sales  </i> : <b>Rs. {Sale.monthly_sales_total()}</b>")
        return super().changelist_view(request, extra_context)
    
    @admin.action(description="Download Filtered Sales")
    def download_filtered_report(self,request,queryset):
        fromd = request.GET.get("date__gte",datetime.date(2024,4,1).strftime("%Y-%m-%d"))
        tod = request.GET.get("date__lte",datetime.date.today().strftime("%Y-%m-%d"))
        df = pd.read_sql(f"select * from app_sale where date between '{fromd}' and '{tod}'",connection)
        # df = pd.read_sql(f"select * from app_sale where bill_no in {tuple(queryset.values_list('bill_no',flat=True))}",connection)
        df["amt"] = df["amt"].round()
        #Add one last row , which says the total amt
        df.loc["Total"] = df.sum(numeric_only=True)
        df.loc["Total"]["bill_no"] = "Total"
        df.to_csv("sales.csv",index=False)
        response = HttpResponse(open("sales.csv"),content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="sales-{datetime.date.today()}.csv"'
        return response
    
    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        sale = form.instance
        sale.amt = round(sum([sp.qty * sp.price * (1 + sp.product.rt/100) for sp in sale.products.all()]))
        sale.save()
    
class PurchaseAdmin(admin.ModelAdmin):
    group = "Billing" 
    inlines = [PurchaseProductInline]
    def changelist_view(self, request: HttpRequest, extra_context=None) -> TemplateResponse:
        extra_context = extra_context or {}
        extra_context["title"] = mark_safe(f"<i> Month Purchase  </i> : <b>Rs. {Purchase.monthly_purchase_total()}</b>")
        return super().changelist_view(request, extra_context)

class OutstandingAdmin(ModelPermission,CustomAdminModel,NoSelectActions):
    permissions = []
    list_display = ["date","customer","bill_no","balance"]
    search_fields = ["customer","bill_no"]
    actions = ["download_report"]
    empty_actions = ["download_report"]
    
    def changelist_view(self, request: HttpRequest, extra_context=None) -> TemplateResponse:
        extra_context = extra_context or {}
        extra_context["title"] = mark_safe(f"<i> Total Outstanding </i> : <b>Rs. {Outstanding.total()}</b>")
        return super().changelist_view(request, extra_context)
    
    @admin.action(description="Download Full Report")
    def download_report(self,request,queryset):
        df = pd.read_sql(f"select * from app_outstanding",connection)
        df["days"] =  (pd.Timestamp.today().normalize() - pd.to_datetime(df["date"])).dt.days
        df["balance"] = -df["balance"].round()
        df = df[["customer","bill_no","days","balance"]]
        df.sort_values("days",inplace=True,ascending=False)
        df.loc["Total"] = df.sum(numeric_only=True)
        df.loc["Total","days"] = ""
        df.loc["Total","bill_no"] = "Total"
        df.to_csv("outstanding.csv",index=False)
        response = HttpResponse(open("outstanding.csv"),content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="outstanding-{datetime.date.today()}.csv"'
        return response
    
    class BillAutocomplete(autocomplete.Select2QuerySetView):
        def get_queryset(self):
            qs = Outstanding.objects.all()
            qs = qs.filter(Q(bill_no__icontains=self.q, customer = self.forwarded.get("customer",None))) 
            return qs
    
    def get_outstanding(self,request, bill_no):
        try:
            obj = Outstanding.objects.get(bill_no=bill_no)
            return JsonResponse({ 'balance': str(round(-obj.balance,2)) , 'date' : obj.date })
        except Outstanding.DoesNotExist:
            return JsonResponse({ 'balance': 0 , 'date' : None })

    custom_views = [("get-outstanding/<str:bill_no>","get_outstanding"),
                    ("bill-autocomplete",BillAutocomplete.as_view())]

class CollectionBillEntryInline(admin.TabularInline) : 
    class BillForm(forms.ModelForm):
        balance  = forms.FloatField(label="Balance",required=False,disabled=False,initial=0)
        customer  = forms.CharField(label="Customer",required=False,disabled=False,widget=forms.HiddenInput())
        date  = forms.DateField(label="Bill Date",required=False,disabled=False)
        class Meta:
            fields = ["bill","date","balance","amt","customer"]
            widgets = {
                'bill': dal.autocomplete.ModelSelect2(url='/app/outstanding/bill-autocomplete/',
                                                      forward=["customer"]) ,  
            }
            
    show_change_link = False
    form = BillForm
    extra = 0
    model = CollectionBillEntry
    class Media:
        js = ('coll.js',)

class CollectionAdmin(NoDeleteAction) :
    inlines = [CollectionBillEntryInline]
    autocomplete_fields = ['customer']
    list_display = ["date","customer","mode","amt"]
    def changelist_view(self, request: HttpRequest, extra_context=None) -> TemplateResponse:
        extra_context = extra_context or {}
        extra_context["title"] = mark_safe(f"<i> Month Collection  </i> : <b>Rs. {Collection.monthly_coll_total()}</b>")
        return super().changelist_view(request, extra_context)
    



class AdminSite(admin.AdminSite):
    site_title = "Devaki Paints"
    site_header = "Devaki Paints & Hardware"
    enable_nav_sidebar = True 
    ordered = ["Sale","Collection","Outstanding","Purchase","Product","Customer","Supplier"]
    def get_app_list(self, request,app_label = None):
        app_list = super().get_app_list(request,app_label)
        for app in app_list:
            models = [ model_dictionary for model_dictionary in app["models"] ]
            models.sort(key = lambda x : self.ordered.index(x["object_name"]))
            app["models"] = models
        return app_list


admin.site = AdminSite(name='myadmin')
admin.site.register(Customer,CustomerAdmin)
admin.site.register(Supplier)
admin.site.register(Product,ProductAdmin)
admin.site.register(Sale,SaleAdmin)
admin.site.register(Purchase,PurchaseAdmin)
admin.site.register(Outstanding,OutstandingAdmin)
admin.site.register(Collection,CollectionAdmin)

