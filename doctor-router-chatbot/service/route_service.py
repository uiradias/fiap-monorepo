import json
from pathlib import Path
from typing import List


class RouteService:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.routes = self._load_routes()

    def get_routes_summary_as_list(self) -> List[str]:
        summary_lines = []
        for route in self.routes:
            summary_lines.append(self.extract_route_summary(route))
        return summary_lines

    @staticmethod
    def extract_route_summary(route: dict) -> str:
        equip_name = route["vehicle"]
        route_id = route["id"]
        lines = [
            f"Rota {route_id} - Veículo: {equip_name} - Origem latitude: {route['src_lat']} - Origem longitude: {route['src_lng']}"]
        for loc in route["locations"]:
            lines.append(f"  - {loc['id']} (Latitude: {loc['lat']}, Longitude: {loc['lng']})")
        return "\n".join(lines)

    # -----------------
    # Private methods
    # -----------------
    def _load_routes(self):
        with open(self.file_path, "r", encoding="utf-8") as f:
            return json.load(f)
