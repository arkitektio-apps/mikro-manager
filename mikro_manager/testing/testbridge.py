from pycromanager import Acquisition, Core, JavaObject, JavaClass
import numpy as np
from pycromanager import Studio
import xarray as xr
from mikro.api.schema import from_xarray, RepresentationFragment, ROIFragment, PositionFragment, StageFragment, create_stage, create_position, OmeroRepresentationInput, PhysicalSizeInput, ObjectiveFragment, create_objective, get_objective, create_instrument, create_stage, PlaneInput, RepresentationViewInput, create_channel, ChannelFragment
import time
from koil.vars import check_cancelled
from typing import Optional, List
import datetime
import gc
import dask.array as da
from pydantic import BaseModel
from typing import Dict


class TestBridge(BaseModel):
    """A bridge to the micro manager core"""

    config_values: Dict[str, List[str]] = {}

    _started = False



    def start(self):
        self._started = True

    def on_provide(self):
        pass


    def get_config_values(self, config_name: str) -> List[str]:
        return self.config_values[config_name]
    

    def get_config_names(self) -> List[str]:
        return list(self.config_values.keys())