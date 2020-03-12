from pslx.core.base import Base


class ExceptionBase(Base, Exception):
    pass


class ProtobufNameNotExistException(ExceptionBase):
    pass


class ProtobufValueNotExistException(ExceptionBase):
    pass


class ProtobufEnumTypeNotExistException(ExceptionBase):
    pass


class ProtobufMessageTypeNotExistException(ExceptionBase):
    pass


class OperatorFailureException(ExceptionBase):
    pass


class OperatorStatusInconsistentException(ExceptionBase):
    pass


class OperatorDataModelInconsistentException(ExceptionBase):
    pass


class FileNotExistException(ExceptionBase):
    pass


class DirNotExistException(ExceptionBase):
    pass


class ContainerUninitializedException(ExceptionBase):
    pass


class ContainerAlreadyInitializedException(ExceptionBase):
    pass


class StorageInternalException(ExceptionBase):
    pass


class StoragePastLineException(ExceptionBase):
    pass


class StorageReadException(ExceptionBase):
    pass


class StorageWriteException(ExceptionBase):
    pass


class StorageExceedsFixedSizeException(ExceptionBase):
    pass


class FileLockToolException(ExceptionBase):
    pass


class RPCAlreadyExistException(ExceptionBase):
    pass


class RPCServerNotInitializedException(ExceptionBase):
    pass


class QueueAlreadyExistException(ExceptionBase):
    pass


class QueueConsumerNotInitializedException(ExceptionBase):
    pass


class SQLConnectionException(ExceptionBase):
    pass


class SQLNotInitializedException(ExceptionBase):
    pass


class SQLExecutionException(ExceptionBase):
    pass
