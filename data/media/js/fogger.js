(function() {

var dispatch = function(data) {
  var params = [];
  for (key in data) {
    if (data.hasOwnProperty(key)) {
      params.push(escape(key) + '=' + escape(data[key]));
    }
  }
  var string = params.join('&');
  console.log(string)
  var uri = 'http://fogger.local/?' + string;
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

// Quicklists
var QuicklistItem = function(name, callback) {
  this.type = 'quicklist';
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
    this._dispatch({
      'action': 'add_quicklist_item',
      'name': conf.name,
    });
    return this;
  }
}

Quicklist.prototype.removeItem = function(conf) {
  if (!conf.name) {
    console.error('Conf must contain "name"');
    return;
  }
  var data = {
    'action': 'remove_quicklist_item',
    'name': conf.name
  }
  this._dispatch(data);
  delete(this.items[conf.name]);
};


var MenuItem = function(name, callback) {
  this.name = name;
  this.callback = callback;
}

var Menu = function(name) {
  this.name = name;
  this.items = {};
  this._dispatch = dispatch;
  this._dispatch({
      'action': 'add_menu',
      'name': this.name,
  });
  fogger.menus[name] = this;
};

Menu.prototype.remove = function() {
  this._dispatch({
    'action': 'remove_menu',
    'name': this.name,
  });
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
    this._dispatch({
      'action': 'add_menu_item',
      'menu_name': this.name,
      'item_name': conf.name,
      'type': conf.type === undefined ? 'GtkMenuItem' : conf.type,
    });
    return item;
  }
};

Menu.prototype.removeItem = function(conf) {
  if (!conf.name) {
    console.error('Conf must contain "name"');
    return;
  }
  this._dispatch({
    'action': 'remove_menu_item',
    'menu_name': this.name,
    'item_name': conf.name
  });
  delete(this.items[conf.name]);
};


/* Desktop */
var Desktop = function() {
  this.__version__  = 12.07;
  this._dispatch = dispatch;
};

Desktop.prototype.setProgress = function(progress) {
  this._dispatch({
    'action': 'set_progress',
    'progress': progress
    });
};

Desktop.prototype.setProgressVisible = function(visible) {
  this._dispatch({
    'action': 'set_progress_visible',
    'visible': visible,
  });
};

Desktop.prototype.setCount = function(count) {
  var data = {
    'action': 'set_count',
    'count': count,
  }
  this._dispatch(data);
};

Desktop.prototype.setCountVisible = function(visible) {
  this._dispatch({
    'action': 'set_count_visible',
    'visible': visible,
  });
}

Desktop.prototype.notify = function(summary, body) {
  this._dispatch({
    'action': 'notify',
    'summary': summary,
    'body': body
  });
}

Desktop.prototype.setUrgent = function(urgent) {
  this._dispatch({
    'action': urgent == true ? 'set_urgent': 'unset_urgent',
  });
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
