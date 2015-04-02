"use strict";

/*
 * web/static/js/views/DeploymentItemView.js
 */

var DeploymentItemView = Backbone.View.extend({
  tagName: 'li',
  initialize: function() {
  },
  template: JST['static/js/partials/DeploymentItem.html'],
  render: function() {
    this.$el.html(this.template({model: this.model}));
    return this;
  }
});
