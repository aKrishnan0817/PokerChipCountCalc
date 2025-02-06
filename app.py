from flask import Flask, request, redirect, url_for, send_file, render_template, jsonify

from blueprints.poker import poker
from blueprints.page_splitter import page_splitter
from blueprints.line_memorizer import line_memorizer

app = Flask(__name__)
app.register_blueprint(poker)
app.register_blueprint(page_splitter)
app.register_blueprint(line_memorizer)

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)