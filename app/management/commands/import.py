from app.management.commands.common import * 
import pandas as pd
df = pd.read_excel("opening_stock.xlsx")
df["base"] = (df["COLUR"].fillna("") + df["BASE"].fillna("")).str.upper().str.strip()
df["company"] = df["COMPANY"].str.upper().str.strip()
df["category"] = df["ITEM"].str.upper().str.strip()
df["size"] = df["LITRES"].astype(str).apply(lambda x : x + " LTR" if x.replace(".","").isnumeric() else x.upper().strip() ).fillna("")
df["opening_stock"] = df["STOCK"].astype(int)
df["dpl"] = df["DPL"].fillna(0)
df["hsn"] = df["HSN"]
df["rt"] = 18
df["mrp"] = df["MRP"].fillna(0)
df = df[["base","company","category","size","dpl","opening_stock","hsn","rt","mrp"]]
df["name"] = (df["category"] + " " + df["base"] + " " + df["size"]).str.strip()
print( df[df.name.duplicated()] )

# query_db("delete from app_saleproduct")
# query_db("delete from app_purchaseproduct")
# query_db("delete from app_purchase")
query_db("delete from app_product")
bulk_raw_insert("product",df,ignore=False)

df = pd.read_excel("opening_party.xlsx")
print(df)
df["name"] = df["Name"].str.upper().str.strip()
df["phone"] = df["Phone No."]
df["phone"] = df["phone"].astype(str).str.replace(r"[^0-9]", "", regex=True)
df["address"] = df["Address"].fillna("-").str.strip()
df["gstin"] = df["Gstin"].str.strip()
df["referral"] = df["Linked"].str.strip()
df["opening_balance"] = df["Receivable Balance"].astype(float).fillna(0)
df = df[["name","phone","address","gstin","referral","opening_balance"]]
query_db("delete from app_customer")
bulk_raw_insert("customer",df,ignore=False)

Outstanding.update()
print( query_db("select * from app_outstanding",is_select=True) )

exit(0)