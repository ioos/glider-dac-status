"use strict";
/*
 * MapView
 *
 * A Leaflet Container in Backbone
 *
 * Models:
 * Partials:
 * SubViews:
 */
var MapView = Backbone.View.extend({
	initialize: function(options) {
		var self = this;
    var center = [41.505, -80.09];
    var zoom = 3;
    var maxZoom = 18;

    if(options && options.center) {
      center = options.center;
    }
    if(options && options.zoom) {
      zoom = options.zoom;
    }
    if(options && options.maxZoom) {
      maxZoom = options.maxZoom;
    }
    this.map = L.map(this.el,{
	       center: center,
	       zoom: zoom,
	       maxZoom: maxZoom
   	});
    this.render();
    return this
	},
  addTrajectory: function(feature) {
    var myStyle = {
        "color": "#ff7800",
        "weight": 5,
        "opacity": 0.85
    };

    L.geoJson(feature, {
        style: myStyle
    }).addTo(this.map);
  },
  example: function() {
    var geojsonFeature = {
      "type": "Feature",
      "properties": {
          "name": "Coors Field",
          "amenity": "Baseball Stadium",
          "popupContent": "This is where the Rockies play!"
      },
      "geometry": {
          "type": "Point",
          "coordinates": [-104.99404, 39.75621]
      }
    };
    L.geoJson(geojsonFeature).addTo(this.map);
    console.log("Added point");

    var myLines = [{
        "type": "LineString",
        "coordinates": [[-100, 40], [-105, 45], [-110, 55]]
    }, {
        "type": "LineString",
        "coordinates": [[-105, 40], [-110, 45], [-115, 55]]
    }];

    console.log("Added lines");
    this.map.setView([39.75, -104.99], 13);
  },
 	//renders a simple map view
	render: function() {
		//needs to be set
		L.Icon.Default.imagePath = '/lib/leaflet/dist/images';
   
    var map = this.map;

		var OSM = L.tileLayer('https://{s}.tiles.mapbox.com/v3/{id}/{z}/{x}/{y}.png', {
			maxZoom: 18,
			attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, ' +
				'<a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, ' +
				'Imagery © <a href="http://mapbox.com">Mapbox</a>',
			id: 'examples.map-20v6611k'
		}).addTo(map);
    "http://maps.ngdc.noaa.gov/arcgis/rest/services/web_mercator/etopo1_hillshade/MapServer/tile/2/2/0"
    var etopo = L.tileLayer('http://maps.ngdc.noaa.gov/arcgis/rest/services/web_mercator/etopo1_hillshade/MapServer/tile/{z}/{y}/{x}',{
      attribution: 'NOAA NGDC ETOPO1'
    });
    
	
		var Esri_WorldImagery = L.tileLayer('http://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{	
      attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
    });

    var Stamen_TonerHybrid = L.tileLayer('http://{s}.tile.stamen.com/toner-hybrid/{z}/{x}/{y}.png', {
      attribution: 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a> &mdash; Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>',
      subdomains: 'abcd',
      minZoom: 0,
      maxZoom: 20
    });     

    //HERE_hybridDay.addTo(map);    
    //OSM.addTo(this.map);
    etopo.addTo(this.map);
    //Esri_WorldImagery.addTo(map);
    //Stamen_TonerHybrid.addTo(map);

    L.Util.requestAnimFrame(map.invalidateSize,map,!1,map._container);
	},
});
