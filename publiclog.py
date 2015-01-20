# Millionaire Makers Drawing Platform
# https://www.reddit.com/r/millionairemakers
#
# Drawing public log server
#
# Contact /u/minlite for comments/suggestions
import time

from flask import Flask, render_template
import configuration


app = Flask(__name__)

log = ""
last_read = 0

@app.route('/')
def public_log():
    return render_template("publiclog.html", log=get_log())


@app.route('/get_log')
def get_log():
    global last_read
    global log
    if (time.time() - last_read) > configuration.LOG_CACHE_LIFETIME:
        last_read = time.time()
        with open(configuration.LOG_FILE_NAME, "r") as f:
            log = f.read()
            return log
    else:
        return log


if __name__ == '__main__':
    app.run(debug=configuration.DEBUG, host="0.0.0.0", port=80)
