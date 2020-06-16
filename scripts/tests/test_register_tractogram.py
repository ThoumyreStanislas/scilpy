#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tempfile

from scilpy.io.fetcher import get_testing_files_dict, fetch_data, get_home


# If they already exist, this only takes 5 seconds (check md5sum)
fetch_data(get_testing_files_dict(), keys=['bundles.zip'])
tmp_dir = tempfile.TemporaryDirectory()


def test_help_option(script_runner):
    ret = script_runner.run('scil_register_tractogram.py', '--help')
    assert ret.success


def test_execution_bundles(script_runner):
    os.chdir(os.path.expanduser(tmp_dir.name))
    input_moving = os.path.join(get_home(), 'bundles',
                                'bundle_0_reco.tck')
    input_static = os.path.join(get_home(), 'bundles', 'voting_results',
                                'bundle_0.trk')
    input_ref = os.path.join(get_home(), 'bundles',
                             'avg_dwi.nii.gz')
    ret = script_runner.run('scil_register_tractogram.py', input_moving,
                            input_static, '--only_rigid',
                            '--moving_tractogram_ref', input_ref)
    assert ret.success
