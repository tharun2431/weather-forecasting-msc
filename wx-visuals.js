/* wx-visuals.js — weather-driven artwork.
   Two things live here: the small icons used in the hourly strip, and the
   scene that sits behind the hero card. Both are plain SVG strings keyed off
   the WMO weather code plus whether it is currently night in that city.

   The app is dark-themed, so these deliberately stay tonally dark. A bright
   daylight sky of the kind a consumer weather site uses would fight the rest
   of the interface and make the white text on top of it unreadable. */

(function (global) {
  'use strict';

  /* ── condition grouping ───────────────────────────────────
     WMO codes are finer-grained than the artwork needs. */
  function group(code) {
    if (code === 0) return 'clear';
    if (code === 1) return 'mostly-clear';
    if (code === 2) return 'partly';
    if (code === 3) return 'overcast';
    if (code === 45 || code === 48) return 'fog';
    if (code >= 51 && code <= 57) return 'drizzle';
    if (code >= 61 && code <= 67) return 'rain';
    if (code >= 71 && code <= 77) return 'snow';
    if (code >= 80 && code <= 82) return 'rain';
    if (code === 85 || code === 86) return 'snow';
    if (code >= 95) return 'storm';
    return 'partly';
  }

  /* ── icons (24x24) ────────────────────────────────────────
     One accent colour for the luminary, one neutral for cloud, so a row of
     them reads as a set rather than a pile of clip art. */
  var SUN = '#f0b93f', MOON = '#c9d6e4', CLOUD = '#9fb0c2',
      CLOUD_D = '#7c8ea3', RAIN = '#68a8e0', SNOW = '#cfe2f2', BOLT = '#f0c93f';

  function icon(code, night, cls) {
    var g = group(code), c = cls || 'wx-i';
    var lum = night
      ? '<path d="M15.6 4.2a6.4 6.4 0 1 0 4.2 8.1 5.2 5.2 0 0 1-4.2-8.1z" fill="' + MOON + '"/>'
      : '<circle cx="12" cy="11" r="4.6" fill="' + SUN + '"/>' +
        '<g stroke="' + SUN + '" stroke-width="1.6" stroke-linecap="round" opacity=".85">' +
        '<path d="M12 2.6v2M12 19.4v2M2.6 11h2M19.4 11h2M5.3 4.3l1.4 1.4M17.3 15.7l1.4 1.4M18.7 4.3l-1.4 1.4M6.7 15.7l-1.4 1.4"/></g>';
    var lumSmall = night
      ? '<path d="M9.4 3.4a4.6 4.6 0 1 0 3 5.8 3.7 3.7 0 0 1-3-5.8z" fill="' + MOON + '"/>'
      : '<circle cx="9" cy="7.6" r="3.4" fill="' + SUN + '"/>';
    var cloud = '<path d="M7.4 19.5h9.3a3.6 3.6 0 0 0 .3-7.2 5.3 5.3 0 0 0-10.1-1 3.7 3.7 0 0 0 .5 8.2z" fill="' + CLOUD + '"/>';
    var cloudDark = cloud.replace(CLOUD, CLOUD_D);
    var body;

    switch (g) {
      case 'clear':
      case 'mostly-clear':
        body = lum; break;
      case 'partly':
        body = lumSmall + cloud; break;
      case 'overcast':
        body = '<path d="M5.6 16.4h9.2a3.4 3.4 0 0 0 .3-6.8 5 5 0 0 0-9.5-.9 3.5 3.5 0 0 0 0 7.7z" fill="' + CLOUD_D + '" opacity=".75"/>' + cloud; break;
      case 'fog':
        body = cloudDark +
          '<g stroke="' + CLOUD + '" stroke-width="1.7" stroke-linecap="round" opacity=".85">' +
          '<path d="M4.5 21h7M13.5 21h6"/></g>'; break;
      case 'drizzle':
        body = cloud + '<g stroke="' + RAIN + '" stroke-width="1.6" stroke-linecap="round" opacity=".9">' +
          '<path d="M9.5 21v1.4M14.5 21v1.4"/></g>'; break;
      case 'rain':
        body = cloud + '<g stroke="' + RAIN + '" stroke-width="1.7" stroke-linecap="round">' +
          '<path d="M8.6 20.6l-.8 2.2M12.4 20.6l-.8 2.2M16.2 20.6l-.8 2.2"/></g>'; break;
      case 'snow':
        body = cloud + '<g fill="' + SNOW + '">' +
          '<circle cx="8.6" cy="21.8" r="1"/><circle cx="12.4" cy="22.4" r="1"/><circle cx="16.2" cy="21.8" r="1"/></g>'; break;
      case 'storm':
        body = cloudDark + '<path d="M12.6 19.6l-3 3.6h2.2l-.9 2.8 3.4-4.1h-2.2z" fill="' + BOLT + '"/>'; break;
      default:
        body = lumSmall + cloud;
    }
    return '<svg class="' + c + '" viewBox="0 0 24 26" width="26" height="28" ' +
           'aria-hidden="true" focusable="false">' + body + '</svg>';
  }

  /* ── hero scene ───────────────────────────────────────────
     Sized 400x200 and stretched with `slice`, so it fills the card at any
     width without distorting. Every palette is dark enough that the white
     hero text keeps well clear of the contrast floor. */
  var SKIES = {
    'clear':        { day: ['#1d5c8f', '#2f86bd'], night: ['#0a1728', '#16294a'] },
    'mostly-clear': { day: ['#1e5885', '#3079ab'], night: ['#0a1728', '#152743'] },
    'partly':       { day: ['#245069', '#3a7292'], night: ['#0c1a2a', '#17293d'] },
    'overcast':     { day: ['#2a323b', '#414d59'], night: ['#12171d', '#222a33'] },
    'fog':          { day: ['#3a3f45', '#5c6167'], night: ['#1b1e22', '#33383e'] },
    'drizzle':      { day: ['#243544', '#37505f'], night: ['#0e1620', '#1d2a36'] },
    'rain':         { day: ['#1f3040', '#324a5c'], night: ['#0c141d', '#1a2733'] },
    'snow':         { day: ['#3d5062', '#6d8399'], night: ['#1a2430', '#33445a'] },
    'storm':        { day: ['#141a22', '#242f3c'], night: ['#05080c', '#101720'] }
  };

  function cloudPath(x, y, s, fill, op) {
    return '<g transform="translate(' + x + ' ' + y + ') scale(' + s + ')" opacity="' + op + '">' +
      '<path fill="' + fill + '" d="M18 34h58a17 17 0 0 0 1.5-33.8A25 25 0 0 0 29 -3 18 18 0 0 0 18 34z"/></g>';
  }

  var uid = 0;
  function scene(code, night) {
    var g = group(code);
    var sky = SKIES[g] || SKIES.partly;
    var pair = night ? sky.night : sky.day;
    var p = [];
    // ids must be unique per render: two scenes in one document with the same
    // gradient id both resolve to whichever was parsed first, so every scene
    // would silently inherit the first one's palette
    var GS = 'skyg' + (++uid), GL = 'lumg' + uid;

    p.push('<defs>' +
      '<linearGradient id="' + GS + '" x1="0" y1="0" x2="0.25" y2="1">' +
        '<stop offset="0" stop-color="' + pair[1] + '"/>' +
        '<stop offset="1" stop-color="' + pair[0] + '"/>' +
      '</linearGradient>' +
      '<radialGradient id="' + GL + '" cx=".5" cy=".5" r=".5">' +
        '<stop offset="0" stop-color="' + (night ? '#dbe6f2' : '#ffd98a') + '" stop-opacity=".55"/>' +
        '<stop offset="1" stop-color="' + (night ? '#dbe6f2' : '#ffd98a') + '" stop-opacity="0"/>' +
      '</radialGradient></defs>');

    p.push('<rect width="400" height="200" fill="url(#' + GS + ')"/>');

    // stars, only on a clear-ish night
    if (night && (g === 'clear' || g === 'mostly-clear' || g === 'partly')) {
      var stars = '';
      for (var i = 0; i < 26; i++) {
        var sx = (i * 61.8) % 400, sy = 26 + (i * 37.3) % 108,
            r = i % 5 === 0 ? 1.3 : 0.85, o = i % 3 === 0 ? 0.85 : 0.5;
        stars += '<circle cx="' + sx.toFixed(1) + '" cy="' + sy.toFixed(1) +
                 '" r="' + r + '" fill="#e8f0fa" opacity="' + o + '"/>';
      }
      p.push('<g class="sky-stars">' + stars + '</g>');
    }

    // the luminary, unless it is fully hidden
    if (g !== 'overcast' && g !== 'rain' && g !== 'storm' && g !== 'fog' && g !== 'snow') {
      p.push('<circle cx="316" cy="84" r="78" fill="url(#' + GL + ')"/>');
      p.push(night
        ? '<path d="M328 62a24 24 0 1 0 15 30 19.5 19.5 0 0 1-15-30z" fill="#e2ebf6"/>'
        : '<circle cx="316" cy="84" r="24" fill="#ffce6b"/>');
    }

    // cloud decks
    var deckFill = night ? '#5d6f84' : '#8ea3b8';
    if (g === 'partly' || g === 'mostly-clear') {
      p.push('<g class="sky-drift">' + cloudPath(18, 104, 1.0, deckFill, night ? .40 : .52) + '</g>');
      p.push('<g class="sky-drift sky-drift-2">' + cloudPath(232, 122, .78, deckFill, night ? .30 : .40) + '</g>');
    } else if (g === 'overcast' || g === 'fog') {
      p.push('<g class="sky-drift">' + cloudPath(-24, 82, 1.3, deckFill, .48) + '</g>');
      p.push('<g class="sky-drift sky-drift-2">' + cloudPath(182, 100, 1.15, deckFill, .40) + '</g>');
    } else if (g === 'drizzle' || g === 'rain' || g === 'snow' || g === 'storm') {
      p.push('<g class="sky-drift">' + cloudPath(-18, 76, 1.25, deckFill, .55) + '</g>');
      p.push('<g class="sky-drift sky-drift-2">' + cloudPath(188, 88, 1.08, deckFill, .45) + '</g>');
    }

    // fog bands
    if (g === 'fog') {
      var bands = '';
      // wide, soft, overlapping bands - thin lines at low opacity just vanished
      for (var b = 0; b < 6; b++) {
        bands += '<rect x="-60" y="' + (58 + b * 24) + '" width="520" height="' + (13 + (b % 2) * 6) +
                 '" rx="9" fill="#dae3ec" opacity="' + (0.30 - b * 0.035).toFixed(2) + '"/>';
      }
      p.push('<rect width="400" height="200" fill="#c8d3de" opacity=".13"/>');
      p.push('<g class="sky-fog">' + bands + '</g>');
      p.push('<g class="sky-fog sky-drift-2">' +
             '<rect x="-60" y="132" width="520" height="30" rx="15" fill="#e4ebf2" opacity=".16"/></g>');
    }

    // precipitation
    if (g === 'rain' || g === 'drizzle' || g === 'storm') {
      var streaks = '', heavy = (g !== 'drizzle');
      for (var r2 = 0; r2 < (heavy ? 34 : 20); r2++) {
        var rx = (r2 * 43.7) % 400, ry = 96 + ((r2 * 29) % 96),
            len = heavy ? 13 : 8;
        streaks += '<line x1="' + rx.toFixed(1) + '" y1="' + ry.toFixed(1) +
                   '" x2="' + (rx - 4).toFixed(1) + '" y2="' + (ry + len) +
                   '" stroke="#a8cbe8" stroke-width="1.4" stroke-linecap="round" opacity=".42"/>';
      }
      p.push('<g class="sky-rain">' + streaks + '</g>');
    }
    if (g === 'snow') {
      var flakes = '', flakes2 = '';
      // two layers at different sizes and speeds - one thin layer of 1.4px dots
      // at 62% simply could not be seen against the sky
      for (var f = 0; f < 44; f++) {
        var fx = ((f * 41.7) % 400), fy = 40 + ((f * 53) % 160);
        flakes += '<circle cx="' + fx.toFixed(1) + '" cy="' + fy.toFixed(1) +
                  '" r="' + (f % 4 === 0 ? 3.4 : f % 2 === 0 ? 2.5 : 1.8) +
                  '" fill="#ffffff" opacity="' + (f % 3 === 0 ? '.95' : '.78') + '"/>';
      }
      for (var f2 = 0; f2 < 26; f2++) {
        flakes2 += '<circle cx="' + ((f2 * 67.1) % 400).toFixed(1) + '" cy="' +
                   (30 + ((f2 * 71) % 165)).toFixed(1) + '" r="1.5" fill="#eaf4ff" opacity=".55"/>';
      }
      p.push('<g class="sky-snow-far">' + flakes2 + '</g>');
      p.push('<g class="sky-snow">' + flakes + '</g>');
      p.push('<rect x="0" y="150" width="400" height="50" fill="#dfeaf5" opacity=".14"/>');
    }
    if (g === 'storm') {
      // a bolt that is only visible during the flash leaves storm and rain
      // looking identical for most of the cycle, so one stays on permanently
      p.push('<path d="M214 92l-24 44h17l-9 37 33-50h-18z" fill="#ffd863" opacity=".55"/>');
      p.push('<path class="sky-bolt" d="M214 92l-24 44h17l-9 37 33-50h-18z" fill="#fff3c4"/>');
      p.push('<path class="sky-bolt sky-bolt-2" d="M96 104l-18 33h13l-7 27 25-37h-14z" fill="#ffe27a"/>');
      p.push('<rect class="sky-flash" width="400" height="200" fill="#cfe0f5"/>');
    }

    return '<svg class="sky" viewBox="0 0 400 200" preserveAspectRatio="xMidYMid slice" ' +
           'aria-hidden="true" focusable="false">' + p.join('') + '</svg>';
  }


  /* ── stat icons ───────────────────────────────────────────
     Drawn with currentColor rather than a fixed hex, so they take the colour of
     the label they sit beside and survive a theme change without edits. */
  var STAT = {
    feels:    '<path d="M14 14.8V5a2 2 0 1 0-4 0v9.8a4 4 0 1 0 4 0z"/><path d="M12 9v6"/>',
    humidity: '<path d="M12 3.2s5.4 5.6 5.4 9.2a5.4 5.4 0 0 1-10.8 0C6.6 8.8 12 3.2 12 3.2z"/>',
    wind:     '<path d="M3 8.5h11a2.8 2.8 0 1 0-2.8-2.8"/><path d="M3 15.5h8.6a2.6 2.6 0 1 1-2.6 2.6"/><path d="M3 12h15.2a2.4 2.4 0 1 0-2.4-2.4"/>',
    pressure: '<path d="M4.2 17.2a9 9 0 1 1 15.6 0"/><path d="M12 13.6l3.8-3.6"/><circle cx="12" cy="14.4" r="1.5" fill="currentColor" stroke="none"/>'
  };

  function statIcon(name) {
    var d = STAT[name];
    if (!d) return '';
    return '<svg class="stat-i" viewBox="0 0 24 24" width="15" height="15" ' +
           'fill="none" stroke="currentColor" stroke-width="1.7" ' +
           'stroke-linecap="round" stroke-linejoin="round" ' +
           'aria-hidden="true" focusable="false">' + d + '</svg>';
  }

  /* night is decided from the city's own clock, not the viewer's */
  function isNight(localHour) {
    return localHour < 6 || localHour >= 20;
  }

  global.WXV = { icon: icon, scene: scene, group: group,
                 isNight: isNight, statIcon: statIcon };
})(window);
