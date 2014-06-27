(function () {
  var app = angular.module('meghdoot');

  app.factory('MongoService', ['$resource', function ($resource) {
    return {
      databases: $resource('/mongo-api/dbs'),
      host: $resource('/mongo-api/host', {}, { query: {method: 'GET', isArray: false}})
    };
  }]);

})();