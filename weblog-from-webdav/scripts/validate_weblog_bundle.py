#!/usr/bin/env python3
"""Sanity-check a weblog-from-webdav skill bundle."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


CHECKS = {
    "templates/deploy-weblog-opl-site.sql": [
        "DAV_RES_UPLOAD_STRSES_INT",
        "string_output",
        "RSS",
        "Atom",
    ],
    "templates/deploy-weblog-opl-site-facet.sql": [
        "schema:category",
        "dict_iter_next",
        "contains",
        "._%",
    ],
    "SKILL.md": [
        "isql-engine",
        "webdav-posts",
        "WebDAV is then used for the post-publication workflow",
    ],
    "references/webdav-mode.md": [
        "not the engine setup channel",
        "switch to `isql` engine bootstrap",
    ],
    "references/webdav-weblog-engine-gate.md": [
        "Static HTML is only an optional preview",
        "DAV_RES_UPLOAD_STRSES_INT",
        "validate_generated_weblog_bundle.py",
    ],
    "scripts/validate_generated_weblog_bundle.py": [
        "DAV_RES_UPLOAD_STRSES_INT",
        "string_output",
        "VHOST_DEFINE",
    ],
    "templates/register-weblog-pinning-tool.sql": [
        "WEBLOG_DAV_SET_PIN",
        "schema:position",
        "REGISTER_CHAT_FUNCTION",
        "openapi.yaml",
        "OPAL registration is best-effort",
        "exec ('OAI.DBA.REGISTER_CHAT_FUNCTION",
    ],
    "references/opal-tool-mode.md": [
        "WEBLOG_DAV_SET_PIN",
        "REGISTER_CHAT_FUNCTION",
        "openapi.yaml",
        "OPAL registration is best-effort",
    ],
    "templates/deploy-weblog-skinned.sql": [
        "WEBLOG_DAV_DEPLOY_SKINNED",
        "WEBLOG_DAV_GET_COLLECTION_PROP",
        "weblog:skin",
        "weblog:newsletterEnabled",
        "weblog:publicRoute",
        "nl_action",
        "RES_OWNER",
        "admin_route",
        "{{ADMIN_ROUTE}}",
        "admin_msg",
        "dashboard.html",
        "WEBLOG_DASHBOARD_REFRESH",
        "weblog:adminActionToken",
        "admin_action",
        "send_digest_now",
        "set_digest_interval",
        "set_digest_mode",
        "set_content_mode",
        "import_subscribers_csv",
        "import_subscribers_rdf",
        "import_subscribers_manual",
        "set_skin",
        "set_email_config",
        "set_digest_schedule",
        "set_dashboard_schedule",
        "set_post_category",
        "set_post_pin",
        "admin_unsubscribe",
        "admin_email",
        "weblog:adminEmail",
        "nl_is_post",
        "nl_needs_confirm_post",
    ],
    "templates/register-weblog-newsletter.sql": [
        "WEBLOG_NEWSLETTER_SUBSCRIBE",
        "WEBLOG_NEWSLETTER_CONFIRM",
        "WEBLOG_NEWSLETTER_UNSUBSCRIBE",
        "WEBLOG_NEWSLETTER_SEND_DIGEST",
        "WEBLOG_NEWSLETTER_POST_TITLE",
        "WEBLOG_NEWSLETTER_POST_EXCERPT",
        "WEBLOG_NEWSLETTER_POST_CARD",
        "WEBLOG_NEWSLETTER_HTML_SHELL",
        "WEBLOG_NEWSLETTER_IS_INFOGRAPHIC",
        "WEBLOG_NEWSLETTER_STRIP_ELEMENT",
        "WEBLOG_NEWSLETTER_EXTRACT_STYLE_BLOCKS",
        "extra_css",
        "anim-fade",
        "ui-monospace",
        "Email Server Config",
        "Tagging &amp; Scheduling",
        "weblog-dashboard-refresh",
        "data-theme-toggle",
        "theme-switch-thumb",
        "role=\"switch\"",
        "weblog-dashboard-theme",
        "category-options",
        "row-action",
        "admin-banner-slot",
        "admin_msg",
        "WEBLOG_NEWSLETTER_IMPORT_CSV",
        "WEBLOG_NEWSLETTER_IMPORT_RDF",
        "WEBLOG_NEWSLETTER_IMPORT_ONE",
        "WEBLOG_NEWSLETTER_SEND_ACTIVATION",
        "WEBLOG_NEWSLETTER_SEND_UNSUBSCRIBE_NOTICE",
        "WEBLOG_NEWSLETTER_BULK_HEADERS",
        "WEBLOG_NEWSLETTER_NOTIFY_ADMIN",
        "weblog:adminEmail",
        "Reply-To",
        "Message-ID",
        "List-Id",
        "List-Unsubscribe",
        "List-Unsubscribe-Post",
        "Precedence: bulk",
        "WS_NAME",
        "manual-add",
        "skin_choice",
        "weblog:newsletterContentMode",
        "smtp_send",
        "WEBLOG_SUBSCRIBER",
        "WEBLOG_DASHBOARD_REFRESH",
        "WEBLOG_DASHBOARD_SCHEDULE_REFRESH",
        "weblog:adminDavUser",
        "weblog:newsletterMode",
        "immediate",
        "text/html; charset=UTF-8",
    ],
    "references/skin-authoring-contract.md": [
        "Resolution order",
        "weblog:skin",
        "PROP_TYPE='C'",
    ],
    "templates/upgrade.sql": [
        "SECTION 1 of 2",
        "SECTION 2 of 2",
        "REDEPLOY",
        "WEBLOG_DAV_DEPLOY_SKINNED",
        "__DAV_COLLECTION__",
        "PRE-FLIGHT BACKUP 1 of 2",
        "PRE-FLIGHT BACKUP 2 of 2",
        "WEBLOG_SUBSCRIBER_BACKUP_",
        "WEBLOG_UPGRADE_BACKUP",
        "TO RESTORE",
    ],
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-dir", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    missing: list[str] = []
    for rel, needles in CHECKS.items():
        path = args.skill_dir / rel
        if not path.exists():
            missing.append(f"missing file: {rel}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for needle in needles:
            if needle not in text:
                missing.append(f"{rel}: missing marker {needle!r}")
    if missing:
        for item in missing:
            print(item, file=sys.stderr)
        return 1
    print("weblog-from-webdav bundle markers OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
