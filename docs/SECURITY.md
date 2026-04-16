# WKApp Security Model

WKApp is designed to serve a Bottle.py application on `localhost` inside a
Pythonista 3 iOS app and render it in a fullscreen `WKWebView`. Every user of
the app is effectively "the developer of the app on the device". There is no
remote user, no multi-tenant concern and no built-in authentication —
authentication is unnecessary for a loopback-only UI process.

However, any third-party HTML / JS / CSS loaded into a view (including code
pulled from CDNs such as Bootstrap, Preact, Pyodide, or Wasmer.js in the
bundled `test/views`) executes with full access to the dev server. WKApp
therefore applies secure-by-default settings that prevent common web
vulnerabilities from manifesting in views authored against it.

## Secure-by-default settings

### Bottle `debug` mode is OFF by default

Bottle's debug mode renders verbose stack traces (including filesystem paths
and surrounding source) in HTTP error responses. Prior versions always ran the
server with `debug=True`. WKApp now defaults to `debug=False`. To enable it for
development only:

```python
app = WKApp(__file__, debug=True)
```

### CORS is scoped to the app's own origin by default

Prior versions responded with `Access-Control-Allow-Origin: *` and
`Access-Control-Allow-Methods: *` on every response. That allowed any page
loaded in the webview (including third-party scripts) to read responses from
the app's own dev server. The default is now the app's own base URL; opt back
in with `cors_origin='*'` if needed:

```python
app = WKApp(__file__, cors_origin='*')
```

### Form and query parameters only bind to declared, non-callable view state

The automatic POST/GET binding that assigns `request.forms` / `request.query`
values onto the view instance now refuses to overwrite:

- attribute names starting with `_`
- attribute names that don't already exist on the view
- attribute names that resolve to a callable (methods)
- framework-internal names inherited from `WKView`
  (`app`, `url`, `path`, `template`, `js`, `eval_js`, `eval_js_async`,
  `element`, `elements`, `event`, `webview`)

This prevents an attacker-supplied query parameter like `?eval_js=pwn` from
replacing a bound method on the view, and stops form values from clobbering
the view's wiring to the framework.

### `view.invoke` / `app.invoke` cannot call framework-internal methods

JavaScript running in the webview can call Python via
`window.webkit.messageHandlers`. The Python side (`webview_on_invoke`) now
enforces:

- `target` names starting with `_` are denied.
- `WKApp` context: only `exit` is callable. `stop_server`, `cleanup`,
  `setup_server_routes`, `static_file`, `template`, `get_view`,
  `_bind_request_value`, etc. are **not** reachable from JS.
- `WKView` context: only methods declared on the view class subclass are
  callable. Inherited framework methods (`eval_js`, `eval_js_async`,
  `element`, `elements`, `event`, `webview`) are **not** reachable from JS.

Subclass views remain free to expose any callable they define.

### `wkapp://` proxy requires opt-in and an allowlist

The `wkapp://` custom URL scheme previously exposed a `proxy` command that
forwarded arbitrary HTTP requests — with attacker-controlled method, headers
and body — to arbitrary URLs. That is a blind SSRF primitive against any
network reachable from the device. It is now disabled by default and requires
both `allow_proxy=True` and an explicit allowlist of hostnames:

```python
app = WKApp(
    __file__,
    allow_proxy=True,
    proxy_allowed_hosts={'api.example.com'},
    proxy_timeout=30,
)
```

Only `http`/`https` URLs are allowed; non-http schemes and unlisted hostnames
are rejected. `proxy_timeout` bounds how long a single proxied request may
block. The existing `wkapp://localhost/...` passthrough to the app's own
Bottle server is unaffected.

### Mako autoescapes `${...}` expressions by default

`TemplateLookup` is configured with `default_filters=['h']`, so any `${...}`
Mako expression is HTML-escaped by default. This mitigates reflected XSS from
auto-bound form / query values rendered with expressions like `${view.name}`.

Templates that intentionally emit HTML, CSS or JS (for example the
`<%def name="codeblock">` helper) can opt a specific expression out with the
`| n` filter:

```mako
${codeblock('''<h1>emitted as HTML</h1>''') | n}
```

### Dependency minimums

`requirements.txt` and `pyproject.toml` now pin minimum versions for
transitive dependencies with known CVEs:

| Package  | Minimum  | Reason                                            |
|----------|----------|---------------------------------------------------|
| Mako     | `1.2.2`  | CVE-2022-40023 (ReDoS in Mako lexer)              |
| requests | `2.32.2` | CVE-2024-35195 (`Session.verify=False` bypass)    |

## Reporting vulnerabilities

Please open a private security advisory on
<https://github.com/M4nw3l/pythonista-wkapp/security/advisories/new> rather
than filing a public issue.
