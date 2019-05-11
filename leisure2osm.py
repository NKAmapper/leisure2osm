#!/usr/bin/env python
# -*- coding: utf8

# leisure2osm
# Converts Anleggsregisteret leisure facilities from JSON file to OSM format for import/update
# Usage: python leisure.py [input_filename.json]
# Loads data from Anleggsregisteret unless file name is given
# Loads municipality and county data from Kartverket/Geonorge


import json
import cgi
import sys
import urllib2
import copy


version = "0.3.0"

header = {
	"X-Requested-With": "XMLHttpRequest",
	"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1.2 Safari/605.1.15"
}


transform_municipality = {
	'Tana': 'Deatnu-Tana',
	'Kautokeino': 'Guovdageaidnu-Kautok',
	'Karasjok': 'Karasjohka-Karasjok',
	'Nesseby': 'Unjargga-Nesseby',
	u'Aurskog-Høland': u'Aurskog Høland'
}


# Output message

def message (output_text):

	sys.stdout.write (output_text)
	sys.stdout.flush()


# Produce a tag for OSM file

def make_osm_line(key,value):

    if value:
		encoded_value = cgi.escape(value.encode('utf-8'),True)
		out_file.write ('    <tag k="%s" v="%s" />\n' % (key, encoded_value))


# Output OSM tags for facility
# Includes correctig coordinats through testing alternative UTM zones

def process_facility (facility):

	global node_id, facilities_ok, facilities_fixed, facilities_noshow, facilities_nocoord, facilities_notfixed

	if facility['status'] == "EXISTING":

		# Check if coordinates are within municipality bounding box

		node_id -= 1
		latitude = facility['latitude']
		longitude = facility['longitude']
		message_text = ""

		if not (latitude and longitude):
			latitude = 0
			longitude = 0
			facilities_nocoord += 1
			message_text = "No coordinates"

		else:
			ref = facility['countyName'] + "/" + facility['municipalityName'].replace("Og", "og")
			bbox = municipalities[ ref ]

			if (latitude < bbox['latitude_min']) or (latitude > bbox['latitude_max']) or \
				(longitude < bbox['longitude_min']) or (longitude > bbox['longitude_max']):

				message_text = "Coordinates not within municipality"
				found = False

				if (latitude >= bbox['latitude_min']) and (latitude <= bbox['latitude_max']):

					# Attempt relocating longitude to identify correct UTM zone (each 6 degrees appart)

					for zone in [-3, -2, -1, 1, 2, 3]:
						test_longitude = longitude + zone*6.0

						if (test_longitude >= bbox['longitude_min']) and (test_longitude <= bbox['longitude_max']):
							longitude = test_longitude
							facilities_fixed += 1
							found = True
							message_text = "Longitude relocated %i degrees" % (zone * 6)
							break

				if not found:
					facilities_notfixed += 1

			else:
				facilities_ok += 1

				# Extra check for Oslo

				if (latitude == 59.917201 and longitude == 10.727413) or (latitude == 59.917112 and longitude == 10.727424):
					message_text = "Not exact coordinates (Oslo)"

		# Produce tags

		out_file.write ('  <node id="%i" lat="%f" lon="%f">\n' % (node_id, latitude, longitude))

		if message_text:
			make_osm_line("ERROR", message_text)

		make_osm_line("ref:anlegg", str(facility['facilityId']))

		name = facility['name'].replace(";", ",").strip()
		if name == name.upper():
			make_osm_line("name", name.title())
		else:
			make_osm_line("name", name)

		if facility['ownerName']:
			make_osm_line("owner", facility['ownerName'].strip().title())

		if facility['operatorName']:
			make_osm_line("operator", facility['operatorName'].strip().title())  # None seen in dataset

		make_osm_line("MUNICIPALITY", facility['municipalityName'].replace("Og", "og"))
		make_osm_line("COUNTY", facility['countyName'])

		make_osm_line("CATEGORY", facility['categoryDescription'])
		make_osm_line("TYPE", facility['typeDescription'])

		# Generate OSM tagging according to facility type json file

		if facility['typeDescription'] != "UDEFINERT":
			if facility['typeDescription'] in facility_tagging:
				for key,value in facility_tagging[ facility['typeDescription'] ].iteritems():
					make_osm_line(key, value)
			else:
				message ("Facility type '%s' in category '%s' not defined\n" % (facility['typeDescription'], facility['categoryDescription']))

		out_file.write ('  </node>\n')

	else:
		facilities_noshow += 1


# Main program

if __name__ == '__main__':

	message ("\nLoading municipality data... ")

	# Load tagging per facility type

	filename = "https://raw.githubusercontent.com/osmno/leisure2osm/master/anleggsregister_kategorier.json"
	file = urllib2.urlopen(filename)
	facility_tagging_data = json.load(file)
	file.close()

	facility_tagging = {}
	for facility_category, facility_types in facility_tagging_data.iteritems():
		for facility_type, facility_tags in facility_types.iteritems():
			facility_tagging[facility_type] = copy.deepcopy(facility_tags)

	# Load municipality bounding boxes

	file = urllib2.urlopen("https://ws.geonorge.no/kommuneinfo/v1/kommuner")
	municipalities_data = json.load(file)
	file.close()
	municipalities = {}

	for municipality in municipalities_data:

		query = "https://ws.geonorge.no/kommuneinfo/v1/kommuner/%s" % municipality['kommunenummer']
		request = urllib2.Request(query, headers=header)
		file = urllib2.urlopen(request)
		municipality_data = json.load(file)
		file.close()

		name = municipality_data['fylkesnavn'] + "/"
		if municipality_data['kommunenavnNorsk'] in transform_municipality:
			name += transform_municipality[ municipality_data['kommunenavnNorsk'] ]
		else:
			name += municipality_data['kommunenavnNorsk']

		bbox = {
			'latitude_min': 90.0,
			'latitude_max': -90.0,
			'longitude_min': 180.0,
			'longitude_max': -180.0
		}

		for node in municipality_data['avgrensningsboks']['coordinates'][0][1:]:
			bbox['latitude_max'] = max(bbox['latitude_max'], node[1])
			bbox['latitude_min'] = min(bbox['latitude_min'], node[1])
			bbox['longitude_max'] = max(bbox['longitude_max'], node[0])
			bbox['longitude_min'] = min(bbox['longitude_min'], node[0])

		municipalities[name] = bbox

	# Initiate OSM file and counters

	message ("\nConvertering facilities...\n")

	out_filename = "anleggsregister.osm"
	out_file = open(out_filename, "w")

	out_file.write ('<?xml version="1.0" encoding="UTF-8"?>\n')
	out_file.write ('<osm version="0.6" generator="facility2osm v%s" upload="false">\n' % version)

	facilities_count = 0
	facilities_ok = 0
	facilities_fixed = 0
	facilities_notfixed = 0
	facilities_noshow = 0
	facilities_nocoord = 0

	node_id = -1000
	last_page = False
	page = 0

	# Iterate all facilities and produce OSM tags

	while not last_page:

		link = "https://fagsystem.anleggsregisteret.no/idrett/api/facilities?page=%i&size=500&" % page
		request = urllib2.Request(link, headers=header)
		file = urllib2.urlopen(request)
		facility_data = json.load(file)
		file.close()

		for facility in facility_data['content']:
			process_facility (facility)
			facilities_count += 1

		message ("\r%i " % facilities_count)

		last_page = facility_data['last']
		page += 1


	# Produce OSM file footer

	out_file.write ('</osm>\n')
	out_file.close()

	message ("\rFacilities saved to file '%s'...\n"  % out_filename)
	message ("  Loaded from Anleggsregisteret: %i\n" % facilities_count)
	message ("  Not existing                 : %i\n" % facilities_noshow)
	message ("  With correct coordinates     : %i\n" % facilities_ok)
	message ("  With fixed coordinates       : %i\n" % facilities_fixed)
	message ("  With incorrect coordinates   : %i\n" % facilities_notfixed)
	message ("  Wihout coordinates           : %i\n" % facilities_nocoord)
