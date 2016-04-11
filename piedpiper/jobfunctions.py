# coding=utf-8

"""
Module wrapping job functions suitable for Ruffus pipelines
The functions will be passed to the pipeline module via the
SyscallInterface object
Design-wise, this appears to be a bit quirky (?), but at least one can
avoid importing a module with generic inputfile -> outputfile job functions
in each and every pipeline script
"""

import os as os
import fnmatch as fnm


def _normalize_job_output(output):
    """
    :param output:
    :return:
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
    :param out:
    :param err:
    :return:
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


def syscall_raw(cmd, syscall):
    """
    :param cmd:
    :param syscall:
    :return:
    """
    out, err = syscall(cmd)
    out, err = _check_job(out, err)
    return


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
        cmd = cmd.format(*(inputfile, outputfile))
    else:
        files = {'inputfile': inputfile, 'outputfile': outputfile}
        cmd = cmd.format(**files)
    out, err = syscall(cmd)
    out, err = _check_job(out, err)
    assert os.path.isfile(outputfile), 'Output path is not a file: {} - job failed?'.format(outputfile)
    return outputfile


def syscall_in_pat(inputfile, outputfiles, outdir, filter, cmd, syscall, posrep=False):
    """ System call for cases where a single input file is split
    into multiple output files (number determined at runtime), hence
    outputfiles represents a matching pattern rather than a filename

    :return: list of files
    """
    assert os.path.isfile(inputfile), 'Input path is not a file: {}'.format(inputfile)
    if posrep:
        cmd = cmd.format(*(inputfile,))
    else:
        cmd = cmd.format(**{'inputfile': inputfile})
    out, err = syscall(cmd)
    out, err = _check_job(out, err)
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
    cmd = cmd.format(**fmt)
    out, err = syscall(cmd)
    out, err = _check_job(out, err)
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
    assert all([os.path.isfile(f) for f in inputfiles]), 'Invalid path to input file(s): {}'.format(inputfiles)
    assert os.path.isfile(reference), 'Invalid path to reference file: {}'.format(reference)
    fmt = {'inputfiles': ' '.join(inputfiles), 'outputfile': outputfile, 'referencefile': reference}
    cmd = cmd.format(**fmt)
    out, err = syscall(cmd)
    out, err = _check_job(out, err)
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
    cmd = cmd.format(**fmt)
    out, err = syscall(cmd)
    out, err = _check_job(out, err)
    assert os.path.isfile(outputfile), 'Output path is not a file: {} - job failed?'.format(outputfile)
    return outputfile


def syscall_ins_out(inputfiles, outputfile, cmd, syscall, posrep=False):
    """ Merge/join job, several input files create a single output file
    :param inputfiles:
    :param outputfile:
    :return:
    """
    assert all([os.path.isfile(f) for f in inputfiles]), 'Not all input paths are files: {}'.format(inputfiles)
    assert outputfile, 'Received no output file'
    inputfiles = ' '.join(inputfiles)
    if posrep:
        cmd = cmd.format(*(inputfiles, outputfile))
    else:
        cmd = cmd.format(**{'inputfiles': inputfiles, 'outputfile': outputfile})
    out, err = syscall(cmd)
    out, err = _check_job(out, err)
    assert os.path.isfile(outputfile), 'Output path is not a file: {} - job failed?'.format(outputfile)
    return outputfile


def syscall_ins_pat(inputfiles, outputpattern, outdir, filter, cmd, syscall, posrep=False):
    """ System call for cases where a set of input files is split
    into multiple output files (number determined at runtime), hence
    outputfiles represents a matching pattern rather than a filename

    :return: list of files
    """
    assert all([os.path.isfile(f) for f in inputfiles]), 'Not all input paths are files: {}'.format(inputfiles)
    assert os.path.isdir(outdir), 'Output dir is not a folder: {}'.format(outdir)
    outfiles = os.listdir(outdir)
    outfiles = fnm.filter(outfiles, filter)
    if len(outfiles) > 0:
        return [os.path.join(outdir, f) for f in outfiles]
    if posrep:
        cmd = cmd.format(*(str(inputfiles),))
    else:
        cmd = cmd.format(**{'inputfiles': str(inputfiles)})
    out, err = syscall(cmd)
    out, err = _check_job(out, err)
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
    if len(inputpair) == 1:
        inputpair = inputpair[0]
    assert len(inputpair) == 2, 'Missing paired input: {}'.format(inputpair)
    assert all([os.path.isfile(f) for f in inputpair]), 'Not all input paths are files: {}'.format(inputpair)
    cmd = cmd.format(**{'inputfile1': inputpair[0], 'inputfile2': inputpair[1], 'outputfile': outputfile})
    out, err = syscall(cmd)
    out, err = _check_job(out, err)
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
    cmd = cmd.format(**{'inputfile': inputfile, 'outputfile1': outputpair[0], 'outputfile2': outputpair[1]})
    out, err = syscall(cmd)
    out, err = _check_job(out, err)
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
