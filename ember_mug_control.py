"""Main module that either:
1) Processes command line arguments
2) Prompts the user interactively
for arguments to then connect to and control the appropriate Ember Mug device.
"""

import argparse
import asyncio
import re

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from bleak.exc import BleakDeviceNotFoundError
from mug import Mug

# list to ensure we've not seen the device before
seen_devices = []

def device_found(device: BLEDevice, advertisement_data: AdvertisementData):
    """_summary_

    Args:
        device (BLEDevice): _description_
        advertisement_data (AdvertisementData): _description_
    """
    ember_pattern = re.compile("ember", flags=re.IGNORECASE)
    if device.address not in seen_devices and ember_pattern.search(str(device)) is not None:
        print()
        print(f"[{len(seen_devices) + 1}]: { device}")
        print("".join('-'*len(str(device))))
        print(advertisement_data)
        seen_devices.append(device.address)

async def mug_find(num_seconds):
    """ Scans and displays any found Ember Mugs for the user to select to start interacting
    with.

    Args:
        num_seconds (int): Number of seconds to scan for mugs.

    Returns:
        Boolean: False if no mugs are found, or if the user exits without selecting a mug.
    """
    scanner = BleakScanner(detection_callback=device_found)
    await scanner.start()
    await asyncio.sleep(num_seconds)
    await scanner.stop()

    if len(seen_devices) == 0:
        print("No Ember Mug devices found.")
        return False
    selected_mug = int(input(
        "Find your mug? Enter the number for it here, or 0 for no match: "
    ))
    if selected_mug <= 0 or selected_mug > len(seen_devices):
        return False
    # now we've got the right mac address, we need to figure out what the user wants to do
    #   with their mug.
    selected_mug_addr = seen_devices[selected_mug - 1]
    print(f"You've selected: {selected_mug_addr}")
    await interactive_mug_control(selected_mug_addr)

async def mug_control(mug_id, command, command_arg = False):
    """ Connects to the provided mug and runs the selected command, printing the result to
    the screen.

    Args:
        mug_id (string): MAC Address of the mug to interact with
        command (string): Name of the command to execute against the mug.
        command_arg (bool, string, int): Argument applying to the selected command. 
        Defaults to False.
    """
    async with BleakClient(mug_id) as client:
        await client.pair()
        mug = Mug(mug_id, client)

        if command == 'status':
            temp_unit = await mug.temp_unit

            print(f"Mug Name: {await mug.name} | Status: {await mug.status}")
            print(f"Battery: {await mug.battery_percent} | State: {await mug.battery_state}")
            print(
                f"Current Temp: {await mug.current_temp} deg {temp_unit} | "+
                f"Target: {await mug.target_temp} deg {temp_unit}"
            )
        elif command == 'set-name':
            print(f"Setting the name of your mug to {command_arg}...")
            await mug.set_name(command_arg)
            print("Successfully set the name.")
        elif command == 'set-target-temp':
            temp_unit = await mug.temp_unit
            print(f"Setting the target temperature of your mug to {command_arg} deg {temp_unit}...")
            await mug.set_target_temp(command_arg)
            print("Successfully set the temperature unit.")
        elif command == 'set-temp-unit':
            print(f"Setting the temperature unit of your mug to {command_arg}")
            await mug.set_temp_unit(command_arg)
            print("Successfully set the temperature.")

    await client.unpair()

async def interactive_mug_control(mac_addr):
    """ Collects the arguments from the user to then supply to the mug to perform various 
    operations, such as checking the status or setting various operating parameters.

    Args:
        mac_addr (str): MAC Address of the mug to connect to.

    Returns:
        Boolean: Returns false if the user no longer wants to continue.
    """
    print("Now that you've selected the mug you'd like to interact with, what do you want to do?")
    print("  1) Check status")
    print("  2) Set mug name")
    print("  3) Set the target temperature")
    print("  4) Set the temperature unit")
    print("  5) Exit")
    selected_control = input("Your choice?\n")
    match(selected_control):
        case "1":
            await mug_control(mac_addr, 'status')
        case "2":
            selected_name = input(
                "Please enter your mug's name. It cannot contain spaces and must be shorter "+
                "than 14 bytes/characters\n"
            )
            await mug_control(mac_addr, 'set-name', selected_name)
        case "3":
            # really need to see what the unit is before we prompt...
            client = BleakClient(mac_addr)
            try:
                await client.connect()
                mug = Mug(mac_addr, client)
                current_temp_unit = await mug.temp_unit
            except Exception as e:
                print(f"Something bad happened while getting the temperature unit: {e}")
            finally:
                await client.disconnect()
            desired_temp = float(input(
                f"What is the temperature (in {current_temp_unit}) you would like to target?\n"
            ))
            await mug_control(mac_addr, 'set-target-temp', desired_temp)
        case "4":
            selected_unit = input(
                "What is the temperature unit you would like to use? (Select C or F)\n"
            )
            await mug_control(mac_addr, 'set-temp-unit', selected_unit)
        case "5":
            return False
        case _:
            print("You've selected an invalid option, please try again.")
            await interactive_mug_control(mac_addr)

def main():
    """ Generates all the command line syntax / helper docs and collects the arguments to
    then pass to the appropriate function (depending on if the user wanted to scan or simply
    connect to a device).
    """
    # Define and collect our command line arguments
    parser = argparse.ArgumentParser(
        prog="EmberMugController",
        description="Connects to and controls Ember Mugs"
    )
    subparsers = parser.add_subparsers(
        title='Operating modes',
        description="Select the operation to perform",
        dest="mode",
        required=True
    )
    # Connect operation parser
    subparser_connect = subparsers.add_parser(
        'connect',
        help='Connect to the Ember Mug with the provided MAC address'
    )
    subparser_connect.add_argument(
        '--id',
        type=str,
        required=True,
        help="The MAC address of the mug to connect to. Required if 'mode' is connect."
    )
    # Starting subparser for the various mug commands
    subparser_connect_cmds = subparser_connect.add_subparsers(
        title='Mug commands',
        description="Select the mug command to perform",
        dest="mug_command",
        required=True
    )
    # Set name parser
    subparser_connect_set_name = subparser_connect_cmds.add_parser(
        'set-name',
        help='Sets the name of the mug'
    )
    subparser_connect_set_name.add_argument(
        '--name',
        help='Name to set. Required.'
    )
    # Status parser
    subparser_connect_cmds.add_parser(
        'status',
        help='Display status of the Ember Mug'
    )
    # Set target temp parser
    subparser_connect_set_temp = subparser_connect_cmds.add_parser(
        'set-target-temp',
        help='Set the target temperature of the mug'
    )
    subparser_connect_set_temp.add_argument(
        '--temp',
        help='Target temperature to set. Required.'
    )
    # Set temperature unit parser
    subparser_connect_set_unit = subparser_connect_cmds.add_parser(
        'set-temp-unit',
        help='Set the temperature unit of the mug'
    )
    subparser_connect_set_unit.add_argument(
        '--unit',
        help='Unit of temperature to set (C or F). Required.'
    )
    # Scan operation parser
    subparser_scan = subparsers.add_parser(
        'scan',
        help='Scan for and output MAC addresses of Ember Mugs to connect to',
    )
    subparser_scan.add_argument(
        '--time',
        type=int,
        default=5,
        help="Number of seconds to poll for devices. Default is 5."
    )
    args = parser.parse_args()

    # starting to process arguments
    if args.mode == 'scan':
        asyncio.run(mug_find(args.time))
    else:
        try:
            selected_arg = False
            # Probably a better way of doing this, just wanted to ensure selected_arg
            #   was populated appropriately for the given command.
            if args.mug_command == 'set-temp-unit':
                selected_arg = args.unit
            elif args.mug_command == 'set-target-temp':
                selected_arg = args.temp
            asyncio.run(mug_control(args.id, args.mug_command, selected_arg))
        except BleakDeviceNotFoundError:
            print(f'Unable to find Ember Mug with address {args.id}')

if __name__ == '__main__':
    main()
