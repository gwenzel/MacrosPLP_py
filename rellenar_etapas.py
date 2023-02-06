
import pandas as pd
 
# Format: "year-month-date"
start_date, end_date = "2023-01-01", "2051-03-01"
 
month_list = pd.period_range(start=start_date, end=end_date, freq='M')
month_list = [month.strftime("%b-%Y") for month in month_list]

print(f"Months that lie between '{start_date}' and '{end_date}' are: ")
print(*month_list, sep=", ")
print(f"Total months: {len(month_list)}")

