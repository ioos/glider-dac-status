"use strict";
/*
 * navo/static/js/views/MapView.js
 * View definition for the Map
 *
 * Partials:
 *  
 */

var MapView = Backbone.View.extend({
  initialize: function(options) {
    var self = this;
    _.bindAll(this, "onEachFeature", "highlight_layer", "reset_highlight");
    var center = [41.505, -80.09];
    var zoom = 3;
    var maxZoom = 18;

    this.featureStyle = {
        "color": "#ff7800",
        "weight": 5,
        "opacity": 0.85
    };

    this.controlLayers = null;

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

    if (options.bbox) {
      this.map.fitBounds(options.bbox);
    }

    this.map.on('click', function(event) {
      self.trigger('mapClick', self);
    });
    this.map.on('popupopen', function(e) {
      // The top UL corner of the popup was under the zoom controls.
      // Thank you, http://stackoverflow.com/questions/22538473/leaflet-center-popup-and-marker-to-the-map.
      var px = e.popup._map.project(e.popup._latlng); // find the pixel location on the map where the popup anchor is
      px.y -= e.popup._container.clientHeight/2 // find the height of the popup container, divide by 2, subtract from the Y axis of marker location
      e.popup._map.panTo(e.popup._map.unproject(px),{animate: true}); // pan to new center
    });
    return this
  },
  addTrajectory: function(feature) {
    L.geoJson(feature, {
        style: this.featureStyle,
        onEachFeature: this.onEachFeature
    }).addTo(this.map);
  },
  onEachFeature: function(feature, layer) {
    var self = this;
    var popupContent = "No Popup Content";
    if (feature.properties && feature.properties.popupContent) {
      popupContent = feature.properties.popupContent;
    }
    layer.bindPopup(popupContent);
    layer.on({
      mouseover: function(e) {
        self.highlight_layer(layer);
      },
      mouseout: function(e) {
        self.reset_highlight(layer);
      }
    });
  },
  highlight_layer: function(layer) {
    if (layer._map != null) {
      layer.setStyle({color: 'red'});
    }
  },
  reset_highlight: function(layer) {
    layer.setStyle(this.featureStyle);
  },
  //renders a simple map view
  render: function() {
      //needs to be set
    L.Icon.Default.imagePath = '/lib/leaflet/dist/images';
   
    var map = this.map;

    if(this.controlLayers === null) {

      var oceansBasemap = L.tileLayer('http://services.arcgisonline.com/ArcGIS/rest/services/Ocean_Basemap/MapServer/tile/{z}/{y}/{x}.jpg', {
          minZoom: 1,
          maxZoom: 12,
          attribution: 'Sources: Esri, GEBCO, NOAA, National Geographic, DeLorme, HERE, Geonames.org, and other contributors'
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
      /*

      var satelliteWMS = new L.TileLayer.WMS('http://whooms.mapwarper.net/wms', {
        layers: 'current_image.tiff',
        format: 'image/png',
        attribution: "I'll deal with it later",
        opacity: 0.4
      });
      //http://whooms.mapwarper.net/wms?SERVICE=WMS&REQUEST=GetMap&VERSION=1.1.1&LAYERS=current_image.tiff&STYLES=&FORMAT=image%2Fpng&TRANSPARENT=false&HEIGHT=256&WIDTH=256&SRS=EPSG%3A3857&BBOX=-9157767.484790396,5048512.844179319,-9118631.726308387,5087648.602661328
      */


      oceansBasemap.addTo(this.map);
      this.controlLayers = L.control.layers({
        "ESRI OceansBaseMap" : oceansBasemap,
        "ESRI World Imagery" : Esri_WorldImagery
      })
      this.controlLayers.addTo(this.map);
    }
    

    L.Util.requestAnimFrame(map.invalidateSize,map,!1,map._container);
    return this;
  },
  /*
   * options: 
   *   lat,
   *   lon,
   *   highlighted
   */
  drawMarker: function(options) {
    if(!(options && options.lat && options.lon)) {
      console.error("lat and lon are required options");
      return;
    }

    var lat = options.lat;
    var lon = options.lon;

    var opts = {
      title: ''
    }
    _.extend(opts, options);

    var icon;

    if (opts.category == 'stations') {
      icon = L.AwesomeMarkers.icon({
        prefix: 'fa',
        icon: opts.highlighted || opts.selected ? 'fa-circle' : 'fa-circle-o',
        markerColor: opts.highlighted || opts.selected ? 'red' : 'darkblue',
        html: '',
        className: 'awesome-marker'
      });
    }
    else {
      icon = L.AwesomeMarkers.icon({
        prefix: 'fa',
        icon: ' ',
        markerColor: opts.highlighted || opts.selected ? 'red' : 'darkblue',
        html: options.html,
        className: 'awesome-marker awesome-marker-text'
      });
    }

    var marker = L.marker([lat, lon], {
      icon: icon,
      zIndexOffset: opts.highlighted || opts.selected ? 1000 : 0,
      title: opts.title,
    });

    if (!opts.hidden) { 
      marker.addTo(this.map);
    }

    return marker;
  },
  redraw: function() {
    this.map.invalidateSize();
  }
});

