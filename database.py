import sqlite3
DATABASE_NAME = 'pos_system.db'

def init_db():
    """
    データベースを初期化し、必要なテーブルを作成
    すでに存在する場合は何もしない
    """
    #データベースファイルに接続
    conn = sqlite3.connect(DATABASE_NAME)
    
    #データベースを操作するためのカーソル(メッセンジャー)を用意する
    #cursorはSQL文を実行するためのオブジェクト
    #カーソルを使ってSQL文(設計図)を実行する
    #conn.cursor()は、データベースに対してSQL文を実行するためのカーソルを作成するメソッド
    
    cursor = conn.cursor()
    
    #命令: 「products」という名前のテーブルを新規作成
    # テーブルが存在しない場合のみ作成
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        unit TEXT, -- 単位 (例: 箱, 個, 本)
        current_stock INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    #命令: 「stock_history」という名前のテーブルを新規作成
    # 在庫の出入りを記録。
    # テーブルが存在しない場合のみ作成
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stock_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        user_name TEXT, -- 使用者名
        change_type TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products (id)
    )
    ''')
    
    #変更を保存して、接続を閉じる
    conn.commit()
    conn.close()
    
def add_product(product_code, name, unit):
    """消耗品を新たにデータベースに追加する関数"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO products (product_code, name, unit) VALUES (?, ?, ?)", (product_code, name, unit))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
    #商品コードが重複している場合はエラーを返す
        return False
    finally:
        conn.close()
    

if __name__ == '__main__':
    #このファイルを直接実行したときはデータベースを初期化するコード(init_db)を実行
    init_db()
    print(f"データベース '{DATABASE_NAME}' の準備ができました")

#消耗品情報の取得
def get_product_by_code(product_code):
    """商品コードから消耗品情報を取得する関数"""
    conn = sqlite3.connect(DATABASE_NAME)
    #辞書形式で結果　を取得するためにrow_factoryを設定
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE product_code = ?", (product_code,))
    product = cursor.fetchone()
    conn.close()
    return product

#在庫数の更新
def update_stock(product_id, quantity_change):
    """在庫数を更新する関数。quantity_changeは正の値で追加、負の値で減少"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET current_stock = current_stock + ? WHERE id = ?",(quantity_change, product_id))
    conn.commit()
    conn.close()
    

#在庫履歴の記録
def add_stock_history(product_id, user_name, change_type, quantity):
    """在庫の出入りを記録する関数"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO stock_history (product_id, user_name, change_type, quantity) VALUES (?, ?, ?, ?)", 
                   (product_id, user_name, change_type, quantity))
    conn.commit()
    conn.close()


def get_all_products():
    """全ての消耗品情報を取得する関数"""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    #商品名で並び変える
    cursor.execute("SELECT id, product_code, name,current_stock, unit FROM products ORDER BY name ASC")
    products = cursor.fetchall()
    conn.close()
    return products

def get_all_history():
    """全ての在庫履歴を取得する関数"""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    #履歴テーブル、商品テーブルを結合し、新しい順に並び替える
    cursor.execute('''
        SELECT
            h.timestamp,
            h.user_name,
            p.name,
            h.change_type,
            h.quantity
        FROM
            stock_history AS h
        JOIN
            products AS p ON h.product_id = p.id
        ORDER BY
            h.timestamp DESC
    ''')
    history = cursor.fetchall()
    conn.close()
    return history

def set_stock_count(product_id_, new_quantity):
    """在庫数を直接設定する関数"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET current_stock = ? WHERE id = ?", (new_quantity, product_id_))
    conn.commit()
    conn.close()
