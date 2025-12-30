# RUBIX-TRY
This project implements a program to solve a standard 3x3x3 Rubik's Cube from any scrambled state. It uses an efficient algorithm to find a sequence of moves to reach the solved state. The solver can output the sequence of moves to the console or a file. 
Algorithms Used
The solver is built upon the Two-Phase Algorithm developed by Herbert Kociemba, which efficiently finds solutions in a relatively small number of moves (typically 20 moves or less, which is "God's number"). 

    Phase 1: Orients all edge and corner pieces correctly.
    Phase 2: Permutes the pieces into their final positions while maintaining their orientation. 

Other implementations might use different methods such as the beginner-friendly CFOP (Cross, F2L, OLL, PLL) method, Iterative Deepening A* (IDA*), or even reinforcement learning. 

pour tester: python3 rubiks_simple.py
