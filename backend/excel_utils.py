# backend/excel_utils.py
import pandas as pd

def generate_excel_from_business_list(business_list, out_path="case1_output.xlsx"):
    """
    business_list: list of dicts with keys name,address,phone,website,primary_category
    Produces an .xlsx file with 3 sheets.
    """
    df = pd.DataFrame(business_list)
    # Ensure expected columns
    for col in ["name","address","phone","website","primary_category","has_website"]:
        if col not in df.columns:
            df[col] = ""

    # Write sheets
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="All Results", index=False)
        df[df["has_website"]==True].to_excel(writer, sheet_name="With Website", index=False)
        df[df["has_website"]==False].to_excel(writer, sheet_name="No Website", index=False)
    return out_path
