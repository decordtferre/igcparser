import unittest
import datetime
from dataio import parse_lat, parse_lon, get_flightinfo, load_igc_file, get_h_records, clean_altitude_series, \
    parse_b_record


class TestAdd(unittest.TestCase):

    def test_parse_lat_north(self):
        self.assertAlmostEqual(parse_lat('5054314', 'N'), 50 + 54.314/60)
        self.assertAlmostEqual(parse_lat('5002302', 'N'), 50 + 2.302/60)

    def test_parse_lat_south(self):
        self.assertAlmostEqual(parse_lat('5054314', 'S'), -(50 + 54.314 / 60))
        self.assertAlmostEqual(parse_lat('5002302', 'S'), -(50 + 2.302 / 60))

    def test_parse_lon_east(self):
        self.assertAlmostEqual(parse_lon('00524526', 'E'), 5 + 24.526/60)
        self.assertAlmostEqual(parse_lon('00543272', 'E'), 5 + 43.272/60)

    def test_parse_lon_west(self):
        self.assertAlmostEqual(parse_lon('00524526', 'W'), -(5 + 24.526 / 60))
        self.assertAlmostEqual(parse_lon('00543272', 'W'), -(5 + 43.272 / 60))

    def test_get_flightinfo(self):
        lines = load_igc_file("/Users/ferredecordt/Documents/IGCreaderPython/2023-07-06-LXV-2J0-01.igc")
        h_records = get_h_records(lines)
        info = get_flightinfo(h_records)
        self.assertEqual(info.get('Pilot'), 'FERRE DE CORDT')
        self.assertEqual(info.get('Date'), "06/07/2023")
        self.assertEqual(info.get('Crew'), 'None')
        self.assertEqual(info.get('Registration'), "D-5585")

    def test_clean_altitudeseries(self):
        corrupted_series = [190, 200, 800, 220, 250, 54226, 260]
        clean_series = clean_altitude_series(corrupted_series)
        self.assertEqual(clean_series, [190, 200, 210, 220, 250, 255, 260])

    def test_parse_b_record(self):
        record = 'B0946005002302N00524526EA004890060300501000011269000'
        parsed_record = parse_b_record(record)
        self.assertEqual(parsed_record.get('TimeUTC'), datetime.time(9, 46,0))
        self.assertEqual(parsed_record.get('Latitude'), parse_lat('5002302', 'N'))
        self.assertEqual(parsed_record.get('Longitude'), parse_lon('00524526', 'E'))
        self.assertEqual(parsed_record.get('Fix Validity'), 'A')
        self.assertEqual(parsed_record.get('pressAltitude'), 489 )
        self.assertEqual(parsed_record.get('gpsAltitude'), 603)


# To run tests from command line:
if __name__ == '__main__':
    unittest.main()
    print("All tests passed")
