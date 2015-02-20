
var ClockUtc = (function() {

  var $DIV;

  function init(ID) {

    if (!ID) {
      return false;
    }

    $DIV = $(ID);
    if ($DIV.length != 1) {
      return false;
    }

    setInterval(update_clock, 1000);

  }

  function update_clock() {

    var MONTHS = ['Jan',
      'Feb',
      'Mar',
      'Apr',
      'May',
      'Jun',
      'Jul',
      'Aug',
      'Sep',
      'Oct',
      'Nov',
      'Dec'];

    var now,
        month,
        day,
        year,
        hour,
        min,
        sec,
        ts;

    // Initialize the data object
    now = new Date();

    // Get date pieces
    month = MONTHS[now.getUTCMonth()];
    day = now.getUTCDate();
    year = now.getUTCFullYear();
    hour = now.getUTCHours();
    minutes = now.getUTCMinutes();
    seconds = now.getUTCSeconds();
 
    // Prepend necessary zeros
    //month   = month < 10 ? "0" + month : month;
    day     = day < 10 ? "0" + day : day;
    hour    = hour < 10 ? "0" + hour : hour;
    minutes = minutes < 10 ? "0" + minutes : minutes;
    seconds = seconds < 10 ? "0" + seconds : seconds;
 
    // Create time string
    ts = month + ". " + day + ", " + year;
    ts += " " + hour + ":" + minutes + ":" + seconds + " Z";

//    console.log("Time: " + ts);

    $DIV.text(ts);

  }

  return {
    init : init
  }


})();

