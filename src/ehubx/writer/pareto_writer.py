"""Pareto front writer module"""

import os
from enum import Enum
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import pandas as pd

from ehubx.core import exceptions, logging
from ehubx.data.pareto_front_data import ParetoFront


# ------------ #
# Image format #
# ------------ #
class ImageFormat(Enum):
    """
    Format for saved Pareto front images
    """

    EPS = "eps"
    PNG = "png"


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "writ/pareto"
"""Module string for the Pareto writer module for logging purposes"""

COL_PARETOID: str = "pareto_id"
"""Name for Pareto point ids in the Pareto front csv file"""

FILENAME_PARETOCSV: str = "pareto_front.csv"
"""Filename of the pareto front csv file for multi-objective solves"""

FILENAME_PARETOIMG: str = "pareto_front"
"""Filename of the pareto front image for multi-objective solves"""


def save_pareto_front(
    pareto_front: ParetoFront,
    subdir_path: str,
    image_format: ImageFormat = ImageFormat.PNG,
) -> None:
    """
    Saves a Pareto front to an image file and its data to a csv file

    :param pareto_front: Pareto front to be saved
    :type pareto_front: ParetoFront
    :param subdir_path: Directory where the image and the csv file should be
        placed
    :type subdir_path: str
    :param image_format: Format for the Pareto front image, defaults to
        ImageFormat.PNG
    :type image_format: ImageFormat, optional
    """
    # Check subdir_path
    if subdir_path is not None:
        if not os.path.isdir(subdir_path):
            raise exceptions.EhubXException(
                f"Results subdirectory path {subdir_path} does not exist",
                module=LOG_MODULE_STR,
            )
    # Save pareto points to csv
    pp_struct: Dict[str, Any] = {
        COL_PARETOID: [],
        pareto_front.obj_key_1: [],
        pareto_front.obj_key_2: [],
    }
    for pareto_id in pareto_front.ids:
        pp_struct[COL_PARETOID].append(pareto_id)
        point = pareto_front.get_point(pareto_id)
        pp_struct[pareto_front.obj_key_1].append(point[0])
        pp_struct[pareto_front.obj_key_2].append(point[1])
    df_pareto = pd.DataFrame(pp_struct)
    pareto_csv_path = os.path.join(subdir_path, FILENAME_PARETOCSV)
    df_pareto.to_csv(pareto_csv_path, index=False)
    logging.log(f"Pareto front data saved to {pareto_csv_path}", module=LOG_MODULE_STR)
    # Plot Pareto front
    plt.figure()
    obj_vals_1: List[float] = []
    obj_vals_2: List[float] = []
    for pareto_id in pareto_front.ids:
        (obj_val_1, obj_val_2) = pareto_front.get_point(pareto_id)
        obj_vals_1.append(obj_val_1)
        obj_vals_2.append(obj_val_2)
    if len(pareto_front.ids) > 1:
        plt.scatter(obj_vals_1, obj_vals_2, label="Pareto front", color="coral")
    plt.plot(obj_vals_1, obj_vals_2, marker="o", color="darkred", markersize=10)
    plt.title("Pareto front")
    plt.xlabel(pareto_front.obj_key_1)
    plt.ylabel(pareto_front.obj_key_2)
    pareto_img_path = os.path.join(subdir_path, FILENAME_PARETOIMG)
    pareto_img_path += f".{image_format.value}"
    plt.savefig(pareto_img_path)
    logging.log(f"Pareto front image saved to {pareto_img_path}", module=LOG_MODULE_STR)
