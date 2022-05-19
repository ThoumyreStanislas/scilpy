#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to resample a tractogram to a set number of streamlines.
Default behavior:
- IF number of requested streamlines is lower than streamline count: DOWNSAMPLE
- IF number of requested streamlines is higher than streamline count: UPSAMPLE
To prevent upsample if not desired use --never_upsample.

Can be useful to build training sets for machine learning algorithms, to
upsample under-represented bundles or downsample over-represented bundles.

Works by either selecting a subset of streamlines or by generating new
streamlines by adding gaussian noise to existing ones.

Includes smoothing to compensate for the noisiness of new streamlines
generated by the process.

Example usage:
$ scil_resample_tractogram.py input.trk 1000 output.trk \
--point_wise_std 0.5 --spline 5 10 --keep_invalid_streamlines
$ scil_visualize_bundles.py output.trk --local_coloring --width=0.1
"""

import argparse
import logging

from dipy.io.streamline import save_tractogram

from scilpy.io.streamlines import load_tractogram_with_reference
from scilpy.io.utils import (add_overwrite_arg, add_reference_arg,
                             add_verbose_arg,
                             assert_inputs_exist,
                             assert_outputs_exist)

from scilpy.tracking.tools import get_subset_streamlines
from scilpy.utils.streamlines import upsample_tractogram


def _build_arg_parser():
    p = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                description=__doc__)

    p.add_argument('in_tractogram',
                   help='Input tractography file.')
    p.add_argument('nb_streamlines', type=int,
                   help='Number of streamlines to resample the tractogram to.')
    p.add_argument('out_tractogram',
                   help='Output tractography file.')
    std_group = p.add_mutually_exclusive_group()
    std_group.add_argument('--point_wise_std', type=float,
                           help='Noise to add to existing streamlines\'' +
                                ' points to generate new ones.')
    std_group.add_argument('--streamline_wise_std', type=float,
                           help='Noise to add to existing whole' +
                                ' streamlines to generate new ones.')

    sub_p = p.add_mutually_exclusive_group()
    sub_p.add_argument('--gaussian', metavar='SIGMA', type=int,
                       help='Sigma for smoothing. Use the value of surronding'
                            ' X,Y,Z points on the streamline to blur the'
                            ' streamlines.\nA good sigma choice would be '
                            'around 5.')
    sub_p.add_argument('--spline', nargs=2, metavar=('SIGMA', 'NB_CTRL_POINT'),
                       type=int,
                       help='Sigma for smoothing. Model each streamline as a '
                            'spline.\nA good sigma choice would be around 5 '
                            'and control point around 10.')

    p.add_argument('--never_upsample', action='store_true',
                   help='Make sure to never upsample a tractogram.\n'
                        'Useful when downsample batch of files using bash.')
    p.add_argument('--keep_invalid_streamlines', action='store_true',
                   help='Keep invalid newly generated streamlines that may ' +
                        'go out of the bounding box.')
    p.add_argument('--seed', default=None, type=int,
                   help='Use a specific random seed for the resampling.')
    add_reference_arg(p)
    add_overwrite_arg(p)
    add_verbose_arg(p)

    return p


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    if (args.point_wise_std is not None and args.point_wise_std <= 0) or \
            (args.streamline_wise_std is not None and
             args.streamline_wise_std <= 0):
        parser.error('STD needs to be above 0.')

    assert_inputs_exist(parser, args.in_tractogram)
    assert_outputs_exist(parser, args, args.out_tractogram)

    log_level = logging.WARNING
    if args.verbose:
        log_level = logging.DEBUG
    logging.basicConfig(level=log_level)

    sft = load_tractogram_with_reference(parser, args, args.in_tractogram)
    original_number = len(sft.streamlines)
    
    if args.never_upsample and args.nb_streamlines > original_number:
        args.nb_streamlines = original_number

    if args.nb_streamlines > original_number:
        # Check is done here because it is not required if downsampling
        if not args.point_wise_std and not args.streamline_wise_std:
            parser.error("one of the arguments --point_wise_std " +
                         "--streamline_wise_std is required")
        sft = upsample_tractogram(
            sft, args.nb_streamlines,
            args.point_wise_std, args.streamline_wise_std,
            args.gaussian, args.spline, args.seed)
    elif args.nb_streamlines < original_number:
        sft = get_subset_streamlines(sft, args.nb_streamlines, args.seed)

    if not args.keep_invalid_streamlines:
        sft.remove_invalid_streamlines()
    save_tractogram(sft, args.out_tractogram,
                    bbox_valid_check=not args.keep_invalid_streamlines)


if __name__ == "__main__":
    main()