

def test_isfreader():
    import isfreader
    import numpy as np

    data = isfreader.read_file('./T0000CH1.ISF')
    np_data = np.load('./T0000CH1.npy')
    assert data.shape == np_data.shape
    assert data.dtype == np_data.dtype
    assert np.all(data == np_data)


if __name__ == '__main__':
    test_isfreader()
    print('All tests finished successfully!')
