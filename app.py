from flask import Flask

app = Flask(__name__)


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'

@app.route("/test", methods=['GET'])
def test_be():
    return "Backend deluje"


if __name__ == '__main__':
    app.run()
