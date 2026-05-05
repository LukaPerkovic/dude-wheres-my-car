from pathlib import Path


class LocalReservationWriter:
    def __init__(self, output_path: str) -> None:
        self.path = Path(output_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _clean(value: str) -> str:
        return str(value).replace("\n", " ").replace("\r", " ").replace("|", "/").strip()

    def write_reservation(
        self,
        *,
        name: str,
        vehicle_number: str,
        period: str,
        approval_time: str,
    ) -> None:
        line = (
            f"{self._clean(name)} | "
            f"{self._clean(vehicle_number)} | "
            f"{self._clean(period)} | "
            f"{self._clean(approval_time)}\n"
        )

        with self.path.open("a", encoding="utf-8") as f:
            f.write(line)