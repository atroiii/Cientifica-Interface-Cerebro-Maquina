# Subida contínua 50→90 sem ruído (lógica real; 30 s em 50 para acomodar o filtro, depois a subida e 30 s em 90; trocas contadas a partir do fim do patamar em 50)

| Lógica | Filtro | Velocidade da subida | Sequência de gestos emitidos (trocas) | D alcançado? | E alcançado? |
|---|---|---|---|---|---|
| real_v2 | bruto | degrau | B→E | não | sim |
| real_v2 | α=0.1 | degrau | B→C→D→E | sim | sim |
| real_v2 | α=0.2 | degrau | B→C→D→E | sim | sim |
| real_v2 | α=0.3 | degrau | B→C→D→E | sim | sim |
| real_v2 | α=0.5 (código) | degrau | B→C→D→E | sim | sim |
| real_v1 | α=0.5 (código) | degrau | B→C→D→E | sim | sim |
| real_v2 | bruto | 10 pt/s | B→C→D→E | sim | sim |
| real_v2 | α=0.1 | 10 pt/s | B→C→D→E | sim | sim |
| real_v2 | α=0.2 | 10 pt/s | B→C→D→E | sim | sim |
| real_v2 | α=0.3 | 10 pt/s | B→C→D→E | sim | sim |
| real_v2 | α=0.5 (código) | 10 pt/s | B→C→D→E | sim | sim |
| real_v1 | α=0.5 (código) | 10 pt/s | B→C→E | não | sim |
| real_v2 | bruto | 5 pt/s | B→C→D→E | sim | sim |
| real_v2 | α=0.1 | 5 pt/s | B→C→D→E | sim | sim |
| real_v2 | α=0.2 | 5 pt/s | B→C→D→E | sim | sim |
| real_v2 | α=0.3 | 5 pt/s | B→C→D→E | sim | sim |
| real_v2 | α=0.5 (código) | 5 pt/s | B→C→D→E | sim | sim |
| real_v1 | α=0.5 (código) | 5 pt/s | B→C→D→E | sim | sim |
| real_v2 | bruto | 2 pt/s | B→C→D→E | sim | sim |
| real_v2 | α=0.1 | 2 pt/s | B→C→D→E | sim | sim |
| real_v2 | α=0.2 | 2 pt/s | B→C→D→E | sim | sim |
| real_v2 | α=0.3 | 2 pt/s | B→C→D→E | sim | sim |
| real_v2 | α=0.5 (código) | 2 pt/s | B→C→D→E | sim | sim |
| real_v1 | α=0.5 (código) | 2 pt/s | B→C→D→E | sim | sim |
| real_v2 | bruto | 1 pt/s | B→C→D→E | sim | sim |
| real_v2 | α=0.1 | 1 pt/s | B→C→D→E | sim | sim |
| real_v2 | α=0.2 | 1 pt/s | B→C→D→E | sim | sim |
| real_v2 | α=0.3 | 1 pt/s | B→C→D→E | sim | sim |
| real_v2 | α=0.5 (código) | 1 pt/s | B→C→D→E | sim | sim |
| real_v1 | α=0.5 (código) | 1 pt/s | B→C→D→E | sim | sim |
| real_v2 | bruto | 0.5 pt/s | B→C→D→E | sim | sim |
| real_v2 | α=0.1 | 0.5 pt/s | B→C→D→E | sim | sim |
| real_v2 | α=0.2 | 0.5 pt/s | B→C→D→E | sim | sim |
| real_v2 | α=0.3 | 0.5 pt/s | B→C→D→E | sim | sim |
| real_v2 | α=0.5 (código) | 0.5 pt/s | B→C→D→E | sim | sim |
| real_v1 | α=0.5 (código) | 0.5 pt/s | B→C→D→E | sim | sim |
