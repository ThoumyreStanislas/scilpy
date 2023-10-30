# -*- coding: utf-8 -*-

import numpy as np


def _rescale_intensity(val, slope, in_max, bc_max):
    """
    Rescale an intensity value given a scaling factor.
    This scaling factor ensures that the intensity
    range before and after correction is the same.

    Parameters
    ----------
    val: float
         Value to be scaled
    scale: float
         Scaling factor to be applied
    in_max: float
         Max possible value
    bc_max: float
         Max value in the bias correction value range

    Returns
    -------
    rescaled_value: float
         Bias field corrected value scaled by the slope
         of the data
    """

    return in_max - slope * (bc_max - val)


# https://github.com/stnava/ANTs/blob/master/Examples/N4BiasFieldCorrection.cxx
def rescale_dwi(in_data, bc_data):
    """
    Apply N4 Bias Field Correction to a DWI volume.
    bc stands for bias correction. The code comes
    from the C++ ANTS implmentation.

    Parameters
    ----------
    in_data: ndarray (x, y, z, ndwi)
         Input DWI volume 4-dimensional data.
    bc_data: ndarray (x, y, z, ndwi)
         Bias field correction volume estimated from ANTS
         Copied for every dimension of the DWI 4-th dimension

    Returns
    -------
    bc_data: ndarray (x, y, z, ndwi)
         Bias field corrected DWI volume
    """

    in_min = np.amin(in_data)
    in_max = np.amax(in_data)
    bc_min = np.amin(bc_data)
    bc_max = np.amax(bc_data)

    slope = (in_max - in_min) / (bc_max - bc_min)

    chunk = np.arange(0, len(in_data), 100000)
    chunk = np.append(chunk, len(in_data))
    for i in range(len(chunk)-1):
        nz_bc_data = bc_data[chunk[i]:chunk[i+1]]
        rescale_func = np.vectorize(_rescale_intensity, otypes=[np.float32])

        rescaled_data = rescale_func(nz_bc_data, slope, in_max, bc_max)
        bc_data[chunk[i]:chunk[i+1]] = rescaled_data

    return bc_data