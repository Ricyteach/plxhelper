from collections.abc import MutableSequence
from typing import overload, Iterable, TypeVar
from copy import copy

_T = TypeVar('_T')


def _guard_callable(value):
    if not callable(value):
        raise TypeError(f'{type(value).__name__} object is not callable')


def _guard_all_callable(value_iterable):
    if not all(callable(not_callable := v) for v in value_iterable):
        raise TypeError(f'{type(not_callable).__name__} object is not callable')


class TaskChain(MutableSequence):
    """A sequence of operations to be run."""
    _seq: list

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
        _guard_callable(obj)
        self._seq.append(obj)
        return obj

    def insert(self, index: int, value: _T) -> None:
        _guard_callable(value)
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

    def __setitem__(self, index, value):
        if isinstance(index, slice):
            value_tuple = tuple(value)
            _guard_all_callable(value_tuple)
            self._seq[index] = value_tuple
        else:
            _guard_callable(value)
            self._seq[index] = value

    @overload
    def __delitem__(self, index: int) -> None: ...

    @overload
    def __delitem__(self, index: slice) -> None: ...

    def __delitem__(self, index):
        del self._seq[index]

    def __len__(self) -> int:
        return len(self._seq)

    def __iter__(self):
        yield from self._seq
