var should = require('should');
var app = require('../../app');
var http = require('http');

var appHost = {
  url: "localhost",
  port: 3000
};

var request = function(options, postData, callback) {
  var postBody;
  if (arguments.length === 2) {
    callback = postData;
    postData = false;
  }

  else {

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

var resetHost = function(callback) {
  var options = {};
  options.host = appHost.url;
  options.path = "/mongo-api/host";
  options.method = 'POST';
  options.port = appHost.port;
  var postBody = {
    "url": appHost.url
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

describe("Meghdoot Test App", function() {
  before(function(done) {
    resetHost(done);
  })
  afterEach(function(done) {
    resetHost(done);
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
    it("should have a default host of 'localhost'", function(done) {
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

    it("should change the host to a different url", function(done) {
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
});
