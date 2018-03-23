(function() {
  'use strict';

  angular.module('demoApp')
    .service('appSettings', AppSettings);

    function AppSettings() {
      var svc = this;
      svc.template = template;

      function template(item, v) {
        var t = undefined;
        var _ = undefined;
        eval(`t = svc.${item}`);
        eval(`_ = \`${t}\``);
        console.log({ret: _});
        return _;
      };
      svc.writer = {
        pods: "/api/writer/stream/pods/",
        truncate: "/api/writer/truncate",
        write: "/api/writer/${v.suffix}",
        suffix: "write/${v.entries}/${v.rw}/${v.delay}",
        remote: "/api/writer/pods/${v.name}/${v.suffix}",
      };
      svc.reader = {
        pods: "/api/reader/stream/pods/",
        read: "/api/reader/stream/read/${v}",
      };
      svc.web = {
        pods: "/api/web/stream/pods/",
      }
    };

})();
