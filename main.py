import os.path
import csv
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, date
from enum import Enum
import uvicorn
app = FastAPI()

parent_data_dir = "/home/edward/Projects/school/ece284/sleep_data"
data_dir = ""
class SleepEvent(Enum):
    LIGHT = 0
    SOUND = 1
    MOVEMENT = 2

class SensorData(BaseModel):
    temperature: float
    humidity: float
    heat_index: float
    light: int
    sound: int

class SleepEventData(BaseModel):
    sleepEvent: int

@app.post("/sensorData")
async def receive_temp(data: SensorData):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] Temp: {data.temperature} °C | Humidity: {data.humidity} %")

    file_path = f"{data_dir}/sensor_data_log.csv"
    write_header = not os.path.exists(file_path)

    with open(file_path, mode="a", newline="") as file:
        writer = csv.writer(file)
        if write_header:
            writer.writerow(["timestamp", "temperature", "humidity", "heat_index", "light", "sound"])
        writer.writerow([now, data.temperature, data.humidity, data.heat_index, data.light, data.sound])
    return {"status": "success"}



@app.post("/sleepEvent")
async def receive_sleep_event(data: SleepEventData):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    event = SleepEvent(data.sleepEvent)
    print(f"[{now}] Sleep Event: {event.name} %")

    file_path = f"{data_dir}/sleep_event_log.csv"
    write_header = not os.path.exists(file_path)

    with open(file_path, mode="a", newline="") as file:
        writer = csv.writer(file)
        if write_header:
            writer.writerow(["timestamp", "sleep_event"])
        writer.writerow([now, event.name])
    return {"status": "success"}

@app.post("/groundTruth")
async def receive_ground_truth():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Ground Truth Sleep time: {now}")

    file_path = f"{data_dir}/ground_truth_log.csv"
    write_header = not os.path.exists(file_path)

    with open(file_path, mode="a", newline="") as file:
        writer = csv.writer(file)
        if write_header:
            writer.writerow(["timestamp"])
        writer.writerow([now])
    return {"status": "success"}

if __name__ == "__main__":
    print(date.today())
    data_dir = f"{parent_data_dir}/{date.today()}"
    if not os.path.exists(data_dir):
        os.mkdir(data_dir)


    uvicorn.run(app, host="0.0.0.0", port=6543)
