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


def send_email(subject, body):
    """Send an email with a subject and body."""
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.login('ezgzsys', 'ptkhimvkvvomqphe')
    server.sendmail('ezgzsys@gmail.com', 'micahgalizia@gmail.com',
                    'Subject: {}\n{}'.format(subject, body))
    server.quit()
    logging.info('EMail sent')


def copy_get_body(source, dest):
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
        logging.info(f'torrent path not dir "{name}" "{path}"')
        return False

    for root, dirs, files in os.walk(path):
        for filename in files:
            for ext in FILE_EXTENSIONS:
                if filename[-len(ext):] == ext:
                    full_filename = '{}/{}'.format(path, filename)
                    full_destination = '{}/{}'.format(destination, filename)
                    logging.info(f'copying "{full_filename}" to "{full_destination}"')
                    body = copy_get_body(full_filename, destination)
                    send_email('{} Copied'.format(name), body)
                    return True
    return False


def process_params(name, path):
    """Process a torrent."""
    logging.info('*** STARTING "%s" ***', name)
    logging.info('torrent path is "%s"', path)
    logging.info('torrent name is "%s"', name)

    match = re.match(r'(.*)\.([sS]\d+[eE]\d|\d{4}.\d{2}.\d{2})+\.*', name)

    if match is None:
        err = 'ERROR: match is none for "{}"'.format(name)
        logging.error(err)
        send_email('FAILED Copying {}'.format(name), err)
        return

    if match.groups is None:
        err = 'ERROR: groups none for "{}"'.format(name)
        logging.error(err)
        send_email('FAILED Copying {}'.format(name), err)
        return

    if len(match.groups()) == 0:
        err = 'ERROR: Unmatched torrent (0) "{}"'.format(name)
        logging.error(err)
        send_email('FAILED Copying {}'.format(name), err)
        return

    name = match[1].lower()
    logging.info('name is "%s"', name)
    name = TORRENT_MAP[name] if name in TORRENT_MAP.keys() else name.replace('.', ' ').title()

    logging.info('name prefix is "%s"', name)
    destination = None
    for filename in os.listdir(DEST_PATH):
        if name.lower() != filename.lower():
            continue

        logging.info('"%s" == "%s"', name, filename)
        destination = '{}/{}'.format(DEST_PATH, filename)
        logging.info('Going with "%s"', destination)
        break

    if destination is None:
        err = 'Unable to find sufficient match in {}'.format(DEST_PATH)
        logging.error(err)
        send_email('FAILED Copying{}'.format(name), err)
        return

    if not os.path.isdir(destination):
        err = 'Destination not folder'
        logging.error(err)
        send_email('FAILED Copying {}'.format(name), err)
        return

    result = process_mkv_folder(name, path, destination)
    if not result:
        logging.info('Process as file %s, %s, %s', name, path, destination)
        result = process_mkv(name, path, destination)

    if not result:
        send_email('FAILED Copying {}'.format(name), path)

    logging.info('*** DONE "%s" ***', name)


def process_complete_torrents():
    """Process every torrent file in the finished location."""
    for filename in os.listdir('{}/finished'.format(SRC_PATH)):
        logging.info('FILENAME is "%s"', filename)
        splitnames = os.path.splitext(filename)
        logging.info('SPLIT IS "%s"', splitnames)
        if splitnames[1] == '.torrent':
            base = splitnames[0]
            logging.info('MICAH LOOK HERE WHEN IT BREAKS - SPLITTING BASE BY SPACE BECAUSE OF " [TD]" SUFFIX')
            logging.info('BASE WAS "%s"', base)
            base = base.split()[0]
            logging.info('BASE IS "%s"', base)
            process_params(base, f'{SRC_PATH}/{base}')
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
