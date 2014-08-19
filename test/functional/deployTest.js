var should = require('should');
var http = require('http');
var fs = require('fs');
var AppAPI = require('../../lib/appApi');

var appHost = {
  url: "10.1.24.7",
  port: 80
};
var deploy_output_file = 'bin/deploy_output.json';

var dbExists = function(dbs, name) {
  Array.isArray(dbs).should.be.ok;
  return dbs.reduce(function(prev, curr) {
    return prev || (curr.name === name)
  }, false);
};

//App Instances :
// App instance works
// Connect
// Add Db
// Delete Db

var testApp = function(api, host) {
  var localhost = {
    url: "localhost",
    port: 3000
  }
  it("GET should have a default host of 'localhost'", function(done) {
      var options = {};
      options.host = localhost.url;
      options.path = "/mongo-api/host";
      options.method = 'GET';
      options.port = localhost.port;
      api.request(options, function(err, response) {
        var host = JSON.parse(response.body);
        host.url.should.equal("localhost");
        done();
      });
    });

  describe(api.host.url + "/host", function() {
    it("POST should change the host to a different url", function(done) {
      var newHostUrl = host.url;

      var options = {};
      options.host = api.host.url;
      options.path = "/mongo-api/host";
      options.method = 'POST';
      options.port = api.host.port;
      var postBody = {
        "url": newHostUrl
      };
      var postData = JSON.stringify(postBody);
      options.headers = {
          'Content-Type': 'application/json',
          'Content-Length': postData.length
      };
      api.request(options, postData, function(error, response) {
        var host = JSON.parse(response.body);
          host.url.should.equal(newHostUrl);
          done();
      });
    });
  });

  var createdDbs = [];
  describe(api.host.url + "/dbs", function() {
    afterEach(function(done) {
      var loop = function(index, callback, onComplete) {
        return function() {
          if (index<createdDbs.length) {
            var name = createdDbs[index];
            api.deleteDb(name, callback(index +1, loop, onComplete));
          }
          else {
            createdDbs = [];
            onComplete();
          }
        };
      };
      loop(0, loop, done)();
    });

    it("GET should return a list of databases including local", function(done) {
      api.getDbs(function(err, dbs) {
        dbExists(dbs, "local").should.be.ok;
        done();
      });
    });

    it("POST should add a new database", function(done) {
      var dbName = "newTestDatabase";

      api.createDb(dbName, function(error, dbs) {
        dbExists(dbs, dbName).should.be.true;
        createdDbs.push(dbName);
        done();
      });
    });

    it("DELETE should delete database", function(done) {
      var dbName = "newTestDatabase";
      api.createDb(dbName, function(error, dbs) {
        api.deleteDb(dbName, function(error, dbs) {
          dbExists(dbs, dbName).should.be.false;
          done();
        });
      });
    });
  });
};


describe("Meghdoot Test App", function() {
  var api = new AppAPI(appHost);
  before(function(done) {
    api.setHost(appHost, done);
  });

  afterEach(function(done) {
    api.setHost(appHost, done);
  });

  it("should be accessible", function(done) {
      var options = {};
      options.host = "10.1.24.7";
      http.get(options, function(response) {
        response.statusCode.should.equal(200);
        done();
    });
  });

  testApp(api, appHost);
//  testApp(api, { url: "10.0.0.3", port: 80 })
//  api = new AppAPI({ url: "10.1.24.7", port: 80})
});

describe("Deployment", function() {
  it("should have created deploy_output.json", function(done) {
    fs.readFile(deploy_output_file, 'utf8', function (err, data) {
      if (err) {
        console.log('Error: ' + err);
        return;
      }

      data = JSON.parse(data);

      data.forEach(function(vm) {
        var vmType = vm.description.substring(0, vm.description.indexOf(' '));
//        console.log("IP : ", vm.output_value, ", Type : ", vmType);
      });
      done();
    });
  });

  it.skip("should be able to access every ip from deploy_output.json", function(done) {
    fs.readFile(deploy_output_file, 'utf8', function (err, data) {
      if (err) {
        console.log('Error: ' + err);
        return;
      }

      data = JSON.parse(data);

      data.forEach(function(vm) {
        var options = {};
        options.host = vm.output_value;
        http.get(options, function(response) {
          console.log("IP : ", vm.output_value);
          response.statusCode.should.equal(200);
//          done();
        });
      });
      done();
    });
  });
});
