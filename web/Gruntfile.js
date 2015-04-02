module.exports = function(grunt) {

  // Project configuration.
  grunt.initConfig({
    jst: {
      compile: {
        files: {
          "static/app/summary_templates.js": [
            "static/js/partials/DeploymentItem.html",
            "static/js/partials/IOOSBanner.html",
            "static/js/partials/SidePanel.html",
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
            // Lib
            "static/lib/bootstrap-select/dist/js/bootstrap-select.js",
            // Models
            "static/js/models/ColorPaletteModel.js",
            "static/js/models/DeploymentModel.js",
            "static/js/models/InstitutionModel.js",
            "static/js/models/NAVOGliderModel.js",
            // Views
            "static/js/views/DeploymentItemView.js",
            "static/js/views/IOOSBannerView.js",
            "static/js/views/MapView.js",
            "static/js/views/SidePanelView.js"
          ]
        }
      },
      css: {
        files: {
          "static/app/summary.css" : [
            "static/lib/bootstrap-select/dist/css/bootstrap-select.css",
            "static/css/Banner.css",
            "static/css/Map.css",
            "static/css/SidePanel.css"
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
