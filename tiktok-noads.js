/*
 * TikTok feed ad filter for Shadowrocket.
 * Removes only feed items carrying explicit advertising markers.
 * Covers the common JSON feed shapes without changing region fields.
 */

(function () {
  "use strict";

  var body = typeof $response !== "undefined" ? $response.body : "";
  if (!body) {
    $done({});
    return;
  }

  function hasAdFlag(value) {
    return value === true || value === 1 || value === "1" || value === "true";
  }

  function hasNonEmptyObject(value) {
    return value && typeof value === "object" && Object.keys(value).length > 0;
  }

  function hasNonEmptyString(value) {
    return typeof value === "string" && value.trim().length > 0;
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
      if (!candidate || typeof candidate !== "object") return false;

      return hasAdFlag(candidate.is_ads) ||
        hasAdFlag(candidate.is_ad) ||
        hasNonEmptyObject(candidate.ad_info) ||
        hasNonEmptyObject(candidate.raw_ad_data) ||
        hasNonEmptyString(candidate.raw_ad_data);
    });
  }

  function filterFeed(container) {
    if (!container || typeof container !== "object") return 0;

    var removed = 0;
    var inspected = 0;
    ["aweme_list", "item_list"].forEach(function (key) {
      if (!Array.isArray(container[key])) return;

      var before = container[key].length;
      inspected += before;
      container[key] = container[key].filter(function (item) {
        return !isExplicitAd(item);
      });
      removed += before - container[key].length;
    });

    return { removed: removed, inspected: inspected };
  }

  try {
    var payload = JSON.parse(body);
    var result = filterFeed(payload);

    if (payload && payload.data && !Array.isArray(payload.data)) {
      var nestedResult = filterFeed(payload.data);
      result.removed += nestedResult.removed;
      result.inspected += nestedResult.inspected;
    }

    var requestUrl = typeof $request !== "undefined" && $request.url ? $request.url : "unknown URL";

    if (result.removed > 0) {
      console.log("[TikTok NoAds] Removed " + result.removed + " of " + result.inspected + " feed items: " + requestUrl);
      $done({ body: JSON.stringify(payload) });
      return;
    }

    console.log("[TikTok NoAds] Inspected " + result.inspected + " feed items; no explicit ads found: " + requestUrl);
    $done({});
  } catch (error) {
    console.log("[TikTok NoAds] Response was not JSON; left unchanged: " + error);
    $done({});
  }
})();
