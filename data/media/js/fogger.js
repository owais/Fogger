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
  desktopWindow: {
    active: true,
  },
  quicklist: null
};


fogger.injectCSS = function(css_string) {
  var waitForHeadAndInject = function() {
    if(document.head === null) {
      setTimeout(waitForHeadAndInject, 1000);
      return;
    } else {
      var style_id = '__foggerInjectedStyleSheet';
      var style = document.getElementById(style_id);
      if (style === null) {
        style = document.createElement('style');
        style.setAttribute('id', style_id);
      }
      style.innerHTML = css_string;
      style.setAttribute('type', 'text/css');
      document.head.appendChild(style);
    }
  };
  waitForHeadAndInject();
}

// Events
fogger.events.readyEvent = document.createEvent('Event');
fogger.events.readyEvent.initEvent('foggerReady', true, true);

document.addEventListener('foggerMenuCallbackEvent', function(e) {
  var menu = fogger.menus[e.foggerData.menu];
  var item = menu.items[e.foggerData.name];
  if (item.callback !== undefined) {
    item.callback(menu, item);
  };
});

document.addEventListener('foggerQLCallbackEvent', function(e) {
  var item = fogger.quicklist.items[e.foggerData.name];
  if (item.callback !== undefined) {
    item.callback(item);
  };
});

document.addEventListener('foggerWindowStateChange', function(e){
  fogger.desktopWindow.active = e.foggerData.active;
});


var QuicklistItem = function(name, callback) {
  this.name = name;
  this.callback = callback;
}

var Quicklist = function() {
  this.items = {};
  this._dispatch = dispatch;
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
    this._dispatch('add_quicklist_item///' + conf.name)
    return this;
  }
}

Quicklist.prototype.removeItem = function(conf) {
  if (!conf.name) {
    console.error('Conf must contain "name"');
    return;
  }
  this._dispatch('remove_quicklist_item///' + conf.name);
  delete(this.items[conf.name]);
}


var MenuItem = function(name, callback) {
  this.name = name;
  this.callback = callback;
}

var Menu = function(name) {
  this.name = name;
  this.items = {};
  this._dispatch = dispatch;
  this._dispatch('add_menu///' + this.name)
  fogger.menus[name] = this;
};

Menu.prototype.remove = function() {
  this._dispatch('remove_menu///' + this.name);
  delete(fogger.menus[this.name]);
}

Menu.prototype.addItem = function(conf) {
  if (!conf.name) {
    console.error('Conf must contain "name" and "callback"');
    return;
  }
  if (Boolean(this.items[conf.name])) {
    this.items[conf.name].callback = conf.callback;
    return this.items[conf.name];
  } else {
    var item = new MenuItem(conf.name, conf.callback);
    this.items[conf.name] = item;
    this._dispatch('add_menu_item///' + this.name + '///' + conf.name)
    return item;
  }
};

Menu.prototype.removeItem = function(conf) {
  if (!conf.name) {
    console.error('Conf must contain "name"');
    return;
  }
  this._dispatch('remove_menu_item///' + this.name + '///' + conf.name);
  delete(this.items[conf.name]);
}


/* Desktop */
var Desktop = function() {
  this.__version__  = 12.07;
  this._dispatch = dispatch;
};

Desktop.prototype.setProgress = function(progress) {
  this._dispatch('set_progress///' + progress);
}

Desktop.prototype.setProgressVisible = function(visible) {
  var action = 'set_progress_' + (visible == true ? 'visible': 'invisible');
  this._dispatch(action);
}

Desktop.prototype.setCount = function(count) {
  this._dispatch('set_count///' + count);
}

Desktop.prototype.setCountVisible = function(visible) {
  var action = 'set_count_' + (visible == true ? 'visible': 'invisible');
  this._dispatch(action);
}

Desktop.prototype.notify = function(summary, body) {
  this._dispatch('notify///' + summary + '///' + body);
}

Desktop.prototype.setUrgent = function(urgent) {
  var action = urgent == true ? 'set_urgent': 'unset_urgent';
  this._dispatch(action);
}

Desktop.prototype.newMenu = function(name) {
  return fogger.menus[name] || new Menu(name);
}

Desktop.prototype.quicklist = new Quicklist();

fogger.Desktop = Desktop;
fogger.Fogger = Desktop; // TODO: Remove this once all scripts move to fogger.Desktop;
fogger.Menu = Menu;
fogger.MenuItem = MenuItem;
fogger.Quicklist = Quicklist;
fogger.QuicklistItem = QuicklistItem;
window.fogger = fogger;

document.dispatchEvent(fogger.events.readyEvent);


/* Experimental WebKit notifications support */
var webkitNotifications = function() {};

webkitNotifications.Notification = function(icon, title, content) {
    this.icon = icon;
    this.title = title;
    this.content = content;
};

webkitNotifications.Notification.prototype.show = function() {
  new Desktop().notify(this.title, this.content);
};

webkitNotifications.checkPermission = function() {
  return 0;
};

webkitNotifications.requestPermission = function() {};

webkitNotifications.createNotification = function(icon, title, content) {
  return new webkitNotifications.Notification(icon, title, content);
};

webkitNotifications.createHTMLNotification = function(content) {
  return new webkitNotifications.Notification('', '', content);
};

window.webkitNotifications = webkitNotifications;


})();
