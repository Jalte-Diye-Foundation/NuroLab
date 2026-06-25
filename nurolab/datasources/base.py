# File: nurolab/datasources/base.py
from abc import ABC, abstractmethod
import numpy as np


class EEGDataSource(ABC):
    """
    Abstract interface that ALL data sources implement.
    Public datasets, CSV files, and live hardware all look
    identical to the rest of the pipeline through this class.

    The entire pipeline — filters, windowing, feature extraction,
    ML, the app — calls only these methods. It never knows or cares
    whether the bytes came from a 2021 OpenNeuro recording or a live
    device fifteen seconds ago.
    """

    @property
    @abstractmethod
    def sample_rate(self) -> float:
        """Sampling rate in Hz, e.g. 256.0 or 512.0"""
        pass

    @property
    @abstractmethod
    def channel_names(self) -> list:
        """e.g. ['Fp1', 'Fp2', 'F3', 'F4', 'T7', 'T8', 'O1', 'O2']"""
        pass

    @property
    @abstractmethod
    def n_channels(self) -> int:
        pass

    @abstractmethod
    def read_chunk(self, n_samples: int):
        """
        Returns the next n_samples of data.
        Shape: (n_samples, n_channels), values in microvolts (uV).
        Returns None when the source is exhausted (offline mode).
        For a live source, this call BLOCKS until enough data exists.
        """
        pass

    @abstractmethod
    def is_live(self) -> bool:
        """True for real-time hardware, False for offline datasets."""
        pass

    def close(self):
        """Optional cleanup hook. Override if needed."""
        pass
