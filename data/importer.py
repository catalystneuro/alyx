from collections import OrderedDict
import json
import logging
from operator import itemgetter
import os.path as op
from pickle import load, dump
from pprint import pprint
import re
import sys

# from django.utils.timezone import is_aware, make_aware
from django.core.management import call_command
from dateutil.parser import parse as parse_
import gspread
from oauth2client.service_account import ServiceAccountCredentials
# from pytz import timezone


logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


DATA_DIR = op.abspath(op.dirname(__file__))
SEVERITY_CHOICES = (
    (1, 'Sub-threshold'),
    (2, 'Mild'),
    (3, 'Moderate'),
    (4, 'Severe'),
    (5, 'Non-recovery'),
)
MOUSE_SPECIES_ID = 'c8339f4f-4afe-49d5-b2a2-a7fc61389aaf'
DEFAULT_RESPONSIBLE_USER_ID = 5


def pad(s):
    if not s:
        return ''
    return re.sub(r'\_([0-9]+)$', lambda m: '_%04d' % int(m.group(1)), s)


def flatten(l):
    return [item for sublist in l for item in sublist]


def get_username(initials):
    return {
        'AL': 'armin',
        'AP': 'andy',
        'CR': 'charu',
        'NS': 'nick',
        'JL': 'julie',
        'ICL': 'i-chun',
        'PZH': 'peter',
        'MDia': 'mika',
        'MK': 'michael',
        'SF': 'sam',
        'MP': 'marius',
        'PC': 'pip',
        'MW': 'miles',
        'LF': 'laura',
    }[initials]


def parse(date_str):
    date_str = date_str.strip() if date_str is not None else date_str
    if not date_str or date_str == '-':
        return ''
    ret = parse_(date_str)
    # if not is_aware(ret):
    #     ret = make_aware(ret, timezone=timezone('Europe/London'))
    return ret.strftime("%Y-%m-%d")


def get_sheet_doc(doc_name):
    scope = ['https://spreadsheets.google.com/feeds']
    path = op.join(DATA_DIR, 'gdrive.json')
    credentials = ServiceAccountCredentials.from_json_keyfile_name(path, scope)
    gc = gspread.authorize(credentials)
    return gc.open(doc_name)


def _load(fn):
    with open(op.join(DATA_DIR, fn), 'rb') as f:
        return load(f)


def _dump(obj, fn):
    with open(op.join(DATA_DIR, fn), 'wb') as f:
        dump(obj, f)


class Bunch(dict):
    def __init__(self, *args, **kwargs):
        super(Bunch, self).__init__(*args, **kwargs)
        self.__dict__ = self


def sheet_to_table(wks, header_line=0, first_line=2):
    logger.debug("Downloading %s...", wks)
    rows = wks.get_all_values()
    table = []
    headers = rows[header_line]
    for row in rows[first_line:]:
        l = {headers[i].strip(): row[i].strip() for i in range(len(headers))}
        # Empty line = end of table.
        if all(_ == '' for _ in l.values()):
            break
        table.append(Bunch(l))
    return table


def make_fixture(model, data, name_field='name'):
    def _transform(k, v):
        if k.endswith('_date') and not v:
            return None
        return v

    def _gen():
        for item in data.values() if isinstance(data, dict) else data:
            yield OrderedDict((
                ('model', model),
                ('pk', None),
                ('fields', ({k: _transform(k, v) for k, v in item.items()}
                            if isinstance(item, dict)
                            else {name_field: item})),
            ))
    with open(op.join(DATA_DIR, model + '.json'), 'w') as f:
        json.dump(list(_gen()), f, indent=2)


class GoogleSheetImporter(object):
    _table_names = ('procedure_table',
                    'current_lines_table',
                    'line_tables',
                    'breeding_pairs_table',
                    )

    def __init__(self):
        # self._download_tables()
        # self._cache_tables()
        # return
        self._load_tables()

        self.users = self._load_users()

        self.strains = self._get_strains(self.current_lines_table)
        self.alleles = self._get_alleles()
        self.lines = self._get_lines(self.current_lines_table)
        self.sequences = self._get_sequences(self.line_tables)
        self.subjects = self._get_subjects(self.line_tables)
        self.litters = self._get_litters(self.subjects)
        self._set_autoname_indices(self.line_tables)
        self.surgeries = self._process_procedures(self.procedure_table)
        self.breeding_pairs = self._get_breeding_pairs(self.breeding_pairs_table)
        self._set_breeding_pairs()
        self.genotype_tests = self._process_genotype_tests()

    def _download_tables(self):
        self._line_doc = get_sheet_doc('Mice Stock - C57 and Transgenic')
        self._procedure_doc = get_sheet_doc('Mice Procedure Log')

        # Load the procedure table.
        logger.debug("Downloading the procedure table...")
        self.procedure_table = sheet_to_table(self._procedure_doc.worksheet('PROCEDURE LOG'))

        # Load the current lines in the unit table.
        logger.debug("Downloading the current lines table...")
        self.current_lines_table = sheet_to_table(self._line_doc.worksheet('Current lines in the '
                                                                           'unit'))

        # Load all line sheets into tables.
        line_sheets = self._line_doc.worksheets()[7:]
        self.line_tables = {}
        for sheet in line_sheets:
            n = sheet.title.strip()
            logger.debug("Downloading the %s table..." % n)
            self.line_tables[n] = sheet_to_table(sheet, header_line=2, first_line=3)

        # Load the breeding pairs table.
        logger.debug("Downloading the breeding pairs table...")
        self.breeding_pairs_table = sheet_to_table(self._line_doc.worksheet('September 2016'),
                                                   header_line=2, first_line=3)

    def _cache_tables(self):
        for n in self._table_names:
            _dump(getattr(self, n), n)

    def _load_tables(self):
        for n in self._table_names:
            setattr(self, n, _load(n))

    def _load_users(self):
        with open(op.join(DATA_DIR, 'dumped_static.json'), 'r') as f:
            l = json.load(f)
        users = {}
        for item in l:
            if item['model'] == 'auth.user':
                users[item['fields']['username']] = item['pk']
        return users

    def _get_strains(self, table):
        return sorted(set(row['strain'] for row in table if row.get('strain', None)))

    def _get_alleles(self):
        with open(op.join(DATA_DIR, 'alleles.json'), 'r') as f:
            return json.load(f)['alleles']

    def _get_lines(self, table):
        """Dict of lines indexed by sheet name."""
        lines = {}
        for row in table:
            if not row['Sheet Name']:
                continue
            fields = Bunch()
            fields['name'] = row['NAME']
            fields['auto_name'] = row['Autoname']
            fields['target_phenotype'] = row['LONG NAME']
            fields['description'] = row['BLURB']
            fields['strain'] = [row['strain']] if row['strain'] else None
            fields['json'] = {
                "stock_no": row['STOCK NO'],
                "source": row['SOURCE'],
                "genotype": row['GENOTYPE'],
                "bru_strain_number": row['BRU STRAIN NUMBER'],
                "atlas": row['ATLAS'],
            }
            lines[row['Sheet Name']] = fields
        return lines

    def _get_line_sequences(self, line_table):
        if not line_table:
            return
        return sorted(set(c[8:].strip() for c in line_table[0].keys()
                          if c.startswith('Genotype') and c[8:].strip()))

    def _get_sequences(self, line_tables):
        """Set each line's sequences and return the list of all sequences."""
        seqs = []
        for name, line_table in line_tables.items():
            sequences = self._get_line_sequences(line_table)
            self.lines[name]['sequences'] = [[_] for _ in sequences]
            seqs.append(sequences)
        return sorted(set(flatten(seqs)))

    def _get_genotype_test(self, row):
        # row from line table
        for col, val in row.items():
            if not col.startswith('Genotype'):
                continue
            if val not in ('-', '+'):
                continue
            test_result = '-+'.index(val)
            sequence = col[8:].strip()
            yield {'sequence': sequence,
                   'test_result': test_result,
                   }

    def _get_litter_notes(self, row):
        mother = row.get('F Parent', '')
        father = row.get('M Parent', '')
        notes = 'mother=%s\nfather=%s' % (mother, father)
        return notes

    def _get_subjects_in_line(self, line, table):
        line_name = self.lines[line].auto_name
        subjects = {}
        for row in table:
            fields = Bunch()
            fields['ear_mark'] = row['Ear mark']
            fields['sex'] = row['Sex']
            fields['notes'] = row['Notes']
            fields['birth_date'] = parse(row['DOB'])
            fields['death_date'] = parse(row.get('death date', None))
            fields['wean_date'] = parse(row.get('Weaned', None))
            fields['nickname'] = pad(row['autoname'].strip())
            fields['json'] = {}
            fields['json']['lamis_cage'] = row['LAMIS Cage number']
            fields['line'] = [line_name]
            litter_notes = self._get_litter_notes(row)
            fields['litter'] = (line_name, fields['birth_date'], litter_notes)
            fields['genotype_test'] = list(self._get_genotype_test(row))
            # Temporary values used later on.
            fields['bp_index'] = row.get('BP index', None)

            subjects[fields['nickname']] = fields
        return subjects

    def _get_subjects(self, line_tables):
        subjects = {}
        for line, table in line_tables.items():
            subjects.update(self._get_subjects_in_line(line, table))
        return subjects

    def _get_line(self, line):
        out = self.lines.get(line, None)
        if not out:
            for l in self.lines.values():
                if l.auto_name == line:
                    return l
        return out

    def _get_litters(self, subjects):
        """Return a set of unique tuples (line, birth_date, notes)."""
        litters_set = sorted(set([subject.litter for subject in subjects.values()]),
                             key=itemgetter(1))
        litters = {}
        litter_map = {}
        for line, birth_date, notes in litters_set:
            # Find the litter name.
            for i in range(1, 1000):
                name = '%s_L_%03d' % (line, i)
                if name in litters:
                    continue
                break
            litters[name] = Bunch(descriptive_name=name,
                                  line=[line],
                                  birth_date=birth_date,
                                  notes=notes,
                                  )
            self._get_line(line)['litter_autoname_index'] = i
            litter_map[line, birth_date, notes] = name
        # Replace the litter tuples by the litter names.
        for subject in subjects.values():
            subject.litter = [litter_map[subject.litter]]
        return litters

    def _set_autoname_indices(self, line_tables):
        for line, table in line_tables.items():
            self.lines[line]['subject_autoname_index'] = int(table[-1].get('n', '') or 0)

    def _get_severity(self, severity_name):
        for s, n in SEVERITY_CHOICES:
            if n == severity_name:
                return s

    def _process_procedures(self, table):
        surgeries = []
        for row in table:
            old_name = row['transgenic spreadsheet mouse name']
            new_name = pad(row['Nickname'])
            birth_date = parse(row['Date of Birth'])
            # Get or create the subject.
            self.subjects[new_name] = self.subjects.pop(old_name, Bunch(birth_date=birth_date))
            # Update the subject name.
            subject = self.subjects[new_name]

            subject['nickname'] = new_name
            subject['actual_severity'] = self._get_severity(row['Actual Severity'])
            subject['line'] = [self.lines[row['Line']].auto_name] if row['Line'] else None
            subject['adverse_effects'] = row['Adverse Effects']
            subject['death_date'] = parse(row['Cull Date'])
            subject['cull_method'] = row['Cull Method']
            subject['protocol_number'] = row['Protocol #']
            subject['responsible_user'] = [get_username(row['Responsible User'])]

            # Add the surgery.
            surgery = Bunch()
            surgery['users'] = [[get_username(initials.strip())]
                                for initials in re.split(',|/', row['Surgery Performed By'])]
            surgery['subject'] = [new_name]
            surgery['start_time'] = parse(row['Date of surgery'])
            surgery['outcome_type'] = row['Acute/ Recovery'][0]
            surgery['narrative'] = row['Procedures']

            surgeries.append(surgery)
        return surgeries

    def _get_breeding_pairs(self, table):
        breeding_pairs = {}
        for row in table:
            line = row['line']
            index = row['index'] or 0
            if not line:
                continue

            bp = Bunch()
            bp['name'] = '%s_BP_%03d' % (line, int(index))
            bp['line'] = [line]
            bp['notes'] = row['Notes']
            self._get_line(line)['breeding_pair_autoname_index'] = index

            for which_parent in ('father', 'mother1', 'mother2'):
                if not row[which_parent]:
                    continue
                name = pad(row[which_parent])
                parent = self.subjects.get(name, Bunch(nickname=name))
                wp = {'father': 'father', 'mother1': 'mother'}.get(which_parent, '')
                sex = {'father': 'M', 'mother1': 'F', 'mother2': 'F'}[which_parent]
                parent['birth_date'] = parse(row['%s DOB' % wp]) if wp else None
                parent['line'] = [line]
                parent['sex'] = sex
                # Make sure the parent is in the subjects dictionary.
                self.subjects[name] = parent
                bp[which_parent] = [name]

            breeding_pairs[bp['name']] = bp

        return breeding_pairs

    def _set_breeding_pairs(self):
        for subject in self.subjects.values():
            bp_index = subject.pop('bp_index', None)
            if not bp_index:
                continue
            line_name = subject['line']
            bp_name = '%s_BP_%03d' % (line_name, int(bp_index))
            # assert bp_name in self.breeding_pairs
            litter = subject['litter'][0]
            # TODO
            # self.litters[litter]['breeding_pair'] = [bp_name]

    def _process_genotype_tests(self):
        tests = []
        for subject in self.subjects.values():
            for test in subject.pop('genotype_test', []):
                tests.append(dict(
                    subject=[subject['nickname']],
                    sequence=[test['sequence']],
                    test_result=test['test_result'],
                ))
        return tests


def import_data():
    importer = GoogleSheetImporter()

    make_fixture('subjects.strain', importer.strains, 'descriptive_name')
    make_fixture('subjects.allele', importer.alleles, 'informal_name')
    make_fixture('subjects.sequence', importer.sequences, 'informal_name')
    make_fixture('subjects.line', importer.lines, 'auto_name')
    make_fixture('subjects.litter', importer.litters, 'descriptive_name')
    make_fixture('subjects.subject', importer.subjects, 'nickname')
    make_fixture('subjects.genotypetest', importer.genotype_tests)
    make_fixture('subjects.breedingpair', importer.breeding_pairs, 'name')
    make_fixture('actions.surgery', importer.surgeries)

    # TODO: set breeding pairs to litters


if __name__ == '__main__':
    import_data()
