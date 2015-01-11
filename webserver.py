# Millionaire Makers Drawing Platform
# https://www.reddit.com/r/millionairemakers
#
# Drawing backend web server
#
# Contact /u/minlite for comments/suggestions

from time import gmtime, strftime, sleep
import threading
import json
import hashlib
import sys

from flask import Flask, request, render_template, redirect, url_for
from flask.ext.basicauth import BasicAuth
import dropbox
from websocket import create_connection
from websocket._exceptions import WebSocketConnectionClosedException
import requests
import praw

import configuration

app = Flask(__name__)

app.config['BASIC_AUTH_USERNAME'] = configuration.BASIC_AUTH_USERNAME
app.config['BASIC_AUTH_PASSWORD'] = configuration.BASIC_AUTH_PASSWORD

basic_auth = BasicAuth(app)

sys.stdout = open(configuration.LOG_FILE_NAME, "w+", 0)


@app.route('/')
@basic_auth.required
def homepage():
    auth_link = r.get_authorize_url('UniqueKey',
                                    refreshable=True)
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

    auth_link = r.get_authorize_url('UniqueKey',
                                    refreshable=True)

    return render_template("checkusername.html", username=user.name, moderator=configuration.MODERATOR_USERNAME, auth_link=auth_link)


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

    if submission_id == '':
        return redirect(url_for('select_thread'))

    submission = r.get_submission(submission_id=submission_id)

    yes_link = url_for('start_drawing_process') + "?submission_id=" + submission_id
    no_link = url_for('select_thread')

    return render_template("confirmthread.html", username=user.name,
                           title=submission.title,
                           num_comments=submission.num_comments,
                           yes_link=yes_link,
                           no_link=no_link)


@app.route('/start_drawing_process')
@basic_auth.required
def start_drawing_process():
    user = r.get_me()

    if configuration.LIMIT_MODERATION:
        if user.name != configuration.MODERATOR_USERNAME:
            return redirect(url_for('homepage'))

    submission_id = request.args.get('submission_id', '')

    if submission_id == '':
        return redirect(url_for('select_thread'))
    # Start the drawing process
    drawing_thread = DrawingThread(submission_id)
    drawing_thread.start()

    return render_template("startdrawingprocess.html", username="")


@app.route('/public_log')
def public_log():
    return render_template("publiclog.html")


@app.route('/get_log')
@basic_auth.required
def get_log():
    return open(configuration.LOG_FILE_NAME, "r").read()


def chunksize(size, filename):
    f = open(filename, 'rb')
    done = 0
    while not done:
        chunk = f.read(size)
        if chunk:
            yield chunk
        else:
            done = 1
    f.close()
    return


def sha256(filename):
    h = hashlib.sha256()
    for chunk in chunksize(16384, filename):
        h.update(chunk)
    return h.hexdigest()


class DrawingThread(threading.Thread):
    def __init__(self, submission_id):
        super(DrawingThread, self).__init__()
        self.submission_id = submission_id

    def run(self):
        print "Getting comment ids..."

        print ""

        comment_ids = []

        while 1:
            response = requests.get("https://www.reddit.com/comments/" + self.submission_id + ".json?sort=old")
            thread = response.json()

            if type(thread) is list:
                break

            sleep(10)

        children = thread[1]['data']['children']

        for child in children:
            if child['data']['parent_id'] == "t3_" + self.submission_id:
                if child['kind'] == 't1':
                    comment_ids.append(child['data']['id'])

                elif child['kind'] == 'more':
                    # More comments
                    comment_ids[len(comment_ids):] = child['data']['children']

        f_comment_ids = open('comment_ids', 'w')

        for comment_id in comment_ids:
            f_comment_ids.write(comment_id + "\n")

        f_comment_ids.close()

        f_comment_ids = open('comment_ids', 'rb')

        client = dropbox.client.DropboxClient(configuration.DROPBOX_ACCESS_TOKEN)
        comment_ids_response = client.put_file('/comment_ids-' + strftime("%d-%b-%Y", gmtime()) + '.txt', f_comment_ids)

        comment_ids_link = client.share(comment_ids_response['path'], short_url=False)

        f_comment_ids.close()

        print "Participants: " + str(len(comment_ids))
        print ""

        print "Comment IDs: " + comment_ids_link['url'] + " Expires at: " + comment_ids_link['expires']

        print ""

        print "Comment IDs SHA-256: " + sha256('comment_ids')

        print ""

        print "Subscribing to the bitcoin blockchain..."

        print ""

        block_count = 0

        while block_count < configuration.WINNER_BLOCK:
            try:
                ws = create_connection("wss://ws.blockchain.info/inv")
                ws.send("{\"op\":\"blocks_sub\"}")
                print "Waiting for block #" + str(block_count + 1)
                block = ws.recv()
                blockj = json.loads(block)
                print "Block Found! Hash is: " + blockj['x']['hash']
                block_count += 1
                ws.close()
                print "Waiting 10 seconds for the block to settle..."
                sleep(10)
            except WebSocketConnectionClosedException:
                print "Connection Closed. Trying again..."

        height = blockj['x']['height']

        print ""

        print "Winner height is " + str(height)

        print ""

        if configuration.CONFIRMATION_BLOCKS != 0:
            print "Waiting for " + str(configuration.CONFIRMATION_BLOCKS) + " confirmations..."
            print ""

        block_count = 0

        while block_count < configuration.CONFIRMATION_BLOCKS:
            try:
                ws = create_connection("wss://ws.blockchain.info/inv")
                ws.send("{\"op\":\"blocks_sub\"}")
                print "Waiting for block #" + str(block_count + 1)
                block = ws.recv()
                blockj = json.loads(block)
                print "Block Found! Hash is: " + blockj['x']['hash']
                block_count += 1
                ws.close()
                print "Waiting 10 seconds for the block to settle..."
                sleep(10)
            except WebSocketConnectionClosedException:
                print "Connection Closed. Trying again..."

        if configuration.CONFIRMATION_BLOCKS != 0:
            print ""
            print "Confirmation completed..."
            print ""

        print "Retrieving height " + str(height)

        print ""

        blocks_with_height = requests.get("https://blockchain.info/block-height/" + str(height) + "?format=json").json()

        for block_with_height in blocks_with_height['blocks']:
            if block_with_height['main_chain']:
                blockj = block_with_height
                break

        final_hash = blockj['hash']

        print "Winning hash is: " + final_hash

        winner_index = 1 + (int(final_hash, 16) % len(comment_ids))
        winner_id = comment_ids[winner_index - 1]

        print "Participants: " + str(len(comment_ids))
        print "Winner index: " + str(winner_index)
        print "Winner comment id: " + str(winner_id)

        print ""

        while 1:
            comment = requests.get(
                "https://www.reddit.com/comments/" + self.submission_id + ".json?comment=" + winner_id).json()

            if type(comment) is list:
                break

            sleep(10)

        winner = comment[1]['data']['children'][0]['data']['author']

        print "Winner is: " + winner


if __name__ == '__main__':
    r = praw.Reddit(user_agent=configuration.REDDIT_USER_AGENT,
                    api_request_delay=configuration.REDDIT_API_REQUEST_DELAY)

    r.set_oauth_app_info(configuration.REDDIT_CLIENT_ID, configuration.REDDIT_CLIENT_SECRET,
                         configuration.REDDIT_REDIRECT_URI)
    app.run(debug=configuration.DEBUG, port=configuration.WEB_SERVER_PORT)
