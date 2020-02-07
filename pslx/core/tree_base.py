from collections import deque
from collections import OrderedDict
from pslx.core.base import Base


class TreeBase(Base):
    def __init__(self, root, max_dict_size=-1):
        super().__init__()
        self._root = root
        self._node_name_to_node_dict = OrderedDict(
            {root.get_node_name(): root}
        )
        self._max_dict_size = max_dict_size

    def add_node(self, parent_node, child_node):
        assert child_node.get_num_parents() == 0
        if parent_node != self._root:
            assert parent_node.get_num_parents() != 0

        parent_node.add_child(child_node)
        if parent_node.get_node_name() in self._node_name_to_node_dict or \
                child_node.get_node_name() in self._node_name_to_node_dict:
            self.log_print(string='Attention: node names need to be unique.')

        if parent_node.get_node_name() not in self._node_name_to_node_dict:
            self._node_name_to_node_dict[parent_node.get_node_name()] = parent_node
        if child_node.get_node_name() not in self._node_name_to_node_dict:
            self._node_name_to_node_dict[child_node.get_node_name()] = child_node
        self._clean_dict()

    def _clean_dict(self):
        while len(self._node_name_to_node_dict) > self._max_dict_size > 0:
            self._node_name_to_node_dict.popitem(last=False)

    def find_node(self, node_name):
        if node_name in self._node_name_to_node_dict:
            return self._node_name_to_node_dict[node_name]
        search_queue = deque()
        search_queue.append(self._root)
        while search_queue:
            search_node = search_queue.popleft()
            if search_node.get_node_name() == node_name:
                return search_node
            child_nodes = search_node.get_children_nodes()
            for child_node in child_nodes:
                search_node.append(child_node)
        return None

    def get_tree_size(self):
        return self.get_subtree_size(node=self._root)

    def get_subtree_size(self, node):
        if node.get_num_children() == 0:
            return 0
        else:
            result = 1
            for child_node in node.get_children_nodes():
                result += self.get_subtree_size(node=child_node)
            return result

    def bfs_search(self, max_num_node=-1):
        result_node_names, num_result_nodes = [], 0
        search_queue = deque()
        search_queue.append(self._root)
        while search_queue and max_num_node > 0 and num_result_nodes < max_num_node:
            search_node = search_queue.popleft()
            result_node_names.append(search_node.get_node_name())
            child_nodes = search_node.get_children_nodes()
            for child_node in child_nodes:
                search_node.append(child_node)
        return result_node_names

    def dfs_search(self, max_num_node=-1):
        result_node_names, num_result_nodes = [], 0
        search_stack = [self._root]
        while search_stack and max_num_node > 0 and num_result_nodes < max_num_node:
            search_node = search_stack.pop()
            result_node_names.append(search_node.get_node_name())
            child_nodes = search_node.get_children_nodes()
            for child_node in child_nodes:
                search_node.append(child_node)
        return result_node_names

    def _trim_tree(self, node, max_capacity=-1):
        if not node.is_children_ordered():
            self.log_print(string=node.get_node_name() + ' is not ordered. Be careful when you trim the tree.')

        if max_capacity <= 0 or self.get_subtree_size(node=node) <= max_capacity:
            return
        if max_capacity < 1 + node.get_num_children():
            num_children_to_trim = 1 + node.get_num_children() - max_capacity
            for child_node in node.get_children_nodes()[:num_children_to_trim]:
                child_node.delete_parent(parent_node=node)
            return
        else:
            children_nodes = node.get_num_children()
            cumulative_size = 1
            pivot_index = len(children_nodes) - 1
            while pivot_index >= 0:
                child_node = children_nodes[pivot_index]
                child_node_subtree_size = self.get_subtree_size(node=child_node)

                if cumulative_size + child_node_subtree_size < max_capacity:
                    cumulative_size += child_node_subtree_size
                    pivot_index -= 1
                else:
                    self._trim_tree(
                        node=child_node,
                        max_capacity=max_capacity-cumulative_size
                    )
                    break

            for index in range(pivot_index):
                child_node = children_nodes[index]
                child_node.delete_parent(parent_node=node)
            return

    def trim_tree(self, max_capacity=-1):
        self._trim_tree(
            node=self._root,
            max_capacity=max_capacity
        )
        return

    def get_leaves(self):
        leaf_node_names = []
        search_queue = deque()
        search_queue.append(self._root)
        while search_queue:
            search_node = search_queue.popleft()
            child_nodes = search_node.get_children_nodes()

            if len(child_nodes) == 0:
                leaf_node_names.append(search_node.get_node_name())

            for child_node in child_nodes:
                search_node.append(child_node)
        return leaf_node_names
