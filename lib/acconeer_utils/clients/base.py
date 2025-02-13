from abc import ABCMeta, abstractmethod
import logging
from distutils.version import StrictVersion

from acconeer_utils import SDK_VERSION


log = logging.getLogger(__name__)


class BaseClient(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, **kwargs):
        self.squeeze = kwargs.get("squeeze", True)

        self._connected = False
        self._session_setup_done = False
        self._streaming_started = False

    def connect(self):
        if self._connected:
            raise ClientError("already connected")

        info = self._connect()
        self._connected = True

        if info is None:
            info = {}

        try:
            log.info("reported version: {}".format(info["version_str"]))

            if info["strict_version"] < StrictVersion(SDK_VERSION):
                log.warning("old server version - please upgrade server")
            elif info["strict_version"] > StrictVersion(SDK_VERSION):
                log.warning("new server version - please upgrade client")
        except KeyError:
            log.warning("could not read software version (might be too old)")

        return info

    def setup_session(self, config):
        if self._streaming_started:
            raise ClientError("can't setup session while streaming")

        if not self._connected:
            self.connect()

        session_info = self._setup_session(config)
        self._session_setup_done = True

        try:
            start_ok = abs(config.range_start - session_info["actual_range_start"]) < 0.01
            len_ok = abs(config.range_length - session_info["actual_range_length"]) < 0.01
        except (AttributeError, KeyError, TypeError):
            pass
        else:
            if not start_ok or not len_ok:
                log.warning("actual measured range differs from the requested")

        return session_info

    def start_streaming(self, config=None):
        if self._streaming_started:
            raise ClientError("already streaming")

        if config is None:
            ret = None
        else:
            ret = self.setup_session(config)

        if not self._session_setup_done:
            raise ClientError("session needs to be set up before starting stream")

        self._start_streaming()
        self._streaming_started = True
        return ret

    def get_next(self):
        if not self._streaming_started:
            raise ClientError("must be streaming to get next")

        return self._get_next()

    def stop_streaming(self):
        if not self._streaming_started:
            raise ClientError("not streaming")

        self._stop_streaming()
        self._streaming_started = False

    def disconnect(self):
        if not self._connected:
            raise ClientError("not connected")

        if self._streaming_started:
            self.stop_streaming()

        self._disconnect()
        self._connected = False

    @abstractmethod
    def _connect(self):
        pass

    @abstractmethod
    def _setup_session(self, config):
        pass

    @abstractmethod
    def _start_streaming(self):
        pass

    @abstractmethod
    def _get_next(self):
        pass

    @abstractmethod
    def _stop_streaming(self):
        pass

    @abstractmethod
    def _disconnect(self):
        pass


class ClientError(Exception):
    pass


def decode_version_str(version: str):
    if "-" in version:
        strict_version = StrictVersion(version.split("-")[0])
    else:
        strict_version = StrictVersion(version)

    return {
        "version_str": version,
        "strict_version": strict_version,
    }
