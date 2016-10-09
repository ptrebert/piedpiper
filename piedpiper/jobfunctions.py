# coding=utf-8

"""
A module dedicated to wrapping job functions suitable for pipelines, be it Ruffus or plain Python.
In spirit, most of these functions mimic the behavior of their Ruffus counterparts (but do not depend
on Ruffus being importable) in terms of number of input and output files.
Additionally, each function takes at least a parameter representing the command line
and the respective system call to execute it.
The functions are exposed to the pipeline via the System Call Interface object.
While this design decision may seem a bit odd, it avoids that a generic module
containing these functions has to be imported in each pipeline script (separation of concerns).
"""

import os as os
import itertools as itt
import fnmatch as fnm

# TODO Refactor some functions
# there is no necessity to keep single- and multi-input functions separate


def _flatten_nested_iterable(struct):
    """
    :param struct:
    :return:
    """
    result = []
    for item in struct:
        if hasattr(item, '__iter__') and not isinstance(item, str):
            result.extend(_flatten_nested_iterable(item))
        else:
            result.append(item)
    return result


def _normalize_job_output(output):
    """
    :param output: Tool output on stdout/stderr
    :type output: str or bytes, list of str or bytes
    :return: normalized output, all parts concatenated (if applicable)
    :rtype: str
    """
    if isinstance(output, list):
        if len(output) == 0:
            normout = ''
        elif isinstance(output[0], bytes):
            output = list(map(lambda x: x.decode('utf-8'), output))
            normout = '\n'.join(output).strip()
        else:
            assert isinstance(output[0], str), 'Unexpected type of Job output (in list): {}'.format(type(output[0]))
            normout = '\n'.join(output).strip()
    elif isinstance(output, bytes):
        normout = output.decode('utf-8').strip()
    else:
        assert isinstance(output, str), 'Unexpected type of Job output: {}'.format(type(output))
        normout = output.strip()
    return normout


def _check_job(out, err):
    """
    If a job returned output on stderr, this checks for various keywords in said
    output to determine if the job failed. Unfortunately, some developers do not
    follow the simple rule of a non-zero exit status in case of errors, so this
    heuristic has turned out to be necessary.
    Specifically, this checks for the following keywords:

    ['error', 'fail', 'failed', 'failure', 'segfault', 'abort']

    :param out: Job output on stdout
    :type out: str or bytes, list of str or bytes
    :param err: Job output on stderr
    :type err: str or bytes, list of str or bytes
    :return: checked output of stdout and stderr
    :rtype: 2-tuple of str
    :raises ruffus.JobSignalledBreak:
    :raises RuntimeError:
    """
    error_notes = ['error', 'fail', 'failed', 'failure', 'segfault', 'abort']
    out = _normalize_job_output(out)
    err = _normalize_job_output(err)
    if err:
        if any([msg in err.lower() for msg in error_notes]):
            try:
                from ruffus import JobSignalledBreak
                raise JobSignalledBreak(err)
            except ImportError:
                raise RuntimeError(err)
    return out, err


def _run_command(cmd, formatter, syscall, posrep=False):
    """
    :param cmd:
    :param formatter:
    :param syscall:
    :param posrep:
    :return: None
    :rtype: NoneType
    """
    if posrep:
        tmp = cmd.format(*formatter)
    else:
        tmp = cmd.format(**formatter)
    out, err = syscall(tmp)
    out, err = _check_job(out, err)
    return None


def recursive_collect(basedir, filtpat):
    """
    :param basedir:
    :param filtpat:
    :return:
    """
    collected = []
    for root, dirs, files in os.walk(basedir, followlinks=False):
        if files:
            files = fnm.filter(files, filtpat)
            for f in files:
                collected.append(os.path.join(root, f))
    assert collected, 'No files collected starting at top folder {}'.format(basedir)
    return collected


def syscall_raw(cmd, syscall):
    """
    Execute command line w/o formatting, check output and return

    :param cmd: The command line to execute
     :type: str
    :param syscall: A callable/function object expecting a single argument
     :type: function
    :return: None
     :type: NoneType
    """
    _ = _run_command(cmd, tuple(), syscall, posrep=True)
    return None


def syscall_in_out(inputfile, outputfile, cmd, syscall, posrep=False):
    """
    :param inputfile:
    :param outputfile:
    :param cmd:
    :param syscall:
    :param posrep: use positional replacement for input and output when formatting command
    :return:
     :rtype: str
    """
    assert os.path.isfile(inputfile), 'Input path is not a file: {}'.format(inputfile)
    assert outputfile, 'Received no output file'
    if posrep:
        formatter = (inputfile, outputfile)
    else:
        formatter = {'inputfile': inputfile, 'outputfile': outputfile}
    _ = _run_command(cmd, formatter, syscall, posrep)
    assert os.path.isfile(outputfile), 'Output path is not a file: {} - job failed?'.format(outputfile)
    return outputfile


def syscall_in_pat(inputfile, outputfiles, outdir, filter, cmd, syscall, posrep=False, rec=False):
    """
    System call for cases where a single input file is split
    into multiple output files (number determined at runtime), hence
    outputfiles represents a matching pattern rather than a filename

    :return: list of files
    """
    assert os.path.isfile(inputfile), 'Input path is not a file: {}'.format(inputfile)
    if posrep:
        formatter = inputfile,
    else:
        formatter = {'inputfile': inputfile}
    _ = _run_command(cmd, formatter, syscall, posrep)
    if rec:
        outfiles = recursive_collect(outdir, filter)
    else:
        outfiles = os.listdir(outdir)
        outfiles = fnm.filter(outfiles, filter)
        outfiles = [os.path.join(outdir, f) for f in outfiles]
    assert len(outfiles) > 0, 'No output files produced by command {} with filter pattern {}'.format(cmd, filter)
    return outfiles


def syscall_in_out_ref(inputfile, outputfile, reference, cmd, syscall):
    """
    :param inputfile:
    :param outputfile:
    :param reference:
    :param cmd:
    :param syscall:
    :return:
    """
    assert os.path.isfile(inputfile), 'Input path is not a file: {}'.format(inputfile)
    assert outputfile, 'Received no output file'
    assert os.path.isfile(reference), 'Reference path is not a file: {}'.format(outputfile)
    fmt = {'inputfile': inputfile, 'outputfile': outputfile, 'referencefile': reference}
    _ = _run_command(cmd, fmt, syscall)
    assert os.path.isfile(outputfile), 'Output path is not a file: {} - job failed?'.format(outputfile)
    return outputfile


def syscall_ins_out_ref(inputfiles, outputfile, reference, cmd, syscall):
    """
    :param inputfiles:
    :param outputfile:
    :param reference:
    :param cmd:
    :param syscall:
    :return:
    """
    flattened = _flatten_nested_iterable(inputfiles)
    assert all([os.path.isfile(f) for f in flattened]), 'Not all input paths are files: {}'.format(flattened)
    assert os.path.isfile(reference), 'Invalid path to reference file: {}'.format(reference)
    fmt = {'inputfiles': ' '.join(flattened), 'outputfile': outputfile, 'referencefile': reference}
    _ = _run_command(cmd, fmt, syscall)
    assert os.path.isfile(outputfile), 'Output path is not a file: {} - job failed?'.format(outputfile)
    return outputfile


def syscall_inref_out(inputpair, outputfile, cmd, refext, syscall):
    """
    :param inputpair:
    :param outputfile:
    :param cmd:
    :param syscall:
    :return:
    """
    assert len(inputpair) == 2, 'Too many (or not enough) input files: {}'.format(inputpair)
    if inputpair[1].endswith(refext):
        reference = inputpair[1]
        inputfile = inputpair[0]
    else:
        reference = inputpair[0]
        inputfile = inputpair[1]
    fmt = {'inputfile': inputfile, 'outputfile': outputfile, 'referencefile': reference}
    _ = _run_command(cmd, fmt, syscall)
    assert os.path.isfile(outputfile), 'Output path is not a file: {} - job failed?'.format(outputfile)
    return outputfile


def syscall_ins_out(inputfiles, outputfile, cmd, syscall, posrep=False):
    """
    Merge/join job, several input files create a single output file

    :param inputfiles:
    :param outputfile:
    :return:
    """
    flattened = _flatten_nested_iterable(inputfiles)
    assert all([os.path.isfile(f) for f in flattened]), 'Not all input paths are files: {}'.format(flattened)
    assert outputfile, 'Received no output file'
    flattened = ' '.join(flattened)
    if posrep:
        fmt = (flattened, outputfile)
    else:
        fmt = {'inputfiles': flattened, 'outputfile': outputfile}
    _ = _run_command(cmd, fmt, syscall, posrep)
    assert os.path.isfile(outputfile), 'Output path is not a file: {} - job failed?'.format(outputfile)
    return outputfile


def syscall_ins_pat(inputfiles, outputpattern, outdir, filter, cmd, syscall, posrep=False, rec=False):
    """
    System call for cases where a set of input files is split
    into multiple output files (number determined at runtime), hence
    outputfiles represents a matching pattern rather than a filename

    :return: list of files
    """
    flattened = _flatten_nested_iterable(inputfiles)
    assert all([os.path.isfile(f) for f in flattened]), 'Not all input paths are files: {}'.format(flattened)
    assert os.path.isdir(outdir), 'Output dir is not a folder: {}'.format(outdir)
    outfiles = os.listdir(outdir)
    outfiles = fnm.filter(outfiles, filter)
    if len(outfiles) > 0:
        return [os.path.join(outdir, f) for f in outfiles]
    if posrep:
        fmt = ' '.join(flattened),
    else:
        fmt = {'inputfiles': ' '.join(flattened)}
    _ = _run_command(cmd, fmt, syscall, posrep)
    if rec:
        outfiles = recursive_collect(outdir, filter)
    else:
        outfiles = os.listdir(outdir)
        outfiles = fnm.filter(outfiles, filter)
        outfiles = [os.path.join(outdir, f) for f in outfiles]
    assert len(outfiles) > 0, 'No output files produced by command {} with filter pattern {}'.format(cmd, outputpattern)
    return outfiles


def syscall_inpair_out(inputpair, outputfile, cmd, syscall):
    """
    :param inputpair:
    :param outputfile:
    :param cmd:
    :param syscall:
    :return:
    """
    if len(inputpair) == 1:  # stumble across nested structure every now and then
        inputpair = inputpair[0]
    assert len(inputpair) == 2, 'Missing paired input: {}'.format(inputpair)
    assert all([os.path.isfile(f) for f in inputpair]), 'Not all input paths are files: {}'.format(inputpair)
    fmt = {'inputfile1': inputpair[0], 'inputfile2': inputpair[1], 'outputfile': outputfile}
    _ = _run_command(cmd, fmt, syscall)
    assert os.path.isfile(outputfile), 'Output path is not a file: {} - job failed?'.format(outputfile)
    return outputfile


def syscall_in_outpair(inputfile, outputpair, cmd, syscall):
    """
    :param inputfile:
    :param outputpair:
    :param cmd:
    :param syscall:
    :return:
    """
    if len(outputpair) == 1:
        outputpair = outputpair[0]
    assert len(outputpair) == 2, 'Missing paired output: {}'.format(outputpair)
    assert os.path.isfile(inputfile), 'Invalid path to input file: {}'.format(inputfile)
    fmt = {'inputfile': inputfile, 'outputfile1': outputpair[0], 'outputfile2': outputpair[1]}
    _ = _run_command(cmd, fmt, syscall)
    assert all([os.path.isfile(f) for f in outputpair]), 'No output files created - job failed?'
    return outputpair


JOBFUN_REGISTRY = {'raw': syscall_raw,
                   'in_out': syscall_in_out,
                   'inref_out': syscall_inref_out,
                   'in_pat': syscall_in_pat,
                   'in_out_ref': syscall_in_out_ref,
                   'ins_out': syscall_ins_out,
                   'ins_pat': syscall_ins_pat,
                   'ins_out_ref': syscall_ins_out_ref,
                   'inpair_out': syscall_inpair_out,
                   'in_outpair': syscall_in_outpair}
