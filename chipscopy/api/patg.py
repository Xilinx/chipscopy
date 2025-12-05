# Copyright (C) 2025, Advanced Micro Devices, Inc. All Rights Reserved.
import csv
import time
from enum import IntEnum
from pathlib import Path

from chipscopy.utils.logger import log

DOMAIN = "patg"

# section - defines
MAX_TG_INSTRUCTIONS = 511
dbg_hub_ctrl = 0x2000_0000  # Dbg HUB control word
dbg_hub_preamble = 0x0002_800F  # Dbg HUB preamble


def dbg_hub_txn(device, addr, data):
    log[DOMAIN].debug(f"dhub wtxn: {addr:08X}, l:{len(data)} " + " ".join(f"{x:02X}" for x in data))
    device.memory_write(addr, data)


class IDType(IntEnum):
    CONSTANT_AWID_ARID = 0
    INCREMENTAL_AWID_ARID = 1


class TransactionType(IntEnum):
    READ = 0x00
    WRITE = 0x01
    WAIT = 0x02


class AddressPattern(IntEnum):
    LINEAR_ADDRESS = 0b00
    INCREMENT_BY_VALUE = 0b01
    RANDOM_ADDRESS = 0b10
    RANDOM_ALIGNED_ADDRESS = 0b11


class DataPatterns(IntEnum):
    ADDRESS_AS_DATA = 0x100
    BYTE_XOR_OF_ADDRESS_AS_DATA = 0x101
    HAMMER_DATA = 0x102


class ExpectedResponse(IntEnum):
    NONE = 0b000
    OKAY = 0b100
    EXOKAY = 0b101
    SLVERR = 0b110
    DECERR = 0b111


class PATGInstruction:
    auto_incr = "AUTO_INCR"

    def __init__(
        self,
        axi_user=0x0,
        axi_region=0x0,
        axi_qos=0x0,
        axi_prot=0x0,
        axi_cache=0x0,
        axi_lock=0x0,
        axi_burst=0x0,
        axi_size=0x0,
        axi_len=0x0,
        axi_id_type=IDType.CONSTANT_AWID_ARID,
        txn_count=0x0,
        transaction_type=TransactionType.READ,
        number_of_bytes_per_transaction=0x0,
        axi_addr_offset=0x0,
        high_addr=0x0,
        base_addr=0x0,
        seed=0x0,
        address_pattern=AddressPattern.LINEAR_ADDRESS,
        addr_incr_by=auto_incr,
        loop_address=0x0,
        loop=0x0,
        last_instruction=0x0,
        infinite_transaction=0x0,
        start_delay=0x0,
        loop_count=0x0,
        infinite_loop=0x0,
        loop_start=0x0,
        dest_id=0x0,
        data_integrity=0x0,
        wdata_pat_value=DataPatterns.ADDRESS_AS_DATA,
        loop_addr_incr_by=0x0,
        inst_id_value=0x0,
        exp_resp=ExpectedResponse.NONE,
        user_10_bit=0x0,
        last_write_read=0x0,
        user_11th_bit=0x0,
    ):
        self.axi_user = axi_user
        self.axi_region = axi_region
        self.axi_qos = axi_qos
        self.axi_prot = axi_prot
        self.axi_cache = axi_cache
        self.axi_lock = axi_lock
        self.axi_burst = axi_burst
        self.axi_size = axi_size
        self.axi_len = axi_len
        self.axi_id_type = axi_id_type
        self.txn_count = txn_count
        self.transaction_type = transaction_type
        self.number_of_bytes_per_transaction = number_of_bytes_per_transaction
        self.axi_addr_offset = axi_addr_offset
        self.high_addr = high_addr
        self.base_addr = base_addr
        self.seed = seed
        self.address_pattern = address_pattern
        self.addr_incr_by = addr_incr_by
        self.loop_address = loop_address
        self.loop = loop
        self.last_instruction = last_instruction
        self.infinite_transaction = infinite_transaction
        self.start_delay = start_delay
        self.loop_count = loop_count
        self.infinite_loop = infinite_loop
        self.loop_start = loop_start
        self.dest_id = dest_id
        self.data_integrity = data_integrity
        self.wdata_pat_value = wdata_pat_value
        self.loop_addr_incr_by = loop_addr_incr_by
        self.inst_id_value = inst_id_value
        self.exp_resp = exp_resp
        self.user_10_bit = user_10_bit
        self.last_write_read = last_write_read
        self.user_11th_bit = user_11th_bit

        self.instruction_packing = {
            "axi_user": (4, 0),
            "axi_region": (4, 4),
            "axi_qos": (4, 8),
            "axi_prot": (3, 12),
            "axi_cache": (4, 15),
            "axi_lock": (2, 19),
            "axi_burst": (2, 21),
            "axi_size": (3, 23),
            "axi_len": (8, 26),
            "axi_id_type": (1, 34),
            "txn_count": (16, 35),
            "transaction_type": (2, 51),
            "number_of_bytes_per_transaction": (48, 53),
            "axi_addr_offset": (48, 101),
            "high_addr": (48, 149),
            "base_addr": (48, 197),
            "seed": (48, 245),
            "address_pattern": (2, 293),
            "loop_address": (9, 295),
            "loop": (1, 304),
            "last_instruction": (1, 305),
            "infinite_transaction": (1, 306),
            "start_delay": (16, 307),
            "loop_count": (16, 323),
            "infinite_loop": (1, 339),
            "loop_start": (1, 340),
            "dest_id": (12, 341),
            "data_integrity": (1, 353),
            "wdata_pat_value": (9, 354),
            "loop_addr_incr_by": (16, 363),
            "inst_id_value": (16, 379),
            "exp_resp": (3, 395),
            "user_10_bit": (10, 398),
            "last_write_read": (2, 408),
            "user_11th_bit": (1, 410),
        }
        self.instruction_words = []
        self.very_wide_instruction_word = 0

        # validate ctor fields
        self._validate()

        self._initialize()

    def _initialize(self):
        # compute num_bytes_per_txn if not provided
        # this was ported from the tcl source for the IP (ptg_mem.tcl)
        if self.number_of_bytes_per_transaction == 0:
            if (
                self.transaction_type == TransactionType.WRITE
                or self.transaction_type == TransactionType.READ
            ):
                if (
                    self.axi_addr_offset == AddressPattern.RANDOM_ADDRESS
                    or self.axi_addr_offset == AddressPattern.RANDOM_ALIGNED_ADDRESS
                ):
                    self.number_of_bytes_per_transaction = 0
                else:
                    if self.addr_incr_by == PATGInstruction.auto_incr:
                        if self.axi_burst == 0 and self.axi_lock == 0:
                            self.number_of_bytes_per_transaction = 2**self.axi_size
                        else:
                            self.number_of_bytes_per_transaction = (2**self.axi_size) * (
                                self.axi_len + 1
                            )
                    else:
                        self.number_of_bytes_per_transaction = self.loop_addr_incr_by

    def load_from_csv(self, csv_data):
        def get_value_as_num(specifier: str):
            if specifier.lower().startswith("0x"):
                # noinspection PyTypeChecker
                return True, int(specifier, 16)
            elif specifier.lower().startswith("0b"):
                # noinspection PyTypeChecker
                return True, int(specifier, 2)
            elif specifier == "":
                return True, 0  # is this correct?
            else:  # try decimal
                try:
                    # noinspection PyTypeChecker
                    return True, int(specifier, 10)
                except ValueError:
                    return False, specifier  # this is a string

        for key in csv_data.keys():
            if key in ["TG_NUM", "wdata_pattern"]:  # skip TG_NUM field
                continue
            if key == "addr_incr_by":
                _, value = get_value_as_num(csv_data[key])
                self.addr_incr_by = value
                # num txn handled in _initialize()
            elif key == "cmd":
                if csv_data[key].upper() == "READ":
                    self.transaction_type = TransactionType.READ
                elif csv_data[key].upper() == "WRITE":
                    self.transaction_type = TransactionType.WRITE
                elif csv_data[key].upper() == "WAIT":
                    self.transaction_type = TransactionType.WAIT
                elif csv_data[key].upper() == "PHASE_DONE":
                    self.axi_user = 0x1
                else:
                    raise ValueError(f"Unsupported cmd: {csv_data[key]}")
            elif key == "data_integrity":
                is_int, value = get_value_as_num(csv_data[key])
                if is_int:
                    self.data_integrity = value
                else:
                    if value.upper() == "ENABLED":
                        self.data_integrity = 1
                    elif value.upper() == "DISABLED":
                        self.data_integrity = 0
                    else:
                        raise ValueError(f"Unsupported data_integrity: {value}")
            elif key == "wdata_pat_value":
                is_int, value = get_value_as_num(csv_data[key])
                if is_int:
                    if value in DataPatterns._value2member_map_:
                        self.wdata_pat_value = DataPatterns(value)
                    else:
                        self.wdata_pat_value = value
                else:
                    raise ValueError(f"Unsupported wdata_pattern: {csv_data[key]}")
            elif (
                key == "axi_id"
            ):  # axi_id can be a special type or a constant value, encoded as inst_id_value in tcl
                is_int, value = get_value_as_num(csv_data[key])
                if is_int:
                    self.axi_id_type = IDType.CONSTANT_AWID_ARID
                    setattr(self, "inst_id_value", value)
                else:
                    if value.upper() == PATGInstruction.auto_incr:
                        self.axi_id_type = IDType.INCREMENTAL_AWID_ARID
                    else:
                        raise ValueError(f"Unsupported axi_id: {csv_data[key]}")
            elif key == "exp_resp":
                if csv_data[key].upper() == "":
                    self.exp_resp = ExpectedResponse.NONE
                elif csv_data[key].upper() == "OKAY":
                    self.exp_resp = ExpectedResponse.OKAY
                elif csv_data[key].upper() == "EXOKAY":
                    self.exp_resp = ExpectedResponse.EXOKAY
                elif csv_data[key].upper() == "SLVERR":
                    self.exp_resp = ExpectedResponse.SLVERR
                elif csv_data[key].upper() == "DECERR":
                    self.exp_resp = ExpectedResponse.DECERR
                else:
                    raise ValueError(f"Unsupported exp_resp: {csv_data[key]}")
            elif key == "txn_count/loop_count/wait_option":
                _, value = get_value_as_num(csv_data[key])
                self.txn_count = value
            elif key == "start_delay/loop_operation":
                _, value = get_value_as_num(csv_data[key])
                self.start_delay = value
            else:  # general case
                if not hasattr(self, key):
                    raise ValueError(f"Unsupported field in CSV: {key}")
                _, value = get_value_as_num(csv_data[key])
                setattr(self, key, value)

    def __eq__(self, other):
        if not isinstance(other, PATGInstruction):
            return NotImplemented
        matching = True
        for field_name in self.instruction_packing.keys():
            if getattr(self, field_name) != getattr(other, field_name):
                matching = False
                break
        return matching

    def load_mem_str(self, mem_str):
        self.unpack_from_string(mem_str)

    def is_phase_done(self):
        if self.axi_user != 1:
            return False
        else:
            return True  # TODO this isn't totally correct

    def _validate(self):
        for field_name, (bit_width, _) in self.instruction_packing.items():
            # noinspection PyTypeChecker
            if self.__getattribute__(field_name) not in range(0, 2**bit_width):
                raise ValueError(
                    f"{field_name}: 0x{getattr(self, field_name):08X} is restricted to {bit_width} bits"
                )

    def pack_struct(self):
        very_wide_instruction_word = 0
        for field_name, (width, bit_shift) in self.instruction_packing.items():
            value = getattr(self, field_name)
            log[DOMAIN].trace(f"{field_name}: {value} (width: {width})")
            very_wide_instruction_word |= (value & ((1 << width) - 1)) << bit_shift

        self.very_wide_instruction_word = very_wide_instruction_word
        log[DOMAIN].trace(f"Packed very_wide_instruction_word: 0x{very_wide_instruction_word:064X}")

    def unpack_from_string(self, mem_str: str):
        if len(mem_str) != 103:
            raise ValueError(
                "Memory string must be 103 hexadecimal characters long representing 411 bits. Zero pad if necessary."
            )

        # noinspection PyTypeChecker
        big_int = int(mem_str, 16)
        for field_name, (width, bit_shift) in self.instruction_packing.items():
            value = big_int >> bit_shift & ((1 << width) - 1)
            setattr(self, field_name, value)

        self._validate()

    # print all the values after unpacking
    def __str__(self):
        rep = ""
        for field_name in self.instruction_packing.keys():
            rep += field_name + ": " + str(getattr(self, field_name)) + "\n"
        return rep

    def chop_instruction(self) -> None:
        """
        chops the 411-bit very wide instruction into a list of 32-bit words (LSB first).
        """
        self.instruction_words = []
        very_wide_instruction_word = self.very_wide_instruction_word
        while very_wide_instruction_word > 0:
            self.instruction_words.append(very_wide_instruction_word & 0xFFFFFFFF)
            very_wide_instruction_word >>= 32


class PATGTriggerInterfaceMode(IntEnum):
    AXI4_LITE = 0  # AXI4-Lite to NoC GP interface
    DIM = 1  # AXI-S Debug Hub interface connection


num_words_per_wide_instruction: int = 13  # number of 32bit words in 411bits wide instruction


class PATG:
    """Performance AXI Traffic Generator (PATG) class"""

    def __init__(
        self,
        trigger_base_address,
        tg_idx,
        device,
        interface_mode=PATGTriggerInterfaceMode.DIM,
        vio=None,
        instructions: list[PATGInstruction] = None,
    ):
        self.tg_idx = tg_idx
        self.trigger_ba = trigger_base_address
        self.interface_mode = interface_mode
        if self.interface_mode == PATGTriggerInterfaceMode.DIM:
            # tg start
            self.tg_start = ((self.tg_idx << 16) + 0x4004) >> 2
            self.tg_start |= dbg_hub_ctrl
            # instruction bram
            self.instr_bram_ba = ((self.tg_idx << 16) + 0x8000) >> 2
            # self.instr_bram_ba |= dbg_hub_ctrl
            # soft reset
            self.soft_reset = ((self.tg_idx << 16) + 0x4000) >> 2
            self.soft_reset |= dbg_hub_ctrl
        elif self.interface_mode == PATGTriggerInterfaceMode.AXI4_LITE:
            # tg start
            self.tg_start = self.trigger_ba + 0x4004
            # instruction bram
            self.instr_bram_ba = self.trigger_ba + 0x8000
            # soft reset
            self.soft_reset = self.trigger_ba + 0x4000

        self.instructions = instructions
        if self.instructions and len(self.instructions) > MAX_TG_INSTRUCTIONS - 1:
            raise ValueError(
                f"Number of instructions exceeds maximum of {MAX_TG_INSTRUCTIONS} (spare one for phase done)"
            )
        if self.instructions is None:
            self.instructions = [PATGInstruction(axi_user=0x1)]
        if not self.is_last_instr_phase_done():
            self.instructions.append(PATGInstruction(axi_user=0x1))
        self.device = device
        self.vio = vio

        # obsolete
        self.active_pattern = "Write Linear"
        self.trigger_block_rst_probe = None
        self.tg_rst_probe = None
        if self.vio:
            for probe in self.vio.probe_names:
                if probe.split("/")[-1] == "noc_sim_trig_rst_n":
                    self.trigger_block_rst_probe = probe
                if probe.split("/")[-1] == "noc_tg_tg_rst_n":
                    self.tg_rst_probe = probe

    def is_last_instr_phase_done(self):
        if len(self.instructions) == 0:
            return False
        else:
            # noinspection PyTypeChecker
            return self.instructions[-1].is_phase_done()

    def start(self):
        if self.interface_mode == PATGTriggerInterfaceMode.DIM:
            dbg_hub_txn(self.device, self.trigger_ba, [dbg_hub_preamble, self.tg_start, 0x1, 0x1])
        elif self.interface_mode == PATGTriggerInterfaceMode.AXI4_LITE:
            self.device.memory_write(self.tg_start, [0x1])
            # CR-1062874
            # Second write of the ctrl reg is required for the start command to be effective.
            time.sleep(0.5)
            self.device.memory_write(self.tg_start, [0x1])

    def stop(self):
        if self.interface_mode == PATGTriggerInterfaceMode.DIM:
            dbg_hub_txn(self.device, self.trigger_ba, [dbg_hub_preamble, self.tg_start, 0x1, 0x0])
        elif self.interface_mode == PATGTriggerInterfaceMode.AXI4_LITE:
            # this doesn't seem to be doing much
            self.device.memory_write(self.tg_start, [0x0])

        self._soft_reset()
        self._clear_instruction_memory()

    def block_reset(self):
        if self.vio is not None:
            self.vio.write_probes(
                {
                    self.trigger_block_rst_probe: 0x0,
                    self.tg_rst_probe: 0x0,
                }
            )
            self.vio.write_probes(
                {
                    self.trigger_block_rst_probe: 0x1,
                    self.tg_rst_probe: 0x1,
                }
            )

    def program(self):
        self._soft_reset()
        if self.interface_mode == PATGTriggerInterfaceMode.AXI4_LITE:
            for instruction_idx, instruction in enumerate(self.instructions):
                instruction.pack_struct()  # convert fields to very_wide_instruction_word
                instruction.chop_instruction()  # convert very_wide_instruction_word to list of 32-bit words
                self.device.memory_write(
                    self.instr_bram_ba + (0x40 * instruction_idx), instruction.instruction_words
                )
        elif self.interface_mode == PATGTriggerInterfaceMode.DIM:
            iram_words = []
            for instruction in self.instructions:
                instruction.pack_struct()  # convert fields to very_wide_instruction_word
                instruction.chop_instruction()  # convert very_wide_instruction_word to list of 32-bit words
                iram_words += instruction.instruction_words
            self.write_tg_iram(iram_words)

    def write_tg_iram(self, iram_words):
        cmd = []
        for iram_word_idx, iram_word in enumerate(iram_words):
            word_addr = self.instr_bram_ba + iram_word_idx
            if iram_word_idx == 0:
                word_addr |= dbg_hub_ctrl
            cmd.append([dbg_hub_preamble, word_addr, 0x1, iram_word])

        for row in cmd:
            dbg_hub_txn(self.device, self.trigger_ba, row)

    def set_active_pattern(self, pattern):
        self.active_pattern = pattern
        # noinspection PyTypeChecker
        instruction = self.instructions[0]
        if self.active_pattern == "Write Linear":
            instruction.transaction_type = TransactionType.WRITE
        elif self.active_pattern == "Read Linear":
            instruction.transaction_type = TransactionType.READ
        else:
            raise ValueError(f"Unsupported pattern: {pattern}")

    def _clear_instruction_memory(self):
        if self.interface_mode == PATGTriggerInterfaceMode.DIM:
            # noinspection PyTypeChecker
            for instruction_index in range(2):  # TODO full bram clear?
                for word_index in range(num_words_per_wide_instruction):
                    addr = self.instr_bram_ba + word_index + (instruction_index * 0x10)
                    if word_index == 0 and instruction_index == 0:
                        addr |= dbg_hub_ctrl
                    dbg_hub_txn(self.device, self.trigger_ba, [dbg_hub_preamble, addr, 0x1, 0x0])
        elif self.interface_mode == PATGTriggerInterfaceMode.AXI4_LITE:
            self.device.memory_write(self.instr_bram_ba, [0x0] * num_words_per_wide_instruction)
            self.device.memory_write(
                self.instr_bram_ba + 0x40, [0x0] * num_words_per_wide_instruction
            )

    def _soft_reset(self):
        if self.interface_mode == PATGTriggerInterfaceMode.DIM:
            dbg_hub_txn(self.device, self.trigger_ba, [dbg_hub_preamble, self.soft_reset, 0x1, 0x0])
            dbg_hub_txn(self.device, self.trigger_ba, [dbg_hub_preamble, self.soft_reset, 0x1, 0x1])
        elif self.interface_mode == PATGTriggerInterfaceMode.AXI4_LITE:
            self.device.memory_write(self.soft_reset, [0x0])
            self.device.memory_write(self.soft_reset, [0x1])


class PATGTrigger:
    def __init__(
        self,
        base_address: int,
        device: object,
        instructions_or_csv=None,
        interface_mode=PATGTriggerInterfaceMode.DIM,
        vio: object = None,
    ) -> None:
        """

        Args:
            base_address: the base address of the trigger block
            interface_mode: PATGTriggerInterfaceMode.DIM or PATGTriggerInterfaceMode.AXI4_LITE
            device: the device object
            instructions_or_csv: a dictionary of {tg_index: [PATGInstruction, ...]} correlated to the design
             or a path to a CSV file containing the instructions
            vio: the vio object for reset control
        """
        self.base_address = base_address
        self.device = device
        self.interface_mode = interface_mode
        self.vio = vio

        if isinstance(instructions_or_csv, (str, Path)):
            # Treat as CSV file path
            csv_path = Path(instructions_or_csv)
            with open(csv_path, "r", newline="") as csvfile:
                filtered = (line for line in csvfile if not line.lstrip().startswith("#"))
                reader = csv.reader(filtered)
                fieldnames = next(reader)
                rows = [dict(zip(fieldnames, row)) for row in reader]
                self._extract_tg_instructions_from_csv(rows)
        elif isinstance(instructions_or_csv, dict):
            # Treat as instructions dict
            self.instructions = instructions_or_csv
            self.num_tgs = len(self.instructions.keys())
        elif instructions_or_csv is None:
            self.instructions = None
            self.num_tgs = 1
        else:
            raise ValueError(
                "instructions_or_csv must be a dict of instructions or a path to a CSV file"
            )

        self.tgs = []
        self._construct_tgs()

        self.trigger_block_rst_probe = None
        self.tg_rst_probe = None
        if self.vio is not None:
            for probe in self.vio.probe_names:
                if probe.split("/")[-1] == "noc_sim_trig_rst_n":
                    self.trigger_block_rst_probe = probe
                if probe.split("/")[-1] == "noc_tg_tg_rst_n":
                    self.tg_rst_probe = probe

    def _construct_tgs(self):
        if self.instructions:
            for tg_idx, tg_instructions in self.instructions.items():
                tg = PATG(
                    self.base_address,
                    tg_idx,
                    self.device,
                    self.interface_mode,
                    self.vio,
                    self.instructions[tg_idx],
                )
                self.tgs.append(tg)
        else:
            for tg_idx in range(self.num_tgs):
                tg = PATG(self.base_address, tg_idx, self.device, self.interface_mode, self.vio)
                self.tgs.append(tg)  # tg_index is the index within this array

    def _extract_tg_instructions_from_csv(self, rows):
        self.instructions = {}
        for row in rows:
            tg_num = row["TG_NUM"]
            if tg_num == "":
                tg_idx = 0
            else:
                tg_idx = int(row["TG_NUM"])
            if tg_idx not in self.instructions:
                self.instructions[tg_idx] = []
            instr = PATGInstruction()
            instr.load_from_csv(row)
            self.instructions[tg_idx].append(instr)

    def block_reset_tgs(self):
        # iterate through and perform block level reset using the vio!
        for tg in self.tgs:
            tg.block_reset()
