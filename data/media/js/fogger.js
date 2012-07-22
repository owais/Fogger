(function() {
  var DesktopProperty = function() {};
  DesktopProperty.prototype._dispatch = function(action) {
    var params = [];
    for (key in action) {
      if (action.hasOwnProperty(key)) {
        params.push(escape(key) + '=' + escape(action[key]));
      }
    }
    var string = params.join('&');
    var uri = 'http://fogger.local/?' + string;
    var h = new XMLHttpRequest();
    h.open('GET', uri,  true);
    h.send();
  };
  var newDesktopPropertySubclass = function(constructor) {
    constructor.prototype = new DesktopProperty();
    constructor.prototype.constructor = constructor;
    return constructor;
  };

  // Notification Interface
  var Notification = newDesktopPropertySubclass(function(){});
  Notification.prototype.showNotification = function(summary, body, iconUrl) {
    // TODO: Add support for iconUrl
    this._dispatch({
      'action': 'notify',
      'summary': summary,
      'body': body
    });
  };

  // Launcher Interface
  var Launcher = newDesktopPropertySubclass(function(){
    this.actions = {};
    var that = this;
    document.addEventListener('foggerQLCallbackEvent', function(e) {
      var action = that.actions[e.foggerData.name];
      if (action !== undefined) {
        action();
      };
    });
  });
  Launcher.prototype.addAction = function(name, callback) {
    this._dispatch({
      action: 'add_launcher_action',
      name: name,
    });
    this.actions[name] = callback;
  };
  Launcher.prototype.removeAction = function(name) {
    this._dispatch({
      action: 'remove_launcher_action',
      name: name,
    });
    delete this.actions[name];
  };
  Launcher.prototype.removeActions = function() {
    this._dispatch({
      action: 'remove_launcher_actions',
    });
    this.actions = {};
  };
  Launcher.prototype.setCount = function(count) {
    this._dispatch({
      'action': 'set_count',
      'count': count,
    });
  };
  Launcher.prototype.clearCount = function() {
    this._dispatch({
      'action': 'clear_count',
    });
  };
  Launcher.prototype.setProgress = function(progress) {
    this._dispatch({
      'action': 'set_progress',
      'progress': progress
    });
  };
  Launcher.prototype.clearProgress = function() {
    this._dispatch({
      'action': 'clear_progress',
    });
  };
  Launcher.prototype.setUrgent = function(urgent) {
    this._dispatch({
      'action': urgent ? 'set_urgent' : 'clear_urgent',
    });
  };


  // Unity Object
  var Unity = newDesktopPropertySubclass(function() {
    this.Notification = new Notification();
    this.Launcher = new Launcher();
    this.actions = {};
    var that = this;
    document.addEventListener('foggerActionCallbackEvent', function(e) {
      var action = that.actions[e.foggerData.name];
      if (action !== undefined) {
        action();
      }
    });
  });
  Unity.prototype.init = function(initParams) {
    var onInit = initParams['onInit'];
    if (onInit !== undefined) {
      onInit();
    };
  };
  Unity.prototype.addAction = function(name, callback) {
    this._dispatch({
      action: 'add_action',
      name: name,
    });
    this.actions[name] = callback;
  };
  Unity.prototype.removeAction = function(name) {
    this._dispatch({
      action: 'remove_action',
      name: name,
    });
    delete this.actions[name];
  };
  Unity.prototype.removeActions = function() {
    this._dispatch({
      action: 'remove_actions',
    });
    this.actions = {};
  };


  window.external = window.external || {};
  window.external.getUnityObject = function(version) {
    return new Unity();
  };
})();
