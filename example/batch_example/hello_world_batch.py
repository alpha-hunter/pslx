from pslx.batch.operator import BatchOperator
from pslx.batch.container import DefaultBatchContainer
from pslx.util.dummy_util import DummyUtil


class HelloWorldOp(BatchOperator):

    def __init__(self, operator_name='hello_world_op'):
        super().__init__(operator_name=operator_name)

    def _execute(self):
        print(self.get_node_name())
        return True


class HelloWorldContainer(DefaultBatchContainer):
    def __init__(self):
        super().__init__(container_name='hello_world_container')


if __name__ == "__main__":
    op1 = HelloWorldOp(operator_name='hello_world_op1')
    op2 = HelloWorldOp(operator_name='hello_world_op2')
    op3 = HelloWorldOp(operator_name='hello_world_op3')
    op4 = HelloWorldOp(operator_name='hello_world_op4')
    container1 = HelloWorldContainer()
    container1.add_operator_edge(from_operator=op1, to_operator=op3)
    container1.add_operator_edge(from_operator=op1, to_operator=op4)
    container1.add_operator_edge(from_operator=op2, to_operator=op3)
    container1.add_operator_edge(from_operator=op2, to_operator=op4)
    container1.initialize()
    container1.execute()

    container2 = HelloWorldContainer()
    dummy_op = DummyUtil.dummy_bach_operator(operator_name='dummy')
    container2.add_operator_edge(from_operator=op1,
                                 to_operator=dummy_op)
    container2.add_operator_edge(from_operator=op2,
                                 to_operator=dummy_op)
    container2.add_operator_edge(from_operator=op3,
                                 to_operator=dummy_op)
    container2.add_operator_edge(from_operator=op4,
                                 to_operator=dummy_op)
    container2.initialize()
    container2.execute(num_process=4)
