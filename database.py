# ==============================================================================
# database.py
# ==============================================================================
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
from datetime import datetime
import os
import json
import pytz

# --- Googleスプレッドシートに接続 ---
def get_gspread_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file"
    ]
    if "google_creds_json" in st.secrets:
        creds_json_str = st.secrets["google_creds_json"]
        creds_dict = json.loads(creds_json_str)
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    else:
        local_creds_path = "ou-yasudalab-stock-14b75180fae9.json"
        if not os.path.exists(local_creds_path):
            st.error(f"ローカルに認証ファイルが見つかりません: {local_creds_path}")
            st.stop()
        creds = Credentials.from_service_account_file(local_creds_path, scopes=scopes)
    
    client = gspread.authorize(creds)
    return client

SPREADSHEET_ID = "1kFw-RGElLZOLtMmijTRExBAKcSJ2yiqLR0BuqAF8G1c"
try:
    gspread_client = get_gspread_client()
    spreadsheet = gspread_client.open_by_key(SPREADSHEET_ID)
    products_sheet = spreadsheet.worksheet("products")
    history_sheet = spreadsheet.worksheet("stock_history")
    users_sheet = spreadsheet.worksheet("users")
except Exception as e:
    st.error(f"スプレッドシートへの接続に失敗しました: {e}")
    st.stop()

# --- ユーザー管理用の関数 ---
def get_user(email):
    try:
        cell = users_sheet.find(email, in_column=2)
        if cell:
            headers = users_sheet.row_values(1)
            user_data = users_sheet.row_values(cell.row)
            return dict(zip(headers, user_data))
        return None
    except gspread.exceptions.CellNotFound:
        return None

def add_user(name, email, hashed_password):
    new_row = [str(name), str(email), str(hashed_password)]
    users_sheet.append_row(new_row, value_input_option='USER_ENTERED')

# --- 在庫管理用の関数 ---
def init_db():
    pass

def get_all_products():
    records = products_sheet.get_all_records()
    return [row for row in records if row.get('id')]

def get_product_by_code(product_code):
    try:
        cell = products_sheet.find(product_code, in_column=2)
        if cell:
            row_values = products_sheet.row_values(cell.row)
            headers = products_sheet.row_values(1)
            return dict(zip(headers, row_values))
        return None
    except gspread.exceptions.CellNotFound:
        return None

def update_stock(product_id, quantity_change):
    try:
        cell = products_sheet.find(str(product_id), in_column=1)
        if cell:
            current_stock_col = 5
            current_stock_str = products_sheet.cell(cell.row, current_stock_col).value
            current_stock = int(current_stock_str) if current_stock_str else 0
            new_stock = current_stock + quantity_change
            products_sheet.update_cell(cell.row, current_stock_col, new_stock)
    except gspread.exceptions.CellNotFound:
        pass

def add_stock_history(product_id, user_name, change_type, quantity):
    jst = pytz.timezone('Asia/Tokyo')
    timestamp = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")
    next_row_num = len(history_sheet.get_all_values()) + 1
    new_row = [next_row_num - 1, product_id, user_name, change_type, quantity, timestamp, ''] # misc_item_nameは空
    history_sheet.append_row(new_row, value_input_option='USER_ENTERED')

# ▼▼▼ 新しい関数を追加 ▼▼▼
def add_misc_stock_history(user_name, item_name, quantity):
    """その他備品の使用履歴を記録します。"""
    jst = pytz.timezone('Asia/Tokyo')
    timestamp = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")
    next_row_num = len(history_sheet.get_all_values()) + 1
    # product_idは空欄にし、misc_item_nameに手入力した品目名を入れる
    new_row = [next_row_num - 1, '', user_name, 'その他使用', quantity, timestamp, item_name]
    history_sheet.append_row(new_row, value_input_option='USER_ENTERED')


def set_stock_count(product_id, new_quantity):
    try:
        cell = products_sheet.find(str(product_id), in_column=1)
        if cell:
            current_stock_col = 5
            products_sheet.update_cell(cell.row, current_stock_col, new_quantity)
    except gspread.exceptions.CellNotFound:
        pass

def get_all_history():
    """すべての在庫履歴を取得します。"""
    all_history_records = history_sheet.get_all_records()
    all_products_records = get_all_products()
    
    products_map = {product['id']: product['name'] for product in all_products_records}
    
    # ▼▼▼ 履歴表示ロジックを修正 ▼▼▼
    for record in all_history_records:
        # product_idがあれば、それを元に品目名を取得
        if record.get('product_id') and record['product_id'] in products_map:
            record['name'] = products_map[record['product_id']]
        # なければ、手入力された品目名を使う
        else:
            record['name'] = record.get('misc_item_name', '不明な手動入力品')
    
    sorted_history = sorted(all_history_records, key=lambda x: x['timestamp'], reverse=True)
    return sorted_history