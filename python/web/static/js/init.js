// Ensure jinja2 templates don't strip out angular placeholders
demoApp = angular.module('demoApp',
  ['patternfly.charts', 'patternfly.card', 'ngSanitize', 'ngAnimate', 'ui.bootstrap'] )
  .config(['$interpolateProvider', function($interpolateProvider) {
    $interpolateProvider.startSymbol('{[');
    $interpolateProvider.endSymbol(']}');
}]);
