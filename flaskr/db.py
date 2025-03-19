import sqlite3

DATABASE = "database.db"  # データベースの名前

def create_table():
    con = sqlite3.connect(DATABASE)  # sqliteへアクセスするためのコード
    cur = con.cursor()
    
    # office_id_pwという名前のテーブル作成
    cur.execute("CREATE TABLE IF NOT EXISTS office_id_pw(id, pw ,office_name)")
    
    con.commit()
    con.close()


#データベースの中身確認
# con = sqlite3.connect(DATABASE)
# cur = con.cursor()

# cur.execute("SELECT * FROM office_id_pw")
# data = cur.fetchall()

# print("データベースの中身:", data)

# con.close()

# テーブルを削除する用に
# con = sqlite3.connect(DATABASE) 
# cur = con.cursor()

# # テーブルを削除
# cur.execute("DROP TABLE IF EXISTS office_name")  # 'users'テーブルを削除

# # コミットして変更を反映
# con.commit()

# # 接続を閉じる
# con.close()

# print("テーブル 'office_name' を削除しました。")