from pslx.core.base import Base
from pslx.batch.operator import BatchOperator
from pslx.batch.container import CronBatchContainer
from pslx.tool.filelock_tool import FileLockTool
from pslx.tool.logging_tool import LoggingTool
from pslx.util.dummy_util import DummyUtil
from pslx.util.env_util import EnvUtil
from pslx.util.file_util import FileUtil
from pslx.util.timezone_util import TimezoneUtil


class TTLCleanerOp(BatchOperator):
    def __init__(self):
        super().__init__(operator_name='ttl_cleaner_op')
        self._logger = LoggingTool(
            name=self.get_class_name(),
            ttl=EnvUtil.get_pslx_env_variable(var='PSLX_INTERNAL_TTL')
        )

    def execute_impl(self):
        start_time = TimezoneUtil.cur_time_in_local()
        self._logger.write_log("TTL cleaner started at " + str(start_time) + '.')
        all_files_under_dir = FileUtil.list_files_in_dir_recursively(
            dir_name=EnvUtil.get_pslx_env_variable(var='PSLX_DATABASE')
        )
        num_file_removed,  num_file_failed = 0, 0
        for file_name in all_files_under_dir:
            ttl = FileUtil.get_ttl_from_path(path=file_name)
            if ttl and start_time - FileUtil.get_file_modified_time(file_name=file_name) > ttl:
                self._logger.write_log("Removing file " + file_name + '...')
                try:
                    with FileLockTool(protected_file_path=file_name, read_mode=True):
                        FileUtil.remove_file(
                            file_name=file_name
                        )
                    num_file_removed += 1
                except Exception as err:
                    num_file_failed += 1
                    self._logger.write_log("Removing file " + file_name + ' failed with err ' + str(err) + '.')

        self._logger.write_log("Total number of file removed in this round is " + str(num_file_removed) + '.')
        self._logger.write_log("Total number of file failed to be removed in this round is " +
                               str(num_file_failed) + '.')
        return True


class TTLCleaner(Base):

    def __init__(self):
        super().__init__()
        self._container = CronBatchContainer(
            container_name='ttl_cleaner_container',
            ttl=EnvUtil.get_pslx_env_variable(var='PSLX_INTERNAL_TTL')
        )

    def set_schedule(self, hour, minute):
        self._container.set_schedule(
            day_of_week='mon-sun',
            hour=hour,
            minute=minute
        )

    def set_max_instances(self, max_instances):
        self._container.set_config(
            config={
                'max_instances': max_instances
            }
        )

    def execute(self):
        ttl_cleaner_op = TTLCleanerOp()
        dummy_op = DummyUtil.dummy_batch_operator(operator_name=self.get_class_name() + '_dummy')
        self._container.add_operator_edge(
            from_operator=ttl_cleaner_op,
            to_operator=dummy_op
        )
        self._container.initialize()
        self._container.execute()
