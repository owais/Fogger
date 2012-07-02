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



var Fogger = function() {
  this.__version__  = 12.07;
};


Fogger.prototype._dispatch = function(action) {
  var uri = 'http://fogger.local/' + action
  var h = new XMLHttpRequest();
  h.open('GET', uri,  true);
  h.send();
}

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


window.Fogger = Fogger;

var readyEvent = document.createEvent('Event');
readyEvent.initEvent('foggerReady', true, true);
document.dispatchEvent(readyEvent);
