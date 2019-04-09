import csv
import logging
import os
import progressbar
import zipfile

import common


logging.basicConfig(level=logging.DEBUG)


def add_location_entry(loc_name, loc_main_name, loc_population, loc_country, loc_train, loc_airport, loc_lat, loc_lon):
	sql = '''INSERT INTO locations(name, main_name, population, country, has_train, has_airport, lat, lon)
	  VALUES(?,?,?,?,?,?,?,?)'''
	c.execute(sql, [loc_name, loc_main_name, loc_population, loc_country, loc_train, loc_airport, loc_lat, loc_lon])


conn = common.sqlite_with_distance()
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS locations
			 (id INTEGER PRIMARY KEY AUTOINCREMENT, name text NOT NULL, main_name text NOT NULL, population integer, country text NOT NULL, has_train integer, has_airport integer, lat REAL, lon REAL);''')
conn.commit()

# Loading airport data
airport_names = set()
with open(os.path.join(common.DATA_DIRECTORY, common.AIRPORTS), 'rb') as fc:
	for airport in csv.reader(fc, delimiter=',', quotechar='"'):
		airport_names.add(airport[2].lower())

logging.info('%d unique airport names.' % len(airport_names))

# Loading train station data
station_names = set()
station_data = {}
latlon_separator = ', '
with open(os.path.join(common.DATA_DIRECTORY, common.TRAINSTATIONS), 'rb') as fc:
	stations = csv.reader(fc, delimiter=';')
	stations.next()
	for station in stations:
		station_names.add(station[1].lower())
		
		if latlon_separator in station[-1]:
			lat, lon = station[-1].split(latlon_separator)
		else:
			lat = 0
			lon = 0
		station_data[station[1].lower()] = (station[7], float(lat), float(lon))

logging.info('%d unique train station names.' % len(station_names))

commit_interval = 5000
commit_count = 0

cities_added = 0

# Loading GeoNames data
with zipfile.ZipFile(os.path.join(common.DATA_DIRECTORY, common.GEONAMES)) as f:
	with f.open(common.GEONAMES_DATA) as fc:
		# counting the rows first...
		max_value = sum(1 for _ in fc)

	# Description: http://download.geonames.org/export/dump/readme.txt
	with f.open(common.GEONAMES_DATA) as fc:
		with progressbar.ProgressBar(max_value=max_value) as bar:
			pos = 0
			for city in csv.reader(fc, delimiter='\t', quotechar='"'):
				pos += 1
				bar.update(pos)

				# Skipping - type mismatch
				if not city[6] in common.geonames_allowed_types:
					continue
				
				# Skipping - there is no coordinate to begin with
				if city[4] == 0 and city[5] == 0:
					continue
				
				# Skipping - country is outside of the search area
				if not ((city[8] in common.interesting_country_codes) or (city[9] in common.interesting_country_codes)):
					continue
				
				found_country = city[8]
				
				main_name = city[2].lower()
				# We'll always add the main name of the city
				names_to_add = [main_name]
				
				city_has_train = False
				city_has_airport = False
				
				# Checking the airport - alternative names doesn't matter now
				if city[2].lower() in airport_names:
					city_has_airport = True				
				
				# We'll collect all possible names listed for this "city"
				all_name_variants = [city[2].lower()]

				if city[3]:
					for alternative_name in city[3].split(','):
						all_name_variants.append(alternative_name.strip().lower())
				
				# We need to check each of the name variants in terms of having train stations
				# - there are a few cases where the train station is only listed under an "alternative name"
				for name_variant in list(set(all_name_variants)):

					# Skipping this "name variant" if there is no such train station data at all
					if not name_variant.lower() in station_names:
						continue
					
					# Skipping this "name variant" if there is neither an airport nor a train station
					if not name_variant in station_names and not name_variant in airport_names:
						continue

					# Otherwise, we'll keep the name candidate
					names_to_add.append(name_variant)

					# Verifying the train station data
					
					train_station_country = station_data[name_variant][0]
						
					# Skipping this "name variant" if it is in a different country anyway than the train station we found
					if found_country != train_station_country:
						continue
					
					train_station_latitude = station_data[name_variant][1]
					train_station_longitude = station_data[name_variant][2]
					
					# If we have geolocation, we verify whether the location of the train station is close enough to the city we have
					# The threshold is 10 km now
					distance_threshold = 10
					if train_station_latitude != 0 and train_station_longitude != 0:
						try:
							if distance(train_station_latitude, train_station_longitude, float(city[4]), float(city[5])) > distance_threshold:
								continue
						except:
							# There are a few broken entries that would break this above
							pass
				
					# We know it had a train station
					city_has_train = True
				
				# Adding all names we found
				for name_to_add in names_to_add:
					add_location_entry(name_to_add, main_name, float(city[14]), found_country, city_has_train, city_has_airport, float(city[4]), float(city[5]))
					cities_added += 1
					commit_count += 1
					
					if commit_count > commit_interval:
						conn.commit()
						commit_count = 0
						bar.update(pos)
				
			conn.commit()

logging.info('First pass: %d location names.' % cities_added)				

c.execute('''CREATE INDEX IF NOT EXISTS name_country ON locations (name, country);''')
c.execute('''CREATE INDEX IF NOT EXISTS lat_lon ON locations (lat, lon);''')

# A number of identical entries may appear - in the second pass, we make sure to have only one entry for one place

commit_count = 0

with progressbar.ProgressBar(max_value=progressbar.UnknownLength) as bar:
	for row in c.execute('SELECT name, count(*) FROM locations GROUP BY name HAVING count(*) > 1;').fetchall():
		for city in c.execute('SELECT name, country FROM locations WHERE name = ? GROUP BY country;', (row[0],)).fetchall():
			found = False
			for ccity in c.execute('SELECT id, lat, lon FROM locations WHERE name = ? and country = ?;', city).fetchall():
				if found:
					c.execute('DELETE FROM locations WHERE id = ?;', (ccity[0],))
					continue
				
				if ccity[1] != 0 and ccity[2] != 0:
					found = True
				else:
					c.execute('DELETE FROM locations WHERE id = ?;', (ccity[0],))
			commit_count += 1
		
		if commit_count > commit_interval:
			conn.commit()
			c.execute('SELECT count(*) FROM locations;')
			number = c.fetchone()[0]
			bar.update(max_value - number)
			commit_count = 0

conn.commit()

c.execute('SELECT count(*) FROM locations;')
number = c.fetchone()[0]

logging.info('Second pass: %d location names.' % number)				

conn.close()
