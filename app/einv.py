from app.models import Sale 
sale: Sale = Sale.objects.get(id=1)
total_taxable_value = sum([item.price * item.qty for item in sale.products.all()])

default_einv =   {
        "Version": "1.1",
        "TranDtls": {
            "TaxSch": "GST",
            "SupTyp": "B2B"
        },
        "DocDtls": {
            "Typ": "INV",
            "No": sale.bill_no,
            "Dt": sale.date.strftime("%d/%m/%Y")
        },
        "BuyerDtls": {
            "Gstin": sale.customer.gstin ,
            "LglNm": sale.customer.name ,
            "Pos": "33",
            "Addr1": sale.customer.address,
            "Pin": sale.customer.pincode ,
            "Loc": sale.customer.city.capitalize() ,
            "Stcd": "33"
        },
        "ValDtls": {
            "AssVal": round(total_taxable_value,2) ,
            "TotInvVal": round(sale.amt)
        },
        "ItemList": [
            {
                "IsServc": "N",
                "HsnCd": "34025000",
                "Qty": 1200,
                "Unit": "PCS",
                "UnitPrice": 7.85,
                "TotAmt": 9416.4,
                "Discount": 867.91,
                "AssAmt": 8548.49,
                "GstRt": 18.0,
                "CgstAmt": 769.36,
                "SgstAmt": 769.36,
                "TotItemVal": 10087.21,
                "SlNo": "1"
            }
        ],
}
