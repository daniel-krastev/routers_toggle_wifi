from flask import Flask
import subprocess

app = Flask(__name__)

html_template = """<html>
<head>
<style>
.button {{
    background-color: #4CAF50; /* Green */
    border: none;
    color: white;
    padding: 30px 60px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    font-size: 100px;
    margin: 4px 2px;
    cursor: pointer;
    }}
h1 {{
    color: blue;
    font-size: 4.5rem;
    line-height: 4.5rem;
    }}
h2 {{
    color: red;
    font-size: 2.8rem;
    line-height: 2.8rem;
    }}
</style>
</head>
<body>
<center>
<a href="/status"><button class="button">Check Status</button></a>
<a href="/toggle"><button class="button">Toggle</button></a>
<br><br><br>
<h1>{title}</h1>
<h2>{status}</h2>
</center>
</body>
</html>"""


@app.route("/")
def home():
    return html_template.format(title="", status="")


@app.route("/status")
def check_status():
    try:
        res = subprocess.run(
            ["/home/dani/work/toggle_router/toggle.py", "-c"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        status_line = res.stdout.decode("utf-8").split("\n")[-2]

        router_status = status_line.split(";")[0].split(":")[1].strip()
        extension_status = status_line.split(";")[1].strip()

        return html_template.format(
            title="Current Status:",
            status=f"{router_status.capitalize()}.<br>{extension_status.capitalize()}.",
        )
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"


@app.route("/toggle")
def toggle():
    try:
        subprocess.run(
            ["/home/dani/work/toggle_router/toggle.py"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        return html_template.format(title="Wifi Toggled", status="&#128077;")
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"
