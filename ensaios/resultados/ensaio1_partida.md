# Partida: real_v2 (y inicial = 1ª leitura) x real_v1 (y inicial = 0)

## Sinal constante sem ruído

| Lógica | Filtro | Sinal constante | Primeiros 15 comandos (1 por s) | s em A (de 60) |
|---|---|---|---|---|
| real_v2 | bruto | 19 | `AAAAAAAAAAAAAAA` | 60 |
| real_v2 | α=0.1 | 19 | `AAAAAAAAAAAAAAA` | 60 |
| real_v2 | α=0.2 | 19 | `AAAAAAAAAAAAAAA` | 60 |
| real_v2 | α=0.3 | 19 | `AAAAAAAAAAAAAAA` | 60 |
| real_v2 | α=0.5 (código) | 19 | `AAAAAAAAAAAAAAA` | 60 |
| real_v2 | bruto | 20 | `BBBBBBBBBBBBBBB` | 0 |
| real_v2 | α=0.1 | 20 | `BBBBBBBBBBBBBBB` | 0 |
| real_v2 | α=0.2 | 20 | `BBBBBBBBBBBBBBB` | 0 |
| real_v2 | α=0.3 | 20 | `BBBBBBBBBBBBBBB` | 0 |
| real_v2 | α=0.5 (código) | 20 | `BBBBBBBBBBBBBBB` | 0 |
| real_v2 | bruto | 25 | `BBBBBBBBBBBBBBB` | 0 |
| real_v2 | α=0.1 | 25 | `BBBBBBBBBBBBBBB` | 0 |
| real_v2 | α=0.2 | 25 | `BBBBBBBBBBBBBBB` | 0 |
| real_v2 | α=0.3 | 25 | `BBBBBBBBBBBBBBB` | 0 |
| real_v2 | α=0.5 (código) | 25 | `BBBBBBBBBBBBBBB` | 0 |
| real_v2 | bruto | 42 | `BBBBBBBBBBBBBBB` | 0 |
| real_v2 | α=0.1 | 42 | `BBBBBBBBBBBBBBB` | 0 |
| real_v2 | α=0.2 | 42 | `BBBBBBBBBBBBBBB` | 0 |
| real_v2 | α=0.3 | 42 | `BBBBBBBBBBBBBBB` | 0 |
| real_v2 | α=0.5 (código) | 42 | `BBBBBBBBBBBBBBB` | 0 |
| real_v2 | bruto | 70 | `CCCCCCCCCCCCCCC` | 0 |
| real_v2 | α=0.1 | 70 | `CCCCCCCCCCCCCCC` | 0 |
| real_v2 | α=0.2 | 70 | `CCCCCCCCCCCCCCC` | 0 |
| real_v2 | α=0.3 | 70 | `CCCCCCCCCCCCCCC` | 0 |
| real_v2 | α=0.5 (código) | 70 | `CCCCCCCCCCCCCCC` | 0 |
| real_v2 | bruto | 92 | `EEEEEEEEEEEEEEE` | 0 |
| real_v2 | α=0.1 | 92 | `EEEEEEEEEEEEEEE` | 0 |
| real_v2 | α=0.2 | 92 | `EEEEEEEEEEEEEEE` | 0 |
| real_v2 | α=0.3 | 92 | `EEEEEEEEEEEEEEE` | 0 |
| real_v2 | α=0.5 (código) | 92 | `EEEEEEEEEEEEEEE` | 0 |
| real_v1 | bruto | 19 | `AAAAAAAAAAAAAAA` | 60 |
| real_v1 | α=0.1 | 19 | `AAAAAAAAAAAAAAA` | 60 |
| real_v1 | α=0.2 | 19 | `AAAAAAAAAAAAAAA` | 60 |
| real_v1 | α=0.3 | 19 | `AAAAAAAAAAAAAAA` | 60 |
| real_v1 | α=0.5 (código) | 19 | `AAAAAAAAAAAAAAA` | 60 |
| real_v1 | bruto | 20 | `BBBBBBBBBBBBBBB` | 0 |
| real_v1 | α=0.1 | 20 | `AAAAAAAAAAAAAAA` | 60 |
| real_v1 | α=0.2 | 20 | `AAAAAAAAAAAAAAA` | 60 |
| real_v1 | α=0.3 | 20 | `AAAAAAAAAAAAAAA` | 60 |
| real_v1 | α=0.5 (código) | 20 | `AAAAAAAAAAAAAAA` | 60 |
| real_v1 | bruto | 25 | `BBBBBBBBBBBBBBB` | 0 |
| real_v1 | α=0.1 | 25 | `AAAAAAAAAAAAAAA` | 60 |
| real_v1 | α=0.2 | 25 | `AAAAAAAAAAAAAAA` | 60 |
| real_v1 | α=0.3 | 25 | `AAAAAAAAAAAAAAA` | 60 |
| real_v1 | α=0.5 (código) | 25 | `AAAAAAAAAAAAAAA` | 60 |
| real_v1 | bruto | 42 | `BBBBBBBBBBBBBBB` | 0 |
| real_v1 | α=0.1 | 42 | `AAAAAAAAAAABBBB` | 11 |
| real_v1 | α=0.2 | 42 | `AAAAABBBBBBBBBB` | 5 |
| real_v1 | α=0.3 | 42 | `AAABBBBBBBBBBBB` | 3 |
| real_v1 | α=0.5 (código) | 42 | `BBBBBBBBBBBBBBB` | 0 |
| real_v1 | bruto | 70 | `CCCCCCCCCCCCCCC` | 0 |
| real_v1 | α=0.1 | 70 | `AAAAABBBBBBBBBB` | 5 |
| real_v1 | α=0.2 | 70 | `AABBBBBBBBBCCCC` | 2 |
| real_v1 | α=0.3 | 70 | `BBBBBBBCCCCCCCC` | 0 |
| real_v1 | α=0.5 (código) | 70 | `BBBCCCCCCCCCCCC` | 0 |
| real_v1 | bruto | 92 | `EEEEEEEEEEEEEEE` | 0 |
| real_v1 | α=0.1 | 92 | `AAABBBBBBBBCCCC` | 3 |
| real_v1 | α=0.2 | 92 | `ABBBBCCDDDDEEEE` | 1 |
| real_v1 | α=0.3 | 92 | `BBBCDDDEEEEEEEE` | 0 |
| real_v1 | α=0.5 (código) | 92 | `BCEEEEEEEEEEEEE` | 0 |

## Cenário d com ruído: % das 30 repetições com algum comando A nos primeiros 60 s

| Lógica | Filtro | σ | Patamar B | Patamar C | Patamar D | Patamar E |
|---|---|---|---|---|---|---|
| real_v2 | bruto | 3 | 0 % | 0 % | 0 % | 0 % |
| real_v2 | bruto | 5 | 0 % | 0 % | 0 % | 0 % |
| real_v2 | bruto | 10 | 53 % | 0 % | 0 % | 0 % |
| real_v2 | α=0.1 | 3 | 0 % | 0 % | 0 % | 0 % |
| real_v2 | α=0.1 | 5 | 0 % | 0 % | 0 % | 0 % |
| real_v2 | α=0.1 | 10 | 0 % | 0 % | 0 % | 0 % |
| real_v2 | α=0.2 | 3 | 0 % | 0 % | 0 % | 0 % |
| real_v2 | α=0.2 | 5 | 0 % | 0 % | 0 % | 0 % |
| real_v2 | α=0.2 | 10 | 0 % | 0 % | 0 % | 0 % |
| real_v2 | α=0.3 | 3 | 0 % | 0 % | 0 % | 0 % |
| real_v2 | α=0.3 | 5 | 0 % | 0 % | 0 % | 0 % |
| real_v2 | α=0.3 | 10 | 0 % | 0 % | 0 % | 0 % |
| real_v2 | α=0.5 (código) | 3 | 0 % | 0 % | 0 % | 0 % |
| real_v2 | α=0.5 (código) | 5 | 0 % | 0 % | 0 % | 0 % |
| real_v2 | α=0.5 (código) | 10 | 0 % | 0 % | 0 % | 0 % |
| real_v1 | bruto | 3 | 0 % | 0 % | 0 % | 0 % |
| real_v1 | bruto | 5 | 0 % | 0 % | 0 % | 0 % |
| real_v1 | bruto | 10 | 53 % | 0 % | 0 % | 0 % |
| real_v1 | α=0.1 | 3 | 100 % | 100 % | 100 % | 100 % |
| real_v1 | α=0.1 | 5 | 100 % | 100 % | 100 % | 100 % |
| real_v1 | α=0.1 | 10 | 100 % | 100 % | 100 % | 100 % |
| real_v1 | α=0.2 | 3 | 100 % | 100 % | 100 % | 100 % |
| real_v1 | α=0.2 | 5 | 100 % | 100 % | 100 % | 100 % |
| real_v1 | α=0.2 | 10 | 100 % | 100 % | 93 % | 70 % |
| real_v1 | α=0.3 | 3 | 100 % | 10 % | 0 % | 0 % |
| real_v1 | α=0.3 | 5 | 100 % | 30 % | 0 % | 0 % |
| real_v1 | α=0.3 | 10 | 100 % | 63 % | 7 % | 0 % |
| real_v1 | α=0.5 (código) | 3 | 30 % | 0 % | 0 % | 0 % |
| real_v1 | α=0.5 (código) | 5 | 27 % | 0 % | 0 % | 0 % |
| real_v1 | α=0.5 (código) | 10 | 43 % | 0 % | 0 % | 0 % |
