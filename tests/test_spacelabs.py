import datetime as dt
import os
import unittest

import numpy as np
import pandas as pd

import devicely


class SpacelabsTestCase(unittest.TestCase):
    READ_PATH = "tests/SpaceLabs_test_data/spacelabs.abp"
    WRITE_PATH = "tests/SpaceLabs_test_data/spacelabs_written.abp"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.expected_subject = "000002"
        timestamps = pd.to_datetime([
            "1.1.99 17:03",
            "1.1.99 17:05",
            "1.1.99 17:07",
            "1.1.99 17:09",
            "1.1.99 17:11",
            "1.1.99 17:13",
            "1.1.99 17:25",
            "1.1.99 17:28",
            "1.1.99 17:31",
            "1.1.99 17:34",
            "1.1.99 17:36",
            "1.1.99 17:39",
            "1.1.99 23:42",
            "1.1.99 23:59",
            "1.2.99 00:01",
        ])

        self.expected_data = pd.DataFrame({
            "timestamp": timestamps,
            "date": timestamps.map(lambda timestamp: timestamp.date()),
            "time": timestamps.map(lambda timestamp: timestamp.time()),
            "SYS(mmHg)": [11, 142, 152, 151, 145, 3, 4, 164, 154, 149, 153, 148, 148, 148, 148],
            "DIA(mmHg)": [0, 118, 112, 115, 110, 0, 0, 119, 116, 119, 118, 114, 114, 114, 114],
            "ACC_x": [0, 99, 95, 96, 91, 0, 0, 95, 95, 98, 96, 93, 93, 93, 93],
            "ACC_y": [0, 61, 61, 61, 59, 0, 0, 63, 63, 63, 60, 62, 62, 62, 62],
            "ACC_z": 15 * [np.nan],
            "error": ["EB", np.nan, np.nan, np.nan, np.nan, "EB", "EB", np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
        })

        self.expected_metadata = {
            "PATIENTINFO": {
                "DOB": "16.09.1966",
                "RACE": "native american"
            },
            "REPORTINFO": {
                "PHYSICIAN": "Dr. Hannibal Lecter",
                "NURSETECH": "admin",
                "STATUS": "NOTCONFIRMED",
                "CALIPERSUMMARY": {
                    "COUNT": "0"
                },
            },
        }

    def setUp(self):
        self.spacelabs_reader = devicely.SpacelabsReader(self.READ_PATH)

    def test_read(self):
        # Tests if a basic reading operation.

        pd.testing.assert_frame_equal(self.spacelabs_reader.data,
                                      self.expected_data)
        self.assertEqual(self.spacelabs_reader.subject, self.expected_subject)
        self.assertEqual(self.spacelabs_reader.metadata,
                         self.expected_metadata)

    def test_deidentify(self):
        # Tests if the SpacelabsReader.deidentify method removes all patient metadata.

        self.spacelabs_reader.deidentify()

        self.assertEqual(self.spacelabs_reader.subject, "")
        self.assertEqual(
            self.spacelabs_reader.metadata,
            {
                "PATIENTINFO": {
                    "DOB": "",
                    "RACE": ""
                },
                "REPORTINFO": {
                    "PHYSICIAN": "",
                    "NURSETECH": "",
                    "STATUS": "",
                    "CALIPERSUMMARY": {
                        "COUNT": ""
                    },
                },
            },
        )

    def test_write(self):
        # Tests the SpacelabsReader.write operation by writing, reading again and comparing the old and new signals.

        self.spacelabs_reader.write(self.WRITE_PATH)
        new_reader = devicely.SpacelabsReader(self.WRITE_PATH)

        pd.testing.assert_frame_equal(new_reader.data,
                                      self.spacelabs_reader.data)
        self.assertEqual(new_reader.metadata, self.spacelabs_reader.metadata)
        self.assertEqual(new_reader.subject, self.spacelabs_reader.subject)

        os.remove(self.WRITE_PATH)

    def test_random_timeshift(self):
        earliest_possible_shifted_time_col = pd.to_datetime([
            '1997-01-01 17:03:00',
            '1997-01-01 17:05:00',
            '1997-01-01 17:07:00',
            '1997-01-01 17:09:00',
            '1997-01-01 17:11:00',
            '1997-01-01 17:13:00',
            '1997-01-01 17:25:00',
            '1997-01-01 17:28:00',
            '1997-01-01 17:31:00',
            '1997-01-01 17:34:00',
            '1997-01-01 17:36:00',
            '1997-01-01 17:39:00',
            '1997-01-01 23:42:00',
            '1997-01-01 23:59:00',
            '1997-01-02 00:01:00'
        ])
        latest_possible_shifted_time_col = pd.to_datetime([
            '1998-12-02 17:03:00',
            '1998-12-02 17:05:00',
            '1998-12-02 17:07:00',
            '1998-12-02 17:09:00',
            '1998-12-02 17:11:00',
            '1998-12-02 17:13:00',
            '1998-12-02 17:25:00',
            '1998-12-02 17:28:00',
            '1998-12-02 17:31:00',
            '1998-12-02 17:34:00',
            '1998-12-02 17:36:00',
            '1998-12-02 17:39:00',
            '1998-12-02 23:42:00',
            '1998-12-02 23:59:00',
            '1998-12-03 00:01:00'
        ])

        old_timestamp_column = self.spacelabs_reader.data["timestamp"].copy()
        self.spacelabs_reader.timeshift()
        new_timestamp_column = self.spacelabs_reader.data["timestamp"]
        
        self.assertTrue((earliest_possible_shifted_time_col <= new_timestamp_column).all())
        self.assertTrue((new_timestamp_column <= latest_possible_shifted_time_col).all())

        new_date_column = self.spacelabs_reader.data["date"]
        new_time_column = self.spacelabs_reader.data["time"]
        testing_timestamp_column = pd.Series([
            dt.datetime.combine(new_date_column[i], new_time_column[i])
            for i in range(len(self.spacelabs_reader.data))
        ])

        pd.testing.assert_series_equal(new_timestamp_column, testing_timestamp_column, check_names=False)

    def test_drop_EB(self):
        # The drop_EB method should make timestamp the index column and remove all rows with 'EB' entries in the error column.
        self.expected_data.drop(index=[0, 5, 6], inplace=True)
        self.expected_data.set_index("timestamp", inplace=True)
        self.spacelabs_reader.drop_EB()

        pd.testing.assert_frame_equal(self.spacelabs_reader.data, self.expected_data)

        # When run again, drop_EB should not do anythin.
        self.spacelabs_reader.drop_EB()
        pd.testing.assert_frame_equal(self.spacelabs_reader.data, self.expected_data)

    def test_set_window_column(self):
        self.spacelabs_reader.set_window(dt.timedelta(seconds=30), "bfill")
        window_start = pd.to_datetime("1.1.99 17:02:30")
        window_end = pd.to_datetime("1.1.99 17:03:00")

        self.assertEqual(window_start, self.spacelabs_reader.data.loc[0, "window_start"])
        self.assertEqual(window_end, self.spacelabs_reader.data.loc[0, "window_end"])

        self.spacelabs_reader.set_window(dt.timedelta(seconds=30), "bffill")
        window_start = pd.to_datetime("1.1.99 17:02:45")
        window_end = pd.to_datetime("1.1.99 17:03:15")

        self.assertEqual(window_start, self.spacelabs_reader.data.loc[0, "window_start"])
        self.assertEqual(window_end, self.spacelabs_reader.data.loc[0, "window_end"])

        self.spacelabs_reader.set_window(dt.timedelta(seconds=30), "ffill")
        window_start = pd.to_datetime("1.1.99 17:03:00")
        window_end = pd.to_datetime("1.1.99 17:03:30")

        self.assertEqual(window_start, self.spacelabs_reader.data.loc[0, "window_start"])
        self.assertEqual(window_end, self.spacelabs_reader.data.loc[0, "window_end"])

    def test_set_window_index(self):
        self.spacelabs_reader.drop_EB()

        self.spacelabs_reader.set_window(dt.timedelta(seconds=30), "bfill")
        window_start = pd.to_datetime("1.1.99 17:04:30")
        window_end = pd.to_datetime("1.1.99 17:05:00")

        self.assertEqual(window_start, self.spacelabs_reader.data[["window_start"]].iloc[0].values)
        self.assertEqual(window_end, self.spacelabs_reader.data[["window_end"]].iloc[0].values)

        self.spacelabs_reader.set_window(dt.timedelta(seconds=30), "bffill")
        window_start = pd.to_datetime("1.1.99 17:04:45")
        window_end = pd.to_datetime("1.1.99 17:05:15")

        self.assertEqual(window_start, self.spacelabs_reader.data[["window_start"]].iloc[0].values)
        self.assertEqual(window_end, self.spacelabs_reader.data[["window_end"]].iloc[0].values)

        self.spacelabs_reader.set_window(dt.timedelta(seconds=30), "ffill")
        window_start = pd.to_datetime("1.1.99 17:05:00")
        window_end = pd.to_datetime("1.1.99 17:05:30")

        self.assertEqual(window_start, self.spacelabs_reader.data[["window_start"]].iloc[0].values)
        self.assertEqual(window_end, self.spacelabs_reader.data[["window_end"]].iloc[0].values)


if __name__ == "__main__":
    unittest.main()
