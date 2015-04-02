"use strict";
/*
 * web/static/js/views/SidePanelView.js
 */

var SidePanelView = Backbone.View.extend({
  events: {
    'change #provider-select' : 'onSelect'
  },
  subviews: [],
  initialize: function(options) {
    if(options && options.institutions) {
      this.institutions = options.institutions;
    } else {
      console.error("Institutions is required");
    }
  },
  add: function(model) {
    var subview = new DeploymentItemView({model: model}).render();
    this.subviews.push(subview);
    this.$el.find('.deployment-list').append(subview.el);
  },
  onSelect: function(e) {
    this.trigger('onSelect', this.$el.find('#provider-select').val());
  },
  template: JST['static/js/partials/SidePanel.html'],
  render: function() {
    this.$el.html(this.template({institutions: this.institutions}));
    this.$el.find('.selectpicker').selectpicker({
    });
  }
});
