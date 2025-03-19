# templatesフォルダはこのままの名前で必須（名前変える方法もあるが...)

# flaskの起動（パワーシェルで実施）
# $env:FLASK_APP="flaskr" 
# $env:FLASK_ENV="development"
# $env:FLASK_DEBUG="1"
# flask run

from flask import Flask
from flask_sqlalchemy import SQLAlchemy 

app = Flask(__name__) #Flaskクラスのインスタンスを作成 __name__はどのPythonファイルでアプリが実行されてるのか示す

# PostgreSQLの接続情報を設定（そのまま記載したらOK）
DB_INFO = {
    "user": "postgres",
    "password" : "12731273",
    "host" : "localhost",
    "name" : "postgres"
}
SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://{user}:{password}@{host}/{name}".format(**DB_INFO)
#Flaskに「これが使うべきデータベースですよ」と教え記憶させてる　= SQLALCHEMY_DATABASE_URIは変数（右辺）
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI


# dbのインスタンス化
db = SQLAlchemy(app)

# 他のインポートは後で行う
from flaskr import master_login
from flaskr import main