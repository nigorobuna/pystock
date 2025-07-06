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
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file"
    ]

    # クラウド環境かどうかを判定
    if "google_creds_json" in st.secrets:
        # クラウド環境：Secretsから認証情報を読み込む
        creds_json_str = st.secrets["google_creds_json"]
        creds_dict = json.loads(creds_json_str)
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    else:
        # ローカル環境：JSONファイルから認証情報を読み込む
        # 【注意】このファイル名は、あなたがダウンロードしたファイル名に合わせてください
        local_creds_path = "ou-yasudalab-stock-14b75180fae9.json" # あなたの設定
        if not os.path.exists(local_creds_path):
            st.error(f"ローカルに認証ファイルが見つかりません: {local_creds_path}")
            st.stop()
        creds = Credentials.from_service_account_file(local_creds_path, scopes=scopes)
    
    client = gspread.authorize(creds)
    return client

# --- ▼▼▼ 接続とシートの取得部分を、詳細な診断モードに変更 ▼▼▼ ---
SPREADSHEET_ID = "1kFW-RGEILZoltMmjTRExBAKcSJ2yiqLR0buqAF8G1c" # あなたのスプレッドシートのID

try:
    gspread_client = get_gspread_client()
    st.success("✅ ステップ1/4: Googleクライアントの取得に成功しました。")
except Exception as e:
    st.error(f"❌ ステップ1/4: Googleクライアントの取得で失敗しました: {e}")
    st.stop()

try:
    spreadsheet = gspread_client.open_by_key(SPREADSHEET_ID)
    st.success("✅ ステップ2/4: スプレッドシートのオープンに成功しました。")
except Exception as e:
    st.error(f"❌ ステップ2/4: スプレッドシートのオープンで失敗しました: {e}")
    st.warning("【確認してください】")
    st.info("1. Google Cloudで「Google Drive API」と「Google Sheets API」の両方が有効になっていますか？")
    st.info("2. スプレッドシートの「共有」設定で、サービスアカウントのメールアドレスが「編集者」として追加されていますか？")
    st.stop()

try:
    products_sheet = spreadsheet.worksheet("products")
    st.success("✅ ステップ3/4: 'products'シートの取得に成功しました。")
except Exception as e:
    st.error(f"❌ ステップ3/4: 'products'シートの取得で失敗しました: {e}")
    st.warning("【確認してください】スプレッドシートに 'products' という名前のタブ（シート）が存在しますか？（小文字です）")
    st.stop()

try:
    history_sheet = spreadsheet.worksheet("stock_history")
    st.success("✅ ステップ4/4: 'stock_history'シートの取得に成功しました。")
    st.success("🎉 すべての接続テストに成功しました！")
except Exception as e:
    st.error(f"❌ ステップ4/4: 'stock_history'シートの取得で失敗しました: {e}")
    st.warning("【確認してください】スプレッドシートに 'stock_history' という名前のタブ（シート）が存在しますか？（小文字です）")
    st.stop()


# --- ▼▼▼ これ以降の関数は変更なし ▼▼▼ ---

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
