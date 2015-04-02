'use strict';
 
module.exports = function(grunt) {
  // Project Configuration
  grunt.initConfig({
    assets: grunt.file.readJSON('assets.json'),
    jade: {
      compile: {
        options: {
          data: {
            debug: true
          },
          client: true,
          processName: function(filename) {
            var templateRoot = 'static/js/partials/';
            return filename.split(templateRoot)[1];
          }
        },
        files: {
          "static/build/templates/example.js" : [
            "static/javascripts/partials/example.jade"
          ]
        }
      }
    },
    uglify: {
      main: {
        options: {
          mangle: true,
          compress: true
        },
        files: '<%= assets.main.js %>'
      }
    },
    cssmin: {
      main: {
        files: '<%= assets.main.css %>'
      }
    }
  });
 
  //Load NPM tasks
  grunt.loadNpmTasks('grunt-contrib-cssmin');
  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-contrib-jade');
 
  //Making grunt default to force in order not to break the project.
  grunt.option('force', true);
 
  //Default task(s).
  grunt.registerTask('default', ['jade', 'cssmin', 'uglify']);
 
};
