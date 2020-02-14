import multiprocessing

from pslx.core.graph_base import GraphBase
import pslx.core.exception as exception
from pslx.schema.enums_pb2 import DataModelType
from pslx.schema.enums_pb2 import Signal
from pslx.schema.enums_pb2 import Status
from pslx.schema.snapshots_pb2 import ContainerSnapshot
from pslx.util.file_util import FileUtil
from pslx.util.proto_util import ProtoUtil
from pslx.util.timezone_util import TimezoneUtil
from pslx.util.dummy_util import DummyUtil


class ContainerBase(GraphBase):
    DATA_MODEL = DataModelType.DEFAULT
    STATUS = Status.IDLE

    def __init__(self, container_name, tmp_file_folder='tmp/', ttl=-1):
        super().__init__()
        self._container_name = container_name
        self._is_initialized = False
        self._tmp_file_folder = FileUtil.join_paths(
            root_dir=tmp_file_folder,
            class_name=self.get_class_name() + '__' + container_name,
            ttl=ttl
        )
        self._start_time = None
        self._end_time = None
        self._logger = DummyUtil.dummy_logging()

    def initialize(self, force=False):
        for operator in self._node_name_to_node_dict.values():
            if operator.set_status() != self.STATUS:
                self.log_print("Status of " + operator.get_node_name() + " is not consistent.")
                if not force:
                    raise exception.OperatorStatusInconsistentException
                else:
                    operator.set_status(self.STATUS)
            if operator.get_data_model() != self.DATA_MODEL:
                self.log_print("Data model of " + operator.get_node_name() + " is not consistent.")
                if not force:
                    raise exception.OperatorDataModelInconsistentException
                else:
                    operator.get_data_model(self.DATA_MODEL)

        self._is_initialized = True

    def set_status(self, status):
        self.log_print("Switching to " + ProtoUtil.get_name_by_value(enum_type=Status, value=status) +
                       " status from " + ProtoUtil.get_name_by_value(enum_type=Status, value=self.STATUS) + '.')
        self.STATUS = status

    def unset_status(self):
        self.set_status(status=Status.IDLE)

    def uninitialize(self):
        self._is_initialized = False

    def add_operator_edge(self, from_operator, to_operator):
        if self._is_initialized:
            self.log_print("Cannot add more connections if the container is already initialized.")
            raise exception.ContainerAlreadyInitializedException
        self.add_direct_edge(from_node=from_operator, to_node=to_operator)

    def get_container_snapshot(self):
        if not self._is_initialized:
            self.log_print("Warning: taking snapshot when the container is not initialized.")

        snapshot = ContainerSnapshot()
        snapshot.container_name = self._container_name
        snapshot.is_initialized = self._is_initialized
        snapshot.status = self.STATUS
        if self._start_time:
            snapshot.start_time = str(self._start_time)
        if self._end_time:
            snapshot.end_time = str(self._end_time)

        for op_name, op in self._node_name_to_node_dict:
            op_output_file = FileUtil.dir_name(self._tmp_file_folder) + '/' + 'SNAPSHOT_' + \
                             str(TimezoneUtil.cur_time_in_pst()) + op_name + '.pb'
            snapshot.operator_snapshot_map[op_name] = op.get_operator_snapshot(output_file=op_output_file)

        self.log_print("Saved to file " + self._tmp_file_folder + '.')
        self._logger.write_log("Saved to file " + self._tmp_file_folder + '.')
        FileUtil.write_proto_to_file(
            proto=snapshot,
            file_name=(self._tmp_file_folder + '/' + 'SNAPSHOT_' + str(TimezoneUtil.cur_time_in_pst()) +
                       self._container_name + '.pb')
        )
        return snapshot

    def _execute(self, task_queue, finished_queue):
        for operator_name in iter(task_queue, Signal.STOP):
            self.log_print("Starting task: " + operator_name)
            self._logger.write_log("Starting task: " + operator_name)
            op = self._node_name_to_node_dict[operator_name]
            op.execute()
            self.get_container_snapshot()
            finished_queue.put(operator_name)
            self.log_print("Finished task: " + operator_name)
            self._logger.write_log("Finished task: " + operator_name)

    def execute(self, is_backfill=False, num_process=1):
        if not self._is_initialized:
            self.log_print("Cannot execute if the container is not initialized.")
            raise exception.ContainerUninitializedException
        self.get_container_snapshot()
        self.set_status(status=Status.RUNNING)
        operator_status = {}
        if is_backfill:
            operator_status = self._get_latest_status_of_operators()

        self._start_time = TimezoneUtil.cur_time_in_pst()
        task_queue, finished_queue = multiprocessing.Queue(), multiprocessing.Queue()
        process_list = []
        for _ in range(num_process):
            process = multiprocessing.Process(target=self._execute, args=(task_queue, finished_queue))
            process.start()
            process_list.append(process)

        node_levels = self.get_node_levels()
        max_level = max(node_levels.keys())
        for level in range(max_level + 1):
            for operator_name in node_levels[level]:
                if is_backfill and operator_status[operator_name] == Status.SUCCEEDED:
                    self._node_name_to_node_dict[operator_name].set_status(status=Status.SUCCEEDED)
                    continue
                task_queue.put(operator_name)
        for _ in range(num_process):
            task_queue.put(Signal.STOP)

        self._end_time = TimezoneUtil.cur_time_in_pst()

        self.set_status(status=Status.SUCCEEDED)
        for operator in self._node_name_to_node_dict.values():
            if operator.get_status() == Status.FAILED:
                self.set_status(status=Status.FAILED)
                break

        self.get_container_snapshot()
        log_str = 'Finishing order is:'
        for operator_name in finished_queue.get():
            log_str += '\t' + operator_name
        self._logger.write_log(log_str)
        self.log_print(log_str)

        for process in process_list:
            process.join()

    def _get_latest_status_of_operators(self):
        operator_status = {}
        snapshot_files = FileUtil.get_file_names(dir_name=self._tmp_file_folder)
        for snapshot_file in snapshot_files[::-1]:
            operator_name = snapshot_file.split('_')[1]
            if operator_name not in operator_status:
                operator_status[operator_name] = self._node_name_to_node_dict[operator_name].get_status_from_snapshot(
                    snapshot_file=snapshot_file
                )
            if len(operator_status) == len(self._node_name_to_node_dict):
                break
        return operator_status
