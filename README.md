# ISF Reader

Read tek scope isf files as a numpy array.

```python
import isfreader

data = isfreader.read_file('T0000CH1.ISF')
data[:, 0]  # Time column (Does not always start at 0)
data[:, 1]  # Data (Voltage) column
print(data.shape)
print(data.dtype)

```
