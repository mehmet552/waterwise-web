
from app import app, db, Consumption
import pandas as pd

with app.app_context():
    all_data = Consumption.query.order_by(Consumption.date).all()
    print(f"Total Records: {len(all_data)}")
    
    if not all_data:
        print("No data found.")
        exit()

    data_list = [{'date': d.date, 'category': d.category, 'liters': d.liters} for d in all_data]
    df = pd.DataFrame(data_list)
    df['date'] = pd.to_datetime(df['date'])
    
    print("\n--- Raw Data Head ---")
    print(df.head())
    print("\n--- Data Types ---")
    print(df.dtypes)
    
    today = pd.Timestamp.now().normalize()
    print(f"\nToday (Normalized): {today}")
    
    # Test Bill Filtering Logic
    print("\n--- Filtering Bills ---")
    # Simulate app.py logic
    # Ensure activity_type column exists and handle NaNs if necessary (though pandas usually handles it)
    if 'activity_type' not in df.columns:
        df['activity_type'] = 'custom' # Default for old data
        
    chart_df = df[df['activity_type'] != 'bill']
    chart_df = chart_df[chart_df['category'] != 'Fatura Bildirimi']
    
    print(f"Chart Data Rows (No Bills): {len(chart_df)}")
    if not chart_df.empty:
        print(chart_df.head())
    else:
        print("Chart DataFrame is EMPTY! This explains why graphs are zero.")
        
    bills_df = df[(df['activity_type'] == 'bill') | (df['category'] == 'Fatura Bildirimi')]
    print(f"Bill Data Rows: {len(bills_df)}")
    if not bills_df.empty:
        print(bills_df.head())

    # Test Reindexing (Daily)
    end_date = today
    start_date = end_date - pd.DateOffset(days=29)
    full_idx = pd.date_range(start=start_date, end=end_date, freq='D')
    
    daily_grp = chart_df.groupby(chart_df['date'].dt.normalize())['liters'].sum()
    daily_grp = daily_grp.reindex(full_idx, fill_value=0)
    
    print("\n--- Processed Trend Data (Last 5 days) ---")
    print(daily_grp.tail())
