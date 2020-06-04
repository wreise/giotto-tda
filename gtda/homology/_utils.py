""" Utilities function for persistent homology."""
# License: GNU AGPLv3

import numpy as np
from joblib import Parallel, delayed


def _pad_diagram(Xd, homology_dimensions, max_n_points, min_values):
    for dim in homology_dimensions:
        n_points = len(Xd[dim])
        n_points_to_pad = max_n_points[dim] - n_points
        if n_points == 0 and n_points_to_pad == 0:
            n_points_to_pad = 1

        if n_points_to_pad > 0:
            padding = ((0, n_points_to_pad), (0, 0))
            Xd[dim] = np.pad(Xd[dim], padding, 'constant')
            Xd[dim][-n_points_to_pad:, :] = \
                [min_values[dim], min_values[dim]]

    # Add dimension as the third elements of each (b, d) tuple
    Xd = [np.hstack([Xd[dim], dim * np.ones((Xd[dim].shape[0], 1),
                                            dtype=Xd[dim].dtype)])
          for dim in homology_dimensions]

    Xd = np.vstack([Xd[dim] for dim in homology_dimensions])

    return Xd


def _postprocess_diagrams(Xt, homology_dimensions, infinity_values, n_jobs):
    # Replacing np.inf with infinity_values
    Xt = [{dim: np.nan_to_num(Xt[i][dim], posinf=infinity_values)
          for dim in homology_dimensions}
          for i in range(len(Xt))]

    # Removing points whose birth is higher than their death
    Xt = [{dim: Xt[i][dim][Xt[i][dim][:, 0] < Xt[i][dim][:, 1]]
          for dim in homology_dimensions}
          for i in range(len(Xt))]

    max_n_points = {dim: max(1, np.max([Xt[i][dim].shape[0]
                                        for i in range(len(Xt))]))
                    for dim in homology_dimensions}
    min_values = {dim: min([np.min(Xt[i][dim][:, 0]) if Xt[i][dim].size else
                            np.inf for i in range(len(Xt))])
                  for dim in homology_dimensions}
    min_values = {dim: min_values[dim] if min_values[dim] != np.inf else 0
                  for dim in homology_dimensions}
    Xt = Parallel(n_jobs=n_jobs)(delayed(_pad_diagram)(
        Xt[i], homology_dimensions, max_n_points, min_values)
                                      for i in range(len(Xt)))
    Xt = np.stack(Xt)
    return Xt
