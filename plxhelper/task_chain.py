from collections.abc import MutableSequence
from typing import overload, Iterable, TypeVar
from copy import copy

_T = TypeVar('_T')


class TaskChain(MutableSequence):

    def __init__(self):
        self._seq = []

    def __getattr__(self, item):
        try:
            index = [
                        # call to __dict__ is a workaround to get copy() to work
                        obj.__name__ for obj in self.__dict__['_seq']
                    ].index(item)+1
        except (ValueError, KeyError):
            raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}')
        return self[:index]

    def __call__(self):
        yield from (step() for step in self._seq)

    def link(self, obj):
        self._seq.append(obj)
        return obj

    def insert(self, index: int, value: _T) -> None:
        self._seq.insert(index, value)

    @overload
    def __getitem__(self, index: int) -> _T: ...

    @overload
    def __getitem__(self, index: slice) -> MutableSequence[_T]: ...

    def __getitem__(self, index):
        seq_get_result = self._seq[index]
        if not isinstance(seq_get_result, list):
            return seq_get_result
        cp = copy(self)
        cp._seq = seq_get_result
        return cp

    @overload
    def __setitem__(self, index: int, value: _T) -> None: ...

    @overload
    def __setitem__(self, index: slice, value: Iterable[_T]) -> None: ...

    def __setitem__(self, index: int, value: _T) -> None:
        self._seq[index] = value

    @overload
    def __delitem__(self, index: int) -> None: ...

    @overload
    def __delitem__(self, index: slice) -> None: ...

    def __delitem__(self, index: int) -> None:
        del self._seq[index]

    def __len__(self) -> int:
        return len(self._seq)
