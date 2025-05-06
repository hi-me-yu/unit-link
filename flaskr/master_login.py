from flaskr import app, db, login_manager
from flask import render_template, request, redirect, url_for, json, session, make_response,flash
from datetime import datetime, date, timedelta
from flask_sqlalchemy import SQLAlchemy 
import psycopg2,os,re
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash



# postgreSQlのDB作成に当たってのクラス作成（SQLAlchemy用） 
class Post(UserMixin,db.Model): #flask_loginモジュールのUserMixinクラスの継承：クラスの内容→⓵is_authenticated	ユーザーが認証済みかどうかを判定 (True or False)
    #⓶is_active	アカウントが有効かどうか (True or False)⓷is_anonymous 匿名ユーザーかどうか (False にする)④get_id()	ユーザーの識別IDを取得（セッション管理で使う）
    __tablename__ = 'unit_link'  # 必要ならテーブル名を明示的に指定
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(10), nullable=False)
    pw = db.Column(db.String(200), nullable=False)
    office_name = db.Column(db.String(10), nullable=False)
    unit_name = db.Column(db.String(15), nullable=False)

#@ユーザーが再読み込みする際にlogin_manager.user_loaderがsessionから主キーを読み込みuser_idに引数を渡す
#returnとしてPost.query.get(user_id)で取得した主キーに対応したユーザー情報をcurrent_user関数に返す
#current_user の主な目的は、現在ログインしているユーザーの情報にアクセスできるようにすること
@login_manager.user_loader
def load_user(user_id):
    return Post.query.get(user_id)

# postgreSQLでテーブル作成コード（ターミナルでpython -m flaskr.master_login)
# with app.app_context():
#     db.create_all()  # テーブルを作成
#     print("テーブル作成完了！")

today =date.today()
week = ["（月）", "（火）", "（水）", "（木）", "（金）", "（土）", "（日）"]
today_str = today.isoformat()#isoformatメソッドで今日の日付を文字列にする
today_week = week[today.weekday()] #weekdayメソッドは取得した日付の曜日を数字として表す
today_full = f"{today_str} {today_week}"


# ログイン時に取得するスプレッドシートのデータを絞るための関数
def filter_3months(unit_name, office_name):
    from flaskr.main import get_worksheet
    ws_2 = get_worksheet(unit_name, 2)
    
    datas = ws_2.get_all_values("B2:B")
    
    today = datetime.today().date()
    month_ago = today - timedelta(days = 45)
    month_late = today + timedelta(days = 45)
    
    recent_rows = []
    for i, row in enumerate(datas):
        try:
            # stripメソッド→文字列から先頭と末尾の余分な空白を取り除く
            date_str = row[0].strip()
            # 例）datetime.date(20255.5)となる　strptime(変換したい文字列、変換するために必要な文字列の形)
            row_date = datetime.strptime(date_str, "%Y/%m/%d").date()
            if month_late >= row_date >= month_ago:
                recent_rows.append(i + 2)
        except:
            continue
    
    filter_data_1 = []
    for row_num in recent_rows:
        row_data = ws_2.get_all_values(f"A{row_num}:Z{row_num}")
        if row_data:
            filter_data_1.append(row_data[0])
    
     # タスクデータの抽出と整形
    headers = ws_2.get_values("B2:Z2")[0]  # ヘッダー取得
    office_index = None
    for i, header in enumerate(headers):
        if header == office_name:
            office_index = i
            break
    
    today_tasks = []

    # タスクデータを処理
    for idx, row in enumerate(filter_data_1):
        deadline = row[0]
        task_name = row[1]
        task_url = row[2] if len(row) > 3 else ""
        office = row[3]
        task_display_day = row[4]
        is_done = row[office_index] if len(row) > office_index else ""
        
        try:
            task_display_dayago = datetime.strptime(task_display_day.strip(), "%Y/%m/%d").date() if task_display_day and task_display_day.strip() else None
        except ValueError:
            task_display_dayago = None
        
        # タスクの表示条件
        if task_display_dayago:
            is_display_start = (task_display_dayago is None) or (today >= task_display_dayago)
            is_target_office = office == "全事業所" or office == office_name
            is_not_done = is_done != "〇"

            if is_display_start and is_target_office and is_not_done:
                today_tasks.append((idx, deadline, task_name, task_url, office))

    return today_tasks
    
#一番最初のトップ画面　ログイン画面
@app.route("/") #app.routeはエンドポイントを含めたブラウザを表示させると同時に直後の関数も実行する。関数でＨＴＭＬが設定されているとブラウザ上にＨＴＭＬが表示される
def index():#トップ画面が表示される時に使われる関数
    a = "ログイン画面"  
    if current_user.is_authenticated:
        return redirect(url_for('title'))  # ログイン済みならトップページへ
    return render_template(
       "login.html", login = a
   )
    
#ログイン機能の実装    
@app.route("/login", methods = ["GET", "POST"]) #app.routeはエンドポイントを含めたブラウザを表示させると同時に直後の関数も実行する。関数でＨＴＭＬが設定されているとブラウザ上にＨＴＭＬが表示される
def login():
    from flaskr.main import get_task
    if request.method == "POST":    
    #ユーザ名とパスワードの受け取り
        username = request.form.get("username")
        pw = request.form.get("pw")
        #ユーザ名を元にDBから情報を取得 filter_by():SQLAlchemy の クエリオブジェクトに対してフィルタ条件をかける（id = 3, pw = pw　であればidカラムで３を探す。　pwカラムのpw値を探す）
       #UserMxinクラスを継承していることでget_id()が自動的に発動してid値とpw値に一致する行の主キーを自動的に取得している
        user=Post.query.filter_by(username = username).first() #first()：一番最初の行を取得
        #入力ID/PWとDBベースの情報が一致しているか確認
        #間違ってる場合はエラーと共にログイン画面医
        if user and check_password_hash(user.pw, pw):
            # 前のセッション情報を一旦クリアして次にログインしてきたデータを保存するために備える
            session.clear()
            #login_userはflask_loginモジュールの関数：引数の値にユーザー情報（主キーが入った）を代入。sessionに主キーを保存する
            #主キーの情報は再読み込み時に@login_manager.user_loaderが処理する
            login_user(user, remember=True)
            #管理者はまず管理者画面に飛ぶ
            unit_name = user.unit_name
            # 第〇ユニットの数字の部分だけを取得　r"\D"→数字以外の文字を意味する正規表現　""→どうしたいか？削除しなさい
            unit_number = re.sub(r"\D","",unit_name)
            
            office_name = user.office_name
            # today_tasks = filter_3months(unit_name, office_name)
            today_tasks = get_task(unit_name, 1, office_name)
            task_dicts = [
                {
                    "row": idx,
                    "deadline": deadline,
                    "task_name": task_name,
                    "task_url": task_url,
                    "office": office
                }
            for idx, deadline, task_name, task_url, office in today_tasks]
            session['today_tasks'] = task_dicts
            
            if user.username == f"master{unit_number}":
                # login_user(user)
                return redirect(url_for("master"))
            return redirect(url_for('title'))
        else:
            error = "IDもしくはPWが間違っています"
            return render_template("login.html", error = error)
    else:
        return render_template("login.html")


#ログアウト機能の実装
@app.route("/logout")
def logout():
    session.clear()
    logout_user()
    return redirect(url_for("index")) 


# 新規登録したら登録した事業所名がスプレッドシートのヘッダーに反映される関数
def office_name_header_spreadsheets(office_name, unit_name):
    from flaskr.main import get_worksheet
    ws = get_worksheet(unit_name ,1)    
    current_header = ws.get("B2:Z2")[0]
    
    if office_name and office_name not in current_header:
        current_header.append(office_name)
        ws.update("B2", [current_header])
        return current_header
    

    
#新規登録をして送信したら情報を受け取る
@app.route("/register", methods = ["POST"])
def register():
    if request.method == "POST":
        #request.formでクラスに対してのインスタンス化→request.formでインスタンス化したものにget()：インスタンスメソッド
        username = request.form.get("username")
        pw = request.form.get("pw")
        # パスワードのハッシュ化（暗号化）
        hashed_pass = generate_password_hash(pw)
        office_name = request.form.get("office_name")
        unit_name = request.form.get("unit_name")
        # 新規登録したら登録した事業所名がスプレッドシートのヘッダーに反映される
        if office_name:
            office_name_header_spreadsheets(office_name, unit_name)
        #ユーザー名・PW・事業所名が入力出来てない時にエラーを出す
        if not username or not pw or not office_name:
            # flash関数（flaskの組み込み関数）リダイレクト時にメッセージを表示するための関数　メッセージを一時的に保持する
            flash("すべての項目を入力してください", "danger")
            return redirect(url_for("master"))  # 登録ページにリダイレクト
        #Postクラスに対してのインスタンス化
        post = Post(username = username , pw = hashed_pass , office_name = office_name, unit_name = unit_name)
        #SQLAlchemyでDBの管理・操作するためのコード。(db.sessionが基本).add()：gitでいうステージリング　.commit()：gitでいう保存
        #※ここでのセッションはクッキーを使ったセッションとは異なる
        db.session.add(post)
        db.session.commit()
        flash("登録が完了しました", "success")
        return redirect(url_for("master"))
    
#ID PWの編集・削除画面
@app.route("/update", methods=["POST"])
@login_required
def update():
    if request.method == "POST":    
        # 更新・削除ボタン列の主キーを取得
        #get()の見極め　request.form.get()は辞書型を取得するメソッド　Post.query.get()はSQLAlchemyクラスの関数（主キーに対応する値一つを取得）
        num_update = request.form.get("update") #更新ボタン
        num_delete = request.form.get("delete")  #削除ボタン
        # Postクラスの主キーに対応する値を取得　例）post = Post.query.get(1) 　
        # post.num = 1　post.id = "test1"　post.pw = "1234"　post.office_name = "Tokyo"が取得できる
        post = Post.query.get(num_update) #更新ボタン
        post_delete = Post.query.get(num_delete) #削除ボタン

    if post:
        # post.idはオブジェクトプロパティの事。上書きすることが可能
        post.username = request.form.get(f"username_{num_update}")
        post.office_name = request.form.get(f"office_name_{num_update}")
        post.unit_name = request.form.get(f"unit_name{num_update}")
        
        db.session.commit()
        # DBの削除 #IDの完全削除→pgアドミンで：TRUNCATE TABLE office RESTART IDENTITY; を入力
    elif post_delete:
        db.session.delete(post_delete)
        db.session.commit()  

    return redirect(url_for("master"))


#ログインした事業所のIDを取得する関数
#引数にログインした事業所の主キーを入れて主キーに当てはまる行の情報を全て取得
def get_user_date(user_id):
    user = Post.query.get(user_id)
    return user

#業務報告する画面    
@app.route("/form")  #<a href="{{ url_for('form') }}">このコードによってhttp://127.0.0.1:5000/formにアクセス白ってこと
@login_required 
def form():#http://127.0.0.1:5000/formにアクセスしたらform関数を実行しろってこと→つまりhttp://127.0.0.1:5000/formのブラウザにreport.htmlを表示させるってこと
    #current_user.idは現在ログインしているユーザーの主キーを取得
    office_name = get_user_date(current_user.id).office_name
    
    from flaskr.main import today_full
    
    return render_template("report.html",office_name = office_name,today=today_full
    )
    



    
    