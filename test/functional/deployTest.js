var should = require('should');
var app = require('../../app');
var http = require('http');
var fs = require('fs');

var appHost = {
  url: "localhost",
  port: 3000
};
var deploy_output_file = 'bin/deploy_output.json';

var request = function(options, postData, callback) {
  var postBody;
  if (arguments.length === 2) {
    callback = postData;
    postData = false;
  }
  else {
    options.headers = {
        'Content-Type': 'application/json',
        'Content-Length': postData.length
    };
  }
  var req = http.request(options, function(response) {
    var body = "";
    response.on('data', function(data) {
      body += data;
    });
    response.on('end', function() {
      response.body = body
      callback(null, response);
    });
  });

  req.on('error', function(e) {
    console.log('problem with req: ' + e.message);
  });
  if (postData) {
    req.write(postData);
  }
  req.end();
}

var setHost = function (host, callback) {
  var options = {};
  options.host = appHost.url;
  options.path = "/mongo-api/host";
  options.method = 'POST';
  options.port = appHost.port;
  var postBody = {
    "url": host.url
  };
  var postData = JSON.stringify(postBody);
  options.headers = {
      'Content-Type': 'application/json',
      'Content-Length': postData.length
  };
  request(options, postData, function() {
    callback();
  })
};


var getDbs = function(host, callback) {
    var options = {};
    options.host = host.url;
    options.path = "/mongo-api/dbs";
    options.method = 'GET';
    options.port = host.port;
    request(options, function(err, response) {
      var dbs = JSON.parse(response.body);
      callback(err, dbs);
    });
};

var dbExists = function(dbs, name) {
  Array.isArray(dbs).should.be.ok;
  return dbs.reduce(function(prev, curr) {
    return prev || (curr.name === name)
  }, false);
};

  var createdDbs = [];

var createDb = function(host, name, callback) {
  var options = {};
  options.host = host.url;
  options.path = "/mongo-api/dbs";
  options.method = 'POST';
  options.port = host.port;

  var db = {
    name: name
  };

  var postData = JSON.stringify(db);

  request(options, postData, function(err, response) {
    getDbs(host, callback);
  });
};

var deleteDb = function(host, name, callback) {

  var db = {
    name: name
  };

  var options = {};
  options.host = appHost.url;
  options.path = "/mongo-api/dbs?name=" + db.name;
  options.method = 'DELETE';
  options.port = appHost.port;

  request(options, function(err, response) {
    getDbs(host, callback);
  });
};

describe("Meghdoot Test App", function() {
  before(function(done) {
    setHost(appHost, done);
  })
  afterEach(function(done) {
    setHost(appHost, done);
  });

  it("should be accessible", function(done) {
      var options = {};
      options.host = "10.1.24.7";
      http.get(options, function(response) {
        response.statusCode.should.equal(200);
        done();
    });
  });
  describe("/host", function() {
    it("GET should have a default host of 'localhost'", function(done) {
      var options = {};
      options.host = appHost.url;
      options.path = "/mongo-api/host";
      options.method = 'GET';
      options.port = appHost.port;
      request(options, function(err, response) {
        var host = JSON.parse(response.body);
        host.url.should.equal("localhost");
        done();
      });
    });

    it("POST should change the host to a different url", function(done) {
      var newHostUrl = "10.1.24.7";

      var options = {};
      options.host = appHost.url;
      options.path = "/mongo-api/host";
      options.method = 'POST';
      options.port = appHost.port;
      var postBody = {
        "url": newHostUrl
      };
      var postData = JSON.stringify(postBody);
      options.headers = {
          'Content-Type': 'application/json',
          'Content-Length': postData.length
      };
      request(options, postData, function(error, response) {
        var host = JSON.parse(response.body);
          host.url.should.equal(newHostUrl);
          done();
      });
    });
  });

  describe("/dbs", function() {
    afterEach(function(done) {
      var host = appHost;
      var loop = function(index, callback, onComplete) {
        return function() {
          if (index<createdDbs.length) {
            var name = createdDbs[index];
            deleteDb(host, name, callback(index +1, loop, onComplete));
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
      var host = appHost;
      getDbs(host, function(err, dbs) {
        dbExists(dbs, "local").should.be.ok;
        done();
      });
    });

    it("POST should add a new database", function(done) {
      var host = appHost;
      var dbName = "newTestDatabase";

      createDb(host, dbName, function(error, dbs) {
        dbExists(dbs, dbName).should.be.true;
        createdDbs.push(dbName);
        done();
      });
    });

    it("DELETE should delete database", function(done) {
      var host = appHost;
      var dbName = "newTestDatabase";
      createDb(host, dbName, function(error, dbs) {
        deleteDb(host, dbName, function(error, dbs) {
          dbExists(dbs, dbName).should.be.false;
          done();
        });
      });   
    });
  });
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

