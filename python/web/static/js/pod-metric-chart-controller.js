(function() {
  'use strict';

angular.module('demoApp')
  .component('podMetricChart', {
        require: {
          model: 'ngModel'
        },
        templateUrl: '/static/views/metric-chart-view.html',
        controller: ChartController,
        bindings: {
          chartId: '@',
          headerTitle: '@',
          title: '@',
          units: '@',
          minutes: '@',
          name: '@',
          started: '<',
        },
    }
);

function ChartController($scope, $interval) {
      var vm = this;
      vm.minutes = 2;
      vm.max_items = vm.minutes * 60;
      vm.addDataPoint = addDataPoint;
      vm.promise = undefined;
      vm.start = startfn;
      vm.stop = stopfn;
      vm.$onDestroy = onDestroy;

      vm.$postLink = function() {
        vm.model.$render = function() {
          var m = vm.model.$modelValue;
          var v = vm.model.$viewValue;
          console.log({name: vm.config.chartId, $renderModel: m, $renderView: v});
          addDataPoint(vm.model.$modelValue);
        };
      };

      vm.$onInit = function() {
        vm.minutes = isNaN(vm.minutes) ? 2 :
          vm.minutes < (15/60) ? (15/60) :
            vm.minutes;
        vm.max_items = vm.minutes * 60;

        var today = new Date();
        var xData = ['secs ago'];
        var yData = [vm.units];

        vm.config = {
          'chartId'      : [vm.chartId, vm.name].join('-'),
          'title'        : vm.title,
          'layout'       : 'small',
          'valueType'    : 'actual',
          'units'        : vm.units,
          'tooltipType'  : 'actual',
          'compactLabelPosition'  : 'left',
          'timeFrame'    : timeFrameLabel(),
          'tooltipType'  : 'value',
        };

        vm.data = {
          // 'total': '250',
          'xData': xData,
          'yData': yData,
          get dataAvailable() {
            return xData.length > 2 && yData.length > 2;
          }
        };

        console.log({name: vm.config.chartId, maxItems: vm.max_items, data: vm.data});

      }

      function timeFrameLabel() {
        var num = vm.minutes;
        var unit = 'Min';
        if (num < 1) {
          num *= 60;
          unit = 'Sec';
        }
        if (num > 1) {
          unit += 's';
        }
        return ['Last ', num, ' ', unit].join('');
      };

      function appendData(yData) {
        var xData = new Date().getTime();
        var x = vm.data.xData;
        var y = vm.data.yData;
        // console.log(x.length);
        if (x.length >= vm.max_items-1) {
          for (let i = 1 ; i < x.length -1 ; i++) {
            x[i] = x[i+1];
            y[i] = y[i+1];
          }
          x[x.length-1]=xData;
          y[y.length-1]=yData;
        } else {
          x.push(xData);
          y.push(yData);
        }

      }

      function startfn() {
        if (vm.promise == undefined) {
          vm.promise = $interval(intervalCallback, 1000);
        } else {
          console.log("Was asked to start intervalCallback again.")
        }
      }

      function stopfn() {
        if (vm.promise != undefined) {
          console.log('stopping ' + vm.config.chartId + ' data binding timer');
          $interval.cancel(vm.promise);
        }
      }

      function intervalCallback() {
        vm.addDataPoint(vm.model);
      }

      function addDataPoint(num) {
        num = isNaN(num) ? 0 :
          num < 0 ? Math.random() * 1000 :
            num;
        appendData(Math.round(num));
      };

      function onDestroy() {
        stopfn();
      }
  };

})();
