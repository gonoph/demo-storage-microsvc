(function() {
  'use strict';

  angular.module('demoApp')
    .component('podListView', {
      templateUrl: '/static/views/pod-list-view.html',
      controller: ['$scope', '$http', 'appSettings', 'podService', PodListController],
    });

  function PodListController($scope, $http, appSettings, podService) {
    var vm = this;
    vm.pod_writers = podService.create('writer.pods', $scope, pod_writer_add_listener, pod_writer_del_listener);
    vm.pod_readers = podService.create('reader.pods', $scope, undefined, undefined);
    vm.pod_web = podService.create('web.pods', $scope, undefined, undefined);
    vm.podData = vm.pod_writers.items;
    vm.podReadData = vm.pod_readers.items;
    vm.podWebData = vm.pod_web.items;
    vm.podData_len = _length(vm.podData);
    vm.podReadData_len = _length(vm.podReadData);
    vm.podWebData_len = _length(vm.podWebData);
    vm.podData_filter = _filterPod(vm.podData);
    vm.podReadData_filter = _filterPod(vm.podReadData);
    vm.podWebData_filter = _filterPod(vm.podWebData);
    vm.openData = {};
    vm.button_click_stop = button_click_stop;
    vm.truncate = truncate;
    vm.checkboxPods = true;
    vm.addPodItemTruncateListeners = addPodItemTruncateListeners;
    vm.removePodItemTruncateListeners = removePodItemTruncateListeners;
    vm.btnRWSettings = {};
    vm.btnDelayFactor = {};

    var podItemTruncateListeners = [];

    function _filterPod(obj) {
      return function(state, negated) {
        let f = Object.keys(obj).filter(o => (obj[o].state == state) == negated);
        // console.log({filter: f});
        return f.length;
      }
    };

    function _length(obj) {
      return function() {
        return Object.keys(obj).length;
      }
    };

    function button_click_stop($event) {
      if($event){
        $event.stopPropagation();
        $event.preventDefault();
      }
    }

    function truncate() {
      $http.get(appSettings.template('writer.truncate')).then(vm.truncate.callback);
    }
    truncate.callback = function(response) {
      console.log('truncated');
      podItemTruncateListeners.forEach(function(fn) { fn(); });
    }
    truncate.selected = false;

    vm.btnRWSettings = {
      writeNum: 10,
      selected: 'MODE_RW',
      opened: false,
      modes: {
        MODE_RW: 'Read Write Mode',
        MODE_RO: 'Read Shared Mode',
        MODE_IG: 'Ignore Mode'
      },
      click: function(selection) {
        vm.btnRWSettings.selected = selection;
        vm.btnRWSettings.opened = !vm.btnRWSettings.opened;
      },
    };

    vm.btnDelayFactor = {
      selected: 0,
      opened: false,
      modes: {
        0: 'None',
        1: 'Low',
        5: 'Medium',
        10: 'Heavy'
      },
      click: function(delay) {
        vm.btnDelayFactor.selected = delay;
        vm.btnDelayFactor.opened = !vm.btnDelayFactor.opened;
      }
    };

    vm.btnWriteEntries = {
      selected: 8,
      opened: false,
      modes: {
        8: 8,
        16: 16,
        32: 32,
        64: 64,
        128: 128,
        256: 256,
        // 512: 512,
        // 1024: 1024,
      },
      click: function(entries) {
        vm.btnWriteEntries.selected = entries;
        vm.btnWriteEntries.opened = !vm.btnWriteEntries.opened;
      }
    };

    function addPodItemTruncateListeners(fn) {
      podItemTruncateListeners.push(fn);
    }

    function removePodItemTruncateListeners(fn) {
      // console.log('removing ' + fn);
      var removed = podItemTruncateListeners.splice(0, podItemTruncateListeners.indexOf(fn)+1);
      console.log({removed: removed});
    }

    function pod_writer_add_listener(j) {
      let name = j.pod_name;
      if (!(name in vm.openData)) {
        vm.openData[name] = false;
      }
    };

    function pod_writer_del_listener(j) {
      delete vm.openData[j.pod_name];
    };

  }
})();
