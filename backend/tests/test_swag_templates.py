from pathlib import Path

import yaml

ROOT = Path(__file__).parents[2]


def test_standalone_proxy_compose_does_not_publish_an_auth_bypass_port():
    config = yaml.safe_load((ROOT / "compose.swag.yaml").read_text())
    app = config["services"]["jarvis"]
    assert "ports" not in app
    assert app["expose"] == ["8000"]
    assert config["networks"]["proxy"]["external"] is True
    assert "/var/run/docker.sock:/var/run/docker.sock" not in app["volumes"]
    assert "docofhome" in app["networks"]["proxy"]["aliases"]


def test_browser_vhost_protects_all_application_routes_and_distrusts_client_identity():
    text = (ROOT / "deploy/swag/docofhome.subdomain.conf.sample").read_text()
    root = text.split("location / {", 1)[1].split("# Exact auth check", 1)[0]
    assert "auth_request /outpost.goauthentik.io/auth/nginx;" in root
    assert "error_page 401" in text
    assert "if ($doh_reject_origin) { return 403; }" in root
    assert "map $http_origin $doh_same_origin" in text
    assert "error_page 403" not in text and "satisfy any" not in text
    check = text.split("location = /outpost.goauthentik.io/auth/nginx {", 1)[1].split("}", 1)[0]
    assert "internal;" in check
    assert "proxy_pass_request_headers off;" in check
    assert 'proxy_set_header X-Original-URI "";' in check
    assert "proxy_set_header Cookie $http_cookie;" in check
    assert "location = /mcp { return 404; }" in text
    assert "location ^~ /mcp/ { return 404; }" in text


def test_mcp_vhost_is_restricted_to_mcp_and_preserves_token_auth():
    text = (ROOT / "deploy/swag/docofhome-mcp.subdomain.conf.sample").read_text()
    assert "location ~ ^/mcp(?:/|$)" in text
    assert "location / { return 404; }" in text
    assert "proxy_set_header Authorization $http_authorization;" in text
    assert "auth_request" not in text
    assert "access_log off;" in text
