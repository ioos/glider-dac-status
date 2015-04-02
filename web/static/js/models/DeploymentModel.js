var DeploymentModel = Backbone.Model.extend({
  urlRoot: '../api/deployment',
  defaults: {
    completed: null,
    created: null,
    dap: "",
    deployment_dir: "",
    erddap: "",
    estimated_deploy_date: null,
    estimated_deploy_location: "",
    iso: "",
    name: "",
    operator: "",
    sos: "",
    thredds: "",
    updated: null,
    username: "",
    geo_json: {}, // Requires a separate fetch
    wmo_id: ""
  },
  fetchGeoJSON: function() {
    var self = this;
    var url = '../api/track/' + this.get('username') + '/' + this.get('name');
    $.ajax({
      url: url,
      dataType: 'json',
      success: function(data) {
        self.set('geo_json', data);
        self.trigger('deployment:geojson', self);
      }
    });
  },
});

var DeploymentCollection = Backbone.Collection.extend({
  url: '../api/deployment',
  model: DeploymentModel,
  parse: function(response) {
    if(response && response.results) {
      return response.results;
    }
    return [];
  }
});
