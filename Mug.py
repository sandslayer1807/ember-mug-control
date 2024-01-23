import math

from Temp import Temp

# Created using the ever-helpful Ember Mug BT Documentation located here:
#   https://github.com/orlopau/ember-mug
class Mug:
  
  # Dictionary holding the various service UUIDs for the various commands to control & read data
  #   from the Ember Mug.
  _service_dict = {
    "battery": "fc540007-236c-4c94-8fa9-944a3e5353fa",
    "current_temp": "fc540002-236c-4c94-8fa9-944a3e5353fa",
    "liquid_state": "fc540008-236c-4c94-8fa9-944a3e5353fa",
    "mug_color": "fc540014-236c-4c94-8fa9-944a3e5353fa",
    "mug_name": "fc540001-236c-4c94-8fa9-944a3e5353fa",
    "target_temp": "fc540003-236c-4c94-8fa9-944a3e5353fa",
    "temp_unit": "fc540004-236c-4c94-8fa9-944a3e5353fa"
  }
  
  def __init__(self, id, bleak_client):
    self._id = id
    self._client = bleak_client
    
  # Defining our getters and setters
  @property
  async def battery_percent(self):
    battery_data = await self._client.read_gatt_char(self._service_dict['battery'])
    return "{0:.1f}%".format(battery_data[0])
  
  @property
  async def battery_state(self):
    battery_data = await self._client.read_gatt_char(self._service_dict['battery'])
    return "Charging" if battery_data[1] == 1 else "Not Charging"
  
  @property
  async def color(self):
    color_data = await self._client.read_gatt_char(self._service_dict['mug_color'])
    # returns rgba tuple
    return (color_data[0], color_data[1], color_data[2], color_data[3])
  
  @property
  async def current_temp(self):
    raw_temp_data = await self._client.read_gatt_char(self._service_dict['current_temp'])
    # to 'convert' the uint16 format to float celsius we divide by 100
    celsius_float = int.from_bytes(raw_temp_data, byteorder="little") * .01
    # also need to get the unit to determine if it's in C or F
    if await self.temp_unit == "C":
      return "{0:.2f}".format(celsius_float)
    else:
      # we need to convert from C into F
      return "{0:.2f}".format(Temp.to_fahrenheit(celsius_float))
  
  @property
  async def status(self):
    raw_liquid_state = await self._client.read_gatt_char(self._service_dict['liquid_state'])
    match raw_liquid_state[0]:
      case 1:
        return "Empty"
      case 2:
        return "Filling"
      case 4:
        return "Cooling"
      case 5: 
        return "Heating"
      case 6:
        return "At Temperature"
      case _:
        return "Unknown"
      
  @property
  async def name(self):
    raw_name = await self._client.read_gatt_char(self._service_dict['mug_name'])
    return raw_name.decode("ascii")
  
  # Note that some `setter`s are not compatible with async methods currently...
  async def set_name(self, value):
    # strip any leading/trailing whitespace
    cleaned_name = value.strip()
    # verify the name is ascii-safe / encoded
    try:
      encoded_name = cleaned_name.encode('ascii')
    except UnicodeDecodeError:
      raise ValueError("The name is invalid - it is not ASCII-safe")
    if(' ' in cleaned_name):
      raise ValueError("The name is invalid - spaces are not supported")
    elif(len(encoded_name) > 14):
      raise ValueError("Name is too long (must be smaller than 14 bytes). Your name [{0}] was {1} bytes.".format(value, len(encoded_name)))
    await self._client.write_gatt_char(
      self._service_dict['mug_name'],
      encoded_name
    )
      
  @property
  async def target_temp(self):
    raw_temp_data = await self._client.read_gatt_char(self._service_dict['target_temp'])
    # to 'convert' the uint16 format to float celsius we divide by 100
    celsius_float = int.from_bytes(raw_temp_data, byteorder="little") * .01
    # also need to get the unit to determine if it's in C or F
    if await self.temp_unit == "C":
      return "{0:.2f}".format(celsius_float)
    else:
      # we need to convert from C into F
      return "{0:.2f}".format(Temp.to_fahrenheit(celsius_float))
    
  # Note that some `setter`s are not compatible with async methods currently...
  async def set_target_temp(self, value):
    value_to_set = value
    # need to get the unit to determine if it's in C or F so we can convert appropriately
    current_temp_unit = await self.temp_unit
    # add some safeguards here...
    # TODO: Figure out what the actual ember mug limits are instead of using made up numbers
    if current_temp_unit == "F" and (value_to_set >= 200 or value_to_set < 90):
      raise ValueError("Temperature {0} deg F out of range 90 < x < 200".format(value_to_set))
    elif current_temp_unit == "C" and (value_to_set >= 93 or value_to_set < 32):
      raise ValueError("Temperature {0} deg C out of range 32 < x < 93".format(value_to_set))
    
    if current_temp_unit == "F":
      value_to_set = Temp.to_celsius(value_to_set)
    await self._client.write_gatt_char(
      self._service_dict['target_temp'], 
      # to 'convert' non-int C to the uint16 format required we multiply by 100 and floor it
      int.to_bytes(math.floor(value_to_set * 100), length=2, byteorder="little")
    )
    return "{0:.2f}".format(value)
    
  @property
  async def temp_unit(self):
    raw_temp_unit = await self._client.read_gatt_char(self._service_dict['temp_unit'])
    return "C" if raw_temp_unit[0] == 0 else "F"
  
  async def set_temp_unit(self, value):
    if value != "C" and value != "F":
      raise ValueError("Temperature unit must be either C (Celsius) or F (Fahrenheit)")
    
    value_to_set = 0 if value == "C" else 1
    await self._client.write_gatt_char(self._service_dict['temp_unit'], int.to_bytes(value_to_set, length=1))
    return value
