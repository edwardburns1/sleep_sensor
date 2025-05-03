// Buffer sizes and parameters
#define SAMPLE_RATE 100         // Hz, adjust based on your needs
#define BUFFER_SIZE 64          // Power of 2 works best for FFT and filtering
#define MOVEMENT_THRESHOLD 100    // Adjust based on testing (using integer values)
#define CALIBRATION_SAMPLES 500 // Samples for initial calibration
#define EWMA_ALPHA 0.1          // Exponential weighted moving average parameter (0-1)
#define MEDIAN_WINDOW 5         // Size of median filter window

// Pin definitions for your specific accelerometer
#define ACCEL_X_PIN 33  // Example pin, change to match your wiring
#define ACCEL_Y_PIN A2  // Example pin, change to match your wiring
#define ACCEL_Z_PIN A3  // Example pin, change to match your wiring

// Globals
float offset_x, offset_y, offset_z;           // Calibration offsets
float noise_floor_x, noise_floor_y, noise_floor_z; // Estimated noise levels
float buffer_x[BUFFER_SIZE], buffer_y[BUFFER_SIZE], buffer_z[BUFFER_SIZE];
int buffer_pos = 0;
float ewma_x = 0, ewma_y = 0, ewma_z = 0;    // Exponential weighted moving averages
float last_filtered_x = 0, last_filtered_y = 0, last_filtered_z = 0;
bool movement_detected = false;
unsigned long last_sample_time;
void movement_setup() {
  
  // Set up analog input pins if necessary
  // For digital accelerometers using I2C/SPI, you would initialize them here
  // This assumes you're reading the values directly elsewhere
  
  // Perform initial calibration
  calibrateAccelerometer();
  
  // Initialize filters
  for (int i = 0; i < BUFFER_SIZE; i++) {
    buffer_x[i] = 0;
    buffer_y[i] = 0;
    buffer_z[i] = 0;
  }
}


void advanced_movement_detection() {
  // Read accelerometer raw integer values
  // Replace these lines with your actual method of reading the accelerometer

  // unsigned long sample_time = millis();
  // Serial.printf("Time Since last sample: %lu\n", sample_time - last_sample_time);
  // last_sample_time = sample_time;



  int raw_x = readAccelValue(ACCEL_X_PIN); // Function to read your specific accelerometer
  int raw_y = readAccelValue(ACCEL_Y_PIN);
  int raw_z = readAccelValue(ACCEL_Z_PIN);
  
  // Convert to float and apply calibration offset
  float x = (float)raw_x - offset_x;
  float y = (float)raw_y - offset_y;
  float z = (float)raw_z - offset_z;
  
  // Process the signal through our multi-stage filter pipeline
  float filtered_x, filtered_y, filtered_z;
  processSignal(x, y, z, &filtered_x, &filtered_y, &filtered_z);
  
  // Detect movement
  detectMovement(filtered_x, filtered_y, filtered_z);
  
  // Output for monitoring
  if (movement_detected) {
    Serial.print("Movement detected! Magnitude: ");
    float magnitude = sqrt(filtered_x*filtered_x + filtered_y*filtered_y + filtered_z*filtered_z);
    Serial.println(magnitude, 4);
    
    // You can also output the raw and filtered values for debugging
    Serial.print("Raw: ");
    Serial.print(raw_x); Serial.print(", ");
    Serial.print(raw_y); Serial.print(", ");
    Serial.println(raw_z);
    
    Serial.print("Filtered: ");
    Serial.print(filtered_x, 4); Serial.print(", ");
    Serial.print(filtered_y, 4); Serial.print(", ");
    Serial.println(filtered_z, 4);
  }
  
  // Maintain sample rate
  delay(1000 / SAMPLE_RATE);

}

// Function to read accelerometer values - implement this based on your specific hardware
int readAccelValue(int pin) {
  // This is a placeholder function - implement based on your specific hardware
  // For analog accelerometers:
  // return analogRead(pin);
  
  // For I2C/SPI accelerometers, you would use your specific library functions
  // This is just a placeholder that returns random data for testing
  return analogRead(pin);
}

void calibrateAccelerometer() {
  Serial.println("Calibrating accelerometer...");
  Serial.println("Keep the device still during calibration");
  
  // Variables for accumulation
  float sum_x = 0, sum_y = 0, sum_z = 0;
  float sum_x2 = 0, sum_y2 = 0, sum_z2 = 0; // For variance calculation
  
  // Collect samples
  for (int i = 0; i < CALIBRATION_SAMPLES; i++) {
    // Read raw values from accelerometer
    int raw_x = readAccelValue(ACCEL_X_PIN);
    int raw_y = readAccelValue(ACCEL_Y_PIN);
    int raw_z = readAccelValue(ACCEL_Z_PIN);
    
    sum_x += raw_x;
    sum_y += raw_y;
    sum_z += raw_z;
    
    sum_x2 += raw_x * raw_x;
    sum_y2 += raw_y * raw_y;
    sum_z2 += raw_z * raw_z;
    
    delay(20); // Short delay between samples
  }
  
  // Calculate mean (offset)
  offset_x = sum_x / CALIBRATION_SAMPLES;
  offset_y = sum_y / CALIBRATION_SAMPLES;
  offset_z = sum_z / CALIBRATION_SAMPLES;
  
  // Calculate standard deviation (noise floor estimation)
  noise_floor_x = sqrt(sum_x2 / CALIBRATION_SAMPLES - offset_x * offset_x);
  noise_floor_y = sqrt(sum_y2 / CALIBRATION_SAMPLES - offset_y * offset_y);
  noise_floor_z = sqrt(sum_z2 / CALIBRATION_SAMPLES - offset_z * offset_z);
  
  // Initialize EWMA with zeros
  ewma_x = 0;
  ewma_y = 0;
  ewma_z = 0;
  
  Serial.println("Calibration complete!");
  Serial.print("Offsets: X=");
  Serial.print(offset_x, 4);
  Serial.print(" Y=");
  Serial.print(offset_y, 4);
  Serial.print(" Z=");
  Serial.println(offset_z, 4);
  
  Serial.print("Noise floor: X=");
  Serial.print(noise_floor_x, 4);
  Serial.print(" Y=");
  Serial.print(noise_floor_y, 4);
  Serial.print(" Z=");
  Serial.println(noise_floor_z, 4);
}

void processSignal(float x, float y, float z, float *filtered_x, float *filtered_y, float *filtered_z) {
  // Stage 1: Add to circular buffer
  buffer_x[buffer_pos] = x;
  buffer_y[buffer_pos] = y;
  buffer_z[buffer_pos] = z;
  buffer_pos = (buffer_pos + 1) % BUFFER_SIZE;
  
  // Stage 2: Apply median filter (reduces impulse noise)
  float median_x = applyMedianFilter(buffer_x, buffer_pos);
  float median_y = applyMedianFilter(buffer_y, buffer_pos);
  float median_z = applyMedianFilter(buffer_z, buffer_pos);
  
  // Stage 3: Apply low-pass filter using EWMA
  ewma_x = EWMA_ALPHA * median_x + (1 - EWMA_ALPHA) * ewma_x;
  ewma_y = EWMA_ALPHA * median_y + (1 - EWMA_ALPHA) * ewma_y;
  ewma_z = EWMA_ALPHA * median_z + (1 - EWMA_ALPHA) * ewma_z;
  
  // Stage 4: High-pass filter to remove drift (subtract EWMA from median)
  // This effectively isolates changes from the baseline
  *filtered_x = median_x - ewma_x;
  *filtered_y = median_y - ewma_y;
  *filtered_z = median_z - ewma_z;
}

float applyMedianFilter(float buffer[], int current_pos) {
  // Create a temporary array for the median window
  float window[MEDIAN_WINDOW];
  
  // Fill the window with most recent samples
  for (int i = 0; i < MEDIAN_WINDOW; i++) {
    int pos = (current_pos - 1 - i);
    if (pos < 0) pos += BUFFER_SIZE;
    window[i] = buffer[pos];
  }
  
  // Simple bubble sort for the small window
  for (int i = 0; i < MEDIAN_WINDOW; i++) {
    for (int j = i + 1; j < MEDIAN_WINDOW; j++) {
      if (window[i] > window[j]) {
        float temp = window[i];
        window[i] = window[j];
        window[j] = temp;
      }
    }
  }
  
  // Return the median value
  return window[MEDIAN_WINDOW / 2];
}

void detectMovement(float x, float y, float z) {
  // Compute differences from previous values
  float dx = x - last_filtered_x;
  float dy = y - last_filtered_y;
  float dz = z - last_filtered_z;
  
  // Update last values
  last_filtered_x = x;
  last_filtered_y = y;
  last_filtered_z = z;
  
  // Calculate magnitude of change
  float change_magnitude = sqrt(dx*dx + dy*dy + dz*dz);
  
  // Adaptive threshold based on noise floor
  // Adjust the multiplier (2.5) based on sensitivity needs
  float adaptive_threshold = 2.5 * (noise_floor_x + noise_floor_y + noise_floor_z) / 3;
  adaptive_threshold = max(adaptive_threshold, float(MOVEMENT_THRESHOLD));
  
  // Simple threshold detection
  movement_detected = (change_magnitude > adaptive_threshold);
  
  // Optional: Add persistence to reduce false positives
  // This requires maintaining a count of consecutive detections
  static int detection_count = 0;
  if (change_magnitude > adaptive_threshold) {
    detection_count++;
    if (detection_count >= 3) { // Require 3 consecutive detections
      movement_detected = true;
    }
  } else {
    detection_count = 0;
    movement_detected = false;
  }
}

// Advanced Feature: FFT-based frequency analysis
// Uncomment and implement if you have enough memory on your ESP32
/*
void performFrequencyAnalysis() {
  // This would require an FFT library like arduinoFFT
  // You can isolate specific frequency bands associated with the movements you want to detect
  // and filter out frequency bands associated with noise
}
*/

// Advanced Feature: Kalman filter implementation 
// More complex but very effective for this application
/*
void applyKalmanFilter() {
  // Implement Kalman filtering for more sophisticated noise reduction
  // Particularly useful for tracking position from acceleration data
}
*/