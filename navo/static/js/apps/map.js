var App = function() {
}

_.extend(App.prototype, Backbone.Events, {
  views: {
    mapView: null
  },
  models: {
    trajectory: null,
  },
  start: function() {
    var self = this;
    /* Models */
    this.models.trajectory = new TrajectoryModel();

    var ur_lat = 17.85851867611398;
    var ur_lon = -63.949356079101555;

    var ll_lat = 17.15260066514817;
    var ll_lon = -65.04798889160156;
    
    /* Collections */

    /* Views */
    this.views.mapView = new MapView({
      el: '#map-view',
      bbox: [
        [ll_lat, ll_lon],
        [ur_lat, ur_lon]
      ]
    }).render();

    /* Listeners */
    this.listenTo(this.views.mapView, 'mapClick', function(mapView) {
      console.log(mapView.map.getZoom());
      console.log(mapView.map.getBounds());
    });


    /* Fetches */
    var trajectoryFetch = this.models.trajectory.fetch();

    $.when(trajectoryFetch).done(function() {
      var feature = self.models.trajectory.get('feature');

      feature.properties.popupContent = "Glider ng292";

      self.views.mapView.addTrajectory(feature);
    });
  }
});

var app = new App();
