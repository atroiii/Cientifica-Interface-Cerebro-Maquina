#include <Servo.h>

// Criação dos objetos para os 5 servos
Servo polegar;
Servo indicador;
Servo medio;
Servo anelar;
Servo minimo;

void setup() {
  Serial.begin(9600);
  polegar.attach(3);
  indicador.attach(5);
  medio.attach(6);
  anelar.attach(9);
  minimo.attach(10);
  
    polegar.write(0);
    indicador.write(0);
    medio.write(0);
    anelar.write(0);
    minimo.write(0);

}

void loop() {
  if (Serial.available() > 0) {
    char comando = Serial.read();

    switch (comando) {
      case 'A':
        // Posição A 
        polegar.write(180);
        indicador.write(180);
        medio.write(0);
        anelar.write(0);
        minimo.write(0);
        break;
        
      case 'B':
        // Posição B 
        polegar.write(0);
        indicador.write(0);
        medio.write(0);
        anelar.write(0);
        minimo.write(0);
        break;
        
      case 'C':
        // Posição C 
        polegar.write(180);
        indicador.write(180);
        medio.write(180);
        anelar.write(180);
        minimo.write(180);
        break;
        
      case 'D':
        // Posição D
        polegar.write(0);
        indicador.write(0);
        medio.write(0);
        anelar.write(180);
        minimo.write(180);
        break;
        
      case 'E':
        // Posição E
        polegar.write(0);
        indicador.write(0);
        medio.write(180);
        anelar.write(180);
        minimo.write(0);
        break;
        
      default:
        
        break;
    }
  }
}