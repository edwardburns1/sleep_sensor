import os.path
import csv
from datetime import date

from fastapi import FastAPI, Query
import uvicorn
from fastapi.responses import JSONResponse, HTMLResponse


app = FastAPI()


@app.get("/", response_class=HTMLResponse)
def get_index() -> HTMLResponse:
    with open("static/index.html") as html:
        return HTMLResponse(content=html.read())

@app.get("/sensorData")
async def get_sensor_data(night: str = Query(default=str(date.today()))):
    file_path = f"sleep_data/{night}/sensor_data_log.csv"
    if not os.path.exists(file_path):
        return JSONResponse(content={"error": f"No data found for {night}."}, status_code=404)

    with open(file_path, mode="r") as file:
        reader = csv.DictReader(file)
        data = [row for row in reader]
    return data

@app.get("/sleepEvents")
async def get_sleep_events(night: str = Query(default=str(date.today()))):
    file_path = f"sleep_data/{night}/sleep_event_log.csv"
    if not os.path.exists(file_path):
        return JSONResponse(content={"error": "No sleep events found."}, status_code=404)

    with open(file_path, mode="r") as file:
        reader = csv.DictReader(file)
        data = [row for row in reader]
    return data

@app.get("/groundTruth")
async def get_ground_truth(night: str = Query(default=str(date.today()))):
    file_path = f"sleep_data/{night}/ground_truth_log.csv"
    if not os.path.exists(file_path):
        return JSONResponse(content={"error": "No ground truth found."}, status_code=404)

    with open(file_path, mode="r") as file:
        reader = csv.DictReader(file)
        data = [row for row in reader]
    return data
@app.get("/availableNights")
async def get_available_nights():
    return [name for name in os.listdir("sleep_data") if os.path.isdir(os.path.join("sleep_data", name))]

@app.get("/journal")
async def get_journal(night: str):
    file_path = f"sleep_data/{night}/journal.txt"
    if not os.path.exists(file_path):
        return JSONResponse(content={"error": "No journal found."}, status_code=404)
    with open(file_path, mode='r') as file:
        return file.read().replace('\n', ' ')

@app.get("/melatonin")
async def get_melatonin(night: str):
    file_path = f"sleep_data/{night}/journal.txt"
    if not os.path.exists(file_path):
        return JSONResponse(content={"error": "No journal found."}, status_code=404)
    with open(file_path, mode='r') as file:
        content = file.read()
        if "melatonin" in content:
            return True
        return False

if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=7777)
