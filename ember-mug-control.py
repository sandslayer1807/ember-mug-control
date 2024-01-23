import argparse
import asyncio
import re

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from bleak.exc import BleakDeviceNotFoundError
from Mug import Mug

# list to ensure we've not seen the device before
seen_devices = []

def device_found(device: BLEDevice, advertisement_data: AdvertisementData):
  ember_pattern = re.compile("ember", flags=re.IGNORECASE)
  if device.address not in seen_devices and ember_pattern.search(str(device)) is not None:
    print()
    print("[{0}]: {1}".format(len(seen_devices) + 1, device))
    seen_devices.append(device.address)

async def mug_find(num_seconds):
  scanner = BleakScanner(detection_callback=device_found)
  await scanner.start()
  await asyncio.sleep(num_seconds)
  await scanner.stop()
  
  if len(seen_devices) == 0:
    print("No Ember Mug devices found.")
  else: 
    selected_mug = int(input("Find your mug? Enter the number for it here, or 0 for no match:\n"))
    if selected_mug <= 0 or selected_mug > len(seen_devices):
      return False
    else:
      # now we've got the right mac address, we need to figure out what the user wants to do
      #   with their mug.
      selected_mug_addr = seen_devices[selected_mug - 1]
      print("You've selected: {0}".format(selected_mug_addr))
      await interactive_mug_control(selected_mug_addr)
  
async def mug_control(id, command, command_arg = False):
  async with BleakClient(id) as client:
    paired = await client.pair()
    mug = Mug(id, client)
    
    if command == 'status':
      temp_unit = await mug.temp_unit
      
      print("Mug Name: {0} | Status: {1}".format(await mug.name, await mug.status))
      print("Battery: {0} | State: {1}".format(await mug.battery_percent, await mug.battery_state))
      print("Current Temp: {0} deg {1} | Target: {2} deg {3}".format(
        await mug.current_temp, temp_unit, await mug.target_temp, temp_unit
      ))
    elif command == 'set-name':
      print("Setting the name of your mug to {0}...".format(command_arg))
      await mug.set_name(command_arg)
      print("Successfully set the name.")
    elif command == 'set-target-temp':
      temp_unit = await mug.temp_unit
      print("Setting the target temperature of your mug to {0} deg {1}...".format(command_arg, temp_unit))
      await mug.set_target_temp(command_arg)
      print("Successfully set the temperature unit.")
    elif command == 'set-temp-unit':
      print("Setting the temperature unit of your mug to {0}".format(command_arg))
      await mug.set_temp_unit(command_arg)
      print("Successfully set the temperature.")
    
    await client.unpair()
    
async def interactive_mug_control(mac_addr):
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
      selected_name = input("Please enter your mug's name. It cannot contain spaces and must be shorter than 14 bytes/characters\n")
      await mug_control(mac_addr, 'set-name', selected_name)
    case "3":
      # really need to see what the unit is before we prompt...
      client = BleakClient(mac_addr)
      try:
        await client.connect()
        mug = Mug(mac_addr, client)
        current_temp_unit = await mug.temp_unit
      except Exception as e:
        print("Something bad happened while getting the temperature unit: {0}".format(e))
      finally:
        await client.disconnect()
      desired_temp = float(input("What is the temperature (in {0}) you would like to target?\n".format(current_temp_unit)))
      await mug_control(mac_addr, 'set-target-temp', desired_temp)
    case "4":
      selected_unit = input("What is the temperature unit you would like to use? (Select C or F)\n".format(current_temp_unit))
      await mug_control(mac_addr, 'set-temp-unit', selected_unit)
    case "5":
      return True
    case _:
      print("You've selected an invalid option, please try again.")
      await interactive_mug_control(mac_addr)
    
def main():
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
  subparser_connect_cmds = subparser_connect.add_subparsers(
    title='Mug commands', 
    description="Select the mug command to perform",
    dest="mug_command",
    required=True
  )
  subparser_connect_set_name = subparser_connect_cmds.add_parser(
    'set-name',
    help='Sets the name of the mug'
  )
  subparser_connect_set_name_arg = subparser_connect_set_name.add_argument(
    '--name',
    help='Name to set. Required.'
  )
  subparser_connect_status = subparser_connect_cmds.add_parser(
    'status',
    help='Display status of the Ember Mug'
  )
  subparser_connect_set_temp = subparser_connect_cmds.add_parser(
    'set-target-temp',
    help='Set the target temperature of the mug'
  )
  subparser_connect_set_temp_temp_arg = subparser_connect_set_temp.add_argument(
    '--temp',
    help='Target temperature to set. Required.'
  )
  subparser_connect_set_unit = subparser_connect_cmds.add_parser(
    'set-temp-unit',
    help='Set the temperature unit of the mug'
  )
  subparser_connect_set_unit_unit_arg = subparser_connect_set_unit.add_argument(
    '--unit',
    help='Unit of temperature to set (C or F). Required.'
  )
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
      if args.mug_command == 'set-temp-unit':
        selected_arg = args.unit
      elif args.mug_command == 'set-target-temp':
        selected_arg = args.temp
      asyncio.run(mug_control(args.id, args.mug_command, selected_arg))
    except BleakDeviceNotFoundError:
      print('Unable to find Ember Mug with address {0}'.format(args.id))
 
if __name__ == '__main__':
  main()
