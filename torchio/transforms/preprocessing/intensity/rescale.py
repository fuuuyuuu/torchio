import warnings
from typing import Tuple, Union, Callable
import torch
import numpy as np
from ....torchio import DATA, TypeCallable
from . import NormalizationTransform


class Rescale(NormalizationTransform):
    """Rescale intensity values to a certain range.

    Args:
        out_min_max: Range :math:`(n_{min}, n_{max})` of output intensities.
        percentiles: Percentile values of the input image that will be mapped
            to :math:`(n_{min}, n_{max})`. They can be used for contrast
            stretching, as in `this scikit-image example`_. For example,
            Isensee et al. use ``(0.05, 99.5)`` in their `nn-UNet paper`_.
        masking_method: See
            :py:class:`~torchio.transforms.preprocessing.normalization_transform.NormalizationTransform`.

    .. _this scikit-image example: https://scikit-image.org/docs/dev/auto_examples/color_exposure/plot_equalize.html#sphx-glr-auto-examples-color-exposure-plot-equalize-py
    .. _nn-UNet paper: https://arxiv.org/abs/1809.10486
    """
    def __init__(
            self,
            out_min_max: Tuple[float, float],
            percentiles: Tuple[int, int] = (0, 100),
            masking_method: Union[str, TypeCallable, None] = None,
            ):
        super().__init__(masking_method=masking_method)
        self.out_min, self.out_max = out_min_max
        self.percentiles = percentiles

    def apply_normalization(
            self,
            sample: dict,
            image_name: str,
            mask: torch.Tensor,
            ) -> None:
        image_dict = sample[image_name]
        image_dict[DATA] = self.rescale(image_dict[DATA], mask, image_name)

    def rescale(
            self,
            tensor: torch.Tensor,
            mask: torch.Tensor,
            image_name: str,
            ) -> torch.Tensor:
        array = tensor.numpy()
        mask = mask.numpy()
        values = array[mask]
        cutoff = np.percentile(values, self.percentiles)
        np.clip(array, *cutoff, out=array)
        array -= array.min()  # [0, max]
        array_max = array.max()
        if array_max == 0:
            message = (
                f'Rescaling image "{image_name}" not possible'
                ' due to division by zero'
            )
            warnings.warn(message)
            return tensor
        array /= array.max()  # [0, 1]
        out_range = self.out_max - self.out_min
        array *= out_range  # [0, out_range]
        array += self.out_min  # [out_min, out_max]
        return torch.from_numpy(array)
