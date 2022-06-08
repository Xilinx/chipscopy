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
import enum
from typing import Union


def replace_enum_values(dd: {}) -> None:
    """Replace enum values with their text strings."""
    to_update = {key: val.name for key, val in dd.items() if isinstance(val, enum.Enum)}
    if to_update:
        dd.update(to_update)


def prop_to_enum(props: {}, enum_types: ()) -> None:
    for p_name, p_type in enum_types:
        if isinstance(props[p_name], str):
            props[p_name] = p_type[props[p_name]]


__probe_value_hex_to_bin__ = {
    "0": "0000",
    "1": "0001",
    "2": "0010",
    "3": "0011",
    "4": "0100",
    "5": "0101",
    "6": "0110",
    "7": "0111",
    "8": "1000",
    "9": "1001",
    "a": "1010",
    "b": "1011",
    "c": "1100",
    "d": "1101",
    "e": "1110",
    "f": "1111",
    "x": "xxxx",
    "_": "",  # Don't keep underscore.
}

# 4-bit values created with { f'{idx:04b}'[::-1]: hex(idx)[2] for idx in range(16) }
__bin_reversed_to_hex__ = {
    # Keys: binary values with reversed bit order.
    "0": "0",
    "1": "1",
    "00": "0",
    "10": "1",
    "01": "2",
    "11": "3",
    "000": "0",
    "100": "1",
    "010": "2",
    "110": "3",
    "001": "4",
    "101": "5",
    "011": "6",
    "111": "7",
    "0000": "0",
    "1000": "1",
    "0100": "2",
    "1100": "3",
    "0010": "4",
    "1010": "5",
    "0110": "6",
    "1110": "7",
    "0001": "8",
    "1001": "9",
    "0101": "A",
    "1101": "B",
    "0011": "C",
    "1011": "D",
    "0111": "E",
    "1111": "F",
}


__hex_char_reversed__ = {
    "0": "0",
    "1": "8",
    "2": "4",
    "3": "C",
    "4": "2",
    "5": "A",
    "6": "6",
    "7": "E",
    "8": "1",
    "9": "9",
    "A": "5",
    "B": "D",
    "C": "3",
    "D": "B",
    "E": "7",
    "F": "F",
}


def bin_reversed_to_hex(bin_value: str) -> str:
    hex_chars = [
        __bin_reversed_to_hex__[bin_value[idx : idx + 4]]
        for idx in reversed(range(0, len(bin_value), 4))
    ]
    return "".join(hex_chars)


def int_reversed_to_hex(val: int, bit_width: int) -> str:
    # 4 bit_len examples:  4 => '2', 3 -> 'C'
    # 3 bit_len examples:  4 => '1', 3 -> '6'
    bin_value = f"{val:0{bit_width}b}"
    return bin_reversed_to_hex(bin_value)


def bin_reversed_to_hex_values(bin_values: [str]) -> [str]:
    return [bin_reversed_to_hex(val) for val in bin_values]


def to_bin_str(val: Union[int, str], bit_width: int, enum_def: enum.EnumMeta = None) -> str:
    is_hex = is_hex_str(val, bit_width)

    if isinstance(val, enum.Enum):
        val = val.value
    elif enum_def and type(val) == str and not is_hex:
        try:
            val = enum_def[val].value
        except ValueError:
            # Keep going. val is not a enum name.
            pass
    if isinstance(val, int):
        # Both positive and negative integers, with '0'/'1' fill.
        return f"{val:0{bit_width}b}" if val >= 0 else bin((1 << bit_width) + val)[2:]
    if is_hex:
        bin_val = "".join([__probe_value_hex_to_bin__[ch] for ch in val[2:].lower()])
        start_index = len(bin_val) - bit_width
        return bin_val[start_index:]
    else:
        # Already a binary string.
        return val


def bytearray_bit_reversed_to_hex(buffer: bytearray) -> str:
    """Bit-order is reversed for buffer and converted to hex-string."""
    # Hex string in reverse byte order. LSB will be first in 'hex_list'.
    hex_list = list(buffer.hex().upper())
    # Swap upper/lower hex char, within each byte.
    for idx in range(0, len(hex_list), 2):
        hex_list[idx], hex_list[idx + 1] = hex_list[idx + 1], hex_list[idx]
    # Reverse bits in each hex char.
    hex_reversed = "".join([__hex_char_reversed__[ch] for ch in hex_list])
    return hex_reversed


__byte_bit_reversed__ = None


def _get_reversed_byte(bb: int):
    global __byte_bit_reversed__
    if not __byte_bit_reversed__:
        __byte_bit_reversed__ = [int(f"{bb:08b}"[::-1], 2) for bb in range(256)]
    return __byte_bit_reversed__[bb]


def bytearray_each_32bit_word_reversed_to_hex(buffer: bytearray) -> str:
    """Bit-order for each 32 bits are reversed and converted to hex-string."""
    if len(buffer) % 4 != 0:
        raise IndexError("Data is not aligned on 4 byte boundary.")
    buf2 = bytearray(len(buffer))
    for idx in range(0, len(buffer), 4):
        buf2[idx] = _get_reversed_byte(buffer[idx + 3])
        buf2[idx + 1] = _get_reversed_byte(buffer[idx + 2])
        buf2[idx + 2] = _get_reversed_byte(buffer[idx + 1])
        buf2[idx + 3] = _get_reversed_byte(buffer[idx])

    hex_list = [f"{bb:02X}" for bb in reversed(buf2)]
    return "".join(hex_list)


def round_up_to_power_of_two(num: int) -> int:
    return 1 if num == 0 else 1 << (num - 1).bit_length()


def round_down_to_power_of_two(num: int) -> int:
    return 1 if num == 0 else 1 << (num.bit_length() - 1)


def is_hex_str(number, bit_width: int) -> bool:
    # 2 bit value "0x" is binary.
    # 3 bit value "0x?" is interpreted as binary, not hex.
    return (
        isinstance(number, str)
        and number.startswith(("0x", "0X"))
        and bit_width != len(number) - number.count("_")
    )
