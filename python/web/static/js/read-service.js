(function() {
  'use strict';

  angular.module('demoApp')
  .service('readService', ['appSettings', ReadService]);

  function ReadService(appSettings) {
    var svc = this;
    svc.create = create;

    function create(vm, $scope, callback) {
      var fn = {
        scope: $scope,
        start: start,
        stop: stop,
        readStarted: false,
        callback: callback
      };

      return fn;

      function stop() {
        console.log({stop_read: vm.pod});
        if (typeof fn.sse != 'undefined') {
          fn.sse.close();
          fn.sse = undefined;
        }
        fn.readStarted = false;
      };

      function start() {
        fn.sse = new EventSource(appSettings.template('reader.read', vm.read_pos));
        fn.sse.addEventListener('message', message_listener, false);
        fn.sse.addEventListener('timeout', timeout_listener, false);
        fn.readStarted = true;
      };

      function timeout_listener(e) {
        console.log({sse_timeout: e, data: e.data});
        fn.stop();
        fn.start();
      };

      function message_listener(e) {
        console.log({listener: fn});
        var j = JSON.parse(e.data);
        console.log({sse_read: j});
        fn.scope.$apply(function() {
          fn.callback(j);
        })
        if (typeof fn.sse == 'undefined') {
          fn.stop();
        }
      }

    }
  }
})();
