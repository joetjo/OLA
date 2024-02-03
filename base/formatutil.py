
class FormatUtil:
    @staticmethod
    def formatDuration( strValue ):
        if strValue is None:
            return ""
        try:
            val = int(float(strValue))
        except TypeError:
            return ""
        if val < 60:
            return "{}s".format(str(val))
        elif val < 3600:
            minute = int(val / 60)
            second = int(val - (minute * 60))
            return "{}m {}s".format(str(minute), str(second))
        else:
            hour = int(val / 3600)
            minute = int((val - (hour * 3600)) / 60)
            return "{}h{}m".format(str(hour), str(minute))
