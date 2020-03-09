import ast
import os
from pslx.micro_service.rpc.rpc_base import RPCBase
from pslx.schema.enums_pb2 import Status, StorageType, PartitionerStorageType
from pslx.schema.rpc_pb2 import RPCIORequest, RPCIOResponse
from pslx.storage.default_storage import DefaultStorage
from pslx.storage.fixed_size_storage import FixedSizeStorage
from pslx.storage.proto_table_storage import ProtoTableStorage
import pslx.storage.partitioner_storage as partitioner
from pslx.tool.lru_cache_tool import LRUCacheTool
from pslx.util.proto_util import ProtoUtil


class RPCIO(RPCBase):
    REQUEST_MESSAGE_TYPE = RPCIORequest
    PARTITIONER_TYPE_TO_IMPL = {
        PartitionerStorageType.YEARLY: partitioner.YearlyPartitionerStorage,
        PartitionerStorageType.MONTHLY: partitioner.MonthlyPartitionerStorage,
        PartitionerStorageType.DAILY: partitioner.DailyPartitionerStorage,
        PartitionerStorageType.HOURLY: partitioner.HourlyPartitionerStorage,
        PartitionerStorageType.MINUTELY: partitioner.MinutelyPartitionerStorage,
    }

    def __init__(self, request_storage):
        super().__init__(service_name=self.get_class_name(), request_storage=request_storage)
        self._lru_cache_tool = LRUCacheTool(
            max_capacity=os.getenv('PSLX_INTERNAL_CACHE', 100)
        )
        self._storage_type_to_impl_func = {
            StorageType.DEFAULT_STORAGE: self._default_storage_impl,
            StorageType.FIXED_SIZE_STORAGE: self._fixed_size_storage_impl,
            StorageType.PROTO_TABLE_STORAGE: self._proto_table_storage_impl,
            StorageType.PARTITIONER_STORAGE: self._partitioner_storage_impl,
        }

    def _default_storage_impl(self, request):
        read_params = dict(request.params)
        lru_key = (request.type, request.file_name)
        storage = self._lru_cache_tool.get(key=lru_key)
        if not storage:
            storage = DefaultStorage()
            storage.initialize_from_file(file_name=request.file_name)
            self._lru_cache_tool.set(
                key=lru_key,
                value=storage
            )
        if 'num_line' in read_params:
            read_params['num_line'] = int(read_params['num_line'])
        response = RPCIOResponse()
        data = storage.read(params=read_params)
        for item in data:
            response.data.append(item)
        return response

    def _fixed_size_storage_impl(self, request):
        read_params = dict(request.params)
        lru_key = (request.type, request.file_name)
        if 'fixed_size' in read_params:
            lru_key += (read_params['fixed_size'],)
        if 'force_load' in read_params:
            read_params['force_load'] = ast.literal_eval(read_params['force_load'])
        if 'num_line' in read_params:
            read_params['num_line'] = int(read_params['num_line'])

        storage = self._lru_cache_tool.get(key=lru_key)
        if not storage:
            if 'fixed_size' in read_params:
                storage = FixedSizeStorage(fixed_size=int(read_params['fixed_size']))
            else:
                storage = FixedSizeStorage()
            storage.initialize_from_file(file_name=request.file_name)
            self._lru_cache_tool.set(
                key=lru_key,
                value=storage
            )
        read_params.pop('fixed_size', None)
        response = RPCIOResponse()
        data = storage.read(params=read_params)
        for item in data:
            response.data.append(item)
        return response

    def _proto_table_storage_impl(self, request):
        read_params = dict(request.params)
        lru_key = (request.type, request.file_name)
        storage = self._lru_cache_tool.get(key=lru_key)
        if not storage:
            storage = ProtoTableStorage()
            storage.initialize_from_file(file_name=request.file_name)
            self._lru_cache_tool.set(
                key=lru_key,
                value=storage
            )
        read_params['message_type'] = ProtoUtil.infer_message_type_from_str(
            message_type_str=read_params['message_type']
        )
        return storage.read(params=read_params)

    def _partitioner_storage_impl(self, request):
        read_params = dict(request.params)
        lru_key = (read_params['PartitionerStorageType'], request.dir_name)
        storage = self._lru_cache_tool.get(key=lru_key)
        if not storage:
            partitioner_type = ProtoUtil.get_value_by_name(
                enum_type=PartitionerStorageType,
                name=read_params['PartitionerStorageType']
            )
            storage = self.PARTITIONER_TYPE_TO_IMPL[partitioner_type]()
            storage.initialize_from_dir(dir_name=request.dir_name)
            self._lru_cache_tool.set(
                key=lru_key,
                value=storage
            )

        read_params['num_line'] = -1
        read_params.pop('PartitionerStorageType', None)
        data = storage.read(params=read_params)

        response = RPCIOResponse()
        for item in data:
            response.data.append(item)
        return response

    def send_request_impl(self, request):
        if request.is_test:
            return self.REQUEST_MESSAGE_TYPE(), Status.SUCCEEDED

        response = self._storage_type_to_impl_func[request.type](request=request)
        return response, Status.SUCCEEDED
