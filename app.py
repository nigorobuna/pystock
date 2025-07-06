# Streamlitアプリケーションのメインファイル
# -*- coding: utf-8 -*-
import streamlit as st
import database
import pandas as pd
import qrcode
import io
import bcrypt
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import cv2
from urllib.parse import urlparse, parse_qs
import time
import os # osライブラリを追加
import yaml # yamlライブラリを追加
from yaml.loader import SafeLoader # SafeLoaderを追加

# --- データベースの準備（変更なし） ---
database.init_db()

# --- ページタイトルの設定 ---
st.set_page_config(page_title="安田研究室 消耗品管理システム", layout="wide")


# --- ▼▼▼ 管理者パスワードを安全に読み込むロジックを追加 ▼▼▼ ---
admin_hashed_password = None
# クラウド環境かどうかを判定
if "google_creds_json" in st.secrets:
    admin_hashed_password = st.secrets.get("admin_password")
else:
    # ローカル環境
    if os.path.exists('config.yaml'):
        with open('config.yaml', 'r', encoding='utf-8') as file:
            config = yaml.load(file, Loader=SafeLoader)
        admin_hashed_password = config.get("admin_password")

# --- ▼▼▼ 認証ロジックを自作 ▼▼▼ ---

# ログイン状態の初期化
if 'authentication_status' not in st.session_state:
    st.session_state.authentication_status = None
if 'name' not in st.session_state:
    st.session_state.name = None

# --- ログイン成功時のメイン処理 ---
if st.session_state["authentication_status"]:
    name = st.session_state["name"]
    st.sidebar.write(f'ようこそ、{name}さん！')
    if st.sidebar.button('ログアウト'):
        # セッション情報をクリアしてリロード
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    # --- 管理者メニューのパスワード認証 ---
    st.sidebar.divider()
    if 'admin_unlocked' not in st.session_state:
        st.session_state.admin_unlocked = False

    if st.session_state.admin_unlocked:
        # --- 管理者ページ ---
        st.sidebar.success("管理者メニュー (ロック解除済み)")
        st.title('管理者メニュー')
        if st.button('メイン画面に戻る'):
            st.session_state.admin_unlocked = False
            st.rerun()

        st.subheader('在庫数の手動更新(入荷、棚卸しなど)')
        all_products_list = database.get_all_products()
        product_options = {f"{p['name']} ({p['product_code']})": p['id'] for p in all_products_list}
        
        if product_options:
            with st.form('update_stock_form', clear_on_submit=True):
                selected_product_display_name = st.selectbox('更新する商品を選択してください', options=list(product_options.keys()))
                quantity_change = st.number_input('数量の変更（正の値で追加、負の値で減少）', min_value=-1000, max_value=1000, value=0)
                submit_button = st.form_submit_button('在庫数を更新')

                if submit_button and quantity_change != 0:
                    product_id = product_options[selected_product_display_name]
                    database.update_stock(product_id, quantity_change)
                    change_type = '入荷' if quantity_change > 0 else '棚卸調整'
                    database.add_stock_history(product_id, name, change_type, abs(quantity_change))
                    st.success(f"「{selected_product_display_name}」の在庫数を更新しました。")
                    st.rerun()
        else:
            st.write('更新対象の商品がありません')
        
        st.subheader('現在の在庫一覧')
        if all_products_list:
            df_products = pd.DataFrame(all_products_list)
            df_products.columns = ['id', 'product_code', 'name', 'unit', 'current_stock', 'created_at']
            df_display = df_products[['product_code', 'name', 'current_stock', 'unit']]
            df_display.columns = ['商品コード', '品目名', '現在庫数', '単位']
            st.dataframe(df_display, use_container_width=True)
        else:
            st.write('商品はまだ登録されていません。')
        
        st.subheader('使用履歴')
        all_history = database.get_all_history()
        if all_history:
            df_history = pd.DataFrame(all_history)
            df_history.columns = ['日時', '使用者', '品目名', '操作', '数量']
            st.dataframe(df_history, use_container_width=True)
        else:
            st.write('使用履歴がありません。')
        
        st.subheader('QRコード生成')
        if all_products_list:
            base_url = st.text_input("アプリのベースURLを入力", "https://ouyasudalab-stock.streamlit.app", help="デプロイ後に発行される、このアプリのURLを入力してください。")
            product_for_qr = st.selectbox(label="QRコードを生成する備品を選択", options=[f"{p['name']} ({p['product_code']})" for p in all_products_list], index=None, placeholder="備品を選択してください...")
            if product_for_qr:
                selected_code = product_for_qr.split('(')[-1].replace(')', '')
                url_to_encode = f"{base_url}?product_code={selected_code}"
                st.write("生成されたURL:")
                st.code(url_to_encode)
                qr_img = qrcode.make(url_to_encode)
                buf = io.BytesIO()
                qr_img.save(buf, format='PNG')
                img_bytes = buf.getvalue()
                st.image(img_bytes, caption=f"{product_for_qr} のQRコード", width=200)
                st.info("この画像を右クリックして保存し、印刷して使用してください。")

    else:
        # --- 通常ユーザーのメインページ（在庫利用画面） ---
        st.sidebar.subheader("管理者用")
        admin_password_input = st.sidebar.text_input("管理者パスワードを入力", type="password", key="admin_pass")
        if st.sidebar.button("認証"):
            # ▼▼▼ bcryptを使った安全なパスワードチェックに修正 ▼▼▼
            if admin_hashed_password and bcrypt.checkpw(admin_password_input.encode('utf-8'), admin_hashed_password.encode('utf-8')):
                st.session_state.admin_unlocked = True
                st.rerun()
            else:
                st.sidebar.error("パスワードが違います。")
        
        st.title('安田研究室　消耗品管理システム')
        st.header('使用登録')
        # ... (在庫利用画面のコードは変更なし) ...
        query_params = st.query_params
        product_code_from_url = query_params.get("product_code")

        if 'processed_code' not in st.session_state:
            st.session_state.processed_code = None

        if product_code_from_url and st.session_state.processed_code == product_code_from_url:
            st.success("使用記録が正常に処理されました。")
            st.markdown('[🏠 ホームに戻る](app.py)')
        elif product_code_from_url:
            product = database.get_product_by_code(product_code_from_url)
            if not product:
                st.error(f"商品コード '{product_code_from_url}' が見つかりません。")
                st.markdown('[🏠 ホームに戻る](app.py)')
            else:
                st.subheader(f"品目名: {product['name']}")
                st.metric(label="現在の在庫数", value=f"{product['current_stock']} {product['unit']}")
                if product['current_stock'] > 0:
                    if st.button(f"「{product['name']}」を1つ使用する", type="primary"):
                        database.update_stock(product['id'], -1)
                        database.add_stock_history(product['id'], name, '使用', 1)
                        st.session_state.processed_code = product_code_from_url
                        st.rerun()
                else:
                    st.error(f"「{product['name']}」の在庫がありません。")
                    st.markdown('[🏠 ホームに戻る](app.py)')
        else:
            st.info("QRコードを読み取って、商品コードを取得してください。")
            st.session_state.processed_code = None


# --- ログイン前の処理 ---
else:
    st.title('安田研究室　消耗品管理システム')
    login_tab, register_tab = st.tabs(["ログイン", "新規登録"])

    # --- ログインタブ ---
    with login_tab:
        with st.form("login_form"):
            email = st.text_input("メールアドレス")
            password = st.text_input("パスワード", type="password")
            submitted = st.form_submit_button("ログイン")
            if submitted:
                user = database.get_user(email)
                if user and bcrypt.checkpw(password.encode('utf-8'), user['hashed_password'].encode('utf-8')):
                    st.session_state.authentication_status = True
                    st.session_state.name = user['name']
                    st.rerun()
                else:
                    st.error("メールアドレスまたはパスワードが間違っています。")

    # --- 新規登録タブ ---
    with register_tab:
        st.info('【ご注意】\n\n- **お名前:** ログイン後に表示される名前です。\n- **メールアドレス:** ログインIDとして使います。\n- **パスワード:** 6文字以上で設定してください。')
        with st.form("registration_form", clear_on_submit=True):
            name_reg = st.text_input("お名前")
            email_reg = st.text_input("メールアドレス")
            password_reg = st.text_input("パスワード", type="password")
            password_rep = st.text_input("パスワード（確認用）", type="password")
            reg_submitted = st.form_submit_button("登録する")
            
            if reg_submitted:
                if not (name_reg and email_reg and password_reg and password_rep):
                    st.warning("すべての項目を入力してください。")
                elif password_reg != password_rep:
                    st.error("パスワードが一致しません。")
                elif database.get_user(email_reg):
                    st.error("このメールアドレスは既に使用されています。")
                else:
                    hashed_password = bcrypt.hashpw(password_reg.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    database.add_user(name_reg, email_reg, hashed_password)
                    
                    # ▼▼▼ ここを修正 ▼▼▼
                    st.toast('ユーザー登録が完了しました！ログイン画面に切り替わります。')
                    time.sleep(2) # 2秒待ってメッセージを見せる
                    st.rerun()
