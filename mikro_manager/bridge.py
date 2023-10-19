from pycromanager import Acquisition, Core, JavaObject, JavaClass
import numpy as np
from pycromanager import Studio
import xarray as xr
from mikro.api.schema import from_xarray, RepresentationFragment, ROIFragment, PositionFragment, StageFragment, create_stage, create_position, OmeroRepresentationInput, PhysicalSizeInput, ObjectiveFragment, create_objective, create_instrument, create_stage, PlaneInput, RepresentationViewInput, create_channel, ChannelFragment
import time
from koil.vars import check_cancelled
from typing import Optional, List
import datetime
import gc
import dask.array as da



class AbstractAquisition(Acquisition):
    """ Enables passing of a core object to the acquisition"""

    def __init__(self, *args, core=None, **kwargs):
        self.___core = core
        super().__init__(*args, **kwargs)


    def _create_remote_acquisition(self, **kwargs):
        core = self.___core
        acq_factory = JavaObject("org.micromanager.remote.RemoteAcquisitionFactory",
            port=self._port, args=[core])
        show_viewer = kwargs['show_display'] == True and (kwargs['directory'] is not None and kwargs['name'] is not None)

        self._remote_acq = acq_factory.create_acquisition(
            kwargs['directory'],
            kwargs['name'],
            show_viewer,
            kwargs['saving_queue_size'],
            kwargs['core_log_debug'],
        )

class MMBridge:
    """A bridge to the micro manager core"""
    core: Core 
    studio: Studio
    active_position: Optional[PositionFragment]
    active_objective:  Optional[ObjectiveFragment]
    active_channel:  Optional[ChannelFragment]

    def __init__(self) -> None:
        self.core = None
        self.studio = None
        self.objective_config = "Objective"
        self.channel_config = "Channel"

        self.auto_focus_offsets = {} # Dict of objective name to offset

        self.xy_stage_config = "XYStage"
        self.z_stage_config = "ZDrive"
        self.instrument_name_config = "So Spim"
        self.instrument_serial_config = "1234"

        self.active_position = None
        self.active_channel = None
        self.active_objective = None
        self.active_stage = None
        self.active_instrument = None
        self.started = False


    def start(self):
        self.core = Core()
        self.studio = Studio()
        self.lang = JavaClass('java.lang.System')
        self.started = True

    def on_provide(self):
        self.active_instrument = create_instrument(name=self.instrument_name_config, serial_number=self.instrument_serial_config)


    def get_affine_matrix(self, zstep=1):
        """ Gets the affine matrix of the currently active pixel size"""
        a = []
        l = self.core.get_pixel_size_affine()
        for i in range(l.size()):
            a.append(l.get(i))

        a += [0,0,zstep]
        print(a)
        return np.array(a).reshape(3,3)
    
    def get_current_position(self) -> PositionFragment:
        """ Gets the current position of the stage"""
        x = 0
        y= 0
        z = 0

        x = self.core.get_x_position()
        y = self.core.get_y_position()
        z = self.core.get_position()

        print(x, y, z)

        self.active_position = create_position(stage=self.active_stage, x=x, y=y, z=z)

        return self.active_position

    
    def get_current_objective(self):
        """Get the current objective

        Returns
        -------
        _type_
            _description_
        """
        prop = self.core.get_current_config(self.objective_config)
        self.active_objective = create_objective(serial_number=f"mmm:{prop}", name=prop, magnification=60) #TODO: Read out from config
        return self.active_objective

    def get_current_channel(self):
        """Get the current channel"""

        prop = self.core.get_current_config(self.channel_config)
        self.active_channel = create_channel(serial_number=f"mmm:{prop}", name=prop, magnification=60) #TODO: Read out from config
        return prop
    
    def snap_image(self) -> xr.DataArray:
        """Snaps an image and returns it as a numpy array

        Returns
        -------
        _type_
            _description_
        """
        self.core.snap_image()
        tagged_image = self.core.get_tagged_image()
        image_array = np.reshape(
                tagged_image.pix,
                newshape=[1, tagged_image.tags["Height"], tagged_image.tags["Width"]],
            )

        return xr.DataArray(image_array, dims=["z", "y", "x"])
    

    def move_to_position_xy(self, position: PositionFragment):
        """Moves the stage to the specified position

        """
        if self.active_position == position:
            return

        self.core.set_xy_position(position.x, position.y)
        self.active_position = position


    def set_auto_focusoffset(self, objective: ObjectiveFragment, offset: int):
        """Sets the auto focus offset

        """
        self.core.set_auto_focus_offset(offset)
        self.set_auto_focusoffset



    def ensure_focus(self):

        dev = self.core.get_auto_focus_device()
        self.core.set_property(dev, "FocusMaintenance", "On")
        while not self.core.is_continuous_focus_locked():
            print("Not locked, sleeping")
            check_cancelled()
            time.sleep(0.01)


    def detach_pfs(self):
        dev = self.core.get_auto_focus_device()
        self.core.set_property(dev, "FocusMaintenance", "Off")


    def set_objective(self, objective: ObjectiveFragment, ensure_focus: bool = True) -> None:
        """MM Set Objective

        Set the active objective"""
        if self.active_objective == objective:
            return

        self.core.set_config("Objective", objective.name)
         
        if ensure_focus:
            assert objective.name in self.auto_focus_offsets, "Please set an autofocus first before using this objective"
       
            if objective.name in self.auto_focus_offsets:
                self.core.set_auto_focus_offset(self.auto_focus_offsets[objective.name])
                self.ensure_focus()

        self.active_objective = objective

    def set_channel(self, channel: Optional[ChannelFragment]) -> None:
        """MM Set Channel

        Set the active channel"""

        global current_channel
        self.core.set_config("Channel", channel.name)
        current_channel = channel

    
    def acquire_2d(self, position: Optional[PositionFragment], objective: Optional[ObjectiveFragment], channel: Optional[ChannelFragment]) -> RepresentationFragment:
        """ Acquire 2D (with offset)

        Acquire a 2D snap of an image  (with offset)


        """

        position, objective, channel = self.ensure_environment(position, objective, channel)

        self.core.snap_image()

        pixel_size = self.core.get_pixel_size_um()
        assert pixel_size, f"Pixel size was not set for this specific objective {objective}, please set it!"


        t = self.get_affine_matrix()
        print(t)

        omero = OmeroRepresentationInput(
                    positions=[position],
                    acquisitionDate=datetime.datetime.now(),
                    physicalSize=PhysicalSizeInput(
                        x=pixel_size, y=pixel_size, z=pixel_size, c=1, t=1
                    ),
                    affineTransformation=t,
                    objective=objective,
                )


        tagged_image = self.core.get_tagged_image()
        image_array = np.reshape(
                tagged_image.pix,
                newshape=[1, tagged_image.tags["Height"], tagged_image.tags["Width"]],
            )

        self.core.clear_circular_buffer()


    def ensure_environment(self, position: Optional[PositionFragment], objective: Optional[ObjectiveFragment], channel: Optional[ChannelFragment]):
        if position:
            #assert current_stage.id == position.stage.id, "Position was not create in current stage, please create a new position."
            self.move_to(position)
        else:
            position = self.get_current_position()


        if objective:
            self.set_objective(objective)
        else:
            objective = self.get_current_objective()
            

        if channel:
            self.set_channel(channel)
        else:
            channel = self.get_current_channel()

        self.ensure_focus()
        return position, objective, channel


    


    def acquire_3d(self, position: Optional[PositionFragment], objective: Optional[ObjectiveFragment], channel: Optional[ChannelFragment], z_steps: int = 2, z_step: float = 0.3, crop_physical_height: Optional[float] = None, crop_physical_width: Optional[float] = None) -> RepresentationFragment:
        """Acquire Stack

        acquire a 3d stack

        Args:
            position (Optional[PositionFragment]): The postion
            objective (Optional[ObjectiveFragment]): The objective to use
            channel (Optional[ChannelFragment]): The channel to use
            auto_focus_offset (Optional[int]): A temporaty autofocus offset
            z_steps (int, optional): The amount of zsteps (around midpoint). Defaults to 2.
            z_step (float, optional): The z-step to take in um. Defaults to 0.3

        Returns:
            RepresentationFragment: The image
        """    """"""

        position, objective, channel = self.ensure_environment(position, objective, channel)

        pixel_size = self.core.get_pixel_size_um()
        assert pixel_size, f"Pixel size was not set for this specific objective {objective}, please set it!"
        assert z_steps * z_step < 100, "Unsafe for current working distqnce"


        width = None
        height = None

        if crop_physical_width:
            width =  int(crop_physical_width / pixel_size)

        if crop_physical_height:
            height = int(crop_physical_height / pixel_size)

        if width or height:
            camera_width = self.core.get_image_width()
            camera_height = self.core.get_image_width()
            assert height is None or height <= camera_height, f"Cannot acquire a roi of {crop_physical_height} µm height with this camera. The field of with this camera and objective is to small"
            assert width is None or  width <= camera_width, f"Cannot acquire a roi of {crop_physical_width} µm width with this camera. The field of with this camera and objective is to small"

            height = height or camera_height
            width = width or camera_width
            top_left_y = (camera_height - height ) // 2
            top_left_x = (camera_width - width) // 2

            self.core.set_roi(top_left_x, top_left_y, width, height)





        z_pixel_size = z_step

        t = self.get_affine_matrix(zstep=z_pixel_size)
        images = []
        views = []
        planes = []

        # z stack parameters
        half_size =  ( z_pixel_size * z_steps ) / 2
        z_start = -half_size
        z_end = half_size

        z_sequence = np.linspace(z_start, z_end, z_steps)
        print(z_sequence)



        # setup z stage
        z_stage = self.core.get_focus_device()
        start_position = self.core.get_position(z_stage)
        z_pos = self.core.get_position(z_stage)
        self.ensure_focus()

        # Add relative positions
        z_sequence += z_pos
        print(z_sequence)

        views.append(RepresentationViewInput(cMin=0, cMax=0, channel=current_channel))


        self.acquire_2d()

        def append(image, metadata):
            print(image, metadata)
            images.append(image)
            planes.append(PlaneInput(z=metadata.get("Axes", {}).get("z", 0), exposureTime=metadata.get("Exposure"), deltaT=metadata.get("ElapsedTime-ms")))
            views.append(RepresentationViewInput(zMin=metadata.get("Axes", {}).get("z", 0), zMax=metadata.get("Axes", {}).get("z", 0)))

            return image, metadata


        with AbstractAquisition(core=self.core, directory=None, name=None,
                        show_display=False,
                        image_process_fn = append) as acq:
            events = []
            for index, z_um in enumerate(z_sequence):
                events.append(
                    {
                        "axes": {"subset": 0, "z": index},
                        "z": z_um,
                    }
                )
            
            acq.acquire(events if events else [{
                        "axes": {"subset": 0, "z": 0},
                        "z": z_pos,
                    }])
            

        # Memory Leak prevention (pycromanager leaks memory, this at least partially remedies it)
        del acq
        gc.collect()
        self.lang.gc()
        self.core.clear_circular_buffer()

        # Reset ROI
        if width or height:
            self.core.clear_roi()


        # Reset z stage
        self.core.set_position(start_position)
        self.ensure_focus()
        data = da.stack(
            images, axis=0
        )


        omero = OmeroRepresentationInput(
                positions=[position],
                acquisitionDate=datetime.datetime.now(),
                physicalSize=PhysicalSizeInput(
                    x=pixel_size, y=pixel_size, z=z_pixel_size, c=1, t=1
                ),
                planes=planes,
                affineTransformation=t,
                objective=objective,
            )

        return from_xarray(xr.DataArray(data, dims=["z", "y", "x"]), name="Test Image", omero=omero, views=views)

    
    def retrieve_positions(self) -> List[PositionFragment]:
        """MM Retrieve Positions

        retrieves positions within a stage context established
        right here
        """
        self.active_stage = create_stage(name="Latest Stage",  tags=["default"], instrument=self.active_instrument) 

        pm = self.studio.positions()
        pos_list = pm.get_position_list()
        positions = []

        for idx in range(pos_list.get_number_of_positions()):
            pos = pos_list.get_position(idx)
            pos_name = pos.get_label()

            x = None
            y = None
            z = None


            for ipos in range (pos.size()):
                stage_pos = pos.get(ipos)
                name = stage_pos.get_stage_device_label()
                if name == "XYStage":
                    x = stage_pos.x
                    y = stage_pos.y
                if name == "ZDrive":
                    z = stage_pos.x
            
            positions.append(create_position(self.active_stage, x, y, z, name=pos_name))

        return positions

    def retrieve_objectives(self) -> List[ObjectiveFragment]:
        """MM Retrieve Objectives

        retrieves Objectives that are installed in this microscope
        """

        t = self.core.get_available_configs(self.objective_config)
        objectives = []

        for i in range(t.size()):
            objectives.append(create_objective(serial_number=f"mmm:{t.get(i)}", name=t.get(i), magnification=60))

        return objectives
    
    def retrieve_channels(self) -> List[ChannelFragment]:
        """MM Retrieve Channels

        retrieves Channels that are installed in this microscope
        """

        t = self.core.get_available_configs(self.channel_config)
        channels = []

        for i in range(t.size()):
            channels.append(create_channel(name=t.get(i)))
