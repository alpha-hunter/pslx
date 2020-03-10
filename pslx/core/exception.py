from pslx.core.base import Base


class ExceptionBase(Base, Exception):
    pass


class ProtobufException(ExceptionBase):
    pass


class ProtobufNameNotExistException(ProtobufException):
    pass


class ProtobufValueNotExistException(ProtobufException):
    pass


class ProtobufEnumTypeNotExistException(ProtobufException):
    pass


class ProtobufMessageTypeNotExistException(ProtobufException):
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
