import dollarN as dN


class GestureRecognizer:

    def __init__(self):
        self.r = dN.recognizer()

        # Options configurables :
        # self.r.set_same_nb_strokes(False)
        # self.r.set_rotation_invariance(False)

        # Gestes de base : liste de traits -> [ [trait_1], [trait_2], ... ]
        self.ajouter_forme('U', [[[0.0, 5.0], [0.0, 0.0], [5.0, 0.0], [5.0, 5.0]]])  # 1 trait
        self.ajouter_forme('X', [[[0.0, 0.0], [5.0, 5.0]], [[0.0, 5.0], [5.0, 0.0]]])  # 2 traits
        self.ajouter_forme('T', [[[0.0, 5.0], [5.0, 5.0]], [[2.5, 0.0], [2.5, 5.0]]])  # 2 traits

    def ajouter_forme(self, nom, strokes):
        self.r.add_gesture(nom, strokes)

    def reconnaitre(self, points):
        return self.r.recognize(points)


if __name__ == '__main__':
    recognizer = GestureRecognizer()
    test_t = [[[0.0, 5.2], [5.0, 5.0]], [[2.5, 0.0], [2.5, 5.0]]]
    resultat = recognizer.reconnaitre(test_t)
    print(resultat)