#!/usr/bin/env python3
# coding=utf-8

"""
Pied Piper pipeline runner - call with --help to get basic usage information
"""

import os as os
import sys as sys

import io as io
import time as time
import traceback as trb
import argparse as argp
import configparser as cfgp
import importlib as imp

from piedpiper.syscallinterface import SysCallInterface
from piedpiper.notify import send_email_notification

__version__ = '0.1.1'

__description__ = "Pied Piper is a deliberately simple pipeline runner that can execute either Ruffus pipelines" \
                  " or Python3 scripts with the ability to directly interface a grid engine via DRMAA bindings." \
                  " Pied Piper can be configured via INI files or command line. Library imports for Ruffus or DRMAA" \
                  " are isolated via the (independent) SysCallInterface class."


def piper_argument_parser():
    """
    :return:
    """
    parser = argp.ArgumentParser(prog='Pied Piper', description=__description__)
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('--grid-mode', '-grid', dest='gridmode', default=False, action='store_true',
                        help='Switch to grid engine mode. This argument should be checked in pipelines or'
                             ' scripts to determine the type of system call that should be used.')
    parser.add_argument('--run-config', '-run', dest='runconfig', type=str, default='',
                        help='Specify a full path to an RUN configuration file for Pied Piper.'
                             ' The path can also be given in form of the environment variable'
                             ' PIED_PIPER_CONFIG in the current shell.')
    parser.add_argument('--env-config', '-env', dest='envconfig', type=str,
                        default='/TL/deep-share/nobackup/deep_svn/Deep/pipelines/trunk/configs/environment.ini',
                        help='Specify a full path to an ENVIRONMENT configuration file for'
                             ' Pied Piper. By default, the env config file is read from the'
                             ' DEEP SVN in /TL/deep-share/nobackup.')
    parser.add_argument('--run-mode', '-mode', dest='runmode', type=str, choices=['ruffus', 'script'], default='ruffus',
                        help='Run a regular Ruffus pipeline or a Python3 script.')
    parser.add_argument('--debug-only', '-dbg', dest='debug', action='store_true', default=False,
                        help='Dump a full configuration and PYTHONPATH listing to the current working directory'
                             ' after command line and configuration file parsing and exit.')
    parser.add_argument('--email-user', '-usr', dest='notify', default='', type=str,
                        help='If a valid email address is specified, a notification is sent upon exit of'
                             ' Pied Piper. Note that this requires that localhost is configured as SMTP'
                             ' server or knows where to find one.')
    parser.add_argument('--limit-size', '-sz', dest='sizelimit', default=3000, type=int,
                        help='Specify the number of characters to send via email from the exception message'
                             ' and from the stack traceback. This number is divided by two and the first'
                             ' and the last N/2 characters are included in the email. This avoids overly'
                             ' long emails that may take a long time to load. Default: 3000 = 2 * 1500')
    args, unknown_args = parser.parse_known_args()
    return args, unknown_args


def piper_configuration_parser(args):
    """
    :return:
    """
    assert os.path.isfile(args.envconfig), 'No ENVIRONMENT configuration file found'
    if os.path.isfile(args.runconfig):
        runcfg = args.runconfig
    else:
        assert 'PIED_PIPER_CONFIG' in os.environ, 'No Pied Piper configuration file found as' \
                                                  ' command line argument ({}) or as shell' \
                                                  ' environment variable'.format(args.runconfig)
        runcfg = os.environ['PIED_PIPER_CONFIG']
        assert os.path.isfile(runcfg), 'Path to Pied Piper configuration file in shell environment' \
                                       ' is not a valid file path: {}'.format(runcfg)
    config = cfgp.ConfigParser(interpolation=cfgp.ExtendedInterpolation())
    # this change makes ConfigParser to read options case-sensitive
    config.optionxform = str
    config.read([args.envconfig, runcfg])
    assert config.has_section('Run'), 'No RUN section found in configuration'
    assert config.has_option('Run', 'load_path'), 'No LOAD PATH specified in RUN section of configuration'
    assert config.has_option('Run', 'load_name'), 'No LOAD NAME specified in RUN section of configuration'
    if config.has_option('Run', 'config'):
        add_configs = config.get('Run', 'config').split()
        config.read(add_configs)
    if config.has_option('Run', 'mkdir'):
        os.makedirs(config.get('Run', 'mkdir').strip(), exist_ok=True)
    return config


def overwrite_ruffus_args(args, config):
    """
    :param args:
    :param config:
    :return:
    """
    if config.has_section('Ruffus'):
        cmdargs = dict()
        cmdargs['draw_horizontally'] = bool
        cmdargs['flowchart'] = str
        cmdargs['flowchart_format'] = str
        cmdargs['forced_tasks'] = lambda x: x.split()
        cmdargs['history_file'] = str
        cmdargs['jobs'] = int
        cmdargs['just_print'] = bool
        cmdargs['key_legend_in_graph'] = bool
        cmdargs['log_file'] = str
        cmdargs['recreate_database'] = bool
        cmdargs['target_tasks'] = lambda x: x.split()
        cmdargs['touch_files_only'] = bool
        cmdargs['use_threads'] = bool
        cmdargs['verbose'] = lambda x: x.split()
        for k, v in config.items('Ruffus'):
            try:
                args.__setattr__(k, cmdargs[k](v))
            except KeyError:
                pass
    return args


def adapt_sys_path(config):
    """
    :param config:
    :return:
    """
    if config.has_option('Run', 'load_path'):
        add_paths = config.get('Run', 'load_path').split()
        for p in add_paths:
            sys.path.insert(0, p)
    return config.get('Run', 'load_name')


def make_debug_dump(config):
    """
    :param config:
    :return:
    """
    with open('dbg_pied_piper_config.ini', 'w') as outfile:
        config.write(outfile)
    with open('dbg_pied_piper_paths.txt', 'w') as outfile:
        _ = outfile.write('PYTHONPATH\n\n{}'.format('\n'.join(sys.path)))
    return


def notify_user(user_addr, start, end, exc, runinfo, err, trb, limit):
    """
    :param user_addr:
    :param start:
    :param end:
    :param exc: exit code
    :param err: the exception, if applicable
    :param trb: the stack traceback, if applicable
    :param limit: character limit for sending error information
    :return:
    """
    half_limit = limit // 2
    if len(trb) > limit:
        trb = trb[:half_limit] + '\n\n[ ... SIZE LIMIT REACHED ... ]\n\n' + trb[-half_limit:]
    if len(err) > limit:
        err = err[:half_limit] + '\n\n[ ... SIZE LIMIT REACHED ... ]\n\n' + err[-half_limit:]
    try:
        subject = 'Pied Piper run exit: {}'.format(exc)
        username = user_addr.split('@')[0]
        body = 'Hello {username},\nyour Pied Piper run finished with status: {exit}\n'\
               'Start time: {start}\nEnd time: {end}\n'\
               'Run info: {runinfo}\n\n'\
               'Exception: {error}\n\nStack traceback: {trace}\n\n' \
               'Have a nice day!\nPied Piper'
        values = {'username': username, 'exit': exc, 'start': start, 'end': end,
                  'error': err, 'trace': trb, 'runinfo': runinfo}
        body = body.format(**values)
        send_email_notification(user_addr, 'pied.piper@pipeline.run', subject, body)
    except Exception as e:
        sys.stderr.write('\nSending notification email failed: {}\n'.format(e))
    finally:
        return


if __name__ == '__main__':
    exc = 0
    start = time.ctime()
    args = None
    run_info = 'ERROR'
    try:
        args, unknown_args = piper_argument_parser()
        config = piper_configuration_parser(args)
        if args.runmode == 'ruffus':
            cmdline = imp.import_module('ruffus.cmdline')
            ruffus_prs = cmdline.get_argparse()
            args, unknown_args = ruffus_prs.parse_known_args(unknown_args, args)
            args = overwrite_ruffus_args(args, config)
        if args.gridmode and args.runmode == 'ruffus':
            args.use_threads = True  # just as fail-safe
        mod_name = adapt_sys_path(config)
        if args.debug:
            make_debug_dump(config)
            sys.exit(0)
        imp_ruffus_drmaa = args.runmode == 'ruffus'
        imp_drmaa = args.runmode == 'script' and args.gridmode
        run_info = os.path.basename(args.runconfig) + ' / ' + config.get('Run', 'load_name')
        with SysCallInterface(imp_ruffus_drmaa, imp_drmaa) as sci_obj:
            mod = imp.import_module(mod_name)
            if args.runmode == 'ruffus':
                pipe = mod.build_pipeline(args, config, sci_obj)
                cmdline.run(args)
            elif args.runmode == 'script':
                exc = mod.run_script(args, config, sci_obj)
            else:
                # note that this should be caught already by ArgumentParser
                raise RuntimeError('Pied Piper run mode {} not recognized'.format(args.runmode))
        end = time.ctime()
        if args and args.notify:
            notify_user(args.notify, start, end, exc, run_info, 'none', 'none', args.sizelimit)
    except Exception as e:
        end = time.ctime()
        buf = io.StringIO()
        trb.print_exc(file=buf)
        sys.stderr.write('\nError: {}'.format(e))
        sys.stderr.write('\n{}\n'.format(buf.getvalue()))
        exc = 1
        if args.notify:
            notify_user(args.notify, start, end, exc, run_info, str(e), buf.getvalue(), args.sizelimit)
    finally:
        sys.exit(exc)
