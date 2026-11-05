# Transitório de partida (lógica real, sinal constante sem ruído)

| Filtro | Sinal constante | Primeiros 15 comandos (1 por s) | s em A |
|---|---|---|---|
| bruto | 42 | `BBBBBBBBBBBBBBB` | 0 |
| α=0.1 | 42 | `AAAAAAAAAAABBBB` | 11 |
| α=0.2 | 42 | `AAAAABBBBBBBBBB` | 5 |
| α=0.3 | 42 | `AAABBBBBBBBBBBB` | 3 |
| α=0.5 (código) | 42 | `BBBBBBBBBBBBBBB` | 0 |
| bruto | 70 | `CCCCCCCCCCCCCCC` | 0 |
| α=0.1 | 70 | `AAAAABBBBBBBBBB` | 5 |
| α=0.2 | 70 | `AABBBBBBBBBCCCC` | 2 |
| α=0.3 | 70 | `BBBBBBBCCCCCCCC` | 0 |
| α=0.5 (código) | 70 | `BBBCCCCCCCCCCCC` | 0 |
| bruto | 92 | `EEEEEEEEEEEEEEE` | 0 |
| α=0.1 | 92 | `AAABBBBBBBBCCCC` | 3 |
| α=0.2 | 92 | `ABBBBCCDDDDEEEE` | 1 |
| α=0.3 | 92 | `BBBCDDDEEEEEEEE` | 0 |
| α=0.5 (código) | 92 | `BCEEEEEEEEEEEEE` | 0 |
