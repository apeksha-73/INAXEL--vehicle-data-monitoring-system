import machine

class MPU6050:
    def __init__(self, i2c, addr=0x68):
        self.i2c = i2c
        self.addr = addr
        self.i2c.writeto_mem(self.addr, 0x6B, b'\x00') # Wake up

    def _read_word(self, reg):
        h = self.i2c.readfrom_mem(self.addr, reg, 1)[0]
        l = self.i2c.readfrom_mem(self.addr, reg + 1, 1)[0]
        val = (h << 8) | l
        return val if val < 32768 else val - 65536

    @property
    def accel(self):
        # Sensitivity 16384 for +/- 2g range
        x = self._read_word(0x3B) / 16384.0
        y = self._read_word(0x3D) / 16384.0
        z = self._read_word(0x3F) / 16384.0
        return type('Data', (), {'x':x, 'y':y, 'z':z})