class DopeSheet:

    def __init__(self):

        self.keyframes = []
        self.interpolations = []

        #  keyframe format: [x, y, intensity, slope, bound]

    def set(self, keyframes):

        self.keyframes = keyframes

    def interpolate(self):

        self.interpolations = []

        for index in range(len(self.keyframes) - 1):

            keyframe = self.keyframes[index]
            next_keyframe = self.keyframes[index + 1]
            interval = next_keyframe[0] - keyframe[0]
            dominance = keyframe[2] / (keyframe[2] + next_keyframe[2])

            initial_slope = keyframe[3]

            #  setting the location and slope of the interpolation based on the intensity
            intersection_position = interval * dominance
            intersection_slope = dominance * initial_slope + (1 - dominance) * next_keyframe[3]
            intersection_intercept = dominance * intersection_position * initial_slope + (1 - dominance) * (next_keyframe[1] - keyframe[1] - intersection_position * next_keyframe[3])
            keyframe[4] = intersection_position + keyframe[0]