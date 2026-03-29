from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.services import PoliceSystem


web = Blueprint("web", __name__)


def get_service() -> PoliceSystem:
    return PoliceSystem()


def _redirect_back(endpoint: str) -> str:
    return request.form.get("next") or url_for(endpoint)


@web.get("/")
def index():
    service = get_service()
    return render_template("index.html", state=service.get_dashboard_state())


@web.get("/citizens")
def citizens():
    service = get_service()
    return render_template(
        "citizens.html",
        citizens=service.list_citizens(),
        zones=sorted(service.police.zones.keys()),
    )


@web.post("/citizens")
def add_citizen():
    service = get_service()
    zone = request.form.get("zone") or None
    result = service.add_citizen(request.form.get("name", ""), zone=zone)
    service.save_data()
    flash(result.message, "success" if result.ok else "error")
    return redirect(_redirect_back("web.citizens"))


@web.post("/citizens/<int:index>/delete")
def delete_citizen(index: int):
    service = get_service()
    result = service.delete_citizen(index)
    service.save_data()
    flash(result.message, "success" if result.ok else "error")
    return redirect(_redirect_back("web.citizens"))


@web.get("/police")
def police():
    service = get_service()
    return render_template(
        "police.html",
        policemen=service.list_policemen(),
        zones=service.get_zone_info(),
        zone_names=sorted(service.police.zones.keys()),
    )


@web.post("/zones")
def add_zone():
    service = get_service()
    result = service.add_zone(request.form.get("zone", ""))
    service.save_data()
    flash(result.message, "success" if result.ok else "error")
    return redirect(_redirect_back("web.police"))


@web.post("/policemen")
def hire_policeman():
    service = get_service()
    result = service.hire_policeman(
        request.form.get("lastname", ""),
        request.form.get("zone", ""),
    )
    service.save_data()
    flash(result.message, "success" if result.ok else "error")
    return redirect(_redirect_back("web.police"))


@web.post("/policemen/fire")
def fire_policeman():
    service = get_service()
    result = service.fire_policeman(request.form.get("lastname", ""))
    service.save_data()
    flash(result.message, "success" if result.ok else "error")
    return redirect(_redirect_back("web.police"))


@web.post("/policemen/relocate")
def relocate_policemen():
    service = get_service()
    raw_indexes = request.form.get("indexes", "").strip()
    try:
        indexes = [int(value) for value in raw_indexes.split() if value]
    except ValueError:
        flash("Indexes must be integers separated by spaces", "error")
        return redirect(_redirect_back("web.police"))

    result = service.relocate_policemen(indexes, request.form.get("target_zone", ""))
    service.save_data()
    flash(result.message, "success" if result.ok else "error")
    return redirect(_redirect_back("web.police"))


@web.post("/policemen/recover")
def recover_policemen():
    service = get_service()
    result = service.recover_policemen()
    service.save_data()
    flash(result.message, "success" if result.ok else "error")
    return redirect(_redirect_back("web.police"))


@web.get("/statements")
def statements():
    service = get_service()
    return render_template(
        "statements.html",
        statements=service.list_statements(),
        citizens=service.list_citizens(),
        laws=service.list_laws(),
        zones=sorted(service.police.zones.keys()),
    )


@web.post("/statements")
def add_statement():
    service = get_service()
    try:
        suspect_idx = int(request.form.get("suspect_idx", "-1"))
        law_idx = int(request.form.get("law_idx", "-1"))
    except ValueError:
        flash("Suspect and law indexes must be integers", "error")
        return redirect(_redirect_back("web.statements"))

    result = service.create_statement(
        request.form.get("description", ""),
        request.form.get("zone", ""),
        suspect_idx,
        law_idx,
    )
    service.save_data()
    flash(result.message, "success" if result.ok else "error")
    return redirect(_redirect_back("web.statements"))


@web.post("/statements/<int:index>/delete")
def delete_statement(index: int):
    service = get_service()
    result = service.delete_statement(index)
    service.save_data()
    flash(result.message, "success" if result.ok else "error")
    return redirect(_redirect_back("web.statements"))


@web.get("/laws")
def laws():
    service = get_service()
    return render_template("laws.html", laws=service.list_laws())


@web.post("/laws")
def add_law():
    service = get_service()
    try:
        article = int(request.form.get("article", "0"))
        severity = int(request.form.get("severity", "1"))
    except ValueError:
        flash("Article and severity must be integers", "error")
        return redirect(_redirect_back("web.laws"))

    result = service.add_law(article, severity, request.form.get("desc", ""))
    service.save_data()
    flash(result.message, "success" if result.ok else "error")
    return redirect(_redirect_back("web.laws"))


@web.get("/investigation")
def investigation():
    service = get_service()
    return render_template(
        "investigation.html",
        statements=service.list_statements(),
        policemen=service.list_policemen(),
        zone_info=service.get_zone_info(),
    )


@web.post("/investigation")
def run_investigation():
    service = get_service()
    do_arrest = request.form.get("mode") == "investigate_and_arrest"
    result = service.investigate_crimes(do_arrest=do_arrest)
    service.save_data()
    flash(result.message, "success" if result.ok else "error")
    if result.details:
        for detail in result.details:
            flash(detail, "info")
    return redirect(_redirect_back("web.investigation"))


@web.post("/arrests")
def run_arrests():
    service = get_service()
    result = service.arrest_criminals()
    service.save_data()
    flash(result.message, "success" if result.ok else "error")
    for detail in result.details:
        flash(detail, "info")
    return redirect(_redirect_back("web.investigation"))


@web.get("/history")
def history():
    service = get_service()
    return render_template("history.html", history=service.list_history())


@web.post("/history/clear")
def clear_history():
    service = get_service()
    result = service.clear_history()
    service.save_data()
    flash(result.message, "success" if result.ok else "error")
    return redirect(_redirect_back("web.history"))
