import re
from datetime import datetime


def parse_scanimage_header(scan):
    header = {}
    for item in scan.header.split('\n'):
        try:
            key, value = item.split(' = ')
            key = re.sub('^scanimage_', '', key.replace('.', '_'))
            header[key] = value
        except:
            pass
    return header


def get_scanimage_acq_time(scan):
    header = parse_scanimage_header(scan)
    recording_time = datetime.strptime((header['epoch'][1:-1]).replace(',', ' '),
                                       '%Y %m %d %H %M %S.%f')
    return recording_time
