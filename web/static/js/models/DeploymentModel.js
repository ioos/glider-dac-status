var DeploymentModel = Backbone.Model.extend({
  urlRoot: '/api/deployment',
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
    wmo_id: ""
  }
});

var DeploymentCollection = Backbone.Collection.extend({
  url: '/api/deployment',
  model: DeploymentModel,
  parse: function(response) {
    if(response && response.results) {
      return response.results;
    }
    return [];
  }
});
