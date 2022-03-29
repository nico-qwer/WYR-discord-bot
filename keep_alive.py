from flask import Flask
from waitress import serve
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Server still alive!"

def run():
    serve(app, host="0.0.0.0", port=8080)
    
def keep_alive():
    t = Thread(target=run)
    print("Server started")
    t.start()