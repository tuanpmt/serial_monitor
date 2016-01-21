import json
import re


class FilterException(Exception):
    pass


class FilterAttributeError(FilterException):
    """
    Filter is missing one or more parameters
    """
    pass

class FilterParsingError(FilterException):
    """
    Filter file could not be parsed
    """
    pass


class _Filter(object):
    """
    Base filter class
    """
    def __init__(self, filter_text, case_sensitive):
        self.filter_text = filter_text
        self.case_sensitive = case_sensitive

    def matches(self, text):
        """
        Required function to check if the text given matches the filter's properties
        :param text: the text to check against the filter
        :type text: str
        :rtype: bool
        """
        raise NotImplementedError


class _FilterContains(_Filter):
    def matches(self, text):
        if self.case_sensitive:
            return self.filter_text in text

        return self.filter_text.lower() in text.lower()


class _FilterEndsWith(_Filter):
    def matches(self, text):
        if self.case_sensitive:
            return text.endswith(self.filter_text)
        return text.lower().endswith(self.filter_text.lower())


class _FilterRegex(_Filter):
    def __init__(self, filter_text, case_sensitive):
        super(_FilterRegex, self).__init__(filter_text, case_sensitive)
        self.pattern = re.compile(filter_text)

    def matches(self, text):
        return self.pattern.search(text) is not None


filters = {
    "contains": _FilterContains,
    "endswith": _FilterEndsWith,
    "regex":    _FilterRegex,
}


class FilterFile(object):
    # filter file parameters
    KEY_NAME = "name"
    KEY_FILTERS = "filters"
    # filter parameters
    KEY_METHOD = "method"
    KEY_TEXT = "text"
    KEY_CASE_SENS = "case_sensitive"
    REQUIRED_FILTER_PARAMS = [KEY_TEXT, KEY_METHOD]
    REQUIRED_FILTER_FILE_PARAMS = [KEY_NAME, KEY_FILTERS]

    def __init__(self, name, filter_list):
        self.name = name
        self.filter_list = filter_list

    @staticmethod
    def parse_filter_file(file_text, skip_invalid_filters=False):
        """
        Parses JSON text into a filter file object

        :param file_text: the text of the filter file
        :type file_text: str
        :param skip_invalid_filters: behavior to take when an invalid filter is discovered.
                                     If set to True, that specific filter will just be ignored and parsing will continue.
                                     If set to False, a FilterAttributeError will be thrown
        :type skip_invalid_filters: bool

        :return: the corresponding FilterFile object
        :rtype: FilterFile
        """
        try:
            file = json.loads(file_text)
        except Exception as ex:
            raise FilterParsingError(ex.args[0])

        if not all(params in file for params in FilterFile.REQUIRED_FILTER_FILE_PARAMS):
            return None

        name = file[FilterFile.KEY_NAME]
        filter_list = []
        i = -1
        for f in file[FilterFile.KEY_FILTERS]:
            i += 1
            # Check that the required parameters are in the dictionary
            if not all(params in f for params in FilterFile.REQUIRED_FILTER_PARAMS):
                msg = "Missing required params for filter {}: {}".format(i, FilterFile.REQUIRED_FILTER_PARAMS)
                if not skip_invalid_filters:
                    raise FilterAttributeError(msg)
                print(msg)

            method = f[FilterFile.KEY_METHOD]
            if method not in filters:
                msg = "Unknown filter method in filter {}: {}.  Possible methods: {}".format(i, method, filters.keys())
                if not skip_invalid_filters:
                    raise FilterAttributeError(msg)
                print(msg)

            filter_type = filters[method]

            case_sensitive = f.get(FilterFile.KEY_CASE_SENS, False)
            text = f[FilterFile.KEY_TEXT]

            filter_list.append(filter_type(text, case_sensitive))
        return FilterFile(name, filter_list)

    def check_filters(self, text):
        """
        Checks the given text against all filters in the file

        :param text: the text to check
        :type text: str

        :return: True if the text satisfies one of the filters
        :rtype: bool
        """
        for f in self.filter_list:
            if f.matches(text):
                return True
        return False



if __name__ == '__main__':
    json_file = \
"""
{
    "name": "My Filter",
    "filters":
    [
        {
            "text": "test",
            "method": "contains",
            "case_sensitive": false
        },
        {
            "text": "([0-9a-fA-f]{2} ){4}\\\\d*",
            "method": "regex"
        }
    ]
}
"""
    filter_file = FilterFile.parse_filter_file(json_file)

    test_inputs = [
        "test123",
        "TeSt",
        "123test123",
        "123test",
        "ttteeessstt",
        "willnotmatch",
        "01 23 45 67 ",
        "texttexttextaa BB CC dd 123452345",
    ]
    for i in test_inputs:
        print("\"{}\" matches? {}".format(i, filter_file.check_filters(i)))

    print("done")
