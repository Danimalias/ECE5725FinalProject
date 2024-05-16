//Libraries needed
#include <Adafruit_DotStar.h>
#include <SPI.h>

// Include each of the images These are generated using genMatr.py.
#include "images/earth.h"
#include "images/soccer.h" // soccer ball 
#include "images/tennisballmapping.h"
#include "images/laughing.h"
#include "images/potato.h" // pacman 
#include "images/Cornell.h" // cornell logo 
#include "images/Rpi.h" // rpi logo 
#include "images/toy.h" // gutetama


//image struct 
typedef struct _image_metadata {
  uint8_t* data;
  int columns;
  int rows;
} image_metadata;


#define MAKEIMAGE(_name, _columns, _rows) (image_metadata){ data: (uint8_t*)&_name[0], columns: _columns, rows: _rows, } //image setup

#define NUM_IMAGES 8 //total current images
image_metadata images[NUM_IMAGES] = {
  MAKEIMAGE(IMAGE_earth, IMAGE_COLUMNS_earth, IMAGE_ROWS_earth), // earth image
  MAKEIMAGE(IMAGE_soccer, IMAGE_COLUMNS_soccer, IMAGE_ROWS_soccer), // soccer image
  MAKEIMAGE(IMAGE_tennisballmapping, IMAGE_COLUMNS_tennisballmapping, IMAGE_ROWS_tennisballmapping), // tennis ball image
  MAKEIMAGE(IMAGE_laughing, IMAGE_COLUMNS_laughing, IMAGE_ROWS_laughing), // laughing emoji image
  MAKEIMAGE(IMAGE_potato, IMAGE_COLUMNS_potato, IMAGE_ROWS_potato), // Mr.Potato head image
  MAKEIMAGE(IMAGE_Cornell, IMAGE_COLUMNS_Cornell, IMAGE_ROWS_Cornell), // Cornell logo image
  MAKEIMAGE(IMAGE_Rpi, IMAGE_COLUMNS_Rpi, IMAGE_ROWS_Rpi), // Raspberry Pi logo image
  MAKEIMAGE(IMAGE_toy, IMAGE_COLUMNS_toy, IMAGE_ROWS_toy) // Alien triplets image
   
};

// Number of LEDs in the entire strip
#define NUMPIXELS 72
// ESP32 Data pin for the DotStar strip
#define DATAPIN    14
// Clock pin for the DotStar strip
#define CLOCKPIN   32
Adafruit_DotStar strip(NUMPIXELS, DATAPIN, CLOCKPIN, DOTSTAR_BGR);

// Input pin for the Hall effect sensor
#define HALLPIN  15


// Initial LED strip brightness value
#define BRIGHTNESS 20
// Number of columns displayed in a single revolution
#define NUM_COLUMNS 72

// Time in microsecoonds after which a failed Hall effect detection turns off the LEDs
#define IDLE_TIME 1000000 // (1 sec)
// Alpha parameter for EWMA calculation of revolution time
#define ALPHA 0.5
// If defined, only show pattern on the front LED strip (rather than on both front and back)
#define FRONT_STRIP_ONLY
// If defined, flash red when the motor is spinning too fast to display all columns in one revolution
#define WARN_IF_TOO_FAST
// Static offset for shifting pixel display in X and Y dimensions
#define X_SHIFT 0
#define Y_SHIFT 0
// Y-offset in pixels for back strip versus front strip
#define BACK_OFFSET 3
// Time in microseconds to trigger next longitudinal shift in the image
#define ROTATE_INTERVAL 10000

// Initialization of the variables needed 
int started = 0;
int cur_hall = 0;
int cur_step = 0;
int cur_x_offset = 0;
uint32_t last_hall_time = 0;
uint32_t last_rotate_time = 0;
uint32_t last_clock_time = 0;
uint32_t last_button_time = 0;
uint32_t cycle_time = 0;
uint32_t per_column_time = 0;
uint32_t next_column_time = 0;

int cur_image_index; // change index value with UART
image_metadata *cur_image = &images[cur_image_index]; //current image pointer



//******************************************************************************* Helper Functions Below **************************************************************************************//


// Set all pixels to the given color.
void setAll(uint32_t color) {
  for (int i = 0; i < NUMPIXELS; i++) { //lloops through the entire LED strip length
    strip.setPixelColor(i, color); // sets color of each pixel
  }
  strip.show(); // broadcasts pixel color
}

uint32_t get_color(int x, int y) { // gets Color from the image header file
  if (x < 0 || x > cur_image->columns-1) return 0x0; // not within the dedicated columns, return no color
  if (y < 0 || y > cur_image->rows-1) return 0x0; // not within dedicated row, return no color
  int index = (y * cur_image->columns * 3) + (x * 3); // takes apart array in triplet sets representing RGB
  uint8_t* p = (uint8_t*)&cur_image->data[index]; // pointer gets pixel value according to triplet sets
  uint32_t* pv = (uint32_t*)p; // pointer to the array
  uint32_t pixel = (*pv) & 0xffffff; // pixel value from pointer
  return pixel; 
}

void doPaint(uint32_t cur_time) { // paints and broadcasts LED colors
  if (cur_time < next_column_time) { //ring not spinning
    return; // exit function
  }
  
  int x = (cur_step - X_SHIFT + cur_x_offset) % NUM_COLUMNS; // x axis of our ring, based off of offsetted values which varies with motor
  int frontx = x; //front strip labeled
  int backx = (x + (NUM_COLUMNS/2)) % NUM_COLUMNS; // backstrip labeled and will start from the LED closest to the slip ring (LED[0])

  // Front strip.
  for (int i = 0; i < NUMPIXELS/2; i++) { //loops through half of the LED strip
    int y = (NUMPIXELS/2) - i;   // Swap y-axis of the front stip according to the array of colors from image header file
    strip.setPixelColor(i, get_color(frontx, y)); // uses library to set each pixel the color of the image array/header file
  }

  // Back strip.
  for (int i = NUMPIXELS/2; i < NUMPIXELS; i++) { //loops through half of the LED strip
    int y = i - (NUMPIXELS/2) + BACK_OFFSET; // Swap y-axis of the back strip according to the array of colors from image header file
    strip.setPixelColor(i, get_color(backx, y));
  }

  strip.show(); // displays the LED colors that are now done setting 
  cur_step++; //increases current step to allow new column of pixels to be read from image file
  next_column_time = cur_time + per_column_time; // next column time updated accordingly (can be affected by motor speeds, hall effect sensor depends on motor speed)
}



//******************************************************************* SetUp and Main Loop Function Below **************************************************************************************//


void setup() {
  Serial.begin(9600); //UART baud rate, can be changed but Rpi side would need to be changed to match this value
  Serial.println("Initializing..."); // start up sequence
  
  pinMode(LED_BUILTIN, OUTPUT); // LED GPIO pin setup for ESP32 
  pinMode(HALLPIN, INPUT_PULLUP); // hall effect sensor GPIO pin setup for ESP32
  
  last_hall_time = micros(); // sets time in microseconds (10^-6)
  next_column_time = micros(); // sets time in microseconds (10^-6)

  strip.begin(); // final intialization of the LED strip
  strip.show(); // shows the LED strip color(in this case always begins with LEDs all turned off, as no color was set previously
  strip.setBrightness(BRIGHTNESS); // sets brightness of the LEDs to 20
}


void loop() { // constant loop 
  uint32_t cur_time = micros(); // current time in microseconds (10^-6)
  int hall = digitalRead(HALLPIN); // the hall pin value initially

  //UART BELOW
  if(Serial.available() >0) //constant polling of the Serial terminal
  {
    String data = Serial.readStringUntil('\n');//reading entire line sent from the Rpi
    Serial.print("You sent me: ");//retransmitting recevied message to notify the Rpi that message sent was successful
    Serial.println(data); //retransmitting received message
    if(data.equals("earth")) //different images sent from the Rpi --> default image is the Earth
    {
      cur_image_index = 0; //grab image from array of pre-made images
      Serial.println("cur_image_index =" + cur_image_index); //prints our image index as a placeholder 
    }
    if(data.equals("soccer")) //soccer ball image
    {
      cur_image_index = 1;
      Serial.println("cur_image_index =" + cur_image_index);
    }
    if(data.equals("tennis ball")) // tennis ball image
    {
      cur_image_index = 2;
      Serial.println("cur_image_index =" + cur_image_index);
    }
    if(data.equals("laughing")) // laughing emoji image
    {
      cur_image_index = 3;
      Serial.println("cur_image_index =" + cur_image_index);
    }
    if(data.equals("potato")) // Mr.Potato head image
    {
      cur_image_index = 4;
      Serial.println("cur_image_index =" + cur_image_index);
    }
    if(data.equals("cornell")) // Cornell logo image
    {
      cur_image_index = 5;
      Serial.println("cur_image_index =" + cur_image_index);
    }
    if(data.equals("rpi")) // Rpi logo image
    {
      cur_image_index = 6;
      Serial.println("cur_image_index =" + cur_image_index);
    }
    if(data.equals("toy")) // Alien Triplets from ToyStory image
    {
      cur_image_index = 7;
      Serial.println("cur_image_index =" + cur_image_index);
    }
    cur_image = &images[cur_image_index]; // sets the newly updated image from UART to the current image to display on the ring
  }

  if (hall == LOW && cur_hall == 1) { // the transition from high to low of the hall effect sensor
    if (cur_time - last_hall_time > 10000) {  // Debounce.     
      cur_hall = 0; // current hall value is low
      cur_step = 0; // Reset cycle of spinning
      // Estimates timing of the braodcasting of the LEDs to take into account of the irregularities of the motor spinning by conditioning on the hall effect sensor values
      cycle_time = (ALPHA * cycle_time) + ((1.0 - ALPHA) * (cur_time - last_hall_time)); //EWMA Calculation~:) uses a weighted estimate to generate a "accurate" prediction of cycle time
      per_column_time = (cycle_time / NUM_COLUMNS); // uses predicted cycle time to estimate column time
      next_column_time = cur_time - per_column_time; // uses predicted cycle time to estimate next column time
      last_hall_time = cur_time;
    
      #ifdef ROTATE_INTERVAL
      if (cur_time - last_rotate_time > ROTATE_INTERVAL) {
        last_rotate_time = cur_time;
      }
#endif
    }
  } else if (hall == HIGH && cur_hall == 0) { // transition of 1 revolution
    cur_hall = 1; // updates cur_hall to be high as hall's digital read is HIGH
#ifdef HALLDEBUG
    setAll(0x0); // debug when hall effect not sensed, turns off all LEDs
#endif
  }
#ifndef HALLDEBUG
  if (cur_time - last_hall_time < IDLE_TIME) { //when the hall effect sensor is detected within 1 second, need to display image
    doPaint(cur_time); // paints LEDs based on current time
  } else {
    setAll(0x0); // paints all LEDs to be off
  }
#endif

}
