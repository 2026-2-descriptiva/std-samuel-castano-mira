from pathlib import Path

import numpy as np
import pandas as pd

ACTIVITY_DIR = Path(__file__).resolve().parents[1]
DEADLINE_BUSINESS_DAYS = 15
WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def pregunta_01() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Una entidad pública recibe peticiones, quejas, reclamos y sugerencias
    (PQRS) por dos canales, la página web y las cartas, y la ley le da 15 días
    hábiles para responder cada una. Su tarea es medir si la entidad cumple
    ese plazo.

    Los archivos `data/historical_requests_web.csv.gz` y
    `data/historical_requests_letter.csv.gz` tienen una fila por solicitud
    recibida entre 2016 y 2021 por cada canal, con su identificador
    (`record_id`), la fecha de entrada (`in_date`), el día de la semana de
    entrada (`day_name`) y la fecha de respuesta (`out_date`). Si `out_date`
    está vacía, la solicitud todavía no ha sido respondida.

    Tenga en cuenta lo siguiente:

    - Algunas solicitudes aparecen repetidas: elimine las filas idénticas
      dentro de cada canal, para contar cada solicitud una sola vez. Las
      filas sin `record_id` son solicitudes válidas.
    - Llame `letter` al canal de las cartas y `web` al de la página web.
    - Los días hábiles de respuesta son los días de lunes a viernes
      posteriores a la fecha de entrada, hasta la fecha de respuesta
      incluida. Por ejemplo, una solicitud que entra un viernes y se responde
      el lunes siguiente tardó 1 día hábil. No considere los festivos.
    - Los días calendario de respuesta son la diferencia entre la fecha de
      respuesta y la de entrada.
    - Una solicitud cumple el plazo si fue respondida en 15 días hábiles o
      menos. Una solicitud pendiente no ha cumplido el plazo.
    - `on_time_rate` es la proporción de solicitudes que cumplen el plazo,
      sobre el total de solicitudes, incluidas las pendientes.
    - Las medianas de días se calculan solamente con las solicitudes
      respondidas.

    Genere tres archivos en `submission/`, sin el índice de Pandas y con las
    columnas en el orden indicado:

    1. `channel_summary.csv`, con una fila por canal, en orden alfabético:
       `channel`, `requests`, `answered`, `pending`,
       `median_business_days` y `on_time_rate`.

    2. `yearly_summary.csv`, con una fila por año de entrada y canal,
       ordenada por año y luego por canal: `year`, `channel`, `requests`,
       `pending` y `on_time_rate`.

    3. `entry_day_summary.csv`, con una fila por día de entrada, de lunes a
       domingo, con los dos canales juntos: `day_name`, `requests`,
       `median_calendar_days` y `median_business_days`.

    Observe en el tercer archivo cómo cambia la lectura del tiempo de
    respuesta según se cuenten días calendario o días hábiles.

    La función también debe retornar las tres tablas, en el mismo orden.

    Ejemplo del formato de `channel_summary.csv`:

        channel,requests,answered,pending,median_business_days,on_time_rate
        letter,28138,...
        ...
    """

    data_dir = ACTIVITY_DIR / "data"
    out_dir = ACTIVITY_DIR / "submission"
    out_dir.mkdir(exist_ok=True)

    frames = []
    for channel in ("letter", "web"):
        frame = pd.read_csv(
            data_dir / f"historical_requests_{channel}.csv.gz",
            parse_dates=["in_date", "out_date"],
        )
        # Filas idénticas = solicitud repetida (NaN en record_id cuenta como igual).
        frame = frame.drop_duplicates().assign(channel=channel)
        frames.append(frame)
    requests = pd.concat(frames, ignore_index=True)

    answered = requests["out_date"].notna()
    requests["calendar_days"] = (requests["out_date"] - requests["in_date"]).dt.days
    # Días hábiles: lunes a viernes después de la entrada, hasta la respuesta incluida.
    requests["business_days"] = np.nan
    requests.loc[answered, "business_days"] = np.busday_count(
        (requests.loc[answered, "in_date"] + pd.Timedelta(days=1)).values.astype(
            "datetime64[D]"
        ),
        (requests.loc[answered, "out_date"] + pd.Timedelta(days=1)).values.astype(
            "datetime64[D]"
        ),
    )
    # Pendiente (NaN) no cumple: la comparación con NaN da False.
    requests["on_time"] = requests["business_days"] <= DEADLINE_BUSINESS_DAYS
    requests["pending"] = ~answered
    requests["year"] = requests["in_date"].dt.year

    def summarize(keys):
        grouped = requests.groupby(keys)
        return pd.DataFrame(
            {
                "requests": grouped.size(),
                "answered": grouped["pending"].apply(lambda s: int((~s).sum())),
                "pending": grouped["pending"].sum().astype(int),
                "median_business_days": grouped["business_days"].median(),
                "on_time_rate": grouped["on_time"].mean(),
            }
        ).reset_index()

    channel_summary = summarize("channel")[
        [
            "channel",
            "requests",
            "answered",
            "pending",
            "median_business_days",
            "on_time_rate",
        ]
    ]
    yearly_summary = summarize(["year", "channel"])[
        ["year", "channel", "requests", "pending", "on_time_rate"]
    ].sort_values(["year", "channel"])

    grouped = requests.groupby("day_name")
    entry_day_summary = (
        pd.DataFrame(
            {
                "requests": grouped.size(),
                "median_calendar_days": grouped["calendar_days"].median(),
                "median_business_days": grouped["business_days"].median(),
            }
        )
        .reindex(WEEK)
        .reset_index()
    )

    channel_summary.round(4).to_csv(out_dir / "channel_summary.csv", index=False)
    yearly_summary.round(4).to_csv(out_dir / "yearly_summary.csv", index=False)
    entry_day_summary.round(4).to_csv(out_dir / "entry_day_summary.csv", index=False)

    return channel_summary, yearly_summary, entry_day_summary
