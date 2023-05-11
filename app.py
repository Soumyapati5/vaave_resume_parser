from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from new import resume_parser

from flask import Flask,render_template, request
from flask_mysqldb import MySQL
 
app = Flask(__name__)
 
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'flask'
 
mysql = MySQL(app)


@app.route('/')
@app.route('/home')
def home():
   return 'Hii from my web'


@app.route('/upload')
def upload_file():
   return render_template('upload.html')
	
@app.route('/uploader', methods = ['POST'])
def upload_and_extract_data():
   if request.method == 'POST':
      f = request.files['file']
      filename = secure_filename(f.filename)
      f.save(filename)
      data = resume_parser(filename)
      return data

@app.route('/upload_multiple_file')
def upload_multi_file():
   return render_template('index.html')

@app.route('/upload_multiple', methods=['POST'])
def upload_and_extract_multiple():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return 'No file part'
        
        # get list of files from request
        files = request.files.getlist('file')

        # initialize list to store parsed data
        all_data = []
        
        # loop through files and save each one
        for f in files:
            filename = secure_filename(f.filename)
            f.save(filename)
            data = resume_parser(filename)
            all_data.append(data)

        # return parsed data as JSON
        return (all_data)



if __name__ == '__main__':
   app.run(debug = True)
