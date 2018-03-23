(function() {
  'use strict';

  angular.module('demoApp')
  .service('writeService', ['$interval', '$http', 'appSettings', WriteService]);

  function WriteService($interval, $http, appSettings) {
    var svc = this;
    svc.create = create;

    function create(vm, write_callback) {
      var fn = {
        start: start,
        stop: stop,
        promise: undefined,
        writeStarted: false,
        callback: write_callback
      };

      return fn;

      function stop() {
        console.log({stop_write: vm.pod});
        if (typeof fn.promise != 'undefined') {
          $interval.cancel(fn.promise);
          fn.promise = undefined;
          fn.writeStarted = false;
        };
      }

      function start() {
        fn.promise = $interval(intervalfn, 1000, 1);
        fn.writeStarted = true;
      }

      function intervalfn() {
        if (typeof fn.promise != 'undefined') {
          var v = {
            name: vm.pod.pod_name,
            entries: vm.plc.btnWriteEntries.selected,
            rw: vm.plc.btnRWSettings.selected,
            delay: vm.plc.btnDelayFactor.selected,
          };
          v.suffix = appSettings.template('writer.suffix', v);
          var url = vm.plc.checkboxPods
            ? appSettings.template('writer.remote', v)
            : appSettings.template('writer.write', v);
          console.log({intervalfn: url, checkbox: vm.plc.checkboxPods});
          $http.get(url).then(callback)
        }
      }

      function callback(response) {
        console.log({write_callback: response});
        var rd = response.data;
        fn.callback(rd);

        if (vm.btnModel['Write'][0]) {
          fn.start();
          // setTimeout(function() {fn.start()}, 1000);
        } else {
          fn.stop();
        }
      }
    }
  }
})();
