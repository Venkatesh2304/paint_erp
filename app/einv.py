from app.models import Sale 
sale: Sale = Sale.objects.get(id=1)
total_taxable_value = sum([item.price * item.qty for item in sale.products.all()])

default_einv =   