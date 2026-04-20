"""Custom website views for HomageMUD."""

from django.shortcuts import render

from evennia.server.sessionhandler import SESSIONS


def online_characters(request):
    """List online: both puppeted characters and accounts without a puppet."""
    seen_chars = set()
    seen_accounts = set()
    characters = []
    idle_accounts = []
    for session in SESSIONS.get_sessions():
        puppet = getattr(session, "puppet", None)
        account = getattr(session, "account", None)
        if puppet and puppet.id not in seen_chars:
            seen_chars.add(puppet.id)
            characters.append(
                {
                    "name": puppet.key,
                    "account": account.username if account else "",
                    "id": puppet.id,
                }
            )
            if account:
                seen_accounts.add(account.id)
        elif account and account.id not in seen_accounts:
            seen_accounts.add(account.id)
            idle_accounts.append({"name": account.username, "id": account.id})
    characters.sort(key=lambda c: c["name"].lower())
    idle_accounts.sort(key=lambda a: a["name"].lower())
    return render(
        request,
        "website/online.html",
        {"characters": characters, "idle_accounts": idle_accounts},
    )
