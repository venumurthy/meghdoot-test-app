var should = require('should');

describe("Passing Test", function() {
  it("should pass", function() {
    var test = true;
    test.should.be.ok;
  });
  describe("Failing Test", function() {
    it ("should fail", function() {
      var test = false;
      test.should.be.ok;
    });
  });
});
