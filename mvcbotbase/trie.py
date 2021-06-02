from typing import Iterable, Hashable


class Trie:

    def __init__(self):
        self.root = {}

    def add(self, key: Iterable[Hashable], value):
        root = self.root
        for symbol in key:
            root = root.setdefault(symbol, {})
        root["end"] = value

    def __getitem__(self, key: Iterable[Hashable]):
        root = self.root
        for symbol in key:
            root = root[symbol]
        return root["end"]

    def remove(self, key: Iterable[Hashable]):
        root = self.root
        dicts_stack = []
        for symbol in key:
            dicts_stack.append((root, symbol))
            root = root[symbol]
        del root["end"]
        for dict_, key in dicts_stack[::-1]:
            # Going from upper to lower element
            # If the upper dict consists of one element, delete it in the lower
            # dict
            if len(dict_[key]) == 0:
                del dict_[key]
            else:
                break


class CaseFoldTrie(Trie):

    def add(self, key: str, value):
        Trie.add(self, key.casefold(), value)

    def __getitem__(self, key: str):
        return Trie.__getitem__(self, key.casefold())

    def remove(self, key: str):
        Trie.remove(self, key.casefold())
