"""Custom website views for HomageMUD."""

from django.shortcuts import render

from evennia.server.sessionhandler import SESSIONS


def online_characters(request):
    """List currently-puppeted characters across all online sessions."""
    seen = set()
    characters = []
    for session in SESSIONS.get_sessions():
        puppet = getattr(session, "puppet", None)
        if not puppet or puppet.id in seen:
            continue
        seen.add(puppet.id)
        account = getattr(puppet, "account", None)
        characters.append(
            {
                "name": puppet.key,
                "account": account.username if account else "",
                "id": puppet.id,
            }
        )
    characters.sort(key=lambda c: c["name"].lower())
    return render(request, "website/online.html", {"characters": characters})
