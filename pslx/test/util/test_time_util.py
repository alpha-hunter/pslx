import datetime
import unittest

from pslx.util.timezone_util import TimezoneUtil, TimezoneObj


class ProtoUtilTest(unittest.TestCase):

    def test_cur_time_from_str_1(self):
        time_str = "2020-02-20 00:18:14.713721-08:00"
        expect_result = datetime.datetime(2020, 2, 20, 0, 18, 14, 713721).replace(
            tzinfo=TimezoneObj.WESTERN_TIMEZONE
        )
        result = TimezoneUtil.cur_time_from_str(time_str=time_str)
        self.assertEqual(result.replace(tzinfo=None), expect_result.replace(tzinfo=None))

    def test_cur_time_from_str_2(self):
        time_str = "2020-02-20 00:18:14.713721"
        expect_result = datetime.datetime(2020, 2, 20, 0, 18, 14, 713721).replace()
        result = TimezoneUtil.cur_time_from_str(time_str=time_str)
        self.assertEqual(result, expect_result)

    def test_cur_time_from_str_3(self):
        time_str = "2020-02-20 00:18:14"
        expect_result = datetime.datetime(2020, 2, 20, 0, 18, 14).replace()
        result = TimezoneUtil.cur_time_from_str(time_str=time_str)
        self.assertEqual(result, expect_result)
