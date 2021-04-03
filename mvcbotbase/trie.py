class Trie:

    def __init__(self):
        self.root = {}

    def add(self, key: str, value):
        root = self.root
        for symbol in key:
            root = root.setdefault(symbol, {})
        root["end"] = value

    def __getitem__(self, key: str):
        root = self.root
        for symbol in key:
            root = root[symbol]
        return root["end"]

    def remove(self, key: str):
        root = self.root
        dicts_stack = []
        for symbol in key:
            dicts_stack.append((root, symbol))
            root = root[symbol]
        del root["end"]
        for dict_, key in dicts_stack[::-1]:
            # Going from upper to lower element
            # If the upper dict consists of one element, delete it in lower dict
            if len(dict_[key]) == 0:
                del dict_[key]
            else:
                break
