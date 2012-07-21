(function() {

// utils
var randoms = [];
function randomString(length) {
  var length = length || 10;
  var chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXTZabcdefghiklmnopqrstuvwxyz'.split('');
  if (!length) {
    length = Math.floor(Math.random() * chars.length);
  }
  var str = '';
  for (var i = 0; i < length; i++) {
    str += chars[Math.floor(Math.random() * chars.length)];
  }
  if (randoms.indexOf(str) != -1) {
    randomString(length);
  } else {
    return str;
  }
}

var dispatch = function(data) {
  var params = [];
  for (key in data) {
    if (data.hasOwnProperty(key)) {
      params.push(escape(key) + '=' + escape(data[key]));
    }
  }
  var string = params.join('&');
  var uri = 'http://fogger.local/?' + string;
  var h = new XMLHttpRequest();
  h.open('GET', uri,  true);
  h.send();
};


// Base GtkWidget
var GtkWidget = function() {
  this._id = randomString();
  fogger._widgets[this._id] = this;
  this._dispatch = dispatch;
};

GtkWidget.prototype.rename = function(name) {
  this.name = name;
  this._dispatch({
    'action': 'rename_item',
    'name': this.name,
    'id': this._id,
  });
};


// Base model
var fogger = {
  _widgets: {},
  events: {},
  menus: {},
  indicators: {},
  desktopWindow: {
    active: true,
  },
  quicklist: null
};


// Events
fogger.events.readyEvent = document.createEvent('Event');
fogger.events.readyEvent.initEvent('foggerReady', true, true);

document.addEventListener('foggerMenuCallbackEvent', function(e) {
  var menu = fogger._widgets[e.foggerData.menu_id];
  var item = fogger._widgets[e.foggerData.item_id];
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
var QuicklistItem = function(quicklist, name, callback) {
  GtkWidget.call(this);
  this.type = 'quicklist';
  this.quicklist = quicklist;
  this.name = name;
  this.callback = callback;
};
QuicklistItem.prototype = new GtkWidget();
QuicklistItem.prototype.constructor = QuicklistItem;


var Quicklist = function() {
  this.items = {};
  this._dispatch = dispatch;
  fogger.quicklist = this;
};
Quicklist.prototype = new GtkWidget();
Quicklist.prototype.constructor = Quicklist;

Quicklist.prototype.addItem = function(conf) {
  if (!conf.name) {
    console.error('Conf must contain "name" and "callback"');
    return;
  }
  if (this.items[conf.name]) {
    this.items[conf.name].callback = conf.callback;
    return this.items[conf.name];
  } else {
    var item = new QuicklistItem(this, conf.name, conf.callback);
    this.items[conf.name] = item;
    this._dispatch({
      'action': 'add_quicklist_item',
      'name': conf.name,
      'id': item._id,
    });
    return item;
  }
};

Quicklist.prototype.removeItem = function(conf) {
  if (!conf.name) {
    console.error('Conf must contain "name"');
    return;
  }
  var item = this.items[conf.name];
  if (item) {
    var data = {
      'action': 'remove_quicklist_item',
      'id': item._id,
    }
    this._dispatch(data);
    delete(this.items[conf.name]);
  };
};


// Menus
var MenuItem = function(menu, name, callback) {
  GtkWidget.call(this);
  this.type = 'menuitem'
  this.menu = menu;
  this.name = name;
  this.callback = callback;
}
MenuItem.prototype = new GtkWidget();
MenuItem.prototype.constructor = MenuItem;

var Menu = function(name) {
  GtkWidget.call(this);
  this.name = name;
  this.items = {};
  this._dispatch = dispatch;
  this._dispatch({
      'action': 'add_menu',
      'name': this.name,
      'id': this._id,
  });
  fogger.menus[name] = this;
};
Menu.prototype = new GtkWidget();
Menu.prototype.constructor = Menu;

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
    var item = new MenuItem(this, conf.name, conf.callback);
    this.items[conf.name] = item;
    this._dispatch({
      'action': 'add_menu_item',
      'name': conf.name,
      'id': item._id,
      'menu_id': this._id,
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
  var item = this.items[conf.name];
  console.log(item)
  if (item !== undefined) {
    this._dispatch({
      'action': 'remove_menu_item',
      'id': item._id,
    });
    delete(this.items[conf.name]);
  };
};


/* Desktop */
var Desktop = function() {
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
    'action': 'set_urgent',
    'urgent': urgent,
  });
}

Desktop.prototype.newMenu = function(name) {
  return fogger.menus[name] || new Menu(name);
}

Desktop.prototype.quicklist = new Quicklist();

fogger.Desktop = Desktop;
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
