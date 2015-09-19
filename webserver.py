# Millionaire Makers Drawing Platform
# https://www.reddit.com/r/millionairemakers
#
# Drawing backend web server
#
# Contact /u/minlite for comments/suggestions
import sys
import time

from flask import Flask, request, render_template, redirect, url_for
from flask.ext.basicauth import BasicAuth
from drawing import DrawingThread

import praw
import configuration


app = Flask(__name__)

app.config['BASIC_AUTH_USERNAME'] = configuration.BASIC_AUTH_USERNAME
app.config['BASIC_AUTH_PASSWORD'] = configuration.BASIC_AUTH_PASSWORD

basic_auth = BasicAuth(app)

sys.stdout = open(configuration.LOG_FILE_NAME, "w+", 0)

log = ""
last_read = 0

# Holds a reference to the drawing thread so it won't be executed twice accidentally
drawing_thread = False

@app.route('/')
@basic_auth.required
def homepage():
    auth_link = r.get_authorize_url('uniqueKey', 'identity history', False)
    return render_template("homepage.html", auth_link=auth_link)


@app.route('/authorize_callback')
@basic_auth.required
def check_username():
    state = request.args.get('state', '')
    code = request.args.get('code', '')
    info = r.get_access_information(code)
    user = r.get_me()

    if not configuration.LIMIT_MODERATION or user.name == configuration.MODERATOR_USERNAME:
        return redirect(url_for('select_thread'))

    auth_link = r.get_authorize_url('uniqueKey', 'identity history', False)

    return render_template("checkusername.html", username=user.name, moderator=configuration.MODERATOR_USERNAME,
                           auth_link=auth_link)


@app.route('/select_thread')
@basic_auth.required
def select_thread():
    user = r.get_me()

    if configuration.LIMIT_MODERATION:
        if user.name != configuration.MODERATOR_USERNAME:
            return redirect(url_for('homepage'))

    submissions = user.get_submitted(limit=None)
    action = url_for('confirm_thread')

    return render_template("selectthread.html", username=user.name, submissions=submissions, action=action)


@app.route('/confirm_thread')
@basic_auth.required
def confirm_thread():
    user = r.get_me()

    if configuration.LIMIT_MODERATION:
        if user.name != configuration.MODERATOR_USERNAME:
            return redirect(url_for('homepage'))

    submission_id = request.args.get('submission_id', '')
    cutoff_comment_id = request.args.get('cutoff_comment_id', '')

    if submission_id == '':
        return redirect(url_for('select_thread'))

    submission = r.get_submission(submission_id=submission_id)

    yes_link = url_for('start_drawing_process') + "?submission_id=" + submission_id + "&cutoff_comment_id=" + cutoff_comment_id
    no_link = url_for('select_thread')

    return render_template("confirmthread.html", username=user.name,
                           title=submission.title,
                           num_comments=submission.num_comments,
                           yes_link=yes_link,
                           no_link=no_link)


@app.route('/start_drawing_process')
@basic_auth.required
def start_drawing_process():
    global drawing_thread

    user = r.get_me()

    if configuration.LIMIT_MODERATION:
        if user.name != configuration.MODERATOR_USERNAME:
            return redirect(url_for('homepage'))

    submission_id = request.args.get('submission_id', '')
    cutoff_comment_id = request.args.get('cutoff_comment_id', '')

    if submission_id == '':
        return redirect(url_for('select_thread'))

    # Check if the drawing thread has not been started yet
    if not drawing_thread:
        # Start the drawing process
        drawing_thread = DrawingThread(submission_id=submission_id, cutoff_comment_id=cutoff_comment_id)
        drawing_thread.start()

    return render_template("startdrawingprocess.html", username=user.name)


@app.route('/public_log')
@basic_auth.required
def public_log():
    return render_template("immediatelog.html", log=get_immediate_log())


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


@app.route('/get_immediate_log')
@basic_auth.required
def get_immediate_log():
    global log
    with open(configuration.LOG_FILE_NAME, "r") as f:
        log = f.read()
        return log



if __name__ == '__main__':
    r = praw.Reddit(user_agent=configuration.REDDIT_USER_AGENT,
                    api_request_delay=configuration.REDDIT_API_REQUEST_DELAY)

    r.set_oauth_app_info(configuration.REDDIT_CLIENT_ID, configuration.REDDIT_CLIENT_SECRET,
                         configuration.REDDIT_REDIRECT_URI)

    app.run(debug=configuration.DEBUG, host=configuration.WEB_SERVER_HOST, port=configuration.WEB_SERVER_PORT)
