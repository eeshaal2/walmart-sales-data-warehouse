import pandas as pd

trans = pd.read_csv("transactional_data.csv")
prod = pd.read_csv("product_master_data.csv")

matched_products = trans['Product_ID'].isin(prod['Product_ID']).sum()

print("Matched products:", matched_products)
print("Total transactions:", len(trans))
print("Unmatched products:", len(trans) - matched_products)

# df = pd.read_csv("transactional_data.csv")
# print("Read transactional_data.csv")
# print(df.columns)
# print(df.head())

