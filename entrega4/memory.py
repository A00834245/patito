from __future__ import annotations

from dataclasses import dataclass

# Address ranges (inclusive start; grow upwards)
@dataclass(frozen=True)
class SegmentRanges:
    global_int: int = 1000
    global_float: int = 2000
    global_bool: int = 3000
    global_str: int = 4000

    local_int: int = 6000
    local_float: int = 7000
    local_bool: int = 8000
    local_str: int = 9000

    const_int: int = 14000
    const_float: int = 15000
    const_bool: int = 16000
    const_str: int = 17000

    temp_int: int = 20000
    temp_float: int = 21000
    temp_bool: int = 22000
    temp_str: int = 23000


class AddressAllocator:
    def __init__(self, ranges: SegmentRanges | None = None) -> None:
        self.r = ranges or SegmentRanges()
        self._counters = {
            'global': {'int': self.r.global_int, 'float': self.r.global_float, 'bool': self.r.global_bool, 'string': self.r.global_str},
            'local': {'int': self.r.local_int, 'float': self.r.local_float, 'bool': self.r.local_bool, 'string': self.r.local_str},
            'const': {'int': self.r.const_int, 'float': self.r.const_float, 'bool': self.r.const_bool, 'string': self.r.const_str},
            'temp': {'int': self.r.temp_int, 'float': self.r.temp_float, 'bool': self.r.temp_bool, 'string': self.r.temp_str},
        }

    def _next(self, segment: str, ty: str) -> int:
        cur = self._counters[segment][ty]
        self._counters[segment][ty] += 1
        return cur

    def global_var(self, ty: str) -> int:
        return self._next('global', ty)

    def local_var(self, ty: str) -> int:
        return self._next('local', ty)

    def const(self, ty: str) -> int:
        return self._next('const', ty)

    def temp(self, ty: str) -> int:
        return self._next('temp', ty)


class ConstantTable:
    def __init__(self, allocator: AddressAllocator) -> None:
        self.alloc = allocator
        self._pool_int: dict[int, int] = {}
        self._pool_float: dict[float, int] = {}
        self._pool_bool: dict[bool, int] = {}
        self._pool_str: dict[str, int] = {}

    def intern(self, val, ty: str) -> int:
        if ty == 'int':
            if val not in self._pool_int:
                self._pool_int[val] = self.alloc.const('int')
            return self._pool_int[val]
        if ty == 'float':
            if val not in self._pool_float:
                self._pool_float[val] = self.alloc.const('float')
            return self._pool_float[val]
        if ty == 'bool':
            if val not in self._pool_bool:
                self._pool_bool[val] = self.alloc.const('bool')
            return self._pool_bool[val]
        if ty == 'string':
            if val not in self._pool_str:
                self._pool_str[val] = self.alloc.const('string')
            return self._pool_str[val]
        raise ValueError(f'Unknown const type: {ty}')
