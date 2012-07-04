(function() {

var dispatch = function(action) {
  var uri = 'http://fogger.local/' + action
  var h = new XMLHttpRequest();
  h.open('GET', uri,  true);
  h.send();
};

// Base model

var fogger = {
  events: {},
  callbackStore: {},
  menus: {},
  indicators: {},
  quicklist: null
};

// Events
fogger.events.readyEvent = document.createEvent('Event');
fogger.events.readyEvent.initEvent('foggerReady', true, true);

document.addEventListener('foggerMenuCallbackEvent', function(e) {
  var menu = fogger.menus[e.foggerData.menu];
  var item = menu.items[e.foggerData.name];
  var callback = item['callback'];
  if (callback) {
    callback(menu, item);
  };
});

document.addEventListener('foggerQLCallbackEvent', function(e) {
  var item = fogger.quicklist.items[e.foggerData.name];
  var callback = item['callback'];
  if (callback) {
    callback(item);
  };
});

/*
window.webkitNotifications = function() {};

window.webkitNotifications.Notification = function(icon, title, content) {
    this.icon = icon;
    this.title = title;
    this.content = content;
};

window.webkitNotifications.Notification.prototype.show = function() {
  new Fogger().notify(this.title, this.content);
};

window.webkitNotifications.checkPermission = function() {
  return 0;
};

window.webkitNotifications.requestPermission = function() {};

window.webkitNotifications.createNotification = function(icon, title, content) {
  return new webkitNotifications.Notification(icon, title, content);
};

window.webkitNotifications.createHTMLNotification = function(content) {
  return new webkitNotifications.Notification('', '', content);
};
*/

var QuicklistItem = function(name, callback) {
  this.name = name;
  this.callback = callback;
}

var Quicklist = function() {
  this.items = {};
  this._dispatch = dispatch;
  this._dispatch('add_quicklist')
  fogger.quicklist = this;
}

Quicklist.prototype.addItem = function(conf) {
  if (!conf.name) {
    console.error('Conf must contain "name" and "callback"');
    return;
  }
  if (this.items[conf.name]) {
    this.items[conf.name].callback = conf.callback;
    return this.items[conf.name];
  } else {
    var item = new QuicklistItem(conf.name, conf.callback);
    this.items[conf.name] = item;
    this._dispatch('add_quicklist_item/' + conf.name)
    return this;
  }
}


var MenuItem = function(name, callback) {
  this.name = name;
  this.callback = callback;
}

var Menu = function(name) {
  this.name = name;
  this.items = {};
  this._dispatch = dispatch;
  this._dispatch('add_menu/' + this.name)
  fogger.menus[name] = this;
};

Menu.prototype.addItem = function(conf) {
  if (!conf.name) {
    console.error('Conf must contain "name" and "callback"');
    return;
  }
  if (this.items[conf.name]) {
    this.items[conf.name].callback = conf.callback;
    return this.items[conf.name];
  } else {
    var item = new MenuItem(conf.name, conf.callback);
    this.items[conf.name] = item;
    this._dispatch('add_menu_item/' + this.name + '/' + conf.name)
    return item;
  }
};


var Fogger = function() {
  this.__version__  = 12.07;
  this._dispatch = dispatch;
};

Fogger.prototype.setProgress = function(progress) {
  this._dispatch('set_progress/' + progress);
}

Fogger.prototype.setProgressVisible = function(visible) {
  var action = 'set_progress_' + (visible == true ? 'visible': 'invisible');
  this._dispatch(action);
}

Fogger.prototype.setCount = function(count) {
  this._dispatch('set_count/' + count);
}

Fogger.prototype.setCountVisible = function(visible) {
  var action = 'set_count_' + (visible == true ? 'visible': 'invisible');
  this._dispatch(action);
}

Fogger.prototype.notify = function(summary, body) {
  this._dispatch('notify/' + summary + '/' + body);
}

Fogger.prototype.setUrgent = function(urgent) {
  var action = urgent == true ? 'set_urgent': 'unset_urgent';
  this._dispatch(action);
}

Fogger.prototype.new_menu = function(name) {
  return fogger.menus[name] || new Menu(name);
}

Fogger.prototype.quicklist = new Quicklist();

fogger.Fogger = Fogger;
window.fogger = fogger;

document.dispatchEvent(fogger.events.readyEvent);

})();
