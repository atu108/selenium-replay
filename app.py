from flask import Flask,abort,render_template,request,redirect,url_for
from werkzeug import secure_filename
from runner import runner
import os
import json
from flask import jsonify
from gevent.pywsgi import WSGIServer
app = Flask(__name__)
UPLOAD_FOLDER = './uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route("/")
def hello():
    return "Hello World!"


@app.route('/generatehar', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        try:
            file = request.files['file']
        except:
            file = None
        if file:
            filename = secure_filename(file.filename)
            # print(filename)
            file_data = json.loads(file.read())
            url = file_data['url'] + file_data['tests'][0]['commands'][0]['target']
            # file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return jsonify(runner(file_data, filename, url))
        else:
            form_data = request.json
            filename = form_data["filename"]
            commands = form_data["data"]
            url = form_data["url"]
            return jsonify(runner(commands, filename, url, form_data["saveDropdown"]))

if __name__ == '__main__':
    http_server = WSGIServer(('0.0.0.0', 4040), app)
    http_server.serve_forever()