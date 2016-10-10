# coding=utf-8

"""
Module for convenience wrappers to schedule DRMAA jobs or local system calls
"""

import os as os
import io as io
import subprocess as sp
import traceback as trb
import fnmatch as fnm
import functools as fnt

# As note to self from DRMAA Python docs
# JobInfo = namedtuple("JobInfo",
#                     """jobId hasExited hasSignal terminatedSignal hasCoreDump
#                        wasAborted exitStatus resourceUsage""")


def _read_output_file(filepath, endpattern, attempts=3):
    """
    :param filepath:
    :param endpattern:
    :return:
    """
    allfiles = os.listdir(filepath)
    outfiles = fnm.filter(allfiles, endpattern)
    content = ''
    for of in outfiles:
        a = attempts
        while a > 0:
            try:
                tmp = open(os.path.join(filepath, of), 'r').read().strip()
            except IOError:
                a -= 1
                continue
            else:
                tmp += '\n'
                content += tmp
                break
    return content


def exec_env(syscall):
    """
    :param syscall:
    :return:
    """
    @fnt.wraps(syscall)
    def wrap_env(*args, **kwargs):
        """
        :param args:
        :param kwargs:
        :return:
        """
        kwtmp = dict(kwargs)
        assert len(args) == 1, 'Expecting command line as single positional argument'
        cmdtmp = args[0]
        if 'activate' in kwtmp:
            env = kwtmp['activate']
            if env is not None:
                cmdtmp = 'source activate {} && '.format(env) + cmdtmp + ' ; source deactivate'
            del kwtmp['activate']
        return syscall(cmdtmp, **kwtmp)
    return wrap_env


@exec_env
def drmaa_singlejob(cmd, jobtemplate, session, waitforever, lock):
    """
    :param cmd:
    :param jobtemplate:
    :param session:
    :param waitforever:
    :return:
    """
    out, err = '', ''
    try:
        with lock:
            outpath = jobtemplate.outputPath
            errpath = jobtemplate.errorPath
            jobtemplate.remoteCommand = cmd
            jobid = session.runJob(jobtemplate)
        out, err = _handle_drmaa_singlejob(jobid, session, waitforever, outpath, errpath)
    except Exception as e:
        err = 'Error for SingleJob call: {}\nMessage: {}'.format(cmd, e)
    finally:
        return out, err


@exec_env
def drmaa_singlejob_argv(cmd, argv, jobtemplate, session, waitforever, lock):
    """
    :param cmd:
    :param argv:
    :param jobtemplate:
    :param session:
    :param waitforever:
    :return:
    """
    out, err = '', ''
    try:
        with lock:
            argv = list(map(str, argv))
            outpath = jobtemplate.outputPath
            errpath = jobtemplate.errorPath
            jobtemplate.remoteCommand = cmd
            jobtemplate.args = argv
            jobid = session.runJob(jobtemplate)
        out, err = _handle_drmaa_singlejob(jobid, session, waitforever, outpath, errpath)
    except Exception as e:
        err = 'Error for SingleJob argV call: {}\nMessage: {}'.format(cmd, e)
    finally:
        return out, err


def _handle_drmaa_singlejob(jid, session, waitforever, outpath, errpath):
    """
    :param jid:
    :param session:
    :param waitforever:
    :param outpath:
    :param errpath:
    :return:
    """
    out, err = ['Job {} submitted'.format(jid)], []
    try:
        try:
            stat = session.jobStatus(jid)
            out.append('Job {} status: {}'.format(jid, stat))
        except Exception as e:
            err.append('Checking job status failed: {}'.format(str(e)))
        retval = session.wait(jid, waitforever)
        if retval.exitStatus != 0:
            err.append('Exit {} - Error'.format(retval.exitStatus))
        out.append('Job {} finished with status: {} - [Was aborted? {}]'.format(jid, retval.hasExited, retval.wasAborted))
        if 'start_time' in retval.resourceUsage:
            ru = retval.resourceUsage
            out.append('Start: {}'.format(ru['start_time']))
            out.append('End: {}'.format(ru['end_time']))
            out.append('MAXRSS: {}'.format(ru['ru_maxrss']))
        out.append(_read_output_file(outpath.strip(':'), '*o' + jid))
        err.append(_read_output_file(errpath.strip(':'), '*e' + jid))
    except Exception as e:
        buf = io.StringIO()
        trb.print_exc(file=buf)
        err.append('Error during job handling: {}'.format(e))
        err.append('Job ID: {}'.format(jid))
        err.append('Call type: DRMAA single job')
        err.append('=== Traceback ===')
        err.append(buf.getvalue())
    finally:
        return '\n'.join(out), '\n'.join(err)


@exec_env
def drmaa_arrayjob(cmd, jobtemplate, session, waitforever, lock, start, end, step):
    """
    :param cmd:
    :param jobtemplate:
    :param session:
    :param waitforever:
    :return:
    """
    out, err = '', ''
    try:
        with lock:
            outpath = jobtemplate.outputPath
            errpath = jobtemplate.errorPath
            jobtemplate.remoteCommand = cmd
            jobids = session.runBulkJobs(jobtemplate, start, end, step)
        out, err = _handle_drmaa_arrayjob(jobids, session, waitforever, outpath, errpath)
    except Exception as e:
        err = 'Error for SingleJob argV call: {}\nMessage: {}'.format(cmd, e)
    finally:
        return out, err


@exec_env
def drmaa_arrayjob_argv(cmd, argv, jobtemplate, session, waitforever, lock, start, end, step):
    """
    :param cmd:
    :param argv:
    :param jobtemplate:
    :param session:
    :param waitforever:
    :return:
    """
    out, err = '', ''
    try:
        with lock:
            argv = list(map(str, argv))
            outpath = jobtemplate.outputPath
            errpath = jobtemplate.errorPath
            jobtemplate.remoteCommand = cmd
            jobtemplate.args = argv
            jobids = session.runBulkJobs(jobtemplate, start, end, step)
        out, err = _handle_drmaa_arrayjob(jobids, session, waitforever, outpath, errpath)
    except Exception as e:
        err = 'Error for SingleJob argV call: {}\nMessage: {}'.format(cmd, e)
    finally:
        return out, err


def _handle_drmaa_arrayjob(jids, session, waitforever, outpath, errpath):
    """
    :param jids: job ID combined with task ID
     :type: list of str
    :param session:
    :param waitforever:
    :param outpath:
    :param errpath:
    :return:
    """
    out, err = ['ArrayJob {} submitted - first task'.format(jids[0])], []
    try:
        # blocking call, wait until all jobs done
        # Important
        # Calling synchronize() with dispose=False can lead to a memory leak
        # if the calling application does not call wait() for each individual
        # job afterwards
        session.synchronize(jids, waitforever, dispose=False)
        for j in jids:
            try:
                retval = session.wait(j, waitforever)
                if retval.exitStatus != 0:
                    err.append('Exit {} - Error'.format(retval.exitStatus))
                out.append('Job {} finished with status: {} - [Was aborted? {}]'.format(j, retval.hasExited, retval.wasAborted))
                if 'start_time' in retval.resourceUsage:
                    ru = retval.resourceUsage
                    out.append('Start: {}'.format(ru['start_time']))
                    out.append('End: {}'.format(ru['end_time']))
                    out.append('MAXRSS: {}'.format(ru['ru_maxrss']))
                # for thousands of jobs, this can take quite some time
                # maybe, one should enforce /dev/null if the number of
                # tasks in an array job is too large
                out.append(_read_output_file(outpath.strip(':'), '*o' + j))
                err.append(_read_output_file(errpath.strip(':'), '*e' + j))
            except Exception as e:
                err.append('Warning: checking job status for {} after sync failed: {}'.format(j, e))
    except Exception as e:
        buf = io.StringIO()
        trb.print_exc(file=buf)
        err.append('Error during job handling: {}'.format(e))
        err.append('ArrayJob first task: {}'.format(jids[0]))
        err.append('Call type: DRMAA array job')
        err.append('=== Traceback ===')
        err.append(buf.getvalue())
    finally:
        return '\n'.join(out), '\n'.join(err)


@exec_env
def custom_systemcall(cmd, workdir=None, env=None):
    """
    :param cmd:
    :param workdir:
    :param env:
    :return:
    """
    out, err = '', ''
    try:
        proc = sp.Popen(cmd, cwd=workdir, env=env, shell=True,
                        stdout=sp.PIPE, stderr=sp.PIPE, executable='/bin/bash')
        out, err = proc.communicate()
        if proc.returncode != 0:
            out = out.decode('utf-8')
            err = 'ERROR from call: {}\nExit code: {}\nMessage: {}'.format(cmd, proc.returncode, err.decode('utf-8'))
        else:
            out, err = out.decode('utf-8'), err.decode('utf-8')
    except Exception as e:
        err = 'ERROR during call: {}\nMessage: {}'.format(cmd, str(e))
    finally:
        return out, err
