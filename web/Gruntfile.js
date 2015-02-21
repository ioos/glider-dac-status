module.exports = function(grunt) {

  // Project configuration.
  grunt.initConfig({
    jst: {
      compile: {
        files: {
          "static/app/summary_templates.js": [
            "static/js/partials/Map.html"
          ]
        }
      }
    },
    concat: {
      js: {
        options: {
          banner: "'use strict';\n",
          process: function(src, filepath) {
            return '// Source: ' + filepath + '\n' +
            src.replace(/(^|\n)[ \t]*('use strict'|"use strict");?\s*/g, '$1');
          },
        },
        files: {
          "static/app/summary.js" : [
            // Models
            "static/js/models/DeploymentModel.js",
            // Views
            "static/js/views/MapView.js"
          ]
        }
      },
      css: {
        files: {
          "static/app/summary.css" : [
            "static/css/Map.css"
          ]
        }
      }
    },
    watch: {
      partials: {
        files: ['**/partials/*.html'],
        tasks: ['jst'],
        options: {
        }
      },
      scripts: {
        files: ['**/views/*.js', '**/models/*.js', '**/css/*.css'],
        tasks: ['concat'],
        options: {
        }
      }
    }
  })

  // Load the plugin that provides the "uglify" task.
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-jst');
  grunt.loadNpmTasks('grunt-contrib-watch');

  grunt.registerTask('default', ['jst', 'concat']);
  // Empty Commnet
};
