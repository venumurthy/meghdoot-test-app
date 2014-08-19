var http = require('http');

var AppAPI = function(appHost) {
  var self = this;

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

  var getDbs = function(callback) {
    var options = {};
    options.host = appHost.url;
    options.path = "/mongo-api/dbs";
    options.method = 'GET';
    options.port = appHost.port;
    request(options, function(err, response) {
      var dbs = JSON.parse(response.body);
      callback(err, dbs);
    });
  };

  var createDb = function(name, callback) {
    var options = {};
    options.host = appHost.url;
    options.path = "/mongo-api/dbs";
    options.method = 'POST';
    options.port = appHost.port;

    var db = {
      name: name
    };

    var postData = JSON.stringify(db);

    request(options, postData, function(err, response) {
      getDbs(callback);
    });
  };

  var deleteDb = function(name, callback) {
    var db = {
      name: name
    };

    var options = {};
    options.host = appHost.url;
    options.path = "/mongo-api/dbs?name=" + db.name;
    options.method = 'DELETE';
    options.port = appHost.port;

    request(options, function(err, response) {
      getDbs(callback);
    });
  };

  self.request = request;
  self.setHost = setHost;
  self.getDbs = getDbs;
  self.createDb = createDb;
  self.deleteDb = deleteDb;
  self.host = appHost;
}

module.exports = AppAPI;