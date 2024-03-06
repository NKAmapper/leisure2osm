#!/usr/bin/env python3
# -*- coding: utf8

# leisure2osm
# Converts Anleggsregisteret leisure facilities from JSON file to OSM format for import/update
# Usage: python leisure.py
# Loads municipality and county data from Kartverket/Geonorge + tagging scheme from Github


import json
import html
import sys
import urllib.request
import copy


version = "1.0.0"

header = {
	"X-Requested-With": "XMLHttpRequest",
	"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1.2 Safari/605.1.15"
}


transform_municipality = {
	'Deatnu-Tana': 'Tana',
	'Guovdageaidnu-Kautok': 'Kautokeino',
	'Karasjohka-Karasjok': 'Karasjok',
	'Unjargga-Nesseby': 'Nesseby',
	'Aurskog Høland': 'Aurskog-Høland'
}

transform_name = {
	'Hus': 'hus',
	'Grendehus': 'grendehus',
	'Grendahus': 'grendahus',
	'Forsamlingshus': 'forsamlingshus',
	'Samfunnshus': 'samfunnshus',
	'Ungdomshus': 'ungdomshus',
	'Aktivitetshus': 'aktivitetshus',
	'Klubbhus': 'klubbhus',
	'Velhus': 'velhus',
	'Bedehus': 'bedehus',
	'Misjonshus': 'misjonshus',
	'Menighetshus': 'menighetshus',
	'Eldrehus': 'eldrehus',
	'Speiderhus': 'speiderhus',
	'Kulturhus': 'kulturhus',
	'Flerbrukshus': 'flerbrukshus',
	'Kultursenter': 'kultursenter',
	'Kulturbygg': 'kulturbygg',
	'Bibliotek': 'bibliotek',
	'Skole': 'skole',
	'Skule': 'skule',
	'Ungdomsskole': 'ungdomsskole',
	'Ungdomsskule': 'ungdomsskule',
	'U-skole': 'ungdomsskole',
	'Videregående': 'videregående'
}

transform_owner = {
	'Kommune': 'kommune',
	'Bygdelag': 'bygdelag',
	'Idrettsforening': 'idrettsforeing',
	'Idrettsklubb': 'idrettsklubb',
	'Idrettslag': 'idrettslag',
	'Sportsklubb': 'sportsklubb',
	'Ungdomslag': 'ungdomslag',
	'I': 'i',
	'Og': 'og',
	'For': 'for',
	'Avd': 'avd',
	'Al': 'AL',
	'As': 'AS',
	'Ba': 'BA',
	'Da': 'DA',
	'If': 'IF',
	'Il': 'IL',
	'Ik': 'IK',
	'Sa': 'SA',
	'Sk': 'SK',
	'Ul': 'UL',
	'Kfuk': 'KFUK',
	'Kfum': 'KFUM',
	'Kfuk/Kfum': 'KFUK/KFUM',
	'Kfuk-Kfum': 'KFUK/KFUM'
}



# Output message

def message (output_text):

	sys.stdout.write (output_text)
	sys.stdout.flush()



# Produce a tag for OSM file

def make_osm_line(key,value):

	if value:
		encoded_value = html.escape(value).strip()
		out_file.write ('    <tag k="%s" v="%s" />\n' % (key, encoded_value))



# Output OSM tags for facility
# Includes correctig coordinats through testing alternative UTM zones

def process_facility (facility):

	global node_id, facilities_ok, facilities_fixed, facilities_noshow, facilities_nocoord, facilities_notfixed, new_category_structure

	if facility['status'] == "EXISTING":

		# Check if coordinates are within municipality bounding box

		node_id -= 1
		latitude = facility['latitude']
		longitude = facility['longitude']
		message_text = ""

		municipality = facility['municipalityName']
		if municipality == municipality.upper():
			municipality = municipality.title()
		municipality = municipality.replace("Og", "og").replace(" Kommune", "")
		if municipality in transform_municipality:
			municipality = transform_municipality[ municipality ]

		ref = facility['countyName'] + "/" + municipality

		if not (latitude and longitude):
			latitude = 0
			longitude = 0
			facilities_nocoord += 1
			message_text = "No coordinates"

		else:
			bbox = municipalities[ ref ]

			if (latitude < bbox['latitude_min'] or latitude > bbox['latitude_max']
				or longitude < bbox['longitude_min'] or longitude > bbox['longitude_max']):

				message_text = "Coordinates not within municipality"
				found = False

				if latitude >= bbox['latitude_min'] and latitude <= bbox['latitude_max']:

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

				if latitude == 59.917201 and longitude == 10.727413 or latitude == 59.917112 and longitude == 10.727424:
					message_text = "Not exact coordinates (Oslo)"

		# Produce tags

		out_file.write ('  <node id="%i" lat="%f" lon="%f">\n' % (node_id, latitude, longitude))

		if message_text:
			make_osm_line("ERROR", message_text)

		make_osm_line("ref:anlegg", str(facility['facilityId']))

		name = facility['name'].replace(";", ",").strip()
		if name == name.upper():
			name = name.title()

		name_split = name.split(" ")
		for i, word in enumerate(name_split):
			if i > 0 and word in transform_name:
				name_split[i] = transform_name[ word ]
		name = " ".join(name_split)
		make_osm_line("name", name)

		if facility['ownerName']:
			owner = facility['ownerName'].strip().title()
			owner_split = owner.split(" ")
			for i, word in enumerate(owner_split):
				if word in transform_owner:
					owner_split[i] = transform_owner[ word ]
			owner = " ".join(owner_split)
			make_osm_line("owner", owner)

		if facility['operatorName'] and facility['operatorName'] != facility['ownerName']:
			operator = facility['operatorName'].strip().title()
			operator_split = operator.split(" ")
			for i, word in enumerate(operator_split):
				if word in transform_owner:
					operator_split[i] = transform_owner[ word ]
			operator = " ".join(operator_split)			
			make_osm_line("operator", operator)


		if ref in municipalities:
			make_osm_line("MUNICIPALITY", "#%s %s" % (municipalities[ ref ]['ref'], municipality))
		else:
			make_osm_line("MUNICIPALITY", municipality)
		make_osm_line("COUNTY", facility['countyName'])

		make_osm_line("CATEGORY", facility['categoryDescription'])
		make_osm_line("TYPE", facility['typeDescription'])

		# Generate OSM tagging according to facility type json file

		if facility['typeDescription'] != "UDEFINERT":
			# Get tags
			if facility['typeDescription'] in facility_tagging:
				for key,value in iter(facility_tagging[ facility['typeDescription'] ].items()):
					make_osm_line(key, value)
			else:
				not_defined.add( (facility['categoryDescription'], facility['typeDescription']) )  # Display at end

			# Build updated category dict
			if facility['categoryDescription'] not in new_categories:
				new_categories[ facility['categoryDescription'] ] = {}
			if facility['typeDescription'] not in new_categories[ facility['categoryDescription'] ]:
				if facility['typeDescription'] in facility_tagging:
					tags = facility_tagging[ facility['typeDescription'] ]
				else:
					tags = { 'FIXME': 'New facility type' }
				new_categories[ facility['categoryDescription'] ][ facility['typeDescription'] ] = tags

			if facility['categoryDescription'] not in facility_tagging_data or facility['typeDescription'] not in facility_tagging_data[ facility['categoryDescription'] ]:
				new_category_structure = True

		out_file.write ('  </node>\n')

	else:
		facilities_noshow += 1



# Main program

if __name__ == '__main__':

	message ("\nLoading municipality boundaries... ")

	# Load tagging per facility type

	filename = "https://raw.githubusercontent.com/osmno/leisure2osm/master/anleggsregister_kategorier.json"
	file = urllib.request.urlopen(filename)
#	file = open("anleggsregister_kategorier.json")  # For testing
	facility_tagging_data = json.load(file)
	file.close()

	facility_tagging = {}
	for facility_category, facility_types in iter(facility_tagging_data.items()):
		for facility_type, facility_tags in iter(facility_types.items()):
			facility_tagging[facility_type] = copy.deepcopy(facility_tags)

	# Load municipality bounding boxes

	file = urllib.request.urlopen("https://ws.geonorge.no/kommuneinfo/v1/kommuner")
	municipalities_data = json.load(file)
	file.close()
	municipalities = {}

	for municipality in municipalities_data:

		query = "https://ws.geonorge.no/kommuneinfo/v1/kommuner/%s" % municipality['kommunenummer']
		file = urllib.request.urlopen(query)
		municipality_data = json.load(file)
		file.close()

		ref = municipality_data['fylkesnavn'] + "/" + municipality_data['kommunenavnNorsk']

		bbox = {
			'ref': municipality['kommunenummer'],
			'latitude_min': 90.0,
			'latitude_max': -90.0,
			'longitude_min': 180.0,
			'longitude_max': -180.0
		}

		for node in municipality_data['avgrensningsboks']['coordinates'][0]:
			bbox['latitude_max'] = max(bbox['latitude_max'], node[1])
			bbox['latitude_min'] = min(bbox['latitude_min'], node[1])
			bbox['longitude_max'] = max(bbox['longitude_max'], node[0])
			bbox['longitude_min'] = min(bbox['longitude_min'], node[0])

		municipalities[ ref ] = bbox

	# Initiate OSM file and counters

	message ("\nConvertering facilities...\n")

	out_filename = "anleggsregister.osm"
	out_file = open(out_filename, "w")

	out_file.write ('<?xml version="1.0" encoding="UTF-8"?>\n')
	out_file.write ('<osm version="0.6" generator="leisure2osm v%s" upload="false">\n' % version)

	facilities_count = 0
	facilities_ok = 0
	facilities_fixed = 0
	facilities_notfixed = 0
	facilities_noshow = 0
	facilities_nocoord = 0

	node_id = -1000
	last_page = False
	page = 0

	not_defined = set()  # Will contain new facility categories/types not found in category file
	new_categories = {}  # Will contain updated facility cateogry dict as read from api
	new_category_structure = False  # Will become True if category structure has been changed in api

	# Iterate all facilities and produce OSM tags

	while not last_page:

#		link = "https://fagsystem.anleggsregisteret.no/idrett/api/facilities?page=%i&size=500&" % page
		link = "https://backoffice.anleggsregisteret.no/api/facilities?page=%i&size=500" % page
		request = urllib.request.Request(link, headers=header)
		file = urllib.request.urlopen(request)
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

	# Output updated types/categories

	if not_defined:
		message ("\nFacility types not defined (per category):\n")
		for missing in sorted(not_defined):
			message ("  '%s': '%s'\n" % (missing[0], missing[1]))

	if not_defined or new_category_structure:
		filename = "anleggsregister_kategorier_ny.json"
		message ("\nSaving new categories to '%s'\n" % filename)
		file = open(filename, "w")
		sorted_categories = { key: dict(sorted(new_categories[key].items())) for key in sorted(new_categories) }  # Two level sort
		json.dump(sorted_categories, file, indent=4, ensure_ascii=False)
		file.close()
		if new_category_structure:
			message ("  Category structure was modified\n")

	message ("\n")
