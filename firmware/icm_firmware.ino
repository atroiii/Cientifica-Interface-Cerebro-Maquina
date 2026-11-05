// =============================================================================
// FIRMWARE DA MÃO ROBÓTICA (Arduino)
//
// Passo a passo:
//   1. setup: abre a serial a 9600 bps (ligada ao HC-05) e põe os 5 servos
//      em 0 grau, que é a postura B (neutro).
//   2. loop: se chegou um byte, lê o caractere e aplica a postura dele.
//
// Entrada: um caractere pela serial ('A' a 'E', ou 'T' no ensaio 2).
// Saída: ângulo dos 5 servos; no caso 'T', um 'T' de volta pela serial.
// =============================================================================
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

    // O PC manda UM caractere por comando. O switch escolhe a postura.
    // A a E: cada letra é um gesto (A distração, B neutro, C foco leve,
    // D foco alto, E foco máximo). Cada servo recebe 0 ou 180 graus.
    // O PC envia o gesto a cada pacote (~1 por segundo), mesmo repetido.
    // Repetir a mesma letra reescreve os mesmos ângulos: a mão não se mexe.
    // Qualquer outro caractere cai no default e é ignorado.
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

      case 'T':
        // Ensaio de latência (ensaios/ensaio2_latencia.py): eco sem mover servos
        // O PC manda 'T' e cronometra até o 'T' voltar (RTT).
        // A resposta sai logo após a leitura, antes de qualquer servo.
        // Por isso o eco mede só o ENLACE (PC ↔ HC-05 ↔ Arduino), não a
        // latência total: ficam de fora o headset, o filtro e o giro dos
        // servos.
        Serial.write('T');
        break;

      default:
        
        break;
    }
  }
}