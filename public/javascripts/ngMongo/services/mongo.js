(function () {
  var app = angular.module('ngMongo');

  var Mongo = function ($resource) {
    return {
      databases: $resource('/mongo-api/dbs')
    };
  };

  app.factory('Mongo', ['$resource', Mongo]);
  
  var Host = function($resource) {
    return $resource('/mongo-api/host', {}, { query: {method: 'GET', isArray: false}});
  };
  
  app.factory('Host', ['$resource', Host]);
})();
