// Borrowed from https://github.com/moment/moment-timezone/issues/167
// Adds support for time zones 'UTC-12'..'UTC+12'
function addUtcTimeZones() {
  // Moment.js uses the IANA timezone database, which supports generic time zones like 'Etc/GMT+1'.
  // However, the signs for these time zones are inverted compared to ISO 8601.
  // For more details, see https://github.com/moment/moment-timezone/issues/167
  for (let offset = -12; offset <= 12; offset++) {
    const posixSign = offset <= 0 ? "+" : "-";
    const isoSign = offset >= 0 ? "+" : "-";
    const link = `Etc/GMT${posixSign}${Math.abs(
      offset
    )}|UTC${isoSign}${Math.abs(offset)}`;
    moment.tz.link(link);
  }
}

function update_filtering(data) {
  var page_url = "{{site.baseurl}}";
  store.set("{{site.domain}}-subs", data.subs);

  $(".ConfItem").hide();
  for (const j in data.all_subs) {
    const s = data.all_subs[j];
    const identifier = "." + s + "-conf";
    if (data.subs.includes(s)) {
      $(identifier).show();
    }
  }

  if (subs.length == 0) {
    window.history.pushState("", "", page_url);
  } else {
    window.history.pushState("", "", page_url + "/?sub=" + data.subs.join());
  }
}

function formatCalendarTime(date) {
  return date.toISOString().replace(/-|:|\.\d+/g, "");
}

function buildGoogleCalendarUrl(event) {
  var start = formatCalendarTime(event.start);
  var durationMs = (event.duration || 60) * 60000;
  var end = event.end
    ? formatCalendarTime(event.end)
    : formatCalendarTime(new Date(event.start.getTime() + durationMs));
  return encodeURI(
    [
      "https://www.google.com/calendar/render",
      "?action=TEMPLATE",
      "&text=" + (event.title || ""),
      "&dates=" + start + "/" + end,
      "&details=" + (event.description || ""),
      "&location=" + (event.address || ""),
    ].join("")
  );
}

function createCalendarFromObject(data) {
  var base = "{{ site.baseurl }}";
  var wrap = document.createElement("div");
  wrap.className = "add-to-calendar calendar-obj";
  if (data.id) {
    wrap.id = data.id;
  }

  var googleUrl = buildGoogleCalendarUrl({
    title: data.title || "",
    start: data.date,
    duration: data.duration || 60,
    description: data.description || "",
    address: data.address || "",
  });

  var iconSrc = base + "/static/img/calendar.png";
  wrap.innerHTML =
    '<a class="cal-add-btn" href="' +
    googleUrl +
    '" target="_blank" rel="noopener" title="Add to Google Calendar">' +
    '<img src="' +
    iconSrc +
    '" alt="" class="cal-add-icon" width="20" height="20"> Google</a>';

  return wrap;
}
