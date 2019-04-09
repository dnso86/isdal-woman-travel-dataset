from math import sin, cos, acos, radians
import sqlite3


DATABASE_NAME = 'isdal-geo.sqlite'
DATA_DIRECTORY = 'data'
GENERATED_DIRECTORY = 'generated'

AIRPORTS = 'airports-extended.dat'
TRAINSTATIONS = 'european-train-stations.csv'
GEONAMES = 'allCountries.zip'
GEONAMES_DATA = 'allCountries.txt'

# Description: http://www.geonames.org/export/codes.html
geonames_allowed_types = set(['P'])

MINIMAL_KM_STEPS = 100
MAXIMAL_KM_STEPS = 3000

interesting_country_codes = set([
	'AD',
	'AL',
	'AT',
	'AX',
	'BA',
	'BE',
	'BG',
	'BY',
	'CH',
	'CS',
	'CY',
	'CZ',
	'DE',
	'DK',
	'EE',
	'ES',
	'FI',
	'FO',
	'FR',
	'GB',
	'GG',
	'GI',
	'GR',
	'HR',
	'HU',
	'IE',
	'IM',
	'IS',
	'IT',
	'JE',
	'LI',
	'LT',
	'LU',
	'LV',
	'MC',
	'MD',
	'ME',
	'MK',
	'MT',
	'NL',
	'NO',
	'PL',
	'PT',
	'RO',
	'RS',
	'RU',
	'SE',
	'SI',
	'SJ',
	'SK',
	'SM',
	'UA',
	'VA',
	'XK',
])


def distance(p1_lat,p1_long,p2_lat,p2_long):
	# Based on https://gist.github.com/willperkins/1051879
	if p1_lat == p2_lat and p1_long == p2_long:
		return 0.0
	
	multiplier = 6371.0
	return (multiplier *
		acos(
			cos(radians(p1_lat)) *
			cos(radians(p2_lat)) *
			cos(radians(p2_long) - radians(p1_long)) +
			sin(radians(p1_lat)) * sin(radians(p2_lat)))
	)


def sqlite_with_distance():
	conn = sqlite3.connect(DATABASE_NAME)
	sqlite3.enable_callback_tracebacks(True)
	conn.execute('pragma journal_mode=wal')
	conn.create_function('distance', 4, distance)
	conn.text_factory = lambda x: unicode(x, 'utf-8', 'ignore')
	return conn

