from pslx.core.operator_base import OperatorBase
from pslx.schema.enums_pb2 import DataModelType
from pslx.schema.enums_pb2 import SortOrder


class BatchOperator(OperatorBase):
    DATA_MODEL = DataModelType.BATCH

    def __init__(self, operator_name, order=SortOrder.ORDER):
        super().__init__(operator_name=operator_name, order=order)

    def set_data_model(self, model):
        pass

    def unset_data_model(self):
        pass

    def convert_to_streaming_operator(self):
        self.DATA_MODEL = DataModelType.STREAMING

    def _execute(self):
        raise NotImplementedError
