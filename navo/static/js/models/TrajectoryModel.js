"use strict";
/*
 * navo/static/js/models/TrajectoryModel.js
 * Model definition for the glider trajectory
 */

var TrajectoryModel = Backbone.Model.extend({
  url: 'static/json/trajectories.json',
  parse: function(response) {
    return {feature: response};
  }
});
