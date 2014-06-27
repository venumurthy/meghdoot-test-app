(function(){
  var app = angular.module('meghdoot');

  var DatabaseCtrl = function($scope, MongoService){
    var getDatabases = function(){
      return MongoService.databases.query().sort();
    };

    $scope.databases = MongoService.databases.query();

    $scope.host = MongoService.host.query(function(host) {
      $scope.hostUrl = host.url;
      $scope.databases = getDatabases();
    });

    $scope.changeHost = function() {
      var newHost = new MongoService.host({url: $scope.hostUrl});
      newHost.$save(function(u) {
        $scope.databases = getDatabases();
      });
    };

    $scope.addDatabase = function(){
      var databaseName = $scope.newDatabaseName;

      if(!databaseName) return;

      var newDatabase = new MongoService.databases({name: databaseName});
      newDatabase.$save(function(u, resp) {
        //Success
        $scope.databases.push(newDatabase);
      }, function(u) {
        //Error
        alert("Error: could not connect to the database");
      });


      $scope.newDatabaseName = '';
    };

    $scope.removeDatabase = function(database){
      if(!database) return;

      if(confirm(String.format("Are you sure you want to delete the database '{0}'?", database.name))) {
        database.$delete({name: database.name});
        $scope.databases = _.without($scope.databases, database);
      }
    };
  };

  app.controller('DatabaseCtrl', ['$scope', 'MongoService', DatabaseCtrl]);
})();
