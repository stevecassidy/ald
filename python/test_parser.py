import unittest

from typesetting_parse import *


class TestParser(unittest.TestCase):
    """Test the typesetting parser"""


    def getlines(self, filename, start, end):
        """Get a number of lines from a typesetting file"""

        lines = []
        with open(filename) as fd:
            count = 1
            for line in fd:
                if count >= start:
                    lines.append(line)
                if count >= end:
                    break
                count += 1
        return ''.join(lines)



    def test_split_entries(self):
        """Can we split a typesetting file into entries?"""

        text = self.getlines('../typesetting/txt/a.txt', 42, 55)

        entries = split_entries(text)

        self.assertEqual(2, len(entries))
        self.assertEqual('abbreviation', entries[0].split('|')[0])
        self.assertEqual('ABC', entries[1].split('|')[0])


    def test_split_entries_abide(self):
        """finding 'abide' was failing"""

        text = self.getlines('../typesetting/txt/a.txt', 64, 88)

        entries = split_entries(text)

        self.assertEqual(2, len(entries))
        self.assertEqual('abide', entries[0].split('|')[0])
        self.assertEqual('ability', entries[1].split('|')[0])


    def test_process_entry(self):
        """test parsing one entry"""

        text = self.getlines('../typesetting/txt/a.txt', 32, 40)

        entry = split_entries(text)[0]

        info = process_entry(entry)

        self.assertEqual(info['headword'], 'abandon')
        self.assertEqual(info['pronounce'], "@`bAnd@n'")

        # expect two senses
        self.assertEqual(len(info['senses']), 2)
        self.assertEqual(info['sense'][0]['ps'], "verb")
        self.assertEqual(info['sense'][0]['definition'], "If you abandon something, you stop doing it.")





if __name__=='__main__':

    unittest.main()
