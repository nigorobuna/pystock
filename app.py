# Streamlitアプリケーションのメインファイル
# -*- coding: utf-8 -*-
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import database
import pandas as pd
import qrcode
import io
import bcrypt
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import cv2
from urllib.parse import urlparse, parse_qs

#---データベースの準備---
database.init_db()

#--- ▼▼▼ ユーザー認証の設定を、より確実な方法で判定 ▼▼▼ ---
# StreamlitのSecretsに 'credentials' が存在するかで、クラウド環境かどうかを判断
if "credentials" in st.secrets:
    # クラウド環境：Secretsから設定を読み込む
    config = {
        'credentials': st.secrets['credentials'],
        'cookie': st.secrets['cookie'],
        'admin_password': st.secrets.get('admin_password')
    }
else:
    # ローカル環境：config.yamlファイルから読み込む
    with open('config.yaml', 'r', encoding='utf-8') as file:
        config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

#---ログイン成功時の処理---
if st.session_state.get("authentication_status"):
    name = st.session_state["name"]
    st.sidebar.write(f'ようこそ、{name}さん！')
    authenticator.logout('Logout', 'sidebar')

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
            df_products.columns = ['id', 'product_code', 'name', 'current_stock', 'unit']
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
            base_url = st.text_input("アプリのベースURLを入力", "https://your-app-name.streamlit.app", help="デプロイ後に発行される、このアプリのURLを入力してください。")
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
            stored_hashed_password = config.get('admin_password', '').encode('utf-8')
            if stored_hashed_password and bcrypt.checkpw(admin_password_input.encode('utf-8'), stored_hashed_password):
                st.session_state.admin_unlocked = True
                st.rerun()
            else:
                st.sidebar.error("パスワードが違います。")

        # QRコードスキャナ
        st.header('使用登録')
        def qr_code_callback(frame):
            img = frame.to_ndarray(format="bgr24")
            qr_detector = cv2.QRCodeDetector()
            data, bbox, straight_qrcode = qr_detector.detectAndDecode(img)
            if data:
                try:
                    parsed_url = urlparse(data)
                    query_params = parse_qs(parsed_url.query)
                    if 'product_code' in query_params:
                        st.session_state.scanned_code = query_params['product_code'][0]
                except Exception:
                    pass
            return frame

        webrtc_streamer(
            key="qr-scanner",
            mode=WebRtcMode.SENDONLY,
            video_frame_callback=qr_code_callback,
            media_stream_constraints={"video": {"facingMode": "environment"}, "audio": False},
            async_processing=True,
        )
        st.markdown("---")
        
        if 'scanned_code' not in st.session_state:
            st.session_state.scanned_code = None
        
        active_product_code = st.session_state.scanned_code or st.query_params.get("product_code")

        if active_product_code:
            product = database.get_product_by_code(active_product_code)
            if not product:
                st.error(f"商品コード '{active_product_code}' が見つかりません。")
            else:
                st.subheader(f"品目名: {product['name']}")
                st.metric(label="現在の在庫数", value=f"{product['current_stock']} {product['unit']}")
                if product['current_stock'] > 0:
                    if st.button(f"「{product['name']}」を1つ使用する", type="primary", use_container_width=True):
                        database.update_stock(product['id'], -1)
                        database.add_stock_history(product['id'], name, '使用', 1)
                        st.session_state.scanned_code = None
                        st.success(f"「{product['name']}」の使用を記録しました。")
                        st.balloons()
                        st.rerun()
                else:
                    st.error(f"「{product['name']}」の在庫がありません。")
        else:
            st.info("上のカメラでQRコードをスキャンしてください。")

else:
    # --- ログインしていない場合の処理 ---
    st.title('安田研究室　消耗品管理システム')
    login_tab, register_tab = st.tabs(["ログイン", "新規登録"])

    with login_tab:
        authenticator.login(location='main')
    with register_tab:
        st.info('【ご注意】\n\n- **お名前:** ログイン後に表示される名前です。（例: 山田 太郎）\n- **ユーザー名:** ログインIDとして使用します。**半角英数字**で入力してください。（例: t_yamada）\n- **Eメール:** 連絡可能なメールアドレスを入力してください。')
        try:
            if authenticator.register_user(location='main'):
                st.success('ユーザー登録が成功しました。ログインタブからログインしてください。')
                with open('config.yaml', 'w', encoding='utf-8') as file:
                    yaml.dump(config, file, default_flow_style=False)
        except Exception as e:
            st.error(e)
    
    if st.session_state.get("authentication_status") is False:
        st.error('メールアドレスまたはパスワードが間違っています。再度入力してください。')
    elif st.session_state.get("authentication_status") is None:
        st.warning('メールアドレスとパスワードを入力してログインしてください。')
