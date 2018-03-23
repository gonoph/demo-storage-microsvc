(function() {
  'use strict';

  angular.module('demoApp')
    .component('podItemView', {
      require: {
        model: 'ngModel',
        plc: '^podListView',
        // readService: '^^readService'
      },
      templateUrl: '/static/views/pod-item-view.html',
      controller: ['$scope', '$interval', '$http', 'readService', 'writeService', PodItemController],
      bindings: {
        name: '<'
      },
  });
  function PodItemController($scope, $interval, $http, readService, writeService) {
    var vm = this;

    vm.pod = undefined;
    vm.is_open = false;
    vm.btnChange = btnChange;
    vm.getModelList = getModelList;
    vm.onTruncate = onTruncate;
    vm.stateToType = stateToType;
    vm.stateToClass = stateToClass;
    Object.defineProperty(vm, 'open', {
      get: get_open,
      set: set_open
    });
    vm.reader = readService.create(vm, $scope, read_callback);
    vm.writer = writeService.create(vm, write_callback);

    vm.read_data = undefined;
    vm.read_pos = 0;

    vm.read_now = {
      timer: 0,
      items: 0,
      errors: 0,
    };
    vm.read_sum = {
      items: 0,
      errors: 0,
    };

    vm.write_promise = undefined;
    vm.write_data = undefined;
    vm.read_sse = undefined;
    vm.write_now = {
      timer: 0,
      items: 0,
      bytes: 0,
    };
    vm.write_sum = {
      items: 0,
      bytes: 0,
    };

    vm.readStarted = false;
    vm.writeStarted = false;
    vm.btnModel = {
      'Read': [false, 'btn-success', vm.reader.start, vm.reader.stop],
      'Write': [false, 'btn-warning', vm.writer.start, vm.writer.stop]
    };
    vm.infoStatus = {
      title: undefined,
      "href":"",
      "iconClass": "pficon pficon-server",
      "info":[
        '0.0.0.0',
        'state: unknown',
        'phase: unknown',
      ]
    };

    vm.$onInit = function() {
      console.log({caller: 'vm.$onInit', pod: vm.pod, name: vm.name});
      vm.plc.addPodItemTruncateListeners(vm.onTruncate);
    };

    vm.$postLink = function() {
      console.log({caller: 'vm.$postLink', pod: vm.model.$modelValue});
      vm.model.$render = function() {
        vm.pod = vm.model.$modelValue;
        console.log({caller: 'vm.$postLink.$render', m: vm.model.$modelValue, v: vm.model.$viewValue });
        if (vm.pod == undefined) {
          return;
        }
        var info = [
          vm.pod.ip_address || '0.0.0.0',
          'state: ' + vm.pod.state,
          'phase: ' + vm.pod.phase
        ];
        vm.infoStatus.title = vm.pod.pod_name;
        vm.infoStatus.info = info;
      };
    };

    vm.$onDestroy = function() {
      console.log({caller: 'vm.$onDestroy', pod: vm.pod, name: vm.name});
      vm.reader.stop();
      vm.writer.stop();
      vm.plc.removePodItemTruncateListeners(vm.onTruncate);
    };

    function stateToType() {
      var state = vm.pod == undefined ? 'Creating' : vm.pod.state;
      return typeMap[state];
    };

    function stateToClass() {
      var state = vm.pod == undefined ? 'Creating' : vm.pod.state;
      return classMap[state];
    };

    function btnChange(mode) {
      console.log({name: vm.pod.pod_name, rw: mode});
      if (vm.btnModel[mode][0]) {
        vm.btnModel[mode][2]();
      } else {
        vm.btnModel[mode][3]();
      }
    };

    function get_open() {
      return vm.plc.openData[vm.name];
    }

    function set_open(flag) {
      vm.plc.openData[vm.name] = flag;
    }

    function getModelList() {
        return Object.keys(vm.btnModel).sort();
    }

    function read_callback(j) {
      vm.read_pos = j.reads.pos;
      vm.read_data = j;
      vm.read_now = {
        timer: j.timer,
        items: j.reads.records.num,
        errors: (j.reads.fails.num || 0) + (j.reads.errors.num || 0)
      };
      vm.read_sum.items += vm.read_now.items;
      vm.read_sum.errors += vm.read_now.errors;
    };

    function write_callback(rd) {
      vm.write_data = rd;
      var items = undefined;
      var bytes = undefined;
      if ('remote' in rd) {
        items = rd.remote.body.writes.entries;
        bytes = rd.remote.body.writes.bytes;
      } else {
        items = rd.writes.entries;
        bytes = rd.writes.bytes;
      }
      vm.write_now = {
        timer: rd.timer,
        items: items,
        bytes: bytes,
      };
      vm.write_sum.items += vm.write_now.items;
      vm.write_sum.bytes += vm.write_now.bytes / 1024;
    }

    function onTruncate() {
      console.log({pod: vm.pod.pod_name, called: 'truncate'});
      vm.write_now.timer = vm.write_now.items = vm.write_now.bytes = 0;
      vm.read_now.timer = vm.read_now.items = vm.read_now.errors = 0;
      vm.read_pos = 0;
      vm.write_sum.items = vm.write_sum.bytes = 0;
      vm.read_sum.items = vm.read_sum.errors = 0;
    }
  }

  var typeMap = {
    'Crashing': 'warning',
    'Terminating': 'danger',
    'Creating': 'info',
    'Running': 'success',
  };

  var classMap = {
    'Crashing': 'progress-striped active',
    'Terminating': 'progress-striped active',
    'Creating': 'progress-striped active',
    'Running': 'progress',
  }

})();
