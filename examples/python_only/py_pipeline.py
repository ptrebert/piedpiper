# coding=utf-8


def run_script(args, config, sciobj):
    """
    :param args: command line args
    :type args: Namespace
    :param config:
    :type config: dict
    :param sciobj:
    :type sciobj: SysCallInterface
    :return:
    """

    sciobj.set_config_env(dict(config.items('JobConfig')), dict(config.items('EnvConfig')))
    if args.gridmode:
        jobcall = sciobj.drmaa_singlejob()
    else:
        jobcall = sciobj.local_job()

    print('Job 1')
    cmd = config.get('Pipeline', 'sysinfo')
    out, err = jobcall(cmd)
    if err:
        print('Error in call {} - {}'.format(cmd, err))

    print('Job 2 - expected fail')
    cmd = config.get('Pipeline', 'error')
    out, err = jobcall(cmd)
    if err:
        print('Error in call {} - {}'.format(cmd, err))

    return 0
