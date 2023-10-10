from flask import Flask
import subprocess

app = Flask(__name__)


@app.route("/")
def check_status():
    try:
        res = subprocess.run(
            ["/home/dani/work/toggle_router/toggle.py", "-c"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return f'<h2>{res.stdout.decode("utf-8")}</h2><br><br><br><a href="/toggle">Toggle</a>'
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"


@app.route("/toggle")
def toggle():
    try:
        res = subprocess.run(
            ["/home/dani/work/toggle_router/toggle.py"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return f'<h2>{res.stdout.decode("utf-8")}</h2><br><br><br><a href="/">Home</a>'
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"

