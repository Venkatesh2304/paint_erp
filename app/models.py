import datetime
from typing import Any, Iterable
from django.db import models
import pandas as pd

# Create your models here.
# Product : name(pk) , company , category , base , size(text), pur_price , sale_price , opening_stock 
# hsn , rt .
# Name is auto generated by the system , which is a combination of category + base + size .
class Product(models.Model):
    name = models.CharField(max_length=100, primary_key=True, editable=False)
    company = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    base = models.CharField(max_length=100,null=True,blank=True)
    size = models.CharField(max_length=100)
    dpl = models.IntegerField(db_default = 0 , default=0)
    mrp = models.IntegerField()
    opening_stock = models.IntegerField(default=0)
    hsn = models.CharField(max_length=100)
    rt = models.FloatField()
    
    def closing_stock(self) : 
        return self.opening_stock - sum([ sale.qty for sale in self.sales.all() ]) + sum([ pur.qty for pur in self.purchase.all() ])

    def save(self, *args, **kwargs):
        self.category = self.category.upper()
        self.base = (self.base or "").upper()
        self.size = (self.size or "").upper()
        self.name = f"{self.category} {self.base} {self.size}"
        return super().save(*args, **kwargs)

    def can_delete(self) :
        return (not self.sales.exists()) and (not self.purchase.exists())
    
    def __str__(self):
        return self.name
    


# Customer : name(pk) , gstin , phone , address 
class Customer(models.Model):
    name = models.CharField(max_length=100, primary_key=True)
    gstin = models.CharField(max_length=100,null=True,blank=True)
    phone = models.CharField(max_length=100,null=True,blank=True)
    address = models.TextField()
    city = models.CharField(max_length=100,default = "Trichy",db_default="Trichy")
    pincode = models.CharField(max_length=100,default = "620001",db_default="620001")
    opening_balance = models.FloatField(default=0,db_default=0)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        Outstanding.update()
        
    def __str__(self):
        return self.name
    
# Supplier : name(pk) , gstin , phone , address
class Supplier(models.Model):
    name = models.CharField(max_length=100, primary_key=True)
    gstin = models.CharField(max_length=100,null=True,blank=True)
    phone = models.CharField(max_length=100,null=True,blank=True)
    address = models.TextField(null=True,blank=True)

    def __str__(self):
        return self.name
    
# Sale : bill_no(pk) , date , customer , amt 
class Sale(models.Model):
    bill_no = models.CharField(max_length=15,primary_key=True)
    date = models.DateField(default=datetime.date.today)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    amt = models.FloatField(null=True,verbose_name="Total Bill Value")
    discount = models.IntegerField(default=0,verbose_name="Discount",db_default=0)

    @staticmethod 
    def monthly_sales_total() : 
        return round(Sale.objects.filter(date__month=datetime.date.today().month).aggregate(models.Sum('amt'))['amt__sum'] or 0)
        
    def save(self, *args, **kwargs):
        if (not self.bill_no) or (self.bill_no == "TEMPORARY"):  # Generate only if not already set
            last_bill = Sale.objects.order_by('-bill_no').first()
            if last_bill:
                last_number = int(last_bill.bill_no[1:])  # Extract number part
                new_number = f"S{last_number + 1:05d}"  # Increment and format
            else:
                new_number = "S00001"  # First bill case
            self.bill_no = new_number
        super().save(*args, **kwargs)
        Outstanding.update()
     
    def delete(self,*args, **kwargs):
        super().delete(*args, **kwargs)
        Outstanding.update()

    def __str__(self):
        return str(self.bill_no)
    
    def einv_dict(self) : 
        return {
        "Version": "1.1",
        "TranDtls": {
            "TaxSch": "GST",
            "SupTyp": "B2B"
        },
        "DocDtls": {
            "Typ": "INV",
            "No": self.bill_no,
            "Dt": self.date.strftime("%d/%m/%Y")
        },
        "BuyerDtls": {
            "Gstin": self.customer.gstin ,
            "LglNm": self.customer.name ,
            "Pos": "33",
            "Addr1": self.customer.address,
            "Pin": self.customer.pincode ,
            "Loc": self.customer.city.capitalize() ,
            "Stcd": "33"
        },
        "ValDtls": {
            "AssVal": round(sum([item.price * item.qty for item in self.products.all()]),2) ,
            "TotInvVal": self.amt
        },
        "ItemList": [
            {
                "IsServc": "N",
                "HsnCd": item.product.hsn ,
                "Qty": item.qty,
                "Unit": "NOS",
                "UnitPrice": round(item.price,2) ,
                "TotAmt": round(item.price*item.qty*(1+item.product.rt/100),2),
                "Discount": 0,
                "AssAmt": round(item.price*item.qty,2),
                "GstRt": round(item.product.rt,1),
                "CgstAmt": round(item.price*item.qty*item.product.rt/200,2) ,
                "SgstAmt": round(item.price*item.qty*item.product.rt/200,2) ,
                "TotItemVal": round(item.price*item.qty*(1+item.product.rt/100),2),
                "SlNo": str(idx+1) 
            } for idx,item in enumerate(self.products.all())
        ],
}

# SaleProduct : sale , product , qty , price
class SaleProduct(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE,related_name="products")
    product = models.ForeignKey(Product, on_delete=models.DO_NOTHING,related_name="sales")
    qty = models.IntegerField()
    price = models.FloatField(verbose_name="Sale Price / Unit")
    color = models.IntegerField(verbose_name="Color",null=True,blank=True)
    
    

    def __str__(self):
        return f"{self.sale} - {self.product}"
    
# Purchase : bill_no(pk) , date , supplier , amt
class Purchase(models.Model):
    bill_no = models.CharField(max_length=15,primary_key=True)
    date = models.DateField(default=datetime.date.today)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    amt = models.FloatField(null=True,verbose_name="Total Bill Value")

    @staticmethod
    def monthly_purchase_total() :
        return round(Purchase.objects.filter(date__month=datetime.date.today().month).aggregate(models.Sum('amt'))['amt__sum'] or 0)
    
    def __str__(self):
        return str(self.bill_no)
    
# PurchaseProduct : purchase , product , qty , price
class PurchaseProduct(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE,related_name="products")
    product = models.ForeignKey(Product, on_delete=models.DO_NOTHING,related_name="purchase")
    qty = models.IntegerField()
    base_rate = models.FloatField(verbose_name="Base Rate / Unit")
    discount = models.FloatField(verbose_name="Total Discount")
    price = models.FloatField(verbose_name="Purchase Price / Unit",null=True,blank=True)
    
    def save(self, *args, **kwargs):
        self.price = self.base_rate - (self.discount/self.qty) 
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.purchase} - {self.product}"





# Collection : date , amt , customer , mode , bill_no
class Collection(models.Model):
    date = models.DateField(verbose_name="Collection Date",default=datetime.date.today)
    customer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING)
    mode = models.CharField(max_length=100,choices=[("Cash","Cash"),("Cheque","Cheque"),("UPI","UPI")])
    amt = models.FloatField(verbose_name="Total Collection")

    @staticmethod 
    def monthly_coll_total() : 
        return round(Collection.objects.filter(date__month=datetime.date.today().month).aggregate(models.Sum('amt'))['amt__sum'] or 0)
       
    def __str__(self):
        return f"{self.date} - {self.customer} - {self.amt}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        Outstanding.update()

    def delete(self,*args, **kwargs):
        super().delete(*args, **kwargs)
        Outstanding.update()

# CollectionEntry : bill_no , date
class CollectionBillEntry(models.Model):     
    collection = models.ForeignKey("app.Collection", on_delete=models.CASCADE,related_name="bills")
    bill = models.ForeignKey(Sale, on_delete=models.DO_NOTHING,verbose_name="Sales Bill No")
    amt = models.FloatField(verbose_name="Amount Collected")
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        Outstanding.update()

class Outstanding(models.Model) : 
      customer = models.CharField(max_length=100)
      bill_no = models.CharField(max_length=20,primary_key=True)
      balance = models.FloatField()
      date = models.DateField()
      
      def __str__(self):
          return f"{self.bill_no}"
      
      @staticmethod 
      def total() : 
            return round(abs(Outstanding.objects.aggregate(models.Sum('balance'))['balance__sum'] or 0))
      
      @staticmethod               
      def update() :
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute( 'DELETE FROM app_outstanding' )
            cursor.execute('''
                INSERT INTO app_outstanding (customer, bill_no, balance, date)
                SELECT customer_id as customer   , bill_no, SUM(amt) AS balance, MIN(date) AS date 
                FROM (
                SELECT customer_id , bill_no , date, -amt as amt  FROM app_sale
                UNION ALL
                SELECT customer_id, bill_id as bill_no , date, amt FROM (select app_collectionbillentry.amt as amt , * from app_collection join app_collectionbillentry on app_collection.id = app_collectionbillentry.collection_id)
                ) 
                GROUP BY customer_id , bill_no 
                HAVING ABS(SUM(amt)) > 1 
                
            ''')
      
      class Meta : 
            verbose_name_plural = 'Outstanding'
            ordering = ['bill_no']
