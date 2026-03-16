import ctypes
import os
from ctypes import POINTER, byref, c_char_p, c_uint32, c_uint64, c_void_p
from dataclasses import dataclass
from pathlib import Path


ALL_ONES = (1 << 64) - 1


class LxsApiError(RuntimeError):
    pass


@dataclass(frozen=True)
class PlanCounts:
    input_count: int
    output_count: int
    net_count: int
    level_count: int
    chunk_count: int
    macro_count: int
    multi_macro_count: int
    standard_mux_count: int
    standard_add_count: int
    standard_cmp_count: int
    standard_alu_count: int
    functional_region_count: int
    register_count: int
    rom_count: int
    ram_count: int
    regfile_count: int


@dataclass(frozen=True)
class Probes:
    input_apply: int
    chunk_exec: int
    gate_eval: int
    dff_exec: int
    tick_count: int
    state_commit_count: int
    input_toggle: int
    state_change_commit: int
    contention_count: int
    unknown_state_materialize_count: int
    highz_materialize_count: int
    multi_driver_resolve_count: int
    tri_no_drive_count: int
    pup_z_source_count: int
    pdn_z_source_count: int


class _PlanCountsC(ctypes.Structure):
    _fields_ = [
        ("input_count", c_uint32),
        ("output_count", c_uint32),
        ("net_count", c_uint32),
        ("level_count", c_uint32),
        ("chunk_count", c_uint32),
        ("macro_count", c_uint32),
        ("multi_macro_count", c_uint32),
        ("standard_mux_count", c_uint32),
        ("standard_add_count", c_uint32),
        ("standard_cmp_count", c_uint32),
        ("standard_alu_count", c_uint32),
        ("functional_region_count", c_uint32),
        ("register_count", c_uint32),
        ("rom_count", c_uint32),
        ("ram_count", c_uint32),
        ("regfile_count", c_uint32),
    ]


class _ProbesC(ctypes.Structure):
    _fields_ = [
        ("input_apply", c_uint64),
        ("chunk_exec", c_uint64),
        ("gate_eval", c_uint64),
        ("dff_exec", c_uint64),
        ("tick_count", c_uint64),
        ("state_commit_count", c_uint64),
        ("input_toggle", c_uint64),
        ("state_change_commit", c_uint64),
        ("contention_count", c_uint64),
        ("unknown_state_materialize_count", c_uint64),
        ("highz_materialize_count", c_uint64),
        ("multi_driver_resolve_count", c_uint64),
        ("tri_no_drive_count", c_uint64),
        ("pup_z_source_count", c_uint64),
        ("pdn_z_source_count", c_uint64),
    ]


class LxsApiLibrary:
    def __init__(self, dll_path: str | Path | None = None):
        self.dll_path = Path(dll_path) if dll_path is not None else self._default_dll_path()
        if not self.dll_path.exists():
            raise LxsApiError(f"lxs_api.dll not found at {self.dll_path}")
        if os.name == "nt":
            os.add_dll_directory(str(self.dll_path.parent))
        self.lib = ctypes.CDLL(str(self.dll_path))
        self._bind()

    @staticmethod
    def _default_dll_path() -> Path:
        ui_repo = Path(__file__).resolve().parents[2]
        lxs_repo = ui_repo.parent / "LXS"
        return lxs_repo / "build" / "bin" / "lxs_api.dll"

    def _bind(self):
        lib = self.lib
        lib.lxs_api_result_string.argtypes = [ctypes.c_int]
        lib.lxs_api_result_string.restype = c_char_p
        lib.lxs_api_get_last_error.argtypes = []
        lib.lxs_api_get_last_error.restype = c_char_p

        lib.lxs_api_netlist_load_bench.argtypes = [c_char_p, POINTER(c_void_p)]
        lib.lxs_api_netlist_load_bench.restype = ctypes.c_int
        lib.lxs_api_netlist_free.argtypes = [c_void_p]
        lib.lxs_api_netlist_free.restype = None

        lib.lxs_api_plan_compile.argtypes = [c_void_p, POINTER(c_void_p)]
        lib.lxs_api_plan_compile.restype = ctypes.c_int
        lib.lxs_api_plan_free.argtypes = [c_void_p]
        lib.lxs_api_plan_free.restype = None
        lib.lxs_api_plan_get_counts.argtypes = [c_void_p, POINTER(_PlanCountsC)]
        lib.lxs_api_plan_get_counts.restype = ctypes.c_int
        lib.lxs_api_plan_get_input_name.argtypes = [c_void_p, c_uint32, POINTER(c_char_p)]
        lib.lxs_api_plan_get_input_name.restype = ctypes.c_int
        lib.lxs_api_plan_get_output_name.argtypes = [c_void_p, c_uint32, POINTER(c_char_p)]
        lib.lxs_api_plan_get_output_name.restype = ctypes.c_int
        lib.lxs_api_plan_find_net.argtypes = [c_void_p, c_char_p, POINTER(c_uint32)]
        lib.lxs_api_plan_find_net.restype = ctypes.c_int

        lib.lxs_api_engine_create.argtypes = [c_void_p, POINTER(c_void_p)]
        lib.lxs_api_engine_create.restype = ctypes.c_int
        lib.lxs_api_engine_free.argtypes = [c_void_p]
        lib.lxs_api_engine_free.restype = None
        lib.lxs_api_engine_reset.argtypes = [c_void_p]
        lib.lxs_api_engine_reset.restype = ctypes.c_int
        lib.lxs_api_engine_apply_inputs.argtypes = [c_void_p, POINTER(c_uint64), POINTER(c_uint64), c_uint32]
        lib.lxs_api_engine_apply_inputs.restype = ctypes.c_int
        lib.lxs_api_engine_tick.argtypes = [c_void_p]
        lib.lxs_api_engine_tick.restype = ctypes.c_int
        lib.lxs_api_engine_tick_many.argtypes = [c_void_p, c_uint32]
        lib.lxs_api_engine_tick_many.restype = ctypes.c_int
        lib.lxs_api_engine_read_outputs.argtypes = [c_void_p, POINTER(c_uint64), POINTER(c_uint64), c_uint32]
        lib.lxs_api_engine_read_outputs.restype = ctypes.c_int
        lib.lxs_api_engine_read_net.argtypes = [c_void_p, c_uint32, POINTER(c_uint64), POINTER(c_uint64)]
        lib.lxs_api_engine_read_net.restype = ctypes.c_int
        lib.lxs_api_engine_read_probes.argtypes = [c_void_p, POINTER(_ProbesC)]
        lib.lxs_api_engine_read_probes.restype = ctypes.c_int

    def _check(self, result: int, context: str):
        if result != 0:
            message = self.lib.lxs_api_get_last_error()
            text = message.decode("utf-8") if message else f"error code {result}"
            raise LxsApiError(f"{context}: {text}")

    def load_bench(self, path: str | Path):
        handle = c_void_p()
        self._check(
            self.lib.lxs_api_netlist_load_bench(str(path).encode("utf-8"), byref(handle)),
            "load_bench",
        )
        return handle

    def free_netlist(self, handle):
        self.lib.lxs_api_netlist_free(handle)

    def compile_plan(self, netlist):
        handle = c_void_p()
        self._check(self.lib.lxs_api_plan_compile(netlist, byref(handle)), "compile_plan")
        return handle

    def free_plan(self, handle):
        self.lib.lxs_api_plan_free(handle)

    def get_plan_counts(self, plan) -> PlanCounts:
        counts = _PlanCountsC()
        self._check(self.lib.lxs_api_plan_get_counts(plan, byref(counts)), "get_plan_counts")
        return PlanCounts(*[int(getattr(counts, field)) for field, _ in counts._fields_])

    def get_input_name(self, plan, index: int) -> str:
        value = c_char_p()
        self._check(self.lib.lxs_api_plan_get_input_name(plan, index, byref(value)), "get_input_name")
        return value.value.decode("utf-8")

    def get_output_name(self, plan, index: int) -> str:
        value = c_char_p()
        self._check(self.lib.lxs_api_plan_get_output_name(plan, index, byref(value)), "get_output_name")
        return value.value.decode("utf-8")

    def find_net(self, plan, name: str) -> int:
        net_id = c_uint32()
        self._check(self.lib.lxs_api_plan_find_net(plan, name.encode("utf-8"), byref(net_id)), "find_net")
        return int(net_id.value)

    def create_engine(self, plan):
        handle = c_void_p()
        self._check(self.lib.lxs_api_engine_create(plan, byref(handle)), "create_engine")
        return handle

    def free_engine(self, handle):
        self.lib.lxs_api_engine_free(handle)

    def reset_engine(self, engine):
        self._check(self.lib.lxs_api_engine_reset(engine), "reset_engine")

    def apply_inputs(self, engine, values: list[int], masks: list[int] | None = None):
        masks = [0] * len(values) if masks is None else masks
        value_array = (c_uint64 * len(values))(*values)
        mask_array = (c_uint64 * len(masks))(*masks)
        self._check(
            self.lib.lxs_api_engine_apply_inputs(engine, value_array, mask_array, len(values)),
            "apply_inputs",
        )

    def tick(self, engine, count: int = 1):
        if count == 1:
            self._check(self.lib.lxs_api_engine_tick(engine), "tick")
        else:
            self._check(self.lib.lxs_api_engine_tick_many(engine, count), "tick_many")

    def read_outputs(self, engine, count: int) -> tuple[list[int], list[int]]:
        value_array = (c_uint64 * count)()
        mask_array = (c_uint64 * count)()
        self._check(self.lib.lxs_api_engine_read_outputs(engine, value_array, mask_array, count), "read_outputs")
        return list(value_array), list(mask_array)

    def read_net(self, engine, net_id: int) -> tuple[int, int]:
        value = c_uint64()
        mask = c_uint64()
        self._check(self.lib.lxs_api_engine_read_net(engine, net_id, byref(value), byref(mask)), "read_net")
        return int(value.value), int(mask.value)

    def read_probes(self, engine) -> Probes:
        probes = _ProbesC()
        self._check(self.lib.lxs_api_engine_read_probes(engine, byref(probes)), "read_probes")
        return Probes(*[int(getattr(probes, field)) for field, _ in probes._fields_])


def logic_to_word(value: int | bool) -> int:
    return ALL_ONES if bool(value) else 0
