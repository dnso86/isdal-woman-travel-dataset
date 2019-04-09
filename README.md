# Isdal Woman Travel dataset

This script generates a SQLite database containing place names, geolocation and airport / train station information - to facilitate analysis on the notes of the "Isdal woman". You can read more about the case of the Isdal Woman [here](https://www.nrk.no/dokumentar/do-you-remember-this-woman_-1.13215629).

# Generating the dataset

- Go to [GeoNames](http://www.geonames.org/) and download the file called `allCountries.zip`
- Go to [OpenDataSoft](https://public.opendatasoft.com) and download the file containing the list of european train stations, `european-train-stations.csv`
- Go to [openflights.org](https://openflights.org/data.html) and download the file containing the OpenFlights Airports Database, `airports-extended.dat`
- Copy all files downloaded above to the `data/` directory
- Run `load-data.py`
- The database will be saved to `isdal-geo.sqlite`


