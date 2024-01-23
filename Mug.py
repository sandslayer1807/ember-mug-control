import math

from temp import Temp

# Created using the ever-helpful Ember Mug BT Documentation located here:
#   https://github.com/orlopau/ember-mug
class Mug:
    """Class that assists in setting & retrieving various Ember Mug datapoints provided
    the MAC address of the mug and an active connection.

    Raises:
        set_name:
            ValueError: Name is not ASCII-encoded/encodable
            ValueError: Name is too long
            ValueError: Name contains spaces
        set_target_temp:
            ValueError: Temperature out of range
        set_temp_unit:
            ValueError: Temperature unit not supported

    Returns:
        Mug: Mug class
    """
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

    def __init__(self, mug_id, bleak_client):
        """Constructor that stores the mug MAC address and the Bleak client used
        to interact with the mug.

        Args:
            id (str): MAC address for the mug.
            bleak_client (BleakClient): Bleak client connected to the mug in question.
        """
        self._id = mug_id
        self._client = bleak_client

    # Defining our getters and setters
    @property
    async def battery_percent(self):
        """Retrieves the current battery percentage.

        Returns:
            str: Formatted battery percentage.
        """
        battery_data = await self._client.read_gatt_char(self._service_dict['battery'])
        return f"{battery_data[0]:.1f}%"

    @property
    async def battery_state(self):
        """Retrieves the current battery state.

        Returns:
            str: Whether or not the mug is charging.
        """
        battery_data = await self._client.read_gatt_char(self._service_dict['battery'])
        return "Charging" if battery_data[1] == 1 else "Not Charging"

    @property
    async def color(self):
        """Retrieves the user-defined color for the mug.

        Returns:
            tuple: RGBA tuple containing the color details.
        """
        color_data = await self._client.read_gatt_char(self._service_dict['mug_color'])
        # returns rgba tuple
        return (color_data[0], color_data[1], color_data[2], color_data[3])

    @property
    async def current_temp(self):
        """Retrieves the current temperature of the mug converted to the mug's 
        temperature unit.

        Returns:
            int/float: The current temp. Can either be a float or an int depending 
            on the temperature.
        """
        raw_temp_data = await self._client.read_gatt_char(self._service_dict['current_temp'])
        # to 'convert' the uint16 format to float celsius we divide by 100
        celsius_float = int.from_bytes(raw_temp_data, byteorder="little") * .01
        # also need to get the unit to determine if it's in C or F
        if await self.temp_unit == "C":
            return f"{celsius_float:.2f}"
        # we need to convert from C into F
        return f"{Temp.to_fahrenheit(celsius_float):.2f}"

    @property
    async def status(self):
        """Retrieves the liquid state of the mug, which is pretty much the overall mug status, as
        it indicates if it is:
        - Empty
        - Filling
        - Heating
        - Cooling
        - At target temperature and is stable
        - Unknown status in all other cases

        Returns:
            str: The mug status.
        """
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
        """Retrieves the user-defined name for the mug.

        Returns:
            str: The name of the mug.
        """
        raw_name = await self._client.read_gatt_char(self._service_dict['mug_name'])
        return raw_name.decode("ascii")

    # Note that some `setter`s are not compatible with async methods currently...
    async def set_name(self, value):
        """Sets the name of the mug to the provided value.

        Args:
            value (str): Desired name for the mug.

        Raises:
            ValueError: Name does not comply with ASCII encoding
            ValueError: Name contains spaces
            ValueError: Name is too long / contains more than 14 bytes
        """
        # strip any leading/trailing whitespace
        cleaned_name = value.strip()
        # verify the name is ascii-safe / encoded
        try:
            encoded_name = cleaned_name.encode('ascii')
        except UnicodeDecodeError as ex:
            raise ValueError("The name is invalid - it is not ASCII-safe", ex) from ex
        if ' ' in cleaned_name:
            raise ValueError("The name is invalid - spaces are not supported")
        if len(encoded_name) > 14:
            raise ValueError(
                f"Name is too long (must be smaller than 14 bytes). Your name [{value}] "+
                "was {len(encoded_name)} bytes."
            )
        await self._client.write_gatt_char(
            self._service_dict['mug_name'],
            encoded_name
        )

    @property
    async def target_temp(self):
        """Retrieves the target temperature of the mug converted to the mug's temperature unit.

         Returns:
            int/float: The target temperature. Can either be a float or an int depending 
            on the temperature.
        """
        raw_temp_data = await self._client.read_gatt_char(self._service_dict['target_temp'])
        # to 'convert' the uint16 format to float celsius we divide by 100
        celsius_float = int.from_bytes(raw_temp_data, byteorder="little") * .01
        # also need to get the unit to determine if it's in C or F
        if await self.temp_unit == "C":
            return f"{celsius_float:.2f}".format()
        # we need to convert from C into F
        return f"{Temp.to_fahrenheit(celsius_float):.2f}"

    # Note that some `setter`s are not compatible with async methods currently...
    async def set_target_temp(self, value):
        """Sets the desired target temperature of the mug

        Args:
            value (int/float): The desired target temperature of the mug in the mug's
            current temperature unit (C or F).

        Raises:
            ValueError: Temperature out of range (120F< x < 145F)
            ValueError: Temperature out of range (50C < x < 62.5C)

        Returns:
            str: The set temperature.
        """
        value_to_set = value
        # need to get the unit to determine if it's in C or F so we can convert appropriately
        current_temp_unit = await self.temp_unit
        # add some safeguards here...
        if current_temp_unit == "F" and (value_to_set > 145 or value_to_set < 120):
            raise ValueError(f"Temperature {value_to_set} deg F out of range 120 < x < 145")
        if current_temp_unit == "C" and (value_to_set > 62.5 or value_to_set < 50):
            raise ValueError(f"Temperature {value_to_set} deg C out of range 50 < x < 62.5")

        if current_temp_unit == "F":
            value_to_set = Temp.to_celsius(value_to_set)
        await self._client.write_gatt_char(
            self._service_dict['target_temp'],
            # to 'convert' non-int C to the uint16 format required we multiply by 100 and floor it
            int.to_bytes(math.floor(value_to_set * 100), length=2, byteorder="little")
        )
        return f"{value:.2f}"

    @property
    async def temp_unit(self):
        """Gets the current temperature unit (Fahrenheit or Celsius) the mug is using.

        Returns:
            str: C for Celsius, F for Fahrenheit.
        """
        raw_temp_unit = await self._client.read_gatt_char(self._service_dict['temp_unit'])
        return "C" if raw_temp_unit[0] == 0 else "F"

    async def set_temp_unit(self, value):
        """Sets the temperature unit (Fahrenheit or Celsius) the mug is using.

        Args:
            value (str): Either 'C' or 'F' for Celsius or Fahrenheit, respectively.

        Raises:
            ValueError: Provided string is not equal to 'C' or 'F'

        Returns:
            str: The set temperature unit.
        """
        if value != "C" and value != "F":
            raise ValueError("Temperature unit must be either C (Celsius) or F (Fahrenheit)")

        value_to_set = 0 if value == "C" else 1
        await self._client.write_gatt_char(
            self._service_dict['temp_unit'], 
            int.to_bytes(value_to_set, length=1)
        )
        return value
