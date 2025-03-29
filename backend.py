from fastapi import FastAPI, HTTPException, Depends
import sqlite3
import re
from dotenv import load_dotenv
from fastapi.security.api_key import APIKeyHeader

app =FastAPI()
API_KEY = "secret-api"
API_KEY_NAME = 'x-api-key'
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    
def connect_to_db():
    return sqlite3.connect("test.db", check_same_thread=False)
    
def mock_db():
    con = connect_to_db()
    cursor = con.cursor()
    cursor.execute('''
        CREATE TABLE sales_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE,
            category TEXT,
            status TEXT,
        )
    ''')
    mock_data = [
        ("ODID001","T-Shirts", "Shipped"),
        ("ODID002","T-Shirts", "Pending"),
        ("ODID003","T-Shirts", "Delivered"),
        ("ODID004","Shoes", "Cancelled"),
        ("ODID005","Shoes", "Shipped"),
        ("ODID006","Shoes", "Delivered"),
        ("ODID007","Hats", "Pending"),
        ("ODID008","Hats", "Shipped"),
        ("ODID009","Hats", "Cancelled"),
    ]
    for index, (order_id,category, status, price, order_date) in enumerate(mock_data, start=1):
        cursor.execute(
            "INSERT INTO sales_table (order_id, category, status) VALUES (?, ?, ?)",
            (order_id, category, status)
        )
    con.commit()
    con.close()

def gen_sql(natural_query:str):
    query_map = {
        "show all orders": "SELECT * FROM sales_table;",
        "count all orders": "SELECT COUNT(*) FROM sales_table;",
    } 

    categories = {"T-Shirts", "Shoes", "Hats"}
    statuses = {"Shipped", "Cancelled", "Pending", "Delivered"}

    natural_query= natural_query.lower().strip()
    match = re.match(r"(show all|count all) ([\w\s-]+) orders", natural_query)
    if match:
        query_type, keyword= match.groups()
        keyword= keyword.title()
        if keyword in categories:
            if query_type==("show all"):
                return f"Select * From sales_table Where Category = '{keyword}';"
            elif query_type==("count all"):
              return f"Select Count(*) From sales_table Where Category = '{keyword}';"
        elif keyword in statuses:
            if query_type == "show all":
                return f"SELECT * FROM sales_table WHERE status = '{keyword}';"
            elif query_type == "count all":
                return f"SELECT COUNT(*) FROM sales_table WHERE status = '{keyword}';"
    
    return query_map.get(natural_query, None)
    
@app.get("/")
def root():
    return {"message": "FastAPI NLP to SQL service is running!"}

@app.get('/query')
def get_data(natural_query:str, api_key:str = Depends(verify_api_key)):
    sql_query= gen_sql(natural_query)
    if sql_query is None:
        raise HTTPException(status_code=400, detail='Unsupported query')
    con= connect_to_db()
    cursor= con.cursor()
    cursor.execute(sql_query)
    results = cursor.fetchall()
    con.close()
    return{'query':natural_query, 'sql':sql_query, 'results':results}

@app.get('/explain')
def explain_query(natural_query:str, api_key:str = Depends(verify_api_key)):
    sql_query = gen_sql(natural_query)
    if sql_query is None:
        raise HTTPException(status_code=400, detail='Unsupported query')
    return{'query':natural_query, 'sql':sql_query}

@app.get('/validate')
def validate_query(natural_query:str, api_key:str = Depends(verify_api_key)):
    sql_query = gen_sql(natural_query)
    if sql_query:
        return {'valid':True, 'sql_translation':sql_query}
    else:
        return {'valid':False, 'error':'Unsupported Query'}

mock_db()
