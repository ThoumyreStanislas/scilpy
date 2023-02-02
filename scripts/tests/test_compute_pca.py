#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tempfile

from scilpy.io.fetcher import get_testing_files_dict, fetch_data, get_home


# If they already exist, this only takes 5 seconds (check md5sum)
fetch_data(get_testing_files_dict(), keys=['connectivity.zip'])
tmp_dir = tempfile.TemporaryDirectory()


def test_help_option(script_runner):
    ret = script_runner.run('scil_compute_pca.py',
                            '--help')
    assert ret.success


def test_execution_pca(script_runner):
    os.chdir(os.path.expanduser(tmp_dir.name))
    afd_max = os.path.join(get_home(), 'connectivity',
                           'afd_max.npy')
    length = os.path.join(get_home(), 'connectivity',
                          'len.npy')
    sc = os.path.join(get_home(), 'connectivity',
                      'sc.npy')
    vol = os.path.join(get_home(), 'connectivity',
                       'vol.npy')
    sim = os.path.join(get_home(), 'connectivity',
                       'sim.npy')
    ret = script_runner.run('scil_compute_pca.py', './', './', '--metrics', afd_max,
                            length, sc, vol, sim)
    assert ret.success
