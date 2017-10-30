# -*- coding: utf-8 -*-
import requests
import logging
import os
import json

logging.basicConfig(filename='nanopool.log', level=logging.DEBUG)

TOKEN = None
# токен вашего бота, полученный от @BotFather
with open('.token') as token_file:
    TOKEN = token_file.read()


# commands
# add - Add a new worker
# address - Set your ETH wallet address
# worker - Set your worker
# hashrate - Minimal hashrate to notify

class NanopoolCheck:
    commands = ['/add', '/address', '/worker', '/hashrate']

    def __init__(self, token):
        self.token = token
        self.api_url = "https://api.telegram.org/bot{}/".format(token)

    def get_updates(self, offset=None, timeout=2):
        method = 'getUpdates'
        params = {'timeout': timeout, 'offset': offset}
        resp = requests.get(self.api_url + method, params)
        result_json = resp.json()['result']
        return result_json

    def send_message(self, chat_id, text, force_reply=False):
        params = {
            'chat_id': chat_id,
            'text': text,
            'reply_markup': json.dumps({'force_reply': force_reply})
        }

        method = 'sendMessage'
        resp = requests.post(self.api_url + method, params)
        result_json = resp.json()['result']
        return result_json

    def get_last_update(self):
        get_result = self.get_updates()
        return get_result[-1] if len(get_result) > 0 else None

    def get_boot_command(self, message):
        if 'entities' not in message:
            return
        for entity in message['entities']:
            if entity['type'] == 'bot_command':
                return message['text'][entity['offset']:entity['offset'] + entity['length']]

    def mkdir_user(self, user_dir):
        if not os.path.isdir(user_dir):
            os.mkdir(user_dir)


def main():
    nanopool_bot = NanopoolCheck(TOKEN)
    new_offset = None
    data = {}
    wait = {}

    while True:
        nanopool_bot.get_updates(new_offset)

        last_update = nanopool_bot.get_last_update()

        if not last_update:
            continue

        last_update_id = last_update['update_id']
        message = last_update['message']
        last_chat_id = message['chat']['id']

        user_id = message['from']['id']
        user_dir = os.path.join('data', str(user_id))
        user_data = os.path.join('data', str(user_id), 'settings.json')

        if user_id not in data:
            data[user_id] = {}

        if os.path.exists(user_data):
            with open(user_data) as data_file:
                data[user_id] = json.load(data_file)

        if 'reply_to_message' in message:
            for cmd in nanopool_bot.commands:
                if cmd not in wait:
                    continue
                if message['reply_to_message']['message_id'] == wait[cmd]:
                    data[user_id].update({cmd: message['text'].strip()})

        msg = None
        force_reply = False
        if '/worker' in data[user_id] and '/address' in data[user_id]:
            nanopool_bot.mkdir_user(user_dir)
            with open(user_data, 'w') as data_file:
                json.dump(data[user_id], data_file)
                msg = "Your ETH address and worker have been saved!\n" + \
                      "If you want to set minimal hashrate to notify, use the command /hashrate"
        else:
            bot_command = nanopool_bot.get_boot_command(message)
            if bot_command is None:
                if '/address' not in data[user_id]:
                    bot_command = '/address'
                elif '/worker' not in data[user_id]:
                    bot_command = '/worker'
            if bot_command == '/start':
                msg = "Hello! Let's add your nanopool worker to watch! Use /add command"
            elif bot_command == '/add':
                msg = """Ok! Now send me your NanoPool ETH /address and /worker using the appropriate commands."""
            elif bot_command == '/address':
                msg = """Your ETH address:"""
                force_reply = True
            elif bot_command == '/worker':
                msg = """Your worker name:"""
                force_reply = True

        if msg:
            result = nanopool_bot.send_message(last_chat_id, msg, force_reply=force_reply)
            if bot_command and force_reply:
                wait[bot_command] = result['message_id']

        new_offset = last_update_id + 1


if __name__ == '__main__':
    try:
        print('Start bot!')
        main()
    except KeyboardInterrupt:
        print('Stop bot!')
        exit()
