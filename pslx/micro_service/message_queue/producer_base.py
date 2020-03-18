import datetime
import pika
import uuid
from pslx.core.base import Base
from pslx.schema.rpc_pb2 import GenericRPCRequest, GenericRPCResponse
from pslx.util.dummy_util import DummyUtil
from pslx.util.proto_util import ProtoUtil
from pslx.util.timezone_util import TimezoneUtil, TimeSleepObj


class ProducerBase(Base):
    RESPONSE_MESSAGE_TYPE = None

    def __init__(self, exchange, queue_name, connection_str):
        super().__init__()
        self._logger = DummyUtil.dummy_logging()
        self._connection = pika.BlockingConnection(
            pika.URLParameters(connection_str)
        )
        self._channel = self._connection.channel()
        self._queue_name = queue_name
        self._exchange = exchange
        self._channel.confirm_delivery()
        self._channel.basic_consume(
            queue=queue_name,
            on_message_callback=self.on_response,
            auto_ack=True)

        self._corr_id = None
        self._response = None

    def on_response(self, ch, method, props, body):
        if self._corr_id == props.correlation_id:
            self._response = ProtoUtil.json_to_message(
                message_type=GenericRPCResponse,
                json_str=body
            )

    def get_queue_name(self):
        return self._queue_name

    @classmethod
    def get_response_type(cls):
        return cls.RESPONSE_MESSAGE_TYPE

    def send_request(self, request):
        generic_request = GenericRPCRequest()
        generic_request.request_data.CopyFrom(ProtoUtil.message_to_any(message=request))
        generic_request.timestamp = str(TimezoneUtil.cur_time_in_pst())
        generic_request.uuid = str(uuid.uuid4())
        if self.RESPONSE_MESSAGE_TYPE:
            generic_request.message_type = ProtoUtil.infer_str_from_message_type(
                    message_type=self.RESPONSE_MESSAGE_TYPE
                )
        self.sys_log("Getting request of uuid " + generic_request.uuid + '.')
        try:
            generic_request_str = ProtoUtil.message_to_json(
                proto_message=generic_request
            )
            self._channel.basic_publish(
                exchange=self._exchange,
                routing_key=self._queue_name,
                properties=pika.BasicProperties(
                    reply_to=self._queue_name,
                    correlation_id=self._corr_id,
                    delivery_mode=2
                ),
                body=generic_request_str)
            wait_start_time = TimezoneUtil.cur_time_in_pst()
            while not self._response:
                self._connection.process_data_events(time_limit=TimeSleepObj.ONE_MINUTE * 3)
                if TimezoneUtil.cur_time_in_pst() - wait_start_time > \
                        datetime.timedelta(seconds=TimeSleepObj.ONE_MINUTE * 3):
                    break

            if not self.RESPONSE_MESSAGE_TYPE:
                return None
            else:
                return ProtoUtil.any_to_message(
                    message_type=self.RESPONSE_MESSAGE_TYPE,
                    any_message=self._response.response_data
                )
        except Exception as err:
            self._logger.error(self.get_class_name() + " send request with error " + str(err) + '.')
            self.sys_log(self.get_class_name() + " send request with error " + str(err) + '.')
            pass

