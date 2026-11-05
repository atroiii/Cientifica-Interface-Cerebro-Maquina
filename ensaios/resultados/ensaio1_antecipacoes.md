# Espúrios que são antecipações (cenário b, rampa + ruído)

Antecipação = troca para G que ocorre no máximo 15 s antes de o sinal sem ruído entrar em G.

| Lógica | Filtro | σ | Espúrios (30 rep.) | Antecipações (≤ 15 s) | Mediana da antecipação (s) |
|---|---|---|---|---|---|
| real_v2 | α=0.5 (código) | 3 | 71 | 70 | 4 |
| real_v2 | α=0.5 (código) | 5 | 101 | 87 | 7 |
| real_v2 | α=0.5 (código) | 10 | 274 | 61 | 10 |
| real_v1 | α=0.5 (código) | 3 | 71 | 70 | 4 |
| real_v1 | α=0.5 (código) | 5 | 101 | 86 | 7 |
| real_v1 | α=0.5 (código) | 10 | 270 | 58 | 10 |
| faixas_sem_trava | α=0.5 (código) | 3 | 770 | 233 | 4 |
| faixas_sem_trava | α=0.5 (código) | 5 | 1422 | 385 | 5 |
| faixas_sem_trava | α=0.5 (código) | 10 | 3038 | 545 | 7 |
| histerese_3 | α=0.5 (código) | 3 | 10 | 10 | 2 |
| histerese_3 | α=0.5 (código) | 5 | 181 | 79 | 4 |
| histerese_3 | α=0.5 (código) | 10 | 1331 | 284 | 7 |
