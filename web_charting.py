import os.path
import csv
from fastapi import FastAPI
import uvicorn
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles


app = FastAPI()
# app.mount("/", StaticFiles(directory="static", html=True), name="static")


@app.get("/", response_class=HTMLResponse)
def get_index() -> HTMLResponse:
    with open("static/index.html") as html:
        return HTMLResponse(content=html.read())
@app.get("/sensorData")
async def get_sensor_data():
    file_path = f"sleep_data/2025-05-02/sensor_data_log.csv"
    if not os.path.exists(file_path):
        return JSONResponse(content={"error": "No data found."}, status_code=404)

    with open(file_path, mode="r") as file:
        reader = csv.DictReader(file)
        data = [row for row in reader]
    print(data)
    return data

@app.get("/sleepEvents")
async def get_sleep_events():
    file_path = f"sleep_data/2025-05-02/sleep_event_log.csv"
    if not os.path.exists(file_path):
        return JSONResponse(content={"error": "No sleep events found."}, status_code=404)

    with open(file_path, mode="r") as file:
        reader = csv.DictReader(file)
        data = [row for row in reader]
    return data


if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=7777)
