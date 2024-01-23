class Temp:
  @staticmethod
  def to_fahrenheit(c_value):
    return (c_value * 9 / 5) + 32

  @staticmethod
  def to_celsius(f_value):
    return (f_value - 32) * 5 / 9