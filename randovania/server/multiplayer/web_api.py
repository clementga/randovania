import html
import json

import construct
import sanic
from python_paginate.web.sanic_paginate import Pagination

from randovania.game_description import default_database
from randovania.layout.versioned_preset import VersionedPreset
from randovania.network_common import remote_inventory
from randovania.server.database import MultiplayerMembership, MultiplayerSession, World, WorldUserAssociation
from randovania.server.server_app import ServerApp

bp = sanic.Blueprint("web_api")


def _get_session(session_id: int) -> MultiplayerSession:
    try:
        return MultiplayerSession.get_by_id(session_id)
    except MultiplayerSession.DoesNotExist:
        raise sanic.SanicException("No such session.", status_code=404)


@bp.route("/sessions")
async def admin_sessions(request: sanic.Request) -> sanic.HTTPResponse:
    query = MultiplayerSession.select().order_by(MultiplayerSession.creation_date.desc())
    pagination = Pagination(request, total=query.count())

    if pagination.page > pagination.total_pages:
        raise sanic.SanicException("No such page.", status_code=404)

    lines = []
    for session in query.paginate(pagination.page, pagination.per_page):
        assert isinstance(session, MultiplayerSession)
        lines.append(
            "<tr>{}</tr>".format(
                "".join(
                    f"<td>{col}</td>"
                    for col in [
                        "<a href='{}'>{}</a>".format(
                            request.url_for("web_api.admin_session", session_id=session.id),
                            html.escape(session.name),
                        ),
                        html.escape(session.creator.name),
                        session.creation_date,
                        len(session.members),
                        len(session.worlds),
                        session.password is not None,
                    ]
                )
            )
        )

    previous = "Previous"
    if pagination.page > 1:
        previous = "<a href='{}'>Previous</a>".format(
            request.url_for("web_api.admin_sessions", page=pagination.page - 1)
        )

    next_link = "Next"
    if pagination.page < pagination.total_pages:
        next_link = "<a href='{}'>Next</a>".format(request.url_for("web_api.admin_sessions", page=pagination.page + 1))

    header = ["Name", "Creator", "Creation Date", "Num Users", "Num Worlds", "Has Password?"]
    return sanic.html(
        ("<table border='1'><tr>{header}</tr>{content}</table>Page {page} of {num_pages}. {previous} / {next}.").format(
            header="".join(f"<th>{it}</th>" for it in header),
            content="".join(lines),
            page=pagination.page,
            num_pages=pagination.total_pages,
            previous=previous,
            next=next_link,
        )
    )


@bp.route("/session/<session_id>")
def admin_session(request: sanic.Request, session_id: int) -> sanic.HTTPResponse:
    session = _get_session(session_id)

    rows = []

    associations: list[WorldUserAssociation] = list(
        WorldUserAssociation.select()
        .join(World)
        .where(
            World.session == session,
        )
    )

    for association in associations:
        inventory = []

        if association.inventory is not None:
            parsed_inventory = remote_inventory.decode_remote_inventory(association.inventory)

            if isinstance(parsed_inventory, construct.ConstructError):
                inventory.append(f"Error parsing: {parsed_inventory}")
            else:
                game = VersionedPreset.from_str(association.world.preset).game
                db = default_database.resource_database_for(game)
                for item_name, item in parsed_inventory.items():
                    if item > 0:
                        inventory.append(f"{db.get_item(item_name).long_name} x{item}")
        else:
            inventory.append("Missing")

        rows.append(
            [
                html.escape(association.user.name),
                html.escape(association.world.name),
                json.loads(association.world.preset)["game"],
                association.connection_state.pretty_text,
                ", ".join(inventory),
                MultiplayerMembership.get_by_ids(association.user_id, session_id).admin,
                "<a href='{link}'>Download</a>".format(
                    link=request.url_for("web_api.download_world_preset", world_id=association.world_id)
                ),
            ]
        )

    header = ["User", "World", "Game", "Connection State", "Inventory", "Is Admin?", "Preset"]
    table = "<table border='1'><tr>{}</tr>{}</table>".format(
        "".join(f"<th>{h}</th>" for h in header),
        "".join("<tr>{}</tr>".format("".join(f"<td>{h}</td>" for h in r)) for r in rows),
    )

    entries = [
        f"<p>Session: {html.escape(session.name)}</p>",
        f"<p>Created by {html.escape(session.creator.name)} at {session.creation_datetime}</p>",
        f"<p>Session is password protected, password is <code>{html.escape(session.password)}</code></p>"
        if session.password is not None
        else "Session is not password protected",
        "<p><a href='{link}'>Download rdvgame</a></p>".format(
            link=request.url_for("web_api.download_session_spoiler", session_id=session_id)
        )
        if session.has_layout_description()
        else "<p>No rdvgame attached</p>",
        "<p><a href='{link}'>Delete session</a></p>".format(
            link=request.url_for("web_api.delete_session", session_id=session_id)
        ),
        table,
    ]

    return sanic.html("\n".join(entries))


@bp.route("/session/<session_id>/rdvgame")
def download_session_spoiler(request: sanic.Request, session_id: int) -> sanic.HTTPResponse:
    session = _get_session(session_id)

    layout = session.get_layout_description_as_json()
    if layout is None:
        raise sanic.SanicException("Session does not have spoiler.", status_code=404)

    return sanic.json(layout, headers={"Content-Disposition": f"attachment; filename={session.name}.rdvgame"})


@bp.route("/world/<world_id>/rdvpreset")
def download_world_preset(request: sanic.Request, world_id: int) -> sanic.HTTPResponse:
    try:
        world = World.get_by_id(world_id)
    except World.DoesNotExist:
        raise sanic.SanicException("World does not exist.", status_code=404)

    session = _get_session(world.session_id)

    return sanic.text(
        world.preset,
        content_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={session.name} - {world.name}.rdvpreset"},
    )


@bp.route("/session/<session_id>/delete", methods=["GET", "POST"])
def delete_session(request: sanic.Request, session_id: int) -> sanic.HTTPResponse:
    if request.method == "GET":
        return sanic.html('<form method="POST"><input type="submit" value="Confirm delete"></form>')

    session = _get_session(session_id)
    session.delete_instance(recursive=True)

    return sanic.html(
        "Session deleted. <a href='{to_list}'>Return to list</a>".format(
            to_list=request.url_for("web_api.admin_sessions"),
        )
    )


def setup_app(sa: ServerApp):
    sa.app.blueprint(bp)
