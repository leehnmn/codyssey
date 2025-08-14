from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("menu.html")

@app.route("/menu")
def menu():
    return render_template("menu.html")

@app.route("/test2")
def test2():
    return render_template('test2.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
