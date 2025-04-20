# from flask import Flask リモートホスト用※from flaskr import appは消す
from flaskr import app
from flask import render_template, request, redirect, url_for, json #HTMLのデータを読み込んでPythonのデータに埋め込んで表示させる ※jinja2を使ってる
import gspread  #gspreadモジュールをインポート
import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build #gooleapiclientライブラリ→Googleの色んなAPI（スプレとかドライブとかGmaiｌとか）を使うためのツール
from datetime import date, datetime, timedelta
from flaskr.master_login import get_office_name
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user

# app = Flask(__name__)リモートホスト用

# スプレッドシートの認証情報関数
def get_spread_sheets():
        #開発モード用
    json_file_path = "spread-sheet-test.json" 
    #WEBアプリ用
    # json_file_path = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
    
    scopes = ["https://www.googleapis.com/auth/spreadsheets"] #スコープ：どの範囲でまでその権限・影響を及ばせるか 今回のパターンで行くとスプレッドシートの読み書きが行える
    # from_service_account_file関数に引数json_file_path, scopes=scopesを渡すことでクラスメソッドとしてCredentialsクラスに値を渡しインスタンス変数を設定。
    # グーグルアカウントの認証管理をするクラスメソッド
    credentials = Credentials.from_service_account_file(json_file_path, scopes=scopes)
    
    # authorizeはgspreadモジュールの関数。「この認証情報を使って、スプレッドシートを操作する許可をください！」というリクエストを送る
    # gspreadモジュールはスプレッドシートのセルやシートを簡単に操作したい時に使う（例：入力とか読み取りとか色変えるとか）
    # 認証されたらClientを返し、gspread.Clientオブジェクトとしてスプレッドシートの操作オブジェクトとなる
    gc = gspread.authorize(credentials)
    spreadsheet_id = "1kSXfl_g3WwopEyGIIvswYzNFwotVqh_g1DPNI31gb_w"
    sh = gc.open_by_key(spreadsheet_id)
    return sh

# スプレッドシートのシートを取得するための関数
def spread_sheets(ws):
    sh = get_spread_sheets()
    ws_sheets = sh.get_worksheet(ws)
    return ws_sheets

# スプレッドシートのタスク一覧を昇順で並べ替えリクエスト作成関数→管理者画面でタスク登録した際に実行
def sort_by_task_deadline_desc():
    json_file_path = "spread-sheet-test.json" 
    #WEBアプリ用
    # json_file_path = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]   
    scopes = ["https://www.googleapis.com/auth/spreadsheets"] 

    credentials = Credentials.from_service_account_file(json_file_path, scopes=scopes)   
    gc = gspread.authorize(credentials)
    spreadsheet_id = "1kSXfl_g3WwopEyGIIvswYzNFwotVqh_g1DPNI31gb_w"
    sh = gc.open_by_key(spreadsheet_id)
    ws_2 = sh.get_worksheet(1)
    sheet_id = ws_2.id  # 並べ替え対象のシートID
    
    # リクエスト内容
    sort_request = {
        "requests": [
            {
                "sortRange": {#並び替え操作指示
                    "range": {#並び替えの範囲して
                        "sheetId": sheet_id,
                        "startRowIndex": 2, #並び替え開始行（2は３行目）
                        "startColumnIndex": 0,#並び替え開始列
                        "endColumnIndex": ws_2.col_count #並び替え終了列 col_countはプロパティで列数を自動で取得してくれる
                    },
                    "sortSpecs": [#並び替え条件指定
                        {
                            "dimensionIndex": 1,  # B列
                            "sortOrder": "ASCENDING" #昇順　DESCENDINGは降順
                        }
                    ]
                }
            }
        ]
    }
    # batchUpdateメソッドを使うことで並び替え・行列の追加・非表示などシート全体に指示を与える事ができる
    # build関数：GoogleAPIクライアントライブラリのモジュール→APIリクエストを送るようするためのオブジェクト作成
    # build(serviceName:使いたいサービス（例：スプレ、ドライブ、メール）, version：APIのバージョン, credentials=None：認証)
    service = build("sheets", "v4", credentials=credentials)
    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=sort_request
    ).execute()
    
    
spreadsheet_url = "https://docs.google.com/spreadsheets/d/1kSXfl_g3WwopEyGIIvswYzNFwotVqh_g1DPNI31gb_w/edit?gid=0#gid=0"
spreadsheet_url_2 = "https://docs.google.com/spreadsheets/d/1kSXfl_g3WwopEyGIIvswYzNFwotVqh_g1DPNI31gb_w/edit?gid=1221591128#gid=1221591128"

#   #クラスメソッドで本日の日付と曜日を取得
today =date.today()
week = ["（月）", "（火）", "（水）", "（木）", "（金）", "（土）", "（日）"]
today_str = datetime.today().strftime("%Y/%m/%d")#isoformatメソッドで今日の日付を文字列にする
today_week = week[today.weekday()] #weekdayメソッドは取得した日付の曜日を数字として表す
today_full = f"{today_str} {today_week}"


    
@app.route("/spread", methods=["GET", "POST"]) 
#POST:入力データを送る、GET:ページを開く POSTは送る側・貰う側両方設定必要。（GETは貰う側だけでOK)
@login_required
def spread():
    ws = spread_sheets(0)
    
    if request.method == "POST":
        # フォームのデータを取得
        report_data = request.form["report"]
        revenue_data = request.form["revenue"]
        budget_data = request.form["budget"]
        mile_data = request.form["mile"]  
        
        #事業所名をDBから取得
        office_name = get_office_name(current_user.id)
        
        #曜日ごとの色の設定
        weekday_colors =  {
            0: {"red": 0.9, "green": 0.95, "blue": 1.0},  # 月曜: 超薄い青
            1: {"red": 1.0, "green": 0.95, "blue": 0.95},  # 火曜: 超薄い赤
            2: {"red": 1.0, "green": 1.0, "blue": 0.85},  # 水曜: 超薄い黄色
            3: {"red": 0.95, "green": 1.0, "blue": 0.95},  # 木曜: 超薄い緑
            4: {"red": 1.0, "green": 0.95, "blue": 0.85},  # 金曜: 超薄いオレンジ
            5: {"red": 0.97, "green": 0.92, "blue": 1.0},  # 土曜: 超薄い紫
            6: {"red": 1.0, "green": 1.0, "blue": 1.0}   # 日曜: 超薄い水色（白に近い）
        }

        
        
        # 新しい業務報告データ（3行目に挿入する）
        #各列にフォームから取得して下記リストのデータを入れる
        new_data = [
            "",
            today_full,   # B列: 日付
            "VP" + office_name,  # C列: 事業所名
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
       
        #曜日ごとにセルの色が変わる
        ws.format("B3:G3", {
            "backgroundColor": weekday_colors[today.weekday()]})

        # マイルストーン振り返り期間中はB列の日付に色をつける
        today_day = today.day #today.dayのdayはプロパティ（値だけを取得したい）ので（）はいらない
        if today_day in [3, 4, 5, 19, 20, 21]: #if today_day == 3 or 4 or 5 or 19 or 20 or 21:この書き方は×or以降”数値”として判断されるから０以外全部tureになる
            ws.format("B3", {
                "textFormat": {"foregroundColor": {"red": 0, "green": 0, "blue": 2}, "bold": True, "fontSize": 12}
            })
        else:
            ws.format("B3", {
                "textFormat": {"foregroundColor": {"red": 0, "green": 0, "blue": 0}, "bold": False, "fontSize": 10}
            })
        
            
        #マイストーンチェックをプルダウン化にする
        if mile_data == "option2":
            ws.update_acell(f"F3","〇")
        else:
            ws.update_acell(f"F3","")
        
         # 送信後スプレッドシートへ飛ぶ HTMLファイルに飛ばしたいときはrender_template、URLに飛ばしたかったらredirect
        return redirect(spreadsheet_url)

    return render_template(
        "report.html") #GETに対応。spread関数を実行するときにreport.htmlを開く
    

#業務報告をする、見る画面（title.hmtlにタスクを表示させたいからrender_template関数使って
# 　　　　　　　　　　　　　　　　　　　　　　　　表示させるためタスク実装のコードをここに記載）
@app.route("/title", methods=["POST", "GET"])
@login_required
def title():
    # spread_sheets(1)
    ws_2 = spread_sheets(1)
    
    # 今日の日付を引数の形で取得
    today = date.today() 
    today_2 = datetime.today().strftime("%Y/%m/%d")
    
    # master_login.pyからget_office_name関数（ログインした事業所の事業所名を取得する関数）をインポート利用
    office_name = get_office_name(current_user.id)
    
    # ◎指定日にちでマイルストーン振り返りメッセージの表示
    special_days = [3, 4, 5, 6, 19, 20, 21, 22, 28]
    message = "マイルストーン振り返りの期間です" if today.day in special_days else ""
    
    # ◎タスクの表示とタスクボタン関連について
    #POSTの場合にその情報を取得してスプレッドシートに反映
    if request.method == "POST":
        # ◎タスクボタンを押したときに各事業所のスプレッドシートに〇が付く    
        # else:    
            done_row = request.form.get("task_ok")

            
            # もし完了ボタンが押されたら
            if done_row:
                done_row = int(done_row)  
                
                # 表示されたタスクの情報を取得
                done_task_name = request.form.get("done_task_name")
                done_deadline = request.form.get("done_deadline")
                # スプレッドシートの行を全て取得（行単位で）
                all_rows = ws_2.get_all_values()
                              
                for row in all_rows:
                        row_deadline =row[1]
                        row_task_name = row[2]
                        # 完了ボタンを押したタスクとスプレッドシートのタスク（期限、タスク名、ログインした事業所名とスプレッドシートの事業省名）が一致したら
                        if row_deadline == done_deadline and row_task_name == done_task_name:
                            header_row = all_rows[1]
                            # office_indexに5.6の数字を代入
                            for office_index in range(5,8):
                                # もし２行目の5,6列目の中にログイン事業所があれば
                                if header_row[office_index] == office_name:
                                    # スプレッドシートは１行目はインデックス１始まり。取得したdone_rowは最低値０。〇をつけたい最低行はスプレッドシートで３
                                    cell_row = done_row + 3 
                                    # office_index(5,12)の中からこの時点でoffice_indexの値は一つに絞り込まれている。
                                    # 後はスプレッドシートの数値＋１にする
                                    cell_col = office_index + 1 
                                    # update_cellメソッド→（行番号,列番号,表示したいもの）
                                    ws_2.update_cell(cell_row, cell_col, "〇")
                            break
                        
                # スプレッドシートのデータを再取得し、完了したタスクを除外
                # [0]はget_valuesは返り値が２次元リスト[['タスク名', '期限', 'URL'],['タスク名', '期限', 'URL']]みたいな形で返ってくるから
                headers = ws_2.get_values("B2:Z2")[0]
                # office_index = None
                for i, header in enumerate(headers):
                    # ヘッダーの中にログインした事業所名が含まれていたら
                    if header == office_name:
                        # 変数名office_indexにi、つまり要素の列番号を入れる
                        office_index = i
                        break

                data = ws_2.get_values("B2:Z")
                today_tasks = []
                for idx, row in enumerate(data[1:]):
                    deadline = row[0]
                    task_name = row[1]
                    task_url = row[2] if len(row) > 3 else ""
                    office = row[3]
                    # 例えば、row = ['4/12', '書類提出', '', '全事業所', '〇'これ以降〇なし]の時→len(5)ってこと。
                    # 最後の〇以降はデータは取得できない。でも例えばoffice_index=6の時にlen(5)までしかないからデータがないのにrowで取得しようとしてしまいエラー出るのを防ぐ
                    # ここでは〇は関係なく、例えばrow = ['4/12', '書類提出', '', 'A事業所', '', "〇"]で、ログインしているのがoffice_index = 4 だとしてもrow=5に〇がついてるから
                    # ""としてoffice_indexの列を取得できる
                    is_done = row[office_index] if len(row) > office_index else ""
                    # タスク期限の日付をdatatime型 例：（datetime(2025, 4, 13, 10, 0, 0)からdateがたに変更
                    deadline_date = datetime.strptime(deadline, "%Y/%m/%d").date()

                    # 表示条件
                     # timedelta→何日前かを取得するメソッド（このままでdate型 例:（2025, 4, 13))
                    three_days_ago = today + timedelta(days=3)
                    # deadline_dateがthree_days_agoとtodayの間にあるか
                    is_today_ago =  today <= deadline_date <= three_days_ago
                    is_target_office = office == "全事業所" or office == office_name
                    # is_done!の!はでなかったらの否定形
                    is_not_done = is_done != "〇"
                    
                    # 期限、ログイン事業所名、事業所カラムに〇がついてなければその行の情報をtoday_tasksに追加
                    # ※逆を言うと事業所カラムに〇がついてたらその行はtoday_tasksに追加せず表示させない
                    if is_today_ago and is_target_office and is_not_done:
                        cell_rw = idx
                        today_tasks.append((cell_rw, deadline, task_name, task_url, office))
                # 表示セット
                if today_tasks:
                    task = today_tasks
                    coment = None
                else:
                    task = None
                    coment = "本日のタスクはありません"

                return render_template(
                    "title.html",
                    message=message,
                    today=today_full,
                    office_name=office_name,
                    task=task,
                    coment=coment,
                    done_row = done_row
                )  
                
     # ●表示用のデータ取得
    headers = ws_2.get_values("B2:Z2")[0]
    office_index = None
    for i, header in enumerate(headers):
        # ヘッダーの中にログインした事業所名が含まれていたら
        if header == office_name:
            # 変数名office_indexにi、つまり要素の列番号を入れる
            office_index = i
            break
    # スプレッドシートのB2列を起点にE列までの全てを取得
    data = ws_2.get_values("B2:Z")
    # データ入れる様の変数を定義
    today_tasks = []
    # 今日から３日前の日付取得
    three_days_ago = today + timedelta(days=3)

    #●表示用ロジック（ログインしてる事業所に応じて表示切り替え）
    # 取得した行（列の場合もあり）を要素のインデックスと各行ずつidx,rowにリスト化
    # enumerate関数→要素のインデックスを取得
    for idx, row in enumerate(data[1:]):
        deadline = row[0]
        task_name  = row[1] 
        # もし取得したデータが３つより大きい場合はtask_urlにURLを入れる、それ以外は空白で。
        # ["日付", "タスク名", "事業所"]でURLなしでタスク登録された場合、事業所がrow[2]になるの防ぐ
        task_url = row[2] if len(row) > 3 else ""
        office = row[3]
        is_done = row[office_index] if len(row) > office_index else ""
        
        # deadlineをdatetime型→date型に変更
        deadline_date = datetime.strptime(deadline, "%Y/%m/%d").date()
        
        # 表示条件
        # deadline_dateがthree_days_agoとtodayの間にあるか
        is_today_ago = today <= deadline_date <= three_days_ago
        is_target_office = office == "全事業所" or office == office_name
        # is_done!の!はでなかったらの否定形
        is_not_done = is_done != "〇"
        # 全事業所向けのタスク各事業所向けのタスクか判別コード（office == office_nameで今ログインしている事業所名と入力された事業所名が一致したら）
        # 期限と今日の日付が一致かつ事業所名に全事業所もしくは各事業所名が入力されたら｛タスク名とURLを空のリスト｝をtoday_taskに追加
        if is_today_ago and is_target_office and is_not_done:
            cell_rw = idx 
            today_tasks.append((cell_rw, deadline, task_name, task_url, office))

    # 表示セット
    if today_tasks:
        task = today_tasks
        coment = None
    else:
        task = None
        coment = "本日のタスクはありません"
          
    return render_template(
        "title.html",
        message=message,
        today=today_full,
        office_name=office_name,
        task=task,
        coment=coment
    )
    
# スプレッドシートへ飛ぶ    
@app.route("/spread_link")
def spread_link():
    return redirect(spreadsheet_url)

# task.htmlにタスクを表示
@app.route("/task_display")
def task_display() :
    ws_2 = spread_sheets(1)
    
    office_name = get_office_name(current_user.id)
    today_month = date.today().month# 今日の月を取得
    data = ws_2.get_values("B2:Z")
    date_header = data[0]# スプレッドシートのヘッダー（１行目）を取得
    
    today_tasks = []
    for idx, row in enumerate(data[1:]):#スプレッドシートの２行目からリストに入れる
        deadline = row[0]
        #strptime(文字列、書式)←第１引数と第２引数が一致したらdatetime型 datetime(2025, 4, 13, 0, 0)を文字列から変更するdatetimeはクラス
        deadline_date = datetime.strptime(deadline, "%Y/%m/%d")
        # 例）本日が2025/4/13 2025/4/13←これがdeadline_dateで.monthでこの中の月←４
        if deadline_date.month in [today_month, today_month % 12 + 1]: #%12 + 1は13月にならないように
            deadline = row[0]
        else:
            continue
        task_name  = row[1] 
        # もし取得したデータが３つより大きい場合はtask_urlにURLを入れる、それ以外は空白で。
        # ["日付", "タスク名", "事業所"]でURLなしでタスク登録された場合、事業所がrow[2]になるの防ぐ
        task_url = row[2] if len(row) > 3 else ""
        # select_officeのフィルターかけてる　select_officeに全事業所、office_nameがなければselect_officeはスキップされる
        select_office = row[3]
        if select_office not in ["全事業所", office_name]:
            continue
        # ヘッダーの中にログイン事業所名があれば、ログイン事業所のある要素番号を取得。ログイン事業所の列の〇だけを所得する
        office = ""
        if office_name in date_header:
            # index()→リストの中から（data_headerの事）指定した値が最初に出てくるインデックス番号を取得
            office_index = date_header.index(office_name)
            office = row[office_index] if len(row) > office_index else ""
        
        today_tasks.append({
            "deadline": deadline,
            "task_name": task_name,
            "task_url": task_url,
            "select_office": select_office,
            "office": office
        })
    
    return render_template("task.html", today_tasks = today_tasks)
    
# if __name__ == "__main__" :
#     app.run(host="0.0.0.0", port=8090, debug=True)　リモートホスト用

