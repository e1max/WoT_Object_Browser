# model.py

class Node(object):
    def __init__(self, name, type_name, level):
        self.name = name              # acceptPrebattleInvite
        self.type = type_name         # <type 'instancemethod'>
        self.level = level            # рівень вкладеності
        self.children = []            # дочірні вузли

    def add_child(self, node):
        self.children.append(node)

    def short_type(self):
        if not self.type:
            return "other"

        if "Event.Event" in self.type:
            return "event"

        if self.type.startswith("<class"):
            return "class"

        if "instancemethod" in self.type:
            return "method"

        if "function" in self.type:
            return "function"

        if "int" in self.type:
            return "int"

        if "float" in self.type:
            return "float"

        if "bool" in self.type:
            return "bool"

        if "str" in self.type:
            return "str"

        if "dict" in self.type:
            return "dict"

        if "list" in self.type:
            return "list"

        if "tuple" in self.type:
            return "tuple"

        return "other"

    def filter(self, allowed_types):
        """
        Повертає копію вузла або None
        """
        filtered_children = []

        for child in self.children:
            filtered = child.filter(allowed_types)
            if filtered:
                filtered_children.append(filtered)

        own_type = self.short_type()
        keep_self = own_type in allowed_types

        if keep_self or filtered_children:
            new_node = Node(self.name, self.type, self.level)
            new_node.children = filtered_children
            return new_node

        return None

    def filter_by_name(self, text):
        if not text:
            return self

        text = text.lower()
        matched_children = []

        for child in self.children:
            filtered = child.filter_by_name(text)
            if filtered:
                matched_children.append(filtered)

        if text in self.name.lower() or matched_children:
            new_node = Node(self.name, self.type, self.level)
            new_node.children = matched_children
            return new_node

        return None
