# Copyright 2017-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from flask import render_template
from flask import Flask
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
csrf = CSRFProtect()
csrf.init_app(app)

@app.route('/')
def hello():
    return render_template('app.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0')
