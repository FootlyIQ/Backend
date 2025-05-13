from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app) #ZAENKRAT DOVOLIMO ALL ORIGINS - PRED PRODUKCIJO POPRAVIT


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'

@app.route("/test", methods=['GET'])
def test_be():
    return "Backend deluje"


if __name__ == '__main__':
    app.run()
