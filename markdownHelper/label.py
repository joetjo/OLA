


class MhLabels:

    def __init__(self, JSON):
        self.about = self.readLabel(JSON, "labelAbout", "About")
        self.tags = self.readLabel(JSON, "labelTags", "Tags")
        self.comment = self.readLabel(JSON, "labelComment", "Comment")

    @staticmethod
    def readLabel(JSON, label, default):
        try:
            return JSON[label]
        except KeyError:
            return default
