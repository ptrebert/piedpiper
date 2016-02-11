# coding=utf-8

"""
This module offers a single, flexible (?) interface to various types
of system calls, either for local computations or grid engine jobs
To facilitate encapsulation and proper shutdown, the class supports
Python's with statement
"""

import sys as sys
import os as os
import functools as fnt
import copy as copy
import random as rand
import importlib as imp
from string import ascii_uppercase as ASCII
from threading import Lock

import piedpiper.syscalls as sc

# For reference

# DRMAA session
# ['JOB_IDS_SESSION_ALL', 'JOB_IDS_SESSION_ANY', 'TIMEOUT_NO_WAIT', 'TIMEOUT_WAIT_FOREVER',
# 'contact', 'contactString', 'control', 'createJobTemplate', 'deleteJobTemplate', 'drmaaImplementation',
# 'drmsInfo', 'exit', 'initialize', 'jobStatus', 'runBulkJobs', 'runJob', 'synchronize', 'version', 'wait']

# DRMAA JobTemplate
# ['HOME_DIRECTORY', 'PARAMETRIC_INDEX', 'WORKING_DIRECTORY', 'args', 'attributeNames',
# 'blockEmail', 'deadlineTime', 'delete', 'email', 'errorPath', 'hardRunDurationLimit',
# 'hardWallclockTimeLimit', 'inputPath', 'jobCategory', 'jobEnvironment', 'jobName',
# 'jobSubmissionState', 'joinFiles', 'nativeSpecification', 'outputPath', 'remoteCommand',
# 'softRunDurationLimit', 'softWallclockTimeLimit', 'startTime', 'transferFiles', 'workingDirectory']


class SysCallInterface(object):
    """ This interface class encapsulates all references to DRMAA
     objects and supports the 'with' context manager to ensure clean
     shutdown of the DRMAA session
    """
    def __init__(self, import_ruffus_drmaa=False,
                 import_drmaa=False, norm_env=True):
        """
        :param import_ruffus_drmaa: Import Ruffus' DRMAA wrapper
        :param import_drmaa: Import the Python DRMAA bindings
        :param norm_env: Should the names of the environment variables all be made UPPERCASE?
        :return:
        """
        self.ruffus_drmaa = None
        self.drmaa_mod = None
        if import_ruffus_drmaa:
            self.ruffus_drmaa = imp.import_module('ruffus.drmaa_wrapper')
            self.drmaa_mod = imp.import_module('drmaa')
            self.drmaa_ver = self.drmaa_mod.__version__
        elif import_drmaa:
            self.drmaa_mod = imp.import_module('drmaa')
            self.drmaa_ver = self.drmaa_mod.__version__
        self.norm_env = norm_env
        self._str_args = ('workdir', 'inpath', 'outpath', 'errpath',
                          'jobname', 'native_spec', 'scriptdir')
        self._complex_args = ('env',)
        self._bool_args = ('keepscripts', 'joinfiles')
        self.supported_args = self._str_args + self._complex_args + self._bool_args
        self.config = None
        # these members are cleaned up upon exit
        self.lock = Lock()
        self.session = None
        self.jobtemplates = []

    def __enter__(self):
        """
        :return: self
        """
        if self.drmaa_mod is not None:
            self.session = self.drmaa_mod.Session()
            self.session.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """ When exiting, take care of cleaning up JobTemplates and closing
        the session to avoid memory leaks
        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return:
        """
        if self.session is not None:
            for jt in self.jobtemplates:
                try:
                    self.session.deleteJobTemplate(jt)
                except Exception as e:
                    #pass  # do we care?
                    sys.stderr.write('\nDeleting DRMAA job template failed: {}\n'.format(e))
            try:
                self.session.exit()
            except Exception as e:
                sys.stderr.write('\nClosing DRMAA session failed: {}\n'.format(e))

    def _sanity_check(self):
        """ The sanity check function performs some
        duck typing checks, but due to the potential
        complexity of the supplied arguments, cannot check
        for their semantic correctness
        """
        if 'env' in self.config:
            if not isinstance(self.config['env'], dict):
                self.config['env'] = dict(self.config['env'])
            if self.norm_env:
                norm_env = dict()
                for var, val in self.config['env'].items():
                    norm_env[var.upper()] = val
                self.config['env'] = norm_env
        for arg in self._str_args:
            try:
                self.config[arg] = str(self.config[arg])
            except KeyError:
                pass  # why did I do this?!
        return

    def _configure_jobtemplate(self, jobtemplate):
        """ Configure a JobTemplate object according to the
        current configuration of the SystemCallInterface
        By default, the JobName is suffixed with 4 random
        uppercase letters to ease identification
        """
        assert self.config is not None, 'No configuration set'
        jname = self.config.get('jobname', 'SCIjob')
        jname += ''.join([rand.choice(ASCII) for _ in range(4)])
        jobtemplate.jobName = jname
        wd = self.config.get('workdir', os.getcwd()).strip(':')
        op = self.config.get('outpath', '/dev/null').strip(':')
        ep = self.config.get('errpath', '/dev/null').strip(':')
        jobtemplate.workingDirectory = wd  # this one is critical, with a : in front, does not work
        jobtemplate.outputPath = ':' + op
        jobtemplate.errorPath = ':' + ep
        jobtemplate.jobEnvironment = self.config.get('env', {})
        jobtemplate.remoteCommand = ''
        jobtemplate.nativeSpecification = self.config.get('native_spec', '')
        jobtemplate.joinFiles = bool(int(self.config.get('joinfiles', False)))
        return jobtemplate

    def summarize_status(self):
        """ Return a summary string of the current status, i.e.
        loaded modules and configuration
        """
        raise NotImplementedError

    def set_config_env(self, config, env):
        """ Update static and environment configuration if
        provided.
        Note to myself: since both are mutable objects subject
        to change in the global scope, deepcopy is probably a
        necessity - though, by design, a change in config would
        usually be followed by an update of the system calls
        """
        if config is not None:
            self.config = copy.deepcopy(config)
        if env is not None:
            self.config['env'] = copy.deepcopy(env)
        self._sanity_check()
        return

    def local_job(self):
        """ Basic system call using Python's subprocess class
        Callable object returns stdout and stderr
        This is semantically equivalent to the ruffus_localjob
        below - just w/o depending on Ruffus obviously
        """
        kwargs = dict()
        kwargs['workdir'] = self.config.get('workdir', None)
        kwargs['env'] = self.config.get('env', None)
        call_me = fnt.partial(sc.custom_systemcall, **kwargs)
        return call_me

    def ruffus_gridjob(self):
        """ This job type is suitable for arbitrary command lines
        as the command string is written to a temporary shell script
        and then submitted
        """
        kwargs = dict()
        kwargs['job_name'] = self.config.get('jobname', None)
        kwargs['job_other_options'] = self.config.get('native_spec', None)
        kwargs['job_script_directory'] = self.config.get('scriptdir', None)
        kwargs['job_environment'] = self.config.get('env', None)
        kwargs['working_directory'] = self.config.get('workdir', None)
        kwargs['drmaa_session'] = self.session
        kwargs['retain_job_scripts'] = bool(int(self.config.get('keepscripts', False)))
        call_me = fnt.partial(self.ruffus_drmaa.run_job, **kwargs)
        return call_me

    def ruffus_localjob(self):
        """ This job type is suitable for arbitrary command lines
        as the command string is written to a temporary shell script
        and then submitted
        """
        kwargs = dict()
        kwargs['job_environment'] = self.config.get('env', None)
        kwargs['working_directory'] = self.config.get('workdir', None)
        kwargs['run_locally'] = True  # here is the switch
        kwargs['local_echo'] = True
        call_me = fnt.partial(self.ruffus_drmaa.run_job, **kwargs)
        return call_me

    def drmaa_singlejob(self):
        """ This job type can be used w/o Ruffus, i.e. it directly
        interfaces with the Grid Engine and can thus only be used
        for proper commands (shell scripts or binaries if the native
        specification is set appropriately)
        """
        jt = self.session.createJobTemplate()
        jt = self._configure_jobtemplate(jt)
        self.jobtemplates.append(jt)
        kwargs = dict()
        kwargs['jobtemplate'] = jt
        kwargs['session'] = self.session
        kwargs['waitforever'] = self.drmaa_mod.Session.TIMEOUT_WAIT_FOREVER
        kwargs['lock'] = self.lock
        call_me = fnt.partial(sc.drmaa_singlejob, **kwargs)
        raise call_me

    def drmaa_singlejob_argv(self):
        """ Same as drmaa_singlejob, but command line arguments can
        be passed to the job (list of strings). These are then
        accessible via $1, $2 and so on
        """
        jt = self.session.createJobTemplate()
        jt = self._configure_jobtemplate(jt)
        self.jobtemplates.append(jt)
        kwargs = dict()
        kwargs['jobtemplate'] = jt
        kwargs['session'] = self.session
        kwargs['waitforever'] = self.drmaa_mod.Session.TIMEOUT_WAIT_FOREVER
        kwargs['lock'] = self.lock
        call_me = fnt.partial(sc.drmaa_singlejob_argv, **kwargs)
        raise call_me

    def drmaa_arrayjob(self, start, end, step=1):
        """ This job type can be used w/o Ruffus, i.e. it directly
        interfaces with the Grid Engine and can thus only be used
        for proper commands (very likely only shell scripts or specialized
        tools aware of the SGE_TASK_ID variable)
        """
        assert 0 < start < start + step < end, 'Number of tasks in ArrayJob not well-defined:' \
                                               ' {}-{}-{}'.format(start, end, step)
        jt = self.session.createJobTemplate()
        jt = self._configure_jobtemplate(jt)
        self.jobtemplates.append(jt)
        kwargs = dict()
        kwargs['jobtemplate'] = jt
        kwargs['session'] = self.session
        kwargs['waitforever'] = self.drmaa_mod.Session.TIMEOUT_WAIT_FOREVER
        kwargs['lock'] = self.lock
        call_me = fnt.partial(sc.drmaa_arrayjob, **kwargs)
        raise call_me

    def drmaa_arrayjob_argv(self, start, end, step=1):
        """ Same as drmaa_arrayjob, but command line arguments can
        be passed to the job (list of strings). These are then
        accessible via $1, $2 and so on
        """
        assert 0 < start < start + step < end, 'Number of tasks in ArrayJob not well-defined:' \
                                               ' {}-{}-{}'.format(start, end, step)
        jt = self.session.createJobTemplate()
        jt = self._configure_jobtemplate(jt)
        self.jobtemplates.append(jt)
        kwargs = dict()
        kwargs['jobtemplate'] = jt
        kwargs['session'] = self.session
        kwargs['waitforever'] = self.drmaa_mod.Session.TIMEOUT_WAIT_FOREVER
        kwargs['lock'] = self.lock
        call_me = fnt.partial(sc.drmaa_arrayjob_argv, **kwargs)
        return call_me
