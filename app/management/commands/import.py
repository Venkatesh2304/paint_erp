from app.management.commands.common import * 
import pandas as pd
df = pd.read_excel("opening_stock.xlsx")
df["base"] = (df["COLOUR"].fillna("") + df["BASE"].fillna("")).str.upper().str.strip()
df["company"] = df["COMPANY"].str.upper().str.strip()
df["category"] = df["ITEM"].str.upper().str.strip()
df["size"] = df["LITRES"].astype(str).apply(lambda x : x + "LTR" if x.replace(".","").isnumeric() else x.upper().strip() ).fillna("")
df["opening_stock"] = df["STOCK"].astype(int)
df["dpl"] = df["DPL"].fillna(0)
df["hsn"] = "32099020"
df["rt"] = 18
df["mrp"] = df["MRP"].fillna(0)
df = df[["base","company","category","size","dpl","opening_stock","hsn","rt","mrp"]]
df["name"] = df["category"] + " " + df["base"] + " " + df["size"]
# query_db("delete from app_saleproduct")
# query_db("delete from app_purchaseproduct")
# query_db("delete from app_purchase")
query_db("delete from app_product")
bulk_raw_insert("product",df,ignore=False)

df = pd.read_excel("party.xlsx")
print(df)
df["name"] = df["Name"].str.upper().str.strip()
df["phone"] = df["Phone No."]
df["address"] = df["Address"].fillna("-").str.strip()
df["gstin"] = df["GSTIN"].str.strip()
df = df[["name","phone","address","gstin"]]
bulk_raw_insert("customer",df,ignore=False)

exit(0)