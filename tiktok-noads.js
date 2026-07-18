/*
 * TikTok feed ad filter for Shadowrocket.
 * Removes only feed items explicitly marked with is_ads=true/1.
 */

(function () {
  "use strict";

  var body = typeof $response !== "undefined" ? $response.body : "";
  if (!body) {
    $done({});
    return;
  }

  function hasAdFlag(value) {
    return value === true || value === 1 || value === "1";
  }

  function isExplicitAd(item) {
    if (!item || typeof item !== "object") return false;

    var candidates = [
      item,
      item.aweme,
      item.aweme_info,
      item.aweme_detail
    ];

    return candidates.some(function (candidate) {
      return candidate && hasAdFlag(candidate.is_ads);
    });
  }

  function filterFeed(container) {
    if (!container || typeof container !== "object") return 0;

    var removed = 0;
    ["aweme_list", "item_list"].forEach(function (key) {
      if (!Array.isArray(container[key])) return;

      var before = container[key].length;
      container[key] = container[key].filter(function (item) {
        return !isExplicitAd(item);
      });
      removed += before - container[key].length;
    });

    return removed;
  }

  try {
    var payload = JSON.parse(body);
    var removed = filterFeed(payload);

    if (payload && payload.data && !Array.isArray(payload.data)) {
      removed += filterFeed(payload.data);
    }

    if (removed > 0) {
      console.log("[TikTok NoAds] Removed feed ads: " + removed);
      $done({ body: JSON.stringify(payload) });
      return;
    }

    $done({});
  } catch (error) {
    console.log("[TikTok NoAds] Response was not JSON; left unchanged: " + error);
    $done({});
  }
})();
