"use strict";
/*
 * web/static/js/views/IOOSBannerView.js
 *
 * View definition for the IOOS-style banner
 */
var IOOSBannerView = Backbone.View.extend({
  initialize: function() {
  },
  template: JST['static/js/partials/IOOSBanner.html'],
  render: function() {
    this.$el.html(this.template());
    return this;
  }
});
