from flaskr import app, db
from flask import render_template, request, redirect, url_for, json, session, make_response,flash
from datetime import datetime, date, timedelta
from flask_sqlalchemy import SQLAlchemy 
import psycopg2,os
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash


# ローカル用　セッションキーの設定
# app.config["SECRET_KEY"] = os.urandom(24)

#Flask-Loginの「Remember Me（ログイン状態を維持）」機能を制御
#Flask-Login が「Remember Me」用のクッキーを作成し、セッションが切れても自動ログインできるようになる。通常はブラウザ綴じるとセッション切れる
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7)
app.config['SESSION_COOKIE_SECURE'] = True  # Secure属性を有効にする

# login_managerインスタンス化
login_manager = LoginManager()
login_manager.init_app(app)

# postgreSQlのDB作成に当たってのクラス作成（SQLAlchemy用） 
class Post(UserMixin,db.Model): #flask_loginモジュールのUserMixinクラスの継承：クラスの内容→⓵is_authenticated	ユーザーが認証済みかどうかを判定 (True or False)
    #⓶is_active	アカウントが有効かどうか (True or False)⓷is_anonymous 匿名ユーザーかどうか (False にする)④get_id()	ユーザーの識別IDを取得（セッション管理で使う）
    __tablename__ = 'unit_link'  # 必要ならテーブル名を明示的に指定
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(10), nullable=False)
    pw = db.Column(db.String(200), nullable=False)
    office_name = db.Column(db.String(10), nullable=False)

#@ユーザーが再読み込みする際にlogin_manager.user_loaderがsessionから主キーを読み込みuser_idに引数を渡す
#returnとしてPost.query.get(user_id)で取得した主キーに対応したユーザー情報をcurrent_user関数に返す
#current_user の主な目的は、現在ログインしているユーザーの情報にアクセスできるようにすること
@login_manager.user_loader
def load_user(user_id):
    return Post.query.get(user_id)

# postgreSQLでテーブル作成コード（ターミナルでpython -m flaskr.master_login)
with app.app_context():
    db.create_all()  # テーブルを作成
    print("テーブル作成完了！")

today =date.today()
week = ["（月）", "（火）", "（水）", "（木）", "（金）", "（土）", "（日）"]
today_str = today.isoformat()#isoformatメソッドで今日の日付を文字列にする
today_week = week[today.weekday()] #weekdayメソッドは取得した日付の曜日を数字として表す
today_full = f"{today_str} {today_week}"

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
            #login_userはflask_loginモジュールの関数：引数の値にユーザー情報（主キーが入った）を代入。sessionに主キーを保存する
            session.clear()
            #主キーの情報は再読み込み時に@login_manager.user_loaderが処理する
            login_user(user, remember=True)
            #管理者はまず管理者画面に飛ぶ
            if user.username == "master":
                # login_user(user)
                return redirect(url_for("master"))
             #一致していればログインさせてタイトル画面に    
            return redirect(url_for("title")) 
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
def office_name_header_spreadsheets(office_name):
    from flaskr.main import spread_sheets
    ws_2 = spread_sheets(1)
    current_header = ws_2.get_all_values("B2:Z2")[0]
    if office_name and office_name not in current_header:
        current_header.append(office_name)
        ws_2.update("B2", [current_header])
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
        # 新規登録したら登録した事業所名がスプレッドシートのヘッダーに反映される
        if office_name:
            office_name_header_spreadsheets(office_name)
        #ユーザー名・PW・事業所名が入力出来てない時にエラーを出す
        if not username or not pw or not office_name:
            # flash関数（flaskの組み込み関数）リダイレクト時にメッセージを表示するための関数　メッセージを一時的に保持する
            flash("すべての項目を入力してください", "danger")
            return redirect(url_for("master"))  # 登録ページにリダイレクト
        #Postクラスに対してのインスタンス化
        post = Post(username = username , pw = hashed_pass , office_name = office_name)
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
        
        db.session.commit()
        # DBの削除 #IDの完全削除→pgアドミンで：TRUNCATE TABLE office RESTART IDENTITY; を入力
    elif post_delete:
        db.session.delete(post_delete)
        db.session.commit()  

    return redirect(url_for("master"))


#ログインした事業所名を取得する関数
#引数にログインした事業所の主キーを入れて主キーに当てはまる行の情報を全て取得
def get_office_name(user_id):
    user = Post.query.get(user_id)
    return user.office_name 




#業務報告する画面    
@app.route("/form")  #<a href="{{ url_for('form') }}">このコードによってhttp://127.0.0.1:5000/formにアクセス白ってこと
@login_required 
def form():#http://127.0.0.1:5000/formにアクセスしたらform関数を実行しろってこと→つまりhttp://127.0.0.1:5000/formのブラウザにreport.htmlを表示させるってこと
    #current_user.idは現在ログインしているユーザーの主キーを取得
    office_name = get_office_name(current_user.id)
    
    from flaskr.main import today_full
    
    return render_template("report.html",office_name = office_name,today=today_full
    )
    



    
    