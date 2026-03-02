from django.db import connection, transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

DELTA_STATE_ID = 25

def dictfetchall(cursor):
    cols = [col[0] for col in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]

def home(request):
    return render(request, "results/home.html")

def polling_unit_results(request):
    selected_pu = request.GET.get("pu")
    pu_results = []
    pu_info = None

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT p.uniqueid, COALESCE(p.polling_unit_name,'(Unnamed PU)') AS polling_unit_name
            FROM polling_unit p
            INNER JOIN lga l ON l.lga_id = p.lga_id
            WHERE l.state_id = %s
            ORDER BY polling_unit_name ASC
                """,
            [DELTA_STATE_ID],
        )
        polling_units = dictfetchall(cursor)

        if selected_pu:
            cursor.execute(
                """
                SELECT p.uniqueid, p.polling_unit_name, p.lga_id, p.ward_id
                FROM polling_unit p
                INNER JOIN lga l ON l.lga_id = p.lga_id
                WHERE p.uniqueid = %s AND l.state_id = %s
                """,
                [selected_pu, DELTA_STATE_ID],
            )
            pu_info = cursor.fetchone()

            cursor.execute(
                """
                SELECT party_abbreviation, party_score
                FROM announced_pu_results
                WHERE polling_unit_uniqueid = %s
                ORDER BY party_abbreviation
                """,
                [selected_pu],
            )
            pu_results = dictfetchall(cursor)

    return render(
        request,
        "results/q1_polling_unit.html",
        {
            "polling_units": polling_units,
            "selected_pu": selected_pu,
            "pu_info": pu_info,
            "pu_results": pu_results,
        },
    )

def lga_summary(request):
    selected_lga = request.GET.get("lga")
    summed = []
    announced = []
    lga_name = None

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT lga_id, lga_name
            FROM lga
            WHERE state_id = %s
            ORDER BY lga_name ASC
            """,
            [DELTA_STATE_ID],
        )
        lgas = dictfetchall(cursor)

        if selected_lga:
            cursor.execute(
                """
                SELECT r.party_abbreviation, SUM(r.party_score) AS total_score
                FROM announced_pu_results r
                INNER JOIN polling_unit p ON p.uniqueid = r.polling_unit_uniqueid
                INNER JOIN lga l ON l.lga_id = p.lga_id
                WHERE p.lga_id = %s AND l.state_id = %s
                GROUP BY r.party_abbreviation
                ORDER BY r.party_abbreviation
                """,
                [selected_lga, DELTA_STATE_ID],
            )
            summed = dictfetchall(cursor)

            cursor.execute(
                """
                SELECT lga_name
                FROM lga
                WHERE lga_id = %s AND state_id = %s
                LIMIT 1
                """,
                [selected_lga, DELTA_STATE_ID],
            )
            row = cursor.fetchone()
            lga_name = row[0] if row else None

            if lga_name:
                cursor.execute(
                    """
                    SELECT party_abbreviation, party_score
                    FROM announced_lga_results
                    WHERE lga_name = %s
                    ORDER BY party_abbreviation
                    """,
                    [lga_name],
                )
                announced = dictfetchall(cursor)

    return render(
        request,
        "results/q2_lga_summary.html",
        {
            "lgas": lgas,
            "selected_lga": selected_lga,
            "summed": summed,
            "announced": announced,
            "lga_name": lga_name,
        },
    )

def new_polling_unit(request):
    context = {"state_id": DELTA_STATE_ID, "success": False, "error": None}

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT DISTINCT party_abbreviation
            FROM announced_pu_results
            ORDER BY party_abbreviation
            """
        )
        context["parties"] = [r[0] for r in cursor.fetchall()]

        cursor.execute(
            """
            SELECT lga_id, lga_name
            FROM lga
            WHERE state_id=%s
            ORDER BY lga_name
            """,
            [DELTA_STATE_ID],
        )
        context["lgas"] = dictfetchall(cursor)

    if request.method == "POST":
        polling_unit_name = (request.POST.get("polling_unit_name") or "").strip()
        lga_id = request.POST.get("lga_id")
        ward_id = request.POST.get("ward_id")

        party_scores = {
            k.replace("party_score_", ""): v
            for k, v in request.POST.items()
            if k.startswith("party_score_")
        }

        try:
            if not polling_unit_name:
                raise ValueError("Polling unit name is required.")
            if not lga_id or not ward_id:
                raise ValueError("LGA and Ward are required.")

            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM lga WHERE lga_id=%s AND state_id=%s",
                    [lga_id, DELTA_STATE_ID],
                )
                if cursor.fetchone() is None:
                    raise ValueError("Invalid LGA (must be in Delta State).")

            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("SELECT COALESCE(MAX(uniqueid), 0) + 1 FROM polling_unit")
                    new_pu_uniqueid = cursor.fetchone()[0]

                    cursor.execute(
                        """
                        INSERT INTO polling_unit (uniqueid, polling_unit_name, ward_id, lga_id)
                        VALUES (%s, %s, %s, %s)
                        """,
                        [new_pu_uniqueid, polling_unit_name, ward_id, lga_id],
                    )

                    cursor.execute("SELECT COALESCE(MAX(result_id), 0) FROM announced_pu_results")
                    next_result_id = (cursor.fetchone()[0] or 0) + 1

                    inserted = 0
                    for party, score in party_scores.items():
                        if score is None or str(score).strip() == "":
                            continue
                        score_int = int(score)
                        cursor.execute(
                            """
                            INSERT INTO announced_pu_results
                                (result_id, polling_unit_uniqueid, party_abbreviation, party_score,
                                 entered_by_user, date_entered, user_ip_address)
                            VALUES
                                (%s, %s, %s, %s, %s, %s, %s)
                            """,
                            [
                                next_result_id,
                                new_pu_uniqueid,
                                party,
                                score_int,
                                "django_user",
                                timezone.now(),
                                request.META.get("REMOTE_ADDR", ""),
                            ],
                        )
                        next_result_id += 1
                        inserted += 1

                    if inserted == 0:
                        raise ValueError("No party scores were provided. Enter at least one score.")

            context["success"] = True

        except Exception as e:
            context["error"] = str(e)

    return render(request, "results/q3_new_polling_unit.html", context)

def api_lgas(request):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT lga_id, lga_name
            FROM lga
            WHERE state_id=%s
            ORDER BY lga_name
            """,
            [DELTA_STATE_ID],
        )
        data = [{"id": r[0], "name": r[1]} for r in cursor.fetchall()]
    return JsonResponse({"lgas": data})

def api_wards(request):
    lga_id = request.GET.get("lga_id")
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT ward_id, ward_name
            FROM ward
            WHERE lga_id=%s
            ORDER BY ward_name
            """,
            [lga_id],
        )
        data = [{"id": r[0], "name": r[1]} for r in cursor.fetchall()]
    return JsonResponse({"wards": data})

def api_polling_units(request):
    ward_id = request.GET.get("ward_id")
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT p.uniqueid, COALESCE(p.polling_unit_name,'(Unnamed PU)') AS polling_unit_name
            FROM polling_unit p
            INNER JOIN lga l ON l.lga_id = p.lga_id
            WHERE p.ward_id=%s AND l.state_id=%s
            ORDER BY polling_unit_name
            """,
            [ward_id, DELTA_STATE_ID],
        )
        data = [{"id": r[0], "name": r[1]} for r in cursor.fetchall()]
    return JsonResponse({"polling_units": data})
