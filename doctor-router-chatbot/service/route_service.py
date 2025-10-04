import json
from pathlib import Path

class RouteService:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.routes = self._load_routes()

    def get_routes_summary(self) -> str:
        """Transforms the routes into a summary string."""
        summary_lines = []
        for route in self.routes:
            summary_lines.append(self.extract_route_summary(route))
        return "\n".join(summary_lines)

    @staticmethod
    def extract_route_summary(route: dict) -> str:
        """Gera resumo textual de uma rota específica"""
        equip_name = route["equipment"]["name"]
        driver_key = route["driver"]["key"]
        route_id = route["id"]
        lines = [f"Rota {route_id} - Veículo: {equip_name} - Motorista: {driver_key}"]
        for stop in route["stops"]:
            loc = stop["location"]
            lines.append(f"  - {loc['name']} (Lat: {loc['latitude']}, Lon: {loc['longitude']})")
        return "\n".join(lines)

    # -----------------
    # Private methods
    # -----------------
    def _load_routes(self):
        with open(self.file_path, "r", encoding="utf-8") as f:
            return json.load(f).get("routes", [])
