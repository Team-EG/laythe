class FlagBase:
    def __init__(self, *args, **kwargs):
        self.values = {x: getattr(self, x) for x in dir(self) if isinstance(getattr(self, x), int)}
        self.value = 0
        for x in args:
            if x.upper() not in self.values:
                raise AttributeError(f"invalid name: `{x}`")
            self.value |= self.values[x.upper()]
        for k, v in kwargs.items():
            if k.upper() not in self.values:
                raise AttributeError(f"invalid name: `{k}`")
            if v:
                self.value |= self.values[k.upper()]

    def __int__(self):
        return self.value

    def __getattr__(self, item):
        return self.has(item)

    def __iter__(self):
        for k, v in self.values.items():
            if self.has(k):
                yield v

    def has(self, name: str):
        if name.upper() not in self.values:
            raise AttributeError(f"invalid name: `{name}`")
        return (self.value & self.values[name.upper()]) == self.values[name.upper()]

    def __setattr__(self, key, value):
        orig = key
        key = key.upper()
        if orig in ["value", "values"] or key not in self.values.keys():
            return super().__setattr__(orig, value)
        if not isinstance(value, bool):
            raise TypeError(f"only type `bool` is supported.")
        has_value = self.has(key)
        if value and not has_value:
            self.value |= self.values[key]
        elif not value and has_value:
            self.value &= ~self.values[key]

    def add(self, value):
        return self.__setattr(value, True)

    def remove(self, value):
        return self.__setattr(value, False)

    @classmethod
    def from_value(cls, value: int):
        ret = cls()
        ret.value = value
        return ret
