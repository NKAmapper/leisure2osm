# leisure2osm
Extracts leisure facilities from [Anleggsregisteret](https://www.anleggsregisteret.no/) and produces an OSM file.

### Usage

<code>python leisure2osm.py</code>

### Notes

* "*Anleggsregisteret*" is a register maintained by the Ministry of Culture which contains all sport, leisure and culture facilities in Norway which have received public funding. The information is being registered by municipalities and counties.
* The program extracts all facilities from the register which are marked as *existing* and generates an OSM file with the file name "*anleggsregister.osm*".
* OSM tags are generated based on mapping the given facility types in the register using the JSON file [anleggsregister_kategorier.json](https://github.com/osmno/leisure2osm/blob/master/anleggsregister_kategorier.json).
  * Not all facilities are tagged due to too general categories/types.
  * All facilities are nodes in the generated OSM file. Some categories should be mapped as ways, for example a raceway or a soccer pitch.
  * Please propose changes to the mapping on GitHub if you discover errors or improvements.
* Notes on coordinates:
  * Coordinates are in general rough and need inspection.
  * Some coordinates are outside of the boarders of the given municipality - they get an *ERROR* tag.
  * Some facilities have no coordinates in the register - they get the (0,0) coordinate in the generated OSM file.
  * A number of facilities have been registered with the wrong UTM zone - their coordinates are fixed by the program and marked by an *ERROR* tag.
* Please review spelling and orthography of names and owners.
* Please remove tags with CAPITAL letters before uploading to OSM.


### References

* [Anleggsregisteret.no](https://www.anleggsregisteret.no)
* [OSM tagging per facility type](https://github.com/osmno/leisure2osm/blob/master/anleggsregister_kategorier.json)
