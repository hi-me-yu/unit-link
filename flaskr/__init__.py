# templatesフォルダはこのままの名前で必須（名前変える方法もあるが...)

# flaskの起動（パワーシェルで実施）
# $env:FLASK_APP="flaskr" 
# $env:FLASK_ENV="development"
# $env:FLASK_DEBUG="1"
# flask run

from flask import Flask
from flask_sqlalchemy import SQLAlchemy 
import os
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from datetime import datetime, date, timedelta
from flask_session import Session

app = Flask(__name__) #Flaskクラスのインスタンスを作成 __name__はどのPythonファイルでアプリが実行されてるのか示す

# PostgreSQLの接続情報を設定 ローカルホスト用（そのまま記載したらOK）
DB_INFO = {
    "user": "postgres",
    "password" : "12731273",
    "host" : "localhost",
    "name" : "postgres"
}
SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://{user}:{password}@{host}/{name}".format(**DB_INFO)
#Flaskに「これが使うべきデータベースですよ」と教え記憶させてる　= SQLALCHEMY_DATABASE_URIは変数（右辺）
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI

# WEBアプリ用
# app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")#sessionモジュールを使うための秘密鍵。これ設定しないとsessionモジュール使えない
# app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")#renderで作成したpostgreSQLをflaskで接続するために必要
# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # 警告を消すため

# ローカル用　セッションキーの設定
app.config["SECRET_KEY"] = os.urandom(24)

# flask-sessionの初期化
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

#Flask-Loginの「Remember Me（ログイン状態を維持）」機能を制御
#Flask-Login が「Remember Me」用のクッキーを作成し、セッションが切れても自動ログインできるようになる。通常はブラウザ綴じるとセッション切れる
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7)
app.config['SESSION_COOKIE_SECURE'] = True  # Secure属性を有効にする

# dbのインスタンス化
db = SQLAlchemy(app)

# login_managerインスタンス化
login_manager = LoginManager()
login_manager.init_app(app)

# 他のインポートは後で行う
from flaskr import master_login
from flaskr import main

# ⓵パスワード数を10文字以上 〇
# ⓶スケジュールとタスクを分けて表示
# ⓷スケジュールはメモ欄を入れてメモを送信できるように
# ④タスクは期限過ぎても見れるように（完了押さないと非表示にならない）　〇
# ⓹タスク表示期間を決めれる　〇
# ⓺業務報告はなし　〇
# ⓻フッターの変更
# ⓼管理者画面の充実
# ⓽ユニットごとに分けて実装　ココ　←スプレッドシートを分けてタスクが管理できるように

# 優先順位→まずフォルダコピーしてとりあえず⓵だけで実装し使えるようにしておく
# 1.まずは⓵④⓺を実装してとりあえず使えるようにする

# 2.⓽ユニットごとにわけてコードが入力できるようにする
# 3.第５ユニット優先で⓵④⓺のコード実装を入れる
# 4.⓶⓷⓹の実装
# 5.⓼の実装
# 6.⓻を聞いて入力

# ◎スプレッドシートの呼び出しを必要最小限にして軽くする
# 1. 初回ログイン時にスプレッドシートを一括取得
# ユーザーがログインした際に、必要なデータ（例えば、タスクなど）をスプレッドシートから一括で取得。
# スプレッドシートデータをFlaskセッションに保存。

# 2. POST操作時のみスプレッドシートを更新
# ユーザーがタスクやデータを追加・更新した際に、スプレッドシートをPOSTリクエストで更新。
# その後、更新内容をセッションに反映し、再度保存。

# 3. GET時にセッションのデータを使用
# ログイン後、GETリクエストが発生する度にセッション内のデータを使用。
# 5分ごとの自動更新（バックグラウンドで定期的にGETして最新のデータをセッションにキャッシュ）を実施。

# 4. 定期的なスプレッドシートの更新
# 定期的にスプレッドシートのデータをチェックして最新データを反映。
# 例えば、5分後に自動でスプレッドシートを更新し、その後セッションに保存する。

# 5. セッションデータの管理
# ユーザーごとにスプレッドシートのデータを個別にセッション保存（事業所ごとに分ける）。
# セッションの有効期限（7日間）内にアプリを再度開く場合、保存されたデータを再利用。

# 6. セッション保存とRedisなどの活用
# セッション保存が大きくなった場合、Redisを使ってセッション管理をスケーラブルに。
# Flask-Sessionのfilesystemを使うが、データ量が増えた場合はRedisに移行を検討。

# 7. セッションのデータ量を最適化
# 必要なデータ（例えばタスクの直近2ヶ月分のみ）を取得し、データの量を最小化。
# セッションに保存するデータ量が増えすぎないように管理。