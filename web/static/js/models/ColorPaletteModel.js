"use strict";

/*
 * web/static/js/models/ColorPaletteModel.js
 */

var ColorPaletteModel = Backbone.Model.extend({
  url: 'static/json/colors.json',
  chooseColor: function() {
    var colors = this.get('colors');
    var idx = this.get('index');
    var color = colors[idx++ % colors.length];
    this.set('index', idx);
    return color;
  },
  defaults: {
    colors: [
      '#671DD1',
      '#9920DE',
      '#D624F0',
      '#DB1E65',
      '#D61FB8'
    ],
    index: 0
  }
});
