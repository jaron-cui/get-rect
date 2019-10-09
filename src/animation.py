class DopeSheet:

    def __init__(self):

        test1 = [0, 300, 1, .1]
        test2 = [400, 800, 10, .1]
        self.keyframes = [test1, test2]
        self.interpolations = []
        self.equation = 0

        #  keyframe format: [x, y, slope, intensity]

    def at(self, time):

        if time >= self.interpolations[len(self.interpolations) - 1][0]:

            self.equation = len(self.interpolations) - 1

        elif time < self.interpolations[0][0]:

            return self.interpolations[0][1]

        else:

            while time >= self.interpolations[self.equation + 1][0]:

                self.equation -= 1

            while time < self.interpolations[self.equation][0]:

                self.equation += 1

        coefficients = self.interpolations[self.equation]

        if len(coefficients) == 3:

            return coefficients[1] * (time - coefficients[0]) + coefficients[2]

        else:

            x = time - coefficients[0]
            an, ad = coefficients[1]
            bn, bd = coefficients[2]

            return an * (x ** 3) / ad + bn * (x ** 2) / bd + coefficients[3] * x + coefficients[4]

    def set_keyframes(self, keyframes):

        self.keyframes = keyframes

    def interpolate(self):

        self.interpolations = []

        for index in range(len(self.keyframes) - 1):

            keyframe = self.keyframes[index]
            next_keyframe = self.keyframes[index + 1]
            interval = next_keyframe[0] - keyframe[0]
            dominance = keyframe[3] / (keyframe[3] + next_keyframe[3])

            #  setting the location and slope of the interpolation based on the intensity

            ease_center = interval * dominance
            ease_lower_bound = dominance * keyframe[3] * interval
            ease_upper_bound = interval - (1 - dominance) * next_keyframe[3] * interval

            x = ease_upper_bound - ease_lower_bound - keyframe[0]
            y = next_keyframe[2] * (ease_upper_bound - next_keyframe[0]) - keyframe[2] * (ease_lower_bound - keyframe[0]) + next_keyframe[1] - keyframe[1]
            s1 = keyframe[2]
            s2 = next_keyframe[2]

            # formula for the coefficients of a cubic function that connects two keyframes smoothly

            a = (s1 * x + s2 * x - 2 * y),  (x ** 3)
            b = (3 * y - 2 * s1 * x - s2 * x), (x ** 2)
            c = s1

            self.interpolations.append([keyframe[0], keyframe[2], keyframe[1]])
            self.interpolations.append([ease_lower_bound + keyframe[0], a, b, c, keyframe[1]])
            self.interpolations.append([ease_upper_bound + keyframe[0], next_keyframe[2], y + keyframe[1]])

        print(self.interpolations)
