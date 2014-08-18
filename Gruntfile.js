var path = require('path');

module.exports = function(grunt) {

  log = function(err, stdout, stderr, cb) {
    console.log(stdout);
    cb();
  };

  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),
    protractor: {
      options: {
        configFile: "test/protractor.conf.js", // Default config file
        args: {
          seleniumPort: 4444
        }
      },
      run: {}
    },
    simplemocha: {
      options: {
        reporter: "spec"
      },
      unit: { src: ['./test/unit/*.js'] },
      functional: { src: ['./test/functional/*.js'] }

    }
  });

  grunt.loadNpmTasks('grunt-protractor-runner');

  grunt.loadNpmTasks('grunt-selenium-webdriver');

  grunt.loadNpmTasks('grunt-simple-mocha');

  grunt.registerTask("protractorTest", "custom test", function() {
    var app = require('./app.js');
    app.set('port', process.env.PORT || 3000);

    var server = app.listen(app.get('port'), function() {
      grunt.log.writeln('Express server listening on port ' + server.address().port);
    });

    grunt.task.run("protractor");
  });

  grunt.registerTask('angular', ['selenium_start', 'selenium_phantom_hub', 'protractorTest', 'selenium_stop']);
  grunt.registerTask('unit', ['simplemocha:unit']);
  grunt.registerTask('functional', ['simplemocha:functional']);
};
