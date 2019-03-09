from flask import Flask,abort,render_template,request,redirect,url_for
from werkzeug import secure_filename
from runner import runner
import os
import json
from flask import jsonify
app = Flask(__name__)
UPLOAD_FOLDER = './uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route("/")
def hello():
    return "Hello World!"


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            print(file)
            filename = secure_filename(file.filename)
            # print(filename)
            # file_data = file.read()
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return jsonify(runner(file.filename))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4040, debug= True)
