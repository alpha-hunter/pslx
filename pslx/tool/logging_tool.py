import logging
import datetime
from inspect import getframeinfo, stack
import os
from pslx.core.base import Base
from pslx.schema.enums_pb2 import DiskLoggerLevel
from pslx.util.env_util import EnvUtil
from pslx.util.color_util import ColorsUtil
from pslx.util.timezone_util import TimezoneUtil
from pslx.util.file_util import FileUtil


class LoggingTool(Base):
    def __init__(self, name, date=datetime.datetime.utcnow(), level=DiskLoggerLevel.INFO, ttl=-1):
        super().__init__()
        if name:
            self._start_date = date
            assert '-' not in name

            self._name = name

            if level == DiskLoggerLevel.DEBUG:
                self._logging_level = logging.DEBUG
                self._suffix = 'debug'
                self._bg_color = ColorsUtil.Background.ORANGE
            elif level == DiskLoggerLevel.INFO:
                self._logging_level = logging.INFO
                self._suffix = 'info'
                self._bg_color = ColorsUtil.Background.GREEN
            elif level == DiskLoggerLevel.WARNING:
                self._logging_level = logging.WARNING
                self._suffix = 'warning'
                self._bg_color = ColorsUtil.Background.RED
            else:
                self._logging_level = logging.NOTSET
                self._suffix = 'notset'
                self._bg_color = ColorsUtil.Background.PURPLE

            self._log_file_dir = FileUtil.join_paths_to_file_with_mode(
                root_dir=FileUtil.join_paths_to_dir(
                    root_dir=EnvUtil.get_pslx_env_variable(var='PSLX_DATABASE'),
                    base_name='log'
                ),
                base_name=name,
                ttl=ttl
            )

            self._new_logger()

    def _new_logger(self):
        logging.basicConfig(level=self._logging_level)
        self._logger = logging.getLogger(self._name)
        if not os.path.exists(self._log_file_dir):
            os.makedirs(self._log_file_dir)
        file_name = self._log_file_dir + '/' + self._name + '-' + str(self._start_date.year) + '-' + str(
            self._start_date.month) + '-' + str(self._start_date.day) + '-' + self._suffix

        fh = logging.FileHandler(file_name + '.log')
        fh.setLevel(self._logging_level)
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self._logger.addHandler(fh)

    def write_log(self, string):
        now = datetime.datetime.utcnow()
        if now.date() != self._start_date.date():
            self._start_date = now
            self._new_logger()
        caller = getframeinfo(stack()[1][0])
        self._logger.info(' [' + FileUtil.base_name(caller.filename) + ': ' + str(caller.lineno) + ', ' +
                          str(TimezoneUtil.cur_time_in_pst().replace(tzinfo=None)) + ' PST]: ' + string)
