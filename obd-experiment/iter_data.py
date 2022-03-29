from collections import Counter, defaultdict
from typing import NamedTuple

from obd import OBDCommand
from quickdump import iter_dumps
from rich.console import Console
from rich.pretty import Pretty

SKIPPED_PREFIXES = (
    "DTC_",
    "MIDS_",
    "PIDS_",
    "OBD_COMPLIANCE",
    "CLEAR_DTC",
    "GET_DTC",
    "DISTANCE_SINCE_DTC_CLEAR",
    "GET_CURRENT_DTC",
    "ELM_VERSION",
)


prev_t = 0


# Don't confuse the MAP sensor parameter with intake manifold vacuum; they're not the same. A simple formula to use
# is: barometric pressure (BARO) / MAP = intake manifold vacuum. For example, BARO 27.5 in./Hg / MAP 10.5 = intake
# manifold vacuum of 17.0 in./Hg.


class ResponseCommand(NamedTuple):
    t: float
    response: OBDCommand


timed = []
received_values = defaultdict(Counter)
for response in iter_dumps("obd_data"):
    if response.command is None:
        continue

    if any(response.command.name.startswith(sk) for sk in SKIPPED_PREFIXES):
        continue

    try:
        key = (
            (response.value.m, response.value.u)
            if response.value is not None
            else response.value
        )
    except:
        key = response.value

    if isinstance(key, list):
        key = tuple(key)
    received_values[response.command][key] += 1

    # t = response.time - prev_t
    print(response.command.name, response.command.desc, response.value)
    # if response.command.desc == "Vehicle Speed":
    # dt = datetime.fromtimestamp(response.time).ctime()
    # print(dt, response.command.desc, response.value)
    # print(response)
    # if "29.0 kph" in str(response):
    #     print("neat")

Console().print(Pretty(received_values))
