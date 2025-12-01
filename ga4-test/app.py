import os
from flask import Flask, render_template

# Optional: load env vars from .env if you want
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

GA_MEASUREMENT_ID = os.getenv("GA_MEASUREMENT_ID", "G-XXXXXXX")

app = Flask(__name__)


@app.route("/")
def index():
    # Pass the measurement ID into the template
    return render_template("index.html", ga_measurement_id=GA_MEASUREMENT_ID)


if __name__ == "__main__":
    # Run on http://localhost:5000
    app.run(host="127.0.0.1", port=5000, debug=True)
