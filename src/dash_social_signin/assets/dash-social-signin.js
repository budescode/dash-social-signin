(function () {
  "use strict";

  var DEFAULTS = {
    google: {
      authUrl: "https://accounts.google.com/o/oauth2/v2/auth",
      scope: "openid email profile",
      responseType: "code"
    },
    facebook: {
      authUrl: "https://www.facebook.com/v18.0/dialog/oauth",
      scope: "public_profile,email",
      responseType: "code"
    },
    github: {
      authUrl: "https://github.com/login/oauth/authorize",
      scope: "read:user user:email",
      responseType: "code"
    },
    x: {
      authUrl: "https://twitter.com/i/oauth2/authorize",
      scope: "tweet.read users.read offline.access",
      responseType: "code"
    },
    linkedin: {
      authUrl: "https://www.linkedin.com/oauth/v2/authorization",
      scope: "openid profile email",
      responseType: "code"
    },
    microsoft: {
      authUrl: "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
      scope: "openid email profile",
      responseType: "code"
    },
    apple: {
      authUrl: "https://appleid.apple.com/auth/authorize",
      scope: "name email",
      responseType: "code"
    },
    discord: {
      authUrl: "https://discord.com/api/oauth2/authorize",
      scope: "identify email",
      responseType: "code"
    },
    slack: {
      authUrl: "https://slack.com/openid/connect/authorize",
      scope: "openid profile email",
      responseType: "code"
    }
  };

  var PROVIDER_LABELS = {
    google: "Continue with Google",
    facebook: "Continue with Facebook",
    github: "Continue with GitHub",
    x: "Continue with X",
    linkedin: "Continue with LinkedIn",
    microsoft: "Continue with Microsoft",
    apple: "Continue with Apple",
    discord: "Continue with Discord",
    slack: "Continue with Slack"
  };

  function merge(target, source) {
    var result = {};
    Object.keys(target || {}).forEach(function (key) {
      result[key] = target[key];
    });
    Object.keys(source || {}).forEach(function (key) {
      result[key] = source[key];
    });
    return result;
  }

  function buildAuthUrl(provider, options) {
    var defaults = DEFAULTS[provider] || {};
    var cfg = merge(defaults, options || {});

    if (!cfg.clientId || !cfg.redirectUri) {
      throw new Error("Missing clientId or redirectUri for " + provider);
    }

    var params = {
      client_id: cfg.clientId,
      redirect_uri: cfg.redirectUri,
      response_type: cfg.responseType || "code"
    };

    if (cfg.scope) {
      params.scope = cfg.scope;
    }

    if (cfg.state) {
      params.state = cfg.state;
    }

    var extra = cfg.extraParams || {};
    Object.keys(extra).forEach(function (key) {
      params[key] = extra[key];
    });

    var query = Object.keys(params)
      .map(function (key) {
        return encodeURIComponent(key) + "=" + encodeURIComponent(params[key]);
      })
      .join("&");

    var separator = cfg.authUrl.indexOf("?") === -1 ? "?" : "&";
    return cfg.authUrl + separator + query;
  }

  function createButton(provider, options) {
    var button = document.createElement("button");
    button.type = "button";
    button.className = "dss-btn dss-btn-" + provider;
    button.textContent = PROVIDER_LABELS[provider] || "Continue";

    button.addEventListener("click", function () {
      var url = buildAuthUrl(provider, options);
      window.location.assign(url);
    });

    return button;
  }

  function renderButtons(config, container) {
    var providers = config.providers || {};
    Object.keys(providers).forEach(function (provider) {
      var options = providers[provider];
      var button = createButton(provider, options);
      container.appendChild(button);
    });
  }

  function init() {
    var nodes = document.querySelectorAll("[data-dss-config]");
    nodes.forEach(function (node) {
      if (node.getAttribute("data-dss-initialized")) {
        return;
      }

      var raw = node.getAttribute("data-dss-config");
      if (!raw) {
        return;
      }

      var config;
      try {
        config = JSON.parse(raw);
      } catch (err) {
        console.error("Invalid data-dss-config JSON", err);
        return;
      }

      renderButtons(config, node);
      node.setAttribute("data-dss-initialized", "true");
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Re-run init only when new element nodes are added to the DOM.
  if (typeof MutationObserver !== "undefined") {
    var observer = new MutationObserver(function (mutations) {
      for (var i = 0; i < mutations.length; i++) {
        var added = mutations[i].addedNodes;
        for (var j = 0; j < added.length; j++) {
          if (added[j].nodeType === 1) {
            init();
            return;
          }
        }
      }
    });

    observer.observe(document.body, { childList: true, subtree: true });
  }

  window.DashSocialSignin = {
    buildAuthUrl: buildAuthUrl
  };
})();
