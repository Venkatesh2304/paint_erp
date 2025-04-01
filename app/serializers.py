#Serialise Sales 
from rest_framework import serializers
from drf_writable_nested import WritableNestedModelSerializer

from .models import * 

class OutstandingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Outstanding
        fields = '__all__'

class CollectionBillSerializer(serializers.ModelSerializer):
    balance = serializers.SerializerMethodField()
    class Meta:
        model = CollectionBillEntry
        fields = ['bill','amt','balance']

    def get_balance(self,obj):
        try : 
            outstanding = Outstanding.objects.get(bill_no=obj.bill_id)
            return  -outstanding.balance
        except Outstanding.DoesNotExist:
            return 0 

class CollectionSerializer(WritableNestedModelSerializer):
    bills = CollectionBillSerializer(many=True)
    class Meta:
        model = Collection
        fields = '__all__'

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'


class SupplierNameSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        return instance.name
    class Meta:
        model = Supplier 
        fields = ['name']

class CustomerNameSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        return instance.name
    class Meta:
        model = Customer 
        fields = ['name']

class ProductNameSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        return instance.name
    class Meta:
        model = Product 
        fields = ['name']

class ProductSerializer(serializers.ModelSerializer):
    closing_stock = serializers.SerializerMethodField()
    class Meta:
        model = Product 
        fields = ["name","company","category","base","size","dpl","mrp","opening_stock","hsn","rt","closing_stock"]
    def get_closing_stock(self, obj):
        return obj.closing_stock()
    

class SaleProductSerializer(serializers.ModelSerializer):
    dpl = serializers.SlugRelatedField(source="product",slug_field='dpl', read_only=True)
    rt = serializers.SlugRelatedField(source="product",slug_field='rt', read_only=True)
    margin = serializers.SerializerMethodField()
    class Meta:
        model = SaleProduct
        fields = ['product', 'qty','price','dpl','margin',"color","rt"]

    def get_margin(self,obj) : 
        return round( (obj.price - obj.product.dpl) * 100 / obj.product.dpl,2) if obj.product.dpl else "0"
    
class SalesSerializer(WritableNestedModelSerializer):
    products = SaleProductSerializer(many=True)
    class Meta:
        model = Sale
        fields = '__all__'

class PurchaseProductSerializer(serializers.ModelSerializer):
    dpl = serializers.SlugRelatedField(source="product",slug_field='dpl', read_only=True)
    class Meta:
        model = PurchaseProduct
        fields = ['product', 'qty','dpl','discount',"base_rate"]


class PurchaseSerializer(WritableNestedModelSerializer):
    products = PurchaseProductSerializer(many=True)
    class Meta:
        model = Purchase
        fields = '__all__'
