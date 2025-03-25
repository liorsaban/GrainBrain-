import serial
import time
import numpy as np

class SerialConnection:
    """Robust Serial Connection Handler for Scale."""

    def __init__(self, port="COM4", baudrate=9600, timeout=2):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        self.connect()

    def connect(self):
        """Establish a serial connection, ensuring no conflicts."""
        if self.ser and self.ser.is_open:
            self.ser.close()
            time.sleep(1)  # give OS time to release the port

        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            self.ser.reset_input_buffer()
            print(f"✅ Connected to scale on {self.port}")
        except serial.SerialException as e:
            print(f"❌ SerialException: {e}")
            self.ser = None
        except PermissionError as e:
            print(f"❌ Permission error: {e}")
            self.ser = None

    def read_weight(self):
        """Read weight from the scale via serial."""
        if self.ser is None:
            print("⚠️ No connection to scale. Cannot read weight.")
            return np.nan

        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.ser.reset_input_buffer()  # Clear the input buffer first
                self.ser.write(b'SI\r\n')      # Request new weight measurement
                time.sleep(1.5)                # Wait longer (1.5s) to ensure new data is ready

                # Read until we get a non-empty line or timeout
                start_time = time.time()
                line = ""
                while (time.time() - start_time) < self.timeout:
                    if self.ser.in_waiting > 0:
                        line = self.ser.readline().decode('ascii').strip()
                        if line:
                            break

                if not line:
                    raise ValueError("Empty response from scale.")

                # Check if the line format is correct ('SI x.xx g')
                parts = line.split()
                if len(parts) < 3 or not parts[1].replace('.', '', 1).isdigit():
                    raise ValueError(f"Unexpected response format: '{line}'")

                weight = float(parts[1])
                print(f"✅ Weight read: {weight} g")
                return weight

            except (ValueError, IndexError, UnicodeDecodeError) as e:
                print(f"⚠️ Parsing error: {e}. Response: '{line}'. Retrying ({attempt + 1}/{max_retries})...")
                time.sleep(1)  # short delay before retrying

        # All retries failed
        print("❌ Failed to read valid weight after multiple attempts.")
        return np.nan


def close(self):
    """Close the serial connection explicitly."""
    if self.ser and self.ser.is_open:
        self.ser.close()
        self.ser = None
        print(f"🔌 Connection to {self.port} closed.")

