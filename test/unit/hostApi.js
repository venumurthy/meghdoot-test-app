var should = require('should');
var request = require('supertest');
var app = require('../../app');

describe("Host API Endpoint", function() {
  it("should return localhost by default", function(done) {
    var expected = JSON.stringify({"url": "localhost"});
    request(app).get('/mongo-api/host').expect(expected, done);
  });
  it("should set a new host", function(done) {
    var expected = JSON.stringify({"url": "192.168.33.1"});
    request(app).post('/mongo-api/host').send({url: "192.168.33.1"}).expect(expected, done);
  });
});
