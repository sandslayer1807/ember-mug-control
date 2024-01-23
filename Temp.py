"""This helper module converts between Fahrenheit and Celsius."""
class Temp:
    """Class with static methods to convert between Fahrenheit and Celsius."""
    @staticmethod
    def to_fahrenheit(c_value):
        """ Converts the provided Celsius value to Fahrenheit.

        Args:
            c_value (float/int): Celsius value to convert to Fahrenheit.

        Returns:
            float/int: The Fahrenheit value corresponding to the provided Celsius value.
        """
        return (c_value * 9 / 5) + 32

    @staticmethod
    def to_celsius(f_value):
        """ Converts the provided Fahrenheit value to Celsius.

        Args:
            c_value (float/int): Fahrenheit value to convert to Celsius.

        Returns:
            float/int: The Celsius value corresponding to the provided Fahrenheit value.
        """
        return (f_value - 32) * 5 / 9
