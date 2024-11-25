#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Estimates the per-voxel spatial density of a set of fibertubes. In other
words, how much space is occupied by fibertubes and how much is emptiness.

Works by building a binary mask segmenting voxels that contain at least
a single fibertube. Then, valid voxels are finely sampled and we count the
number of samples that landed within a fibertube. For each voxel, this
number is then divided by its total amount of samples.

See also:
    - docs/source/documentation/fibertube_tracking.rst
"""

import os
import json
import nibabel as nib
import argparse
import logging
import numpy as np

from scilpy.io.streamlines import load_tractogram_with_reference
from scilpy.tractanalysis.fibertube_scoring import fibertube_density
from scilpy.io.utils import (assert_inputs_exist,
                             assert_outputs_exist,
                             add_overwrite_arg,
                             add_verbose_arg,
                             add_json_args)


def _build_arg_parser():
    p = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=__doc__)

    p.add_argument('in_fibertubes',
                   help='Path to the tractogram (must be .trk) file \n'
                        'containing fibertubes. They must be: \n'
                        '1- Void of any collision. \n'
                        '2- With their respective diameter saved \n'
                        'as data_per_streamline. \n'
                        'For both of these requirements, see \n'
                        'scil_tractogram_filter_collisions.py.')

    p.add_argument('out_density', type=str,
                   help='Path of the output density image file')

    p.add_argument('--out_density_measures', default=None, type=str,
                   help='Path of the output file containing central \n'
                        'tendency measures. (Must be .json)')

    add_overwrite_arg(p)
    add_verbose_arg(p)
    add_json_args(p)

    return p


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    logging.getLogger().setLevel(logging.getLevelName(args.verbose))
    logging.getLogger('numba').setLevel(logging.WARNING)

    if os.path.splitext(args.in_fibertubes)[1] != '.trk':
        parser.error('Invalid input streamline file format (must be trk):' +
                     '{0}'.format(args.in_fibertubes))

    if args.out_density_measures:
        if os.path.splitext(args.out_density_measures)[1] != '.json':
            parser.error('Invalid output file format (must be json): {0}'
                         .format(args.out_density_measures))

    assert_inputs_exist(parser, args.in_fibertubes)
    assert_outputs_exist(parser, args, [args.out_density],
                         [args.out_density_measures])

    logging.debug('Loading tractogram & diameters')
    sft = load_tractogram_with_reference(parser, args, args.in_fibertubes)
    sft.to_voxmm()
    sft.to_center()

    if "diameters" not in sft.data_per_streamline:
        parser.error('No diameters found as data per streamline on ' +
                     args.in_fibertubes)

    logging.debug('Computing fibertube density')
    density_3D, density_flat = fibertube_density(sft, 10,
                                                 args.verbose == 'WARNING')

    logging.debug('Saving density image')
    header = nib.nifti1.Nifti1Header()
    extra = {
        'affine': sft.affine,
        'dimensions': sft.dimensions,
        'voxel_size': sft.voxel_sizes[0],
        'voxel_order': "RAS"
    }
    density_img = nib.nifti1.Nifti1Image(density_3D, sft.affine, header,
                                         extra)
    nib.save(density_img, args.out_density)

    if args.out_density_measures:
        density_measures = {
            'mean': np.mean(density_flat),
            'median': np.median(density_flat),
            'max': np.max(density_flat),
            'min': np.min(density_flat),
        }
        with open(args.out_density_measures, 'w') as file:
            json.dump(density_measures, file, indent=args.indent,
                      sort_keys=args.sort_keys)


if __name__ == "__main__":
    main()
