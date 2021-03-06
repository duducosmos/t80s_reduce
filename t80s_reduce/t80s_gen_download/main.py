import sys, os
import numpy as np
import logging
from datetime import datetime
import yaml
from t80s_reduce.core.constants import *


def main(argv):
    import argparse

    parser = argparse.ArgumentParser(description='Given a configuration file, generate a .sh script with the '
                                                 'appropriate instructions to download all dataset.')

    parser.add_argument('-c', '--config',
                        help='Configuration file. The file will be over-written at the end with the result from the '
                             'checks.',
                        type=str)

    parser.add_argument('-o', '--output',
                        help='Output name.',
                        type=str)

    parser.add_argument("--check", action="store_true",
                        help='Check that the files exists in local path before generating wget line.')
    parser.add_argument('--verbose', '-v', action='count')

    args = parser.parse_args(argv[1:])

    logging.basicConfig(format='%(levelname)s:%(asctime)s::%(message)s',
                        level=args.verbose)

    log = logging.getLogger(__name__)

    # Open configuration file
    log.debug('Reading configuration file: %s' % args.config)
    with open(args.config, 'r') as fp:
        config = yaml.load(fp)

    # Prepare calibrations

    # Check that there is a path defined in the configuration file
    if args.check and 'path' not in config:
        log.warning('Cannot run in "check" mode without a path defined in the configuration file. Ignoring check')
        args.check = False

    download_string = '# Download script - Generated by t80s_reduce - %s\n' % datetime.today()

    if 'bias' in config['calibrations']:
        download_string += '# This will download your bias frames\n'

        for bias in config['calibrations']['bias']['raw files']:
            path = '' if 'path' not in config else os.path.join(config['path'],
                                                                config['calibrations']['bias']['night'],
                                                                'bias',
                                                                'raw_files')
            if args.check and os.path.exists(os.path.join(path, bias)):
                log.debug('File %s in path. Skipping...' % bias)
                continue
            else:
                log.debug('Requesting file %s.' % bias)

            download_string += DOWNLOAD_STRING_HEADER + DOWNLOAD_STRING_HOST.format(
                night=config['calibrations']['bias']['night'],
                filename=bias,
                dest_path=path)
            download_string += '\n'

        download_string += '# End bias frames\n'

    if 'sky-flat' in config['calibrations']:
        download_string += '# This will download your sky-flat frames\n'

        for filter in config['calibrations']['sky-flat']['filters']:

            download_string += '# Start filter %s\n' % filter

            for flat in config['calibrations']['sky-flat'][filter]['raw files']:
                path = '' if 'path' not in config else os.path.join(config['path'],
                                                                    config['calibrations']['sky-flat'][filter]['night'],
                                                                    'flat',
                                                                    filter,
                                                                    'raw_files')
                if args.check and os.path.exists(os.path.join(path, flat)):
                    log.debug('File %s in path. Skipping...' % flat)
                    continue
                else:
                    log.debug('Requesting file %s.' % flat)

                download_string += DOWNLOAD_STRING_HEADER + DOWNLOAD_STRING_HOST.format(
                    night=config['calibrations']['sky-flat'][filter]['night'],
                    filename=flat,
                    dest_path=path)
                download_string += '\n'
            download_string += '# End filter %s\n' % filter

        download_string += '# End flats\n'

    download_string += '# This will download your data frames\n'

    for object in config['objects']:
        for filter in FILTERS:
            if filter not in config['objects'][object]:
                continue
            download_string += '# Start: %s:%s\n' % (object, filter)
            for raw in config['objects'][object][filter]['raw files']:
                path = '' if 'path' not in config else os.path.join(config['path'],
                                                                    config['objects'][object]['night'],
                                                                    object.replace(' ', '_'),
                                                                    filter,
                                                                    'raw_files')
                if args.check and os.path.exists(os.path.join(path, raw)):
                    log.debug('File %s in path. Skipping...' % raw)
                    continue
                else:
                    log.debug('Requesting file %s.' % raw)

                download_string += DOWNLOAD_STRING_HEADER + DOWNLOAD_STRING_HOST.format(
                    night=config['objects'][object]['night'],
                    filename=raw,
                    dest_path=path)
                download_string += '\n'
            download_string += '# End: %s:%s\n' % (object, filter)

    download_string += '# End data frames\n'

    log.info('Saving download script to %s' % args.output)
    with open(args.output, 'w') as fp:
        fp.write(download_string)

    return 0
