# from flask import Flask リモートホスト用※from flaskr import appは消す
from flaskr import app
from flask import render_template, request, redirect, url_for, json #HTMLのデータを読み込んでPythonのデータに埋め込んで表示させる ※jinja2を使ってる
import gspread  #gspreadモジュールをインポート
import os
from google.oauth2.service_account import Credentials
from datetime import date, datetime

# app = Flask(__name__)リモートホスト用

branch_map = {
    "127.0.0.1": "c事業所",
    "192.168.3.2" :"アイフォン",
    "192.168.3.5" :"アイフォン2",
    "192.168.3.11":"自分",
    # 必要に応じて追加
}

# json_file_path = "spread-sheet-test.json" #開発モード用
json_file_path = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]

scopes = ["https://www.googleapis.com/auth/spreadsheets"] #スコープ：どの範囲でまでその権限・影響を及ばせるか 今回のパターンで行くとスプレッドシートの読み書きが行える

# from_service_account_file関数に引数json_file_path, scopes=scopesを渡すことでクラスメソッドとしてCredentialsクラスに値を渡しインスタンス変数を設定。
# グーグルアカウントの認証管理をするクラスメソッド
credentials = Credentials.from_service_account_file(
    json_file_path, scopes=scopes)

# authorizeはgspreadモジュールの関数。「この認証情報を使って、スプレッドシートを操作する許可をください！」というリクエストを送る
# 認証されたらClientを返し、gspread.Clientオブジェクトとしてスプレッドシートの操作オブジェクトとなる
gc = gspread.authorize(credentials)

spreadsheet_id = "1kSXfl_g3WwopEyGIIvswYzNFwotVqh_g1DPNI31gb_w"
spreadsheet_url = "https://docs.google.com/spreadsheets/d/1kSXfl_g3WwopEyGIIvswYzNFwotVqh_g1DPNI31gb_w/edit?gid=0#gid=0"
sh = gc.open_by_key(spreadsheet_id)
ws = sh.get_worksheet(0)

#   #クラスメソッドで本日の日付と曜日を取得
today =date.today()
week = ["（月）", "（火）", "（水）", "（木）", "（金）", "（土）", "（日）"]
today_str = today.isoformat()#isoformatメソッドで今日の日付を文字列にする
today_week = week[today.weekday()] #weekdayメソッドは取得した日付の曜日を数字として表す
today_full = f"{today_str} {today_week}"
    
@app.route("/spread", methods=["GET", "POST"]) 
#POST:入力データを送る、GET:ページを開く POSTは送る側・貰う側両方設定必要。（GETは貰う側だけでOK)
def spread():
    if request.method == "POST":
        # フォームのデータを取得
        report_data = request.form["report"]
        revenue_data = request.form["revenue"]
        budget_data = request.form["budget"]
        mile_data = request.form["mile"]  

        # IPアドレスから事業所名を取得
         #request.headersでHTTPリクエストのヘッダーの情報を取得、get('X-Forwarded-For', None)でヘッダーの中からX-Forwarded-Forを取得
        forwarded_for = request.headers.get('X-Forwarded-For', None) 
        #リバースプロキシがある場合は上、ない場合はremote_addrを使用してIPアドレスを取得
        if forwarded_for:
             #split(',')[0]は文字列に対して引数に指定した所で区切るメソッド（何個もあるIPアドレスの１番目を取得）、.strip()は前後の余分な空白や改行を削除するメソッド  
            user_ip = forwarded_for.split(',')[0].strip()  
        else:
            user_ip = request.remote_addr  
         # オブジェクト.get(一致を求める値、一致しなかった際に返す値) →オブジェクトに対して第一引数の値が一致するか確認し一致してたらその値を返す、一致してなければ第二引数を返す   
        branch_name = branch_map.get(user_ip, "事業所なし")

        # 新しい業務報告データ（3行目に挿入する）
        #各列にフォームから取得して下記リストのデータを入れる
        new_data = [
            "",
            today_full,   # B列: 日付
            branch_name,  # C列: 事業所名
            revenue_data + "万円",  # D列: 売上予測
            budget_data + "万円",   # E列: 予算差
            mile_data,    # F列: マイルストーンチェック
            report_data   # G列: 備考
        ]
        
         # 3行目に新しいデータを挿入し、既存データを1行ずつ下へずらす （基本）ws.insert_row(データのリスト, 挿入する行の位置)
        ws.insert_row(new_data, index=3)

         # 予算差がマイナスの場合、E列を赤字にする 
        if "-" in budget_data:
            ws.format("E3", {
                "textFormat": {"foregroundColor": {"red": 1, "green": 0, "blue": 0}, "bold": True, "fontSize": 15}
            })
        else:
            ws.format("E3", {
                "textFormat": {"foregroundColor": {"red": 0, "green": 0, "blue": 0}, "bold": True, "fontSize": 15}
            })
        

        # マイルストーン振り返り期間中はB列の日付に色をつける
        today_day = today.day #today.dayのdayはプロパティ（値だけを取得したい）ので（）はいらない
        if today_day in [3, 4, 5, 19, 20, 21]: #if today_day == 3 or 4 or 5 or 19 or 20 or 21:この書き方は×or以降”数値”として判断されるから０以外全部tureになる
            ws.format("B3", {
                "textFormat": {"foregroundColor": {"red": 0, "green": 0, "blue": 2}, "bold": True, "fontSize": 12}
            })
        else:
            ws.format("B3", {
                "textFormat": {"foregroundColor": {"red": 0, "green": 0, "blue": 0}, "bold": True, "fontSize": 12}
            })
        
            
        #マイストーンチェックをプルダウン化にする
        if mile_data == "option2":
            ws.update_acell(f"F3","〇")
        else:
            ws.update_acell(f"F3","")
        
         # 送信後スプレッドシートへ飛ぶ HTMLファイルに飛ばしたいときはrender_template、URLに飛ばしたかったらredirect
        return render_template("exit.html")

    return render_template("report.html") #GETに対応。spread関数を実行するときにreport.htmlを開く
    
@app.route("/spread_link")
def spread_link():
    return redirect(spreadsheet_url)

# if __name__ == "__main__" :
#     app.run(host="0.0.0.0", port=8090, debug=True)　リモートホスト用



