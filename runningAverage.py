#
#   runningAverage      Simple running average
#
#    X = runningAverage(width_of_window)
#
#    average = X.value(nextitem)
#

class runningAverage:
    def __init__(self, window):
        self.P = window
        self.stream = []
    def value(self, instance):
        self.stream.append(instance)
        if len(self.stream) > self.P:
            self.stream.pop(0)
        if len(self.stream) == 0:
            average = instance
        else:
            average = sum(self.stream)/len(self.stream)
        return average
