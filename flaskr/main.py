# from flask import Flask リモートホスト用※from flaskr import appは消す
from flaskr import app
from flask import render_template, request, redirect, url_for, json, session #HTMLのデータを読み込んでPythonのデータに埋め込んで表示させる ※jinja2を使ってる
import gspread  #gspreadモジュールをインポート
import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build #gooleapiclientライブラリ→Googleの色んなAPI（スプレとかドライブとかGmaiｌとか）を使うためのツール
from datetime import date, datetime, timedelta
from flaskr.master_login import get_user_date
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from flask_session import Session

# app = Flask(__name__)リモートホスト用

# スプレッドシートのシートを取得するための関数
def get_worksheet(unit_name,sheet_index):
    #〇開発モード用
    unit_map = {
        "第4ユニット": {"unit_json": "unit-link.json" , "sheet_id": "1DQBOs1TzvLz1r8DnomCTUCyAzACvml4cc9aHlyTB3ds"},
        "第5ユニット": {"unit_json": "spread-sheet-test.json" , "sheet_id": "1kSXfl_g3WwopEyGIIvswYzNFwotVqh_g1DPNI31gb_w"}
    }
    #WEBアプリ用
    # unit_map = {
    #     "第4ユニット": {"unit_json": os.environ["GOOGLE_APPLICATION_CREDENTIALS_UNIT_4"] , "sheet_id": "1kSXfl_g3WwopEyGIIvswYzNFwotVqh_g1DPNI31gb_w"},
    #     "第5ユニット": {"unit_json": os.environ["GOOGLE_APPLICATION_CREDENTIALS"] , "sheet_id": "1kSXfl_g3WwopEyGIIvswYzNFwotVqh_g1DPNI31gb_w"}
    # }
        
    scopes = ["https://www.googleapis.com/auth/spreadsheets"] #スコープ：どの範囲でまでその権限・影響を及ばせるか 今回のパターンで行くとスプレッドシートの読み書きが行える
    # from_service_account_file関数に引数json_file_path, scopes=scopesを渡すことでクラスメソッドとしてCredentialsクラスに値を渡しインスタンス変数を設定。
    # グーグルアカウントの認証管理をするクラスメソッド
    config = unit_map[unit_name]
    
    credentials = Credentials.from_service_account_file(config["unit_json"], scopes=scopes)
    
    # authorizeはgspreadモジュールの関数。「この認証情報を使って、スプレッドシートを操作する許可をください！」というリクエストを送る
    # gspreadモジュールはスプレッドシートのセルやシートを簡単に操作したい時に使う（例：入力とか読み取りとか色変えるとか）
    # 認証されたらClientを返し、gspread.Clientオブジェクトとしてスプレッドシートの操作オブジェクトとなる
    gc = gspread.authorize(credentials)
    sh = gc.open_by_key(config["sheet_id"])
    ws = sh.get_worksheet(sheet_index)

    return ws
    

# スプレッドシートのタスク一覧を昇順で並べ替えリクエスト作成関数→管理者画面でタスク登録した際に実行
def sort_by_task_deadline_desc(unit_name): 
    unit_map = {
        "第4ユニット": {"unit_json": "unit-link.json" , "sheet_id": "1DQBOs1TzvLz1r8DnomCTUCyAzACvml4cc9aHlyTB3ds"},
        "第5ユニット": {"unit_json": "spread-sheet-test.json" , "sheet_id": "1kSXfl_g3WwopEyGIIvswYzNFwotVqh_g1DPNI31gb_w"}
    }
    #WEBアプリ用
    # unit_map = {
    #     "第4ユニット": {"unit_json": os.environ["GOOGLE_APPLICATION_CREDENTIALS_UNIT_4"] , "sheet_id": "1DQBOs1TzvLz1r8DnomCTUCyAzACvml4cc9aHlyTB3ds"},
    #     "第5ユニット": {"unit_json": os.environ["GOOGLE_APPLICATION_CREDENTIALS"] , "sheet_id": "1kSXfl_g3WwopEyGIIvswYzNFwotVqh_g1DPNI31gb_w"}
    # }
    
    scopes = ["https://www.googleapis.com/auth/spreadsheets"] 
    config = unit_map[unit_name]

    credentials = Credentials.from_service_account_file(config["unit_json"], scopes=scopes)   
    gc = gspread.authorize(credentials)
    sh = gc.open_by_key(config["sheet_id"])
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
        spreadsheetId=config["sheet_id"],
        body=sort_request
    ).execute()
    
    
spreadsheet_url_5_1 = "https://docs.google.com/spreadsheets/d/1kSXfl_g3WwopEyGIIvswYzNFwotVqh_g1DPNI31gb_w/edit?gid=0#gid=0"
spreadsheet_url_5_2 = "https://docs.google.com/spreadsheets/d/1kSXfl_g3WwopEyGIIvswYzNFwotVqh_g1DPNI31gb_w/edit?gid=1221591128#gid=1221591128"

spreadsheet_url_4_1 = "https://docs.google.com/spreadsheets/d/1DQBOs1TzvLz1r8DnomCTUCyAzACvml4cc9aHlyTB3ds/edit?gid=0#gid=0"
spreadsheet_url_4_2 = "https://docs.google.com/spreadsheets/d/1DQBOs1TzvLz1r8DnomCTUCyAzACvml4cc9aHlyTB3ds/edit?gid=0#gid=0"
#   #クラスメソッドで本日の日付と曜日を取得
today =date.today()
week = ["（月）", "（火）", "（水）", "（木）", "（金）", "（土）", "（日）"]
today_str = datetime.today().strftime("%Y/%m/%d")#isoformatメソッドで今日の日付を文字列にする
today_week = week[today.weekday()] #weekdayメソッドは取得した日付の曜日を数字として表す
today_full = f"{today_str} {today_week}"

# report.htmlの内容（業務報告入力した内容）をスプレッドシートへ反映    
@app.route("/spread", methods=["GET", "POST"]) 
#POST:入力データを送る、GET:ページを開く POSTは送る側・貰う側両方設定必要。（GETは貰う側だけでOK)
@login_required
def spread():
    
    unit_name = get_user_date(current_user.id).unit_name
    ws = get_worksheet(unit_name, 0)
    
    if request.method == "POST":
        # フォームのデータを取得
        report_data = request.form["report"]
        revenue_data = request.form["revenue"]
        budget_data = request.form["budget"]
        mile_data = request.form["mile"]  
        
        #事業所名をDBから取得
        office_name = get_user_date(current_user.id).office_name
        
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
        return redirect(spreadsheet_url_4_1)

    return render_template(
        "report.html") #GETに対応。spread関数を実行するときにreport.htmlを開く

# 【関数】スケジュールのスプレッドシートからデータを取得する関数   
def get_schedule(unit_name, index):
    ws_sheet = get_worksheet(unit_name, index)
    date_3 = ws_sheet.get_all_values("B2:J")
    today = date.today() 
    today_day = today.day
    schedule_1 =[]
    schedule_2 =[]
    
    for idx, row in enumerate(date_3[1:]):
        row_1 = row[:4]
        day = row_1[0]
        schedule = row_1[1] if len(row_1) > 1 else ""
        schedule_display_day = row_1[2] if len(row_1) > 2 else ""
        schedule_url = row_1[3] if len(row_1) > 3 else ""
        
        row_2 = row[5:]
        day_2 = row_2[0]
        schedule_data_2 = row_2[1] if len(row_2) > 1 else ""
        schedule_display_day_2 = row_2[2] if len(row_2) > 2 else ""
        schedule_url_2 = row_2[3] if len(row_2) > 3 else ""
        
        # スプレッドシートの日付の部分を実際のdate型に置き換える
        try:
            schedule_day = date(today.year, today.month, int(day))
        except ValueError:
            continue  # 日付変換できなければスキップ
        try:
            schedule_day_2 = date(today.year, today.month, int(day_2))
        except ValueError:
            continue  # 日付変換できなければスキップ
        
        # スプレッドシートの表示開始日を数値に置き換える    
        if schedule_display_day == "1日前":
            ago = 1
        elif schedule_display_day == "3日前":
            ago = 3
        else:
            ago = 7
            
        if schedule_display_day_2 == "1日前":
            ago_2 = 1
        elif schedule_display_day_2 == "3日前":
            ago_2 = 3
        else:
            ago_2 = 7
        
        # スケジュール日から表示開始日を引いて何日前から表示させるかを確定        
        days_ago = schedule_day - timedelta(days = ago)
        days_ago_2 = schedule_day_2 - timedelta(days = ago_2)
                
        # 表示開始日がスプレッドシートに入ってるかの判定（if schedule_display_day is Noneでは空欄を判定しない）
        if not schedule_display_day:
            is_display = int(day) == today_day
        else:
            is_display = schedule_day >= today >= days_ago
            
        if not schedule_display_day_2:
            is_display_2 = int(day_2) == today_day
        else:
            is_display_2 = schedule_day_2 >= today >= days_ago_2
        
        # スケジュールが入っててかつ表示開始日がある（表示開始日は空欄でもＯＫ）
        if schedule and is_display:
                schedule_1.append({
                    "cell_rw": idx,
                    "day": day,
                    "schedule": schedule,
                    "schedule_url": schedule_url})

        if schedule_data_2 and is_display_2:
                schedule_2.append({
                    "cell_rw": idx,
                    "day": day_2,
                    "schedule": schedule_data_2,
                    "schedule_url": schedule_url_2})
        
    return schedule_1, schedule_2

# 【関数】タスクのスプレッドシートからデータを取得する関数   
def get_task(unit_name, index, office_name):
    ws_2 = get_worksheet(unit_name, index)
  # ●タスク表示用のデータ取得
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

    if len(data) < 2:
        task = None
        coment = "本日のタスクはありません"
    else:
        #●表示用ロジック（ログインしてる事業所に応じて表示切り替え）
        # 取得した行（列の場合もあり）を要素のインデックスと各行ずつidx,rowにリスト化
        # enumerate関数→要素のインデックスを取得
        for idx, row in enumerate(data[1:]):
            deadline = row[0]
            try:
                if deadline and deadline.strip():
                    deadline_date = datetime.strptime(deadline.strip(), "%Y/%m/%d").date()
                    deadline_display = deadline.strip()  # すでに"YYYY/MM/DD"なのでそのまま
                else:
                    deadline_display = ""
            except ValueError:
                deadline_display = ""
            task_name  = row[1] 
            # もし取得したデータが３つより大きい場合はtask_urlにURLを入れる、それ以外は空白で。
            # ["日付", "タスク名", "事業所"]でURLなしでタスク登録された場合、事業所がrow[2]になるの防ぐ
            task_url = row[2] if len(row) > 3 else ""
            office = row[3]
            task_display_day = row[4]
            is_done = row[office_index] if len(row) > office_index else ""
            try:
                task_display_dayago = datetime.strptime(task_display_day.strip(), "%Y/%m/%d").date() if task_display_day and task_display_day.strip() else None
            except ValueError:
                task_display_dayago = None
                
            # deadline_dateがNoneでない場合にのみ、比較処理を行う
            if task_display_dayago:
                # 表示条件
                is_display_start = (task_display_dayago is None) or (today >= task_display_dayago)
                is_target_office = office == "全事業所" or office == office_name
                is_not_done = is_done != "〇"

                if is_display_start and is_target_office and is_not_done:
                    cell_rw = idx
                    today_tasks.append((cell_rw, deadline_display, task_name, task_url, office))
            else:
                # deadlineがNoneのときはスキップ（または他の処理があればそれを行う）
                continue
    return today_tasks
            
            
#業務報告をする、見る画面（title.hmtlにタスクを表示させたいからrender_template関数使って
# 　　　　　　　　　　　　　　　　　　　　　　　　表示させるためタスク実装のコードをここに記載）
@app.route("/title", methods=["POST", "GET"])
@login_required
def title():
    # ユニットによってHTMLの表示内容を変更する（Pythonでユニット名を取得してHTMLでif文使って反映）
    unit_name = get_user_date(current_user.id).unit_name
    unit_name_type_1 = None  # 初期化
    unit_name_type_2 = None 
    if unit_name == "第4ユニット":
        unit_name_type_1 = unit_name
    else:
        unit_name_type_2 = unit_name
   
    # master_login.pyからget_user_date関数（ログインした事業所のidを取得する関数）をインポート利用
    office_name = get_user_date(current_user.id).office_name
    
    # ◎GET表示用
    # ◎get_schedule関数からスケジュールメッセージ表示のデータ取得
    schedule_1, schedule_2 = get_schedule(unit_name, 2)
    # ◎get_schedule関数からスケジュールメッセージ表示のデータ取得        
    # today_tasks = get_task(unit_name, 1, office_name)
    tasks = session.get("today_tasks", [])
    
    
      # 表示セット   
    if schedule_1 or schedule_2:
        schedule = schedule_1
        schedule2 = schedule_2
        coments = None
    else:
        schedule = None
        schedule2 = None
        coments = "本日のスケジュールはありません"
      
    if tasks:
        task = tasks
        coment = None
    else:
        task = None
        coment = "本日のタスクはありません"
    
    # ◎POST表示用    
    # ◎タスクの表示とタスクボタン関連について
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
                ws_2 = get_worksheet(unit_name, 1)
                all_rows = ws_2.get_all_values()
                            
                for row in all_rows:
                        row_deadline =row[1]
                        row_task_name = row[2]
                        # 完了ボタンを押したタスクとスプレッドシートのタスク（期限、タスク名、ログインした事業所名とスプレッドシートの事業省名）が一致したら
                        if row_deadline == done_deadline and row_task_name == done_task_name:
                            headers = ws_2.get_values("B2:Z2")[0]
                            # office_index = None
                            for i, header in enumerate(headers):
                                # ヘッダーの中にログインした事業所名が含まれていたら
                                if header == office_name:
                                    # 変数名office_indexにi、つまり要素の列番号を入れる
                                    office_index = i
                                    # スプレッドシートは１行目はインデックス１始まり。取得したdone_rowは最低値０。〇をつけたい最低行はスプレッドシートで３
                                    cell_row = done_row + 3 
                                    # office_index(5,12)の中からこの時点でoffice_indexの値は一つに絞り込まれている。
                                    # 後はスプレッドシートの数値＋１にする
                                    cell_col = office_index + 2
                                    # update_cellメソッド→（行番号,列番号,表示したいもの）
                                    ws_2.update_cell(cell_row, cell_col, "〇")
                            break
                        
                # ◎get_schedule関数からスケジュールメッセージ表示のデータ取得        
                today_tasks = get_task(unit_name, 1, office_name)
                # ◎get_schedule関数からスケジュールメッセージ表示のデータ取得
                schedule_1, schedule_2 = get_schedule(unit_name, 2)
         
                # 表示セット
                if schedule_1 or schedule_2:
                    schedule = schedule_1
                    schedule2 = schedule_2
                    coments = None
                else:
                    schedule = None
                    schedule2 = None
                    coments = "本日のスケジュールはありません"
                    
                if today_tasks:
                    task = today_tasks
                    coment = None
                else:
                    task = None
                    coment = "本日のタスクはありません"

                return render_template(
                    "title.html",
                    today=today_full,
                    office_name=office_name,
                    task=task,
                    coment=coment,
                    coments = coments,
                    done_row = done_row,
                    unit_name_type_1 = unit_name_type_1,
                    unit_name_type_2=unit_name_type_2,
                    schedule = schedule,
                    schedule2 = schedule2)  
                
    return render_template(
        "title.html",
        today=today_full,
        office_name=office_name,
        task=task,
        coment=coment,
        coments=coments,
        unit_name_type_1 = unit_name_type_1,
        unit_name_type_2=unit_name_type_2,
        schedule = schedule,
        schedule2 = schedule2
    )            
                
   
# task.htmlにタスクを表示
@app.route("/task_display")
def task_display() :
    unit_name = get_user_date(current_user.id).unit_name
    ws_2 = get_worksheet(unit_name, 1)
    
    office_name = get_user_date(current_user.id).office_name
    today_month = date.today().month# 今日の月を取得
    data = ws_2.get_values("B2:Z")
    date_header = data[0]# スプレッドシートのヘッダー（１行目）を取得
    
    today_tasks = []
    for idx, row in enumerate(data[1:]):#スプレッドシートの２行目からリストに入れる
        deadline = row[0]
        #strptime(文字列、書式)←第１引数と第２引数が一致したらdatetime型 datetime(2025, 4, 13, 0, 0)を文字列から変更するdatetimeはクラス
        if deadline and deadline.strip():
                try:
                    deadline_date = datetime.strptime(deadline.strip(), "%Y/%m/%d")
                    # 例）本日が2025/4/13 2025/4/13←これがdeadline_dateで.monthでこの中の月←４
                    if deadline_date.month in [today_month, today_month % 12 + 1]: #%12 + 1は13月にならないように
                        deadline = row[0]
                    else:
                        continue
                except ValueError:
                    # 日付の形式が正しくない場合はNoneに設定
                    deadline_date = None
        else:
            deadline_date = None
        
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
       
#管理者画面　サインアップとDBを表示させる 
@app.route("/master", methods = ["GET", "POST"]) #app.routeはエンドポイントを含めたブラウザを表示させると同時に直後の関数も実行する。関数でＨＴＭＬが設定されているとブラウザ上にＨＴＭＬが表示される
@login_required  #「ログインしているか？」をチェックするデコレーター
def master():#トップ画面が表示される時に使われる関数 
    from flaskr.master_login import Post 
    unit_name = get_user_date(current_user.id).unit_name
    unit_name_type_1 = None  # 初期化
    unit_name_type_2 = None 
    if unit_name == "第4ユニット":
        unit_name_type_1 = unit_name
    else:
        unit_name_type_2 = unit_name
        
    ws_2 = get_worksheet(unit_name, 1)
    
    #Post.queryでクラスメソッドによるオブジェクト化（PostのDBに対して取得・操作・更新などの指示、命令をするメソッド）
    # Post テーブルのデータを id の昇順で並べて、すべて取得する(order_byメソッド)
    # filter_by(unit_name = unit_name)→テーブルにフィルターをかける（テーブルのカラム名 =　Pythonの変数）
    #all()で全ての情報をリスト化して返す
    posts = Post.query.filter_by(unit_name = unit_name).order_by(Post.id).all()
    
    get_sheets_B = ws_2.get("B2:B")
    
    if request.method == "POST":
        # 完了ボタンを押すことによるtask_okだけのPOSTとタスク入力のPOSTを分けて使い分けるためのif文（全部一緒ではエラー出る
        if "task_ok" not in request.form:
            deadline_raw = request.form["deadline"]
            # replace関数：第１引数の文字列を第２引数の文字列に変換（今回は例：2025-04-20→2025/04/20に変換）
            deadline = deadline_raw.replace("-", "/")
            task_name = request.form["task"]
            task_url = request.form["task_url"]
            select_office = request.form["select_office"]  # 登録用
            task_display = request.form["task_display_day"]
            task_display_day = task_display.replace("-", "/")
                        
            if not task_url:
               task_url = ""
               
            new_task = [deadline, task_name, task_url, select_office, task_display_day]   
            # B2列のデータを全て取得してlenで数を数える。+2はB2を外しての数を数えるから入力したいセルは+2個目になる
            next_row = len(get_sheets_B) + 2  # B2から数えて次の空き行
            ws_2.update(f"B{next_row}:F{next_row}", [new_task])      
            
            sort_by_task_deadline_desc(unit_name)
 
    return render_template(
       "master.html",posts = posts, unit_name_type_1  = unit_name_type_1,
       unit_name_type_2 = unit_name_type_2
   )
    
    # スプレッドシートへ飛ぶ    
@app.route("/spread_link")
def spread_link():
    return redirect(spreadsheet_url_5_2)
@app.route("/spread_link_4")
def spread_link_4():
    return redirect(spreadsheet_url_4_2)

# if __name__ == "__main__" :
#     app.run(host="0.0.0.0", port=8090, debug=True)　リモートホスト用


 
