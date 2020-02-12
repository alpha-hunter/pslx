import os

from pslx.core.container_base import ContainerBase
from pslx.schema.enums_pb2 import DataModelType
from pslx.tool.logging_tool import LoggingTool
from pslx.util.proto_util import ProtoUtil


class BatchContainer(ContainerBase):
    DATA_MODEL = DataModelType.BATCH

    def __init__(self, container_name, tmp_file_folder='tmp/', ttl=-1):
        super().__init__(container_name, tmp_file_folder=tmp_file_folder, ttl=ttl)
        self._logger = LoggingTool(
            name=(self.get_class_name() + '-' +
                  ProtoUtil.get_name_by_value(enum_type=DataModelType, value=self.DATA_MODEL) + container_name),
            root_dir=os.getenv('DATA_ROOT_DIR', 'database/'),
            ttl=ttl
        )
