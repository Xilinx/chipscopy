# Copyright 2021 Xilinx, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from enum import Enum, EnumMeta
import inspect
import json
import struct
from typing import List, Any, Optional

from chipscopy.utils.printer import printer

WORD_SIZE = 4


def words_from_bytes(buf):
    words = []
    s = struct.Struct("<I")
    for i in range(0, len(buf), WORD_SIZE):
        words.append(s.unpack(buf[i : i + WORD_SIZE])[0])
    return words


def bytes_from_words(words, word_count=0):
    if not word_count:
        word_count = len(words)
    buf = bytearray(word_count * WORD_SIZE)
    count = min(len(words), word_count)
    s = struct.Struct("<I")
    start = 0
    for i in range(count):
        buf[start : start + WORD_SIZE] = s.pack(words[i])
        start += WORD_SIZE

    word_count -= count
    while word_count > 0:
        buf[start : start + WORD_SIZE] = s.pack(words[-1])
        start += WORD_SIZE
        word_count -= 1

    return buf


def word_align(addr: int) -> int:
    return int(addr / WORD_SIZE) * WORD_SIZE


def listify(item) -> List[Any]:
    if isinstance(item, list):
        return item
    elif isinstance(item, str) or isinstance(item, int) or isinstance(item, float):
        return [item]
    else:
        return list(item)


def deprecated_api(*, release: str, replacement: Optional[str] = None):
    def inner(function_to_decorate):
        def actual_decorator(*args, **kwargs):
            deprecated_func_name = list(
                filter(
                    lambda entry: entry[0] == "__name__", inspect.getmembers(function_to_decorate)
                )
            ).pop()[1]
            called_from = inspect.stack()[1]

            msg = f"{deprecated_func_name}() has been deprecated and will be removed in {release}\n"
            if replacement:
                msg += f"Please consider using the alternative {replacement}\n"
            msg += f"\nCalled from line {called_from.lineno} in file {called_from.filename}"

            printer(msg, level="warning")

            return function_to_decorate(*args, **kwargs)

        return actual_decorator

    return inner


class Enum2StrEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return str(obj)
        if isinstance(obj, EnumMeta):
            items = {item.name: item.value for item in list(obj)}
            return items
        return json.JSONEncoder.default(self, obj)
