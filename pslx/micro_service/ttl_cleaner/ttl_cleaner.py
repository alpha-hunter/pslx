from pslx.batch.operator import BatchOperator
from pslx.batch.container import CronBatchContainer
from pslx.tool.filelock_tool import FileLockTool
from pslx.tool.logging_tool import LoggingTool
from pslx.util.dummy_util import DummyUtil
from pslx.util.env_util import EnvUtil
from pslx.util.file_util import FileUtil
from pslx.util.timezone_util import TimezoneUtil, TimeSleepObj


class TTLCleanerOp(BatchOperator):
    def __init__(self):
        super().__init__(operator_name='ttl_cleaner_op')
        self._logger = LoggingTool(
            name='PSLX_TTL_CLEANER_OP',
            ttl=EnvUtil.get_pslx_env_variable(var='PSLX_INTERNAL_TTL')
        )
        self._ttl_dir = [EnvUtil.get_pslx_env_variable(var='PSLX_DATABASE')]

    def watch_dir(self, dir_name):
        self._ttl_dir.append(dir_name)

    def _recursively_check_dir_deletable(self, dir_name):
        if FileUtil.list_files_in_dir(dir_name=dir_name):
            return False
        sub_dirs = FileUtil.list_dirs_in_dir(dir_name=dir_name)
        if sub_dirs:
            for sub_dir in sub_dirs:
                if not self._recursively_check_dir_deletable(dir_name=sub_dir):
                    return False

        return True

    def _delete_file(self, cur_time, path_name):
        num_file_removed, num_file_failed = 0, 0
        if FileUtil.is_file(path_name=path_name):
            ttl = FileUtil.get_ttl_from_path(path_name=path_name)
            if ttl and cur_time - FileUtil.get_file_modified_time(file_name=path_name) > ttl:
                self._logger.info("Removing file " + path_name + '...')
                try:
                    with FileLockTool(protected_file_path=path_name, read_mode=True,
                                      timeout=TimeSleepObj.ONE_TENTH_SECOND):
                        FileUtil.remove_file(
                            file_name=path_name
                        )
                    num_file_removed += 1
                    self.counter_increment("num_file_removed")
                except Exception as err:
                    num_file_failed += 1
                    self.counter_increment("num_file_failed_to_be_removed")
                    self._logger.error("Removing file " + cur_time + ' failed with err ' + str(err) + '.')
        else:
            for file_name in FileUtil.list_files_in_dir(dir_name=path_name):
                stats = self._delete_file(cur_time=cur_time, path_name=file_name)
                num_file_removed += stats[0]
                num_file_failed += stats[1]
            for dir_name in FileUtil.list_dirs_in_dir(dir_name=path_name):
                stats = self._delete_file(cur_time=cur_time, path_name=dir_name)
                num_file_removed += stats[0]
                num_file_failed += stats[1]

        return num_file_removed, num_file_failed

    def _delete_dir(self, dir_name):
        num_dir_removed, num_dir_failed = 0, 0
        for sub_dir_name in FileUtil.list_dirs_in_dir(dir_name=dir_name):
            if FileUtil.does_dir_exist(dir_name=sub_dir_name) and self._recursively_check_dir_deletable(
                    dir_name=sub_dir_name):
                self._logger.info("Removing directory " + sub_dir_name + '...')
                try:
                    FileUtil.remove_dir_recursively(dir_name=sub_dir_name)
                    self.counter_increment("num_directory_removed")
                    num_dir_removed += 1
                except Exception as err:
                    num_dir_failed += 1
                    self.counter_increment("num_directory_failed_to_be_removed")
                    self._logger.error("Removing directory " + sub_dir_name + ' failed with err ' + str(err) + '.')
            else:
                stats = self._delete_dir(dir_name=sub_dir_name)
                num_dir_removed += stats[0]
                num_dir_failed += stats[1]
        return num_dir_removed, num_dir_failed

    def execute_impl(self):
        start_time = TimezoneUtil.cur_time_in_local()
        self._logger.info("TTL cleaner started at " + str(start_time) + '.')
        num_file_removed,  num_file_failed = 0, 0
        for ttl_dir_name in list(set(self._ttl_dir)):
            self._logger.info("TTL cleaner starts to check dir " + ttl_dir_name + " for file deletion.")
            stats = self._delete_file(
                cur_time=start_time,
                path_name=ttl_dir_name
            )
            num_file_removed += stats[0]
            num_file_failed += stats[1]

        self._logger.info("Total number of file removed in this round is " + str(num_file_removed) + '.')
        self._logger.info("Total number of file failed to be removed in this round is " +
                          str(num_file_failed) + '.')

        num_dir_removed, num_dir_failed = 0, 0
        for ttl_dir_name in list(set(self._ttl_dir)):
            self._logger.info("TTL cleaner starts to check dir " + ttl_dir_name + " for directory deletion.")
            stats = self._delete_dir(
                dir_name=ttl_dir_name
            )
            num_dir_removed += stats[0]
            num_dir_failed += stats[1]

        self._logger.info("Total number of directory removed in this round is " + str(num_dir_removed) + '.')
        self._logger.info("Total number of directory failed to be removed in this round is " +
                          str(num_dir_failed) + '.')


class TTLCleaner(CronBatchContainer):

    def __init__(self, container_name='PSLX_TTL_CLEANER_CONTAINER'):
        super().__init__(container_name=container_name, ttl=EnvUtil.get_pslx_env_variable(var='PSLX_INTERNAL_TTL'))

    def set_schedule(self, hour, minute):
        self.add_schedule(
            day_of_week='mon-sun',
            hour=hour,
            minute=minute
        )

    def set_max_instances(self, max_instances):
        self.set_config(
            config={
                'max_instances': max_instances
            }
        )

    def start(self):
        ttl_cleaner_op = TTLCleanerOp()
        dummy_op = DummyUtil.dummy_batch_operator(operator_name=self.get_class_name() + '_dummy')
        self.add_operator_edge(
            from_operator=ttl_cleaner_op,
            to_operator=dummy_op
        )
        self.initialize()
        self.execute()
