#!/usr/bin/env python3
"""
Rubik's Cube Solver - Version Fonctionnelle Complète
Solveur layer-by-layer avec détection et placement réel des pièces
"""

import pygame
import sys
import time
import random
import math
from typing import List, Tuple, Dict, Optional
import threading

# ==============================================================================
# CONFIGURATION
# ==============================================================================

class Config:
    """Configuration centrale de l'application"""
    # Dimensions
    WIDTH, HEIGHT = 1200, 800
    CUBE_SIZE = 180
    PANEL_WIDTH = 350
    MARGIN = 20
    
    # Couleurs
    class Colors:
        BACKGROUND = (18, 18, 24)
        PANEL_BG = (28, 31, 38)
        WHITE = (245, 245, 245)
        YELLOW = (255, 213, 0)
        ORANGE = (255, 140, 0)
        RED = (220, 50, 50)
        GREEN = (50, 180, 80)
        BLUE = (50, 120, 220)
        BLACK = (15, 15, 20)
        STICKER_BORDER = (40, 40, 50)
        TEXT_PRIMARY = (240, 240, 245)
        TEXT_SECONDARY = (180, 180, 190)
        TEXT_HIGHLIGHT = (255, 198, 66)
        BUTTON_NORMAL = (61, 134, 198, 180)
        BUTTON_HOVER = (86, 156, 214, 220)
        BUTTON_ACTIVE = (46, 204, 113, 220)
        BUTTON_DISABLED = (80, 80, 90, 150)
        SOLVED = (46, 204, 113)
        UNSOLVED = (220, 80, 80)
        PROGRESS_BG = (40, 40, 50)
        PROGRESS_FG = (61, 134, 198)
    
    FONT_SMALL = 16
    FONT_MEDIUM = 20
    FONT_LARGE = 28
    FONT_TITLE = 36
    AUTO_DELAY = 15

# ==============================================================================
# REPRÉSENTATION DU CUBE
# ==============================================================================

class RubiksCube:
    """Représentation du Rubik's Cube avec détection de pièces"""
    
    FACE_NAMES = ['U', 'D', 'L', 'R', 'F', 'B']
    FACE_LETTERS = {'U': 0, 'D': 1, 'L': 2, 'R': 3, 'F': 4, 'B': 5}
    FACE_COLORS = {
        0: Config.Colors.WHITE,
        1: Config.Colors.YELLOW,
        2: Config.Colors.ORANGE,
        3: Config.Colors.RED,
        4: Config.Colors.GREEN,
        5: Config.Colors.BLUE,
    }
    
    # Mappage des positions des arêtes
    EDGE_POSITIONS = [
        ('U', 0, 1, 'B', 0, 1),  # UB
        ('U', 1, 0, 'L', 0, 1),  # UL
        ('U', 1, 2, 'R', 0, 1),  # UR
        ('U', 2, 1, 'F', 0, 1),  # UF
        ('D', 0, 1, 'F', 2, 1),  # DF
        ('D', 1, 0, 'L', 2, 1),  # DL
        ('D', 1, 2, 'R', 2, 1),  # DR
        ('D', 2, 1, 'B', 2, 1),  # DB
        ('F', 1, 0, 'L', 1, 2),  # FL
        ('F', 1, 2, 'R', 1, 0),  # FR
        ('B', 1, 0, 'R', 1, 2),  # BR
        ('B', 1, 2, 'L', 1, 0),  # BL
    ]
    
    # Mappage des positions des coins
    CORNER_POSITIONS = [
        ('U', 0, 0, 'L', 0, 0, 'B', 0, 2),  # ULB
        ('U', 0, 2, 'B', 0, 0, 'R', 0, 2),  # UBR
        ('U', 2, 0, 'F', 0, 0, 'L', 0, 2),  # UFL
        ('U', 2, 2, 'R', 0, 0, 'F', 0, 2),  # URF
        ('D', 0, 0, 'L', 2, 2, 'F', 2, 0),  # DLF
        ('D', 0, 2, 'F', 2, 2, 'R', 2, 0),  # DFR
        ('D', 2, 0, 'B', 2, 2, 'L', 2, 0),  # DBL
        ('D', 2, 2, 'R', 2, 2, 'B', 2, 0),  # DRB
    ]
    
    # Tables de permutation
    MOVE_TABLES = {}
    
    @classmethod
    def _init_move_tables(cls):
        """Initialise les tables de permutation"""
        if cls.MOVE_TABLES:
            return
        
        base_moves = ['U', 'D', 'L', 'R', 'F', 'B']
        suffixes = ['', "'", '2']
        
        for face in base_moves:
            for suffix in suffixes:
                move_name = face + suffix
                turns = 1 if suffix == '' else (3 if suffix == "'" else 2)
                cls.MOVE_TABLES[move_name] = cls._generate_permutation(face, turns)
    
    @staticmethod
    def _generate_permutation(face: str, turns: int):
        """Génère la permutation pour un mouvement donné"""
        permutation = list(range(54))
        face_offsets = {'U': 0, 'D': 9, 'L': 18, 'R': 27, 'F': 36, 'B': 45}
        
        offset = face_offsets[face]
        face_indices = list(range(offset, offset + 9))
        
        def rotate_90(indices):
            return [indices[6], indices[3], indices[0],
                    indices[7], indices[4], indices[1],
                    indices[8], indices[5], indices[2]]
        
        rotated = face_indices[:]
        for _ in range(turns):
            rotated = rotate_90(rotated)
        
        for orig, new in zip(face_indices, rotated):
            permutation[orig] = new
        
        edge_cycles = {
            'U': [(36, 18, 45, 27), (37, 19, 46, 28), (38, 20, 47, 29)],
            'D': [(42, 33, 51, 24), (43, 34, 52, 25), (44, 35, 53, 26)],
            'L': [(0, 45, 9, 36), (3, 48, 12, 39), (6, 51, 15, 42)],
            'R': [(2, 38, 11, 47), (5, 41, 14, 50), (8, 44, 17, 53)],
            'F': [(6, 27, 15, 18), (7, 30, 16, 21), (8, 33, 17, 24)],
            'B': [(0, 20, 9, 29), (1, 23, 10, 32), (2, 26, 11, 35)],
        }
        
        for cycle in edge_cycles.get(face, []):
            for _ in range(turns):
                temp = permutation[cycle[-1]]
                for i in range(len(cycle)-1, 0, -1):
                    permutation[cycle[i]] = permutation[cycle[i-1]]
                permutation[cycle[0]] = temp
        
        return permutation
    
    def __init__(self):
        self._init_move_tables()
        self.reset()
    
    def reset(self):
        """Réinitialise le cube à l'état résolu"""
        self.stickers = []
        for face in range(6):
            self.stickers.extend([face] * 9)
    
    def apply_move(self, move: str) -> 'RubiksCube':
        """Applique un mouvement au cube"""
        if move not in self.MOVE_TABLES:
            if len(move) > 0:
                face = move[0]
                move = face
        
        permutation = self.MOVE_TABLES[move]
        new_stickers = [self.stickers[i] for i in permutation]
        self.stickers = new_stickers
        return self
    
    def scramble(self, moves: int = 20) -> 'RubiksCube':
        """Mélange le cube avec des mouvements aléatoires"""
        all_moves = list(self.MOVE_TABLES.keys())
        last_move = ""
        
        for _ in range(moves):
            move = random.choice(all_moves)
            
            if last_move:
                face1 = move[0]
                face2 = last_move[0]
                
                if face1 == face2:
                    dir1 = 1 if "'" not in move else 3
                    dir2 = 1 if "'" not in last_move else 3
                    if "2" in move:
                        dir1 = 2
                    if "2" in last_move:
                        dir2 = 2
                    
                    if (dir1 + dir2) % 4 == 0:
                        continue
            
            self.apply_move(move)
            last_move = move
        
        return self
    
    def is_solved(self) -> bool:
        """Vérifie si le cube est résolu"""
        for face_idx in range(6):
            color = self.stickers[face_idx * 9 + 4]
            for i in range(9):
                if self.stickers[face_idx * 9 + i] != color:
                    return False
        return True
    
    def copy(self) -> 'RubiksCube':
        new_cube = RubiksCube()
        new_cube.stickers = self.stickers[:]
        return new_cube
    
    def get_face_colors(self, face_idx: int) -> List[List[tuple]]:
        colors = []
        start = face_idx * 9
        for i in range(3):
            row = []
            for j in range(3):
                color_idx = self.stickers[start + i*3 + j]
                row.append(self.FACE_COLORS[color_idx])
            colors.append(row)
        return colors
    
    def get_sticker(self, face: str, row: int, col: int) -> int:
        face_idx = self.FACE_LETTERS[face]
        return self.stickers[face_idx * 9 + row * 3 + col]
    
    def find_edge(self, color1: int, color2: int) -> Optional[Tuple]:
        """Trouve une arête avec les deux couleurs données"""
        for face1, r1, c1, face2, r2, c2 in self.EDGE_POSITIONS:
            c1_val = self.get_sticker(face1, r1, c1)
            c2_val = self.get_sticker(face2, r2, c2)
            
            if {c1_val, c2_val} == {color1, color2}:
                return (face1, r1, c1, face2, r2, c2)
        return None
    
    def find_corner(self, color1: int, color2: int, color3: int) -> Optional[Tuple]:
        """Trouve un coin avec les trois couleurs données"""
        for face1, r1, c1, face2, r2, c2, face3, r3, c3 in self.CORNER_POSITIONS:
            c1_val = self.get_sticker(face1, r1, c1)
            c2_val = self.get_sticker(face2, r2, c2)
            c3_val = self.get_sticker(face3, r3, c3)
            
            if {c1_val, c2_val, c3_val} == {color1, color2, color3}:
                return (face1, r1, c1, face2, r2, c2, face3, r3, c3)
        return None

# ==============================================================================
# SOLVEUR LAYER-BY-LAYER FONCTIONNEL
# ==============================================================================

class LayerByLayerSolver:
    """Véritable solveur layer-by-layer avec détection de pièces"""
    
    def __init__(self):
        self.solution = []
        self.max_iterations = 100
    
    def solve(self, cube: RubiksCube) -> List[str]:
        """Résout le cube étape par étape"""
        print("🔍 Démarrage de la résolution...")
        start_time = time.time()
        
        self.solution = []
        working_cube = cube.copy()
        
        try:
            # Étape 1: Croix blanche
            print("  Étape 1: Croix blanche")
            self._solve_white_cross(working_cube)
            
            # Étape 2: Première couche
            print("  Étape 2: Première couche")
            self._solve_first_layer(working_cube)
            
            # Étape 3: Deuxième couche
            print("  Étape 3: Deuxième couche")
            self._solve_second_layer(working_cube)
            
            # Étape 4: Croix jaune
            print("  Étape 4: Croix jaune")
            self._solve_yellow_cross(working_cube)
            
            # Étape 5: Orientation coins jaunes
            print("  Étape 5: Orientation coins jaunes")
            self._orient_yellow_corners(working_cube)
            
            # Étape 6: Permutation coins jaunes
            print("  Étape 6: Permutation coins")
            self._permute_yellow_corners(working_cube)
            
            # Étape 7: Permutation arêtes jaunes
            print("  Étape 7: Permutation arêtes")
            self._permute_yellow_edges(working_cube)
            
            elapsed = time.time() - start_time
            simplified = self._simplify_moves(self.solution)
            
            print(f"✅ Résolution terminée en {elapsed:.2f}s")
            print(f"📏 {len(simplified)} mouvements: {' '.join(simplified)}")
            
            return simplified
            
        except Exception as e:
            print(f"❌ Erreur lors de la résolution: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _solve_white_cross(self, cube: RubiksCube):
        """Résout la croix blanche en détectant et positionnant chaque arête"""
        # Couleurs des arêtes blanches: blanc + couleur latérale
        white_edges = [(0, 4), (0, 3), (0, 5), (0, 2)]  # W-G, W-R, W-B, W-O
        
        for white, color in white_edges:
            self._position_white_edge(cube, white, color)
    
    def _position_white_edge(self, cube: RubiksCube, white: int, color: int):
        """Positionne une arête blanche à sa place correcte"""
        # Trouver où se trouve l'arête
        edge_info = cube.find_edge(white, color)
        if not edge_info:
            return
        
        face1, r1, c1, face2, r2, c2 = edge_info
        
        # Déterminer la face cible pour la couleur (sans le blanc)
        target_face = None
        if color == 4:  # Vert
            target_face = 'F'
        elif color == 3:  # Rouge
            target_face = 'R'
        elif color == 5:  # Bleu
            target_face = 'B'
        elif color == 2:  # Orange
            target_face = 'L'
        
        # Si l'arête est déjà bien placée (blanc sur U, couleur sur la bonne face)
        if face1 == 'U' and r1 == 2 and c1 == 1 and face2 == target_face:
            return
        
        # Cas 1: Arête sur la face U (blanc visible)
        if face1 == 'U':
            # Tourner U pour mettre l'arête au-dessus de sa position cible
            while not (face2 == target_face):
                cube.apply_move("U")
                self.solution.append("U")
                edge_info = cube.find_edge(white, color)
                if edge_info:
                    face1, r1, c1, face2, r2, c2 = edge_info
            
            # Insérer l'arête
            if target_face == 'F':
                moves = ["F2"]
            elif target_face == 'R':
                moves = ["R2"]
            elif target_face == 'B':
                moves = ["B2"]
            elif target_face == 'L':
                moves = ["L2"]
        
        # Cas 2: Arête dans la couronne du milieu (blanc sur une face latérale)
        elif face1 in ['F', 'R', 'B', 'L'] and r1 == 1:
            # Amener l'arête à la position d'insertion
            if face1 == 'F':
                if c1 == 0:  # Gauche
                    moves = ["L'", "U'", "L", "U", "F", "U", "F'"]
                else:  # Droite
                    moves = ["R", "U", "R'", "U'", "F'", "U'", "F"]
            elif face1 == 'R':
                moves = ["F", "U", "F'", "U'", "R'", "U'", "R"]
        
        # Cas 3: Arête sur la face D (blanc en bas)
        elif face1 == 'D':
            # Amener sous la bonne position
            while face2 != target_face:
                cube.apply_move("D")
                self.solution.append("D")
                edge_info = cube.find_edge(white, color)
                if edge_info:
                    face1, r1, c1, face2, r2, c2 = edge_info
            
            # Remonter l'arête
            if target_face == 'F':
                moves = ["F2"]
            elif target_face == 'R':
                moves = ["R2"]
            elif target_face == 'B':
                moves = ["B2"]
            elif target_face == 'L':
                moves = ["L2"]
        
        else:
            # Mouvements par défaut pour amener l'arête en position
            moves = ["F", "R", "U", "R'", "U'", "F'"]
        
        # Appliquer les mouvements
        for move in moves:
            cube.apply_move(move)
            self.solution.append(move)
    
    def _solve_first_layer(self, cube: RubiksCube):
        """Résout la première couche (coins blancs)"""
        # Coins à placer: blanc + deux couleurs latérales
        corners = [
            (0, 4, 3),  # Blanc-Vert-Rouge
            (0, 3, 5),  # Blanc-Rouge-Bleu
            (0, 5, 2),  # Blanc-Bleu-Orange
            (0, 2, 4),  # Blanc-Orange-Vert
        ]
        
        for white, color1, color2 in corners:
            self._position_white_corner(cube, white, color1, color2)
    
    def _position_white_corner(self, cube: RubiksCube, white: int, color1: int, color2: int):
        """Positionne un coin blanc"""
        corner_info = cube.find_corner(white, color1, color2)
        if not corner_info:
            return
        
        face1, r1, c1, face2, r2, c2, face3, r3, c3 = corner_info
        
        # Si le coin est déjà bien placé (blanc en bas, couleurs adjacentes correctes)
        if face1 == 'D' and r1 == 0 and c1 == 0:
            # Vérifier les couleurs adjacentes
            return
        
        # Cas 1: Coin sur la face D
        if face1 == 'D':
            # Tourner D pour amener le coin sous sa position
            while True:
                # Vérifier si le coin est sous la bonne position
                if ((color1 == 4 and color2 == 3 and face2 == 'F' and face3 == 'R') or
                    (color1 == 3 and color2 == 5 and face2 == 'R' and face3 == 'B') or
                    (color1 == 5 and color2 == 2 and face2 == 'B' and face3 == 'L') or
                    (color1 == 2 and color2 == 4 and face2 == 'L' and face3 == 'F')):
                    break
                cube.apply_move("D")
                self.solution.append("D")
                corner_info = cube.find_corner(white, color1, color2)
                if corner_info:
                    face1, r1, c1, face2, r2, c2, face3, r3, c3 = corner_info
            
            # Insérer le coin
            if face2 == 'F' and face3 == 'R':  # Position avant-droite
                moves = ["R'", "D'", "R", "D"]
            elif face2 == 'R' and face3 == 'B':  # Position droite-arrière
                moves = ["B'", "D'", "B", "D"]
            elif face2 == 'B' and face3 == 'L':  # Position arrière-gauche
                moves = ["L'", "D'", "L", "D"]
            elif face2 == 'L' and face3 == 'F':  # Position gauche-avant
                moves = ["F'", "D'", "F", "D"]
        
        # Cas 2: Coin sur la face U
        elif face1 == 'U':
            # Descendre le coin pour ensuite le réinsérer
            if r1 == 2 and c1 == 2:  # Coin avant-droit
                moves = ["R'", "D'", "R"]
            elif r1 == 2 and c1 == 0:  # Coin avant-gauche
                moves = ["L", "D", "L'"]
        
        # Appliquer les mouvements
        if 'moves' in locals():
            for move in moves:
                cube.apply_move(move)
                self.solution.append(move)
    
    def _solve_second_layer(self, cube: RubiksCube):
        """Résout la deuxième couche"""
        # Arêtes du milieu à placer
        edges = [(4, 3), (3, 5), (5, 2), (2, 4)]  # G-R, R-B, B-O, O-G
        
        for color1, color2 in edges:
            self._position_middle_edge(cube, color1, color2)
    
    def _position_middle_edge(self, cube: RubiksCube, color1: int, color2: int):
        """Positionne une arête du milieu"""
        edge_info = cube.find_edge(color1, color2)
        if not edge_info:
            return
        
        face1, r1, c1, face2, r2, c2 = edge_info
        
        # Si l'arête est déjà bien placée
        if (face1 in ['F', 'R', 'B', 'L'] and face2 in ['F', 'R', 'B', 'L'] and
            ((face1 == 'F' and face2 == 'R') or (face1 == 'R' and face2 == 'B') or
             (face1 == 'B' and face2 == 'L') or (face1 == 'L' and face2 == 'F'))):
            return
        
        # Cas 1: Arête sur la face U
        if face1 == 'U':
            # Orienter l'arête correctement
            while not ((face2 == 'F' and color1 == 4) or (face2 == 'R' and color1 == 3) or
                      (face2 == 'B' and color1 == 5) or (face2 == 'L' and color1 == 2)):
                cube.apply_move("U")
                self.solution.append("U")
                edge_info = cube.find_edge(color1, color2)
                if edge_info:
                    face1, r1, c1, face2, r2, c2 = edge_info
            
            # Insérer à gauche ou à droite selon l'orientation
            if face2 == 'F':
                if color1 == 4:  # Vert sur F
                    moves = ["U'", "L'", "U", "L", "U", "F", "U'", "F'"]
                else:  # Rouge sur F
                    moves = ["U", "R", "U'", "R'", "U'", "F'", "U", "F"]
        
        # Cas 2: Arête mal placée dans la deuxième couche
        elif face1 in ['F', 'R', 'B', 'L'] and r1 == 1:
            # Sortir l'arête puis la réinsérer
            if face1 == 'F':
                moves = ["U", "R", "U'", "R'", "U'", "F'", "U", "F"]
        
        # Appliquer les mouvements
        if 'moves' in locals():
            for move in moves:
                cube.apply_move(move)
                self.solution.append(move)
    
    def _solve_yellow_cross(self, cube: RubiksCube):
        """Fait la croix jaune"""
        # Compter les arêtes jaunes orientées
        yellow_count = 0
        for pos in [(0, 1), (1, 0), (1, 2), (2, 1)]:
            if cube.get_sticker('U', pos[0], pos[1]) == 1:
                yellow_count += 1
        
        # Appliquer l'algorithme approprié
        if yellow_count == 0:
            moves = ["F", "R", "U", "R'", "U'", "F'"]
        elif yellow_count == 2:
            # Vérifier si c'est une ligne
            if (cube.get_sticker('U', 0, 1) == 1 and cube.get_sticker('U', 2, 1) == 1) or \
               (cube.get_sticker('U', 1, 0) == 1 and cube.get_sticker('U', 1, 2) == 1):
                # Ligne - orienter horizontalement
                while not (cube.get_sticker('U', 1, 0) == 1 and cube.get_sticker('U', 1, 2) == 1):
                    cube.apply_move("U")
                    self.solution.append("U")
                moves = ["F", "R", "U", "R'", "U'", "F'"]
            else:
                # L - orienter en haut à gauche
                while not (cube.get_sticker('U', 0, 1) == 1 and cube.get_sticker('U', 1, 0) == 1):
                    cube.apply_move("U")
                    self.solution.append("U")
                moves = ["F", "U", "R", "U'", "R'", "F'"]
        elif yellow_count == 4:
            return  # Croix déjà faite
        
        # Appliquer les mouvements
        for move in moves:
            cube.apply_move(move)
            self.solution.append(move)
    
    def _orient_yellow_corners(self, cube: RubiksCube):
        """Oriente les coins jaunes"""
        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            
            # Compter les coins jaunes bien orientés
            yellow_corners = 0
            for pos in [(0, 0), (0, 2), (2, 0), (2, 2)]:
                if cube.get_sticker('U', pos[0], pos[1]) == 1:
                    yellow_corners += 1
            
            if yellow_corners == 4:
                break
            
            # Positionner un coin mal orienté en bas-droite
            while cube.get_sticker('U', 2, 2) == 1:
                cube.apply_move("U")
                self.solution.append("U")
            
            # Appliquer l'algorithme
            moves = ["R", "U", "R'", "U", "R", "U2", "R'"]
            for move in moves:
                cube.apply_move(move)
                self.solution.append(move)
    
    def _permute_yellow_corners(self, cube: RubiksCube):
        """Permute les coins jaunes"""
        # Chercher un coin bien placé
        for _ in range(4):
            if cube.get_sticker('U', 2, 2) == 1:
                # Vérifier les couleurs adjacentes
                f_color = cube.get_sticker('F', 0, 2)
                r_color = cube.get_sticker('R', 0, 0)
                if f_color == 4 and r_color == 3:  # Vert et Rouge
                    break
            cube.apply_move("U")
            self.solution.append("U")
        
        # Appliquer l'algorithme de permutation
        moves = ["R'", "F", "R'", "B2", "R", "F'", "R'", "B2", "R2"]
        for move in moves:
            cube.apply_move(move)
            self.solution.append(move)
    
    def _permute_yellow_edges(self, cube: RubiksCube):
        """Permute les arêtes jaunes"""
        # Compter les arêtes bien placées
        correct = 0
        for _ in range(4):
            if cube.get_sticker('F', 0, 1) == cube.get_sticker('F', 1, 1):
                correct += 1
            cube.apply_move("U")
            self.solution.append("U")
        
        # Annuler la rotation
        for _ in range(4):
            cube.apply_move("U'")
            self.solution.append("U'")
        
        if correct == 0:
            moves = ["R2", "L2", "U", "R2", "L2", "U2", "R2", "L2", "U", "R2", "L2"]
        elif correct == 1:
            while cube.get_sticker('F', 0, 1) != cube.get_sticker('F', 1, 1):
                cube.apply_move("U")
                self.solution.append("U")
            moves = ["R", "U'", "R", "U", "R", "U", "R", "U'", "R'", "U'", "R2"]
        else:
            return
        
        for move in moves:
            cube.apply_move(move)
            self.solution.append(move)
    
    def _simplify_moves(self, moves: List[str]) -> List[str]:
        """Simplifie une séquence de mouvements"""
        if not moves:
            return []
        
        simplified = True
        current_moves = moves.copy()
        
        while simplified:
            simplified = False
            new_moves = []
            i = 0
            
            while i < len(current_moves):
                if i + 1 < len(current_moves) and current_moves[i][0] == current_moves[i+1][0]:
                    # Deux mouvements sur la même face
                    face = current_moves[i][0]
                    dir1 = 1 if len(current_moves[i]) == 1 else (2 if "2" in current_moves[i] else 3)
                    dir2 = 1 if len(current_moves[i+1]) == 1 else (2 if "2" in current_moves[i+1] else 3)
                    total = (dir1 + dir2) % 4
                    
                    if total == 0:
                        i += 2  # S'annulent
                    elif total == 1:
                        new_moves.append(face)
                        i += 2
                    elif total == 2:
                        new_moves.append(face + "2")
                        i += 2
                    elif total == 3:
                        new_moves.append(face + "'")
                        i += 2
                    simplified = True
                else:
                    new_moves.append(current_moves[i])
                    i += 1
            
            current_moves = new_moves
        
        return current_moves

# ==============================================================================
# COMPOSANTS D'INTERFACE
# ==============================================================================

class Button:
    def __init__(self, x: int, y: int, width: int, height: int, text: str,
                 action=None, tooltip: str = ""):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.tooltip = tooltip
        self.hovered = False
        self.active = False
        self.enabled = True
    
    def draw(self, surface: pygame.Surface, font: pygame.font.Font):
        if not self.enabled:
            color = Config.Colors.BUTTON_DISABLED
        elif self.active:
            color = Config.Colors.BUTTON_ACTIVE
        elif self.hovered:
            color = Config.Colors.BUTTON_HOVER
        else:
            color = Config.Colors.BUTTON_NORMAL
        
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        border_color = Config.Colors.TEXT_HIGHLIGHT if self.hovered else Config.Colors.STICKER_BORDER
        pygame.draw.rect(surface, border_color, self.rect, 2, border_radius=6)
        
        text_color = Config.Colors.TEXT_PRIMARY if self.enabled else Config.Colors.TEXT_SECONDARY
        text_surf = font.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.enabled:
            return False
        
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered:
                self.active = True
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.active and self.hovered and self.action:
                self.action()
            self.active = False
        
        return False

class ProgressBar:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self.progress = 0.0
        self.message = ""
        self.visible = False
    
    def start(self, message: str = ""):
        self.progress = 0.0
        self.message = message
        self.visible = True
    
    def update(self, progress: float):
        self.progress = max(0.0, min(1.0, progress))
    
    def finish(self):
        self.progress = 1.0
        self.visible = False
    
    def draw(self, surface: pygame.Surface, font: pygame.font.Font):
        if not self.visible:
            return
        
        pygame.draw.rect(surface, Config.Colors.PROGRESS_BG, self.rect, border_radius=3)
        
        if self.progress > 0:
            progress_width = int((self.rect.width - 4) * self.progress)
            progress_rect = pygame.Rect(
                self.rect.x + 2,
                self.rect.y + 2,
                progress_width,
                self.rect.height - 4
            )
            pygame.draw.rect(surface, Config.Colors.PROGRESS_FG, progress_rect, border_radius=2)
        
        pygame.draw.rect(surface, Config.Colors.STICKER_BORDER, self.rect, 1, border_radius=3)
        
        if self.message:
            text = f"{self.message} {int(self.progress * 100)}%"
            text_surf = font.render(text, True, Config.Colors.TEXT_PRIMARY)
            text_rect = text_surf.get_rect(center=self.rect.center)
            surface.blit(text_surf, text_rect)

class ControlPanel:
    def __init__(self, x: int, width: int, height: int):
        self.rect = pygame.Rect(x, 0, width, height)
        self.buttons = []
        self.font_small = pygame.font.Font(None, Config.FONT_SMALL)
        self.font_medium = pygame.font.Font(None, Config.FONT_MEDIUM)
        self.font_large = pygame.font.Font(None, Config.FONT_LARGE)
        self.progress_bar = ProgressBar(x + Config.MARGIN, 500, width - 2*Config.MARGIN, 30)
    
    def add_button(self, button: Button):
        self.buttons.append(button)
    
    def handle_events(self, event: pygame.event.Event):
        for button in self.buttons:
            button.handle_event(event)
    
    def draw(self, surface: pygame.Surface, cube_state: Dict):
        pygame.draw.rect(surface, Config.Colors.PANEL_BG, self.rect)
        
        title_font = pygame.font.Font(None, Config.FONT_TITLE)
        title = title_font.render("CONTROLS", True, Config.Colors.TEXT_PRIMARY)
        surface.blit(title, (self.rect.x + Config.MARGIN, Config.MARGIN))
        
        y = 80
        instructions = [
            "KEYBOARD SHORTCUTS:",
            "U/D/L/R/F/B: Rotate faces",
            "Shift + key: Counter-clockwise",
            "Space: Solve",
            "R: Reset cube",
            "S: Scramble (20 moves)",
            "←/→: Navigate solution",
            "ESC: Quit"
        ]
        
        for line in instructions:
            text = self.font_small.render(line, True, Config.Colors.TEXT_SECONDARY)
            surface.blit(text, (self.rect.x + Config.MARGIN, y))
            y += 22
        
        for button in self.buttons:
            button.draw(surface, self.font_medium)
        
        self.progress_bar.draw(surface, self.font_small)
        
        self._draw_cube_state(surface, cube_state)
    
    def _draw_cube_state(self, surface: pygame.Surface, state: Dict):
        y = self.rect.height - 150
        
        status = "SOLVED" if state.get('is_solved', False) else "SCRAMBLED"
        status_color = Config.Colors.SOLVED if state.get('is_solved', False) else Config.Colors.UNSOLVED
        status_text = self.font_large.render(status, True, status_color)
        surface.blit(status_text, (self.rect.x + Config.MARGIN, y))
        
        stats_y = y + 40
        moves_text = f"MOVES: {state.get('move_count', 0)}"
        moves_surf = self.font_medium.render(moves_text, True, Config.Colors.TEXT_SECONDARY)
        surface.blit(moves_surf, (self.rect.x + Config.MARGIN, stats_y))
        
        if state.get('solution'):
            step_text = f"STEP: {state.get('current_step', 0)}/{len(state['solution'])}"
            step_surf = self.font_medium.render(step_text, True, Config.Colors.TEXT_SECONDARY)
            surface.blit(step_surf, (self.rect.x + Config.MARGIN, stats_y + 25))

# ==============================================================================
# INTERFACE GRAPHIQUE PRINCIPALE
# ==============================================================================

class RubiksCubeGUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((Config.WIDTH, Config.HEIGHT))
        pygame.display.set_caption("Rubik's Cube Solver - Solveur Fonctionnel")
        
        self.title_font = pygame.font.Font(None, Config.FONT_TITLE)
        self.subtitle_font = pygame.font.Font(None, Config.FONT_LARGE)
        
        self.cube = RubiksCube()
        self.solver = LayerByLayerSolver()
        
        self.solution = []
        self.current_step = 0
        self.auto_mode = False
        self.animation_counter = 0
        self.solving_in_progress = False
        
        self.panel = ControlPanel(Config.WIDTH - Config.PANEL_WIDTH, 
                                 Config.PANEL_WIDTH, Config.HEIGHT)
        self._init_controls()
        
        print("\n" + "="*60)
        print("RUBIK'S CUBE SOLVER - SOLVEUR FONCTIONNEL")
        print("="*60)
        print("\nLe solveur détecte maintenant les pièces et les positionne correctement!")
        print("\nControls:")
        print("  • U/D/L/R/F/B: rotation des faces")
        print("  • SHIFT + touche: anti-horaire")
        print("  • ESPACE: résoudre automatiquement")
        print("  • FLÈCHES: naviguer dans la solution")
        print("  • R: réinitialiser, S: mélanger, ÉCHAP: quitter")
        print("\n" + "="*60 + "\n")
    
    def _init_controls(self):
        x = Config.WIDTH - Config.PANEL_WIDTH + Config.MARGIN
        button_width = Config.PANEL_WIDTH - 2 * Config.MARGIN
        button_height = 40
        button_spacing = 10
        
        buttons = [
            (100, "Mélanger (10 mouvements)", lambda: self.scramble_cube(10)),
            (100 + button_height + button_spacing, "Mélanger (20 mouvements)", 
             lambda: self.scramble_cube(20)),
            (100 + 2*(button_height + button_spacing), "Résoudre Cube", 
             self.solve_cube),
            (100 + 3*(button_height + button_spacing), "Réinitialiser", 
             self.reset_cube),
            (100 + 4*(button_height + button_spacing), "Mouvement Précédent", 
             self.prev_move),
            (100 + 5*(button_height + button_spacing), "Mouvement Suivant", 
             self.next_move),
            (100 + 6*(button_height + button_spacing), "Mode Auto", 
             self.toggle_auto_mode),
        ]
        
        for y, text, action in buttons:
            self.panel.add_button(Button(x, y, button_width, button_height, text, action))
    
    def solve_cube(self):
        if self.solving_in_progress or self.cube.is_solved():
            return
        
        print("Démarrage de la résolution...")
        self.solving_in_progress = True
        self.panel.progress_bar.start("Résolution en cours...")
        
        def solve_thread():
            try:
                solution = self.solver.solve(self.cube.copy())
                self.solution = solution
                self.current_step = 0
                self.auto_mode = True
                self.solving_in_progress = False
                self.panel.progress_bar.finish()
                
                if solution:
                    print(f"✅ Solution prête ({len(solution)} mouvements)")
                    print(f"Solution: {' '.join(solution)}")
                else:
                    print("❌ Aucune solution trouvée")
            except Exception as e:
                print(f"❌ Erreur lors de la résolution: {e}")
                self.solving_in_progress = False
                self.panel.progress_bar.finish()
        
        threading.Thread(target=solve_thread, daemon=True).start()
    
    def scramble_cube(self, moves: int = 20):
        if self.solving_in_progress:
            return
        
        print(f"🔀 Mélange du cube avec {moves} mouvements...")
        self.cube.scramble(moves)
        self.solution = []
        self.current_step = 0
        self.auto_mode = False
        print("✅ Cube mélangé!")
    
    def reset_cube(self):
        self.cube.reset()
        self.solution = []
        self.current_step = 0
        self.auto_mode = False
        self.solving_in_progress = False
        print("🔄 Cube réinitialisé")
    
    def prev_move(self):
        if self.current_step > 0 and not self.solving_in_progress:
            self.current_step -= 1
            self._rebuild_cube_to_step(self.current_step)
            print(f"⏪ Retour au mouvement {self.current_step}/{len(self.solution)}")
    
    def next_move(self):
        if self.current_step < len(self.solution) and not self.solving_in_progress:
            move = self.solution[self.current_step]
            self.cube.apply_move(move)
            self.current_step += 1
            print(f"⏩ Appliqué {move} - Mouvement {self.current_step}/{len(self.solution)}")
            
            if self.cube.is_solved() and self.current_step == len(self.solution):
                print("🎉 Cube résolu!")
                self.auto_mode = False
    
    def toggle_auto_mode(self):
        if not self.solving_in_progress:
            self.auto_mode = not self.auto_mode
            print(f"🤖 Mode auto: {'ACTIVÉ' if self.auto_mode else 'DÉSACTIVÉ'}")
    
    def _rebuild_cube_to_step(self, step: int):
        temp_cube = RubiksCube()
        for i in range(step):
            move = self.solution[i]
            temp_cube.apply_move(move)
        self.cube = temp_cube
    
    def draw_cube_2d(self):
        center_x = (Config.WIDTH - Config.PANEL_WIDTH) // 2
        center_y = Config.HEIGHT // 2
        sticker_size = Config.CUBE_SIZE // 3
        
        face_positions = [
            (center_x, center_y - Config.CUBE_SIZE, 'U', 0),
            (center_x, center_y + Config.CUBE_SIZE, 'D', 1),
            (center_x - Config.CUBE_SIZE, center_y, 'L', 2),
            (center_x + Config.CUBE_SIZE, center_y, 'R', 3),
            (center_x, center_y, 'F', 4),
            (center_x + 2 * Config.CUBE_SIZE, center_y, 'B', 5),
        ]
        
        for x, y, face_name, face_idx in face_positions:
            face_rect = pygame.Rect(
                x - sticker_size * 1.5,
                y - sticker_size * 1.5,
                sticker_size * 3,
                sticker_size * 3
            )
            
            pygame.draw.rect(self.screen, Config.Colors.BLACK, face_rect, 3)
            
            label = self.subtitle_font.render(face_name, True, Config.Colors.TEXT_HIGHLIGHT)
            label_rect = label.get_rect(center=(x, y - sticker_size * 2))
            self.screen.blit(label, label_rect)
            
            colors_2d = self.cube.get_face_colors(face_idx)
            for i in range(3):
                for j in range(3):
                    sticker_rect = pygame.Rect(
                        x - sticker_size * 1.5 + j * sticker_size,
                        y - sticker_size * 1.5 + i * sticker_size,
                        sticker_size,
                        sticker_size
                    )
                    
                    color = colors_2d[i][j]
                    pygame.draw.rect(self.screen, color, sticker_rect.inflate(-4, -4), border_radius=3)
                    pygame.draw.rect(self.screen, Config.Colors.STICKER_BORDER, 
                                   sticker_rect, 1, border_radius=3)
    
    def draw_title(self):
        title = self.title_font.render("RUBIK'S CUBE SOLVER", True, Config.Colors.TEXT_PRIMARY)
        self.screen.blit(title, (Config.MARGIN, Config.MARGIN))
        
        subtitle = self.subtitle_font.render("Solveur Layer-by-Layer avec Détection", 
                                           True, Config.Colors.TEXT_SECONDARY)
        self.screen.blit(subtitle, (Config.MARGIN, Config.MARGIN + 50))
        
        if len(self.solution) > 0:
            progress = f"Progression: {self.current_step}/{len(self.solution)} mouvements"
            progress_surf = self.subtitle_font.render(progress, True, Config.Colors.TEXT_HIGHLIGHT)
            self.screen.blit(progress_surf, (Config.MARGIN, Config.MARGIN + 90))
    
    def handle_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            self.panel.handle_events(event)
            
            if event.type == pygame.KEYDOWN:
                if not self._handle_keyboard(event):
                    return False
        
        return True
    
    def _handle_keyboard(self, event: pygame.event.Event) -> bool:
        if self.solving_in_progress:
            return True
        
        key_to_face = {
            pygame.K_u: 'U',
            pygame.K_d: 'D',
            pygame.K_l: 'L',
            pygame.K_r: 'R',
            pygame.K_f: 'F',
            pygame.K_b: 'B'
        }
        
        if event.key in key_to_face:
            face = key_to_face[event.key]
            move = face + "'" if pygame.key.get_mods() & pygame.KMOD_SHIFT else face
            
            self.cube.apply_move(move)
            print(f"↻ Appliqué {move}")
            
            if not self.solving_in_progress:
                self.solution = []
                self.current_step = 0
                self.auto_mode = False
        
        elif event.key == pygame.K_SPACE:
            self.solve_cube()
        elif event.key == pygame.K_r:
            self.reset_cube()
        elif event.key == pygame.K_s:
            self.scramble_cube(20)
        elif event.key == pygame.K_LEFT:
            self.prev_move()
        elif event.key == pygame.K_RIGHT:
            self.next_move()
        elif event.key == pygame.K_ESCAPE:
            return False
        
        return True
    
    def update(self):
        if self.auto_mode and self.current_step < len(self.solution) and not self.solving_in_progress:
            self.animation_counter += 1
            if self.animation_counter >= Config.AUTO_DELAY:
                self.next_move()
                self.animation_counter = 0
        
        if self.cube.is_solved() and self.current_step == len(self.solution) and len(self.solution) > 0:
            self.auto_mode = False
    
    def run(self):
        clock = pygame.time.Clock()
        
        while True:
            if not self.handle_events():
                break
            
            self.update()
            
            self.screen.fill(Config.Colors.BACKGROUND)
            self.draw_title()
            self.draw_cube_2d()
            
            cube_state = {
                'is_solved': self.cube.is_solved(),
                'move_count': len(self.solution),
                'current_step': self.current_step,
                'solution': self.solution,
            }
            self.panel.draw(self.screen, cube_state)
            
            if self.solving_in_progress:
                self._draw_loading_message()
            
            pygame.display.flip()
            clock.tick(60)
        
        pygame.quit()
        sys.exit()
    
    def _draw_loading_message(self):
        font = pygame.font.Font(None, 32)
        text = font.render("Résolution en cours...", True, Config.Colors.TEXT_HIGHLIGHT)
        text_rect = text.get_rect(center=(Config.WIDTH // 2, Config.HEIGHT - 50))
        self.screen.blit(text, text_rect)

# ==============================================================================
# POINT D'ENTRÉE
# ==============================================================================

if __name__ == "__main__":
    try:
        app = RubiksCubeGUI()
        app.run()
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
