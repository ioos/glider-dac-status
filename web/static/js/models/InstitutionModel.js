"use strict";
/*
 * navo/static/js/models/TrajectoryModel.js
 * Model definition for the glider trajectory
 */

var InstitutionModel = Backbone.Model.extend({
  url: '#',
  defaults: {
    name: ""
  }
});


var InstitutionCollection = Backbone.Collection.extend({
  model: InstitutionModel
});
