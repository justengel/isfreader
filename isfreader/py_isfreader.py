"""
    ISF Reader - Items for reading and parsing ISF files.

    The purpose of this file is to read in time/value data. This file can read this data from csv
    files or isf files.

    SeaLandAire Technologies
    :author: Jengel
"""
import numpy as np

__all__ = ['read_file', 'split_isf_header', 'parse_isf_header', 'parse_isf_data']


# Header Parsers
HEADER_DISPATCHER = {
            'BYT_NR': int,
            'ENCDG': str,
            'BN_FMT': str,
            'BYT_OR': str,
            'WFID': str,
            'NR_PT': int,
            'PT_FMT': str,
            'XUNIT': lambda s: str.strip(s, '"'),
            'XINCR': float,
            'XZERO': float,
            'PT_OFF': int,
            'YUNIT': lambda s: str.strip(s, '"'),
            'YMULT': float,
            'YOFF': float,
            'YZERO': float,

            'VSCALE': float,
            'HSCALE': float,
            'VPOS': float,
            'VOFFSET': float,
            'HDELAY': float,
            ':CURVE': str,
            }

SCOPE1_HD = {
            'BYT_NR': 'BYT_NR',
            'ENCDG': 'ENCDG',
            'BN_FMT': 'BN_FMT',
            'BYT_OR': 'BYT_OR',
            'WFID': 'WFID',
            'NR_PT': 'NR_PT',
            'PT_FMT': 'PT_FMT',
            'XUNIT': 'XUNIT',
            'XINCR': 'XINCR',
            'XZERO': 'XZERO',
            'PT_OFF': 'PT_OFF',
            'YUNIT': 'YUNIT',
            'YMULT': 'YMULT',
            'YOFF': 'YOFF',
            'YZERO': 'YZERO',
            'VSCALE': 'VSCALE',
            'HSCALE': 'HSCALE',
            'VPOS': 'VPOS',
            'VOFFSET': 'VOFFSET',
            'HDELAY': 'HDELAY',
            ':CURVE': ':CURVE',
             }

SCOPE2_HD = {
            'BYT_N': 'BYT_NR',
            'ENC': 'ENCDG',
            'BN_F': 'BN_FMT',
            'BYT_O': 'BYT_OR',
            'WFI': 'WFID',
            'NR_P': 'NR_PT',
            'PT_F': 'PT_FMT',
            'XUN': 'XUNIT',
            'XIN': 'XINCR',
            'XZE': 'XZERO',
            'PT_O': 'PT_OFF',
            'YUN': 'YUNIT',
            'YMU': 'YMULT',
            'YOF': 'YOFF',
            'YZE': 'YZERO',
            'VSCALE': 'VSCALE',
            'HSCALE': 'HSCALE',
            'VPOS': 'VPOS',
            'VOFFSET': 'VOFFSET',
            'HDELAY': 'HDELAY',
            ':CURV': ':CURVE',

            # Different extra header values
            'COMP': str,  # COMPOSITE_{PT_F}; Basically what the value is.
            'FILTERF': int,
            }

CORRECTING_HD = SCOPE1_HD
CORRECTING_HD.update(SCOPE2_HD)


class InvalidFileError(Exception):
    """Custom Exception for an invalid file."""
    pass


def split_isf_header(data):
    """Split the header from the data in an isf file.

    Args:
        data (str/bytes): Data for the file, binary or str.
    """
    # Get the index for splitting the header from the data
    curve = b':CURV'
    find = data.find(curve)
    if data[find+len(curve)] == b'E'[0]:
        length = len(b':CURVE #')
    elif find != -1:
        length = len(b':CURV #')
    else:
        raise InvalidFileError('Cannot find header separator!')
    # end
    find += length

    # Get the correct splitting point
    pad_char = int(data[find: find+1].decode('latin1')) + 1  # Parse string value to an integer
    data_len = int(data[find+1: find + pad_char].decode('latin1'))  # Parse string value to an integer
    split = find + pad_char

    # Split
    header_text = data[:split]
    bin_data = data[split:split+data_len]

    # Get the header values
    header = parse_isf_header(header_text.decode('latin1'))  # Convert header data to human readable latin1

    # Make sure we have the right data.
    if header['PT_FMT'] == 'ENV':
        try:
            header, bin_data = split_isf_header(data[split+data_len:])
        except (IndexError, InvalidFileError):
            raise InvalidFileError('The file does not contain the correct header information!')

    return header, bin_data


def parse_isf_header(header_text):
    """Parse the header text into a dictionary.

    Return:
        header (dict): Dictionary of header items matching the HEADER_DISPATCHER.

    Args:
        header_text (str): Text containing the header information.
    """
    remove = ':WFMPRE:'
    if remove not in header_text:
        remove = ':WFMP:'

    # Get header values
    header = dict.fromkeys(HEADER_DISPATCHER.keys())
    for kv_pair in header_text.strip(';').split(';'):
        if kv_pair.find(' '):
            (key, val) = kv_pair.split(' ', 1)
            key = key.replace(remove, '')
            key = CORRECTING_HD.get(key, None)  # Get the correct key (Same key, for the conversion)
            if key in HEADER_DISPATCHER:
                header[key] = HEADER_DISPATCHER[key](val)
    # end

    # Check for header values
    if None in header.values():
        raise InvalidFileError('Header field missing from ISF file.')

    return header


def parse_isf_data(data):
    """Parse isf data to x and y data.

    Args:
        data (str/bytes): Data to parse.
    """
    # Separate header from data
    if isinstance(data, str):
        data = data.encode('latin1')
    header, data = split_isf_header(data)

    # Get Values
    num_rows = header['NR_PT']
    yoff = header['YOFF']
    ymult = header['YMULT']
    yzero = header['YZERO']
    pt_off = header['PT_OFF']
    xincr = header['XINCR']
    xzero = header['XZERO']  # What value does x start with
    byte_order = '>' if header['BYT_OR'] == 'MSB' else '<'  # Byte order (Most Significant Bit)
    byte_format = 'i' if header['BN_FMT'] == 'RI' else 'u'  # Signed integer or unsigned positive integer
    byte_size = header['BYT_NR']  # Number of bytes per sample

    # Convert string to binary data to avoid any misunderstandings about encoding
    dtype = '{}{}{}'.format(byte_order, byte_format, byte_size)
    data = np.fromstring(data, dtype=dtype)
    xdata = ((np.arange(num_rows) - pt_off) * xincr + xzero)
    ydata = ((data - yoff) * ymult) + yzero

    return np.array((xdata, ydata)).T


def read_file(filename):
    """Read the given filename.

    Args:
        filename (str): The filename you want to load.

    Returns:
        data (numpy.array): Loaded data.
    """
    with open(filename, 'rb') as file:
        byts = file.read()

    return parse_isf_data(byts)
