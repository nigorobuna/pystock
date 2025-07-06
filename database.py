import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import pandas as pd
from datetime import datetime
import os
import json

# --- Googleスプレッドシートに接続 ---
def get_gspread_client():
    """
    StreamlitのSecretsまたはローカルのJSONファイルから認証情報を読み込み、
    gspreadクライアントを返す。
    """
    # ▼▼▼ プログラムがGoogleに「何を使いたいか」を伝えるためのリスト ▼▼▼
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file"
    ]

    # クラウド環境かどうかを判定
    if "google_creds_json" in st.secrets:
        # クラウド環境：Secretsから認証情報を読み込む
        creds_json_str = st.secrets["google_creds_json"]
        creds_dict = json.loads(creds_json_str)
        # ▼▼▼ ここに scopes を追加 ▼▼▼
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    else:
        # ローカル環境：JSONファイルから認証情報を読み込む
        # 【注意】このファイル名は、あなたがダウンロードしたファイル名に合わせてください
        local_creds_path = "ou-yasudalab-stock-14b75180fae9.json" # 例
        if not os.path.exists(local_creds_path):
            st.error(f"ローカルに認証ファイルが見つかりません: {local_creds_path}")
            st.stop()
        # ▼▼▼ ここにも scopes を追加 ▼▼▼
        creds = Credentials.from_service_account_file(local_creds_path, scopes=scopes)
    
    client = gspread.authorize(creds)
    return client

# --- 接続とシートの取得 ---
# 【注意】スプレッドシートの名前を、あなたが作成したものに合わせてください
SPREADSHEET_NAME = "ouyasudalab-stock.streamlit.app/"
try:
    gspread_client = get_gspread_client()
    spreadsheet = gspread_client.open(SPREADSHEET_NAME)
    products_sheet = spreadsheet.worksheet("products")
    history_sheet = spreadsheet.worksheet("stock_history")
except Exception as e:
    st.error(f"スプレッドシートへの接続に失敗しました: {e}")
    st.stop()


# --- ▼▼▼ これまでの関数は変更なし ▼▼▼ ---

def init_db():
    """この関数はもう不要だが、app.pyからの呼び出しのために残しておく。"""
    pass

def get_all_products():
    """すべての商品情報を取得します。"""
    records = products_sheet.get_all_records()
    return [row for row in records if row.get('id')]

def get_product_by_code(product_code):
    """商品コードを使って、商品情報を取得します。"""
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
    """在庫数を更新します。"""
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
    """在庫変動の履歴を記録します。"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    next_row_num = len(history_sheet.get_all_values()) + 1
    new_row = [next_row_num - 1, product_id, user_name, change_type, quantity, timestamp]
    history_sheet.append_row(new_row, value_input_option='USER_ENTERED')

def set_stock_count(product_id, new_quantity):
    """在庫数を指定された値に直接設定します。"""
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
    
    for record in all_history_records:
        record['name'] = products_map.get(record['product_id'], '不明な商品')
    
    sorted_history = sorted(all_history_records, key=lambda x: x['timestamp'], reverse=True)
    return sorted_history
