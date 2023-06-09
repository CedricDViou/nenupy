#! /usr/bin/python3
# -*- coding: utf-8 -*-


r"""
    *******
    Dynspec
    *******

    :mod:`~nenupy.undysputed.Dynspec` is the module designed to
    read and analyze *UnDySPuTeD* DynSpec high-rate data. It
    benefits from `Dask <https://docs.dask.org/en/latest/>`_, with
    the possibility of reading and applying complex pipelines
    to larger-than-memory data sets.
    It replaces the original `nenupy-tf <https://github.com/AlanLoh/nenupy-tf>`_
    module.

    .. note::
        `nenupy` logger could be activated at will to enhance the verbosity:

        >>> import logging
        >>> logging.getLogger('nenupy').setLevel(logging.INFO)

    UnDySPuTeD receiver
    -------------------

    *UnDySPuTeD* (stands for Unified Dynamic Spectrum Pulsar and
    Time Domain receiver) is the receiver of the NenuFAR
    beamformer mode, fed by the (up-to-)96 core Mini-Arrays (2
    polarizations) from the *LANewBa* backend. 

    DynSpec data
    ------------

    The raw data flow from *LANewBa* consists of 195312.5 pairs
    of complex X and Y values per second per beamlet. These data
    are downsampled in channels per subband (of 195.3125 kHz)
    numbered from 16 to 2048 channels, ``fftlen``, (to achieve a
    frequency resolution of :math:`\delta \nu = 12 - 0.1\, \rm{kHz}`
    respectively). After computation of cross and auto-correlations,
    the data are downsampled again in time, integrating from 4 to 1024
    spectra, ``nfft2int`` (implying a time resolution :math:`195312.5^{-1} \times \rm{fftlen} \times \rm{fft2int}`,
    :math:`\delta t = 0.3 - 83.9\, \rm{ms}`).

    .. seealso::
        `DynSpec data product <https://nenufar.obs-nancay.fr/en/astronomer/#data-products>`_

    DynSpec data files
    ------------------

    Each NenuFAR/*UnDySPuTeD*/DynSpec observation results in the
    production of several proprietary formatted files (``'*.spectra'``),
    each corresponding to an individual lane of the *UnDySPuTeD* receiver.
    Depending on the observation configuration, the bandwidth and/or
    the different observed beams (i.e., beamforming in different sky
    directions) can be spread accross these files.

    The class :class:`~nenupy.undysputed.dynspec.Dynspec` offers
    the possibility to read and analyze all these observation files
    at once, through an API aimed at minimizing user interaction
    over complicated settings.
    
    For the purpose of the following 'how-to' guide, a 1h-observation
    of the famous pulsar `PSR B1919+21 <https://en.wikipedia.org/wiki/PSR_B1919%2B21>`_
    is analyzed. :mod:`~nenupy.undysputed.dynspec.Dynspec` needs
    first to be imported, as well as :mod:`~astropy.units` in order
    to use physcial units (to avoid mistakes).
    Attribute :attr:`~nenupy.undysputed.dynspec.Dynspec.lanefiles`
    is filled with a `list` of all the available lane files (up to four)
    in order to create ``ds``, an instance of
    :class:`~nenupy.undysputed.dynspec.Dynspec`:

    >>> from nenupy.undysputed import Dynspec
    >>> import astropy.units as u
    >>> ds = Dynspec(
            lanefiles=[
                'B1919+21_TRACKING_20200214_090835_0.spectra',
                'B1919+21_TRACKING_20200214_090835_1.spectra'
            ]
        )
    
    .. note::
        :attr:`~nenupy.undysputed.dynspec.Dynspec.lanefiles` must contain
        files related to one specific observation (otherwise, a ``ValueError``
        is raised). It can be practical to automatically find all
        *DynSpec* files if they are stored within an observation folder:

        >>> from glob import glob
        >>> from os.path import join
        >>> obs_path = '/path/to/observation'
        >>> dynspec_files = glob(
                join(obs_path, '*.spectra')
            )

        and then filling in :attr:`~nenupy.undysputed.dynspec.Dynspec.lanefiles`
        with ``dynspec_files``.
    
    Observation properties
    ----------------------
    
    Once the two *DynSpec* files 'lazy'-read/loaded (i.e., without
    being directly stored in memory), and before any data
    selection to occur, it might be handy to check the data
    properties.
    Several getter attributes of :class:`~nenupy.undysputed.dynspec.Dynspec`
    allow for taking an overall look at the data.

    Time
    ^^^^

    :attr:`~nenupy.undysputed.dynspec.Dynspec.tmin` and
    :attr:`~nenupy.undysputed.dynspec.Dynspec.tmax` both return
    :class:`~astropy.time.Time` object instances and give the
    start and stop times of the observation (time can thus be
    expressed in ISOT format, for example, simply by querying the
    ``.isot`` attribute of the :class:`~astropy.time.Time`
    instance):

    >>> ds.tmin.isot
    '2020-02-14T09:08:55.0000000'
    >>> ds.tmax.isot
    '2020-02-14T10:07:54.9506330'

    Native time resolution of the data can also be accessed
    as a :class:`~astropy.units.Quantity` instance by querying
    the :attr:`~nenupy.undysputed.dynspec.Dynspec.dt` attribute 
    (wich can then be converted to any desired equivalent
    unit):  
    
    >>> ds.dt
    0.04194304 s
    >>> ds.dt.to(u.ms)
    41.94304 ms

    Frequency
    ^^^^^^^^^

    :attr:`~nenupy.undysputed.dynspec.Dynspec.fmin` and
    :attr:`~nenupy.undysputed.dynspec.Dynspec.fmax` are the
    minimal and maximal recorded frequencies, independently of
    the beam selection.

    >>> ds.fmin
    11.816406 MHz
    >>> ds.fmax
    83.691406 MHz
    
    Native frequency resolution 
    :attr:`~nenupy.undysputed.dynspec.Dynspec.df` is also an
    instance of :class:`~astropy.units.Quantity` and can thus
    be converted to any matching unit:

    >>> ds.df
    12207.031 Hz
    >>> ds.df.to(u.MHz)
    0.012207031 MHz

    Beam
    ^^^^
    
    Depending on the observation configuration, several beams may
    be spread accross lane files. There could be as many beams as
    available beamlet (i.e. 768 if the full 150 MHz bandwidth is
    used, see `NenuFAR receivers <https://nenufar.obs-nancay.fr/en/astronomer/#receivers>`_).
    They are recorded by their indices and summarized within the
    :attr:`~nenupy.undysputed.dynspec.Dynspec.beams` atribute:

    >>> ds.beams
    array([0])
    
    to help selecting available beam indices. On the current example,
    only one beam has been recorded, hence the single index ``0``.

    Data selection
    --------------

    >>> ds.time_range = [
            '2020-02-14T09:08:55.0000000',
            '2020-02-14T09:30:30.9506330'
        ]
    >>> ds.freq_range = [
            10*u.MHz,
            90*u.MHz
        ]
    >>> ds.beam = 0

    Pipeline setup
    --------------

    Before getting the data, several processes may be set up and
    therefore being used for converting raw data ('L0') to cleaned
    and reduced data ('L1').
    
    Bandpass correction
    ^^^^^^^^^^^^^^^^^^^

    Reconstructed sub-bands may not display a flat bandpass due
    to polyphase filter response. It may be usefull to correct
    for this effect and reduce dynamic spectrum artefacts.
    Several types of correction are implemented and can be set
    with the :attr:`~nenupy.undysputed.dynspec.Dynspec.bp_correction`
    attribute (see :attr:`~nenupy.undysputed.dynspec.Dynspec.bp_correction`
    for more information regarding each correction efficiency).
    
    >>> ds.bp_correction = 'standard'

    Edge channels crop
    ^^^^^^^^^^^^^^^^^^

    By construction, channels at the edges of each sub-band may suffer
    from bad behaviors. One can thus set the attribute
    :attr:`~nenupy.undysputed.dynspec.Dynspec.edge_channels_to_remove`
    to any positive integer value :math:`n_{\rm chan}` (that should be
    less than half of the subband channels content). The first and last
    :math:`n_{\rm chan}` channels values of each sub-band are then set to `NaN`.
    
    >>> ds.edge_channels_to_remove = 4

    .. note::

        Since they are set to `NaN`, these flagged values do not
        interfere with any other methods of the :class:`~nenupy.undysputed.dynspec.Dynspec`
        class, especially the rebinning in which specific averaging
        methods are used (such as :meth:`~numpy.nanmean`).

    Pointing jump correction
    ^^^^^^^^^^^^^^^^^^^^^^^^
    
    Instrumental components used during analogical Mini-Array
    introduction of antenna delays for pointing purposes may
    induce < 1dB gain jumps. To ease correction of this effect,
    analogical pointing orders are set to occur every 6 minutes.

    A correction of these 6-minute jumps is implemented within
    :mod:`~nenupy.undysputed.dynspec` and only requires the
    boolean setting of the :attr:`~nenupy.undysputed.dynspec.Dynspec.jump_correction`
    attribute:

    >>> ds.jump_correction = True

    The jumps are fitted with a function of the form:
    
    .. math::
        f(t) = a \log_{10} (t) + b

    .. image:: ./_images/jumps.png
        :width: 800

    Dedispersion
    ^^^^^^^^^^^^
    
    `Pulsar <https://en.wikipedia.org/wiki/Pulsar>`_ or 
    `Fast Radio Burst <https://en.wikipedia.org/wiki/Fast_radio_burst>`_
    studies may require de-dispersion of the signal before averaging
    and/or summing over the frequency axis.

    A `Dispersion Measure <https://astronomy.swin.edu.au/cosmos/P/Pulsar+Dispersion+Measure>`_
    value other than ``None`` input to the
    :attr:`~nenupy.undysputed.dynspec.Dynspec.dispersion_measure` attribute
    triggers the de-dispersion process of the dynamic spectrum by
    correcting the data for frequency-dependent pulse delay
    (see :func:`~nenupy.astro.astro.dispersion_delay`).

    >>> ds.dispersion_measure = 12.4 * u.pc / (u.cm**3)

    .. warning::
        Dedispersion cannot benefit from `Dask <https://docs.dask.org/en/latest/>`_
        computing performances by construction (it would require
        smart n-dimensional array indexing which is not currently
        a Dask feature).
        Therefore, depending on data native sampling in time and
        frequency, a too large selection may lead to memory error.
        Users are encouraged to ask for smaller data chunks and
        combine them afterward.
    
    Averaging
    ^^^^^^^^^

    Averaging data might be quite useful in order to handle them
    in an easier way by reducing their size. Data can be averaged
    in time (with a :math:`\Delta t` given as input to the
    :attr:`~nenupy.undysputed.dynspec.Dynspec.rebin_dt` attribute)
    or in frequency (with a :math:`\Delta \nu` given as input to the
    :attr:`~nenupy.undysputed.dynspec.Dynspec.rebin_df` attribute):

    >>> ds.rebin_dt = 0.2 * u.s
    >>> ds.rebin_df = 195.3125 * u.kHz

    Either of these attribute can be set to ``None``, in which case
    the data are not averaged on the corresponding dimension. 

    Result examples
    ---------------

    Raw data averaged
    ^^^^^^^^^^^^^^^^^
    
    The first example follows exactly the previous steps,
    although, aiming for raw data visulaization, the gain jump
    correction and the de-dispersion processes are deactivated.
    Stokes I data are averaged and returned thanks to the
    :meth:`~nenupy.undysputed.dynspec.Dynspec.get` method and
    stored in the ``result`` variable, which is a
    :class:`~nenupy.beamlet.sdata.SData` instance.
    The dynamic spectrum is displayed with `matplotlib` after
    subtraction by a median background to enhance the features.
    
    .. code-block:: python
        :emphasize-lines: 12,13
        
        >>> from nenupy.undysputed import Dynspec
        >>> import astropy.units as u
        >>> import matplotlib.pyplot as plt

        >>> ds = Dynspec(lanefiles=dysnpec_files)

        >>> ds.time_range = ['2020-02-14T09:08:55.0000000', '2020-02-14T09:30:30.9506330']
        >>> ds.freq_range = [10*u.MHz, 90*u.MHz]
        >>> ds.beam = 0

        >>> ds.bp_correction = 'standard'
        >>> ds.jump_correction = False
        >>> ds.dispersion_measure = None
        >>> ds.rebin_dt = 0.2 * u.s
        >>> ds.rebin_df = 195.3125 * u.kHz
        
        >>> result = ds.get(stokes='i')

        >>> background = np.nanmedian(result.amp, axis=0)
        >>> plt.pcolormesh(
                result.time.datetime,
                result.freq.to(u.MHz).value,
                result.amp.T - background[:, np.newaxis],
            )

    .. image:: ./_images/psrb1919_nojump.png
        :width: 800
    
    Gain jump correction
    ^^^^^^^^^^^^^^^^^^^^

    The previous example three significant 6-min jumps. They can
    simply be corrected by setting :attr:`~nenupy.undysputed.dynspec.Dynspec.jump_correction`
    to ``True``:
    
    .. code-block:: python
        :emphasize-lines: 12
        
        >>> from nenupy.undysputed import Dynspec
        >>> import astropy.units as u
        >>> import matplotlib.pyplot as plt

        >>> ds = Dynspec(lanefiles=dysnpec_files)

        >>> ds.time_range = ['2020-02-14T09:08:55.0000000', '2020-02-14T09:30:30.9506330']
        >>> ds.freq_range = [10*u.MHz, 90*u.MHz]
        >>> ds.beam = 0

        >>> ds.bp_correction = 'standard'
        >>> ds.jump_correction = True
        >>> ds.dispersion_measure = None
        >>> ds.rebin_dt = 0.2 * u.s
        >>> ds.rebin_df = 195.3125 * u.kHz
        
        >>> result = ds.get(stokes='i')

        >>> background = np.nanmedian(result.amp, axis=0)
        >>> plt.pcolormesh(
                result.time.datetime,
                result.freq.to(u.MHz).value,
                result.amp.T - background[:, np.newaxis],
            )

    .. image:: ./_images/psrb1919.png
        :width: 800

    De-dispersion
    ^^^^^^^^^^^^^

    Finally, as these are `PSR B1919+21 <https://en.wikipedia.org/wiki/PSR_B1919%2B21>`_
    data, with a known dispersion measure of
    :math:`\mathcal{D}\mathcal{M} = 12.4\, \rm{pc}\,\rm{cm}^{-3}`,
    they can be de-dispersed by setting
    :attr:`~nenupy.undysputed.dynspec.Dynspec.dispersion_measure`
    to the pulsar's value:

    .. code-block:: python
        :emphasize-lines: 13

        >>> from nenupy.undysputed import Dynspec
        >>> import astropy.units as u
        >>> import matplotlib.pyplot as plt

        >>> ds = Dynspec(lanefiles=dysnpec_files)

        >>> ds.time_range = ['2020-02-14T09:08:55.0000000', '2020-02-14T09:30:30.9506330']
        >>> ds.freq_range = [10*u.MHz, 90*u.MHz]
        >>> ds.beam = 0

        >>> ds.bp_correction = 'standard'
        >>> ds.jump_correction = False
        >>> ds.dispersion_measure = 12.4 *u.pc / (u.cm**3)
        >>> ds.rebin_dt = 0.2 * u.s
        >>> ds.rebin_df = 195.3125 * u.kHz
        
        >>> result = ds.get(stokes='i')

        >>> background = np.nanmedian(result.amp, axis=0)
        >>> plt.pcolormesh(
                result.time.datetime,
                result.freq.to(u.MHz).value,
                result.amp.T - background[:, np.newaxis],
            )

    .. image:: ./_images/psrb1919_dedispersed.png
        :width: 800

    The dynamic spectrum is now de-dispersed with two visible effects:

    * The pulsar's pulses are now visible as vertical lines,
    * The 'right-hand' part of the spectrum contains `~numpy.nan` values as data were shifted to compensate for the dispersion delay. 

    Dynspec class
    -------------
"""


__author__ = 'Alan Loh'
__copyright__ = 'Copyright 2020, nenupy'
__credits__ = ['Alan Loh']
__maintainer__ = 'Alan'
__email__ = 'alan.loh@obspm.fr'
__status__ = 'Production'
__all__ = [
    '_Lane',
    'Dynspec'
]


from os.path import isfile, abspath, join, dirname, basename
import re
import numpy as np
import astropy.units as u
from astropy.time import Time
from astropy.modeling import models, fitting
from astropy.modeling.models import custom_model
import dask.array as da
from dask.diagnostics import ProgressBar
from typing import List
import h5py

import nenupy
from nenupy.beamlet import SData
from nenupy.astro import dispersion_delay

import logging
log = logging.getLogger(__name__)
#log.setLevel(logging.INFO)


FREQUENCY_UNIT = "MHz"
FREQ_QUANTITY = u.Unit(FREQUENCY_UNIT)
HEADER_STRUCT = [ # of a lane file
    ("idx", "uint64"), # lane index ?
    ("TIMESTAMP", "uint64"),
    ("BLOCKSEQNUMBER", "uint64"),
    ("fftlen", "int32"),
    ("nfft2int", "int32"),
    ("fftovlp", "int32"),
    ("apodisation", "int32"),
    ("nffte", "int32"),
    ("nbchan", "int32")
]

# ============================================================= #
# ---------------------- dynspec_to_hdf5 ---------------------- #
def _time_to_keywords(prefix: str, time: Time) -> dict:
    """ Returns a dictionnary of keywords in the HDF5 format.
    """
    return {
        f"{prefix.upper()}_MJD": time.mjd,
        f"{prefix.upper()}_TAI": time.tai.isot,
        f"{prefix.upper()}_UTC": time.isot + "Z"
    }
# ============================================================= #
# ============================================================= #


# ============================================================= #
# --------------------------- Lane ---------------------------- #
# ============================================================= #
class _Lane():
    """
    """

    def __init__(self, lanefile: str):
        self.lanefile = lanefile
        
        self.lane_index = None
        self.data = None
        self.time_unix = None
        self.frequency_hz = None
        self.dt = None
        self.df = None
        self.n_channels = None
        
        self._load()


    # --------------------------------------------------------- #
    # --------------------- Getter/Setter --------------------- #
    @property
    def lanefile(self) -> str:
        """
        """
        return self._lanefile
    @lanefile.setter
    def lanefile(self, l: str):
        l = abspath(l)
        if not isfile(l):
            raise FileNotFoundError(
                f"{l} not found."
            )
        pattern = re.compile(r"_(?P<index>\d).spectra$")
        index = pattern.findall(l)
        if len(index) != 1:
            raise ValueError(
                "Wrong file name pattern, is should end with *_<lane>.spectra."
            )
        self.lane_index = int(index[0])
        self._lanefile = l


    @property
    def tmin(self) -> Time:
        """ """
        return Time(self.time_unix[0], format='unix', precision=7)


    @property
    def tmax(self) -> Time:
        """ """
        return Time(self.time_unix[-1], format='unix', precision=7)


    @property
    def fmin(self) -> u.Quantity:
        """ """
        return self._fmin


    @property
    def fmax(self) -> u.Quantity:
        """ """
        return self._fmax
        

    # --------------------------------------------------------- #
    # ------------------------ Methods ------------------------ #
    # def get_stokes(self, stokes='I'):
    #     """ fft0[..., :] = [XX, YY]
    #         fft1[..., :] = [Re(X*Y), Im(X*Y)]
    #         XX=I+Q YY=I-Q XY=U+iV YX=U-iV
    #     """
    #     stokes_data = {
    #         'i': np.sum(self.fft0, axis=4),
    #         'q': self.fft0[..., 0] - self.fft0[..., 1],
    #         'u': self.fft1[..., 0] * 2,
    #         'v': self.fft1[..., 1] * 2,
    #         'l': np.sqrt((self.fft0[..., 0] - self.fft0[..., 1])**2 + (self.fft1[..., 0] * 2)**2),
    #         'xx': self.fft0[..., 0],
    #         'yy': self.fft0[..., 1],
    #         'rexy': self.fft1[..., 0],
    #         'imxy': self.fft1[..., 1]
    #     }
    #     try:
    #         selected_stokes = stokes_data[stokes.lower()]
    #     except KeyError:
    #         log.error(
    #             f'Available Stokes: {stokes_data.keys()}'
    #         )
    #         raise
    #     selected_stokes = self._to2d(selected_stokes)
    #     return selected_stokes

    def get_stokes(self, stokes="I") -> da.Array:
        """ Returns the requested Stokes parameter computed from
            the eJones data matrix.
        """

        data = None

        for stokes_i in stokes:

            # Compute the correct Stokes value
            if stokes_i.upper() == "I":
                data_i = self.data[..., 0, 0].real + self.data[..., 1, 1].real
            elif stokes_i.upper() == "Q":
                data_i = self.data[..., 0, 0].real - self.data[..., 1, 1].real
            elif stokes_i.upper() == "U":
                data_i = self.data[..., 0, 1].real*2
            elif stokes_i.upper() == "V":
                data_i = self.data[..., 0, 1].imag*2
            else:
                raise NotImplementedError(
                    f"Stokes parameter {stokes_i} unknown."
                )

            # Stack everything
            if data is None:
                data = data_i[..., None] # time, frequency, pol
            else: 
                data = da.concatenate([data, data_i[..., None]], axis=-1)

        return data


    # --------------------------------------------------------- #
    # ----------------------- Internal ------------------------ #
    def _load(self) -> None:
        """ """

        # Decode the header
        header = self._decode_header(file_name=self.lanefile)

        # Extract metadata
        n_channels = header["fftlen"]
        nffte = header["nffte"] # n time steps of duration dt per time block
        nfft2int = header["nfft2int"]
        n_subbands = header["nbchan"]

        self.dt = 5.12e-6*n_channels*nfft2int*u.s
        self.df = (1.0/5.12e-6/n_channels)*u.Hz
        self.n_channels = n_channels

        log.debug(
            f'Header of {self.lanefile} correctly parsed.'
        )

        # Read data
        data = self._decode_data(
            file_name=self.lanefile,
            nffte=nffte,
            n_channels=n_channels,
            n_subbands=n_subbands
        )

        # Store reshaped data
        self.data = self._to2d(
            data=self._to_ejones(data["fft0"], data["fft1"]),
            nffte=nffte,
            n_channels=n_channels
        )
        channels = data["channel"][0, :] # Assumed constant over time
        n_timeblocks, n_subbands = data["lane"].shape
        log.debug(
            f"Data of {self.lanefile} correctly parsed."
        )

        # Time array
        self.time_unix = self._compute_times(
            unix_start=header["TIMESTAMP"],
            dt=self.dt,
            n_times=n_timeblocks*nffte,
            block_seq_number=header["BLOCKSEQNUMBER"]
        )

        # Frequency array
        self.frequency_hz = self._compute_frequencies(
            n_channels=n_channels,
            n_subbands=n_subbands,
            df=self.df,
            subband_channels=channels
        )
        # Populate the fmin / fmax, which are not equal to the edges
        # of the frequency array because a beam can be spread over
        # several lanes.
        self._fmin = self.df*n_channels*(np.min(channels).compute() - 1/2)
        self._fmax = self.df*n_channels*(np.max(channels).compute() + 1/2)

        # Beam indices
        self.beam_idx = self._sort_beam_edges(
            beam_array=data['beam'][0].compute(), # asummed same for all time step
            n_channels=n_channels
        )


    @staticmethod
    def _decode_header(file_name: str) -> np.recarray:
        """ """
        log.info(f"Decoding header of {file_name}...")
        with open(file_name, "rb") as rf:
            header_dtype = np.dtype(HEADER_STRUCT)
            header = np.frombuffer(
                rf.read(header_dtype.itemsize),
                count=1,
                dtype=header_dtype,
            )[0]
        return header


    @staticmethod
    def _decode_data(file_name: str, nffte: int,
            n_channels: int, n_subbands: int
        ) -> da.Array:
        """ """
        log.info(f"Decoding data of {file_name}...")
        beamlet_dtype = np.dtype([
            ("lane", "int32"),
            ("beam", "int32"),
            ("channel", "int32"),
            ("fft0", "float32", (nffte, n_channels, 2)),
            ("fft1", "float32", (nffte, n_channels, 2))
        ])
        global_struct = HEADER_STRUCT +\
            [("data", beamlet_dtype, (n_subbands))]
        global_dtype = np.dtype(global_struct)
        itemsize = global_dtype.itemsize
        with open(file_name, "rb") as rf:
            tmp = np.memmap(rf, dtype="int8", mode="r")
        n_blocks = tmp.size*tmp.itemsize//(itemsize)
        return da.from_array(
            tmp[: n_blocks*itemsize].view(global_dtype)
        )["data"] # Dask powered


    @staticmethod
    def _compute_times(
            unix_start: int, dt: u.Quantity,
            n_times: int, block_seq_number: int
        ) -> np.ndarray:
        """
        """
        log.info("Computing the time array...")
        dt = dt.to(u.s).value
        times = da.from_array(
            np.arange(n_times, dtype="float64")
        )
        times *= dt
        times += unix_start + block_seq_number/195312.5
        return times


    @staticmethod
    def _compute_frequencies(
            n_channels: int, n_subbands: int,
            df: u.Quantity, subband_channels: np.ndarray
        ) -> np.ndarray:
        """
        """
        log.info("Computing the frequency array...")
        df = df.to(u.Hz).value
        subband_width = df*n_channels # Should be equal to 0.1953125 MHz
        # Construct the frequency array
        frequencies = da.from_array(
            np.tile(
                np.arange(n_channels) - n_channels/2,
                n_subbands
            )
        )
        frequencies = frequencies.reshape((n_subbands, n_channels))
        frequencies *= df
        frequencies += subband_channels[:, None]*subband_width
        return frequencies.ravel()


    @staticmethod
    def _sort_beam_edges(beam_array: np.ndarray, n_channels: int) -> dict:
        """ Find out where in the frequency axis a beam starts and end.
            This outputs a dictionnary such as:
            {
                "<beam_index>": (freq_axis_start_idx, freq_axis_end_idx,),
                ...
            }
        """
        indices = {}
        unique_beams = np.unique(beam_array)
        for b in unique_beams:
            b_idx = np.where(beam_array == b)[0]
            indices[str(b)] = (
                b_idx[0] * n_channels, # freq start of beam
                (b_idx[-1] + 1) * n_channels # freq stop of beam
            )
        return indices


    @staticmethod
    def _to2d(data, nffte: int, n_channels: int) -> da.Array:
        """ Inverts the halves of each beamlet and reshape the
            array in 2D (time, frequency) or 4D (time, frequency, 2, 2)
            if this is an 'ejones' matrix.
        """
        ntb, nfb = data.shape[:2]
        n_times = ntb*nffte
        n_freqs = nfb*n_channels
        if n_channels%2. != 0.0:
            raise ValueError(
                f'Problem with n_channels value: {n_channels}!'
            )

        # Prepare the various shapes
        temp_shape = (
            n_times,
            int(n_freqs/n_channels),
            2,
            int(n_channels/2)
        )
        final_shape = (n_times, n_freqs)

        # Add dimension if this comes in eJones matrix
        if data.ndim == 4:
            pass
        elif data.ndim == 6:
            final_shape += (2, 2)
            temp_shape += (2, 2)
        else:
            raise IndexError(f"The data has an unexpected shape of {data.shape}.")

        # Swap the subband (1) and nffte (2) dimensions to group
        # frequency and times dimensions together.
        # Reshape in order to isolate the halves of every beamlet.
        data = np.swapaxes(data, 1, 2).reshape(temp_shape)
        # Invert the halves and reshape to the final form.
        return data[:, :, ::-1, ...].reshape(final_shape)


    @staticmethod
    def _to_ejones(fft0, fft1):
        """ fft0[..., :] = [XX, YY]
            fft1[..., :] = [Re(X*Y), Im(X*Y)]
            Returns a (..., 2, 2) matrix (Dask)
        """
        row1 = da.stack(
            [
                fft0[..., 0], # XX
                fft1[..., 0] - 1j*fft1[..., 1] # XY*
            ],
            axis=-1
        )
        row2 = da.stack(
            [
                fft1[..., 0] + 1j*fft1[..., 1], # YX*
                fft0[..., 1] # YY
            ],
            axis=-1
        )
        return da.stack([row1, row2], axis=-1)


    # def _polarization_correction(fft0, fft1, jones):
    #     """
    #         fft0[..., :] = [XX, YY]
    #         fft1[..., :] = [Re(X*Y), Im(X*Y)]
    #         XX=I+Q YY=I-Q XY*=U+iV YX*=U-iV X*Y=U-iV Y*X=U+iV
    #     """
    #     # fft0.shape = (time_blocks, subbands, time_per_blocks, channels, 2)
    #     # jones.shape = (time, frequency, 2, 2)
    #     e_jones = da.concatenate(
    #         [ds.lanes[0].fft0[:100, ...], ds.lanes[0].fft1[:100, ...]],
    #         axis=-1
    #     ).shape
    #     xx = fft0[..., 0]
    #     yy = fft1[..., 1]
    #     xy = fft1[..., 0] - 1j*fft1[..., 1]
    #     yx = fft1[..., 0] + 1j*fft1[..., 1]

# ============================================================= #


# ============================================================= #
# -------------------------- Dynspec -------------------------- #
# ============================================================= #
class Dynspec(object):
    """ Main class to read and analyze UnDySPuTeD high-rate data.

        :param lanefiles:
            List of ``*.spctra`` files (see :attr:`~nenupy.undysputed.dynspec.Dynspec.lanefiles`).
        :type lanefiles: `list`

        .. versionadded:: 1.1.0
    """

    def __init__(self, lanefiles=[]):
        self.lanes = []
        self.lanefiles = lanefiles
        log.info(
            'Observation properties:'\
            f'\n\tTime : {self.tmin.isot} --> {self.tmax.isot}'\
            f'\n\tFrequency : {self.fmin} --> {self.fmax}'\
            f'\n\tTime step : {self.dt}'\
            f'\n\tFrequency step : {self.df}'
        )
        self.beam = 0
        self.dispersion_measure = None
        self.rebin_dt = None
        self.rebin_df = None
        self.jump_correction = False
        self.bp_correction = 'none'
        self.edge_channels_to_remove = 0
        self.freq_flat = False
        self.clean_rfi = False


    # --------------------------------------------------------- #
    # --------------------- Getter/Setter --------------------- #
    @property
    def lanefiles(self):
        """ UnDySPuTeD time-frequency files input (i.e. one file
            per lane) that are stored in the attribute 
            :attr:`~nenupy.undysputed.dynspec.Dynspec.lanes` as
            :class:`~nenupy.undysputed.dynspec._Lane` instances.

            Subsequent selections in time, frequency, beam and
            data operation processes will be run on these files
            while querying only those required. It means that any
            file listed in input is not necessarily read, and
            therefore having more files in input than needed
            does not increase memory usage or computing time.

            :setter: `list` of ``'*.spectra'`` files.

            :getter: `list` of ``'*.spectra'`` files.

            :type: `list`

            :Example:
                >>> from nenupy.undysputed import Dynspec
                >>> ds = Dynspec(
                        lanefiles=['lane_0.spectra', 'lane_0.spectra']
                    )
                >>> ds.lanefiles
                ['/path/to/lane_0.spectra', '/path/to/lane_0.spectra']

            .. warning::
                Files are checked to belong to the same
                observation based on their prefix.
    
            .. versionadded:: 1.1.0
        """
        return list(self._lanefiles)
    @lanefiles.setter
    def lanefiles(self, l):
        if not isinstance(l, list):
            l = [l]
        l = list(map(abspath, l))
        # Check that all the input files belong to the same obs TO REDO
        # names = list(map(basename,l))
        # obsname = [ni[::-1].split('_', 1)[1] for ni in names]
        # if obsname != obsname[::-1]:
        #     raise ValueError(
        #         'Input files seem not to belong to the same observation.'
        #     )
        for li in map(abspath, l):
            if not isfile(li):
                raise FileNotFoundError(
                    f'{li} not found.'
                )
            else:
                log.debug(f'Found {li}')
                self.lanes.append(
                    _Lane(li)
                )
        self._lanefiles = l
        return


    @property
    def time_range(self):
        """ Time range selection.

            :setter: Time range expressed as ``[t_min, t_max]``
                where ``t_min`` and ``t_max`` could either be
                `str` (ISO or ISOT formats) or :class:`~astropy.time.Time`
                instances.

            :getter: Time range in UNIX unit.

            :type: `list`

            .. versionadded:: 1.1.0
        """
        if not hasattr(self, '_time_range'):
            return [self.tmin.unix, self.tmax.unix]
        return self._time_range
    @time_range.setter
    def time_range(self, t):
        if not isinstance(t, list):
            raise TypeError(
                'time_range expects a list.'
            )
        if not len(t) == 2:
            raise ValueError(
                'time_range should be a length-2 list.'
            )
        if not all([isinstance(ti, Time) for ti in t]):
            t = [Time(ti, precision=7) for ti in t]
        if t[0] >= t[1]:
            raise ValueError(
                'time_range start >= stop.'
            )
        log.info(
            f'Time-range set: {t[0].isot} to {t[1].isot}.'
        )
        self._time_range = [t[0].unix, t[1].unix]
        return


    @property
    def freq_range(self):
        """ Frequency range selection.

            :setter: Frequency range expressed as ``[f_min, f_max]``
                where ``f_min`` and ``f_max`` could either be
                `float` (understood as MHz) or :class:`~astropy.units.Quantity`
                instances.

            :getter: Frequency range in Hz.

            :type: `list`

            .. versionadded:: 1.1.0
        """
        if not hasattr(self, '_freq_range'):
            return [self.fmin.to(u.Hz), self.fmax.to(u.Hz)]
        return self._freq_range
    @freq_range.setter
    def freq_range(self, f):
        if not isinstance(f, list):
            raise TypeError(
                'freq_range expects a list.'
            )
        if not len(f) == 2:
            raise ValueError(
                'freq_range should be a length-2 list.'
            )
        if not all([isinstance(fi, u.Quantity) for fi in f]):
            f = [fi*u.MHz for fi in f]
        if f[0] >= f[1]:
            raise ValueError(
                'freq_range min >= max.'
            )
        log.info(
            f'Freq-range set: {f[0].to(u.MHz)} to {f[1].to(u.MHz)}.'
        )
        self._freq_range = [f[0].to(u.Hz), f[1].to(u.Hz)]
        return


    @property
    def beam(self):
        """ Select a beam index among available beams
            :attr:`~nenupy.undysputed.dynspec.Dynspec.beams`.

            :setter: Selected beam index. Default is ``0``.

            :getter: Selected beam index.

            :type: `int`

            .. versionadded:: 1.1.0
        """
        return self._beam
    @beam.setter
    def beam(self, b):
        if not isinstance(b, (int, np.integer)):
            raise TypeError(
                'beam should be an integer.'
            )
        if b not in self.beams:
            log.warning(
                f'Available beam indices are {self.beams}. Setting default to {self.beams[0]}'
            )
            b = self.beams[0]
        self._beam = b
        log.info(
            f'Beam index set: {b}.'
        )
        return


    @property
    def dispersion_measure(self):
        r""" Apply (if other than ``None``) de-dispersion
            process to the data in order to compensate for
            the dispersion delay.

            :setter: Dispersion Measure :math:`\mathcal{D}\mathcal{M}`
                either as `float` (understood as :math:`\rm{pc}\,\rm{cm}^{-3}`
                unit) or :class:`~astropy.units.Quantity`.

            :getter: Dispersion Measure :math:`\mathcal{D}\mathcal{M}` in :math:`\rm{pc}\,\rm{cm}^{-3}`.

            :type: :class:`~astropy.units.Quantity` or `float`

            .. versionadded:: 1.1.0
        """
        return self._dispersion_measure
    @dispersion_measure.setter
    def dispersion_measure(self, dm):
        if not (dm is None):
            if not isinstance(dm, u.Quantity):
                dm *= u.pc / (u.cm**3)
            dm = dm.to(u.pc / (u.cm**3))
            log.info(
                f'DM set to {dm}'
            )
        self._dispersion_measure = dm
        return


    @property
    def rebin_dt(self):
        """ Averaged data time step. If ``None`` data will not
            be time-averaged.

            :setter: Time step  (in sec if no unit is provided).

            :getter: Time step in seconds.

            :type: :class:`~astropy.units.Quantity` or `float`

            .. versionadded:: 1.1.0
        """
        return self._rebin_dt
    @rebin_dt.setter
    def rebin_dt(self, dt):
        if not (dt is None):
            if not isinstance(dt, u.Quantity):
                dt *= u.s
            dt = dt.to(u.s)
            log.info(
                f'Time averaging on {dt}'
            )
        self._rebin_dt = dt
        return


    @property
    def rebin_df(self):
        """ Averaged data frequency step. If ``None`` data will not
            be frequency-averaged.

            :setter: Frequency step (in MHz is not unit is provided).

            :getter: Frequency step in Hz.

            :type: 

            .. versionadded:: 1.1.0
        """
        return self._rebin_df
    @rebin_df.setter
    def rebin_df(self, df):
        if not (df is None):
            if not isinstance(df, u.Quantity):
                df *= u.MHz
            df = df.to(u.Hz)
            log.info(
                f'Frequency averaging on {df}'
            )
        self._rebin_df = df
        return


    @property
    def bp_correction(self):
        """ Polyphase-filter introduces a band-pass response
            that may be corrected using one of the following
            methods:

            * ``'none'``: no band-pass correction is applied,
            * ``'standard'``: pre-computed coefficients are used to correct the bandpass,
            * ``'median'``: the band-pass correction is actively corrected (this lead to the best results but it is the slowest method).

            :setter: Band-pass correction method (default is
                ``'none'``).

            :getter: Band-pass correction method.

            :type: `str`

            .. warning::
                Effects of bandpass correction may depend
                on data quality.

                .. image:: ./_images/bandpass_corr.png
                    :width: 800

            .. versionadded:: 1.1.0
        """
        return self._bp_correction
    @bp_correction.setter
    def bp_correction(self, b):
        available = ['standard', 'median', 'none', 'adjusted']
        if not isinstance(b, str):
            raise TypeError(
                'bp_correction must be a string.'
            )
        b = b.lower()
        if not b in available:
            raise ValueError(
                f'Available bandpass corrections are {available}.'
            )
        log.info(
            f'Bandpass correction set: {b}.'
        )
        self._bp_correction = b
        return    


    @property
    def edge_channels_to_remove(self) -> int:
        """ Number of channels to remove at each subband edge.
            Generally, the 2 extreme channels are not taken into account.

            :type: `int`
        """
        return self._edge_channels_to_remove
    @edge_channels_to_remove.setter
    def edge_channels_to_remove(self, n: int) -> None:
        default_val = 0
        if not isinstance(n, int):
            log.warning(
                "The number of channels to remove at each subband "
                f"edge needs to be an integer. Setting default value {default_val}."
            )
            n = default_val
        elif n*2 > self.nchan:
            log.warning(
                f"Each subband is divided in {self.nchan} channels "
                f"in this dataset. Removing {n} channels at both "
                "edge would not leave any data left. Setting default "
                f"value {default_val}."
            )
            n = default_val
        elif n < 0:
            log.warning(
                "The number of channels to remove should be positive. "
                f"Setting default value {default_val}."
            )
            n = default_val
        if n > 0:
            log.info(
                f"{n} channels will be removed at subband edges."
            )
        self._edge_channels_to_remove = n


    @property
    def jump_correction(self):
        """ Correct or not the known 6-minute gain jumps
            due to analogical Mini-Array pointing orders.

            :setter: 6-min jump correction.

            :getter: 6-min jump correction.

            :type: `bool`

            .. versionadded:: 1.1.0
        """
        return self._jump_correction
    @jump_correction.setter
    def jump_correction(self, j):
        if not isinstance(j, bool):
            raise TypeError(
                'jump_correction must be a boolean.'
            )
        log.info(
            f'6-min jump correction set: {j}.'
        )
        self._jump_correction = j
        return


    @property
    def tmin(self):
        """ Start time of the whole observation.

            :getter: Minimal observation time.

            :type: :class:`~astropy.time.Time`

            .. versionadded:: 1.1.0
        """
        return min(li.tmin for li in self.lanes)


    @property
    def tmax(self):
        """ End-time of the whole observation.

            :getter: Maximal observation time.

            :type: :class:`~astropy.time.Time`

            .. versionadded:: 1.1.0
        """
        return max(li.tmax for li in self.lanes)


    @property
    def dt(self):
        """ Native time resolution.

            :getter: Time resolution in seconds.

            :type: :class:`~astropy.units.Quantity`

            .. versionadded:: 1.1.0
        """
        dts = np.array([li.dt.value for li in self.lanes])
        if not all(dts == dts[0]):
            log.warning(
                'Lanes have different dt values.'
            )
        return self.lanes[0].dt


    @property
    def fmin(self):
        """ Minimal frequency recorded for the observation,
            over all lane file.

            :getter: Minimal frequency in MHz.

            :type: :class:`~astropy.units.Quantity`

            .. versionadded:: 1.1.0
        """
        fm = min(li.fmin for li in self.lanes)
        return fm.to(u.MHz)


    @property
    def fmax(self):
        """ Maximal frequency recorded for the observation,
            over all lane file.

            :getter: Maximal frequency in MHz.

            :type: :class:`~astropy.units.Quantity`

            .. versionadded:: 1.1.0
        """
        fm = max(li.fmax for li in self.lanes)
        return fm.to(u.MHz)


    @property
    def df(self):
        """ Native frequency resolution.

            :getter: Frequency resolution in Hz.

            :type: :class:`~astropy.units.Quantity`

            .. versionadded:: 1.1.0
        """
        dfs = np.array([li.df.value for li in self.lanes])
        if not all(dfs == dfs[0]):
            log.warning(
                'Lanes have different df values.'
            )
        return self.lanes[0].df


    @property
    def nchan(self) -> int:
        """ Native number of channels per subband.

            :type: `int`
 
        """
        nchans = np.array([li.n_channels for li in self.lanes])
        if not all(nchans == nchans[0]):
            log.warning(
                'Lanes have different number of channel values.'
            )
        return self.lanes[0].n_channels

    @property
    def beams(self):
        """ Array of unique beam indices recorded during the
            observation over the different lane files.

            :getter: Available beam indices.

            :type: :class:`~numpy.ndarray`

            .. versionadded:: 1.1.0
        """
        un_beams = []
        for li in self.lanes:
            lane_beams = [int(lbi) for lbi in li.beam_idx.keys()]
            un_beams += lane_beams
        return np.unique(un_beams)


    # --------------------------------------------------------- #
    # ------------------------ Methods ------------------------ #
    def get(self, stokes='I'):
        r""" *UnDySPuTeD* produces four quantities: 
            :math:`|\rm{XX}|^2`,
            :math:`|\rm{YY}|^2`,
            :math:`\operatorname{Re}(\rm{XY}^*)`,
            :math:`\operatorname{Im}(\rm{XY}^*)`. They are used
            to compute the four `Stokes <https://en.wikipedia.org/wiki/Stokes_parameters>`_
            parameters (:math:`\rm{I}`, :math:`\rm{Q}`,
            :math:`\rm{U}`, :math:`\rm{V}`) and the linear
            polarization :math:`\rm{L}`:

            .. math::
                \rm{I} = |\rm{XX}|^2 + |\rm{YY}|^2

            .. math::
                \rm{Q} = |\rm{XX}|^2 - |\rm{YY}|^2

            .. math::
                \rm{U} =  2 \operatorname{Re}(\rm{XY}^*)

            .. math::
                \rm{V} =  2 \operatorname{Im}(\rm{XY}^*)

            .. math::
                \rm{L} = \sqrt{\rm{Q}^2 + \rm{U}^2}

            :param stokes:
                Stokes parameter to return (case insensitive).
                Allowed values are ``'I'``, ``'Q'``, ``'U'``,
                ``'V'``, ``'L'``, ``'XX'``, ``'YY'``. Default
                is ``'I'``.
            :type stokes: `str`

            :returns:
            :rtype: `~nenupy.beamlet.sdata.SData`

            .. versionadded:: 1.1.0
        """
        for li in self.lanes:

            try:
                beam_start, beam_stop = li.beam_idx[str(self.beam)]
            except KeyError:
                # No beam 'self.beam' found on this lane
                continue

            data = li.get_stokes(
                stokes=stokes
            )

            # Time selection
            # way more efficient to compute indices than masking
            tmin_idx = np.argmin(
                np.abs(li.time_unix - self.time_range[0])
            ).compute()
            tmax_idx = np.argmin(
                np.abs(li.time_unix - self.time_range[1])
            ).compute()
            # Freq/beam selection
            # way more efficient to compute indices than masking
            fmin_idx = np.argmin(
                np.abs(li.frequency_hz[beam_start:beam_stop] - self.freq_range[0].value)
            ).compute()
            fmax_idx = np.argmin(
                np.abs(li.frequency_hz[beam_start:beam_stop] - self.freq_range[1].value)
            ).compute()
            if (fmin_idx - fmax_idx) == 0:
                # No data selected on this lane
                continue
            # Ensure that frequency indices are at the bottom and top
            # of a subband (to ease bandpass computation)
            fmin_idx = (fmin_idx//li.n_channels)*li.n_channels
            fmax_idx = (fmax_idx//li.n_channels+1)*li.n_channels

            log.info(
                f'Retrieving data selection from lane {li.lane_index}...'
            )

            # High-rate data selection
            data = data[:, beam_start:beam_stop][
                tmin_idx:tmax_idx,
                fmin_idx:fmax_idx
            ]

            # Bandpass correction
            data = self._bp_correct(
                data=data,
                n_channels=li.n_channels
            )
            selfreqs = li.frequency_hz[beam_start:beam_stop][fmin_idx:fmax_idx].compute()*u.Hz

            # Remove subband edge channels
            data = self._remove_edge_channels(data=data)

            # RFI mitigation
            data = self._clean(
                data=data
            )

            # Correct 6 min jumps
            data = self._correct_jumps(
                data=data,
                dt=li.dt
            )

            # Dedispersion if FRB or Pulsar
            data = self._dedisperse(
                data=data,
                freqs=selfreqs,
                dt=li.dt
            )

            # Rebin data to downweight the output
            data, seltimes, selfreqs = self._rebin(
                data=data,
                times=li.time_unix[tmin_idx:tmax_idx],
                freqs=selfreqs,
                dt=li.dt,
                df=li.df,
            )

            with ProgressBar():
                data = data.compute()

            # Build a SData instance
            sd = SData(
                data=data,
                time=seltimes,
                freq=selfreqs,
                polar=stokes,
            )
            # Stack in frequency the SData instances at
            # each lane reading
            if not 'spec' in locals():
                spec = sd
            else:
                spec = spec & sd
        log.info(
            f'Stokes {stokes} data gathered.'
        )
        return spec


    def write_hdf5(
                self,
                file_name: str,
                stokes: List[str] = ["I"],
                beams: List[int] = [0],
                **metadata
            ) -> None:
        """ Save a NenuFAR dynamic spectrum from the :class:`~nenupy.undysputed.dynspec.Dynspec`
            class. The processing pipeline set up in the ``dynspec``
            object is then run before saving everything in a HDF5 file.

            :param file_name:
                Name of the HDF5 to store.
            :type file_name:
                `str`
            :param stokes:
                List of Stokes parameters to store. Each Stokes
                parameter should be written as if given to the
                :meth:`~nenupy.undysputed.dynspec.Dynspec.get` method.
                Default is ``["I"]``.
            :type stokes:
                `list` of `str`
            :beams:
                List of beam indices to store. This will make use of the 
                :class:`~nenupy.undysputed.dynspec.Dynspec.beam` attribute.
                Default value is ``[0]``.
            :type beams:
                `list` of `int`
            :param **metadata:
                Any additional metadata to be written as the HDF5 root attributes.
        """
        with h5py.File(file_name, "w") as wf:

            # Metadata
            wf.attrs.update(metadata)
            wf.attrs["SOFTWARE_NAME"] = "nenupy"
            wf.attrs["SOFTWARE_VERSION"] = nenupy.__version__
            wf.attrs["SOFTWARE_MAINTAINER"] = "alan.loh@obspm.fr"
            wf.attrs.update(_time_to_keywords("OBSERVATION_START", self.tmin))
            wf.attrs.update(_time_to_keywords("OBSERVATION_END", self.tmax))
            wf.attrs["OBSERVATION_FREQUENCY_MIN"] = self.fmin.to(FREQ_QUANTITY).value
            wf.attrs["OBSERVATION_FREQUENCY_MAX"] = self.fmax.to(FREQ_QUANTITY).value
            wf.attrs["OBSERVATION_FREQUENCY_CENTER"] = ((self.fmax + self.fmin)/2).to(FREQ_QUANTITY).value
            wf.attrs["OBSERVATION_FREQUENCY_UNIT"] = FREQUENCY_UNIT

            for beam in beams:

                if beam not in self.beams:
                    raise IndexError(
                        f"Invalid beam index request: {beam}. (Available beam indices: {self.beams})"
                    )

                log.info(f"Working on Beam #{beam}...")

                beam_group = wf.create_group(f"BEAM_{beam:03d}")

                coordinates_group = beam_group.create_group("COORDINATES")

                self.beam = beam

                for stokes_param in stokes:

                    log.info(f"Running Stokes {stokes_param} pipeline...")

                    # Run the pipeline!
                    stokes_chunk = self.get(stokes_param)

                    dataset = beam_group.create_dataset(
                        name=f"STOKES_{stokes_param.upper()}",
                        data=stokes_chunk.amp
                    )

                    if "frequency" not in coordinates_group:
                        # Update the attributes
                        beam_group.attrs.update(_time_to_keywords("TIME_START", stokes_chunk.time[0]))
                        beam_group.attrs.update(_time_to_keywords("TIME_END", stokes_chunk.time[-1]))
                        beam_group.attrs["FREQUENCY_MIN"] = stokes_chunk.freq.min().to(FREQ_QUANTITY).value
                        beam_group.attrs["FREQUENCY_MAX"] = stokes_chunk.freq.max().to(FREQ_QUANTITY).value
                        beam_group.attrs["FREQUENCY_UNIT"] = FREQUENCY_UNIT

                        # Fill in the coordinates once
                        coordinates_group["frequency"] = stokes_chunk.freq.to(FREQ_QUANTITY).value
                        coordinates_group["frequency"].make_scale(f"Frequency ({FREQUENCY_UNIT})")                
                        coordinates_group["time"] = stokes_chunk.time.jd
                        coordinates_group["time"].make_scale("Time (JD)")

                    dataset.dims[0].label = "frequency"
                    dataset.dims[0].attach_scale(coordinates_group["frequency"])
                    dataset.dims[1].label = "time"
                    dataset.dims[1].attach_scale(coordinates_group["time"])

        log.info(f"{file_name} written.")


    # --------------------------------------------------------- #
    # ----------------------- Internal ------------------------ #
    @staticmethod
    def _bandpass(n_channels: int) -> np.ndarray:
        """ Computes the bandpass correction for a beamlet.
        """
        kaiser_file = join(
            dirname(abspath(__file__)),
            'bandpass_coeffs.dat'
        )
        kaiser = np.loadtxt(kaiser_file)

        n_tap = 16
        over_sampling = n_channels // n_tap
        n_fft = over_sampling * kaiser.size

        g_high_res = np.fft.fft(kaiser, n_fft)
        mid = n_channels // 2
        middle = np.r_[g_high_res[-mid:], g_high_res[:mid]]
        right = g_high_res[mid:mid + n_channels]
        left = g_high_res[-mid - n_channels:-mid]

        midsq = np.abs(middle)**2
        leftsq = np.abs(left)**2
        rightsq = np.abs(right)**2
        g = 2**25/np.sqrt(midsq + leftsq + rightsq)
        return g**2.


    def _bp_correct(self, data: da.Array, n_channels: int) -> da.Array:
        """ Applies the bandpass correction to each beamlet
        """
        if self.bp_correction == "standard":
            bp = self._bandpass(n_channels=n_channels)
            ntimes, nfreqs, npols = data.shape
            data = data.reshape(
                (
                    ntimes,
                    int(nfreqs/bp.size),
                    bp.size,
                    npols
                )
            )
            data *= bp[None, None, :, None]
            return data.reshape((ntimes, nfreqs, npols))

        elif self.bp_correction == "median":
            ntimes, nfreqs, npols = data.shape
            spectrum = np.nanmedian(data, axis=0)
            folded = spectrum.reshape(
                (int(spectrum.size / n_channels), n_channels, npols)
                )
            broadband = np.nanmedian(folded, axis=1)
            data = data.reshape(
                (
                    ntimes,
                    int(spectrum.size / n_channels),
                    n_channels,
                    npols
                )
            )
            data *= broadband[None, :, None, :]
            return data.reshape((ntimes, nfreqs, npols)) / spectrum

        elif self.bp_correction == "adjusted":
            ntimes, nfreqs, npols = data.shape
            data = data.reshape(
                (
                    ntimes,
                    int(nfreqs/n_channels),
                    n_channels,
                    npols
                )
            )
            freqProfile = np.nanmedian(data, axis=0)
            medianPerSubband = np.nanmedian(freqProfile, axis=1)
            subbandProfileNormalized = freqProfile / medianPerSubband[:, None]
            subbandProfile = np.nanmedian(subbandProfileNormalized, axis=0)
            data /= subbandProfile[None, None, :]
            return data.reshape((ntimes, nfreqs, npols))

        else:
            return data


    def _remove_edge_channels(self, data: da.Array) -> da.Array:
        """ Remove the N channels at each subband edge (set their values to NaNs).
        """
        if self.edge_channels_to_remove > 0:
            nchannels = self.nchan
            ntimes, nfreqs, npols = data.shape
            nsubbands = int(nfreqs/nchannels)
            data = data.reshape((ntimes, nsubbands, nchannels, npols))
            data[:, :, :self.edge_channels_to_remove, :] = np.nan # lower edge
            data[:, :, -self.edge_channels_to_remove:, :] = np.nan # upper edge
            data = data.reshape((ntimes, nfreqs, npols))
            log.info(
                f"{self.edge_channels_to_remove} channels have been "
                "set to NaN at the subband edges."
            )
        return data


    def _freqFlattening(self, data):
        """ Flatten the sub-band response
        """
        return data


    def _clean(self, data):
        """
        """
        if self.clean_rfi:
            pass
        return data


    def _dedisperse(self, data, freqs, dt):
        """
            This cannot be done properly with dask...

            .. versionadded:: 1.1.0
        """
        if not (self.dispersion_measure is None):
            log.info(
                'Starting de-dispersion...'
            )
            with ProgressBar():
                data = data.compute()
            if data.shape[1] != freqs.size:
                raise ValueError(
                    'Problem with frequency axis.'
                )
            dm = self.dispersion_measure.value # pc/cm^3
            delays = dispersion_delay(
                frequency=freqs,
                dispersion_measure=self.dispersion_measure
            )
            delays -= dispersion_delay( # relative delays
                frequency=self.freq_range[1],
                dispersion_measure=self.dispersion_measure
            )
            cell_delays = np.round((delays/dt)).astype(int)
            for i in range(freqs.size):
                data[:, i, :] = np.roll(data[:, i, :], -cell_delays[i], 0)
                # mask right edge of dynspec
                data[-cell_delays[i]:, i, :] = np.nan
            log.info(
                'Data are de-dispersed.'
            )
            data = da.from_array(data)
        return data

    # def _dedisperse(self, data, freqs, dt):
    #     """
    #         .. versionadded:: 1.1.0
    #     """
    #     if not (self.dispersion_measure is None):
    #         log.info(
    #             'Starting de-dispersion...'
    #         )
    #         if data.shape[1] != freqs.size:
    #             raise ValueError(
    #                 'Problem with frequency axis.'
    #             )
    #         dm = self.dispersion_measure.value # pc/cm^3
    #         delays = dispersion_delay(
    #             freq=freqs,
    #             dm=self.dispersion_measure)
    #         delays -= dispersion_delay( # relative delays
    #             freq=self.freq_range[1],
    #             dm=self.dispersion_measure
    #         )
    #         cell_delays = np.round((delays/dt).value).astype(int)
    #         #nans = np.ones(data.shape[0])
    #         rows = []
    #         for i in range(freqs.size):
    #             # No item assignement in dask (https://github.com/dask/dask/issues/4399)
    #             # data[:, i] = np.roll(data[:, i], -cell_delays[i], 0)
    #             #data[:, i] = np.roll(data[:, i], -cell_delays[i], 0)/data[:, i]
    #             # mask right edge of dynspec
    #             #data[-cell_delays[i]:, i] = np.nan
    #             #data[-cell_delays[i]:, i] *= np.nan

    #             dedispersed_row = da.roll(data[:, i], -cell_delays[i], 0)
    #             #nans[-cell_delays[i]:] = np.nan
    #             #dedispersed_row *= nans
                
    #             # if 'dedispersed_data' in locals():
    #             #     dedispersed_data = np.vstack((dedispersed_data, dedispersed_row))
    #             # else:
    #             #     dedispersed_data = dedispersed_row
                
    #             rows.append(dedispersed_row)

    #         data = da.stack(rows, axis=1)
    #         log.info(
    #             'Data are de-dispersed.'
    #         )
    #     return data


    def _rebin(self, data, times, freqs, dt, df):
        """
            .. versionadded:: 1.1.0
        """
        ntimes_i, nfreqs_i, npols_i = data.shape
        if not (self.rebin_dt is None):
            # Rebin in time
            tbins = int(np.floor(self.rebin_dt/dt))
            log.info(
                f'Time-averaging {tbins} spectra, dt={tbins*dt}...'
            )
            ntimes = int(np.floor(ntimes_i/tbins))
            tleftover = ntimes_i % ntimes
            log.info(
                f'Last {tleftover} spectra are left over for time-averaging.'
            )
            data = data[:-tleftover if tleftover != 0 else ntimes_i, :, :].reshape(
                (ntimes, int((ntimes_i - tleftover)/ntimes), nfreqs_i, npols_i)
            )
            times = times[:-tleftover if tleftover != 0 else ntimes_i].reshape(
                (ntimes, int((ntimes_i - tleftover)/ntimes))
            )
            data = np.nanmean(data, axis=1)
            times = np.nanmean(times, axis=1)
            ntimes_i, nfreqs_i, npols_i = data.shape
            log.info(
                'Data are time-averaged.'
            )
        if not (self.rebin_df is None):
            # Rebin in frequency
            fbins = int(np.floor(self.rebin_df/df))
            log.info(
                f'Frequency-averaging {fbins} channels: df={fbins*df}...'
            )
            nfreqs = int(np.floor(nfreqs_i/fbins))
            fleftover = nfreqs_i % nfreqs
            log.info(
                f'Last {fleftover} channels are left over for frequency-averaging.'
            )
            data = data[:, :-fleftover if fleftover != 0 else nfreqs_i, :].reshape(
                (ntimes_i, nfreqs, int((nfreqs_i - fleftover)/nfreqs), npols_i)
            )
            freqs = freqs[:-fleftover if fleftover != 0 else nfreqs_i].reshape(
                (nfreqs, int((nfreqs_i - fleftover)/nfreqs))
            )
            data = np.nanmean(data, axis=2)
            freqs = np.nanmean(freqs, axis=1)
            log.info(
                'Data are frequency-averaged.'
            )
        times = Time(
            times,
            format='unix',
            precision=7
        )
        return data, times, freqs


    # def _correct_jumps(self, data, dt):
    #     """ Dask version
    #     """
    #     if not self.jump_correction:
    #         return data
    #     log.info(
    #         'Correcting for 6 min pointing jumps...'
    #     )
    #     # Work on cleanest profile
    #     profile = np.median(data, axis=1).compute()
    #     # detect jumps
    #     dt = dt.to(u.s).value
    #     deriv = np.gradient(profile, dt)
    #     low_threshold = np.nanmedian(deriv) - 8 * np.nanstd(deriv)
    #     lower_thr_indices = np.where(deriv < low_threshold)[0] # detection
    #     # Sort jump indices
    #     jump_idx = [0]
    #     for idx in lower_thr_indices:
    #         if idx > jump_idx[-1] + 10:
    #             jump_idx.append(idx)
    #     jump_idx.append(data.shape[0] - 1)
    #     # Make sure there are no > 6min gaps
    #     sixmin = 6*60.000000 + dt
    #     for idx in range(1, len(jump_idx)):
    #         delta_t = dt * (jump_idx[idx] - jump_idx[idx-1])
    #         if delta_t > sixmin:
    #             missing_idx = int(np.round(sixmin/dt))
    #             jump_idx.insert(idx, missing_idx + jump_idx[idx-1])
    #     # flatten
    #     boundaries = list(map(list, zip(jump_idx, jump_idx[1:])))
    #     previous_endpoint = 1.
    #     flattening = np.ones(data.shape[0])
    #     for i, boundary in enumerate(boundaries):
    #         idi, idf = boundary
    #         med_data_freq = profile[idi:idf]
    #         flattening[idi:idf] /= med_data_freq
    #         if i == 0:
    #             flattening[idi:idf] *= np.median(med_data_freq)
    #         else:
    #             flattening[idi:idf] *= previous_endpoint
    #         previous_endpoint = profile[idf-1] * flattening[idf-1]
    #     log.info(
    #         f'Found and corrected {i+1} jump(s).'
    #     )
    #     return data*flattening[:, np.newaxis]


    # def _correct_jumps_v0(self, data, dt):
    #     """ Dask version
    #     """
    #     if not self.jump_correction:
    #         return data
    #     log.info(
    #         'Correcting for 6 min pointing jumps...'
    #     )
    #     six_min = 6*60.000000 * u.s
    #     seven_min = 7*60.000000 * u.s
    #     # Find first jump
    #     log.info(
    #         'Computing median time-profile...'
    #     )
    #     with ProgressBar():
    #         tprofile = np.median(
    #             data,
    #             axis=1
    #         ).compute()
    #     from scipy.signal import savgol_filter
    #     tprofile_smoothed = savgol_filter(
    #         x=tprofile[:int(seven_min/dt)],
    #         window_length=11,
    #         polyorder=2,
    #         deriv=0
    #     )
    #     deriv = np.gradient(tprofile_smoothed, dt.value)
    #     jump_idx = [0] # start of the time
    #     jump_idx.append(np.argmin(deriv)) # first jump
    #     # Deduce next jump indices
    #     while True:
    #         next_jump_idx = jump_idx[-1] + int(six_min/dt)
    #         if next_jump_idx >= data.shape[0]:
    #             break
    #         jump_idx.append(next_jump_idx)
    #     jump_idx.append(data.shape[0] - 1)
    #     # flatten
    #     boundaries = list(map(list, zip(jump_idx, jump_idx[1:])))
    #     previous_endpoint = 1.
    #     flattening = np.ones(data.shape[0])
    #     for i, boundary in enumerate(boundaries):
    #         idi, idf = boundary
    #         med_data_freq = tprofile[idi:idf]
    #         flattening[idi:idf] /= med_data_freq
    #         if i == 0:
    #             flattening[idi:idf] *= np.median(med_data_freq)
    #         else:
    #             flattening[idi:idf] *= previous_endpoint
    #         previous_endpoint = tprofile[idf-1] * flattening[idf-1]
    #     log.info(
    #         f'Found and corrected {i+1} jump(s).'
    #     )
    #     return data*flattening[:, np.newaxis]


    def _correct_jumps(self, data, dt):
        """ Dask version
        """
        if not self.jump_correction:
            return data
        log.info(
            'Correcting for 6 min pointing jumps...'
        )
        for pol_i in range(data.shape[2]):
            freqProfile = np.nanmedian(
                data[:, :, pol_i],
                axis=0
            ).compute()
            timeProfile = np.nanmedian(
                data[:, :, pol_i] / freqProfile[None, :],
                axis=1
            ).compute()

            duration = timeProfile.size * dt.value
            sixMin = 6*60.000000
            nIntervals = int(np.ceil(duration / sixMin))
            nJumps = nIntervals - 1
            nPointsJump = int(sixMin / dt.value)
            nPointsTotal = timeProfile.size

            # Finding interval indices
            meanTProfile = np.nanmean(timeProfile)
            stdTProfile = np.std(timeProfile)
            timeProfile[timeProfile > meanTProfile + 4*stdTProfile] = meanTProfile # Get rid of strong RFI
            derivativeTProfile = np.gradient(timeProfile)
            jumpIndex = np.argmin(derivativeTProfile)
            firstJumpIndex = jumpIndex%nPointsJump
            jumpIndices = firstJumpIndex + np.arange(nJumps) * nPointsJump
            intervalEdges = np.insert(jumpIndices, 0, 0)
            intervalEdges = np.append(intervalEdges, nPointsTotal - 1)

            # Model fitting for each interval
            @custom_model
            def switchLoadFunc(t, a=1., b=1.):
                """
                    f(t) = a log_10(t) + b
                """
                return a*np.log10(t) + b
            jumpsFitted = np.ones(timeProfile.size)
            for i in range(intervalEdges.size - 1):
                lowEdge = intervalEdges[i]
                highEdge = intervalEdges[i+1]
                intervalProfile = timeProfile[lowEdge:highEdge+1]
                switchModel = switchLoadFunc(1e4, np.mean(intervalProfile))
                fitter = fitting.LevMarLSQFitter()
                times = 1 + np.arange(intervalProfile.size)
                switchModel_fit = fitter(switchModel, times, intervalProfile)
                jumpsFitted[lowEdge:highEdge+1] *= switchModel_fit(times)

            # Model fitting for each interval
            # @custom_model
            # def switchLoadFunc(t, a=1., b=1., c=1., d=1., e=1.):
            #     """
            #         f(t) = a log_10(t) + b
            #     """
            #     return (a*np.log10(t) + b) * (d * t**2 + c * t + e)
            # jumpsFitted = np.ones(timeProfile.size)
            # for i in range(intervalEdges.size - 1):
            #     lowEdge = intervalEdges[i]
            #     highEdge = intervalEdges[i+1]
            #     intervalProfile = timeProfile[lowEdge:highEdge+1]
            #     switchModel = switchLoadFunc(1e4, np.mean(intervalProfile), (intervalProfile[-1]-intervalProfile[0])/sixMin**2, (intervalProfile[-1]-intervalProfile[0])/sixMin, np.mean(intervalProfile))
            #     fitter = fitting.LevMarLSQFitter()
            #     times = 1 + np.arange(intervalProfile.size)
            #     switchModel_fit = fitter(switchModel, times, intervalProfile)
            #     jumpsFitted[lowEdge:highEdge+1] = switchModel_fit.a.value * np.log10(times) + switchModel_fit.b.value
            #     jumpsFitted[lowEdge:highEdge+1] /= switchModel_fit.a.value * np.log10(times[-1]) + switchModel_fit.b.value

            data[:, :, pol_i] /= jumpsFitted[:, None]
        return data
# ============================================================= #

