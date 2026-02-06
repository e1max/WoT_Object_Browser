# parser.py
import re
from model import Node

INDENT = 4

LINE_RE = re.compile(r'^(?P<spaces>\s*)(?P<name>[^=]+)=\s*(?P<type><.+>)')

def parse_log(path):
    root = Node('ROOT', None, -1)
    stack = [root]

    root_object_name = None
    first_node = True

    with open(path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.rstrip()
            if not line:
                continue

            m = LINE_RE.match(line)
            if not m:
                continue

            spaces = len(m.group('spaces'))
            level = spaces // INDENT
            name = m.group('name').strip()
            type_name = m.group('type')

            # 🔴 перший реальний рядок
            if first_node:
                root_object_name = name
                first_node = False
                continue  # ❗ НЕ додаємо в дерево

            node = Node(name, type_name, level)

            while stack and stack[-1].level >= level:
                stack.pop()

            stack[-1].add_child(node)
            stack.append(node)

    return root, root_object_name

