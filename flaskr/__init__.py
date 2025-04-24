# templatesフォルダはこのままの名前で必須（名前変える方法もあるが...)

# flaskの起動（パワーシェルで実施）
# $env:FLASK_APP="flaskr" 
# $env:FLASK_ENV="development"
# $env:FLASK_DEBUG="1"
# flask run

from flask import Flask
from flask_sqlalchemy import SQLAlchemy 
import os

app = Flask(__name__) #Flaskクラスのインスタンスを作成 __name__はどのPythonファイルでアプリが実行されてるのか示す

# PostgreSQLの接続情報を設定 ローカルホスト用（そのまま記載したらOK）
# DB_INFO = {
#     "user": "postgres",
#     "password" : "12731273",
#     "host" : "localhost",
#     "name" : "postgres"
# }
# SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://{user}:{password}@{host}/{name}".format(**DB_INFO)
# #Flaskに「これが使うべきデータベースですよ」と教え記憶させてる　= SQLALCHEMY_DATABASE_URIは変数（右辺）
# app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI

# WEBアプリ用
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")#sessionモジュールを使うための秘密鍵。これ設定しないとsessionモジュール使えない
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")#renderで作成したpostgreSQLをflaskで接続するために必要
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # 警告を消すため

# dbのインスタンス化
db = SQLAlchemy(app)

# 他のインポートは後で行う
from flaskr import master_login
from flaskr import main

# ⓵パスワード数を10文字以上
# ⓶スケジュールとタスクを分けて表示
# ⓷スケジュールはメモ欄を入れてメモを送信できるように
# ④タスクは期限過ぎても見れるように（完了押さないと非表示にならない）
# ⓹タスク表示期間を決めれる
# ⓺業務報告はなし
# ⓻フッターの変更
# ⓼管理者画面の充実
# ⓽ユニットごとに分けて実装

# 優先順位→まずフォルダコピーしてとりあえず⓵だけで実装し使えるようにしておく
# 1.まずは⓵④⓺を実装してとりあえず使えるようにする

# 2.⓽ユニットごとにわけてコードが入力できるようにする
# 3.第５ユニット優先で⓵④⓺のコード実装を入れる
# 4.⓶⓷⓹の実装
# 5.⓼の実装
# 6.⓻を聞いて入力