#include "DHT.h"
#include "WiFi.h"
#define DHTPIN 21     // Digital pin connected to the DHT sensor
#define DHTTYPE DHT11   // DHT 11
#include <HTTPClient.h>

int photoPin = 32;

int accelX = 33;
int accelY = A2;
int accelZ = A3;

int audio_pin = A4;
int buttonPin = 23;

//Home wifi
const char* ssid = "SpectrumSetup-E0";
const char* serverName = "http://192.168.1.145:6543/";
const char* password = "REDACTED";


DHT dht(DHTPIN, DHTTYPE);

typedef enum {LIGHT, SOUND, MOVEMENT} SleepEvent;
#define DEBOUNCE_TIME 3000


#define BUFFER_SIZE 100  // Change size as needed

typedef struct {
    int buffer[BUFFER_SIZE];
    int head = 0;
    int tail = 0;
    int count = 0;
} CircularBuffer;

void setup() {
  Serial.begin(115200);
  delay(1000);
  pinMode(buttonPin, INPUT);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  Serial.print("\nConnecting");
  while(WiFi.status() != WL_CONNECTED){
    Serial.print(".");
    delay(100);
  }
  Serial.println(" Connected!");
  // movement_setup();

  dht.begin();
  delay(10000);
}

void loop() {

  // int photo_val = analogRead(photoPin);

  // // int x = analogRead(accelX);
  // // int y = analogRead(accelY);
  // // int z = analogRead(accelZ);

  // int audio = analogRead(audio_pin);


  // TODO: Add debounce to detectors
  // Serial.printf("Light: %d, x: %d, y: %d, z: %d, Audio: %d\n", photo_val, x, y, z, audio);

  button_detection();
  int avg_sound = sound_detection();
  int avg_light = light_detection();
  // advanced_movement_detection();
  movement_detection();
  data_handler(avg_light, avg_sound);




  delay(10);

}

unsigned long buttonDebounceTime = 0;
void button_detection(){
  int buttonVal = digitalRead(buttonPin);
  if(buttonVal == HIGH && millis() - buttonDebounceTime > DEBOUNCE_TIME){
    Serial.println("Button Pressed");
    sendGroundTruth();
    buttonDebounceTime = millis();
  }
}
void sendPostData(String jsonPayload, String endpoint){
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;

    http.begin(serverName + endpoint);
    http.addHeader("Content-Type", "application/json");


    int httpResponseCode = http.POST(jsonPayload);

    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("Server response: " + response);
    } else {
      Serial.print("Error in POST: ");
      Serial.println(httpResponseCode);
    }

    http.end();
  } else {
    Serial.println("WiFi Disconnected");
  }
}
void sendSensorData(float temperature, float humidity, float heat_index, int light, int sound) {
      // Create JSON payload

    String jsonPayload = "{\"temperature\": " + String(temperature, 2) +
                         ", \"humidity\": " + String(humidity, 2) +
                         ", \"heat_index\": " + String(heat_index, 2) +
                         ", \"light\": " + String(light) +
                         ", \"sound\": " + String(sound) +"}";
    sendPostData(jsonPayload, "sensorData");
}

void sendSleepEvent(SleepEvent event){
  String jsonPayload = "{\"sleepEvent\": " + String(event) + "}";
  sendPostData(jsonPayload, "sleepEvent");
}

void sendGroundTruth(){
  sendPostData("", "groundTruth");
}
#define SOUND_WINDOW_L 100
int sound_window[SOUND_WINDOW_L];
int sound_i = 0;

int sound_setup = SOUND_WINDOW_L;
bool sound_debounce = false;
unsigned long soundDebounceTime = 0;
int sound_detection(){
  int audio = analogRead(audio_pin);

  if(sound_setup){
    sound_window[sound_i] = audio;
    sound_i = (sound_i + 1) % SOUND_WINDOW_L;
    sound_setup -= 1;
    return 0;
  }

  int rolling_avg = get_rolling_avg(SOUND_WINDOW_L, sound_window);
  if(audio > rolling_avg + 300 && (millis() - soundDebounceTime > DEBOUNCE_TIME)){
    Serial.println("Sound Detected!");
    sendSleepEvent(SOUND);
    soundDebounceTime = millis();
  }
  sound_window[sound_i] = audio;
  sound_i = (sound_i + 1) % SOUND_WINDOW_L;
  return rolling_avg;
}

#define LIGHT_WINDOW_L 100
int light_window[LIGHT_WINDOW_L];
int light_i = 0;

int light_setup = LIGHT_WINDOW_L;
unsigned long lightDebounceTime = 0;

int prev_rolling_avg = 0;
int last_avg_sample;
int last_avg_sample_time = 0;

const int AVG_SAMPLE_INTERVAL = 1000;
// CircularBuffer light_avgs;
int light_detection(){
  int photo_val = analogRead(photoPin);
  if(light_setup){
    light_window[light_i] = photo_val;
    light_i = (light_i + 1) % LIGHT_WINDOW_L;
    light_setup -= 1;
    return 0;
  }

  int rolling_avg = get_rolling_avg(LIGHT_WINDOW_L, light_window);

  // cb_enqueue(&light_avgs, rolling_avg);
  // bool light_on = (photo_val > rolling_avg + 50) && (photo_val > 100);
  // bool light_off = (photo_val < rolling_avg - 50) && (photo_val < 50);

  bool light_event = false;
  if(millis() - last_avg_sample_time > AVG_SAMPLE_INTERVAL){
    if(abs(last_avg_sample - rolling_avg) > 10){
      last_avg_sample = rolling_avg;
      last_avg_sample_time = millis();
    }
  }

  int delta = rolling_avg - last_avg_sample;
  // Serial.printf("%d, %d, %d\n", photo_val, rolling_avg, delta);
  if(abs(delta) > 15 && (millis() - lightDebounceTime > DEBOUNCE_TIME)){
    Serial.println("Light Change Detected!");
    sendSleepEvent(LIGHT);
    lightDebounceTime = millis();
  }
  prev_rolling_avg = rolling_avg;

  light_window[light_i] = photo_val;
  light_i = (light_i + 1) % LIGHT_WINDOW_L;
  return rolling_avg;
}




#define MOVEMENT_WINDOW_L 1000
int movement_window[MOVEMENT_WINDOW_L];
int move_i = 0;

int move_setup = MOVEMENT_WINDOW_L;

unsigned long movementDebounceTime = 0;

void movement_detection(){
  int x = analogRead(accelX);
  int y = analogRead(accelY);
  int z = analogRead(accelZ);
  int sum = x + y + z;
  if(move_setup){
    movement_window[move_i] = sum;
    move_i = (move_i + 1) % MOVEMENT_WINDOW_L;
    move_setup -= 1;
    return;
  }

  int rolling_avg = get_rolling_avg(MOVEMENT_WINDOW_L, movement_window);
  if(sum > rolling_avg + 200 && millis() - movementDebounceTime > DEBOUNCE_TIME){
    Serial.println("Movement Detected!");
    sendSleepEvent(MOVEMENT);
    movementDebounceTime = millis();
  }
  movement_window[move_i] = sum;
  move_i = (move_i + 1) % MOVEMENT_WINDOW_L;
}


int get_rolling_avg(int n, int * window){
  int avg = 0;
  for(int i = 0; i < n; i++){
    avg += window[i];
  }
  return avg / n;
}

#define DATA_INTERVAL  60 * 1000
unsigned long lastDataTime = 0;
void data_handler(int light, int sound){

  int fail_count = 0;
  if(millis() - lastDataTime > DATA_INTERVAL){

    while(fail_count < 10){
      float h = dht.readHumidity();
      // Read temperature as Celsius (the default)
      float f = dht.readTemperature(true);

      float hif = dht.computeHeatIndex(f, h);

      if(isnan(h) || isnan(f)) {
        fail_count++;
        delay(3000);
        continue;
      }

      Serial.printf("Sending Sensor Data, Humidity: %f, Temp: %f\n", h, f);
      sendSensorData(f, h, hif, light, sound);

      lastDataTime = millis();
      return;
    }
  }
}


// void temp_handler(){
//   if(millis() - lastTempTime > TEMP_INTERVAL){
//     float h = dht.readHumidity();
//     // Read temperature as Celsius (the default)
//     float f = dht.readTemperature(true);

//     float hif = dht.computeHeatIndex(f, h);

//     sendTemperature(f, h);

//     lastTempTime = millis();
//   }
// }

void temp_stuff(){
    // Reading temperature or humidity takes about 250 milliseconds!
  // Sensor readings may also be up to 2 seconds 'old' (its a very slow sensor)
  float h = dht.readHumidity();
  // Read temperature as Celsius (the default)
  float t = dht.readTemperature();
  // Read temperature as Fahrenheit (isFahrenheit = true)
  float f = dht.readTemperature(true);

  // Check if any reads failed and exit early (to try again).
  if (isnan(h) || isnan(t) || isnan(f)) {
    Serial.println(F("Failed to read from DHT sensor!"));
    return;
  }

  // Compute heat index in Fahrenheit (the default)
  float hif = dht.computeHeatIndex(f, h);
  // Compute heat index in Celsius (isFahreheit = false)
  float hic = dht.computeHeatIndex(t, h, false);

  Serial.print(F("Humidity: "));
  Serial.print(h);
  Serial.print(F("%  Temperature: "));
  Serial.print(t);
  Serial.print(F("C "));
  Serial.print(f);
  Serial.print(F("F  Heat index: "));
  Serial.print(hic);
  Serial.print(F("C "));
  Serial.print(hif);
  Serial.println(F("F"));
}