import requests
from fastapi import HTTPException
from app.config.settings import settings

class ThingSpeakService:
    def __init__(self):
        self.channel_id = settings.THINGSPEAK_CHANNEL_ID
        self.read_api_key = settings.THINGSPEAK_READ_API_KEY

    def get_latest_reading(self, device_id: str) -> dict:
        if not self.channel_id:
            raise HTTPException(status_code=500, detail="ThingSpeak channel ID is not configured")

        url = f"https://api.thingspeak.com/channels/{self.channel_id}/feeds/last.json"
        params = {}
        if self.read_api_key:
            params["api_key"] = self.read_api_key
            
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Map ThingSpeak fields: field1=temperature, field2=humidity, field3=current, field4=power
            def parse_float(val, name):
                if val is None or val == "":
                    raise ValueError(f"Missing or empty field for {name}")
                try:
                    return float(val)
                except ValueError:
                    raise ValueError(f"Invalid numeric value for {name}")

            return {
                "device_id": device_id,
                "thingspeak_entry_id": data.get("entry_id"),
                "temperature": parse_float(data.get("field1"), "temperature"),
                "humidity": parse_float(data.get("field2"), "humidity"),
                "current": parse_float(data.get("field3"), "current"),
                "power": parse_float(data.get("field4"), "power"),
                "timestamp": data.get("created_at")
            }
        except requests.exceptions.Timeout:
            raise HTTPException(status_code=504, detail="ThingSpeak request timed out")
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=502, detail="Unable to retrieve telemetry from ThingSpeak")
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

    def get_historical_readings(self, device_id: str, results: int = 100, start_time: str = None, end_time: str = None) -> list:
        if not self.channel_id:
            raise HTTPException(status_code=500, detail="ThingSpeak channel ID is not configured")

        url = f"https://api.thingspeak.com/channels/{self.channel_id}/feeds.json"
        params = {"results": results}
        if self.read_api_key:
            params["api_key"] = self.read_api_key
        if start_time:
            params["start"] = start_time
        if end_time:
            params["end"] = end_time
            
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            feeds = data.get("feeds", [])
            
            def parse_float_safe(val):
                if val is None or val == "":
                    return None
                try:
                    return float(val)
                except ValueError:
                    return None

            readings = []
            for feed in feeds:
                # Require all fields for a valid reading or handle missing? The prompt says "Handle API failures, missing sensor fields".
                # I'll just map missing fields to None so we don't drop the whole record if 1 field is missing, 
                # but if we want strictly parsed fields, we can do that.
                readings.append({
                    "device_id": device_id,
                    "thingspeak_entry_id": feed.get("entry_id"),
                    "temperature": parse_float_safe(feed.get("field1")),
                    "humidity": parse_float_safe(feed.get("field2")),
                    "current": parse_float_safe(feed.get("field3")),
                    "power": parse_float_safe(feed.get("field4")),
                    "timestamp": feed.get("created_at"),
                    "source": "thingspeak"
                })
            return readings
        except requests.exceptions.Timeout:
            raise HTTPException(status_code=504, detail="ThingSpeak request timed out")
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=502, detail="Unable to retrieve telemetry from ThingSpeak")

thingspeak_service = ThingSpeakService()

