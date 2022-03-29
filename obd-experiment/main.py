import time
from logging import INFO

import obd
import pyudev
from quickdump import QuickDumper
from loguru import logger

OBD_DEV_DRIVER_NAME = "ch341-uart"
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


def cmd_cb(cmd):
    logger.info(f"Got command: {cmd}")
    QuickDumper("obd_data_v2").dump(cmd)


def ensure_connection():
    context = pyudev.Context()
    if not is_obd_device_connected(context):
        logger.info("No device connected. Waiting for connection...")
        await_obd_device_connection(context)
    logger.info("USB device connected!")


def gather_obd() -> obd.Async:
    logger.info("Connecting to USB device...")
    ensure_connection()
    logger.info("Connecting to adapter...")
    # while True:
    #     connection = obd.Async(delay_cmds=0.1)
    #   if connection.is_connected():
    #       break
    #   logger.info("Adapter connected, but ignition is off. Waiting...")
    #   time.sleep(2)
    connection = obd.Async(delay_cmds=0.05)
    logger.info("Connected to adapter!")

    for cmd in connection.supported_commands:
        if any(
            cmd.name.startswith(skipped_prefix) for skipped_prefix in SKIPPED_PREFIXES
        ):
            continue
        connection.watch(cmd, callback=cmd_cb)

    connection.start()
    return connection


def is_obd_device_connected(ctx: pyudev.Context) -> bool:
    return OBD_DEV_DRIVER_NAME in set(d.driver for d in ctx.list_devices())


def await_obd_device_connection(ctx: pyudev.Context) -> pyudev.Device:
    monitor = pyudev.Monitor.from_netlink(ctx)
    for device in iter(monitor.poll, None):
        if device.driver == OBD_DEV_DRIVER_NAME and device.action == "bind":
            logger.info("Device bound: ch341-uart")
            return device


def main():
    logger.add("out.log", level=INFO)
    conn = gather_obd()
    while True:
        time.sleep(1)
        if not conn.is_connected():
            conn = gather_obd()


if __name__ == "__main__":
    try:
        main()
    except:
        logger.exception("Oh no!")
