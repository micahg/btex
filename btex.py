#!/usr/bin/env python3
"""Bittorrent Extractor module."""
import re
import os
import logging
from datetime import datetime
import smtplib
from shutil import copy2
import asyncio
from asyncinotify import Inotify, Mask

LOG_FORMAT = '%(asctime)-15s [%(funcName)s] %(message)s'
DEST_PATH = os.getenv('DEST_PATH', '/srv')
SRC_PATH = os.getenv('SRC_PATH', '/src')
FINISHED_PATH = os.getenv('FINISHED_PATH', f'{SRC_PATH}/finished')

# Email configuration from environment variables
SMTP_HOST = os.getenv('SMTP_HOST', '')
SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
EMAIL_SENDER = os.getenv('EMAIL_SENDER', '')
EMAIL_RECIPIENT = os.getenv('EMAIL_RECIPIENT', '')

NAME_REGEX = '()'
TORRENT_MAP = {
    'stephen colbert': "The Late Show with Stephen Colbert"
}

FILE_EXTENSIONS = ['mkv']

SHOW_RE = r'(.*)\.([sS]\d+[eE]\d+|\d{4}.\d{2}.\d{2})+\.*'

def validate_email_config():
    """Validate email configuration from environment variables."""
    if not SMTP_USERNAME:
        logging.error('No SMTP_USERNAME environment variable set')
        return False
    elif not SMTP_PASSWORD:
        logging.error('No SMTP_PASSWORD environment variable set')
        return False
    elif not EMAIL_SENDER:
        logging.error('No EMAIL_SENDER environment variable set')
        return False
    elif not EMAIL_RECIPIENT:
        logging.error('No EMAIL_RECIPIENT environment variable set')
        return False
    elif not SMTP_HOST:
        logging.error('No SMTP_HOST environment variable set')
        return False
    return True


def send_email(subject, body):
    """Send an email with a subject and body."""
    if not validate_email_config():
        logging.warning('Email not configured - skipping email notification: %s', subject)
        return

    try:
        server = smtplib.SMTP(SMTP_HOST, 587)
        server.ehlo()
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT,
                        f'Subject: {subject}\n{body}')
        server.quit()
        logging.info('Email sent: %s', subject)
    except Exception as err:
        logging.error('Unable to send email: %s', err)
        # Don't exit - continue processing even if email fails


def find_target_file_in_folder(path, extensions):
    """
    Find a target file in a folder.
    @param path The path to search
    @param extensions The file extensions to search for
    """
    for _, _, files in os.walk(path):
        for filename in files:
            for ext in extensions:
                if filename[-len(ext):] == ext:
                    return filename

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
    size_mb = stats.st_size / 1048576
    seconds = delta.total_seconds()
    mb_per_sec = size_mb / seconds if seconds > 0 else 0
    logging.info('Stats "%s"', stats.st_size)
    logging.info('Delta "%s"', delta)
    logging.info('Speed: %.2f MB/s', mb_per_sec)
    body = f'successfully copied "{source}" to "{dest}"'
    body = f'{body}\n\nCopied {size_mb:.2f}MB in {delta} ({mb_per_sec:.2f} MB/s)'
    logging.info(body)
    return body

def unrar_get_body(source, dest):
    """
    Extract archive and return mail body.
    @param source The source
    @param dest The destination
    """
    stats = os.stat(source)
    start_dt = datetime.now()
    os.system(f'7z e "{source}" -o"{dest}" -y')
    stop_dt = datetime.now()
    delta = stop_dt - start_dt
    size_mb = stats.st_size / 1048576
    seconds = delta.total_seconds()
    mb_per_sec = size_mb / seconds if seconds > 0 else 0
    logging.info('Stats "%s"', stats.st_size)
    logging.info('Delta "%s"', delta)
    logging.info('Speed: %.2f MB/s', mb_per_sec)
    body = f'successfully extracted "{source}" to "{dest}"'
    body = f'{body}\n\nExtracted {size_mb:.2f}MB in {delta} ({mb_per_sec:.2f} MB/s)'
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

    filename = find_target_file_in_folder(path, FILE_EXTENSIONS)
    if filename is None:
        return False


    full_filename = f'{path}/{filename}'
    full_destination = f'{destination}/{filename}'
    logging.info('copying "%s" to "%s"', full_filename, full_destination)
    body = copy_get_body(full_filename, destination)
    send_email(f'{name} Copied', body)
    return True

def process_rar(name, path, destination):
    """Process a RAR file."""
    if not os.path.isdir(path):
        logging.info('torrent path not dir "%s" "%s"', name, path)
        return False

    filename = find_target_file_in_folder(path, ['.rar'])
    if filename is None:
        return False

    body = unrar_get_body(f'{path}/{filename}', destination)
    send_email(f'{name} extracted', body)
    return True

def process_params(name, epno, path):
    """Process a torrent."""
    logging.info('*** STARTING "%s" ***', name)
    name = name.replace('.', ' ').lower()
    name = TORRENT_MAP[name] if name in TORRENT_MAP else name.title()

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
        send_email('FAILED Copying "{name}"', err)
        return

    if not os.path.isdir(destination):
        err = 'Destination not folder'
        logging.error(err)
        send_email(f'FAILED Copying "{name}"', err)
        return

    logging.info(f'deleting "{name}" {epno} from {destination}')
    for filename in os.listdir(destination):
        if epno.lower() in filename.lower():
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
        logging.info('Process as rar %s, %s, %s', name, path, destination)
        result = process_rar(name, path, destination)

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

# Async queue and condition for coordinating file watching and processing
torrent_queue = asyncio.Queue()
queue_condition = asyncio.Condition()


async def watch_complete_torrents():
    """Watch FINISHED_PATH for new torrent files and add them to the queue."""
    logging.info('Starting file watcher on: %s', FINISHED_PATH)
    
    # Ensure FINISHED_PATH exists
    os.makedirs(FINISHED_PATH, exist_ok=True)
    
    # Process any existing torrent files on startup
    try:
        for filename in os.listdir(FINISHED_PATH):
            if filename.endswith('.torrent'):
                logging.info('Found existing torrent file: %s', filename)
                async with queue_condition:
                    await torrent_queue.put(filename)
                    queue_condition.notify()
    except Exception as e:
        logging.error('Error processing existing files: %s', e)
    
    # Set up inotify to watch for new files
    inotify = Inotify()
    inotify.add_watch(FINISHED_PATH, Mask.CREATE)
    logging.info('File watcher started, monitoring for new .torrent files')
    
    try:
        async for event in inotify:
            # Only process .torrent files
            if event.name and str(event.name).endswith('.torrent'):
                filename = str(event.name)
                logging.info('Detected new torrent file: %s', filename)
                async with queue_condition:
                    await torrent_queue.put(filename)
                    logging.info('Added to queue: %s (queue size: %d)', 
                                filename, torrent_queue.qsize())
                    queue_condition.notify()
    finally:
        inotify.close()


async def process_complete_torrents():
    """Process torrent files from the queue one at a time."""
    logging.info('Starting torrent processor')
    
    while True:
        # Wait for a torrent to be available in the queue
        async with queue_condition:
            await queue_condition.wait_for(lambda: not torrent_queue.empty())
            filename = await torrent_queue.get()
        
        logging.info('Processing torrent from queue: %s', filename)
        
        try:
            # Check if file still exists (it might have been processed already)
            filepath = f'{FINISHED_PATH}/{filename}'
            if not os.path.exists(filepath):
                logging.warning('Torrent file no longer exists: %s', filepath)
                continue
            
            # Delete the torrent file
            logging.info('FILENAME is "%s" (deleting now)', filename)
            os.remove(filepath)
            
            # Process the torrent
            splitnames = os.path.splitext(filename)
            logging.info('SPLIT IS "%s"', splitnames)
            
            if splitnames[1] == '.torrent':
                name, episode, path = get_show_name_and_episode_and_path(filename)
                logging.info('NAME IS "%s"', name)
                logging.info('EPISODE IS "%s"', episode)
                logging.info('PATH IS "%s"', path)
                process_params(name, episode, f'{SRC_PATH}/{path}')
            
            logging.info('Finished processing: %s', filename)
            
        except Exception as e:
            logging.error('Error processing torrent %s: %s', filename, e)
            send_email(f'FAILED Processing {filename}', str(e))


async def main_async():
    """Run the main program with asyncio."""
    logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)
    logging.info('Starting BTEX processor')
    logging.info('DEST_PATH: %s', DEST_PATH)
    logging.info('SRC_PATH: %s', SRC_PATH)
    logging.info('FINISHED_PATH: %s', FINISHED_PATH)
    
    # Create tasks for watching and processing
    watcher_task = asyncio.create_task(watch_complete_torrents())
    processor_task = asyncio.create_task(process_complete_torrents())
    
    # Run both tasks concurrently
    try:
        await asyncio.gather(watcher_task, processor_task)
    except KeyboardInterrupt:
        logging.info('Shutting down...')
        watcher_task.cancel()
        processor_task.cancel()
        try:
            await asyncio.gather(watcher_task, processor_task)
        except asyncio.CancelledError:
            pass


def main():
    """
    Run the main program
    """
    asyncio.run(main_async())


if __name__ == '__main__':
    main()
