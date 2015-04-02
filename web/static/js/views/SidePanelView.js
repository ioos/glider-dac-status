"use strict";
/*
 * web/static/js/views/SidePanelView.js
 */

var SidePanelView = Backbone.View.extend({
  subviews: [],
  initialize: function() {
  },
  add: function(model) {
    var subview = new DeploymentItemView({model: model}).render();
    this.subviews.push(subview);
    this.$el.find('.deployment-list').append(subview.el);
  },
  template: JST['static/js/partials/SidePanel.html'],
  render: function() {
    this.$el.html(this.template());
  }
});
