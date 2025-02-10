# templatesフォルダはこのままの名前で必須（名前変える方法もあるが...)

# flaskの起動（パワーシェルで実施）
# $env:FLASK_APP="flaskr" 
# $env:FLASK_ENV="development"
# $env:FLASK_DEBUG="1"
# flask run

from flask import Flask
app = Flask(__name__) #Flaskクラスのインスタンスを作成 __name__はどのPythonファイルでアプリが実行されてるのか示す
import flaskr.main