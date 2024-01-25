#!/bin/python

import json
import collections
from datetime import datetime
import argparse

def analyze(group_bot_id, logfilename, start_date, end_date, top):
    with open(logfilename) as res:
        chat = json.loads(res.read())

    users_msgs = {}
    banned_users = set()
    invited_users = []
    approved_users = []
    channel_messages = 0
    user_messages = 0
    first_user_massage_date = ""
    last_user_massage_date = ""

    since_msg = till_msg = ""
    if start_date != "":
        start_time = datetime.strptime(start_date, "%Y-%m-%d").timestamp()
        since_msg = f' since {start_date}'

    if end_date != "":
        end_time = datetime.strptime(end_date, "%Y-%m-%d").timestamp()
        till_msg = f' till {end_date}'

    print(chat['name'])
    if not group_bot_id:
        print("=== WARNING! No group_bot_id given (-i key), results may be inconsistent! ===")

    for msg in chat['messages']:
        if start_date != "" and int(msg['date_unixtime']) < start_time:
            continue
        if end_date != "" and int(msg['date_unixtime']) > end_time:
            continue
        if msg['type'] == 'service':
            if msg['action'] == 'invite_members':
                invited_users.append(msg['actor'] if msg['actor'] else f"Deleted Account: {msg['actor_id']}")
            continue
        msg_id = msg.get('from_id', False)
        if not msg_id:
            continue


        if msg['from_id'].startswith('channel'):
            channel_messages += 1
            continue

        #bot messages handling (highly depends on the message structure)
        if group_bot_id and msg['from_id'] == group_bot_id:
            if msg['text'][0] == 'Hi ' and msg['text'][1]['type'] == 'mention':
                approved_users.append(msg['text'][1]['text'])
            elif len(msg['text'])>1 and msg['text'][1] == ' banned ':
                banned_users.add(msg['text'][2]['text'])
            continue

        if first_user_massage_date == "":
            first_user_massage_date = datetime.utcfromtimestamp(int(msg['date_unixtime'])).strftime('%Y-%m-%d %H:%M:%S')
        user_messages += 1
        if not msg['from']:
            name = f"Deleted Account: {msg['from_id']}"
        else:
            name = msg['from']

        if msg['from_id'] in users_msgs:
            users_msgs[msg['from_id']]['cnt'] += 1
            users_msgs[msg['from_id']]['names'].add(name)
        else:
            users_msgs[msg['from_id']] = {
                'cnt': 1,
                'names': {name}
            }
        last_user_massage_date = datetime.utcfromtimestamp(int(msg['date_unixtime'])).strftime('%Y-%m-%d %H:%M:%S')

    stat = collections.OrderedDict(sorted(users_msgs.items(), key=lambda t:t[1]["cnt"], reverse = True))

    print(f'first user message in the log (UTC): {first_user_massage_date}')
    print(f'last user message in the log (UTC): {last_user_massage_date}')
    print(f'channel messages: {channel_messages}')
    print(f'user messages: {user_messages}')
    print(f'unique users: {len(users_msgs)}')

    print(f'\n-- Message count per user{since_msg}{till_msg}: --')
    place = 1
    for el in stat:
        print(f"{place}: {' aka '.join(stat[el]['names'])}: {stat[el]['cnt']} ({round(stat[el]['cnt']/user_messages*100,2)}%){' - BANNED' if len(stat[el]['names'].intersection(banned_users)) > 0 else ''}")
        place += 1
        if top and place > top:
            break

    print('\n-- Other stats --')
    print(f'invited users (according to service messages): {len(invited_users)}:\n{invited_users if len(invited_users) > 0 else ""}')
    print(f'\napproved users (according to bot): {len(approved_users)}:\n{approved_users if len(approved_users) > 0 else ""}')
    print(f'\nbanned users (by /ban command): {len(banned_users)}:\n{banned_users if len(banned_users) > 0 else ""}')


def check_positive(value):
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError("%s is an invalid positive int value" % value)
    return ivalue

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Telegram chat log analyzer')
    parser.add_argument(
        '-i',
        metavar='user12345',
        help='Chat guardian-bot id, to search ban/welcome messages for, will not destinguish bot messages from others if absent!',
        default=None)
    parser.add_argument(
        '-f',
        metavar='result.json',
        help='Log file. Default is "result.json" in a current directory',
        default="result.json")
    parser.add_argument(
        '-s',
        metavar='YYYY-MM-DD',
        help='Stat date in YYYY-MM-DD format.',
        default="")
    parser.add_argument(
        '-e',
        metavar='YYYY-MM-DD',
        help='End date in YYYY-MM-DD format.',
        default="")
    parser.add_argument(
        '-t',
        metavar='9999',
        help='Show only top N of users',
        default=None,
        type=check_positive)
    args = parser.parse_args()

    analyze(args.i, args.f, args.s, args.e, args.t)
