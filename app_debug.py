import streamlit as st
import os

st.set_page_config(layout="wide")

st.title("Streamlit Secrets 機能 診断アプリ")

# 環境判定
# Streamlit Cloudのサーバーに特有のパスが存在するかで環境を判定
if os.path.exists('/mount/src/pystock'):
    st.header("クラウド環境で実行中")
    
    st.subheader("1. Secretsオブジェクトの全内容の表示テスト")
    try:
        # st.secretsオブジェクト全体を辞書に変換して表示
        secrets_dict = st.secrets.to_dict()
        st.write("st.secrets.to_dict() の結果:")
        st.write(secrets_dict)
    except Exception as e:
        st.error(f"st.secrets.to_dict()でエラーが発生しました: {e}")

    st.subheader("2. 個別のキーへのアクセス テスト")
    try:
        test_value = st.secrets["test_key"]
        st.success(f"st.secrets['test_key']の読み込みに成功しました！")
        st.write(f"取得できた値:  {test_value}")
    except KeyError:
        st.error("st.secrets['test_key']が見つかりませんでした (KeyError)。Secretsの設定を確認してください。")
    except Exception as e:
        st.error(f"st.secrets['test_key']の読み込み中に予期せぬエラーが発生しました: {e}")

else:
    st.header("ローカル環境で実行中")
    st.info("この診断用アプリは、Streamlit Cloud上でのみSecretsのテストを行います。")
