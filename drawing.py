from time import sleep, strftime, gmtime
import threading
import hashlib

from flask import json
import requests
import dropbox
from websocket import create_connection, WebSocketConnectionClosedException

import configuration


def chunk_size(size, filename):
    with open(filename, 'rb') as f:
        done = 0
        while not done:
            chunk = f.read(size)
            if chunk:
                yield chunk
            else:
                done = 1
    return


def sha256(filename):
    h = hashlib.sha256()
    for chunk in chunk_size(16384, filename):
        h.update(chunk)
    return h.hexdigest()


def find_block(total_count):
    block_count = 0
    while True:
        try:
            ws = create_connection("wss://ws.blockchain.info/inv")
            try:
                ws.send("{\"op\":\"blocks_sub\"}")
                print "Waiting for block #" + str(block_count + 1)
                block = ws.recv()
                block_json = json.loads(block)
                print "Block Found! Hash is: " + block_json['x']['hash']
                block_count += 1
                print "Waiting 10 seconds for the block to settle..."
                sleep(10)
                if block_count == total_count:
                    return block_json
            except WebSocketConnectionClosedException:
                print "Connection Closed. Trying again..."
        finally:
            ws.close()


class DrawingThread(threading.Thread):
    def __init__(self, submission_id):
        super(DrawingThread, self).__init__()
        self.submission_id = submission_id

    def run(self):
        print "Getting comment ids...\n"

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

        with open('comment_ids', 'w') as f_comment_ids:
            for comment_id in comment_ids:
                f_comment_ids.write(comment_id + "\n")

        with open('comment_ids', 'rb') as f_comment_ids:
            client = dropbox.client.DropboxClient(configuration.DROPBOX_ACCESS_TOKEN)
            comment_ids_response = client.put_file('/comment_ids-' + strftime("%d-%b-%Y", gmtime()) + '.txt',
                                                   f_comment_ids)
            comment_ids_link = client.share(comment_ids_response['path'], short_url=False)

        print "Participants: " + str(len(comment_ids)) + "\n"
        print "Comment IDs: " + comment_ids_link['url'] + " Expires at: " + comment_ids_link['expires'] + "\n"
        print "Comment IDs SHA-256: " + sha256('comment_ids') + "\n"
        print "Subscribing to the bitcoin blockchain...\n"

        block_json = find_block(configuration.WINNER_BLOCK)
        height = block_json['x']['height']
        print "Winner height is " + str(height) + "\n"

        if configuration.CONFIRMATION_BLOCKS != 0:
            print "Waiting for " + str(configuration.CONFIRMATION_BLOCKS) + " confirmations..."
            find_block(configuration.CONFIRMATION_BLOCKS)
            print "Confirmation completed.\n"

        print "Retrieving height " + str(height) + "\n"
        blocks_with_height = requests.get("https://blockchain.info/block-height/" + str(height) + "?format=json").json()
        block_json = next(block for block in blocks_with_height['blocks'] if block['main_chain'])
        final_hash = block_json['hash']
        print "Winning hash is: " + final_hash

        winner_index = 1 + (int(final_hash, 16) % len(comment_ids))
        winner_id = comment_ids[winner_index - 1]
        print "Participants: " + str(len(comment_ids))
        print "Winner index: " + str(winner_index)
        print "Winner comment id: " + str(winner_id) + "\n"

        while True:
            comment = requests.get(
                "https://www.reddit.com/comments/" + self.submission_id + ".json?comment=" + winner_id).json()
            if type(comment) is list:
                break
            sleep(10)

        winner = comment[1]['data']['children'][0]['data']['author']
        print "Winner is: " + winner
