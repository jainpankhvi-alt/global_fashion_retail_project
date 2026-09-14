import pandas as pd
import mysql.connector
import os

# List of CSV files and their corresponding table names
csv_files = [
    ('raw file/customers.csv', 'customers'),
    ('raw file/discounts.csv', 'discounts'),
    ('raw file/employees.csv', 'employees'),
    ('raw file/products.csv', 'products'),
    ('raw file/stores.csv', 'stores'),
    ('raw file/transactions.csv', 'transactions')
]

# Connect to the MySQL database
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='1234',
    database='global_fashion_retail'
)
cursor = conn.cursor()

# Folder containing the CSV files
folder_path = '.'

def get_sql_type(dtype):
    if pd.api.types.is_integer_dtype(dtype):
        return 'INT'
    elif pd.api.types.is_float_dtype(dtype):
        return 'FLOAT'
    elif pd.api.types.is_bool_dtype(dtype):
        return 'BOOLEAN'
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return 'DATETIME'
    else:
        return 'TEXT'

for csv_file, table_name in csv_files:
    file_path = os.path.join(folder_path, csv_file)
    
    # Read the CSV file into a pandas DataFrame
    df = pd.read_csv(file_path, low_memory=False)
    
    # Replace NaN with None to handle SQL NULL
    df = df.where(pd.notnull(df), None)
    
    # Debugging: Check for NaN values
    print(f"Processing {csv_file}")
    print(f"NaN values before replacement:\n{df.isnull().sum()}\n")

    # Clean column names
    df.columns = [col.replace(' ', '_').replace('-', '_').replace('.', '_') for col in df.columns]

    # Generate the CREATE TABLE statement with appropriate data types
    columns = ', '.join([f'`{col}` {get_sql_type(df[col].dtype)}' for col in df.columns])
    create_table_query = f'CREATE TABLE IF NOT EXISTS `{table_name}` ({columns})'
    cursor.execute(create_table_query)

      # Insert DataFrame data into the MySQL table
    sql = f"""
    INSERT INTO {table_name}
    ({', '.join(['`' + col + '`' for col in df.columns])})
    VALUES ({', '.join(['%s'] * len(df.columns))})
    """

    values = [
        tuple(None if pd.isna(x) else x for x in row)
        for row in df.itertuples(index=False, name=None)
    ]

    batch_size = 5000

    for i in range(0, len(values), batch_size):
        cursor.executemany(sql, values[i:i + batch_size])
        conn.commit()
        print(f"Inserted {min(i + batch_size, len(values))}/{len(values)} rows into {table_name}")
# Close the connection
conn.close()
