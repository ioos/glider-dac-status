"use strict";
/*
 * navo/static/js/models/TrajectoryModel.js
 * Model definition for the glider trajectory
 */

var NAVOGliderModel = Backbone.Model.extend({
  url: '../navo/static/json/trajectories.json',
  parse: function(response) {
    return {feature: response};
  }
});

