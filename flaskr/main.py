from flaskr import app
from flask import render_template, request, redirect, url_for #HTMLのデータを読み込んでPythonのデータに埋め込んで表示させる ※jinja2を使ってる
import gspread  #gspreadモジュールをインポート

gc = gspread.service_account(  #service_account関数を呼び出しspread-sheet-test.jsonを使ってグーグルAPIの認証を行う
    filename=  "spread-sheet-test.json" #関数を実行して戻り値としてClientクラスが作成されそれをgcに代入
)
spreadsheet_url = "https://docs.google.com/spreadsheets/d/1kSXfl_g3WwopEyGIIvswYzNFwotVqh_g1DPNI31gb_w/edit?gid=0#gid=0"

sh = gc.open( #openメソッドで既存のスプレッドシートを呼び出す
    "test_1",
    folder_id = "16PQbDNY5ofXSV5uQvgkcjKMZ0TvXdS2K"
)
ws = sh.get_worksheet(0)
ws.update_acell('A1', 'Hello World')

@app.route("/") #app.routeはエンドポイントを含めたブラウザを表示させると同時に直後の関数も実行する。関数でＨＴＭＬが設定されているとブラウザ上にＨＴＭＬが表示される
def index(): #トップ画面が表示される時に使われる関数
   return render_template(
       "title.html"
   )
 
@app.route("/form")  #<a href="{{ url_for('form') }}">このコードによってhttp://127.0.0.1:5000/formにアクセス白ってこと
def form():#http://127.0.0.1:5000/formにアクセスしたらform関数を実行しろってこと→つまりhttp://127.0.0.1:5000/formのブラウザにreport.htmlを表示させるってこと
    return render_template(
        "report.html"
    )
    
# @app.route("/spread")
# def spread():
#         # スプレッドシートに追加
#         ws.update_acell("A2","オッケー")
        
#         return render_template(
#             "title.html"
#             )


@app.route("/spread", methods=["GET", "POST"]) 
#POST:入力データを送る、GET:ページを開く POSTは送る側・貰う側両方設定必要。（GETは貰う側だけでOK)
def spread():
    if request.method == "POST":
        # フォームのデータを取得
        report_data = request.form["report"]
        
        # スプレッドシートに追加
        ws.update_acell("A1", report_data)
        
        return render_template("exit.html") # 送信後スプレッドシートへ飛ぶ HTMLファイルに飛ばしたいときはrender_template、URLに飛ばしたかったらredirect

    return render_template("report.html") #GETに対応。spread関数を実行するときにreport.htmlを開く
    
@app.route("/spread_link")
def spread_link():
    return redirect(spreadsheet_url)