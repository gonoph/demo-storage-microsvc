(function() {
  'use strict';

  angular.module('demoApp')
  .service('podService', ['appSettings', PodService]);

  function PodService(appSettings) {
    var svc = this;
    svc.create = create;

    function create(type, $scope, mod_callback, del_callback) {
      var fn = {
        scope: $scope,
        stop: stop,
        mod_callback: mod_callback || dummy_cb,
        del_callback: del_callback || dummy_cb,
        items: {},
        old_items: {},
      };

      start(type);
      return fn;

      function dummy_cb(j) {
        console.log({cb: 'dummy', i: j});
      }

      function stop() {
        console.log({stop_read: vm.pod});
        if (typeof fn.sse != 'undefined') {
          fn.sse.close();
          fn.sse = undefined;
          fn.items = fn.old_items = {};
        }
      };

      function start(type) {
        let url = appSettings.template(type);
        fn.sse = new EventSource(url);
        fn.sse.addEventListener('added', add_listener, false);
        fn.sse.addEventListener('modified', add_listener, false);
        fn.sse.addEventListener('deleted', del_listener, false);
        fn.sse.onopen = open_listener;
        // fn.sse.onerror = error_listener;
      };

      function _len(obj) {
        return Object.keys(obj).length;
      }

      function add_listener(e) {
        let j = JSON.parse(e.data);
        j = j.object;
        fn.scope.$apply(function() {
          fn.items[j.pod_name] = j;
          fn.mod_callback(j);
        });
      };

      function del_listener(e) {
        let j = JSON.parse(e.data);
        j = j.object;
        fn.scope.$apply(function() {
          fn.del_callback(j);
          delete fn.items[j.pod_name];
        });
      };

      function reconcile() {
        console.log('Running reconcile');
        if (_len(fn.old_items) > 0) {
          for (let k of Object.keys(fn.old_items)) {
            if (!(k in fn.items)) {
              let j = fn.old_items[k];
              console.log({reconsole: 'removing missing item', item: j});
              fn.scope.$apply(function() {
                fn.del_callback(j);
                delete fn.items[k];
              })
            }
          }
          fn.old_items = [];
        }
      }

      // if it's disconnected, then save the last items so
      // we can reconcile the differences
      function open_listener(e) {
        console.log({open: 'open', e: e});
        if (Object.keys(fn.items).length > 0) {
          fn.old_items = fn.items;
          // reconcile pods in 2 seconds.
          setTimeout(reconcile, 1000);
        }
      }

    }
  }
})();
