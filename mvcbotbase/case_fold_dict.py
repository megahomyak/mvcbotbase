class CaseFoldDict(dict):

    def __getitem__(self, item):
        return dict.__getitem__(self, item.casefold())

    def __setitem__(self, key, value):
        dict.__setitem__(self, key.casefold(), value)

    # noinspection PyMethodOverriding
    def setdefault(self, key, default):
        return dict.setdefault(self, key.casefold(), default)

    def get(self, key, default=None):
        return self.get(key.casefold(), default)
