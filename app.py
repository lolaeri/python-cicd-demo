"""A small Flask application used to demonstrate a CI/CD pipeline.

Endpoints:
    GET /            -> welcome message
    GET /health       -> health check used by the pipeline / load balancer
    GET /add/<a>/<b>  -> returns the sum of two integers
"""
from flask import Flask, jsonify

app = Flask(__name__)

APP_VERSION = "1.0.0"


@app.route("/")
def index():
    return jsonify(message="Hello, CI/CD!", version=APP_VERSION)


@app.route("/health")
def health():
    return jsonify(status="ok")


@app.route("/add/<int:a>/<int:b>")
def add(a, b):
    return jsonify(a=a, b=b, result=a + b)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
