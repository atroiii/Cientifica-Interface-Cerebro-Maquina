# Interface Cérebro-Máquina de baixo custo

Interface cérebro-máquina (ICM) de baixo custo que controla uma mão robótica a partir do
**índice de atenção** do headset EEG **BrainLink** (Macrotellect).

Como funciona:

1. O BrainLink envia os pacotes EEG via Bluetooth (porta serial, 57600 bps).
2. O SDK `BrainLinkParser` decodifica o índice de atenção (0–100).
3. A atenção passa por um **filtro EMA** (média móvel exponencial) com **alpha = 0,50**.
4. Uma **máquina de estados com trava** converte a atenção filtrada em um dos estados **A–E**.
   Depois de um foco alto (D ou E), uma queda de atenção leva ao estado neutro **B** e trava
   o sistema, evitando que a mão passe direto para o estado de distração.
5. O estado (um caractere `A`–`E`) é enviado ao **Arduino** pelo módulo Bluetooth **HC-05**
   (9600 bps), que posiciona os cinco servos dos dedos.
6. Uma interface gráfica (CustomTkinter + Matplotlib) mostra a atenção filtrada, o histórico e o
   estado atual em tempo real.

| Estado | Significado  |
|--------|--------------|
| A      | Distração    |
| B      | Neutro       |
| C      | Foco leve    |
| D      | Foco alto    |
| E      | Foco máximo  |

## Requisitos

- **Windows** (o SDK do BrainLink é distribuído como `.pyd` para Windows)
- **Python 3.11** (o SDK é compilado para o CPython 3.11)
- Headset BrainLink pareado via Bluetooth
- Arduino com 5 servos e módulo HC-05

## Instalação

```bash
pip install -r requirements.txt
```

O SDK do BrainLink **não** está no repositório (é da Macrotellect e não tem licença de
redistribuição). Baixe `BrainLinkParser.pyd` de
<https://github.com/Macrotellect/BrainLinkParser-Python> e coloque em:

```
deps/BrainLinkParser.pyd
```

Para conferir se está tudo no lugar, rode da raiz do projeto:

```bash
python -m tests.teste_rapido
```

O teste deve terminar com `RESULTADO: TUDO OK`.

## Execução

```bash
python main.py
```

Na tela inicial, escolha a porta serial do Arduino (HC-05) e a do BrainLink e clique em **INICIAR**.

## Firmware

O código do Arduino está em `firmware/icm_firmware.ino`.

- Servos nos pinos **3, 5, 6, 9 e 10** (polegar, indicador, médio, anelar e mínimo)
- Comunicação serial a **9600 bps**: recebe um caractere `A`–`E` e move os dedos
- **Desconecte o HC-05 dos pinos 0 (RX) e 1 (TX) antes de gravar** o firmware; senão o upload falha

## Estrutura de pastas

```
.
├── main.py                       # ponto de entrada
├── requirements.txt
├── core/
│   └── state_enum.py             # enum State (A–E) com comparação de ordem
├── deps/
│   └── BrainLinkParser.pyd       # SDK do BrainLink (baixar manualmente, não versionado)
├── firmware/
│   └── icm_firmware.ino          # firmware do Arduino (servos)
├── src/
│   ├── adapters/                 # conexão serial com Arduino e BrainLink
│   ├── models/
│   │   └── eeg_buffer.py         # buffer thread-safe lido pela interface
│   ├── services/
│   │   ├── eeg_state_machine.py  # filtro EMA + máquina de estados
│   │   └── eeg_state_sytem.py    # orquestra hardware, máquina de estados e UI
│   ├── ui/
│   │   └── app.py                # interface gráfica (CustomTkinter)
│   └── utils/
└── tests/
    └── teste_rapido.py           # teste de imports e da máquina de estados
```
