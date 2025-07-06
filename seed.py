#商品リストの登録
import database

# 登録したい備品のリスト
"""
テンプレートは以下のように記述します。
{"code": "(商品コード)", "name": "(名前)", "unit": "(単位)"},
code"は商品コード、"name"は商品名、"unit"は単位を表します。
"""
# ここでは、商品コードは一意でなければならないため、重複しないように注意してください。
products_to_seed = [
    {"code": "sani", "name": "サニメント手袋", "unit": "箱"},
    {"code": "nabi", "name": "ナビロール", "unit": "箱"},
    {"code": "sand120", "name": "研磨紙120", "unit": "箱"},
    {"code": "sand180", "name": "研磨紙180", "unit": "箱"},
    {"code": "sand400", "name": "研磨紙400", "unit": "箱"},
    {"code": "sand600", "name": "研磨紙600", "unit": "箱"},
    {"code": "sand800", "name": "研磨紙800", "unit": "箱"},
    {"code": "sand1000", "name": "研磨紙1000", "unit": "箱"},
    {"code": "sand1200", "name": "研磨紙1200", "unit": "箱"},
    {"code": "sand1500", "name": "研磨紙1500", "unit": "箱"},
    {"code": "sand2000", "name": "研磨紙2000", "unit": "箱"},
    {"code": "sand4000", "name": "研磨紙4000", "unit": "箱"},
    {"code": "wireb", "name": "ワイヤーbrother", "unit": "個"},
    {"code": "wiref", "name": "ワイヤーfanuc", "unit": "個"},
    {"code": "flow", "name": "小麦粉", "unit": "袋"},
    {"code": "swab", "name": "綿棒", "unit": "箱"},
    {"code": "pick", "name": "爪楊枝", "unit": "箱"},
    {"code": "opsl", "name": "OPS液", "unit": "本"},
    {"code": "wipe", "name": "キムワイプ", "unit": "箱"},
    {"code": "glss", "name": "石英管 細", "unit": "本"},
    {"code": "glsb", "name": "石英管 太", "unit": "本"},
    {"code": "etan", "name": "エタノール", "unit": "缶"},
    {"code": "aset", "name": "アセトン", "unit": "缶"},
    {"code": "jsou", "name": "重曹", "unit": "袋"},
    {"code": "tant", "name": "タンタル箔", "unit": "枚"},
    {"code": "unil", "name": "ユニパック 大", "unit": "束"},
    {"code": "unim", "name": "ユニパック 中", "unit": "束"},
    {"code": "unis", "name": "ユニパック 小", "unit": "束"},
    {"code": "magk", "name": "マジック 黒", "unit": "本"},
    {"code": "magr", "name": "マジック 赤", "unit": "本"},
    {"code": "magb", "name": "マジック 青", "unit": "本"},
    {"code": "pins", "name": "ピンセット", "unit": "本"},
    {"code": "gris", "name": "グリース", "unit": "本"},
    {"code": "name", "name": "ネームシール", "unit": "枚"},
    {"code": "marr", "name": "シール 赤", "unit": "枚"},
    {"code": "marb", "name": "シール 青", "unit": "枚"},
    {"code": "marg", "name": "シール 緑", "unit": "枚"},
    {"code": "mary", "name": "シール 黄色", "unit": "枚"},
    {"code": "aron", "name": "アロンアルファ", "unit": "本"},
    {"code": "arod", "name": "アロンアルファ剥し液", "unit": "本"},
    {"code": "bins50", "name": "サンプル管瓶 5 cc", "unit": "箱"},
    {"code": "bins100", "name": "サンプル管瓶 10 cc", "unit": "箱"},
    {"code": "sili", "name": "シリコンシート", "unit": "枚"},
    {"code": "pras1", "name": "スチロール角形ケース 1型", "unit": "箱"},
    {"code": "pras3", "name": "スチロール角形ケース 3型", "unit": "箱"},
    {"code": "pras5", "name": "スチロール角形ケース 5型", "unit": "箱"},
    {"code": "aird", "name": "エアダスター", "unit": "本"},
    {"code": "wpap", "name": "薬包紙", "unit": "束"},
    {"code": "rcut", "name": "回転砥石", "unit": "箱"},
    {"code": "glsp", "name": "ガラス板", "unit": "枚"},
    {"code": "solm", "name": "ソルミックス", "unit": "缶"},
    {"code": "toel", "name": "キムタオル", "unit": "箱"},
]

def seed_data():
    print("備品データの初期登録を開始します...")
    count = 0
    for product in products_to_seed:
        success = database.add_product(product["code"], product["name"], product["unit"])
        if success:
            print(f"  登録成功: {product['name']}")
            count += 1
        else:
            print(f"  登録済み(スキップ): {product['name']}")
            
    print(f"\n{count}件の新しい備品を登録しました。")
    print("初期登録を完了しました。")

if __name__ == '__main__':
    seed_data()