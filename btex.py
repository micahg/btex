#!/usr/bin/env python3
"""Bittorrent Extractor module."""
import re
import os
import logging
from datetime import datetime
import smtplib
from shutil import copy2

LOG_FORMAT = '%(asctime)-15s [%(funcName)s] %(message)s'
DEST_PATH = '/srv/video/tv'
SRC_PATH = '/home/micah/torrents'
NAME_REGEX = '()'
TORRENT_MAP = {
    'the.voice': 'The Voice (US)',
    'the.walking.dead': 'Walking Dead',
    'startalk': 'StarTalk',
    'masterchef.us': 'MasterChef (US)',
    'stephen.colbert': "The Late Show with Stephen Colbert"
}

FILE_EXTENSIONS = ['mkv']

SHOW_RE = r'(.*)\.([sS]\d+[eE]\d+|\d{4}.\d{2}.\d{2})+\.*'

def send_email(subject, body):
    """Send an email with a subject and body."""
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.login('ezgzsys', 'ptkhimvkvvomqphe')
    server.sendmail('ezgzsys@gmail.com', 'micahgalizia@gmail.com',
                    f'Subject: {subject}\n{body}')
    server.quit()
    logging.info('EMail sent')


def copy_get_body(source, dest):
    """
    Copy mail body.
    @param source The source
    @param dest The destination
    """
    stats = os.stat(source)
    start_dt = datetime.now()
    copy2(source, dest)
    stop_dt = datetime.now()
    delta = stop_dt - start_dt
    logging.info('Stats "%s"', stats.st_size)
    logging.info('Delta "%s"', delta)
    body = f'successfully copied "{source}" to "{dest}"'
    body = f'{body}\n\nCopied {stats.st_size/1048576}MB in {delta}'
    logging.info(body)
    return body


def process_mkv(name, path, destination):
    """Process an MKV file."""
    mkv_file = f'{path}.mkv' if path[-4:].lower() != '.mkv' else path
    if not os.path.exists(mkv_file):
        logging.error('%s does not exist', mkv_file)
        return False

    body = copy_get_body(mkv_file, destination)
    send_email(f'{name} Copied', body)
    return True


def process_mkv_folder(name, path, destination):
    """Process an MKV folder."""
    if not os.path.isdir(path):
        logging.info('torrent path not dir "%s" "%s"', name, path)
        return False

    for _, _, files in os.walk(path):
        for filename in files:
            for ext in FILE_EXTENSIONS:
                if filename[-len(ext):] == ext:
                    full_filename = f'{path}/{filename}'
                    full_destination = f'{destination}/{filename}'
                    logging.info('copying "%s" to "%s"', full_filename, full_destination)
                    body = copy_get_body(full_filename, destination)
                    send_email(f'{name} Copied', body)
                    return True
    return False


def process_params(name, epno, path):
    """Process a torrent."""
    logging.info('*** STARTING "%s" ***', name)
    name = TORRENT_MAP[name] if name in TORRENT_MAP else name.replace('.', ' ').title()

    logging.info('name prefix is "%s"', name)
    destination = None
    for filename in os.listdir(DEST_PATH):
        if name.lower() != filename.lower():
            continue

        logging.info('"%s" == "%s"', name, filename)
        destination = f'{DEST_PATH}/{filename}'
        logging.info('Going with "%s"', destination)
        break

    if destination is None:
        err = f'Unable to find sufficient match in {DEST_PATH}'
        logging.error(err)
        send_email('FAILED Copying{name}', err)
        return

    if not os.path.isdir(destination):
        err = 'Destination not folder'
        logging.error(err)
        send_email(f'FAILED Copying {name}', err)
        return

    logging.info('doing deletions')
    for filename in os.listdir(destination):
        if epno in filename.lower():
            deletion = f'{destination}/{filename}'
            logging.info('Deleting %s', deletion)
            try:
                os.remove(deletion)
                logging.info('Successfully deleted %s', deletion)
                send_email(f'DELETED {name} {epno}', deletion)
            except (OSError, FileNotFoundError) as err:
                logging.error('Unable to delete %s: %s', deletion, err)
                send_email(f'FAILED DELETION {name} {epno}', deletion)

    result = process_mkv_folder(name, path, destination)
    if not result:
        logging.info('Process as file %s, %s, %s', name, path, destination)
        result = process_mkv(name, path, destination)

    if not result:
        send_email('FAILED Copying {name}', path)

    logging.info('*** DONE "%s" ***', name)


def get_show_name_and_episode_and_path(name):
    """Get a show name."""
    match = re.match(r'((.*)[\s\.](S\d+E\d+|\d{4}.\d{2}.\d{2}).*?)([\s\.]\[TD\])?.torrent', name)

    if match is None:
        err = f'ERROR: match is none for "{name}"'
        logging.error(err)
        send_email(f'FAILED Copying {name}', err)
        return

    if match.groups is None:
        err = f'ERROR: groups none for "{name}"'
        logging.error(err)
        send_email(f'FAILED Copying {name}', err)
        return

    if len(match.groups()) == 0:
        err = f'ERROR: Unmatched torrent (0) "{name}"'
        logging.error(err)
        send_email(f'FAILED Copying {name}', err)
        return

    # name, episode, path
    return match[2], match[3], match[1]

def process_complete_torrents():
    """Process every torrent file in the finished location."""
    for filename in os.listdir(f'{SRC_PATH}/finished'):
        logging.info('FILENAME is "%s"', filename)
        splitnames = os.path.splitext(filename)
        logging.info('SPLIT IS "%s"', splitnames)
        if splitnames[1] == '.torrent':
            # logging.info('MICAH LOOK HERE WHEN IT BREAKS - SPLITTING BASE BY SPACE BECAUSE OF " [TD]" SUFFIX')
            name, episode, path = get_show_name_and_episode_and_path(filename)
            logging.info('NAME IS "%s"', name)
            logging.info('EPISODE IS "%s"', episode)
            logging.info('PATH IS "%s"', path)
            process_params(name, episode, f'{SRC_PATH}/{path}')
            os.remove(f'{SRC_PATH}/finished/{filename}')


def main():
    """
    Run the main program
    """
    logging.basicConfig(format=LOG_FORMAT, level=logging.INFO,
                        filename='/var/log/btex.log')

    process_complete_torrents()


if __name__ == '__main__':
    main()
